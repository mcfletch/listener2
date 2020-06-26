"""Window configuring the audio input source"""
from PySide2.QtWidgets import QDockWidget, QPushButton, QVBoxLayout
from ..resources import audiowindow
from . import icons
import subprocess


def describe_pulse_sources():
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


class ListenerAudio(QDockWidget, audiowindow.Ui_ListenerAudio):
    """Shows the Listener audio connection"""

    def __init__(self, *args, **named):
        super(ListenerAudio, self).__init__(*args, **named)
        self.setupUi(self)
        self.set_available_inputs()

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

