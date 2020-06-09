#! /usr/bin/env python3
"""Qt GUI Application for controlling RecogPipe"""
from PySide2 import QtCore, QtGui, QtWidgets, QtSvg
import sys, os, logging
HERE = os.path.dirname(os.path.abspath((__file__)))

ICONS = {
    'panel-icon-stopped': None,
    'panel-icon-paused': None,
    'panel-icon-recording': None,
}

def load_icons():
    for key,icon in list(ICONS.items()):
        if icon is None:
            icon = QtGui.QIcon(os.path.join(HERE,'static',key+'.svg'))
            ICONS[key] = icon
    return ICONS
    

log = logging.getLogger(__name__)
def get_options():
    import argparse 
    parser = argparse.ArgumentParser(
        description='RecogPipe GUI front-end in PySide2'
    )
    return parser

def main():
    options = get_options().parse_args()
    load_icons()
    app = QtWidgets.QApplication([])
    icon = QtWidgets.QSystemTrayIcon()
    icon.setIcon(ICONS['panel-icon-stopped'])
    icon.setVisible(True)
    timer = QtCore.QTimer(icon)
    icons = sorted(ICONS.keys())
    def exit_after_test(*args):
        try:
            next = icons.pop(0)
            icon.setIcon(ICONS[next])
        except IndexError as err:
            log.info("Exiting %s", )
            app.quit()
    icon.connect(timer, QtCore.SIGNAL("timeout()"), exit_after_test)
    timer.start(1000 * 5)

    icon.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
