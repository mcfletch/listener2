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

    git clone https://github.com/mcfletch/listener2.git
    cd listener2

Start the Docker Service
-------------------------

The docker service is setup and managed by a script called `listener-docker`
which arranges for the model files to be downloaded and cached,
builds the docker container, and then runs it::

    # Note, depends on having the dependencies listed in 
    # `dependencies.txt` installed
    python3 setup.py develop --user
    listener-docker

Note: your user must be in both the `docker` and `video` groups
to allow you to start docker containers and access the nvidia graphics
card.

Piping Audio Into the Daemon
----------------------------

The `listener-audio` application runs `pacat` to send pulseaudio
content to the daemon. You can also look at the `ffmpeg-audio.sh`
script if you'd like to devise a different method for sending the
content to the docker daemon.

Change the Audio Source 
........................

`listener-audio` is using pacat, so you can
control the input via your desktop's standard Pulse Audio 
controls.

On KDE desktops, to change the microphone used, run:

* `listener-docker`
* `listener-audio`

then right-click on your audio icon in the systray, choose 
`Configure Audio Volume | Audio Volume | Applications` and next to 
`listener-microphone: recogniser` choose your preferred input 
for the audio.

Debugging
..........

Viewing the logs of the transcripts from within the daemon::

    docker logs "listener_${USER}"

Viewing the raw transcripts from the dockerised daemon with netcat::

    nc -U /run/user/`id -u`/listener/events


IBus (Input Method Engine)
--------------------------

Running the IBus daemon on your desktop (not in the docker container)::

    apt install $(cat dependencies.txt)
    # Enable IBus in your desktop, in KDE run `IBus Preferences`
    # See Below for details
    listener-ibus



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
