#! /bin/bash

# Dumps default audio to pcm-coded 16-bit mono
ffmpeg -f alsa -i hw:0,0 -ac 1 -ar 16000 -f s16le -acodec pcm_s16le pipe:1 >  /tmp/dspipe/audio
