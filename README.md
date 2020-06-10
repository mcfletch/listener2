# Voice Dictation as a (Docker) Service for IBus

My goal with this project is to create an input method for those who
have difficulty typing with their hands, with a focus on allowing
coding by voice on Linux Desktops. I am *not* attempting to create a
hands free system or personal assistant.

This repository includes the following:

* a Docker container that can run [Mozilla DeepSpeech](https://github.com/mozilla/DeepSpeech) hardware-accelerated by your
  host OS's (NVidia) graphics card; the container reads audio from a pipe and
  reports results to an event-socket
* an IBus Engine that allows the results of the recognition to be treated as
  regular input to the (Linux) host operating system

The current state of the project is that we have a proof of concept
which can type into visual studio code, kate, and Google Chrome. There will need to be a lot of
work in terms of interpreting the stream of text to allow for:

* providing basic puctuation, capitalisation, etc
* excluding breath sounds and the like from being interpreted
* generally making it a useful tool for desktop use
* allowing for editing/correcting utterances
* voice coding

## Roadmap

* create a docker container with a working deepspeech release [done]
* get basic working dictation into arbitrary applications working [done]
* create a control-panel application
* create punctuation and control short cuts and phrases
* track interaction and key press events to allow for pauses in dictation 
  without jamming words together
* create a "correct that" GUI (with other predictions and free-form editing)
* create a control panel allowing for one click toggling of listening
* cut down the container to a more reasonable size
* allow for switching language models for different programming contexts

[![PyPI Version](https://img.shields.io/pypi/v/recogpipe.svg)](https://pypi.python.org/pypi/recogpipe)

## Installation/Setup

See [Installation Docs](./docs/installation.rst)

## Reference Docs for Devs

* [IBus](https://lazka.github.io/pgi-docs/IBus-1.0/index.html)
* [DeepSpeech](https://deepspeech.readthedocs.io/en/latest/Python-API.html)
* [Pyside2](https://doc.qt.io/qtforpython/modules.html)
