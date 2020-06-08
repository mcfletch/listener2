#! /usr/bin/env python3
from deepspeech import Model, version
import logging, os, sys, select, json, socket, queue, collections
import numpy as np
import webrtcvad

import threading
log = logging.getLogger(__name__)

# How long of leading silence causes it to be discarded?
SAMPLE_RATE = 16000
FRAME_SIZE = (SAMPLE_RATE//1000)*20 # rate of 16000, so 16samples/ms
SILENCE_FRAMES = 10 # in 20ms frames


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
    """Convert DeepSpeect Transcript struct to a json-compatible format"""
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
    def __init__(self, duration=30, rate=SAMPLE_RATE):
        self.duration = duration 
        self.rate = rate
        self.size = duration * rate
        self.buffer = np.zeros((self.size,),dtype=np.int16) 
        self.write_head = 0
        self.start = 0
    def read_in(self, fh, blocksize=1024):
        """Read in content from the buffer"""
        target = self.buffer[self.write_head:self.write_head+blocksize]
        written = fh.readinto(target)
        self.write_head = (self.write_head + written) % self.size 
        return target[:written]
    def itercurrent(self):
        """Iterate over all samples in the current record
        
        After we truncate from the beginning we have to
        reset the stream with the content written already
        """
        if self.write_head < self.start:
            yield self.buffer[self.start:]
            yield self.buffer[:self.write_head]
        else:
            yield self.buffer[self.start:self.write_head]
    def __len__(self):
        if self.write_head < self.start:
            return self.size - self.start + self.write_head 
        else:
            return self.write_head - self.start


def produce_voice_runs(input,read_frames=2,rate=SAMPLE_RATE,silence=SILENCE_FRAMES,voice_detect_aggression=3):
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
    silence_frames = collections.deque([],10)
    while True:
        buffer = ring.read_in(input,read_size)
        if not len(buffer):
            log.debug("Input disconnected")
            yield None
            silence_count = 0
        for start in range(0,len(buffer)-1,FRAME_SIZE):
            frame = buffer[start:start+FRAME_SIZE]
            if vad.is_speech(frame,rate):
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
    model, input, out_queue, read_size=320, rate=SAMPLE_RATE,
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

def iter_metadata(model, input, rate=SAMPLE_RATE,max_decode_rate=4):
    """Iterate over input producing transcriptions with model"""
    stream = model.createStream()
    length = last_decode = 0
    for buffer in produce_voice_runs(
        input,
        rate=rate,
    ):
        if buffer is None:
            if length:
                metadata = metadata_to_json(stream.finishStreamWithMetadata(5),partial=False)
                for tran in metadata['transcripts']:
                    log.info(">>> %0.02f %s", tran['confidence'],tran['words'])
                yield metadata
                stream = model.createStream()
                length = last_decode = 0
        else:
            stream.feedAudioContent(buffer)
            written = len(buffer)
            length += written 
            if (length - last_decode) > rate // max_decode_rate:
                metadata = metadata_to_json(stream.intermediateDecodeWithMetadata(),partial=True)
                yield metadata
                words = metadata['transcripts'][0]['words']
                log.info("... %s",' '.join(words))

def open_fifo(filename,mode='rb'):
    """Open fifo for communication"""
    if not os.path.exists(filename):
        os.mkfifo(filename)
    return open(filename,mode)

def create_output_socket(sockname='/tmp/dspipe/events'):
    if os.path.exists(sockname):
        os.remove(sockname)
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.bind(sockname)
    log.info("Waiting on %s", sockname)
    return sock
def output_thread(sock,outputs):
    log.info("Waiting for connections")
    sock.listen(1)
    while True:
        conn,addr = sock.accept()
        log.info("Got a connection on %s", conn)
        q = queue.Queue()
        outputs.append(q)
        threading.Thread(target=out_writer,args=(conn,q,outputs)).start()
def write_queue(queue, outputs):
    """run the write queue"""
    while True:
        record = queue.get()
        encoded = json.dumps(record).encode('utf-8')
        for output in outputs:
            output.put(encoded)
def out_writer(conn,q, outputs):
    """Trivial thread to write events to the client"""
    while True:
        try:
            content = q.get()
            conn.sendall(content)
            conn.sendall(b'\000')
        except Exception:
            log.exception("Failed during send")
            conn.close()
            break
    outputs.remove(q)

def get_options():
    import argparse 
    parser = argparse.ArgumentParser(
        description = 'Provides an audio sink to which to write buffers to feed into DeepSpeech',
    )
    parser.add_argument(
        '-i','--input',
        default='/src/run/audio',
    )
    parser.add_argument(
        '-o','--output',
        default='/src/run/events',
    )
    parser.add_argument(
        '-m','--model',
        default = '/src/model/deepspeech-%s-models.pbmm'%os.environ.get('DEEPSPEECH_VERSION','0.7.3'),
        help = 'DeepSpeech published model'
    )
    parser.add_argument(
        '-s','--scorer',
        default = '/src/model/deepspeech-%s-models.scorer'%os.environ.get('DEEPSPEECH_VERSION','0.7.3'),
        help = 'DeepSpeect published scorer',
    )
    parser.add_argument(
        '--beam-width',
        default = None,
        type = int,
        help = 'If specified, override the model default beam width',
    )
    return parser 


def main():
    options = get_options().parse_args()
    model = Model(
        options.model,
    )
    if options.beam_width:
        model.setBeamWidth(options.beam_width)
    desired_sample_rate = model.sampleRate()
    log.info("Send Raw, Mono, 16KHz, s16le, audio to %s", options.input)
    model.enableExternalScorer(options.scorer)


    outputs = []
    out_queue = queue.Queue()
    t = threading.Thread(target=write_queue,args=(out_queue,outputs))
    t.setDaemon(True)
    t.start()

    sock = create_output_socket(options.output)
    t = threading.Thread(target=output_thread,args=(sock,outputs))
    t.setDaemon(True)
    t.start()

    log.info("Opening fifo (will pause until a source connects)")
    input = open_fifo(options.input)
    log.info("Starting recognition")
    run_recognition(model, input, out_queue)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(levelname) 7s %(name)s:%(lineno)s %(message)s',
    )
    main()