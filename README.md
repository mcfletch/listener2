# DeepSpeech as a (Docker) Service for IBus

This repository includes the following:

* a Docker container that can run DeepSpeech hardware-accelerated by your
  host OS's (nVidia) graphics card; the container reads audio from a pipe and
  reports results to an event
* an IBus Engine that allows the reslts of the recognition to be treated as
  regular input to the (Linux) host operating system

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


