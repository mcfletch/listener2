#! /bin/bash

# Dumps default audio to pcm-coded 16-bit mono
parec \
    --rate 16000 \
    --format s16le \
    --channels 1 \
    --raw \
    --record \
    --client-name recgpipe-microphone \
    --stream-name primary \
    /run/user/`id -u`/listener/audio
