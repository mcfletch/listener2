import sys, os, logging
from PySide2 import QtCore, QtGui, QtWidgets, QtMultimedia
from . import icons, appstates
from .. import defaults

log = logging.getLogger(__name__)
HERE = os.path.dirname(os.path.abspath((__file__)))
ICON_DIR = os.path.normpath(os.path.join(defaults.LISTENER_SOURCE, 'static'))


class ListenerSystrayIcon(QtWidgets.QSystemTrayIcon):
    """Presents systray icon showing current recording state"""

    def set_state(self, state='stopped'):
        """Set state icon showing overall current state"""
        log.info('Listener state change to %r', state)
        app_state = appstates.by_key(state)
        icon = app_state.icon
        gui_icon = icons.get_icon(icon)
        self.setIcon(gui_icon)
        self.setToolTip(app_state.tooltip)
        self.showMessage(None, app_state.text, gui_icon, 500)

    def set_partial(self, text='', confidence=1.0):
        """Show or hide a partial text preview
        
        Note: this is *really* unsatisfying currently as it's using the 
        notifications GUI, which results in lots of windows popping in and
        out when what we really want is a tiny tooltip-like window that
        just updates contents as we go...
        """
        self.showMessage(None, text, icons.get_icon('microphone'), 2000)


def main():
    logging.basicConfig(level=logging.DEBUG)
    app = QtWidgets.QApplication([])
    icon = ListenerSystrayIcon()
    icon.set_state('stopped')
    icon.setVisible(True)
    timer = QtCore.QTimer(icon)
    icons = [a.key for a in appstates.APP_STATES]

    def exit_after_test(*args):
        try:
            icon.set_state(icons.pop(0))
        except IndexError as err:
            log.info("Exiting %s", err)
            app.quit()

    icon.connect(timer, QtCore.SIGNAL("timeout()"), exit_after_test)
    timer.start(1000 * 2)
    icon.show()
    sys.exit(app.exec_())

