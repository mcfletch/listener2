"""App-specific icons"""
import os, logging, glob
from PySide2 import QtGui

HERE = os.path.dirname(os.path.abspath((__file__)))
ICON_DIR = os.path.normpath(os.path.join(HERE, '../static'))

ICONS = {
    # 'panel-icon-stopped': None,
    # 'panel-icon-paused': None,
    # 'panel-icon-recording': None,
    # 'panel-icon-error': None,
    # 'microphone': None,
    # 'microphone-active': None,
    # 'microphone-inactive': None,
    # 'microphone-recording': None,
}


def resource_icons():
    """Load our resource icons"""
    pattern = os.path.join(ICON_DIR, '*.svg')
    for name in glob.glob(pattern):
        ICONS[os.path.basename(name[:-4])] = None
    assert 'microphone' in ICONS, (ICONS, pattern)


resource_icons()


def get_icon(key):
    """Get our local/static icon by key/filename"""
    current = ICONS.get(key)
    if current is None:
        if key in ICONS:
            current = ICONS[key] = QtGui.QIcon(os.path.join(ICON_DIR, key + '.svg'))
        elif key != 'microphone':
            return QtGui.QIcon.fromTheme(key, get_icon('microphone'))
        else:
            raise RuntimeError("We didn't load our default icon (microphone.svg)!")
    return current
