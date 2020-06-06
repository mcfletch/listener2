#! /usr/bin/python
import subprocess, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
DSPIPE = '/tmp/dspipe'


def main():
    images = subprocess.check_output(['docker','images','deepspeech-client']).decode('utf-8').strip().splitlines()
    if len(images) < 2:
        command = [
            'docker','build','-t','deepspeech-client',HERE,
        ]
        subprocess.check_call(command)
    if not os.path.exists(DSPIPE):
        os.makedirs(DSPIPE)
    command = [
        'docker','run',
        '-it',
        '--device','/dev/dri/card1',
        '--device','/dev/dri/renderD129',
        '-v%s:%s'%(DSPIPE,DSPIPE),
        '-v%s:/src/home/working'%(HERE,),
        '--user','deepspeech',
        'deepspeech-client','/bin/bash'
    ]
    subprocess.check_call(command)

if __name__ == "__main__":
    main()
