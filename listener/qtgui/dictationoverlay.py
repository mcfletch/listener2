"""Displays partial dictation results in a translucent overlay window"""
from PySide2.QtWidgets import QMainWindow, QLabel, QWidget
from PySide2.QtCore import QTimer, Qt, SIGNAL
from .. import defaults


class DictationOverlay(QWidget):
    """Frameless window showing the partial dictation results"""

    def __init__(self, *args, **named):
        super(DictationOverlay, self).__init__(*args, **named)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        # self.setAttribute(Qt.WA_TranslucentBackground, True)
        # self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setMinimumHeight(40)
        self.setMinimumWidth(200)
        self.setWindowOpacity(0.4)
        self.label = QLabel(defaults.APP_NAME_HUMAN, self)
        # self.setCentralWidget(self.label)
        self.timer = QTimer(self)
        self.timer.connect(self.timer, SIGNAL('timeout()'), self.on_timer_finished)

    def set_text(self, text):
        print("Setting text: %s", text)
        import pdb

        pdb.set_trace()
        self.show()
        self.label.setText(text)
        self.timer.start(500)

    def on_timer_finished(self, evt=None):
        # self.hide()
        print("Would have hidden now...")
