"""Displays partial dictation results in a translucent overlay window"""
import logging
from PySide2.QtWidgets import QMainWindow, QLabel, QWidget, QApplication
from PySide2.QtCore import QTimer, Qt, SIGNAL
from .. import defaults

log = logging.getLogger(__name__)


class DictationOverlay(QWidget):
    """Frameless window showing the partial dictation results"""

    @property
    def app(self):
        """Lookup the current application instance"""
        return QApplication.instance()

    def __init__(self, *args, **named):
        super(DictationOverlay, self).__init__(*args, **named)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        # self.setAttribute(Qt.WA_TranslucentBackground, True)
        # self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setMinimumHeight(40)
        self.setMinimumWidth(400)
        self.setWindowOpacity(0.8)
        self.label = QLabel(defaults.APP_NAME_HUMAN, self)
        # self.setCentralWidget(self.label)
        self.timer = QTimer(self)
        self.timer.connect(self.timer, SIGNAL('timeout()'), self.on_timer_finished)

    def show_for_reposition(self):
        """Allow the user to reposition"""
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.label.connect(self.label, SIGNAL('click()'), self.save_new_position)
        self.label.setText('Drag, then click here')
        self.show()

    GEOMETRY_SAVE_KEY = 'overlay.geometry'

    def save_new_position(self, evt, *args):
        """On close during reposition, save geometry and hide"""
        log.info("Saving new position: %s", self.geometry())
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.app.settings.setValue(self.GEOMETRY_SAVE_KEY, self.saveGeometry())
        self.hide()
        self.label.disconnect(SIGNAL('click()'), self.save_new_position)

    def set_text(self, text):
        print("Setting text: %s", text)
        self.show()
        self.label.setText(text)
        self.timer.start(500)

    def on_timer_finished(self, evt=None):
        """When the timer finishes without any interruption/reset, hide the window"""
        self.hide()
        self.timer.stop()

