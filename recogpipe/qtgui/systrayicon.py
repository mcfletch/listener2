from PySide2 import QtCore, QtGui, QtWidgets, QtMultimedia
import sys, os, logging
log = logging.getLogger(__name__)
HERE = os.path.dirname(os.path.abspath((__file__)))
ICON_DIR = os.path.normpath(os.path.join(HERE,'../static'))

class RecogPipeSystrayIcon(QtWidgets.QSystemTrayIcon):
    """Presents systray icon showing current recording state"""
    ICONS = {
        'panel-icon-stopped': None,
        'panel-icon-paused': None,
        'panel-icon-recording': None,
        'panel-icon-error': None,
        'microphone': None,
    }
    @classmethod
    def load_icons(cls):
        for key,icon in list(cls.ICONS.items()):
            if icon is None:
                icon = QtGui.QIcon(os.path.join(ICON_DIR,key+'.svg'))
                cls.ICONS[key] = icon
        return cls.ICONS
    def set_state(self, state='stopped'):
        """Set state icon showing overall current state"""
        icon = 'panel-icon-%s'%(state,)
        self.setIcon(self.load_icons()[icon])
    def set_partial(self, text='', confidence=1.0):
        """Show or hide a partial text preview
        
        Note: this is *really* unsatisfying currently as it's using the 
        notifications GUI, which results in lots of windows popping in and
        out when what we really want is a tiny tooltip-like window that
        just updates contents as we go...
        """
        self.showMessage(None,text,self.load_icons()['microphone'],2000)


def main():
    logging.basicConfig(level=logging.DEBUG)
    app = QtWidgets.QApplication([])
    icon = RecogPipeSystrayIcon()
    icon.set_state('stopped')
    icon.setVisible(True)
    timer = QtCore.QTimer(icon)
    icons = ['paused','recording','error']
    messages = ['Very','Very interesting','Very interesting I say','Very interesting I said']
    def exit_after_test(*args):
        icon.set_partial(messages.pop(0))
        try:
            icon.set_state(icons.pop(0))
        except IndexError as err:
            log.info("Exiting %s", )
            app.quit()
    icon.connect(timer, QtCore.SIGNAL("timeout()"), exit_after_test)
    timer.start(1000 * 2)
    icon.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
