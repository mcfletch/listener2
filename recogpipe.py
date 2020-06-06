#! /usr/bin/env python3
from deepspeech import Model, version
import logging, os, sys, select, json
import numpy as np
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
        content = json.dumps(record)
        output.write(content)

def run_recognition(model, input, output, read_size=512):
    """Read fragments from input, write results to output
    
    model -- DeepSpeech model to run 
    input -- input binary audio stream 16KHz mono 16-bit unsigned machine order audio
    output -- output (text) stream to which to write updates
    rate -- audio rate (16,000 to be compatible with DeepSpeech)
    read_ms -- how much data to read on each update
    buffer_s -- how much total space to save in the buffer

    """
    # create our ring-buffer structure with 60s of audio
    current_content = np.zeros((512,),dtype=np.int16)
    max_length = 20*16000 # 20 second max utterance length...
    write_head = 0
    start_head = 0
    length = 0
    transcriptions = [
        # (start,stop,partial)
    ]
    out_queue = queue.Queue()
    while True:
        written = input.readinto(current_content)
        if not written:
            if length:
                out_queue.put(stream.finishStreamWithMetadata())
                stream = model.create_stream()
            readable = []
            while not readable:
                readable,writable,errable = select.select([input],[],[],timeout=1.0)
        else:
            length += written 
            stream.feedAudioContent(current_content[:written])
            if length > max_length:
                out_queue.put(stream.finishStreamWithMetadata())
                stream = model.create_stream()
            else:
                out_queue.push(stream.intermediateDecodeWithMetadata())

def main():
    options = get_options().parse_args()
    model = Model(
        options.model,
    )
    if options.beam_width:
        model.setBeamWidth(options.beam_width)
    desired_sample_rate = ds.sampleRate()
    log.info("Need a sample rate of %s", desired_sample_rate)
    model.enableExternalScorer(options.scorer)
    input = open_fifo(options.input,'rb')
    if options.output:
        output = open_fifo(options.output,'w')
    else:
        output = sys.stderr
    run_recognition(model, input, output)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    main()