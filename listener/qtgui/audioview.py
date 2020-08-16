"""Window configuring the audio input source"""
import subprocess, time, logging, threading, signal
from PySide2.QtWidgets import QWidget, QPushButton, QVBoxLayout
from PySide2 import QtCore
from ..static import listeneraudiosettings
from . import icons
from . import appref
from . import actions

log = logging.getLogger(__name__)


def describe_pulse_sources():
    """Parse the output of pctl list to describe current pulse devices"""
    _interesting_headers = [
        'State',
        'Name',
        'Description',
        'Mute',
        'Monitor of Sink',
        'Flags',
    ]
    sources_description = subprocess.check_output(['pactl', 'list', 'sources',]).decode(
        'ascii', 'ignore'
    )
    sources = []
    current_source = None
    for line in sources_description.splitlines():
        if line.startswith('Source #'):
            if current_source:
                sources.append(current_source)
            current_source = {
                'number': int(line[8:]),
            }
        else:
            for header in _interesting_headers:
                if line.strip().startswith(header + ':'):
                    value = line.split(':', 1)[1].strip()
                    if value == 'n/a':
                        value = None
                    current_source[header.split()[0].lower()] = value
                    break
    if current_source:
        sources.append(current_source)
    return sources


class ListenerAudio(listeneraudiosettings.Ui_ListenerAudioSettings, QWidget):
    """Shows the Listener audio connection"""

    app = property(appref.app)
    GEOMETRY_SAVE_KEY = 'audioview.geometry'
    INPUT_SAVE_KEY = 'audioview.microphone'
    VOLUME_SAVE_KEY = 'audioview.volume'
    AUDIO_ENABLED_KEY = 'audioview.enable_audio'

    def __init__(self, *args, **named):
        super(ListenerAudio, self).__init__(*args, **named)
        self.want_input = True
        self.setupUi(self)
        self.set_available_inputs()
        self.input_select.currentIndexChanged.connect(self.on_input_selected)
        self.volume_control.valueChanged.connect(self.on_volume_selected)
        default_value = self.app.settings.value(self.VOLUME_SAVE_KEY)
        default_value = 99 if default_value is None else int(default_value)
        self.volume_control.setValue(default_value)
        default_value = self.app.settings.value(self.AUDIO_ENABLED_KEY) == 'true'
        self.enable_audio.toggled.connect(self.on_enable_audio)
        self._recording_button_configure(default_value)
        log.info("Audio settings window set up: %r", default_value)
        # thread = threading.Thread(target=self.run_stream_thread,)
        # thread.setDaemon(True)
        # thread.start()
        # self.running_thread = thread

        # self.microphone_start = QPushButton(
        #     icons.get_icon('microphone-inactive'), 'Mic', self
        # )
        # self.microphone_start.setMinimumHeight(32)
        # layout = QVBoxLayout(self)
        # layout.addWidget(self.microphone_start, stretch=True)
        # self.setMinimumWidth(200)
        # self.setLayout(layout)

    def set_available_inputs(self):
        """Get the available inputs from pulseaudio"""
        for source in sorted(
            describe_pulse_sources(), key=lambda x: x.get('description')
        ):
            if source.get('monitor'):
                # don't really want to use output-monitor for dictation...
                continue
            self.input_select.addItem(source['description'], source)

        current = self.current_input()
        log.info("Current user preference: %s", current)
        index = self.input_select.findText(current,)
        if index > -1:
            self.input_select.setCurrentIndex(index)

    def current_input(self):
        current = self.app.settings.value(self.INPUT_SAVE_KEY)
        if current:
            return current
        return None

    def on_input_selected(self, index: int):
        """We've selected an index, make it our microphone"""
        current = self.input_select.itemData(index)
        self.app.settings.setValue(self.INPUT_SAVE_KEY, current['description'])
        log.info("Updating user preference: %s", current['description'])
        self.app.AUDIO_SETTINGS_CHANGED.emit()
        return True

    def on_volume_selected(self, value: int):
        """We've modified the recording volume"""
        log.info("Updated user volume preference: %s", value)
        self.app.settings.setValue(self.VOLUME_SAVE_KEY, value)
        self.app.AUDIO_SETTINGS_CHANGED.emit()
        return True

    def on_enable_audio(self, value: bool):
        """User has asked us to start/stop audio"""
        self.app.settings.setValue(self.AUDIO_ENABLED_KEY, value)
        self.app.AUDIO_SETTINGS_CHANGED.emit()
        self._recording_button_configure(value)
        return True

    def _recording_button_configure(self, recording):
        if recording:
            self.enable_audio.setText('Stop Recording')
        else:
            self.enable_audio.setText('Start Recording')
        self.enable_audio.setChecked(recording)

    # def run_stream_thread(self):
    #     """Run our listener-audio stream in a subprocess"""
    #     while self.want_input:
    #         source = self.current_input()
    #         command = [
    #             'listener-audio',
    #         ]
    #         if source:
    #             command += ['--device', source]
    #         try:
    #             pipe = subprocess.Popen(command)
    #             try:
    #                 while (
    #                     pipe.poll() is None
    #                     and self.want_input
    #                     and source == self.current_input()
    #                 ):
    #                     time.sleep(1)
    #             finally:
    #                 if pipe.poll() is None:
    #                     os.kill(pipe.pid, signal.SIGINT)

    #         except Exception as err:
    #             log.error("Failure during audio pipe setup")
    #             time.sleep(2.0)

