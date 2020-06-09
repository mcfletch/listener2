#! /usr/bin/env python3
"""Qt GUI Application for controlling RecogPipe"""
from PySide2 import QtCore, QtGui, QtWidgets, QtMultimedia
from . import systrayicon
import sys, os, logging
HERE = os.path.dirname(os.path.abspath((__file__)))


class RecogPipeApp(QtWidgets.QApplication):
    def __init__(self, argv, *args, **named):
        super(RecogPipeApp,self).__init__(argv)
        self.load_config()
        self.create_systray()
        self.create_audio_pipe()
        self.create_event_listener()
        self.history = []

    def load_config(self):
        """Get the application's configuration"""


    def create_systray(self):
        self.systray = systrayicon.RecogPipeSystrayIcon()
        self.systray.set_state('stopped')

    def check_container(self):
        """Check if the container service is running"""

    def create_audio_pipe(self):
        """Eventually should do this with QtMultimedia"""
        self.audio_pipe = pipe = QtCore.Process()
        # TODO: make the daemon use tcp or unix domain sockets... unix:/tmp/ffmpeg.socket
        hw = 'hw:1,0'
        uid = os.geteuid()
        pipe.start( '/bin/bash',[
            '-c',
            "ffmpeg -f alsa -i %(hw)s -ac 1 -ar 16000 -f s16le -acodec pcm_s16le pipe:1 >  /run/user/%(uid)s/recogpipe/audio"%locals()
        ])
        pipe.connect('finished', self.on_audio_pipe_exit)
    def on_audio_pipe_exit(self, *args):
        log.warning("Audio pipe exited, restarting")
        # TODO: should validate that the target is up...
        self.create_audio_pipe()
        
    def create_event_listener(self):
        """Read json events from event source"""
        


log = logging.getLogger(__name__)
def get_options():
    import argparse 
    parser = argparse.ArgumentParser(
        description='RecogPipe GUI front-end in PySide2'
    )
    parser.add_argument(
        '-v','--verbose',
        default=False,
        action='store_true',
        help='Enable verbose logging (for developmen/debugging)',
    )
    return parser

def main():
    options = get_options().parse_args()
    logging.basicConfig(
        level=logging.DEBUG if options.verbose else logging.WARNING,
        format='%(levelname) 7s %(name)s:%(lineno)s %(message)s',
    )
    app = RecogPipeApp([])

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
