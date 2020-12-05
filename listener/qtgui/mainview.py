import logging, os
from PySide2.QtWidgets import (
    QMainWindow,
    QVBoxLayout,
    QSizeGrip,
    QStatusBar,
    QMdiArea,
    QMenuBar,
    QMenu,
    QDockWidget,
    QVBoxLayout,
)
from PySide2.QtCore import Qt
from .. import defaults
from . import icons, actions, audioview, appref, containersettings

log = logging.getLogger(__name__)


class ListenerView(QMainWindow):
    def __init__(self, *args):
        super(ListenerView, self).__init__(*args)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.window_branding()

        self.create_menu()
        self.create_main()
        self.create_status()

        self.create_container_view()
        self.create_audio_view()

    app = property(appref.app)

    def window_branding(self):
        """Setup our general branding for the window"""
        self.setWindowTitle(defaults.APP_NAME_HUMAN)
        self.setWindowIcon(icons.get_icon("microphone"))

    def create_menu(self):
        """Create the overall application menu"""
        self.menu = QMenuBar()
        app = self.app
        self.dictation_menu = self.menu.addMenu('&Dictation')
        self.dictation_menu.addAction(app.start_listening)
        self.dictation_menu.addAction(app.stop_listening)
        self.dictation_menu.addAction(app.reposition_overlay)
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

    def create_audio_view(self):
        """Create the audio control view"""
        self.audio_dock = QDockWidget("Audio", self)
        self.audio_dock.setFloating(False)
        self.audio_view = audioview.ListenerAudio(self)
        self.audio_dock.setWidget(self.audio_view)
        self.addDockWidget(
            Qt.LeftDockWidgetArea, self.audio_dock,
        )

    def create_container_view(self):
        """Create the container view"""
        self.container_dock = QDockWidget("Container", self)
        self.container_dock.setFloating(False)
        self.container_view = containersettings.ContainerSettings(self)
        self.container_dock.setWidget(self.container_view)
        self.addDockWidget(
            Qt.LeftDockWidgetArea, self.container_dock,
        )
