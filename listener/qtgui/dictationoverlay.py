"""Displays partial dictation results in a translucent overlay window"""
import logging
from PySide2.QtWidgets import QMainWindow, QLabel, QWidget, QApplication, QPushButton
from PySide2.QtCore import QTimer, Qt, SIGNAL
from .. import defaults
from . import appref

log = logging.getLogger(__name__)


class DictationOverlay(QWidget):
    """Frameless window showing the partial dictation results
    """

    app = property(appref.app)

    DEFAULT_FLAGS = (
        Qt.WindowStaysOnTopHint
        | Qt.FramelessWindowHint
        | Qt.WindowTransparentForInput
        | Qt.Tool
        | Qt.WindowDoesNotAcceptFocus
    )
    REPOSITION_FLAGS = Qt.WindowStaysOnTopHint | Qt.Tool

    def __init__(self, *args, **named):
        super(DictationOverlay, self).__init__(*args, **named)
        self.setWindowTitle('%s Text Preview' % (defaults.APP_NAME_SHORT))
        self.setWindowFlags(self.DEFAULT_FLAGS)
        # self.setAttribute(Qt.WA_TranslucentBackground, True)
        # self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        # self.setMaximumHeight(40)
        # self.setMinimumWidth(400)
        self.setWindowOpacity(0.8)
        self.label = QPushButton(defaults.APP_NAME_HUMAN, self)
        self.label.setFlat(True)
        self.label.connect(self.label, SIGNAL('clicked()'), self.save_new_position)
        # self.setCentralWidget(self.label)
        self.timer = QTimer(self)
        self.timer.connect(self.timer, SIGNAL('timeout()'), self.on_timer_finished)

    def show_for_reposition(self):
        """Allow the user to reposition"""
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.set_text('Drag, then click here', 0)

    GEOMETRY_SAVE_KEY = 'overlay.geometry'

    def save_new_position(self, *args):
        """On close during reposition, save geometry and hide"""
        log.info("Saving new position: %s", self.geometry())
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.app.settings.setValue(self.GEOMETRY_SAVE_KEY, self.saveGeometry())
        self.hide()
        self.disconnect(SIGNAL('click()'), self.save_new_position)

    def set_text(self, text, timeout=500):
        log.info("Setting text: %s", text)
        self.label.setText(text)
        self.label.adjustSize()
        self.adjustSize()
        self.show()
        if timeout:
            self.timer.start(500)

    def on_timer_finished(self, evt=None):
        """When the timer finishes without any interruption/reset, hide the window"""
        self.hide()
        self.timer.stop()

