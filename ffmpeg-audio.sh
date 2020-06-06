#! /bin/bash

# Dumps default audio to pcm-coded 16-bit mono
ffmpeg -f alsa -i hw:0,0 -ac 1 -f u16le -o /tmp/dspipe/audio
