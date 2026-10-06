# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'qspectrumanalyzer_persistence.ui'
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

class Ui_QSpectrumAnalyzerPersistence(object):
    def setupUi(self, QSpectrumAnalyzerPersistence):
        if not QSpectrumAnalyzerPersistence.objectName():
            QSpectrumAnalyzerPersistence.setObjectName(u"QSpectrumAnalyzerPersistence")
        QSpectrumAnalyzerPersistence.resize(250, 130)
        self.verticalLayout = QVBoxLayout(QSpectrumAnalyzerPersistence)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.label_2 = QLabel(QSpectrumAnalyzerPersistence)
        self.label_2.setObjectName(u"label_2")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.label_2)

        self.decayFunctionComboBox = QComboBox(QSpectrumAnalyzerPersistence)
        self.decayFunctionComboBox.addItem("")
        self.decayFunctionComboBox.addItem("")
        self.decayFunctionComboBox.setObjectName(u"decayFunctionComboBox")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.decayFunctionComboBox)

        self.label = QLabel(QSpectrumAnalyzerPersistence)
        self.label.setObjectName(u"label")

        self.formLayout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.label)

        self.persistenceLengthSpinBox = QSpinBox(QSpectrumAnalyzerPersistence)
        self.persistenceLengthSpinBox.setObjectName(u"persistenceLengthSpinBox")
        self.persistenceLengthSpinBox.setValue(5)

        self.formLayout.setWidget(1, QFormLayout.ItemRole.FieldRole, self.persistenceLengthSpinBox)


        self.verticalLayout.addLayout(self.formLayout)

        self.verticalSpacer = QSpacerItem(20, 5, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.buttonBox = QDialogButtonBox(QSpectrumAnalyzerPersistence)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.verticalLayout.addWidget(self.buttonBox)

#if QT_CONFIG(shortcut)
        self.label_2.setBuddy(self.decayFunctionComboBox)
        self.label.setBuddy(self.persistenceLengthSpinBox)
#endif // QT_CONFIG(shortcut)
        QWidget.setTabOrder(self.decayFunctionComboBox, self.persistenceLengthSpinBox)
        QWidget.setTabOrder(self.persistenceLengthSpinBox, self.buttonBox)

        self.retranslateUi(QSpectrumAnalyzerPersistence)
        self.buttonBox.accepted.connect(QSpectrumAnalyzerPersistence.accept)
        self.buttonBox.rejected.connect(QSpectrumAnalyzerPersistence.reject)

        self.decayFunctionComboBox.setCurrentIndex(1)


        QMetaObject.connectSlotsByName(QSpectrumAnalyzerPersistence)
    # setupUi

    def retranslateUi(self, QSpectrumAnalyzerPersistence):
        QSpectrumAnalyzerPersistence.setWindowTitle(QCoreApplication.translate("QSpectrumAnalyzerPersistence", u"Persistence - QSpectrumAnalyzer", None))
        self.label_2.setText(QCoreApplication.translate("QSpectrumAnalyzerPersistence", u"Decay function:", None))
        self.decayFunctionComboBox.setItemText(0, QCoreApplication.translate("QSpectrumAnalyzerPersistence", u"linear", None))
        self.decayFunctionComboBox.setItemText(1, QCoreApplication.translate("QSpectrumAnalyzerPersistence", u"exponential", None))

        self.label.setText(QCoreApplication.translate("QSpectrumAnalyzerPersistence", u"Persistence length:", None))
    # retranslateUi

