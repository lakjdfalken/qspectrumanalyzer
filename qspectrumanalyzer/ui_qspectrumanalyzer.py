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
from PySide6.QtWidgets import (QApplication, QCheckBox, QDockWidget, QDoubleSpinBox,
    QFormLayout, QGridLayout, QGroupBox, QHBoxLayout,
    QLabel, QMainWindow, QMenu, QMenuBar,
    QPushButton, QSizePolicy, QSlider, QSpacerItem,
    QSpinBox, QSplitter, QStatusBar, QToolButton,
    QVBoxLayout, QWidget)

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
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.controlsDockWidget.sizePolicy().hasHeightForWidth())
        self.controlsDockWidget.setSizePolicy(sizePolicy1)
        self.controlsDockWidget.setMinimumSize(QSize(190, 130))
        self.controlsDockWidget.setFeatures(QDockWidget.DockWidgetFloatable|QDockWidget.DockWidgetMovable)
        self.controlsDockWidgetContents = QWidget()
        self.controlsDockWidgetContents.setObjectName(u"controlsDockWidgetContents")
        self.gridLayout_2 = QGridLayout(self.controlsDockWidgetContents)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.startButton = QPushButton(self.controlsDockWidgetContents)
        self.startButton.setObjectName(u"startButton")

        self.gridLayout_2.addWidget(self.startButton, 0, 0, 1, 1)

        self.stopButton = QPushButton(self.controlsDockWidgetContents)
        self.stopButton.setObjectName(u"stopButton")

        self.gridLayout_2.addWidget(self.stopButton, 0, 1, 1, 1)

        self.singleShotButton = QPushButton(self.controlsDockWidgetContents)
        self.singleShotButton.setObjectName(u"singleShotButton")

        self.gridLayout_2.addWidget(self.singleShotButton, 1, 0, 1, 2)

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


        self.gridLayout_2.addWidget(self.historyGroupBox, 2, 0, 1, 2)

        self.verticalSpacer = QSpacerItem(20, 561, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout_2.addItem(self.verticalSpacer, 3, 0, 1, 1)

        self.controlsDockWidget.setWidget(self.controlsDockWidgetContents)
        QSpectrumAnalyzerMainWindow.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.controlsDockWidget)
        self.frequencyDockWidget = QDockWidget(QSpectrumAnalyzerMainWindow)
        self.frequencyDockWidget.setObjectName(u"frequencyDockWidget")
        sizePolicy1.setHeightForWidth(self.frequencyDockWidget.sizePolicy().hasHeightForWidth())
        self.frequencyDockWidget.setSizePolicy(sizePolicy1)
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
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.startFreqSpinBox.sizePolicy().hasHeightForWidth())
        self.startFreqSpinBox.setSizePolicy(sizePolicy2)
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
        sizePolicy2.setHeightForWidth(self.stopFreqSpinBox.sizePolicy().hasHeightForWidth())
        self.stopFreqSpinBox.setSizePolicy(sizePolicy2)
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

        self.binSizeSpinBox = QDoubleSpinBox(self.frequencyDockWidgetContents)
        self.binSizeSpinBox.setObjectName(u"binSizeSpinBox")
        sizePolicy2.setHeightForWidth(self.binSizeSpinBox.sizePolicy().hasHeightForWidth())
        self.binSizeSpinBox.setSizePolicy(sizePolicy2)
        self.binSizeSpinBox.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.binSizeSpinBox.setProperty(u"showGroupSeparator", True)
        self.binSizeSpinBox.setDecimals(3)
        self.binSizeSpinBox.setMinimum(0.000000000000000)
        self.binSizeSpinBox.setMaximum(10000.000000000000000)
        self.binSizeSpinBox.setValue(10.000000000000000)

        self.formLayout.setWidget(2, QFormLayout.ItemRole.FieldRole, self.binSizeSpinBox)

        self.verticalSpacer_3 = QSpacerItem(20, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.formLayout.setItem(3, QFormLayout.ItemRole.SpanningRole, self.verticalSpacer_3)

        self.frequencyDockWidget.setWidget(self.frequencyDockWidgetContents)
        QSpectrumAnalyzerMainWindow.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.frequencyDockWidget)
        self.settingsDockWidget = QDockWidget(QSpectrumAnalyzerMainWindow)
        self.settingsDockWidget.setObjectName(u"settingsDockWidget")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.settingsDockWidget.sizePolicy().hasHeightForWidth())
        self.settingsDockWidget.setSizePolicy(sizePolicy3)
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

        self.mainCurveCheckBox = QCheckBox(self.settingsDockWidgetContents)
        self.mainCurveCheckBox.setObjectName(u"mainCurveCheckBox")
        self.mainCurveCheckBox.setChecked(True)

        self.gridLayout.addWidget(self.mainCurveCheckBox, 4, 0, 1, 1)

        self.colorsButton = QPushButton(self.settingsDockWidgetContents)
        self.colorsButton.setObjectName(u"colorsButton")

        self.gridLayout.addWidget(self.colorsButton, 4, 1, 1, 2)

        self.peakHoldMaxCheckBox = QCheckBox(self.settingsDockWidgetContents)
        self.peakHoldMaxCheckBox.setObjectName(u"peakHoldMaxCheckBox")

        self.gridLayout.addWidget(self.peakHoldMaxCheckBox, 5, 0, 1, 1)

        self.peakHoldMinCheckBox = QCheckBox(self.settingsDockWidgetContents)
        self.peakHoldMinCheckBox.setObjectName(u"peakHoldMinCheckBox")

        self.gridLayout.addWidget(self.peakHoldMinCheckBox, 5, 1, 1, 2)

        self.averageCheckBox = QCheckBox(self.settingsDockWidgetContents)
        self.averageCheckBox.setObjectName(u"averageCheckBox")

        self.gridLayout.addWidget(self.averageCheckBox, 6, 0, 1, 1)

        self.smoothCheckBox = QCheckBox(self.settingsDockWidgetContents)
        self.smoothCheckBox.setObjectName(u"smoothCheckBox")

        self.gridLayout.addWidget(self.smoothCheckBox, 7, 0, 1, 1)

        self.smoothButton = QToolButton(self.settingsDockWidgetContents)
        self.smoothButton.setObjectName(u"smoothButton")
        self.smoothButton.setAutoRaise(False)

        self.gridLayout.addWidget(self.smoothButton, 7, 2, 1, 1)

        self.persistenceCheckBox = QCheckBox(self.settingsDockWidgetContents)
        self.persistenceCheckBox.setObjectName(u"persistenceCheckBox")

        self.gridLayout.addWidget(self.persistenceCheckBox, 8, 0, 1, 1)

        self.persistenceButton = QToolButton(self.settingsDockWidgetContents)
        self.persistenceButton.setObjectName(u"persistenceButton")
        self.persistenceButton.setAutoRaise(False)

        self.gridLayout.addWidget(self.persistenceButton, 8, 2, 1, 1)

        self.verticalSpacer_2 = QSpacerItem(20, 1, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout.addItem(self.verticalSpacer_2, 11, 0, 1, 1)

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

        self.gridLayout.addWidget(self.baselineCheckBox, 9, 0, 1, 1)

        self.baselineButton = QToolButton(self.settingsDockWidgetContents)
        self.baselineButton.setObjectName(u"baselineButton")
        self.baselineButton.setAutoRaise(False)

        self.gridLayout.addWidget(self.baselineButton, 9, 2, 1, 1)

        self.subtractBaselineCheckBox = QCheckBox(self.settingsDockWidgetContents)
        self.subtractBaselineCheckBox.setObjectName(u"subtractBaselineCheckBox")

        self.gridLayout.addWidget(self.subtractBaselineCheckBox, 10, 0, 1, 1)

        self.settingsDockWidget.setWidget(self.settingsDockWidgetContents)
        QSpectrumAnalyzerMainWindow.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.settingsDockWidget)
        self.levelsDockWidget = QDockWidget(QSpectrumAnalyzerMainWindow)
        self.levelsDockWidget.setObjectName(u"levelsDockWidget")
        sizePolicy3.setHeightForWidth(self.levelsDockWidget.sizePolicy().hasHeightForWidth())
        self.levelsDockWidget.setSizePolicy(sizePolicy3)
        self.levelsDockWidget.setFeatures(QDockWidget.DockWidgetFloatable|QDockWidget.DockWidgetMovable)
        self.levelsDockWidgetContents = QWidget()
        self.levelsDockWidgetContents.setObjectName(u"levelsDockWidgetContents")
        self.verticalLayout_6 = QVBoxLayout(self.levelsDockWidgetContents)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.histogramPlotLayout = GraphicsLayoutWidget(self.levelsDockWidgetContents)
        self.histogramPlotLayout.setObjectName(u"histogramPlotLayout")
        sizePolicy4 = QSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Expanding)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.histogramPlotLayout.sizePolicy().hasHeightForWidth())
        self.histogramPlotLayout.setSizePolicy(sizePolicy4)

        self.verticalLayout_6.addWidget(self.histogramPlotLayout)

        self.levelsDockWidget.setWidget(self.levelsDockWidgetContents)
        QSpectrumAnalyzerMainWindow.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.levelsDockWidget)
#if QT_CONFIG(shortcut)
        self.label_2.setBuddy(self.startFreqSpinBox)
        self.label_3.setBuddy(self.stopFreqSpinBox)
        self.label.setBuddy(self.binSizeSpinBox)
        self.label_4.setBuddy(self.intervalSpinBox)
        self.label_6.setBuddy(self.gainSpinBox)
        self.label_5.setBuddy(self.ppmSpinBox)
        self.label_7.setBuddy(self.cropSpinBox)
#endif // QT_CONFIG(shortcut)
        QWidget.setTabOrder(self.startButton, self.stopButton)
        QWidget.setTabOrder(self.stopButton, self.singleShotButton)
        QWidget.setTabOrder(self.singleShotButton, self.browseHistoryCheckBox)
        QWidget.setTabOrder(self.browseHistoryCheckBox, self.historyBackButton)
        QWidget.setTabOrder(self.historyBackButton, self.historyStepSpinBox)
        QWidget.setTabOrder(self.historyStepSpinBox, self.historyForwardButton)
        QWidget.setTabOrder(self.historyForwardButton, self.historySlider)
        QWidget.setTabOrder(self.historySlider, self.startFreqSpinBox)
        QWidget.setTabOrder(self.startFreqSpinBox, self.stopFreqSpinBox)
        QWidget.setTabOrder(self.stopFreqSpinBox, self.binSizeSpinBox)
        QWidget.setTabOrder(self.binSizeSpinBox, self.intervalSpinBox)
        QWidget.setTabOrder(self.intervalSpinBox, self.gainSpinBox)
        QWidget.setTabOrder(self.gainSpinBox, self.ppmSpinBox)
        QWidget.setTabOrder(self.ppmSpinBox, self.cropSpinBox)
        QWidget.setTabOrder(self.cropSpinBox, self.mainCurveCheckBox)
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
        self.frequencyDockWidget.setWindowTitle(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u"Frequency", None))
        self.label_2.setText(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u"Start:", None))
        self.startFreqSpinBox.setSuffix(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u" MHz", None))
        self.label_3.setText(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u"Stop:", None))
        self.stopFreqSpinBox.setSuffix(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u" MHz", None))
        self.label.setText(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u"&Bin size:", None))
        self.binSizeSpinBox.setSuffix(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u" kHz", None))
        self.settingsDockWidget.setWindowTitle(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u"Settings", None))
        self.label_4.setText(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u"&Interval [s]:", None))
        self.label_6.setText(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u"&Gain [dB]:", None))
        self.label_5.setText(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u"Corr. [ppm]:", None))
        self.label_7.setText(QCoreApplication.translate("QSpectrumAnalyzerMainWindow", u"Crop [%]:", None))
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

