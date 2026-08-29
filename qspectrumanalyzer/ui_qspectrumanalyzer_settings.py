# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'qspectrumanalyzer_settings.ui'
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
    QDialogButtonBox, QDoubleSpinBox, QFormLayout, QHBoxLayout,
    QLabel, QLineEdit, QSizePolicy, QSpacerItem,
    QSpinBox, QToolButton, QVBoxLayout, QWidget)

class Ui_QSpectrumAnalyzerSettings(object):
    def setupUi(self, QSpectrumAnalyzerSettings):
        if not QSpectrumAnalyzerSettings.objectName():
            QSpectrumAnalyzerSettings.setObjectName(u"QSpectrumAnalyzerSettings")
        QSpectrumAnalyzerSettings.resize(600, 388)
        self.verticalLayout = QVBoxLayout(QSpectrumAnalyzerSettings)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.label_3 = QLabel(QSpectrumAnalyzerSettings)
        self.label_3.setObjectName(u"label_3")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.label_3)

        self.backendComboBox = QComboBox(QSpectrumAnalyzerSettings)
        self.backendComboBox.addItem("")
        self.backendComboBox.addItem("")
        self.backendComboBox.addItem("")
        self.backendComboBox.addItem("")
        self.backendComboBox.addItem("")
        self.backendComboBox.setObjectName(u"backendComboBox")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.backendComboBox)

        self.label = QLabel(QSpectrumAnalyzerSettings)
        self.label.setObjectName(u"label")

        self.formLayout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.label)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.executableEdit = QLineEdit(QSpectrumAnalyzerSettings)
        self.executableEdit.setObjectName(u"executableEdit")

        self.horizontalLayout.addWidget(self.executableEdit)

        self.executableButton = QToolButton(QSpectrumAnalyzerSettings)
        self.executableButton.setObjectName(u"executableButton")
        self.executableButton.setMinimumSize(QSize(50, 0))

        self.horizontalLayout.addWidget(self.executableButton)


        self.formLayout.setLayout(1, QFormLayout.ItemRole.FieldRole, self.horizontalLayout)

        self.label_5 = QLabel(QSpectrumAnalyzerSettings)
        self.label_5.setObjectName(u"label_5")

        self.formLayout.setWidget(3, QFormLayout.ItemRole.LabelRole, self.label_5)

        self.label_4 = QLabel(QSpectrumAnalyzerSettings)
        self.label_4.setObjectName(u"label_4")

        self.formLayout.setWidget(4, QFormLayout.ItemRole.LabelRole, self.label_4)

        self.label_2 = QLabel(QSpectrumAnalyzerSettings)
        self.label_2.setObjectName(u"label_2")

        self.formLayout.setWidget(7, QFormLayout.ItemRole.LabelRole, self.label_2)

        self.waterfallHistorySizeSpinBox = QSpinBox(QSpectrumAnalyzerSettings)
        self.waterfallHistorySizeSpinBox.setObjectName(u"waterfallHistorySizeSpinBox")
        self.waterfallHistorySizeSpinBox.setMinimum(1)
        self.waterfallHistorySizeSpinBox.setMaximum(10000000)
        self.waterfallHistorySizeSpinBox.setValue(100)

        self.formLayout.setWidget(7, QFormLayout.ItemRole.FieldRole, self.waterfallHistorySizeSpinBox)

        self.label_7 = QLabel(QSpectrumAnalyzerSettings)
        self.label_7.setObjectName(u"label_7")

        self.formLayout.setWidget(5, QFormLayout.ItemRole.LabelRole, self.label_7)

        self.label_8 = QLabel(QSpectrumAnalyzerSettings)
        self.label_8.setObjectName(u"label_8")

        self.formLayout.setWidget(6, QFormLayout.ItemRole.LabelRole, self.label_8)

        self.label_6 = QLabel(QSpectrumAnalyzerSettings)
        self.label_6.setObjectName(u"label_6")

        self.formLayout.setWidget(2, QFormLayout.ItemRole.LabelRole, self.label_6)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.paramsEdit = QLineEdit(QSpectrumAnalyzerSettings)
        self.paramsEdit.setObjectName(u"paramsEdit")

        self.horizontalLayout_2.addWidget(self.paramsEdit)

        self.paramsHelpButton = QToolButton(QSpectrumAnalyzerSettings)
        self.paramsHelpButton.setObjectName(u"paramsHelpButton")
        self.paramsHelpButton.setMinimumSize(QSize(50, 0))

        self.horizontalLayout_2.addWidget(self.paramsHelpButton)


        self.formLayout.setLayout(2, QFormLayout.ItemRole.FieldRole, self.horizontalLayout_2)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.deviceEdit = QLineEdit(QSpectrumAnalyzerSettings)
        self.deviceEdit.setObjectName(u"deviceEdit")

        self.horizontalLayout_3.addWidget(self.deviceEdit)

        self.deviceHelpButton = QToolButton(QSpectrumAnalyzerSettings)
        self.deviceHelpButton.setObjectName(u"deviceHelpButton")
        self.deviceHelpButton.setMinimumSize(QSize(50, 0))

        self.horizontalLayout_3.addWidget(self.deviceHelpButton)


        self.formLayout.setLayout(3, QFormLayout.ItemRole.FieldRole, self.horizontalLayout_3)

        self.sampleRateSpinBox = QDoubleSpinBox(QSpectrumAnalyzerSettings)
        self.sampleRateSpinBox.setObjectName(u"sampleRateSpinBox")
        self.sampleRateSpinBox.setProperty(u"showGroupSeparator", True)
        self.sampleRateSpinBox.setDecimals(3)
        self.sampleRateSpinBox.setMinimum(0.000000000000000)
        self.sampleRateSpinBox.setMaximum(999999.989999999990687)
        self.sampleRateSpinBox.setSingleStep(0.010000000000000)
        self.sampleRateSpinBox.setValue(61.439999999999998)

        self.formLayout.setWidget(4, QFormLayout.ItemRole.FieldRole, self.sampleRateSpinBox)

        self.bandwidthSpinBox = QDoubleSpinBox(QSpectrumAnalyzerSettings)
        self.bandwidthSpinBox.setObjectName(u"bandwidthSpinBox")
        self.bandwidthSpinBox.setProperty(u"showGroupSeparator", True)
        self.bandwidthSpinBox.setDecimals(3)
        self.bandwidthSpinBox.setMinimum(0.000000000000000)
        self.bandwidthSpinBox.setMaximum(999999.989999999990687)
        self.bandwidthSpinBox.setSingleStep(0.010000000000000)
        self.bandwidthSpinBox.setValue(0.000000000000000)

        self.formLayout.setWidget(5, QFormLayout.ItemRole.FieldRole, self.bandwidthSpinBox)

        self.lnbSpinBox = QDoubleSpinBox(QSpectrumAnalyzerSettings)
        self.lnbSpinBox.setObjectName(u"lnbSpinBox")
        self.lnbSpinBox.setProperty(u"showGroupSeparator", True)
        self.lnbSpinBox.setDecimals(3)
        self.lnbSpinBox.setMinimum(-999999.998999999952503)
        self.lnbSpinBox.setMaximum(999999.998999999952503)
        self.lnbSpinBox.setSingleStep(0.010000000000000)
        self.lnbSpinBox.setValue(0.000000000000000)

        self.formLayout.setWidget(6, QFormLayout.ItemRole.FieldRole, self.lnbSpinBox)


        self.verticalLayout.addLayout(self.formLayout)

        self.verticalSpacer = QSpacerItem(20, 21, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.buttonBox = QDialogButtonBox(QSpectrumAnalyzerSettings)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.verticalLayout.addWidget(self.buttonBox)

#if QT_CONFIG(shortcut)
        self.label_3.setBuddy(self.backendComboBox)
        self.label.setBuddy(self.executableEdit)
        self.label_5.setBuddy(self.deviceEdit)
        self.label_4.setBuddy(self.sampleRateSpinBox)
        self.label_2.setBuddy(self.waterfallHistorySizeSpinBox)
        self.label_7.setBuddy(self.bandwidthSpinBox)
        self.label_8.setBuddy(self.lnbSpinBox)
        self.label_6.setBuddy(self.paramsEdit)
#endif // QT_CONFIG(shortcut)
        QWidget.setTabOrder(self.backendComboBox, self.executableEdit)
        QWidget.setTabOrder(self.executableEdit, self.executableButton)
        QWidget.setTabOrder(self.executableButton, self.paramsEdit)
        QWidget.setTabOrder(self.paramsEdit, self.paramsHelpButton)
        QWidget.setTabOrder(self.paramsHelpButton, self.deviceEdit)
        QWidget.setTabOrder(self.deviceEdit, self.deviceHelpButton)
        QWidget.setTabOrder(self.deviceHelpButton, self.sampleRateSpinBox)
        QWidget.setTabOrder(self.sampleRateSpinBox, self.bandwidthSpinBox)
        QWidget.setTabOrder(self.bandwidthSpinBox, self.lnbSpinBox)
        QWidget.setTabOrder(self.lnbSpinBox, self.waterfallHistorySizeSpinBox)

        self.retranslateUi(QSpectrumAnalyzerSettings)
        self.buttonBox.accepted.connect(QSpectrumAnalyzerSettings.accept)
        self.buttonBox.rejected.connect(QSpectrumAnalyzerSettings.reject)

        QMetaObject.connectSlotsByName(QSpectrumAnalyzerSettings)
    # setupUi

    def retranslateUi(self, QSpectrumAnalyzerSettings):
        QSpectrumAnalyzerSettings.setWindowTitle(QCoreApplication.translate("QSpectrumAnalyzerSettings", u"Settings - QSpectrumAnalyzer", None))
        self.label_3.setText(QCoreApplication.translate("QSpectrumAnalyzerSettings", u"&Backend:", None))
        self.backendComboBox.setItemText(0, QCoreApplication.translate("QSpectrumAnalyzerSettings", u"soapy_power", None))
        self.backendComboBox.setItemText(1, QCoreApplication.translate("QSpectrumAnalyzerSettings", u"rx_power", None))
        self.backendComboBox.setItemText(2, QCoreApplication.translate("QSpectrumAnalyzerSettings", u"rtl_power_fftw", None))
        self.backendComboBox.setItemText(3, QCoreApplication.translate("QSpectrumAnalyzerSettings", u"rtl_power", None))
        self.backendComboBox.setItemText(4, QCoreApplication.translate("QSpectrumAnalyzerSettings", u"hackrf_sweep", None))

        self.label.setText(QCoreApplication.translate("QSpectrumAnalyzerSettings", u"E&xecutable:", None))
        self.executableEdit.setText(QCoreApplication.translate("QSpectrumAnalyzerSettings", u"soapy_power", None))
        self.executableButton.setText(QCoreApplication.translate("QSpectrumAnalyzerSettings", u"...", None))
        self.label_5.setText(QCoreApplication.translate("QSpectrumAnalyzerSettings", u"&Device:", None))
        self.label_4.setText(QCoreApplication.translate("QSpectrumAnalyzerSettings", u"Sa&mple rate:", None))
        self.label_2.setText(QCoreApplication.translate("QSpectrumAnalyzerSettings", u"&Waterfall history size:", None))
        self.label_7.setText(QCoreApplication.translate("QSpectrumAnalyzerSettings", u"Bandwidt&h:", None))
#if QT_CONFIG(tooltip)
        self.label_8.setToolTip(QCoreApplication.translate("QSpectrumAnalyzerSettings", u"Negative frequency for upconverters, positive frequency for downconverters.", None))
#endif // QT_CONFIG(tooltip)
        self.label_8.setText(QCoreApplication.translate("QSpectrumAnalyzerSettings", u"&LNB LO:", None))
        self.label_6.setText(QCoreApplication.translate("QSpectrumAnalyzerSettings", u"Add&itional parameters:", None))
        self.paramsHelpButton.setText(QCoreApplication.translate("QSpectrumAnalyzerSettings", u" ? ", None))
        self.deviceHelpButton.setText(QCoreApplication.translate("QSpectrumAnalyzerSettings", u" ? ", None))
        self.sampleRateSpinBox.setSuffix(QCoreApplication.translate("QSpectrumAnalyzerSettings", u" MHz", None))
        self.bandwidthSpinBox.setSuffix(QCoreApplication.translate("QSpectrumAnalyzerSettings", u" MHz", None))
#if QT_CONFIG(tooltip)
        self.lnbSpinBox.setToolTip(QCoreApplication.translate("QSpectrumAnalyzerSettings", u"Negative frequency for upconverters, positive frequency for downconverters.", None))
#endif // QT_CONFIG(tooltip)
        self.lnbSpinBox.setSuffix(QCoreApplication.translate("QSpectrumAnalyzerSettings", u" MHz", None))
    # retranslateUi

