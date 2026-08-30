# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'qspectrumanalyzer.ui'
##
## Created by: Qt User Interface Compiler version 6.11.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDockWidget,
    QDoubleSpinBox, QFormLayout, QGridLayout, QGroupBox,
    QHBoxLayout, QLabel, QMainWindow, QMenu,
    QMenuBar, QPushButton, QSizePolicy, QSlider,
    QSpacerItem, QSpinBox, QSplitter, QStatusBar,
    QToolButton, QVBoxLayout, QWidget)

from pyqtgraph import GraphicsLayoutWidget

class Ui_QSpectrumAnalyzerMainWindow(object):
    def setupUi(self, QSpectrumAnalyzerMainWindow):
        if not QSpectrumAnalyzerMainWindow.objectName():
            QSpectrumAnalyzerMainWindow.setObjectName(u"QSpectrumAnalyzerMainWindow")
        QSpectrumAnalyzerMainWindow.resize(1200, 892)
        self.action_Settings = QAction(QSpectrumAnalyzerMainWindow)
        self.action_Settings.setObjectName(u"action_Settings")
        self.action_Quit = QAction(QSpectrumAnalyzerMainWindow)
        self.action_Quit.setObjectName(u"action_Quit")
        self.action_About = QAction(QSpectrumAnalyzerMainWindow)
        self.action_About.setObjectName(u"action_About")
        self.centralwidget = QWidget(QSpectrumAnalyzerMainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.horizontalLayout = QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.plotSplitter = QSplitter(self.centralwidget)
        self.plotSplitter.setObjectName(u"plotSplitter")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.plotSplitter.sizePolicy().hasHeightForWidth())
        self.plotSplitter.setSizePolicy(sizePolicy)
        self.plotSplitter.setOrientation(Qt.Vertical)
        self.mainPlotLayout = GraphicsLayoutWidget(self.plotSplitter)
        self.mainPlotLayout.setObjectName(u"mainPlotLayout")
        sizePolicy.setHeightForWidth(self.mainPlotLayout.sizePolicy().hasHeightForWidth())
        self.mainPlotLayout.setSizePolicy(sizePolicy)
        self.plotSplitter.addWidget(self.mainPlotLayout)
        self.waterfallPlotLayout = GraphicsLayoutWidget(self.plotSplitter)
        self.waterfallPlotLayout.setObjectName(u"waterfallPlotLayout")
        sizePolicy.setHeightForWidth(self.waterfallPlotLayout.sizePolicy().hasHeightForWidth())
        self.waterfallPlotLayout.setSizePolicy(sizePolicy)
        self.plotSplitter.addWidget(self.waterfallPlotLayout)
        self.scopePlotLayout = GraphicsLayoutWidget(self.plotSplitter)
        self.scopePlotLayout.setObjectName(u"scopePlotLayout")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.scopePlotLayout.sizePolicy().hasHeightForWidth())
        self.scopePlotLayout.setSizePolicy(sizePolicy1)
        self.plotSplitter.addWidget(self.scopePlotLayout)

        self.horizontalLayout.addWidget(self.plotSplitter)

        QSpectrumAnalyzerMainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(QSpectrumAnalyzerMainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1200, 32))
        self.menu_File = QMenu(self.menubar)
        self.menu_File.setObjectName(u"menu_File")
        self.menu_Help = QMenu(self.menubar)
        self.menu_Help.setObjectName(u"menu_Help")
        QSpectrumAnalyzerMainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(QSpectrumAnalyzerMainWindow)
        self.statusbar.setObjectName(u"statusbar")
        QSpectrumAnalyzerMainWindow.setStatusBar(self.statusbar)
        self.controlsDockWidget = QDockWidget(QSpectrumAnalyzerMainWindow)
        self.controlsDockWidget.setObjectName(u"controlsDockWidget")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.controlsDockWidget.sizePolicy().hasHeightForWidth())
        self.controlsDockWidget.setSizePolicy(sizePolicy2)
        self.controlsDockWidget.setMinimumSize(QSize(190, 130))
        self.controlsDockWidget.setFeatures(QDockWidget.DockWidgetFloatable|QDockWidget.DockWidgetMovable)
        self.controlsDockWidgetContents = QWidget()
        self.controlsDockWidgetContents.setObjectName(u"controlsDockWidgetContents")
        self.gridLayout_2 = QGridLayout(self.controlsDockWidgetContents)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.presetGroupBox = QGroupBox(self.controlsDockWidgetContents)
        self.presetGroupBox.setObjectName(u"presetGroupBox")
        self.presetGridLayout = QGridLayout(self.presetGroupBox)
        self.presetGridLayout.setObjectName(u"presetGridLayout")
        self.presetComboBox = QComboBox(self.presetGroupBox)
        self.presetComboBox.setObjectName(u"presetComboBox")

        self.presetGridLayout.addWidget(self.presetComboBox, 0, 0, 1, 1)


        self.gridLayout_2.addWidget(self.presetGroupBox, 0, 0, 1, 2)

        self.startButton = QPushButton(self.controlsDockWidgetContents)
        self.startButton.setObjectName(u"startButton")

        self.gridLayout_2.addWidget(self.startButton, 1, 0, 1, 1)

        self.stopButton = QPushButton(self.controlsDockWidgetContents)
        self.stopButton.setObjectName(u"stopButton")

        self.gridLayout_2.addWidget(self.stopButton, 1, 1, 1, 1)

        self.singleShotButton = QPushButton(self.controlsDockWidgetContents)
        self.singleShotButton.setObjectName(u"singleShotButton")

        self.gridLayout_2.addWidget(self.singleShotButton, 2, 0, 1, 2)

        self.historyGroupBox = QGroupBox(self.controlsDockWidgetContents)
        self.historyGroupBox.setObjectName(u"historyGroupBox")
        self.historyGridLayout = QGridLayout(self.historyGroupBox)
        self.historyGridLayout.setObjectName(u"historyGridLayout")
        self.browseHistoryCheckBox = QCheckBox(self.historyGroupBox)
        self.browseHistoryCheckBox.setObjectName(u"browseHistoryCheckBox")

        self.historyGridLayout.addWidget(self.browseHistoryCheckBox, 0, 0, 1, 3)

        self.historyBackButton = QPushButton(self.historyGroupBox)
        self.historyBackButton.setObjectName(u"historyBackButton")

        self.historyGridLayout.addWidget(self.historyBackButton, 1, 0, 1, 1)

        self.historyStepSpinBox = QSpinBox(self.historyGroupBox)
        self.historyStepSpinBox.setObjectName(u"historyStepSpinBox")
        self.historyStepSpinBox.setMinimum(1)
        self.historyStepSpinBox.setMaximum(1000000)
        self.historyStepSpinBox.setValue(1)

        self.historyGridLayout.addWidget(self.historyStepSpinBox, 1, 1, 1, 1)

        self.historyForwardButton = QPushButton(self.historyGroupBox)
        self.historyForwardButton.setObjectName(u"historyForwardButton")

        self.historyGridLayout.addWidget(self.historyForwardButton, 1, 2, 1, 1)

        self.historySlider = QSlider(self.historyGroupBox)
        self.historySlider.setObjectName(u"historySlider")
        self.historySlider.setOrientation(Qt.Horizontal)

        self.historyGridLayout.addWidget(self.historySlider, 2, 0, 1, 3)

        self.historyPositionLabel = QLabel(self.historyGroupBox)
        self.historyPositionLabel.setObjectName(u"historyPositionLabel")
        self.historyPositionLabel.setAlignment(Qt.AlignCenter)
        self.historyPositionLabel.setWordWrap(True)

        self.historyGridLayout.addWidget(self.historyPositionLabel, 3, 0, 1, 3)


        self.gridLayout_2.addWidget(self.historyGroupBox, 3, 0, 1, 2)

        self.plotsGroupBox = QGroupBox(self.controlsDockWidgetContents)
        self.plotsGroupBox.setObjectName(u"plotsGroupBox")
        self.plotsGridLayout = QGridLayout(self.plotsGroupBox)
        self.plotsGridLayout.setObjectName(u"plotsGridLayout")
        self.waterfallCheckBox = QCheckBox(self.plotsGroupBox)
        self.waterfallCheckBox.setObjectName(u"waterfallCheckBox")
        self.waterfallCheckBox.setChecked(True)

        self.plotsGridLayout.addWidget(self.waterfallCheckBox, 0, 0, 1, 2)

        self.scopeCheckBox = QCheckBox(self.plotsGroupBox)
        self.scopeCheckBox.setObjectName(u"scopeCheckBox")

        self.plotsGridLayout.addWidget(self.scopeCheckBox, 1, 0, 1, 2)


        self.gridLayout_2.addWidget(self.plotsGroupBox, 4, 0, 1, 2)

        self.scopeGroupBox = QGroupBox(self.controlsDockWidgetContents)
        self.scopeGroupBox.setObjectName(u"scopeGroupBox")
        self.scopeGroupBox.setEnabled(False)
        self.scopeGridLayout = QGridLayout(self.scopeGroupBox)
        self.scopeGridLayout.setObjectName(u"scopeGridLayout")
        self.scopeSpanLabel = QLabel(self.scopeGroupBox)
        self.scopeSpanLabel.setObjectName(u"scopeSpanLabel")

        self.scopeGridLayout.addWidget(self.scopeSpanLabel, 0, 0, 1, 1)

        self.scopeSpanSpinBox = QDoubleSpinBox(self.scopeGroupBox)
        self.scopeSpanSpinBox.setObjectName(u"scopeSpanSpinBox")
        self.scopeSpanSpinBox.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.scopeSpanSpinBox.setDecimals(3)
        self.scopeSpanSpinBox.setMinimum(0.000000000000000)
        self.scopeSpanSpinBox.setMaximum(3600000.000000000000000)

        self.scopeGridLayout.addWidget(self.scopeSpanSpinBox, 0, 1, 1, 1)

        self.scopeBandCheckBox = QCheckBox(self.scopeGroupBox)
        self.scopeBandCheckBox.setObjectName(u"scopeBandCheckBox")

        self.scopeGridLayout.addWidget(self.scopeBandCheckBox, 1, 0, 1, 2)

        self.scopeCentreLabel = QLabel(self.scopeGroupBox)
        self.scopeCentreLabel.setObjectName(u"scopeCentreLabel")

        self.scopeGridLayout.addWidget(self.scopeCentreLabel, 2, 0, 1, 1)

        self.scopeCentreSpinBox = QDoubleSpinBox(self.scopeGroupBox)
        self.scopeCentreSpinBox.setObjectName(u"scopeCentreSpinBox")
        self.scopeCentreSpinBox.setEnabled(False)
        self.scopeCentreSpinBox.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.scopeCentreSpinBox.setDecimals(4)
        self.scopeCentreSpinBox.setMaximum(7250.000000000000000)

        self.scopeGridLayout.addWidget(self.scopeCentreSpinBox, 2, 1, 1, 1)

        self.scopeWidthLabel = QLabel(self.scopeGroupBox)
        self.scopeWidthLabel.setObjectName(u"scopeWidthLabel")

        self.scopeGridLayout.addWidget(self.scopeWidthLabel, 3, 0, 1, 1)

        self.scopeWidthSpinBox = QDoubleSpinBox(self.scopeGroupBox)
        self.scopeWidthSpinBox.setObjectName(u"scopeWidthSpinBox")
        self.scopeWidthSpinBox.setEnabled(False)
        self.scopeWidthSpinBox.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.scopeWidthSpinBox.setDecimals(1)
        self.scopeWidthSpinBox.setMinimum(0.100000000000000)
        self.scopeWidthSpinBox.setMaximum(100000.000000000000000)
        self.scopeWidthSpinBox.setValue(400.000000000000000)

        self.scopeGridLayout.addWidget(self.scopeWidthSpinBox, 3, 1, 1, 1)

        self.scopeTriggerCheckBox = QCheckBox(self.scopeGroupBox)
        self.scopeTriggerCheckBox.setObjectName(u"scopeTriggerCheckBox")

        self.scopeGridLayout.addWidget(self.scopeTriggerCheckBox, 5, 0, 1, 2)

        self.scopeTriggerLabel = QLabel(self.scopeGroupBox)
        self.scopeTriggerLabel.setObjectName(u"scopeTriggerLabel")

        self.scopeGridLayout.addWidget(self.scopeTriggerLabel, 6, 0, 1, 1)

        self.scopeSingleCheckBox = QCheckBox(self.scopeGroupBox)
        self.scopeSingleCheckBox.setObjectName(u"scopeSingleCheckBox")
        self.scopeSingleCheckBox.setEnabled(False)

        self.scopeGridLayout.addWidget(self.scopeSingleCheckBox, 7, 0, 1, 2)

        self.scopeSaveButton = QPushButton(self.scopeGroupBox)
        self.scopeSaveButton.setObjectName(u"scopeSaveButton")

        self.scopeGridLayout.addWidget(self.scopeSaveButton, 9, 1, 1, 1)

        self.scopeArmButton = QPushButton(self.scopeGroupBox)
        self.scopeArmButton.setObjectName(u"scopeArmButton")
        self.scopeArmButton.setEnabled(False)

        self.scopeGridLayout.addWidget(self.scopeArmButton, 8, 1, 1, 1)

        self.scopeTriggerSpinBox = QDoubleSpinBox(self.scopeGroupBox)
        self.scopeTriggerSpinBox.setObjectName(u"scopeTriggerSpinBox")
        self.scopeTriggerSpinBox.setEnabled(False)
        self.scopeTriggerSpinBox.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.scopeTriggerSpinBox.setDecimals(1)
        self.scopeTriggerSpinBox.setMinimum(-200.000000000000000)
        self.scopeTriggerSpinBox.setMaximum(50.000000000000000)
        self.scopeTriggerSpinBox.setValue(-200.000000000000000)

        self.scopeGridLayout.addWidget(self.scopeTriggerSpinBox, 6, 1, 1, 1)

        self.scopeFastCheckBox = QCheckBox(self.scopeGroupBox)
        self.scopeFastCheckBox.setObjectName(u"scopeFastCheckBox")

        self.scopeGridLayout.addWidget(self.scopeFastCheckBox, 4, 0, 1, 2)


        self.gridLayout_2.addWidget(self.scopeGroupBox, 5, 0, 1, 2)

        self.verticalSpacer = QSpacerItem(20, 561, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout_2.addItem(self.verticalSpacer, 6, 0, 1, 1)

        self.controlsDockWidget.setWidget(self.controlsDockWidgetContents)
        QSpectrumAnalyzerMainWindow.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.controlsDockWidget)
        self.frequencyDockWidget = QDockWidget(QSpectrumAnalyzerMainWindow)
        self.frequencyDockWidget.setObjectName(u"frequencyDockWidget")
        sizePolicy2.setHeightForWidth(self.frequencyDockWidget.sizePolicy().hasHeightForWidth())
        self.frequencyDockWidget.setSizePolicy(sizePolicy2)
        self.frequencyDockWidget.setMinimumSize(QSize(208, 166))
        self.frequencyDockWidget.setFeatures(QDockWidget.DockWidgetFloatable|QDockWidget.DockWidgetMovable)
        self.frequencyDockWidgetContents = QWidget()
        self.frequencyDockWidgetContents.setObjectName(u"frequencyDockWidgetContents")
        self.formLayout = QFormLayout(self.frequencyDockWidgetContents)
        self.formLayout.setObjectName(u"formLayout")
        self.formLayout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        self.label_2 = QLabel(self.frequencyDockWidgetContents)
        self.label_2.setObjectName(u"label_2")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.label_2)

        self.startFreqSpinBox = QDoubleSpinBox(self.frequencyDockWidgetContents)
        self.startFreqSpinBox.setObjectName(u"startFreqSpinBox")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.startFreqSpinBox.sizePolicy().hasHeightForWidth())
        self.startFreqSpinBox.setSizePolicy(sizePolicy3)
        self.startFreqSpinBox.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.startFreqSpinBox.setProperty(u"showGroupSeparator", True)
        self.startFreqSpinBox.setDecimals(3)
        self.startFreqSpinBox.setMinimum(0.000000000000000)
        self.startFreqSpinBox.setMaximum(2200.000000000000000)
        self.startFreqSpinBox.setValue(87.000000000000000)

        self.formLayout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.startFreqSpinBox)

        self.label_3 = QLabel(self.frequencyDockWidgetContents)
        self.label_3.setObjectName(u"label_3")

        self.formLayout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.label_3)

        self.stopFreqSpinBox = QDoubleSpinBox(self.frequencyDockWidgetContents)
        self.stopFreqSpinBox.setObjectName(u"stopFreqSpinBox")
        sizePolicy3.setHeightForWidth(self.stopFreqSpinBox.sizePolicy().hasHeightForWidth())
        self.stopFreqSpinBox.setSizePolicy(sizePolicy3)
        self.stopFreqSpinBox.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.stopFreqSpinBox.setProperty(u"showGroupSeparator", True)
        self.stopFreqSpinBox.setDecimals(3)
        self.stopFreqSpinBox.setMinimum(0.000000000000000)
        self.stopFreqSpinBox.setMaximum(2200.000000000000000)
        self.stopFreqSpinBox.setValue(108.000000000000000)

        self.formLayout.setWidget(1, QFormLayout.ItemRole.FieldRole, self.stopFreqSpinBox)

        self.label = QLabel(self.frequencyDockWidgetContents)
        self.label.setObjectName(u"label")

        self.formLayout.setWidget(2, QFormLayout.ItemRole.LabelRole, self.label)

        self.surveyDwellLabel = QLabel(self.frequencyDockWidgetContents)
        self.surveyDwellLabel.setObjectName(u"surveyDwellLabel")

        self.formLayout.setWidget(3, QFormLayout.ItemRole.LabelRole, self.surveyDwellLabel)

        self.surveyDwellSpinBox = QSpinBox(self.frequencyDockWidgetContents)
        self.surveyDwellSpinBox.setObjectName(u"surveyDwellSpinBox")
        self.surveyDwellSpinBox.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.surveyDwellSpinBox.setMinimum(1)
        self.surveyDwellSpinBox.setMaximum(3600)
        self.surveyDwellSpinBox.setValue(60)

        self.formLayout.setWidget(3, QFormLayout.ItemRole.FieldRole, self.surveyDwellSpinBox)

        self.surveyButton = QPushButton(self.frequencyDockWidgetContents)
        self.surveyButton.setObjectName(u"surveyButton")

        self.formLayout.setWidget(4, QFormLayout.ItemRole.SpanningRole, self.surveyButton)

        self.surveyProgressLabel = QLabel(self.frequencyDockWidgetContents)
        self.surveyProgressLabel.setObjectName(u"surveyProgressLabel")
        self.surveyProgressLabel.setWordWrap(True)

        self.formLayout.setWidget(5, QFormLayout.ItemRole.SpanningRole, self.surveyProgressLabel)

        self.binSizeSpinBox = QDoubleSpinBox(self.frequencyDockWidgetContents)
        self.binSizeSpinBox.setObjectName(u"binSizeSpinBox")
        sizePolicy3.setHeightForWidth(self.binSizeSpinBox.sizePolicy().hasHeightForWidth())
        self.binSizeSpinBox.setSizePolicy(sizePolicy3)
        self.binSizeSpinBox.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.binSizeSpinBox.setProperty(u"showGroupSeparator", True)
        self.binSizeSpinBox.setDecimals(3)
        self.binSizeSpinBox.setMinimum(0.000000000000000)
        self.binSizeSpinBox.setMaximum(10000.000000000000000)
        self.binSizeSpinBox.setValue(10.000000000000000)

        self.formLayout.setWidget(2, QFormLayout.ItemRole.FieldRole, self.binSizeSpinBox)

        self.verticalSpacer_3 = QSpacerItem(20, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.formLayout.setItem(6, QFormLayout.ItemRole.SpanningRole, self.verticalSpacer_3)

        self.frequencyDockWidget.setWidget(self.frequencyDockWidgetContents)
        QSpectrumAnalyzerMainWindow.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.frequencyDockWidget)
        self.settingsDockWidget = QDockWidget(QSpectrumAnalyzerMainWindow)
        self.settingsDockWidget.setObjectName(u"settingsDockWidget")
        sizePolicy4 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.settingsDockWidget.sizePolicy().hasHeightForWidth())
        self.settingsDockWidget.setSizePolicy(sizePolicy4)
        self.settingsDockWidget.setFeatures(QDockWidget.DockWidgetFloatable|QDockWidget.DockWidgetMovable)
        self.settingsDockWidgetContents = QWidget()
        self.settingsDockWidgetContents.setObjectName(u"settingsDockWidgetContents")
        self.gridLayout = QGridLayout(self.settingsDockWidgetContents)
        self.gridLayout.setObjectName(u"gridLayout")
        self.label_4 = QLabel(self.settingsDockWidgetContents)
        self.label_4.setObjectName(u"label_4")

        self.gridLayout.addWidget(self.label_4, 0, 0, 1, 1)

        self.label_6 = QLabel(self.settingsDockWidgetContents)
        self.label_6.setObjectName(u"label_6")

        self.gridLayout.addWidget(self.label_6, 0, 1, 1, 1)

        self.intervalSpinBox = QDoubleSpinBox(self.settingsDockWidgetContents)
        self.intervalSpinBox.setObjectName(u"intervalSpinBox")
        self.intervalSpinBox.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.intervalSpinBox.setMaximum(999.000000000000000)
        self.intervalSpinBox.setValue(1.000000000000000)

        self.gridLayout.addWidget(self.intervalSpinBox, 1, 0, 1, 1)

        self.label_5 = QLabel(self.settingsDockWidgetContents)
        self.label_5.setObjectName(u"label_5")

        self.gridLayout.addWidget(self.label_5, 2, 0, 1, 1)

        self.label_7 = QLabel(self.settingsDockWidgetContents)
        self.label_7.setObjectName(u"label_7")

        self.gridLayout.addWidget(self.label_7, 2, 1, 1, 1)

        self.ppmSpinBox = QSpinBox(self.settingsDockWidgetContents)
        self.ppmSpinBox.setObjectName(u"ppmSpinBox")
        self.ppmSpinBox.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.ppmSpinBox.setMinimum(-999)
        self.ppmSpinBox.setMaximum(999)

        self.gridLayout.addWidget(self.ppmSpinBox, 3, 0, 1, 1)

        self.ampCheckBox = QCheckBox(self.settingsDockWidgetContents)
        self.ampCheckBox.setObjectName(u"ampCheckBox")

        self.gridLayout.addWidget(self.ampCheckBox, 4, 0, 1, 3)

        self.mainCurveCheckBox = QCheckBox(self.settingsDockWidgetContents)
        self.mainCurveCheckBox.setObjectName(u"mainCurveCheckBox")
        self.mainCurveCheckBox.setChecked(True)

        self.gridLayout.addWidget(self.mainCurveCheckBox, 5, 0, 1, 1)

        self.colorsButton = QPushButton(self.settingsDockWidgetContents)
        self.colorsButton.setObjectName(u"colorsButton")

        self.gridLayout.addWidget(self.colorsButton, 5, 1, 1, 2)

        self.peakHoldMaxCheckBox = QCheckBox(self.settingsDockWidgetContents)
        self.peakHoldMaxCheckBox.setObjectName(u"peakHoldMaxCheckBox")

        self.gridLayout.addWidget(self.peakHoldMaxCheckBox, 6, 0, 1, 1)

        self.peakHoldMinCheckBox = QCheckBox(self.settingsDockWidgetContents)
        self.peakHoldMinCheckBox.setObjectName(u"peakHoldMinCheckBox")

        self.gridLayout.addWidget(self.peakHoldMinCheckBox, 6, 1, 1, 2)

        self.averageCheckBox = QCheckBox(self.settingsDockWidgetContents)
        self.averageCheckBox.setObjectName(u"averageCheckBox")

        self.gridLayout.addWidget(self.averageCheckBox, 7, 0, 1, 1)

        self.smoothCheckBox = QCheckBox(self.settingsDockWidgetContents)
        self.smoothCheckBox.setObjectName(u"smoothCheckBox")

        self.gridLayout.addWidget(self.smoothCheckBox, 8, 0, 1, 1)

        self.smoothButton = QToolButton(self.settingsDockWidgetContents)
        self.smoothButton.setObjectName(u"smoothButton")
        self.smoothButton.setAutoRaise(False)

        self.gridLayout.addWidget(self.smoothButton, 8, 2, 1, 1)

        self.persistenceCheckBox = QCheckBox(self.settingsDockWidgetContents)
        self.persistenceCheckBox.setObjectName(u"persistenceCheckBox")

        self.gridLayout.addWidget(self.persistenceCheckBox, 9, 0, 1, 1)

        self.persistenceButton = QToolButton(self.settingsDockWidgetContents)
        self.persistenceButton.setObjectName(u"persistenceButton")
        self.persistenceButton.setAutoRaise(False)

        self.gridLayout.addWidget(self.persistenceButton, 9, 2, 1, 1)

        self.verticalSpacer_2 = QSpacerItem(20, 1, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout.addItem(self.verticalSpacer_2, 12, 0, 1, 1)

        self.cropSpinBox = QSpinBox(self.settingsDockWidgetContents)
        self.cropSpinBox.setObjectName(u"cropSpinBox")
        self.cropSpinBox.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridLayout.addWidget(self.cropSpinBox, 3, 1, 1, 2)

        self.gainSpinBox = QDoubleSpinBox(self.settingsDockWidgetContents)
        self.gainSpinBox.setObjectName(u"gainSpinBox")
        self.gainSpinBox.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.gainSpinBox.setDecimals(1)
        self.gainSpinBox.setMinimum(-1.000000000000000)
        self.gainSpinBox.setMaximum(999.000000000000000)
        self.gainSpinBox.setSingleStep(1.000000000000000)
        self.gainSpinBox.setValue(-1.000000000000000)

        self.gridLayout.addWidget(self.gainSpinBox, 1, 1, 1, 2)

        self.baselineCheckBox = QCheckBox(self.settingsDockWidgetContents)
        self.baselineCheckBox.setObjectName(u"baselineCheckBox")

        self.gridLayout.addWidget(self.baselineCheckBox, 10, 0, 1, 1)

        self.baselineButton = QToolButton(self.settingsDockWidgetContents)
        self.baselineButton.setObjectName(u"baselineButton")
        self.baselineButton.setAutoRaise(False)

        self.gridLayout.addWidget(self.baselineButton, 10, 2, 1, 1)

        self.subtractBaselineCheckBox = QCheckBox(self.settingsDockWidgetContents)
        self.subtractBaselineCheckBox.setObjectName(u"subtractBaselineCheckBox")

        self.gridLayout.addWidget(self.subtractBaselineCheckBox, 11, 0, 1, 1)

        self.settingsDockWidget.setWidget(self.settingsDockWidgetContents)
        QSpectrumAnalyzerMainWindow.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.settingsDockWidget)
        self.levelsDockWidget = QDockWidget(QSpectrumAnalyzerMainWindow)
        self.levelsDockWidget.setObjectName(u"levelsDockWidget")
        sizePolicy4.setHeightForWidth(self.levelsDockWidget.sizePolicy().hasHeightForWidth())
        self.levelsDockWidget.setSizePolicy(sizePolicy4)
        self.levelsDockWidget.setFeatures(QDockWidget.DockWidgetFloatable|QDockWidget.DockWidgetMovable)
        self.levelsDockWidgetContents = QWidget()
        self.levelsDockWidgetContents.setObjectName(u"levelsDockWidgetContents")
        self.verticalLayout_6 = QVBoxLayout(self.levelsDockWidgetContents)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.histogramPlotLayout = GraphicsLayoutWidget(self.levelsDockWidgetContents)
        self.histogramPlotLayout.setObjectName(u"histogramPlotLayout")
        sizePolicy5 = QSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Expanding)
        sizePolicy5.setHorizontalStretch(0)
        sizePolicy5.setVerticalStretch(0)
        sizePolicy5.setHeightForWidth(self.histogramPlotLayout.sizePolicy().hasHeightForWidth())
        self.histogramPlotLayout.setSizePolicy(sizePolicy5)

        self.verticalLayout_6.addWidget(self.histogramPlotLayout)

        self.levelsDockWidget.setWidget(self.levelsDockWidgetContents)
        QSpectrumAnalyzerMainWindow.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.levelsDockWidget)
#if QT_CONFIG(shortcut)
        self.scopeSpanLabel.setBuddy(self.scopeSpanSpinBox)
        self.scopeCentreLabel.setBuddy(self.scopeCentreSpinBox)
        self.scopeWidthLabel.setBuddy(self.scopeWidthSpinBox)
        self.scopeTriggerLabel.setBuddy(self.scopeTriggerSpinBox)
        self.label_2.setBuddy(self.startFreqSpinBox)
        self.label_3.setBuddy(self.stopFreqSpinBox)
        self.label.setBuddy(self.binSizeSpinBox)
        self.surveyDwellLabel.setBuddy(self.surveyDwellSpinBox)
        self.label_4.setBuddy(self.intervalSpinBox)
        self.label_6.setBuddy(self.gainSpinBox)
        self.label_5.setBuddy(self.ppmSpinBox)
        self.label_7.setBuddy(self.cropSpinBox)
#endif // QT_CONFIG(shortcut)
        QWidget.setTabOrder(self.presetComboBox, self.startButton)
        QWidget.setTabOrder(self.startButton, self.stopButton)
        QWidget.setTabOrder(self.stopButton, self.singleShotButton)
        QWidget.setTabOrder(self.singleShotButton, self.browseHistoryCheckBox)
        QWidget.setTabOrder(self.browseHistoryCheckBox, self.historyBackButton)
        QWidget.setTabOrder(self.historyBackButton, self.historyStepSpinBox)
        QWidget.setTabOrder(self.historyStepSpinBox, self.historyForwardButton)
        QWidget.setTabOrder(self.historyForwardButton, self.historySlider)
        QWidget.setTabOrder(self.historySlider, self.waterfallCheckBox)
        QWidget.setTabOrder(self.waterfallCheckBox, self.scopeCheckBox)
        QWidget.setTabOrder(self.scopeCheckBox, self.scopeSpanSpinBox)
        QWidget.setTabOrder(self.scopeSpanSpinBox, self.scopeBandCheckBox)
        QWidget.setTabOrder(self.scopeBandCheckBox, self.scopeCentreSpinBox)
        QWidget.setTabOrder(self.scopeCentreSpinBox, self.scopeWidthSpinBox)
        QWidget.setTabOrder(self.scopeWidthSpinBox, self.scopeFastCheckBox)
        QWidget.setTabOrder(self.scopeFastCheckBox, self.scopeTriggerCheckBox)
        QWidget.setTabOrder(self.scopeTriggerCheckBox, self.scopeTriggerSpinBox)
        QWidget.setTabOrder(self.scopeTriggerSpinBox, self.scopeSingleCheckBox)
        QWidget.setTabOrder(self.scopeSingleCheckBox, self.scopeArmButton)
        QWidget.setTabOrder(self.scopeArmButton, self.scopeSaveButton)
        QWidget.setTabOrder(self.scopeSaveButton, self.startFreqSpinBox)
        QWidget.setTabOrder(self.startFreqSpinBox, self.stopFreqSpinBox)
        QWidget.setTabOrder(self.stopFreqSpinBox, self.binSizeSpinBox)
        QWidget.setTabOrder(self.binSizeSpinBox, self.surveyDwellSpinBox)
        QWidget.setTabOrder(self.surveyDwellSpinBox, self.surveyButton)
        QWidget.setTabOrder(self.surveyButton, self.intervalSpinBox)
        QWidget.setTabOrder(self.intervalSpinBox, self.gainSpinBox)
        QWidget.setTabOrder(self.gainSpinBox, self.ppmSpinBox)
        QWidget.setTabOrder(self.ppmSpinBox, self.cropSpinBox)
        QWidget.setTabOrder(self.cropSpinBox, self.ampCheckBox)
        QWidget.setTabOrder(self.ampCheckBox, self.mainCurveCheckBox)
        QWidget.setTabOrder(self.mainCurveCheckBox, self.colorsButton)
        QWidget.setTabOrder(self.colorsButton, self.peakHoldMaxCheckBox)
        QWidget.setTabOrder(self.peakHoldMaxCheckBox, self.peakHoldMinCheckBox)
        QWidget.setTabOrder(self.peakHoldMinCheckBox, self.averageCheckBox)
        QWidget.setTabOrder(self.averageCheckBox, self.smoothCheckBox)
        QWidget.setTabOrder(self.smoothCheckBox, self.smoothButton)
        QWidget.setTabOrder(self.smoothButton, self.persistenceCheckBox)
        QWidget.setTabOrder(self.persistenceCheckBox, self.persistenceButton)
        QWidget.setTabOrder(self.persistenceButton, self.baselineCheckBox)
        QWidget.setTabOrder(self.baselineCheckBox, self.baselineButton)
        QWidget.setTabOrder(self.baselineButton, self.subtractBaselineCheckBox)
        QWidget.setTabOrder(self.subtractBaselineCheckBox, self.histogramPlotLayout)
        QWidget.setTabOrder(self.histogramPlotLayout, self.mainPlotLayout)
        QWidget.setTabOrder(self.mainPlotLayout, self.waterfallPlotLayout)
        QWidget.setTabOrder(self.waterfallPlotLayout, self.scopePlotLayout)

        self.menubar.addAction(self.menu_File.menuAction())
        self.menubar.addAction(self.menu_Help.menuAction())
        self.menu_File.addAction(self.action_Settings)
        self.menu_File.addSeparator()
        self.menu_File.addAction(self.action_Quit)
        self.menu_Help.addAction(self.action_About)

        self.retranslateUi(QSpectrumAnalyzerMainWindow)

        QMetaObject.connectSlotsByName(QSpectrumAnalyzerMainWindow)
    # setupUi

    def retranslateUi(self, QSpectrumAnalyzerMainWindow):
        QSpectrumAnalyzerMainWindow.setWindowTitle(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u"QSpectrumAnalyzer", None))
        self.action_Settings.setText(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u"&Settings...", None))
        self.action_Quit.setText(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u"&Quit", None))
#if QT_CONFIG(shortcut)
        self.action_Quit.setShortcut(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u"Ctrl+Q", None))
#endif // QT_CONFIG(shortcut)
        self.action_About.setText(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u"&About", None))
        self.menu_File.setTitle(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u"&File", None))
        self.menu_Help.setTitle(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u"&Help", None))
        self.controlsDockWidget.setWindowTitle(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u"Controls", None))
        self.presetGroupBox.setTitle(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u"Looking for", None))
#if QT_CONFIG(tooltip)
        self.presetComboBox.setToolTip(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u"Set every control at once for a particular job. These settings interact: the bin size decides how short a pulse survives being measured, the detector decides whether it survives at all, and the recording depth decides whether a whole scan cycle fits on screen. Getting one of them wrong quietly wastes an evening, so pick the job instead of the settings.", None))
#endif // QT_CONFIG(tooltip)
        self.startButton.setText(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u"&Start", None))
        self.stopButton.setText(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u"S&top", None))
        self.singleShotButton.setText(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u"Si&ngle shot", None))
        self.historyGroupBox.setTitle(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u"History", None))
#if QT_CONFIG(tooltip)
        self.browseHistoryCheckBox.setToolTip(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u"Freeze the plots and step back through the recorded sweeps. Acquisition keeps running and keeps recording.", None))
#endif // QT_CONFIG(tooltip)
        self.browseHistoryCheckBox.setText(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u"&Browse recorded sweeps", None))
#if QT_CONFIG(tooltip)
        self.historyBackButton.setToolTip(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u"Step back through the recorded sweeps", None))
#endif // QT_CONFIG(tooltip)
        self.historyBackButton.setText(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u"<", None))
#if QT_CONFIG(tooltip)
        self.historyStepSpinBox.setToolTip(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u"How many sweeps each step moves", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.historyForwardButton.setToolTip(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u"Step forward through the recorded sweeps", None))
#endif // QT_CONFIG(tooltip)
        self.historyForwardButton.setText(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u">", None))
        self.historyPositionLabel.setText(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u"Live", None))
        self.plotsGroupBox.setTitle(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u"Plots", None))
#if QT_CONFIG(tooltip)
        self.waterfallCheckBox.setToolTip(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u"Show the waterfall under the spectrum: the recording as an image, frequency across and time down.", None))
#endif // QT_CONFIG(tooltip)
        self.waterfallCheckBox.setText(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u"&Waterfall", None))
#if QT_CONFIG(tooltip)
        self.scopeCheckBox.setToolTip(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u"Show power over time under the waterfall: the recording along its other axis, so the shape a signal has in time is on screen beside the sweep being looked at. Stepping through the recorded sweeps moves a cursor along it, and dragging that cursor steps to a moment. A signal that comes back every so often shows as evenly spaced spikes.", None))
#endif // QT_CONFIG(tooltip)
        self.scopeCheckBox.setText(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u"Power over &time (scope)", None))
        self.scopeGroupBox.setTitle(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u"Oscilloscope", None))
        self.scopeSpanLabel.setText(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u"S&pan:", None))
#if QT_CONFIG(tooltip)
        self.scopeSpanSpinBox.setToolTip(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u"How much time is on screen. The window keeps this width and rolls forward with the newest data, the way a timebase does. Zero fits the whole recording instead. Zooming the plot with the mouse sets this too.", None))
#endif // QT_CONFIG(tooltip)
        self.scopeSpanSpinBox.setSuffix(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u" ms", None))
        self.scopeSpanSpinBox.setSpecialValueText(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u"all", None))
#if QT_CONFIG(tooltip)
        self.scopeBandCheckBox.setToolTip(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u"Reduce the scope to one stretch of the spectrum instead of all of it, which is a zero span view of that stretch. Set it below, or drag the shaded band on the spectrum plot.", None))
#endif // QT_CONFIG(tooltip)
        self.scopeBandCheckBox.setText(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u"One frequency &band only", None))
        self.scopeCentreLabel.setText(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u"C&entre:", None))
#if QT_CONFIG(tooltip)
        self.scopeCentreSpinBox.setToolTip(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u"The frequency the scope watches.", None))
#endif // QT_CONFIG(tooltip)
        self.scopeCentreSpinBox.setSuffix(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u" MHz", None))
        self.scopeWidthLabel.setText(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u"Wi&dth:", None))
#if QT_CONFIG(tooltip)
        self.scopeWidthSpinBox.setToolTip(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u"How wide a band around the centre to watch. This is the resolution bandwidth of the zero span view; it is snapped to whole bins, so nothing narrower than one bin is possible.", None))
#endif // QT_CONFIG(tooltip)
        self.scopeWidthSpinBox.setSuffix(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u" kHz", None))
#if QT_CONFIG(tooltip)
        self.scopeTriggerCheckBox.setToolTip(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u"Start each sweep where the signal rises past a level, the way a scope does, instead of letting the trace slide through the window. A burst that comes back then lands in the same place every time and stands still, so its shape can be read. When nothing crosses the level the last sweep is held rather than moved.", None))
#endif // QT_CONFIG(tooltip)
        self.scopeTriggerCheckBox.setText(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u"Tri&gger on a rising edge", None))
        self.scopeTriggerLabel.setText(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u"Le&vel:", None))
#if QT_CONFIG(tooltip)
        self.scopeSingleCheckBox.setToolTip(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u"Catch one sweep and hold it, instead of triggering over and over. A burst that happens once, or once a minute, cannot be read off a display that has moved on by the time you look at it. The sweep the burst arrived in stays on screen until you press Arm for the next one. This is the scope's trigger mode; it has nothing to do with the Single shot button above, which takes one measurement and stops.", None))
#endif // QT_CONFIG(tooltip)
        self.scopeSingleCheckBox.setText(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u"Single s&weep", None))
#if QT_CONFIG(tooltip)
        self.scopeSaveButton.setToolTip(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u"Write the sweep on screen out as CSV, at full resolution, with the settings it was taken under and the time t=0 happened. A burst worth catching is worth keeping.", None))
#endif // QT_CONFIG(tooltip)
        self.scopeSaveButton.setText(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u"Sa&ve sweep...", None))
#if QT_CONFIG(tooltip)
        self.scopeArmButton.setToolTip(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u"Let go of the sweep on screen and wait for the next burst above the level.", None))
#endif // QT_CONFIG(tooltip)
        self.scopeArmButton.setText(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u"Ar&m", None))
#if QT_CONFIG(tooltip)
        self.scopeTriggerSpinBox.setToolTip(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u"The power a rising edge has to cross to start a sweep, marked on the plot as a dashed line. At the lowest setting the level is taken from the trace itself, half way between the noise it sits at and the loudest thing in it.", None))
#endif // QT_CONFIG(tooltip)
        self.scopeTriggerSpinBox.setSuffix(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u" dB", None))
        self.scopeTriggerSpinBox.setSpecialValueText(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u"auto", None))
#if QT_CONFIG(tooltip)
        self.scopeFastCheckBox.setToolTip(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u"Measure the band straight off the radio's frames instead of reading it back out of the delivered spectra, and draw it as a second, finer trace. hackrf_stream reaches 25.6 us per reading at 20 MSPS with 40 kHz bins, against 10 ms for a delivered sweep, so a burst far too short to survive the averaging is still measured at full height. The step is set in Settings. Readings are noisier than the spectra behind them, which is the price of the resolution. Only backends that can do it offer it.", None))
#endif // QT_CONFIG(tooltip)
        self.scopeFastCheckBox.setText(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u"Hi&gh-rate tap", None))
        self.frequencyDockWidget.setWindowTitle(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u"Frequency", None))
        self.label_2.setText(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u"Start:", None))
        self.startFreqSpinBox.setSuffix(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u" MHz", None))
        self.label_3.setText(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u"Stop:", None))
        self.stopFreqSpinBox.setSuffix(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u" MHz", None))
        self.label.setText(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u"&Bin size:", None))
        self.surveyDwellLabel.setText(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u"D&well:", None))
#if QT_CONFIG(tooltip)
        self.surveyDwellSpinBox.setToolTip(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u"How long a survey listens to each slice of the range before moving on. Long enough for whatever you are looking for to come round: a radar that turns every five seconds needs tens of seconds to be sure of catching several of its passes.", None))
#endif // QT_CONFIG(tooltip)
        self.surveyDwellSpinBox.setSuffix(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u" s", None))
#if QT_CONFIG(tooltip)
        self.surveyButton.setToolTip(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u"Walk the whole Start to Stop range one tune at a time, camping on each slice for the dwell and writing down what was ever heard in it and how often. Meant for a signal that is only there occasionally: sweeping past such a thing misses it, staying put does not. Press again to stop.", None))
#endif // QT_CONFIG(tooltip)
        self.surveyButton.setText(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u"Sur&vey the range...", None))
        self.surveyProgressLabel.setText("")
        self.binSizeSpinBox.setSuffix(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u" kHz", None))
        self.settingsDockWidget.setWindowTitle(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u"Settings", None))
        self.label_4.setText(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u"&Interval [s]:", None))
        self.label_6.setText(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u"&Gain [dB]:", None))
        self.label_5.setText(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u"Corr. [ppm]:", None))
        self.label_7.setText(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u"Crop [%]:", None))
#if QT_CONFIG(tooltip)
        self.ampCheckBox.setToolTip(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u"Switch on the radio's own front end amplifier, worth about 14 dB on a HackRF. It sits ahead of the gain control, so it costs headroom that gain cannot give back: leave it off near a transmitter, and on for anything faint. Backends with no such amplifier ignore it.", None))
#endif // QT_CONFIG(tooltip)
        self.ampCheckBox.setText(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u"RF a&mp (+14 dB)", None))
        self.mainCurveCheckBox.setText(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u"Main curve", None))
        self.colorsButton.setText(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u"Colors...", None))
        self.peakHoldMaxCheckBox.setText(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u"Max. hold", None))
        self.peakHoldMinCheckBox.setText(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u"Min. hold", None))
        self.averageCheckBox.setText(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u"Average", None))
        self.smoothCheckBox.setText(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u"Smoothing", None))
        self.smoothButton.setText(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u"...", None))
        self.persistenceCheckBox.setText(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u"Persistence", None))
        self.persistenceButton.setText(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u"...", None))
        self.gainSpinBox.setSpecialValueText(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u"auto", None))
        self.baselineCheckBox.setText(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u"Baseline", None))
        self.baselineButton.setText(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u"...", None))
        self.subtractBaselineCheckBox.setText(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u"Subtract baseline", None))
        self.levelsDockWidget.setWindowTitle(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u"Levels", None))
    # retranslateUi

