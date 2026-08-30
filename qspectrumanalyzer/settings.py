import re

from PySide6 import QtCore, QtGui, QtWidgets

from qspectrumanalyzer import backends
from qspectrumanalyzer.data import HistoryBuffer
from qspectrumanalyzer.plot import ScopePlotWidget
from qspectrumanalyzer.utils import human_time

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
        self.lnbSpinBox.setValue(settings.value("lnb_lo", 0, float) / 1e6)
        self.waterfallHistorySizeSpinBox.setValue(settings.value("waterfall_history_size", 100, int))
        self.maxRefreshRateSpinBox.setValue(settings.value("max_refresh_rate", 60, int))
        self.recordDepthSpinBox.setValue(settings.value("record_depth", 1000, int))
        self.antialiasCheckBox.setChecked(settings.value("antialias", 1, int))
        self.levelsMeterCheckBox.setChecked(settings.value("levels_meter", 1, int))
        self.tapResolutionSpinBox.setValue(settings.value("tap_resolution", 0, float))
        self.tapDetectorComboBox.setCurrentIndex(
            1 if settings.value("tap_detector", "peak") == "mean" else 0)
        self.sweepDetectorComboBox.setCurrentIndex(
            1 if settings.value("sweep_detector", "mean") == "peak" else 0)
        self.recordDepthSpinBox.valueChanged.connect(self.update_record_depth_estimate)
        self.update_record_depth_estimate()
        self.tapResolutionSpinBox.valueChanged.connect(self.update_tap_estimate)
        self.tapDetectorComboBox.currentIndexChanged.connect(self.update_tap_estimate)
        self.sampleRateSpinBox.valueChanged.connect(self.update_tap_estimate)
        self.backendComboBox.currentTextChanged.connect(self.update_tap_estimate)

        backend = settings.value("backend", "soapy_power")
        try:
            backend_module = getattr(backends, backend)
        except AttributeError:
            backend_module = backends.soapy_power

        self.paramsEdit.setText(settings.value("params", backend_module.Info.additional_params))
        self.populate_devices(backend_module, settings.value("device", ""))

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

        self.update_tap_estimate()

    def populate_devices(self, backend_module, device):
        """Offer whatever devices this backend can see, keeping `device` set

        The field stays editable: a backend that cannot enumerate (or one
        pointed at something not attached yet) still needs a device string
        typed into it, and soapy_power's is not a serial number at all."""
        self.deviceEdit.blockSignals(True)
        self.deviceEdit.clear()

        try:
            devices = backend_module.Info.list_devices()
        except Exception as error:          # noqa: BLE001 - an empty list is the answer
            print("Could not list devices for {}: {}".format(
                backend_module.__name__.rsplit(".", 1)[-1], error))
            devices = []

        if devices:
            self.deviceEdit.addItem(self.tr("Any ({} found)").format(len(devices)), "")
            for value, label in devices:
                self.deviceEdit.addItem(label, value)

        index = self.deviceEdit.findData(device)
        if index != -1:
            self.deviceEdit.setCurrentIndex(index)
        else:
            # Either nothing to choose from, or a device that is not attached
            # right now; leave what was set rather than silently changing it
            self.deviceEdit.setCurrentText(device)
        self.deviceEdit.blockSignals(False)

        self.deviceHelpButton.setEnabled(bool(backend_module.Info.help_device))

    def current_device(self):
        """The device string to save

        Combo box entries carry the value to store as item data, because what
        is shown for a device is not what identifies it."""
        index = self.deviceEdit.currentIndex()
        if index != -1 and self.deviceEdit.itemText(index) == self.deviceEdit.currentText():
            return self.deviceEdit.itemData(index) or ""
        return self.deviceEdit.currentText()

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
            backend_module.Info.help_device(self.executableEdit.text(), self.current_device()),
            parent=self
        )

        # Opening the help is also the moment to rescan: it is what somebody
        # reaches for after plugging a radio in
        self.populate_devices(backend_module, self.current_device())

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

        try:
            backend_module = getattr(backends, text)
        except AttributeError:
            backend_module = backends.soapy_power

        self.paramsEdit.setText(backend_module.Info.additional_params)
        # A device string belongs to the backend that was chosen, so start the
        # new one on whatever it can actually see
        self.populate_devices(backend_module, "")
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
        megabytes = fits * bins * 4 * 1.5 / (1024 * 1024)

        text = self.tr("~{:.0f} MB at {} bins").format(megabytes, bins)
        if fits < wanted:
            text += self.tr(" - capped at {} sweeps").format(fits)

        # A depth in sweeps only means something once you know how fast they
        # arrive, and that is the number somebody recording a few minutes of
        # signal is actually working in
        rate, guessed = self.expected_sweep_rate()
        if rate:
            # A backend sweeping once every ten seconds has a rate of 0.1, and
            # rounding that to a whole number reads as "0 sweeps/s"
            shown = "{:.0f}".format(rate) if rate >= 1 else "{:.3g}".format(rate)
            text += self.tr(" - {} at {}{} sweeps/s").format(
                human_time(fits / rate), "~" if guessed else "", shown)

        self.recordDepthEstimateLabel.setText(text)

    def expected_sweep_rate(self):
        """Sweeps a second to reckon the recording depth against

        Returns (rate, guessed). Measured while something is running, which is
        the only figure that is really true. Before that it has to come out of
        the settings, so that the depth means something before the first run
        rather than only after it: an interval names the rate outright, and a
        backend that delivers as fast as it can names a ceiling instead."""
        measured = getattr(self.parent(), "sweep_rate", 0)
        if measured:
            return measured, False

        interval = getattr(self.parent(), "intervalSpinBox", None)
        if interval is not None and interval.value() > 0:
            return 1.0 / interval.value(), True

        capped = re.search(r"--max-rate\s+(\d+(?:\.\d+)?)", self.paramsEdit.text())
        if capped:
            return float(capped.group(1)), True
        return 0, False

    def frame_duration(self):
        """Seconds of signal in one FFT frame, for the backend in use

        None when the backend has no band tap to have a frame rate, or when
        the frequency settings do not yet describe one."""
        backend = self.backendComboBox.currentText()
        module = getattr(backends, backend, None)
        if module is None or not hasattr(module.PowerThread, "set_band"):
            return None
        try:
            from hackrf_stream import dsp
        except ImportError:
            return None

        sample_rate = self.sampleRateSpinBox.value() * 1e6
        bin_size = getattr(self.parent(), "binSizeSpinBox", None)
        if not sample_rate or bin_size is None or bin_size.value() <= 0:
            return None
        return dsp.fast_fft_size(sample_rate, bin_size.value() * 1e3) / sample_rate

    @QtCore.Slot()
    def update_tap_estimate(self):
        """Show what the zero span step comes out as, and how far back it reaches

        The step is rounded to whole frames, and how much of it can be kept is
        fixed, so what somebody actually wants to know — how short a burst this
        resolves and how far back the trace goes — takes working out."""
        frame = self.frame_duration()
        if frame is None:
            self.tapEstimateLabel.setText(
                self.tr("The selected backend has no high-rate tap"))
            return

        asked = self.tapResolutionSpinBox.value() / 1e6
        group = max(1, int(round(asked / frame))) if asked else 1
        step = group * frame

        capacity = ScopePlotWidget.FAST_CAPACITY
        # Two float64 per reading, in a ring buffer that over-allocates by half
        megabytes = capacity * 2 * 8 * 1.5 / (1024 * 1024)
        frames = (self.tr("1 frame") if group == 1
                  else self.tr("{} frames").format(group))

        # How much a reading of plain noise moves about. One frame measures
        # 3.3 dB; averaging smooths as the square root of the count, while a
        # peak keeps the loudest frame and barely smooths at all. Both figures
        # are measured, not derived.
        if self.tapDetectorComboBox.currentIndex() == 1:
            wobble = 3.3 / (group ** 0.5)
        else:
            wobble = 3.3 / (group ** 0.25)

        self.tapEstimateLabel.setText(
            self.tr("{:.1f} us per reading ({} of {:.1f} us), noise wobbles "
                    "~{:.1f} dB - {} of it kept, ~{:.0f} MB").format(
                        step * 1e6, frames, frame * 1e6, wobble,
                        human_time(capacity * step), megabytes))

    def accept(self):
        """Save settings when dialog is accepted"""
        settings = QtCore.QSettings()
        settings.setValue("backend", self.backendComboBox.currentText())
        settings.setValue("executable", self.executableEdit.text())
        settings.setValue("params", self.paramsEdit.text())
        settings.setValue("device", self.current_device())
        settings.setValue("sample_rate", self.sampleRateSpinBox.value() * 1e6)
        settings.setValue("bandwidth", self.bandwidthSpinBox.value() * 1e6)
        settings.setValue("lnb_lo", self.lnbSpinBox.value() * 1e6)
        settings.setValue("waterfall_history_size", self.waterfallHistorySizeSpinBox.value())
        settings.setValue("max_refresh_rate", self.maxRefreshRateSpinBox.value())
        settings.setValue("record_depth", self.recordDepthSpinBox.value())
        settings.setValue("tap_resolution", self.tapResolutionSpinBox.value())
        settings.setValue("tap_detector",
                          "mean" if self.tapDetectorComboBox.currentIndex() == 1 else "peak")
        settings.setValue("sweep_detector",
                          "peak" if self.sweepDetectorComboBox.currentIndex() == 1 else "mean")
        settings.setValue("antialias", int(self.antialiasCheckBox.isChecked()))
        settings.setValue("levels_meter", int(self.levelsMeterCheckBox.isChecked()))
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
