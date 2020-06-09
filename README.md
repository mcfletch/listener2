# DeepSpeech as a (Docker) Service for IBus

This repository includes the following:

* a Docker container that can run DeepSpeech hardware-accelerated by your
  host OS's (nVidia) graphics card; the container reads audio from a pipe and
  reports results to an event
* an IBus Engine that allows the reslts of the recognition to be treated as
  regular input to the (Linux) host operating system

The current state of the project is that we have a proof of concept
which can type into visual studio code. there will need to be a lot of
work in terms of interpreting the stream of text to allow for a voice coding
excluding breath sounds and the like from being interpreted, and generally
making it a useful tool for desktop use.

## Roadmap

* create a docker container with a working deepspeech release [done]
* get basic working dictation into arbitrary applications working [done]
* create punctuation and control short cuts and phrases
* create a "correct that" GUI (with other predictions and free-form editing)
* create a control panel allowing for one click toggling of listening
* cut down the container to a more reasonable size
* allow for switching language models for different programming contexts

## Installation/Setup

See [Documentation](./docs/installation.rst)

## Testing bits out...

Sending audio to the daemon
```
./ffmpeg-audio.sh hw:1,1
./ffmpeg-sample.sh /path/to/some.wav
```
Viewing the raw transcripts from the daemon
```
nc -U /tmp/dspipe/events
```
Running the ibus engine interactively:
```
./ibusengine.py
```
[![PyPI Version](https://img.shields.io/pypi/v/recogpipe.svg)](https://pypi.python.org/pypi/recogpipe)


