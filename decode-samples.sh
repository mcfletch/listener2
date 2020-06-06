#! /bin/bash

deepspeech \
    --model ../model/deepspeech-0.7.1-models.pbmm \
    --scorer ../model/deepspeech-0.7.0-models.scorer \
    --json \
    --candidate_transcripts 2 \
    --audio ./this-is-a-test.wav
