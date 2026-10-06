# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'qspectrumanalyzer_baseline.ui'
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
    QFormLayout, QHBoxLayout, QLabel, QLineEdit,
    QSizePolicy, QSpacerItem, QToolButton, QVBoxLayout,
    QWidget)

class Ui_QSpectrumAnalyzerBaseline(object):
    def setupUi(self, QSpectrumAnalyzerBaseline):
        if not QSpectrumAnalyzerBaseline.objectName():
            QSpectrumAnalyzerBaseline.setObjectName(u"QSpectrumAnalyzerBaseline")
        QSpectrumAnalyzerBaseline.resize(500, 100)
        self.verticalLayout = QVBoxLayout(QSpectrumAnalyzerBaseline)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.label = QLabel(QSpectrumAnalyzerBaseline)
        self.label.setObjectName(u"label")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.label)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.baselineFileEdit = QLineEdit(QSpectrumAnalyzerBaseline)
        self.baselineFileEdit.setObjectName(u"baselineFileEdit")

        self.horizontalLayout.addWidget(self.baselineFileEdit)

        self.baselineFileButton = QToolButton(QSpectrumAnalyzerBaseline)
        self.baselineFileButton.setObjectName(u"baselineFileButton")
        self.baselineFileButton.setMinimumSize(QSize(50, 0))

        self.horizontalLayout.addWidget(self.baselineFileButton)


        self.formLayout.setLayout(0, QFormLayout.ItemRole.FieldRole, self.horizontalLayout)


        self.verticalLayout.addLayout(self.formLayout)

        self.verticalSpacer = QSpacerItem(20, 1, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.buttonBox = QDialogButtonBox(QSpectrumAnalyzerBaseline)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.verticalLayout.addWidget(self.buttonBox)

#if QT_CONFIG(shortcut)
        self.label.setBuddy(self.baselineFileEdit)
#endif // QT_CONFIG(shortcut)
        QWidget.setTabOrder(self.baselineFileEdit, self.baselineFileButton)

        self.retranslateUi(QSpectrumAnalyzerBaseline)
        self.buttonBox.accepted.connect(QSpectrumAnalyzerBaseline.accept)
        self.buttonBox.rejected.connect(QSpectrumAnalyzerBaseline.reject)

        QMetaObject.connectSlotsByName(QSpectrumAnalyzerBaseline)
    # setupUi

    def retranslateUi(self, QSpectrumAnalyzerBaseline):
        QSpectrumAnalyzerBaseline.setWindowTitle(QCoreApplication.translate("QSpectrumAnalyzerBaseline", u"Baseline - QSpectrumAnalyzer", None))
        self.label.setText(QCoreApplication.translate("QSpectrumAnalyzerBaseline", u"Baseline &file:", None))
        self.baselineFileButton.setText(QCoreApplication.translate("QSpectrumAnalyzerBaseline", u"...", None))
    # retranslateUi

