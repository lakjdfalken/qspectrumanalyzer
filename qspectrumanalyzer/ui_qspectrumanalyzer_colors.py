# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'qspectrumanalyzer_colors.ui'
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
    QFormLayout, QLabel, QSizePolicy, QSpacerItem,
    QVBoxLayout, QWidget)

from pyqtgraph import ColorButton

class Ui_QSpectrumAnalyzerColors(object):
    def setupUi(self, QSpectrumAnalyzerColors):
        if not QSpectrumAnalyzerColors.objectName():
            QSpectrumAnalyzerColors.setObjectName(u"QSpectrumAnalyzerColors")
        QSpectrumAnalyzerColors.resize(253, 266)
        self.verticalLayout = QVBoxLayout(QSpectrumAnalyzerColors)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.label_2 = QLabel(QSpectrumAnalyzerColors)
        self.label_2.setObjectName(u"label_2")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.label_2)

        self.mainColorButton = ColorButton(QSpectrumAnalyzerColors)
        self.mainColorButton.setObjectName(u"mainColorButton")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.mainColorButton.sizePolicy().hasHeightForWidth())
        self.mainColorButton.setSizePolicy(sizePolicy)

        self.formLayout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.mainColorButton)

        self.label_4 = QLabel(QSpectrumAnalyzerColors)
        self.label_4.setObjectName(u"label_4")

        self.formLayout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.label_4)

        self.peakHoldMaxColorButton = ColorButton(QSpectrumAnalyzerColors)
        self.peakHoldMaxColorButton.setObjectName(u"peakHoldMaxColorButton")
        sizePolicy.setHeightForWidth(self.peakHoldMaxColorButton.sizePolicy().hasHeightForWidth())
        self.peakHoldMaxColorButton.setSizePolicy(sizePolicy)

        self.formLayout.setWidget(1, QFormLayout.ItemRole.FieldRole, self.peakHoldMaxColorButton)

        self.label_6 = QLabel(QSpectrumAnalyzerColors)
        self.label_6.setObjectName(u"label_6")

        self.formLayout.setWidget(2, QFormLayout.ItemRole.LabelRole, self.label_6)

        self.peakHoldMinColorButton = ColorButton(QSpectrumAnalyzerColors)
        self.peakHoldMinColorButton.setObjectName(u"peakHoldMinColorButton")
        sizePolicy.setHeightForWidth(self.peakHoldMinColorButton.sizePolicy().hasHeightForWidth())
        self.peakHoldMinColorButton.setSizePolicy(sizePolicy)

        self.formLayout.setWidget(2, QFormLayout.ItemRole.FieldRole, self.peakHoldMinColorButton)

        self.label_5 = QLabel(QSpectrumAnalyzerColors)
        self.label_5.setObjectName(u"label_5")

        self.formLayout.setWidget(3, QFormLayout.ItemRole.LabelRole, self.label_5)

        self.averageColorButton = ColorButton(QSpectrumAnalyzerColors)
        self.averageColorButton.setObjectName(u"averageColorButton")
        sizePolicy.setHeightForWidth(self.averageColorButton.sizePolicy().hasHeightForWidth())
        self.averageColorButton.setSizePolicy(sizePolicy)

        self.formLayout.setWidget(3, QFormLayout.ItemRole.FieldRole, self.averageColorButton)

        self.label_3 = QLabel(QSpectrumAnalyzerColors)
        self.label_3.setObjectName(u"label_3")

        self.formLayout.setWidget(4, QFormLayout.ItemRole.LabelRole, self.label_3)

        self.persistenceColorButton = ColorButton(QSpectrumAnalyzerColors)
        self.persistenceColorButton.setObjectName(u"persistenceColorButton")
        sizePolicy.setHeightForWidth(self.persistenceColorButton.sizePolicy().hasHeightForWidth())
        self.persistenceColorButton.setSizePolicy(sizePolicy)

        self.formLayout.setWidget(4, QFormLayout.ItemRole.FieldRole, self.persistenceColorButton)

        self.label = QLabel(QSpectrumAnalyzerColors)
        self.label.setObjectName(u"label")

        self.formLayout.setWidget(5, QFormLayout.ItemRole.LabelRole, self.label)

        self.baselineColorButton = ColorButton(QSpectrumAnalyzerColors)
        self.baselineColorButton.setObjectName(u"baselineColorButton")
        sizePolicy.setHeightForWidth(self.baselineColorButton.sizePolicy().hasHeightForWidth())
        self.baselineColorButton.setSizePolicy(sizePolicy)

        self.formLayout.setWidget(5, QFormLayout.ItemRole.FieldRole, self.baselineColorButton)


        self.verticalLayout.addLayout(self.formLayout)

        self.verticalSpacer = QSpacerItem(20, 2, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.buttonBox = QDialogButtonBox(QSpectrumAnalyzerColors)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.verticalLayout.addWidget(self.buttonBox)

#if QT_CONFIG(shortcut)
        self.label_2.setBuddy(self.mainColorButton)
        self.label_4.setBuddy(self.peakHoldMaxColorButton)
        self.label_6.setBuddy(self.peakHoldMinColorButton)
        self.label_5.setBuddy(self.averageColorButton)
        self.label_3.setBuddy(self.persistenceColorButton)
        self.label.setBuddy(self.baselineColorButton)
#endif // QT_CONFIG(shortcut)
        QWidget.setTabOrder(self.mainColorButton, self.peakHoldMaxColorButton)
        QWidget.setTabOrder(self.peakHoldMaxColorButton, self.peakHoldMinColorButton)
        QWidget.setTabOrder(self.peakHoldMinColorButton, self.averageColorButton)
        QWidget.setTabOrder(self.averageColorButton, self.persistenceColorButton)
        QWidget.setTabOrder(self.persistenceColorButton, self.baselineColorButton)

        self.retranslateUi(QSpectrumAnalyzerColors)
        self.buttonBox.accepted.connect(QSpectrumAnalyzerColors.accept)
        self.buttonBox.rejected.connect(QSpectrumAnalyzerColors.reject)

        QMetaObject.connectSlotsByName(QSpectrumAnalyzerColors)
    # setupUi

    def retranslateUi(self, QSpectrumAnalyzerColors):
        QSpectrumAnalyzerColors.setWindowTitle(QCoreApplication.translate("QSpectrumAnalyzerColors", u"Colors - QSpectrumAnalyzer", None))
        self.label_2.setText(QCoreApplication.translate("QSpectrumAnalyzerColors", u"&Main curve color:", None))
        self.mainColorButton.setText(QCoreApplication.translate("QSpectrumAnalyzerColors", u"...", None))
        self.label_4.setText(QCoreApplication.translate("QSpectrumAnalyzerColors", u"Max. peak &hold color:", None))
        self.peakHoldMaxColorButton.setText(QCoreApplication.translate("QSpectrumAnalyzerColors", u"...", None))
        self.label_6.setText(QCoreApplication.translate("QSpectrumAnalyzerColors", u"M&in. peak hold color:", None))
        self.peakHoldMinColorButton.setText(QCoreApplication.translate("QSpectrumAnalyzerColors", u"...", None))
        self.label_5.setText(QCoreApplication.translate("QSpectrumAnalyzerColors", u"Average &color:", None))
        self.averageColorButton.setText(QCoreApplication.translate("QSpectrumAnalyzerColors", u"...", None))
        self.label_3.setText(QCoreApplication.translate("QSpectrumAnalyzerColors", u"Persistence co&lor:", None))
        self.persistenceColorButton.setText(QCoreApplication.translate("QSpectrumAnalyzerColors", u"...", None))
        self.label.setText(QCoreApplication.translate("QSpectrumAnalyzerColors", u"&Baseline color:", None))
        self.baselineColorButton.setText(QCoreApplication.translate("QSpectrumAnalyzerColors", u"...", None))
    # retranslateUi

