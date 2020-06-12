#! /usr/bin/env python3
"""process which runs inside the docker daemon

the purpose of the doctor damon process is to allow the set up of
an environment which will support the deep speech recognition engine
to run on any recent nvidia Ubuntu host.

the basic operation of the demon is to create a named pipe
in the users run directory to which any audio source can then be
piped into the demon. the simplest way to achieve that
is to pipe the import from alsa through ffmpeg into the named pipe.

clients may onto the events unix socket in the same directory
to receive the partial and final event json records.
"""
from deepspeech import Model, version
from listener import eventserver
import logging, os, sys, select, json, socket, queue, collections, time
import numpy as np
import webrtcvad
from . import defaults

import threading

log = logging.getLogger(__name__ if __name__ != '__main__' else 'listener')

# How long of leading silence causes it to be discarded?
FRAME_SIZE = (defaults.SAMPLE_RATE // 1000) * 20  # rate of 16000, so 16samples/ms
SILENCE_FRAMES = 10  # in 20ms frames


def metadata_to_json(metadata, partial=False):
    """Convert DeepSpeech Metadata struct to a json-compatible format"""
    struct = {
        'partial': partial,
        'final': not partial,
        'transcripts': [],
    }
    for transcript in metadata.transcripts:
        struct['transcripts'].append(transcript_to_json(transcript))
    return struct


def transcript_to_json(transcript, partial=False):
    """Convert DeepSpeech Transcript struct to a json-compatible format"""
    struct = {
        'partial': partial,
        'final': not partial,
        'tokens': [],
        'starts': [],
        'words': [],
        'word_starts': [],
        'confidence': transcript.confidence,
    }
    text = []
    word = []
    starts = 0.0
    in_word = False
    for token in transcript.tokens:
        struct['tokens'].append(token.text)
        text.append(token.text)
        struct['starts'].append(token.start_time)

        if token.text == ' ':
            if word:
                struct['words'].append(''.join(word))
            in_word = False
            del word[:]
        else:
            if not in_word:
                struct['word_starts'].append(token.start_time)
            in_word = True
            word.append(token.text)
    if word:
        struct['words'].append(''.join(word))
    struct['text'] = ''.join(text)
    return struct


class RingBuffer(object):
    """Crude numpy-backed ringbuffer"""

    def __init__(self, duration=30, rate=defaults.SAMPLE_RATE):
        self.duration = duration
        self.rate = rate
        self.size = duration * rate
        self.buffer = np.zeros((self.size,), dtype=np.int16)
        self.write_head = 0
        self.start = 0

    def read_in(self, fh, blocksize=1024):
        """Read in content from the buffer"""
        target = self.buffer[self.write_head : self.write_head + blocksize]
        if hasattr(fh, 'readinto'):
            # On the blocking fifo this consistently reads
            # the whole blocksize chunk of data...
            written = fh.readinto(target)
            if written != blocksize * 2:
                log.debug(
                    "Didn't read the whole buffer (likely disconnect): %s/%s",
                    written,
                    blocksize // 2,
                )
                target = target[: (written // 2)]
        else:
            # This is junk, unix and localhost buffering in ffmpeg
            # means we take 6+ reads to get a buffer and we wind up
            # losing a *lot* of audio due to delays
            tview = target.view(np.uint8)
            written = 0
            reads = 0
            while written < blocksize:
                written += fh.recv_into(tview[written:], blocksize - written)
                reads += 1
            if reads > 1:
                log.debug("Took %s reads to get %s bytes", reads, written)
        self.write_head = (self.write_head + written) % self.size
        return target

    def itercurrent(self):
        """Iterate over all samples in the current record
        
        After we truncate from the beginning we have to
        reset the stream with the content written already
        """
        if self.write_head < self.start:
            yield self.buffer[self.start :]
            yield self.buffer[: self.write_head]
        else:
            yield self.buffer[self.start : self.write_head]

    def __len__(self):
        if self.write_head < self.start:
            return self.size - self.start + self.write_head
        else:
            return self.write_head - self.start


def produce_voice_runs(
    input,
    read_frames=2,
    rate=defaults.SAMPLE_RATE,
    silence=SILENCE_FRAMES,
    voice_detect_aggression=3,
):
    """Produce runs of audio with voice detected
    
    input -- FIFO (named pipe) or Socket from which to read
    read_frames -- number of frames to read in on each iteration, this is a 
                   blocking read, so it needs to be pretty small to keep
                   latency down
    rate -- sample rate, 16KHz required for DeepSpeech
    silence -- number of audio frames that constitute a "pause" at which
               we should produce a new utterance
    
    Notes:

        * we want to be relatively demanding about the detection of audio
          as we are working with noisy/messy environments
        * the start-of-voice event often is preceded by a bit of 
          lower-than-threshold "silence" which is critical for catching
          the first word
        * we are using a static ringbuffer so that the main audio buffer shouldn't
          wind up being copied
    
    yields audio frames in sequence from the input
    """
    vad = webrtcvad.Vad(voice_detect_aggression)
    ring = RingBuffer(rate=rate)
    current_utterance = []

    silence_count = 0
    read_size = read_frames * FRAME_SIZE
    # set of frames that were not considered speech
    # but that we might need to recognise the first
    # word of an utterance, here (in 20ms frames)
    silence_frames = collections.deque([], 10)
    while True:
        buffer = ring.read_in(input, read_size)
        if not len(buffer):
            log.debug("Input disconnected")
            yield None
            silence_count = 0
            raise IOError('Input disconnect')
        for start in range(0, len(buffer) - 1, FRAME_SIZE):
            frame = buffer[start : start + FRAME_SIZE]
            if vad.is_speech(frame, rate):
                if silence_count:
                    # Update the ring-buffer to tell us where
                    # the audio started... note: currently there
                    # is no checking for longer-than-ring-buffer
                    # duration speeches...
                    ring.start = ring.write_head
                    log.debug('<')
                    for last in silence_frames:
                        ring.start -= len(last)
                        yield last
                    ring.start = ring.start % ring.size
                yield frame
                silence_count = 0
                silence_frames.clear()
            else:
                silence_count += 1
                silence_frames.append(frame)
                if silence_count == silence:
                    log.debug('[]')
                    yield None
                elif silence_count < silence:
                    yield frame
                    log.debug('? %s', silence_count)


def run_recognition(
    model,
    input,
    out_queue,
    read_size=320,
    rate=defaults.SAMPLE_RATE,
    max_decode_rate=4,
):
    """Read fragments from input, write results to output
    
    model -- DeepSpeech model to run 
    input -- input binary audio stream 16KHz mono 16-bit unsigned machine order audio
    output -- output (text) stream to which to write updates
    rate -- audio rate (16,000 to be compatible with DeepSpeech)
    max_decode_rate -- maximum number of times/s to do partial recognition

    As incoming data comes in, accumulate in a (ring)
    buffer. As partial recognitions are run, look for
    stability in the prefix of the utterance, so if we
    see the same text for the top prediction for N 
    runs then move the start to the start of the last
    word in the stable set, report all the words up to that
    point and then continue processing as though the 
    last word was the start of the utterance
    """
    # create our ring-buffer structure with 60s of audio
    for metadata in iter_metadata(model, input=input, rate=rate):
        out_queue.put(metadata)


def iter_metadata(model, input, rate=defaults.SAMPLE_RATE, max_decode_rate=4):
    """Iterate over input producing transcriptions with model"""
    stream = model.createStream()
    length = last_decode = 0
    for buffer in produce_voice_runs(input, rate=rate,):
        if buffer is None:
            if length:
                metadata = metadata_to_json(
                    stream.finishStreamWithMetadata(15), partial=False
                )
                for tran in metadata['transcripts']:
                    log.info(">>> %0.02f %s", tran['confidence'], tran['words'])
                yield metadata
                stream = model.createStream()
                length = last_decode = 0
        else:
            stream.feedAudioContent(buffer)
            written = len(buffer)
            length += written
            if (length - last_decode) > rate // max_decode_rate:
                metadata = metadata_to_json(
                    stream.intermediateDecodeWithMetadata(), partial=True
                )
                if metadata['transcripts'][0]['text']:
                    yield metadata
                words = metadata['transcripts'][0]['words']
                log.info("... %s", ' '.join(words))


def open_fifo(filename, mode='rb'):
    """Open fifo for communication"""
    if not os.path.exists(filename):
        os.mkfifo(filename)
    return open(filename, mode)


def create_input_socket(port):
    """Connect to the given socket as a read-only client"""
    import socket

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setblocking(True)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 640 * 100)
    sock.bind(('127.0.0.1', port))
    sock.listen(1)
    return sock


def get_options():
    import argparse

    parser = argparse.ArgumentParser(
        description='Provides an audio sink to which to write buffers to feed into DeepSpeech',
    )
    parser.add_argument(
        '-i', '--input', default='/src/run/audio',
    )
    parser.add_argument(
        '-o', '--output', default='/src/run/events',
    )
    parser.add_argument(
        '-m',
        '--model',
        default='/src/model/deepspeech-%s-models.pbmm'
        % os.environ.get('DEEPSPEECH_VERSION', '0.7.3'),
        help='DeepSpeech published model',
    )
    parser.add_argument(
        '-s',
        '--scorer',
        default='/src/model/deepspeech-%s-models.scorer'
        % os.environ.get('DEEPSPEECH_VERSION', '0.7.3'),
        help='DeepSpeech published scorer, use "" to not apply the Language Model within the daemon (letting the interpreter handle the scoring)',
    )
    parser.add_argument(
        '--beam-width',
        default=None,
        type=int,
        help='If specified, override the model default beam width',
    )
    parser.add_argument(
        '--port',
        default=None,
        type=int,
        help='If specified, use a TCP/IP socket, unfortunately we cannot use unix domain sockets due to broken ffmpeg buffering',
    )
    parser.add_argument(
        '-v',
        '--verbose',
        default=False,
        action='store_true',
        help='Enable verbose logging (for developmen/debugging)',
    )
    return parser


def process_input_file(conn, options, out_queue, background=True):
    # TODO: allow socket connections from *clients* to choose
    # the model rather than setting it in the daemon...
    # to be clear, *output* clients, not audio sinks
    log.info("Starting recognition on %s", conn)
    model = Model(options.model,)
    if options.beam_width:
        model.setBeamWidth(options.beam_width)
    desired_sample_rate = model.sampleRate()
    if desired_sample_rate != defaults.SAMPLE_RATE:
        log.error("Model expects rate of %s", desired_sample_rate)
    if options.scorer:
        model.enableExternalScorer(options.scorer)
    else:
        log.info("Disabling the scorer")
        model.disableExternalScorer()
    if background:
        t = threading.Thread(target=run_recognition, args=(model, conn, out_queue))
        t.setDaemon(background)
        t.start()
    else:
        run_recognition(model, conn, out_queue)


def main():
    options = get_options().parse_args()
    defaults.setup_logging(options)
    log.info("Send Raw, Mono, 16KHz, s16le, audio to %s", options.input)

    out_queue = eventserver.create_sending_threads(options.output)

    if options.port:
        sock = create_input_socket(options.port)
        while True:
            log.info("Waiting on %s", sock)
            conn, addr = sock.accept()
            process_input_file(conn, options, out_queue, background=True)
    else:
        # log.info("Opening fifo (will pause until a source connects)")
        while True:
            try:
                sock = open_fifo(options.input)
                log.info("FIFO connected, processing")
                process_input_file(sock, options, out_queue, background=False)
            except (webrtcvad._webrtcvad.Error, IOError) as err:
                log.info("Disconnect, re-opening fifo")
                time.sleep(2.0)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG, format='%(levelname) 7s %(name)s:%(lineno)s %(message)s',
    )
    main()
