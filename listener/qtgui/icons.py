"""App-specific icons"""
import os, logging
from PySide2 import QtGui

HERE = os.path.dirname(os.path.abspath((__file__)))
ICON_DIR = os.path.normpath(os.path.join(HERE, '../static'))

ICONS = {
    'panel-icon-stopped': None,
    'panel-icon-paused': None,
    'panel-icon-recording': None,
    'panel-icon-error': None,
    'microphone': None,
}


def get_icon(key):
    """Get our local/static icon by key/filename"""
    current = ICONS.get(key)
    if current is None:
        icon = ICONS[key] = QtGui.QIcon(os.path.join(ICON_DIR, key + '.svg'))
    return icon
