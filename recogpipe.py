#! /usr/bin/env python3
from deepspeech import Model, version
import logging, os, sys, select, json, socket, queue
import numpy as np
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
        default=''
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

def write_queue(queue, output):
    """run the write queue"""
    while True:
        record = queue.get()
        # log.info("%s %s", '...' if record['partial'] else '>>>', record['text'])
        content = json.dumps(record)
        # output.write(content)
        # output.write('\n')

def metadata_to_json(metadata, partial=False):
    struct = {
        'partial': partial,
        'transcripts': [],
    }
    for transcript in metadata.transcripts:
        struct['transcripts'].append(transcript_to_json(transcript))
    return struct 

def transcript_to_json(transcript, partial=False):
    struct = {
        'partial': partial,
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

class TranscriptionHistory(object):
    def __init__(self):
        self.history = []
    def append(self, transcriptions):
        """Record set of (partial) transcriptions finding stable prefix"""
        self.history.append(transcriptions)
    def reset(self):
        del self.history[:]
    def common_prefix(self, min_count = 3):
        """Report common prefix set with minimum number of common agreements"""
        words = self.history[-1]['transcripts'][0]['words']
        starts = self.history[-1]['transcripts'][0]['word_starts']
        common = len(words)
        for metadata in self.history[-2:-5:-1]:
            otherwords = metadata['transcripts'][0]['words']
            for index,(test,other) in enumerate(zip(words,otherwords)):
                if test != other:
                    common = min((common,index))
                    break 
        return words[:common],starts[:common]



def run_recognition(
    model, input, output, read_size=1024, rate=16000,
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
    ring = RingBuffer(rate=rate)
    max_length = 6*rate # X second max utterance length...
    length = 0
    last_decode = 0
    transcriptions = [
        # (start,stop,partial)
    ]
    out_queue = queue.Queue()
    t = threading.Thread(target=write_queue,args=(out_queue,output))
    t.setDaemon(True)
    t.start()
    stream = model.createStream()
    history = TranscriptionHistory()
    def finish():
        if length:
            metadata = stream.finishStreamWithMetadata(5)
            trans = metadata_to_json(metadata, True)
            for tran in trans['transcripts']:
                log.info(">>> %0.02f %s", tran['confidence'],tran['words'])
            out_queue.put(trans)

    while True:
        buffer = ring.read_in(input,read_size)
        written = len(buffer)

        if not written:
            finish()
            stream = model.createStream()
            length = last_decode = 0
            history.reset()
        else:
            length += written 
            stream.feedAudioContent(buffer)
            if (length - last_decode) > rate // max_decode_rate:
                metadata = metadata_to_json(stream.intermediateDecodeWithMetadata())
                history.append(metadata)
                log.info("... %s",' '.join(metadata['transcripts'][0]['words']))
                last_decode = length
                if length > max_length:
                    # try to find a common subset and truncate prefix...
                    words,starts = history.common_prefix()
                    if len(words)>1:
                        out_queue.put({
                            'transcripts': {
                                'words': words[:-1], # we pass the first word back again...
                                'starts': starts[:-1],
                            },
                        })
                        log.info('<<< %s', ' '.join(words))

                        ring.drop_early(starts[-1])
                        log.info('Dropped %0.2fs from start, new length: %s',starts[-1],length)
                        history.reset()
                        stream = model.createStream()
                        length = 0
                        for block in ring.itercurrent():
                            log.info("Re-feeding %s samples %ss",len(block),len(block)/rate)
                            stream.feedAudioContent(block)
                            length += len(block)
                        last_decode = length
            

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

    input = open_fifo(options.input)

    if options.output:
        output = open_fifo(options.output,'w')
    else:
        output = sys.stderr
    run_recognition(model, input, output)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    main()