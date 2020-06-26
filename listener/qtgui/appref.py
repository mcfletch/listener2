from PySide2.QtWidgets import QApplication


def app(*args):
    """Lookup the current application instance"""
    return QApplication.instance()
