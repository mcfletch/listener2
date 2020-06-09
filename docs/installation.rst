.. highlight:: shell

Installation
============

Requirements:

* nvidia graphic card for running the deep speech model
* docker-ce run time installed
* your user able to run docker containers
* all of the dependencies in dependencies.txt installed
* IBus enabled on your desk top

Get the source code::

    git clone https://github.com/mcfletch/deepspeech-docker.git
    cd deepspeech-docker

Start the daemon in a docker container::

    ./recogpipe/dockersetup.py
    # when docker container is started...
    ./recogpipe/daemon.py

Feed some data into the daemon from your ALSA microphone::

    ffmpeg-audio.sh hw:1,0

Feed some data into the daemon from a wav file::

    ffmpeg-sample.sh path/to/your/file.wav

Running the IBus daemon on your desktop (not in the docker container)::

    apt install $(cat dependencies.txt)
    # Enable IBus in your desktop, in KDE run `IBus Preferences`
    ./recogpipe/ibusengine.py

