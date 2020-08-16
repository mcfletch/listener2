"""Application actions for use in menus, toolbars, shortcuts, etc"""
from PySide2.QtWidgets import QAction
from PySide2.QtGui import QKeySequence
from PySide2.QtCore import SIGNAL
from PySide2.QtCore import QObject
from PySide2.QtCore import Signal
from . import icons


def standard_action(
    parent, icon=None, title=None, help_text=None, callback=None, shortcut=None,
):
    """Create an action with a callback"""
    args = []
    if icon:
        if isinstance(icon, str):
            icon = icons.get_icon(icon)
        args.append(icon)
    args.append(title)
    args.append(help_text)

    action = QAction(title,)
    if callback:
        action.connect(SIGNAL('triggered()'), callback)
    if shortcut:
        if isinstance(shortcut, str):
            shortcut = parent.tr(shortcut)
        sequence = QKeySequence(shortcut)
        action.setShortcut(sequence)
    return action

