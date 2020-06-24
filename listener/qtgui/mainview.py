import logging, os
from PySide2.QtQuick import QQuickView
from PySide2.QtCore import QUrl
from .. import defaults

MAIN_QML = os.path.join(defaults.LISTENER_SOURCE, 'qtgui', 'mainview.qml')


def ListenerView():
    view = QQuickView()
    url = QUrl(MAIN_QML)
    view.setSource(url)
    return view
