#! /usr/bin/env python3
"""Qt GUI Application for controlling Listener"""
import sys, os, logging, subprocess, threading, time, json
from PySide2 import QtCore, QtGui, QtWidgets, QtMultimedia
from . import systrayicon, mainview, dictationoverlay, actions, qmicrophone
from .. import defaults, registerdbus, models
import dbus
import dbus.mainloop.glib

HERE = os.path.dirname(os.path.abspath((__file__)))


class ListenerApp(QtWidgets.QApplication):
    wanted = True
    AUDIO_SETTINGS_CHANGED = QtCore.Signal()
    audio_pipeline = None

    def __init__(self, argv, *args, **named):
        super(ListenerApp, self).__init__(argv)
        self.load_config()
        self.create_actions()

        self.audio_hw = 'hw:1,0'
        self.check_ibus()
        self.create_systray()
        self.create_event_listener()
        self.history = []
        self.main_view = mainview.ListenerView()
        self.main_view.showMaximized()
        self.get_service()
        self.create_overlay()
        # self.create_microphone()
        self.AUDIO_SETTINGS_CHANGED.connect(self.on_audio_settings_changed)

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
        self.setOrganizationName("VRPlumber")
        self.setOrganizationDomain("vrplumber.com")
        self.setApplicationName(defaults.APP_NAME_HUMAN)
        self.settings = QtCore.QSettings()

    def create_systray(self):
        self.systray = systrayicon.ListenerSystrayIcon()
        self.systray.setToolTip(defaults.APP_NAME_HUMAN)
        self.systray.set_state('stopped')
        self.systray.activated.connect(self.on_icon_click,)
        self.systray.show()
        menu = QtWidgets.QMenu()
        action = menu.addAction(QtGui.QIcon('exit'), 'Quit Listener',)
        action.setStatusTip('Exit listener')
        action.triggered.connect(self.cleanup)
        # QtGui.QKeySequence(QtGui.QKeySequence.StandardKey.Quit)

        self.systray.setContextMenu(menu)

    def create_microphone(self):
        """Create our microphone pipeline"""
        self.microphone = qmicrophone.Microphone(None,)
        self.microphone.on_go_live()

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
        # bus_name = dbus.BusName(defaults.DBUS_NAME, bus=self.dbus_bus)
        # self.dbus_bus.connect()

        remote_object = self.dbus_bus.get_object(
            defaults.DBUS_NAME, defaults.DBUS_INTERPRETER_PATH,
        )
        iface = dbus.Interface(remote_object, defaults.DBUS_NAME)
        log.info("Interface: %s", iface)
        self.dbus_bus.add_signal_receiver(
            self.on_partial_result, dbus_interface=defaults.PARTIAL_RESULT_EVENT,
        )
        self.dbus_bus.add_signal_receiver(
            self.on_final_result, dbus_interface=defaults.FINAL_RESULT_EVENT,
        )

    def on_partial_result(self, utterance_struct):
        """Handle a partial result utterance"""
        utterance = models.Utterance.from_dbus_struct(utterance_struct)
        # TODO: this is coming in on glib, but is it actually in the gui thread?
        self.overlay.set_text(' '.join(utterance.best_guess().words), 1000)

    def on_final_result(self, utterance_struct):
        utterance = models.Utterance.from_dbus_struct(utterance_struct)
        self.overlay.set_text(' '.join(utterance.best_guess().words), 2000)

    def create_overlay(self):
        window = dictationoverlay.DictationOverlay()
        window.set_text('%s dictation overlay' % (defaults.APP_NAME_SHORT))
        saved_position = self.settings.value(window.GEOMETRY_SAVE_KEY)
        if saved_position:
            window.restoreGeometry(saved_position)
        self.overlay = window

    def create_actions(self):

        self.start_listening = actions.standard_action(
            self,
            title='Start Listening',
            icon='panel-icon-recording',
            help_text='Start listening and dictating text',
            callback=self.on_start_listening,
            shortcut='Ctrl+L',
        )
        self.stop_listening = actions.standard_action(
            self,
            title='Stop Listening',
            icon='panel-icon-paused',
            help_text='Stop listening and dictating text',
            callback=self.on_stop_listening,
            shortcut='Ctrl+Shift+L',
        )
        self.reposition_overlay = actions.standard_action(
            self,
            title='Reposition Overlay',
            icon='video-display',
            help_text='Show the dictation overlay so that it can be moved/repositioned',
            callback=self.on_reposition_overlay,
        )

    def on_start_listening(self, evt=None, **args):
        """Tell the service to start listening"""
        log.info("Start listening request")
        self.main_view.status_bar.showMessage('Start Listening...')
        self.systray.set_state('start-listening')

    def on_stop_listening(self, evt=None, **args):
        """Tell the service to start listening"""
        log.info("Stop listening request")
        self.main_view.status_bar.showMessage('Stop Listening...')
        self.systray.set_state('stop-listening')

    def on_reposition_overlay(self, evt=None, **args):
        """Ask the overlay to show without closing immediately"""
        self.overlay.show_for_reposition()

    def on_audio_settings_changed(self):
        """Handle a change to our audio settings (potentially restarting audio)"""
        enabled = self.settings.value(defaults.MICROPHONE_ENABLED_KEY) or ''
        log.info("Raw enabled value %r", enabled)
        if isinstance(enabled, str):
            enabled = enabled.lower() in ('true', 'yes', 'on')
        volume = int(self.settings.value(defaults.MICROPHONE_VOLUME_KEY) or 99)
        source = self.settings.value(defaults.MICROPHONE_PREFERENCE_KEY)

        if enabled:
            command = ['listener-audio', '-v']
            if source:
                command.extend(['-d', source])
            if (
                self.audio_pipeline
                and self.audio_pipeline.command == command
                and self.audio_pipeline.poll() is None
            ):
                log.info("No update to audio pipeline")
                return
            log.info("Restarting audio pipeline")
            self.stop_audio()
            self.audio_pipeline = subprocess.Popen(command)
        else:
            log.info("Stopping audio pipeline")
            self.stop_audio()

    def stop_audio(self):
        """Stop our audio pipeline"""
        if self.audio_pipeline:
            self.audio_pipeline, audio_pipeline = (None, self.audio_pipeline)
            audio_pipeline.kill()
            return True
        return False

    def ensure_container(self):
        """Ensure the container is running"""
        status = self.get_container_status()
        if not status:
            self.main_view.showMessage(
                'Container is not currently running, attempting to build and start it'
            )
            subprocess.check_output(['listener-docker'])
            status = self.get_container_status()
            if not status:
                self.main_view.status_bar.setStatusTip(
                    'Could not start the docker container'
                )
                return
        for structure in status:
            status = structure['State']['Status']
            label = '%s: %s' % (defaults.DOCKER_CONTAINER, status)
            self.main_view.container_view.container_name.setText(label)

    def get_container_status(self):
        """Run docker inspect to get the current container information"""
        try:
            output = subprocess.check_output(
                ['docker', 'inspect', defaults.DOCKER_CONTAINER,]
            )
        except subprocess.CalledProcessError as err:
            return []
        else:
            return json.loads(output)


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
    registerdbus.register_dbus()
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    defaults.setup_logging(options)
    icon_search_paths = QtGui.QIcon.fallbackSearchPaths() + [
        os.path.join(defaults.LISTENER_SOURCE, 'static')
    ]

    QtGui.QIcon.setFallbackSearchPaths(icon_search_paths)
    app = ListenerApp([])
    t = threading.Thread(target=app.ensure_container)
    t.setDaemon(True)
    t.start()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
