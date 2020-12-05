# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'containersettings.ui'
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


class Ui_ContainerSettings(object):
    def setupUi(self, ContainerSettings):
        if not ContainerSettings.objectName():
            ContainerSettings.setObjectName(u"ContainerSettings")
        ContainerSettings.resize(400, 300)
        ContainerSettings.setMinimumSize(QSize(200, 0))
        self.verticalLayout = QVBoxLayout(ContainerSettings)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.enable_audio = QPushButton(ContainerSettings)
        self.enable_audio.setObjectName(u"enable_audio")
        icon = QIcon()
        icon.addFile(u"static/microphone-inactive.svg", QSize(), QIcon.Normal, QIcon.Off)
        icon.addFile(u"static/microphone-recording.svg", QSize(), QIcon.Normal, QIcon.On)
        self.enable_audio.setIcon(icon)
        self.enable_audio.setCheckable(True)
        self.enable_audio.setChecked(True)

        self.verticalLayout.addWidget(self.enable_audio)

        self.container_name = QLabel(ContainerSettings)
        self.container_name.setObjectName(u"container_name")

        self.verticalLayout.addWidget(self.container_name)


        self.retranslateUi(ContainerSettings)

        QMetaObject.connectSlotsByName(ContainerSettings)
    # setupUi

    def retranslateUi(self, ContainerSettings):
        ContainerSettings.setWindowTitle(QCoreApplication.translate("ContainerSettings", u"Form", None))
        self.enable_audio.setText(QCoreApplication.translate("ContainerSettings", u"Listening", None))
#if QT_CONFIG(shortcut)
        self.enable_audio.setShortcut(QCoreApplication.translate("ContainerSettings", u"Alt+L", None))
#endif // QT_CONFIG(shortcut)
        self.container_name.setText(QCoreApplication.translate("ContainerSettings", u"Container status...", None))
    # retranslateUi

