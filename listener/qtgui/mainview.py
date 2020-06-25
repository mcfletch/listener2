import logging, os
from PySide2.QtWidgets import (
    QMainWindow,
    QVBoxLayout,
    QSizeGrip,
    QStatusBar,
    QMdiArea,
    QMenuBar,
    QMenu,
)
from .. import defaults
from . import icons, actions

log = logging.getLogger(__name__)


class ListenerView(QMainWindow):
    def __init__(self, *args):
        super(ListenerView, self).__init__(*args)
        self.window_branding()
        self.create_actions()

        self.create_menu()
        self.create_main()
        self.create_status()

    def window_branding(self):
        """Setup our general branding for the window"""
        self.setWindowTitle(defaults.APP_NAME_HUMAN)
        self.setWindowIcon(icons.get_icon("microphone"))

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

    def create_menu(self):
        """Create the overall application menu"""
        self.menu = QMenuBar()
        self.dictation_menu = self.menu.addMenu('&Dictation')
        self.dictation_menu.addAction(self.start_listening)
        self.dictation_menu.addAction(self.stop_listening)

        self.setMenuBar(self.menu)

    def create_main(self):
        """Create our main central widgets"""
        self.mdi = QMdiArea(self)
        self.setCentralWidget(self.mdi)

    def create_status(self):
        """Create our listening status-bar"""
        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage('%s is loading...' % (defaults.APP_NAME_HUMAN))

    def on_start_listening(self, evt=None, **args):
        """Tell the service to start listening"""
        log.info("Start listening request")
        self.status_bar.showMessage('Start Listening...')

    def on_stop_listening(self, evt=None, **args):
        """Tell the service to start listening"""
        log.info("Stop listening request")
        self.status_bar.showMessage('Stop Listening...')

