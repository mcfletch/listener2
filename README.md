# Listener (v2) Voice Dictation as a (Docker) Service for IBus

Listener is a voice dictation service for Linux desk tops
which uses the Mozilla Deep Speech  engine to provide the
basic recognition services and focuses on providing
sufficient  accuracy and services to allow for coding
common programming languages.

My goal with this project is to create an input method for those who
have *difficulty* typing with their hands (such as myself), with a 
focus on allowing coding by voice. My  personal focus is not
to allow for hands free operation of the machine.

## Current Status of the Project

The current state of the project is a proof of concept, what works:

* typing content into visual studio code, kate, and google chrome
* the start of basic punctuation capitalization et cetera  driven by
  user editable rules files

## Roadmap

* create a docker container with a working deepspeech release [done]
* get basic working dictation into arbitrary applications working [done]
* create a control-panel application [started]
* create punctuation and control short cuts and phrases  [mostly done]
* create language models which are  dictation aware, so that the common
  dictation short cuts such as `cap X`  have higher priorities [started]
* maybe create an DBus service for the core code [started]
* allow for switching language models for different programming contexts and providing
  current-context hints such as class methods, modules, etc from the language server
* track interaction and key press events to allow for pauses in dictation without extra spaces
   this will have to happen in the IBus  component in order to get proper notification
* send special keys (tab, enter, and modifiers to start with) [proof of concept done]
* create a "correct that" GUI (with other predictions and free-form editing)
* create a control panel allowing for one click toggling of listening
* cut down the container to a more reasonable size

## Architecture

* listener-audio runs pacat to send raw audio to a named socket
* a docker container runs [Mozilla DeepSpeech](https://github.com/mozilla/DeepSpeech) 
  hardware-accelerated by your host OS's (NVidia) graphics card

  * the container reads the audio from a pipe and reports results to a 
    user-local event-socket

* a listener-interpreter process listens to the event  and attempts to 
  interpret the results according to the user's rules,  and eventually 
  custom language models and contextual biasing/hinting (think autocomplete)
* a DBus service takes the results of the recognition and converts them to
  regular input to the (Linux) host operating system, using uinput for 
  special character injection (think `Alt-Tab`, navigation and the like)

## Quick Start

Since there is not yet a working graphically user interface the set up is not as
friendly as commercial voice dictation solutions.
```
sudo apt install $(cat dependencies.txt)
virtualenv -p python3 listener-env
source listener-env/bin/activate
pip install -r requirements.txt
# following will download the (large) language model to cache
# before starting the docker container
listener-docker
# Feed raw audio into the recognition daemon
listener-audio &
# Interpret the raw recognition events as commands and text
listener-interpreter &
# Send the commands and text to the Linux Desktop via IBus
listener-ibus &
```


## Installation/Setup

See [Installation Docs](./docs/installation.rst) for full installation instructions...

## Reference Docs for Devs

* [IBus](https://lazka.github.io/pgi-docs/IBus-1.0/index.html)
* [DeepSpeech](https://deepspeech.readthedocs.io/en/latest/Python-API.html)
* [Pyside2](https://doc.qt.io/qtforpython/modules.html)

## Research to Explore

* [Biasing by Context](https://static.googleusercontent.com/media/research.google.com/en//pubs/archive/43819.pdf) -- Instead of having to train language models for each context-type
* [Big Code not Big Vocabulary](https://arxiv.org/abs/2003.07914) [Code](https://github.com/mast-group/OpenVocabCodeNLM)
* [Suggesting Accurate Method and Class Names](https://miltos.allamanis.com/publications/2015suggesting/)

[![PyPI Version](https://img.shields.io/pypi/v/listener.svg)](https://pypi.python.org/pypi/listener)

