# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'qspectrumanalyzer_smoothing.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QComboBox, QDialog,
    QDialogButtonBox, QFormLayout, QLabel, QSizePolicy,
    QSpacerItem, QSpinBox, QVBoxLayout, QWidget)

class Ui_QSpectrumAnalyzerSmoothing(object):
    def setupUi(self, QSpectrumAnalyzerSmoothing):
        if not QSpectrumAnalyzerSmoothing.objectName():
            QSpectrumAnalyzerSmoothing.setObjectName(u"QSpectrumAnalyzerSmoothing")
        QSpectrumAnalyzerSmoothing.resize(250, 130)
        self.verticalLayout = QVBoxLayout(QSpectrumAnalyzerSmoothing)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.label = QLabel(QSpectrumAnalyzerSmoothing)
        self.label.setObjectName(u"label")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.label)

        self.windowFunctionComboBox = QComboBox(QSpectrumAnalyzerSmoothing)
        self.windowFunctionComboBox.addItem("")
        self.windowFunctionComboBox.addItem("")
        self.windowFunctionComboBox.addItem("")
        self.windowFunctionComboBox.addItem("")
        self.windowFunctionComboBox.addItem("")
        self.windowFunctionComboBox.setObjectName(u"windowFunctionComboBox")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.windowFunctionComboBox)

        self.label_2 = QLabel(QSpectrumAnalyzerSmoothing)
        self.label_2.setObjectName(u"label_2")

        self.formLayout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.label_2)

        self.windowLengthSpinBox = QSpinBox(QSpectrumAnalyzerSmoothing)
        self.windowLengthSpinBox.setObjectName(u"windowLengthSpinBox")
        self.windowLengthSpinBox.setMinimum(3)
        self.windowLengthSpinBox.setMaximum(1001)
        self.windowLengthSpinBox.setValue(11)

        self.formLayout.setWidget(1, QFormLayout.ItemRole.FieldRole, self.windowLengthSpinBox)


        self.verticalLayout.addLayout(self.formLayout)

        self.verticalSpacer = QSpacerItem(20, 1, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.buttonBox = QDialogButtonBox(QSpectrumAnalyzerSmoothing)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.verticalLayout.addWidget(self.buttonBox)

#if QT_CONFIG(shortcut)
        self.label.setBuddy(self.windowFunctionComboBox)
        self.label_2.setBuddy(self.windowLengthSpinBox)
#endif // QT_CONFIG(shortcut)
        QWidget.setTabOrder(self.windowFunctionComboBox, self.windowLengthSpinBox)
        QWidget.setTabOrder(self.windowLengthSpinBox, self.buttonBox)

        self.retranslateUi(QSpectrumAnalyzerSmoothing)
        self.buttonBox.accepted.connect(QSpectrumAnalyzerSmoothing.accept)
        self.buttonBox.rejected.connect(QSpectrumAnalyzerSmoothing.reject)

        self.windowFunctionComboBox.setCurrentIndex(1)


        QMetaObject.connectSlotsByName(QSpectrumAnalyzerSmoothing)
    # setupUi

    def retranslateUi(self, QSpectrumAnalyzerSmoothing):
        QSpectrumAnalyzerSmoothing.setWindowTitle(QCoreApplication.translate("QSpectrumAnalyzerSmoothing", u"Smoothing - QSpectrumAnalyzer", None))
        self.label.setText(QCoreApplication.translate("QSpectrumAnalyzerSmoothing", u"&Window function:", None))
        self.windowFunctionComboBox.setItemText(0, QCoreApplication.translate("QSpectrumAnalyzerSmoothing", u"rectangular", None))
        self.windowFunctionComboBox.setItemText(1, QCoreApplication.translate("QSpectrumAnalyzerSmoothing", u"hanning", None))
        self.windowFunctionComboBox.setItemText(2, QCoreApplication.translate("QSpectrumAnalyzerSmoothing", u"hamming", None))
        self.windowFunctionComboBox.setItemText(3, QCoreApplication.translate("QSpectrumAnalyzerSmoothing", u"bartlett", None))
        self.windowFunctionComboBox.setItemText(4, QCoreApplication.translate("QSpectrumAnalyzerSmoothing", u"blackman", None))

        self.label_2.setText(QCoreApplication.translate("QSpectrumAnalyzerSmoothing", u"Window len&gth:", None))
    # retranslateUi

