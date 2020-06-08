#! /usr/bin/python
import subprocess, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
DSPIPE = '/tmp/dspipe'
DEFAULT_INPUT = os.path.join(DSPIPE,'audio')
DEFAULT_OUTPU = os.path.join(DSPIPE,'results')

def get_options():
    import argparse
    parser = argparse.ArgumentParser(description='Run DeepSpeech in a container')
    parser.add_argument(
        '-c','--card',
        default = 1,
        type = int,
        help='Which video card (0-indexed) to use for the GPU in the container',
    )
    parser.add_argument(
        '-d','--directory',
        default = DSPIPE,
        help='Directory in which to mount audio input pipe, default: %s'%(DSPIPE,)
    )
    parser.add_argument(
        '-b','--build',
        default=False,
        action='store_true',
        help='If specified, force rebuilding of the docker image',
    )
    return parser

def main():
    options = get_options().parse_args()
    images = subprocess.check_output(['docker','images','deepspeech-client']).decode('utf-8').strip().splitlines()
    if options.build or len(images) < 2:
        command = [
            'docker','build','-t','deepspeech-client',HERE,
        ]
        subprocess.check_call(command)
    if not os.path.exists(options.directory):
        os.makedirs(options.directory)
    command = [
        'docker','run',
        '-it',
        '--device','/dev/dri/card%d'%(options.card,),
        '--device','/dev/dri/renderD%d'%(128+options.card,),
        '-v%s:%s'%(options.directory,DSPIPE),
        '-v%s:/src/home/working'%(HERE,),
        '--user','deepspeech',
        'deepspeech-client','/bin/bash'
    ]
    os.execvp(command[0],command)

if __name__ == "__main__":
    main()
