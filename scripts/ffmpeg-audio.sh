#! /bin/bash

arecord -l
DEVICE=${1:-'hw:1,0'}
# Dumps default audio to pcm-coded 16-bit mono
ffmpeg -f alsa -i ${DEVICE} -ac 1 -ar 16000 -f s16le -acodec pcm_s16le pipe:1 >  /run/user/`id -u`/listener/audio
