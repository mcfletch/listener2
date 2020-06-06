#! /usr/bin/python
import subprocess, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
PARENT = os.path.abspath(os.path.join(HERE,'..'))

def main():
    images = subprocess.check_output(['docker','images','deepspeech-client']).decode('utf-8').strip().splitlines()
    if len(images) < 2:
        command = [
            'docker','build','-t','deepspeech-client',HERE,
        ]
        subprocess.check_call(command)
    command = [
        'docker','run',
        '-it',
        '--device','/dev/dri/card1',
        '--device','/dev/dri/renderD129',
        '-v%s:/src/home/working'%(PARENT,),
        'deepspeech-client','/bin/bash'
    ]
    subprocess.check_call(command)

if __name__ == "__main__":
    main()
