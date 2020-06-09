.. highlight:: shell

Installation
============

Requirements:

* nvidia graphic card using the proprietary driver for running the deep speech model(s)
* docker-ce runtime installed
* your user able to run docker containers
* all of the dependencies in `dependencies.txt` installed
* IBus enabled on your desktop

Get the source code::

    git clone https://github.com/mcfletch/deepspeech-docker.git
    cd deepspeech-docker

Start the Docker Service
-------------------------

The docker service is setup and managed by a script called `recogpipe-docker`
which arranges for the model files to be downloaded and cached,
builds the docker container, and then runs it::

    # Note, depends on having the dependencies listed in 
    # `dependencies.txt` installed
    python3 setup.py develop --user
    recogpipe-docker

Note: your user must be in both the `docker` and `video` groups
to allow you to start docker containers and access the nvidia graphics
card.

Piping Audio Into the Daemon
----------------------------

Feed some data into the daemon from your ALSA microphone::

    ffmpeg-audio.sh hw:1,0

You can find the hardware identifier for your microphone by running::

    mcfletch@tanis:~/ai-dev/deepspeech-docker$ arecord -l
    **** List of CAPTURE Hardware Devices ****
    card 0: PCH [HDA Intel PCH], device 0: CX8070 Analog [CX8070 Analog]
    Subdevices: 1/1
    Subdevice #0: subdevice #0
    card 1: DSP [Plantronics .Audio 626 DSP], device 0: USB Audio [USB Audio]
    Subdevices: 0/1
    Subdevice #0: subdevice #0he

Here there are two capture 
devices available, the first being a built in analog microphone and the second 
being a cheap Plantronics USB headset microphone.
For each entry the values `Card 0` and `device 0` tell you a hardware
identifier, `hw:0,0` and `hw:1,0` respectively. 

Alternately, feed some data into the daemon from a wav file (transcribe it)::

    ffmpeg-sample.sh path/to/your/file.wav

note that the audio will begin transcribing immediately, so you will,
likely lose the first few utterances.

Debugging
..........

Viewing the raw transcripts from the dockerised daemon with netcat::

    nc -U /run/user/`id -u`/recogpipe/events

Running the ibus engine interactively::

    recogpipe-ibus -v


IBus (Input Method Engine)
--------------------------

Running the IBus daemon on your desktop (not in the docker container)::

    apt install $(cat dependencies.txt)
    # Enable IBus in your desktop, in KDE run `IBus Preferences`
    # See Below for details
    recogpipe-ibus


IBus Running on your Desktop
.............................

If you see a message from the IBus demon telling you that it
does not have a connection review the [instructions from Arch Linux](https://wiki.archlinux.org/index.php/IBus#Initial_setup)
on how to make the demon start on login to your desktop.

You will need to add parameters to your profile environment
confirm that you have also installed all of the dependencies
listed in the dependencies.txt in the root of the source tree.

If IBus is not Dictating into an Application
.............................................

The input method system for IBus relies on integrations provided
by the toolkit used by the application. Chrome and most Electron
applications use some version of GTK. KDE/Plasma and Qt based 
desktops use Qt. The dependencies listed should have installed
integrations for GTK-based applications, note that you will need to
restart the applications entirely in order to pick up the IBus 
entry methods.
