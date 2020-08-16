# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'listeneraudiosettings.ui'
##
## Created by: Qt User Interface Compiler version 5.15.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import (QCoreApplication, QDate, QDateTime, QMetaObject,
    QObject, QPoint, QRect, QSize, QTime, QUrl, Qt)
from PySide2.QtGui import (QBrush, QColor, QConicalGradient, QCursor, QFont,
    QFontDatabase, QIcon, QKeySequence, QLinearGradient, QPalette, QPainter,
    QPixmap, QRadialGradient)
from PySide2.QtWidgets import *


class Ui_ListenerAudioSettings(object):
    def setupUi(self, ListenerAudioSettings):
        if not ListenerAudioSettings.objectName():
            ListenerAudioSettings.setObjectName(u"ListenerAudioSettings")
        ListenerAudioSettings.resize(708, 755)
        self.verticalLayout = QVBoxLayout(ListenerAudioSettings)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.input_select = QComboBox(ListenerAudioSettings)
        self.input_select.setObjectName(u"input_select")
        self.input_select.setFrame(True)

        self.verticalLayout.addWidget(self.input_select)

        self.volume_control = QSlider(ListenerAudioSettings)
        self.volume_control.setObjectName(u"volume_control")
        self.volume_control.setValue(99)
        self.volume_control.setSliderPosition(99)
        self.volume_control.setOrientation(Qt.Horizontal)

        self.verticalLayout.addWidget(self.volume_control)

        self.enable_audio = QPushButton(ListenerAudioSettings)
        self.enable_audio.setObjectName(u"enable_audio")
        icon = QIcon()
        icon.addFile(u"static/microphone-inactive.svg", QSize(), QIcon.Normal, QIcon.Off)
        icon.addFile(u"static/microphone-recording.svg", QSize(), QIcon.Normal, QIcon.On)
        self.enable_audio.setIcon(icon)
        self.enable_audio.setCheckable(True)
        self.enable_audio.setChecked(True)

        self.verticalLayout.addWidget(self.enable_audio)


        self.retranslateUi(ListenerAudioSettings)

        QMetaObject.connectSlotsByName(ListenerAudioSettings)
    # setupUi

    def retranslateUi(self, ListenerAudioSettings):
        ListenerAudioSettings.setWindowTitle(QCoreApplication.translate("ListenerAudioSettings", u"Form", None))
#if QT_CONFIG(tooltip)
        self.input_select.setToolTip(QCoreApplication.translate("ListenerAudioSettings", u"Choose the pulse-audio source", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.volume_control.setToolTip(QCoreApplication.translate("ListenerAudioSettings", u"Modify recording level", None))
#endif // QT_CONFIG(tooltip)
        self.enable_audio.setText(QCoreApplication.translate("ListenerAudioSettings", u"Recording", None))
#if QT_CONFIG(shortcut)
        self.enable_audio.setShortcut(QCoreApplication.translate("ListenerAudioSettings", u"Alt+L", None))
#endif // QT_CONFIG(shortcut)
    # retranslateUi

