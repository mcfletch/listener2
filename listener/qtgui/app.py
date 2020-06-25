#! /usr/bin/env python3
"""Qt GUI Application for controlling Listener"""
import sys, os, logging, subprocess, threading, time
from PySide2 import QtCore, QtGui, QtWidgets, QtMultimedia
from . import systrayicon, mainview
import dbus
import dbus.mainloop.glib

HERE = os.path.dirname(os.path.abspath((__file__)))


class ListenerApp(QtWidgets.QApplication):
    wanted = True

    def __init__(self, argv, *args, **named):
        super(ListenerApp, self).__init__(argv)
        self.load_config()
        self.audio_hw = 'hw:1,0'
        self.check_ibus()
        self.create_systray()
        self.create_event_listener()
        self.history = []
        self.main_view = mainview.ListenerView()
        # self.start_pipe(self.run_audio_pipe)
        # self.start_pipe(self.run_ibus_engine)
        self.main_view.showMaximized()
        self.get_service()

    def cleanup(self):
        self.wanted = False
        self.quit()

    def check_ibus(self):
        """Is our IBus daemon running?"""
        address = subprocess.check_output(['ibus', 'address']).decode('ascii', 'ignore')
        if address.strip() == '(null)':
            log.warning("IBus daemon does not seem to be running, attempting to start")
            command = [
                'ibus-daemon',
                '-d',
                '-n',
                os.environ.get('DESKTOP_SESSION', 'plasma'),
                '-r',
                '-v',
            ]
            log.debug("Daemon spawn command: %s", " ".join(command))
            subprocess.check_call(command)
        else:
            log.info("IBus running at %r", address)

    def load_config(self):
        """Get the application's configuration"""

    def create_systray(self):
        self.systray = systrayicon.ListenerSystrayIcon()
        self.systray.set_state('stopped')
        self.systray.activated.connect(self.on_icon_click,)
        self.systray.show()
        menu = QtWidgets.QMenu()
        action = menu.addAction(QtGui.QIcon('exit'), 'Quit Listener',)
        action.setStatusTip('Exit listener')
        action.triggered.connect(self.cleanup)
        # QtGui.QKeySequence(QtGui.QKeySequence.StandardKey.Quit)

        self.systray.setContextMenu(menu)

    def check_container(self):
        """Check if the container service is running"""

    def start_pipe(self, target, *args):
        """Create thread with our audio-pipe minder"""
        thread = threading.Thread(target=target, args=args)
        thread.setDaemon(True)
        thread.start()

    def run_ibus_engine(self):
        while self.wanted:
            command = [
                'listener-ibus',
                '-v',
            ]
            pipe = subprocess.Popen(command,)
            while pipe.poll() is None and self.wanted:
                time.sleep(1.0)

    def run_audio_pipe(self):
        while self.wanted:
            command = [
                'listener-audio',
            ]
            pipe = subprocess.Popen(command,)
            while pipe.poll() is None and self.wanted:
                time.sleep(1.0)

    def create_event_listener(self):
        """Read json events from event source"""

    def on_icon_click(self, evt, *args):
        """Handle the user clicking on the icon"""
        log.info("Clicked on the icon")
        if self.main_view.isVisible():
            self.main_view.hide()
        else:
            self.main_view.showMaximized()

        return True

    def get_service(self):
        """Get a DBus proxy to our ListenerService"""
        self.dbus_bus = dbus.SessionBus()
        remote_object = self.dbus_bus.get_object(
            "com.example.SampleService", "/DBusWidget"
        )
        iface = dbus.Interface(remote_object, "com.example.SampleWidget")
        import ipdb

        ipdb.set_trace()


log = logging.getLogger(__name__)


def get_options():
    import argparse

    parser = argparse.ArgumentParser(description='Listener GUI front-end in PySide2')
    parser.add_argument(
        '-v',
        '--verbose',
        default=True,
        action='store_true',
        help='Enable verbose logging (for development/debugging)',
    )
    return parser


def main():
    options = get_options().parse_args()
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    logging.basicConfig(
        level=logging.DEBUG if options.verbose else logging.WARNING,
        format='%(levelname) 7s %(name)s:%(lineno)s %(message)s',
    )
    app = ListenerApp([])

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
