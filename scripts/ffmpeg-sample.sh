#! /bin/bash
# Dumps default audio to pcm-coded 16-bit mono
FILENAME=${1:-'samples/this-is-a-test.wav'}
ffmpeg -i "${FILENAME}" -ac 1 -ar 16000 -f s16le -acodec pcm_s16le pipe:1 >  /run/user/`id -u`/listener/audio
