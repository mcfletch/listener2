"""Window configuring the audio input source"""
import subprocess, time, logging, threading, signal, json
from PySide2.QtWidgets import QWidget, QPushButton, QVBoxLayout
from PySide2 import QtCore
from ..static import containersettings
from .. import defaults
from . import icons
from . import appref
from . import actions


class ContainerSettings(containersettings.Ui_ContainerSettings, QWidget):
    """Settings for the backend container"""

    def __init__(self, *args, **named):
        super(ContainerSettings, self).__init__(*args, **named)
        self.setupUi(self)
