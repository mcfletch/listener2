import logging
from PySide2 import QtMultimedia, QtCore, QtWidgets
from PySide2.QtCore import QTimer, Qt, SIGNAL
from . import appref
from .. import defaults

log = logging.getLogger(__name__)


class MicrophoneWidget(QtWidgets.QWidget):
    """Widget showing the microphone's current state"""

    def __init__(self, parent, microphone):
        super(MicrophoneWidget, self).__init__(parent)
        self.microphone = microphone
        self.microphone.connect(
            self.microphone,
            SIGNAL('stateChanged(QMediaRecorder::State state)'),
            self.on_microphone_state_change,
        )

    def on_microphone_state_change(self, state):
        log.info("Microphone state changed")


class Microphone(QtMultimedia.QAudioRecorder):
    """Microphone to audio pipe driver for listener
    """

    app = property(appref.app)

    def __init__(self, parent, target=defaults.DEFAULT_INPUT):
        super(Microphone, self).__init__(parent)
        self.target = target
        settings = QtMultimedia.QAudioEncoderSettings()
        settings.setCodec('audio/x-raw')
        settings.setChannelCount(1)
        settings.setSampleRate(16000)
        settings.setEncodingOption('pcm-format', 's16le')
        self.setEncodingSettings(settings)
        self.connect(
            self, SIGNAL('availableAudioInputsChanged()'), self.on_inputs_changed
        )

    def choose_input(self):
        """Choose the appropriate input to use given current inputs"""
        current = self.app.settings.value(defaults.MICROPHONE_PREFERENCE_KEY)
        if current is not None:
            name = self.defaultAudioInput()
        else:
            available = self.audioInputs()
            if current in available:
                name = current
            else:
                name = self.defaultAudioInput()
        if name != self.audioInput():
            log.info("Updating intput to %s", name)
            self.setAudioInput(name)

    def on_inputs_changed(self, *args):
        """Handle change of inputs"""
        self.choose_input()

    def ensure_target(self):
        """Make sure our target named pipe is present"""
        from .. import pipeaudio

        return pipeaudio.ensure_target(self.target)

    def on_go_live(self, *args):
        """Request to go live is received"""
        target = self.ensure_target()
        self.setOutputLocation(QtCore.QUrl.fromLocalFile(target))
        self.record()

    def on_stop(self, *args):
        """Request to stop is received"""
        self.stop()
