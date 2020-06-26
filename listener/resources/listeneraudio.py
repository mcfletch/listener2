# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'listeneraudio.ui'
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


class Ui_ListenerAudio(object):
    def setupUi(self, ListenerAudio):
        if not ListenerAudio.objectName():
            ListenerAudio.setObjectName(u"ListenerAudio")
        ListenerAudio.resize(630, 728)
        ListenerAudio.setFocusPolicy(Qt.TabFocus)
        icon = QIcon()
        icon.addFile(u"../static/microphone.svg", QSize(), QIcon.Normal, QIcon.Off)
        ListenerAudio.setWindowIcon(icon)
        ListenerAudio.setAutoFillBackground(False)
        ListenerAudio.setFloating(True)
        self.dockWidgetContents = QWidget()
        self.dockWidgetContents.setObjectName(u"dockWidgetContents")
        self.verticalLayout_2 = QVBoxLayout(self.dockWidgetContents)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.input_select = QComboBox(self.dockWidgetContents)
        self.input_select.setObjectName(u"input_select")
        self.input_select.setFrame(True)

        self.verticalLayout.addWidget(self.input_select)

        self.volume_control = QSlider(self.dockWidgetContents)
        self.volume_control.setObjectName(u"volume_control")
        self.volume_control.setValue(99)
        self.volume_control.setSliderPosition(99)
        self.volume_control.setOrientation(Qt.Horizontal)

        self.verticalLayout.addWidget(self.volume_control)

        self.enable_audio = QPushButton(self.dockWidgetContents)
        self.enable_audio.setObjectName(u"enable_audio")
        icon1 = QIcon()
        icon1.addFile(u"../static/microphone-inactive.svg", QSize(), QIcon.Normal, QIcon.Off)
        icon1.addFile(u"../static/microphone-recording.svg", QSize(), QIcon.Normal, QIcon.On)
        self.enable_audio.setIcon(icon1)

        self.verticalLayout.addWidget(self.enable_audio)


        self.verticalLayout_2.addLayout(self.verticalLayout)

        ListenerAudio.setWidget(self.dockWidgetContents)

        self.retranslateUi(ListenerAudio)

        QMetaObject.connectSlotsByName(ListenerAudio)
    # setupUi

    def retranslateUi(self, ListenerAudio):
        ListenerAudio.setWindowTitle(QCoreApplication.translate("ListenerAudio", u"A&udio", None))
#if QT_CONFIG(tooltip)
        self.input_select.setToolTip(QCoreApplication.translate("ListenerAudio", u"Choose the pulse-audio source", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.volume_control.setToolTip(QCoreApplication.translate("ListenerAudio", u"Modify recording level", None))
#endif // QT_CONFIG(tooltip)
        self.enable_audio.setText(QCoreApplication.translate("ListenerAudio", u"Microphone", None))
    # retranslateUi

