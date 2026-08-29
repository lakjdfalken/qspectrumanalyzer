from PySide6 import QtCore, QtGui, QtWidgets

from qspectrumanalyzer import backends
from qspectrumanalyzer.data import HistoryBuffer

from qspectrumanalyzer.ui_qspectrumanalyzer_settings import Ui_QSpectrumAnalyzerSettings
from qspectrumanalyzer.ui_qspectrumanalyzer_settings_help import Ui_QSpectrumAnalyzerSettingsHelp


class QSpectrumAnalyzerSettings(QtWidgets.QDialog, Ui_QSpectrumAnalyzerSettings):
    """QSpectrumAnalyzer settings dialog"""
    def __init__(self, parent=None):
        # Initialize UI
        super().__init__(parent)
        self.setupUi(self)
        self.params_help_dialog = None
        self.device_help_dialog = None

        # Load settings
        settings = QtCore.QSettings()
        self.executableEdit.setText(settings.value("executable", "soapy_power"))
        self.deviceEdit.setText(settings.value("device", ""))
        self.lnbSpinBox.setValue(settings.value("lnb_lo", 0, float) / 1e6)
        self.waterfallHistorySizeSpinBox.setValue(settings.value("waterfall_history_size", 100, int))
        self.maxRefreshRateSpinBox.setValue(settings.value("max_refresh_rate", 60, int))
        self.recordDepthSpinBox.setValue(settings.value("record_depth", 1000, int))
        self.recordDepthSpinBox.valueChanged.connect(self.update_record_depth_estimate)
        self.update_record_depth_estimate()

        backend = settings.value("backend", "soapy_power")
        try:
            backend_module = getattr(backends, backend)
        except AttributeError:
            backend_module = backends.soapy_power

        self.paramsEdit.setText(settings.value("params", backend_module.Info.additional_params))
        self.deviceHelpButton.setEnabled(bool(backend_module.Info.help_device))

        self.sampleRateSpinBox.setMinimum(backend_module.Info.sample_rate_min / 1e6)
        self.sampleRateSpinBox.setMaximum(backend_module.Info.sample_rate_max / 1e6)
        self.sampleRateSpinBox.setValue(settings.value("sample_rate", backend_module.Info.sample_rate, float) / 1e6)

        self.bandwidthSpinBox.setMinimum(backend_module.Info.bandwidth_min / 1e6)
        self.bandwidthSpinBox.setMaximum(backend_module.Info.bandwidth_max / 1e6)
        self.bandwidthSpinBox.setValue(settings.value("bandwidth", backend_module.Info.bandwidth, float) / 1e6)

        self.backendComboBox.blockSignals(True)
        self.backendComboBox.clear()
        for b in sorted(backends.__all__):
            self.backendComboBox.addItem(b)

        i = self.backendComboBox.findText(backend)
        if i == -1:
            self.backendComboBox.setCurrentIndex(0)
        else:
            self.backendComboBox.setCurrentIndex(i)
        self.backendComboBox.blockSignals(False)

    @QtCore.Slot()
    def on_executableButton_clicked(self):
        """Open file dialog when button is clicked"""
        filename = QtWidgets.QFileDialog.getOpenFileName(self, self.tr("Select executable - QSpectrumAnalyzer"))[0]
        if filename:
            self.executableEdit.setText(filename)

    @QtCore.Slot()
    def on_paramsHelpButton_clicked(self):
        """Open additional parameters help dialog when button is clicked"""
        try:
            backend_module = getattr(backends, self.backendComboBox.currentText())
        except AttributeError:
            backend_module = backends.soapy_power

        self.params_help_dialog = QSpectrumAnalyzerSettingsHelp(
            backend_module.Info.help_params(self.executableEdit.text()),
            parent=self
        )

        self.params_help_dialog.show()
        self.params_help_dialog.raise_()
        self.params_help_dialog.activateWindow()

    @QtCore.Slot()
    def on_deviceHelpButton_clicked(self):
        """Open device help dialog when button is clicked"""
        try:
            backend_module = getattr(backends, self.backendComboBox.currentText())
        except AttributeError:
            backend_module = backends.soapy_power

        self.device_help_dialog = QSpectrumAnalyzerSettingsHelp(
            backend_module.Info.help_device(self.executableEdit.text(), self.deviceEdit.text()),
            parent=self
        )

        self.device_help_dialog.show()
        self.device_help_dialog.raise_()
        self.device_help_dialog.activateWindow()

    @QtCore.Slot(str)
    def on_backendComboBox_currentTextChanged(self, text):
        """Change executable when backend is changed

        Connected by name to currentTextChanged() rather than to
        currentIndexChanged(), which in Qt6 only carries the index; its
        QString overload is gone, so the old name silently connected to
        nothing and changing the backend stopped updating this dialog."""
        self.executableEdit.setText(text)
        self.deviceEdit.setText("")

        try:
            backend_module = getattr(backends, text)
        except AttributeError:
            backend_module = backends.soapy_power

        self.paramsEdit.setText(backend_module.Info.additional_params)
        self.deviceHelpButton.setEnabled(bool(backend_module.Info.help_device))
        self.sampleRateSpinBox.setMinimum(backend_module.Info.sample_rate_min / 1e6)
        self.sampleRateSpinBox.setMaximum(backend_module.Info.sample_rate_max / 1e6)
        self.sampleRateSpinBox.setValue(backend_module.Info.sample_rate / 1e6)
        self.bandwidthSpinBox.setMinimum(backend_module.Info.bandwidth_min / 1e6)
        self.bandwidthSpinBox.setMaximum(backend_module.Info.bandwidth_max / 1e6)
        self.bandwidthSpinBox.setValue(backend_module.Info.bandwidth / 1e6)

    def current_bin_count(self):
        """Bins per sweep implied by the frequency range currently set"""
        settings = QtCore.QSettings()
        start = settings.value("start_freq", 87.0, float)
        stop = settings.value("stop_freq", 108.0, float)
        bin_size = settings.value("bin_size", 10.0, float)
        if bin_size <= 0 or stop <= start:
            return None
        return int(round((stop - start) * 1e6 / (bin_size * 1e3)))

    @QtCore.Slot()
    def update_record_depth_estimate(self):
        """Show what the chosen recording depth costs in memory"""
        bins = self.current_bin_count()
        if not bins:
            self.recordDepthEstimateLabel.setText("")
            return

        wanted = self.recordDepthSpinBox.value()
        fits = HistoryBuffer.fits(bins, wanted)
        megabytes = fits * bins * 8 * 1.5 / (1024 * 1024)

        if fits < wanted:
            self.recordDepthEstimateLabel.setText(self.tr(
                "~{:.0f} MB at {} bins - capped at {} sweeps").format(megabytes, bins, fits))
        else:
            self.recordDepthEstimateLabel.setText(self.tr(
                "~{:.0f} MB at {} bins").format(megabytes, bins))

    def accept(self):
        """Save settings when dialog is accepted"""
        settings = QtCore.QSettings()
        settings.setValue("backend", self.backendComboBox.currentText())
        settings.setValue("executable", self.executableEdit.text())
        settings.setValue("params", self.paramsEdit.text())
        settings.setValue("device", self.deviceEdit.text())
        settings.setValue("sample_rate", self.sampleRateSpinBox.value() * 1e6)
        settings.setValue("bandwidth", self.bandwidthSpinBox.value() * 1e6)
        settings.setValue("lnb_lo", self.lnbSpinBox.value() * 1e6)
        settings.setValue("waterfall_history_size", self.waterfallHistorySizeSpinBox.value())
        settings.setValue("max_refresh_rate", self.maxRefreshRateSpinBox.value())
        settings.setValue("record_depth", self.recordDepthSpinBox.value())
        QtWidgets.QDialog.accept(self)


class QSpectrumAnalyzerSettingsHelp(QtWidgets.QDialog, Ui_QSpectrumAnalyzerSettingsHelp):
    """QSpectrumAnalyzer settings help dialog"""
    def __init__(self, text, parent=None):
        # Initialize UI
        super().__init__(parent)
        self.setupUi(self)

        # Ask the platform for its fixed-width font instead of guessing a
        # family name. 'monospace' does not exist on macOS, and looking it
        # up cost ~90 ms of font aliasing every time this dialog opened.
        monospace_font = QtGui.QFontDatabase.systemFont(QtGui.QFontDatabase.SystemFont.FixedFont)
        self.helpTextEdit.setFont(monospace_font)
        self.helpTextEdit.setPlainText(text)
