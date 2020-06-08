# DeepSpeech as a (Docker) Service for IBus

This repository includes the following:

* a Docker container that can run DeepSpeech hardware-accelerated by your
  host OS's (nVidia) graphics card; the container reads audio from a pipe and
  reports results to an event
* an IBus Engine that allows the reslts of the recognition to be treated as
  regular input to the (Linux) host operating system

## Installation/Setup

```
git clone https://github.com/mcfletch/deepspeech-docker.git
cd deepspeech-docker
```
Starting the daemon in a docker container:
```
./recogpipe/dockersetup.py
# when docker container is started...
./recogpipe/daemon.py
```
Feeding some data into the daemon from your microphone:
```
ffmpeg-audio.sh 
```
Feeding some data into the daemon from a wav file:
```
ffmpeg-sample.sh path/to/your/file.wav
```
Running the IBus daemon on your desktop:
```
./recogpipe/ibusengine.py
```


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


