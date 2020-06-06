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
        log.info("%s %s", '...' if record['partial'] else '>>>', record['text'])
        content = json.dumps(record)
        # output.write(content)
        # output.write('\n')

def transcript_to_json(transcript, partial=False):
    struct = {
        'partial': partial,
        'tokens': [],
        'starts': [],
        'confidence': transcript.confidence,
    }
    text = []
    starts = 0.0
    for token in transcript.tokens:
        struct['tokens'].append(token.text)
        text.append(token.text)
        struct['starts'].append(token.start_time)
    struct['text'] = ''.join(text)
    return struct


def run_recognition(model, input, output, read_size=512, rate=16000):
    """Read fragments from input, write results to output
    
    model -- DeepSpeech model to run 
    input -- input binary audio stream 16KHz mono 16-bit unsigned machine order audio
    output -- output (text) stream to which to write updates
    rate -- audio rate (16,000 to be compatible with DeepSpeech)
    read_ms -- how much data to read on each update
    buffer_s -- how much total space to save in the buffer

    """
    # create our ring-buffer structure with 60s of audio
    current_content = np.zeros((1024,),dtype=np.int16)
    max_length = 5*rate # 20 second max utterance length...
    write_head = 0
    start_head = 0
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
    while True:
        written = input.readinto(current_content)
        written = written // 2 # 16-bit
        if not written:
            if length:
                metadata = stream.finishStreamWithMetadata()
                trans = transcript_to_json(metadata.transcripts[0])
                out_queue.put(trans)
                log.info("Input stopped, reporting: %s", trans)
                stream = model.createStream()
                length = 0
        else:
            length += written 
            stream.feedAudioContent(current_content[:written])
            # log.info("Have read %s", length)
            if length > max_length:
                log.info("Length exceeded, next stream")
                metadata = stream.finishStreamWithMetadata()
                trans = transcript_to_json(metadata.transcripts[0])
                out_queue.put(trans)

                stream = model.createStream()
                length = 0
            elif (length - last_decode) > rate//4:
                # See what we can parse...
                last_decode = length
                metadata = stream.intermediateDecodeWithMetadata()
                # if metadata.transcripts[0].confidence > .9 and not metadata.transcripts[0].tokens and length > 32000:
                #     log.info("Nothing recognised in %s samples", length)
                #     stream.freeStream()
                #     stream = model.createStream()
                #     length = 0
                # else:
                trans = transcript_to_json(metadata.transcripts[0])
                log.info("... %s", trans['text'])
                out_queue.put(trans)

def main():
    options = get_options().parse_args()
    model = Model(
        options.model,
    )
    if options.beam_width:
        model.setBeamWidth(options.beam_width)
    desired_sample_rate = model.sampleRate()
    log.info("Need a sample rate of %s", desired_sample_rate)
    model.enableExternalScorer(options.scorer)
    # sock = socket.socket(socket.AF_UNIX|socket.SOCK_NONBLOCK, socket.SOCK_STREAM)
    # sock.bind(options.input)
    # while True:
    #     connection, client_address = sock.accept()

    input = open_fifo(options.input)

    if options.output:
        output = open_fifo(options.output,'w')
    else:
        output = sys.stderr
    run_recognition(model, input, output)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    main()