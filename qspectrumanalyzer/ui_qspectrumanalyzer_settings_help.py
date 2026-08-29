# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'qspectrumanalyzer_settings_help.ui'
##
## Created by: Qt User Interface Compiler version 6.11.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QAbstractButton, QApplication, QDialog, QDialogButtonBox,
    QPlainTextEdit, QSizePolicy, QVBoxLayout, QWidget)

class Ui_QSpectrumAnalyzerSettingsHelp(object):
    def setupUi(self, QSpectrumAnalyzerSettingsHelp):
        if not QSpectrumAnalyzerSettingsHelp.objectName():
            QSpectrumAnalyzerSettingsHelp.setObjectName(u"QSpectrumAnalyzerSettingsHelp")
        QSpectrumAnalyzerSettingsHelp.resize(1200, 700)
        self.verticalLayout = QVBoxLayout(QSpectrumAnalyzerSettingsHelp)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.helpTextEdit = QPlainTextEdit(QSpectrumAnalyzerSettingsHelp)
        self.helpTextEdit.setObjectName(u"helpTextEdit")
        self.helpTextEdit.setUndoRedoEnabled(False)
        self.helpTextEdit.setTextInteractionFlags(Qt.TextSelectableByKeyboard|Qt.TextSelectableByMouse)

        self.verticalLayout.addWidget(self.helpTextEdit)

        self.buttonBox = QDialogButtonBox(QSpectrumAnalyzerSettingsHelp)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Close)

        self.verticalLayout.addWidget(self.buttonBox)

        QWidget.setTabOrder(self.helpTextEdit, self.buttonBox)

        self.retranslateUi(QSpectrumAnalyzerSettingsHelp)
        self.buttonBox.accepted.connect(QSpectrumAnalyzerSettingsHelp.accept)
        self.buttonBox.rejected.connect(QSpectrumAnalyzerSettingsHelp.reject)

        QMetaObject.connectSlotsByName(QSpectrumAnalyzerSettingsHelp)
    # setupUi

    def retranslateUi(self, QSpectrumAnalyzerSettingsHelp):
        QSpectrumAnalyzerSettingsHelp.setWindowTitle(QCoreApplication.translate("QSpectrumAnalyzerSettingsHelp", u"Help - QSpectrumAnalyzer", None))
    # retranslateUi

