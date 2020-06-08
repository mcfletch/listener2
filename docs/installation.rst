.. highlight:: shell

============
Installation
============


Get the source code::

    git clone https://github.com/mcfletch/deepspeech-docker.git
    cd deepspeech-docker

Start the daemon in a docker container::

    ./recogpipe/dockersetup.py
    # when docker container is started...
    ./recogpipe/daemon.py

Feed some data into the daemon from your microphone::

    ffmpeg-audio.sh 

Feed some data into the daemon from a wav file::

    ffmpeg-sample.sh path/to/your/file.wav

Running the IBus daemon on your desktop (not in the docker container)::

    apt install $(cat dependencies.txt)
    ./recogpipe/ibusengine.py

