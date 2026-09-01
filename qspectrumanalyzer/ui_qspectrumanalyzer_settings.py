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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QCheckBox, QComboBox,
    QDialog, QDialogButtonBox, QDoubleSpinBox, QFormLayout,
    QHBoxLayout, QLabel, QLineEdit, QSizePolicy,
    QSpacerItem, QSpinBox, QToolButton, QVBoxLayout,
    QWidget)

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

        self.label_10 = QLabel(QSpectrumAnalyzerSettings)
        self.label_10.setObjectName(u"label_10")

        self.formLayout.setWidget(8, QFormLayout.ItemRole.LabelRole, self.label_10)

        self.recordDepthSpinBox = QSpinBox(QSpectrumAnalyzerSettings)
        self.recordDepthSpinBox.setObjectName(u"recordDepthSpinBox")
        self.recordDepthSpinBox.setMinimum(1)
        self.recordDepthSpinBox.setMaximum(10000000)
        self.recordDepthSpinBox.setValue(1000)

        self.formLayout.setWidget(8, QFormLayout.ItemRole.FieldRole, self.recordDepthSpinBox)

        self.recordDepthEstimateLabel = QLabel(QSpectrumAnalyzerSettings)
        self.recordDepthEstimateLabel.setObjectName(u"recordDepthEstimateLabel")
        self.recordDepthEstimateLabel.setWordWrap(True)

        self.formLayout.setWidget(9, QFormLayout.ItemRole.FieldRole, self.recordDepthEstimateLabel)

        self.tapResolutionLabel = QLabel(QSpectrumAnalyzerSettings)
        self.tapResolutionLabel.setObjectName(u"tapResolutionLabel")

        self.formLayout.setWidget(11, QFormLayout.ItemRole.LabelRole, self.tapResolutionLabel)

        self.tapResolutionSpinBox = QDoubleSpinBox(QSpectrumAnalyzerSettings)
        self.tapResolutionSpinBox.setObjectName(u"tapResolutionSpinBox")
        self.tapResolutionSpinBox.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.tapResolutionSpinBox.setDecimals(1)
        self.tapResolutionSpinBox.setMaximum(100000.000000000000000)

        self.formLayout.setWidget(11, QFormLayout.ItemRole.FieldRole, self.tapResolutionSpinBox)

        self.tapDetectorLabel = QLabel(QSpectrumAnalyzerSettings)
        self.tapDetectorLabel.setObjectName(u"tapDetectorLabel")

        self.formLayout.setWidget(12, QFormLayout.ItemRole.LabelRole, self.tapDetectorLabel)

        self.tapDetectorComboBox = QComboBox(QSpectrumAnalyzerSettings)
        self.tapDetectorComboBox.addItem("")
        self.tapDetectorComboBox.addItem("")
        self.tapDetectorComboBox.addItem("")
        self.tapDetectorComboBox.setObjectName(u"tapDetectorComboBox")

        self.formLayout.setWidget(12, QFormLayout.ItemRole.FieldRole, self.tapDetectorComboBox)

        self.sweepDetectorLabel = QLabel(QSpectrumAnalyzerSettings)
        self.sweepDetectorLabel.setObjectName(u"sweepDetectorLabel")

        self.formLayout.setWidget(13, QFormLayout.ItemRole.LabelRole, self.sweepDetectorLabel)

        self.sweepDetectorComboBox = QComboBox(QSpectrumAnalyzerSettings)
        self.sweepDetectorComboBox.addItem("")
        self.sweepDetectorComboBox.addItem("")
        self.sweepDetectorComboBox.setObjectName(u"sweepDetectorComboBox")

        self.formLayout.setWidget(13, QFormLayout.ItemRole.FieldRole, self.sweepDetectorComboBox)

        self.tapEstimateLabel = QLabel(QSpectrumAnalyzerSettings)
        self.tapEstimateLabel.setObjectName(u"tapEstimateLabel")
        self.tapEstimateLabel.setWordWrap(True)

        self.formLayout.setWidget(15, QFormLayout.ItemRole.FieldRole, self.tapEstimateLabel)

        self.levelsMeterCheckBox = QCheckBox(QSpectrumAnalyzerSettings)
        self.levelsMeterCheckBox.setObjectName(u"levelsMeterCheckBox")
        self.levelsMeterCheckBox.setChecked(True)

        self.formLayout.setWidget(17, QFormLayout.ItemRole.SpanningRole, self.levelsMeterCheckBox)

        self.antialiasCheckBox = QCheckBox(QSpectrumAnalyzerSettings)
        self.antialiasCheckBox.setObjectName(u"antialiasCheckBox")
        self.antialiasCheckBox.setChecked(True)

        self.formLayout.setWidget(16, QFormLayout.ItemRole.SpanningRole, self.antialiasCheckBox)

        self.label_9 = QLabel(QSpectrumAnalyzerSettings)
        self.label_9.setObjectName(u"label_9")

        self.formLayout.setWidget(10, QFormLayout.ItemRole.LabelRole, self.label_9)

        self.maxRefreshRateSpinBox = QSpinBox(QSpectrumAnalyzerSettings)
        self.maxRefreshRateSpinBox.setObjectName(u"maxRefreshRateSpinBox")
        self.maxRefreshRateSpinBox.setMinimum(0)
        self.maxRefreshRateSpinBox.setMaximum(1000)
        self.maxRefreshRateSpinBox.setValue(60)

        self.formLayout.setWidget(10, QFormLayout.ItemRole.FieldRole, self.maxRefreshRateSpinBox)

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
        self.deviceEdit = QComboBox(QSpectrumAnalyzerSettings)
        self.deviceEdit.setObjectName(u"deviceEdit")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.deviceEdit.sizePolicy().hasHeightForWidth())
        self.deviceEdit.setSizePolicy(sizePolicy)
        self.deviceEdit.setEditable(True)
        self.deviceEdit.setInsertPolicy(QComboBox.NoInsert)
        self.deviceEdit.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.deviceEdit.setMinimumContentsLength(28)

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
        self.label_10.setBuddy(self.recordDepthSpinBox)
        self.tapResolutionLabel.setBuddy(self.tapResolutionSpinBox)
        self.tapDetectorLabel.setBuddy(self.tapDetectorComboBox)
        self.sweepDetectorLabel.setBuddy(self.sweepDetectorComboBox)
        self.label_9.setBuddy(self.maxRefreshRateSpinBox)
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
        QWidget.setTabOrder(self.waterfallHistorySizeSpinBox, self.recordDepthSpinBox)
        QWidget.setTabOrder(self.recordDepthSpinBox, self.tapResolutionSpinBox)
        QWidget.setTabOrder(self.tapResolutionSpinBox, self.tapDetectorComboBox)
        QWidget.setTabOrder(self.tapDetectorComboBox, self.sweepDetectorComboBox)
        QWidget.setTabOrder(self.sweepDetectorComboBox, self.maxRefreshRateSpinBox)

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
#if QT_CONFIG(tooltip)
        self.label_2.setToolTip(QCoreApplication.translate("QSpectrumAnalyzerSettings", u"How many sweeps the waterfall plot shows. Independent of how many are recorded.", None))
#endif // QT_CONFIG(tooltip)
        self.label_2.setText(QCoreApplication.translate("QSpectrumAnalyzerSettings", u"&Waterfall rows shown:", None))
#if QT_CONFIG(tooltip)
        self.label_10.setToolTip(QCoreApplication.translate("QSpectrumAnalyzerSettings", u"How many sweeps are kept for the history browser to step through. Costs memory: one sweep is 4 bytes per bin.", None))
#endif // QT_CONFIG(tooltip)
        self.label_10.setText(QCoreApplication.translate("QSpectrumAnalyzerSettings", u"Record&ing depth:", None))
#if QT_CONFIG(tooltip)
        self.recordDepthSpinBox.setToolTip(QCoreApplication.translate("QSpectrumAnalyzerSettings", u"How many sweeps are kept for the history browser to step through. Costs memory: one sweep is 4 bytes per bin.", None))
#endif // QT_CONFIG(tooltip)
        self.recordDepthSpinBox.setSuffix(QCoreApplication.translate("QSpectrumAnalyzerSettings", u" sweeps", None))
        self.recordDepthEstimateLabel.setText("")
#if QT_CONFIG(tooltip)
        self.tapResolutionLabel.setToolTip(QCoreApplication.translate("QSpectrumAnalyzerSettings", u"Seconds of signal behind each reading of the oscilloscope's high-rate tap. This is the zero span timebase: smaller resolves shorter bursts, at a higher noise floor, because fewer frames are combined into each reading.", None))
#endif // QT_CONFIG(tooltip)
        self.tapResolutionLabel.setText(QCoreApplication.translate("QSpectrumAnalyzerSettings", u"&Zero span step:", None))
#if QT_CONFIG(tooltip)
        self.tapResolutionSpinBox.setToolTip(QCoreApplication.translate("QSpectrumAnalyzerSettings", u"Seconds of signal behind each reading of the oscilloscope's high-rate tap. Rounded to whole FFT frames, so what you get is shown below. Zero asks for the finest the radio can be read at, which is one frame.", None))
#endif // QT_CONFIG(tooltip)
        self.tapResolutionSpinBox.setSuffix(QCoreApplication.translate("QSpectrumAnalyzerSettings", u" us", None))
        self.tapResolutionSpinBox.setSpecialValueText(QCoreApplication.translate("QSpectrumAnalyzerSettings", u"finest", None))
        self.tapDetectorLabel.setText(QCoreApplication.translate("QSpectrumAnalyzerSettings", u"Zero span &detector:", None))
        self.tapDetectorComboBox.setItemText(0, QCoreApplication.translate("QSpectrumAnalyzerSettings", u"Peak (catch short pulses)", None))
        self.tapDetectorComboBox.setItemText(1, QCoreApplication.translate("QSpectrumAnalyzerSettings", u"Average (smooth the shape)", None))
        self.tapDetectorComboBox.setItemText(2, QCoreApplication.translate("QSpectrumAnalyzerSettings", u"Total across the band (wide pulses)", None))

#if QT_CONFIG(tooltip)
        self.tapDetectorComboBox.setToolTip(QCoreApplication.translate("QSpectrumAnalyzerSettings", u"How the frames making up one reading are combined, which is the video bandwidth choice. Peak keeps the loudest frame, so a pulse shorter than the step still reads at its own height; it does not smooth. Average smooths as the square root of the number of frames, which is what makes the shape of a signal legible when it is only a few dB out of the noise. At the finest step there is one frame per reading and the two are the same. Total is a different question: peak and average both keep the loudest bin of the band and discard the rest, which is right for a carrier in one bin and wrong for a pulse spread over many. Total adds the bins instead, worth about 3 dB on a chirp when the band is matched to it, and worth less than nothing when the band is much wider than the signal.", None))
#endif // QT_CONFIG(tooltip)
        self.sweepDetectorLabel.setText(QCoreApplication.translate("QSpectrumAnalyzerSettings", u"S&weep detector:", None))
        self.sweepDetectorComboBox.setItemText(0, QCoreApplication.translate("QSpectrumAnalyzerSettings", u"Average (quieter floor)", None))
        self.sweepDetectorComboBox.setItemText(1, QCoreApplication.translate("QSpectrumAnalyzerSettings", u"Peak (keeps short pulses)", None))

#if QT_CONFIG(tooltip)
        self.sweepDetectorComboBox.setToolTip(QCoreApplication.translate("QSpectrumAnalyzerSettings", u"How the frames making up one delivered sweep are combined. Average pulls the noise floor down by the square root of the count and is right for a signal that is always there. Peak keeps the loudest frame instead, so a pulse far shorter than a sweep survives at its own height rather than being spread across the whole average: worth 14 dB on a microsecond pulse, at the cost of a noise floor a few dB higher. Backends that deliver sweeps whole ignore it.", None))
#endif // QT_CONFIG(tooltip)
        self.tapEstimateLabel.setText("")
#if QT_CONFIG(tooltip)
        self.levelsMeterCheckBox.setToolTip(QCoreApplication.translate("QSpectrumAnalyzerSettings", u"The colour scale beside the waterfall, which also sets its levels and gradient. It recomputes a histogram of the whole waterfall on every redraw, so turning it off is faster.", None))
#endif // QT_CONFIG(tooltip)
        self.levelsMeterCheckBox.setText(QCoreApplication.translate("QSpectrumAnalyzerSettings", u"Show the waterfall &level meter", None))
#if QT_CONFIG(tooltip)
        self.antialiasCheckBox.setToolTip(QCoreApplication.translate("QSpectrumAnalyzerSettings", u"Smooth the curves. Turning it off is faster, but the traces look harder edged.", None))
#endif // QT_CONFIG(tooltip)
        self.antialiasCheckBox.setText(QCoreApplication.translate("QSpectrumAnalyzerSettings", u"&Antialias the curves", None))
#if QT_CONFIG(tooltip)
        self.label_9.setToolTip(QCoreApplication.translate("QSpectrumAnalyzerSettings", u"Upper limit on how often the plots are redrawn. Sweeps arriving faster than this are still recorded in full, only redundant redraws are skipped. 0 means no limit.", None))
#endif // QT_CONFIG(tooltip)
        self.label_9.setText(QCoreApplication.translate("QSpectrumAnalyzerSettings", u"Max &redraw rate:", None))
#if QT_CONFIG(tooltip)
        self.maxRefreshRateSpinBox.setToolTip(QCoreApplication.translate("QSpectrumAnalyzerSettings", u"Upper limit on how often the plots are redrawn. Sweeps arriving faster than this are still recorded in full, only redundant redraws are skipped. 0 means no limit.", None))
#endif // QT_CONFIG(tooltip)
        self.maxRefreshRateSpinBox.setSpecialValueText(QCoreApplication.translate("QSpectrumAnalyzerSettings", u"No limit", None))
        self.maxRefreshRateSpinBox.setSuffix(QCoreApplication.translate("QSpectrumAnalyzerSettings", u" Hz", None))
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

