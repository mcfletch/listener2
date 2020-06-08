#! /usr/bin/env python3
from deepspeech import Model, version
import logging, os, sys, select, json, socket, queue, collections
import numpy as np
import webrtcvad

import threading
log = logging.getLogger(__name__)

def get_options():
    import argparse 
    parser = argparse.ArgumentParser(
        description = 'Provides an audio sink to which to write buffers to feed into DeepSpeech',
    )
    parser.add_argument(
        '-i','--input',
        default='/tmp/dspipe/audio',
    )
    parser.add_argument(
        '-o','--output',
        default='/tmp/dspipe/events',
    )
    parser.add_argument(
        '-m','--model',
        default = '/src/home/working/model/deepspeech-0.7.1-models.pbmm',
        help = 'DeepSpeech published model'
    )
    parser.add_argument(
        '-s','--scorer',
        default = '/src/home/working/model/deepspeech-0.7.0-models.scorer',
        help = 'DeepSpeect published scorer',
    )
    parser.add_argument(
        '--beam-width',
        default = None,
        type = int,
        help = 'If specified, override the model default beam width',
    )
    return parser 

def open_fifo(filename,mode='rb'):
    """Open fifo for communication"""
    if not os.path.exists(filename):
        os.mkfifo(filename)
    return open(filename,mode)


def metadata_to_json(metadata, partial=False):
    struct = {
        'partial': partial,
        'final': not partial,
        'transcripts': [],
    }
    for transcript in metadata.transcripts:
        struct['transcripts'].append(transcript_to_json(transcript))
    return struct 

def transcript_to_json(transcript, partial=False):
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
    def __init__(self, duration=30, rate=16000):
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
    def drop_early(self, seconds):
        """Drop buffers from start until seconds
        
        Note: does *not* check for write_head overshoot
        """
        samples = int(seconds * 16000)
        self.start = (self.start + samples)%self.size 
    def keep_last(self, samples):
        """Keep the last N samples discarding the rest"""
        self.start = self.write_head-samples
        if self.start < 0:
            self.start = self.size - self.start
        return self.start
    def itercurrent(self):
        """Iterate over all samples in the current set
        
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

# How long of leading silence causes it to be discarded?
SILENCE_FRAMES = 10 # in 20ms frames
FRAME_SIZE = 16*20 # rate of 16000, so 16samples/ms


def produce_voice_runs(input,read_frames=2,rate=16000,silence=SILENCE_FRAMES,voice_detect_aggression=3):
    """Produce runs of audio with voice detected
    
    producer -- generate slices of audio to test
    read_size -- amount of data to read from the producer at a time
    rate -- sample rate 
    silence -- number of audio frames that constitute a "pause" at which
               we should produce a new utterance
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
                    for last in silence_frames:
                        log.debug('<')
                        yield last
                log.debug('>')
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
    model, input, out_queue, read_size=320, rate=16000,
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

def iter_metadata(model, input, rate=16000,max_decode_rate=4):
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
        threading.Thread(target=out_writer,args=(conn,q)).start()
def write_queue(queue, outputs):
    """run the write queue"""
    # log.info("Copying events to outputs")
    while True:
        record = queue.get()
        encoded = json.dumps(record).encode('utf-8')
        # log.info('Update %s to %s clients',len(encoded),len(outputs))
        for output in outputs:
            output.put(encoded)
def out_writer(conn,q):
    while True:
        try:
            content = q.get()
            # log.info('Writing to %s %sB', conn,len(content)+1)
            conn.sendall(content)
            conn.sendall(b'\000')
        except Exception:
            log.exception("Failed during send")
            conn.close()
            break

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