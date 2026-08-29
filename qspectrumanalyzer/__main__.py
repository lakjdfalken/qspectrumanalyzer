#!/usr/bin/env python

import sys, os, signal, time, argparse

from PySide6 import QtCore, QtGui, QtWidgets

from qspectrumanalyzer import backends
from qspectrumanalyzer.version import __version__
from qspectrumanalyzer.data import DataStorage
from qspectrumanalyzer.plot import SpectrumPlotWidget, WaterfallPlotWidget
from qspectrumanalyzer.utils import str_to_color, human_time

from qspectrumanalyzer.settings import QSpectrumAnalyzerSettings
from qspectrumanalyzer.smoothing import QSpectrumAnalyzerSmoothing
from qspectrumanalyzer.persistence import QSpectrumAnalyzerPersistence
from qspectrumanalyzer.colors import QSpectrumAnalyzerColors
from qspectrumanalyzer.baseline import QSpectrumAnalyzerBaseline

from qspectrumanalyzer.ui_qspectrumanalyzer import Ui_QSpectrumAnalyzerMainWindow

debug = False

# Allow CTRL+C and/or SIGTERM to kill us (PyQt blocks it otherwise)
signal.signal(signal.SIGINT, signal.SIG_DFL)
signal.signal(signal.SIGTERM, signal.SIG_DFL)


# Display options that cost redraw time, with the value that is fastest and
# roughly what turning them on costs. Measured with 20000 bins and a 1400 px
# wide plot; the exact figure varies with bin count and window size, but the
# ordering does not.
SPEED_OPTIONS = [
    ("peakHoldMaxCheckBox", False, "slower", "Adds a second curve to every redraw."),
    ("peakHoldMinCheckBox", False, "slower", "Adds a third curve to every redraw."),
    ("averageCheckBox", False, "slower", "Adds another curve, and an average over every sweep."),
    ("smoothCheckBox", False, "slower", "Convolves every sweep before it is drawn."),
    ("persistenceCheckBox", False, "much slower", "Redraws several past traces on top of the live one."),
    ("baselineCheckBox", False, "slower", "Adds another curve to every redraw."),
    ("subtractBaselineCheckBox", False, "slower", "Subtracts the baseline from every sweep."),
]


class QSpectrumAnalyzerMainWindow(QtWidgets.QMainWindow, Ui_QSpectrumAnalyzerMainWindow):
    """QSpectrumAnalyzer main window"""
    def __init__(self, parent=None):
        # Initialize UI
        super().__init__(parent)
        self.setupUi(self)

        # Set window icon
        icon_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "qspectrumanalyzer.svg")
        self.setWindowIcon(QtGui.QIcon(icon_path))

        # Create progress bar
        self.progressbar = QtWidgets.QProgressBar()
        self.progressbar.setMaximumWidth(250)
        self.progressbar.setVisible(False)
        self.statusbar.addPermanentWidget(self.progressbar)

        # Create plot widgets and update UI
        settings = QtCore.QSettings()
        max_refresh_rate = settings.value("max_refresh_rate", 60, int)
        self.spectrumPlotWidget = SpectrumPlotWidget(self.mainPlotLayout,
                                                     max_refresh_rate=max_refresh_rate,
                                                     antialias=settings.value("antialias", 1, int))
        self.waterfallPlotWidget = WaterfallPlotWidget(self.waterfallPlotLayout,
                                                       self.histogramPlotLayout,
                                                       max_refresh_rate=max_refresh_rate)

        # Link main spectrum plot to waterfall plot
        self.spectrumPlotWidget.plot.setXLink(self.waterfallPlotWidget.plot)

        # Setup power thread and connect signals
        self.update_status_timer = QtCore.QTimer()
        self.update_status_timer.timeout.connect(self.update_status)
        self.prev_sweep_time = None
        self.prev_data_timestamp = None
        self.start_timestamp = None
        self.data_storage = None
        self.power_thread = None
        self.backend = None
        self.setup_power_thread()

        # Sweep number currently shown while browsing recorded sweeps
        # (HistoryBuffer.counter of that sweep), or None while live
        self.browse_counter = None

        self.update_buttons()
        self.load_settings()
        self.setup_speed_hints()
        self.update_history_controls()

    def setup_power_thread(self):
        """Create power_thread and connect signals to slots"""
        if self.power_thread:
            self.stop()

        settings = QtCore.QSettings()
        self.data_storage = DataStorage(max_history_size=settings.value("record_depth", 1000, int))
        self.data_storage.data_updated.connect(self.update_data)
        self.data_storage.data_updated.connect(self.spectrumPlotWidget.update_plot)
        self.data_storage.data_updated.connect(self.spectrumPlotWidget.update_persistence)
        self.data_storage.data_recalculated.connect(self.spectrumPlotWidget.recalculate_plot)
        self.data_storage.data_recalculated.connect(self.spectrumPlotWidget.recalculate_persistence)
        self.data_storage.history_updated.connect(self.waterfallPlotWidget.update_plot)
        self.data_storage.history_recalculated.connect(self.waterfallPlotWidget.recalculate_plot)
        self.data_storage.average_updated.connect(self.spectrumPlotWidget.update_average)
        self.data_storage.baseline_updated.connect(self.spectrumPlotWidget.update_baseline)
        self.data_storage.peak_hold_max_updated.connect(self.spectrumPlotWidget.update_peak_hold_max)
        self.data_storage.peak_hold_min_updated.connect(self.spectrumPlotWidget.update_peak_hold_min)

        # Setup default values and limits in case that backend is changed
        backend = settings.value("backend", "soapy_power")
        try:
            backend_module = getattr(backends, backend)
        except AttributeError:
            backend_module = backends.soapy_power

        if self.backend is None or backend != self.backend:
            self.backend = backend
            self.gainSpinBox.setMinimum(backend_module.Info.gain_min)
            self.gainSpinBox.setMaximum(backend_module.Info.gain_max)
            self.gainSpinBox.setValue(backend_module.Info.gain)
            self.startFreqSpinBox.setMinimum(backend_module.Info.start_freq_min)
            self.startFreqSpinBox.setMaximum(backend_module.Info.start_freq_max)
            self.startFreqSpinBox.setValue(backend_module.Info.start_freq)
            self.stopFreqSpinBox.setMinimum(backend_module.Info.stop_freq_min)
            self.stopFreqSpinBox.setMaximum(backend_module.Info.stop_freq_max)
            self.stopFreqSpinBox.setValue(backend_module.Info.stop_freq)
            self.binSizeSpinBox.setMinimum(backend_module.Info.bin_size_min)
            self.binSizeSpinBox.setMaximum(backend_module.Info.bin_size_max)
            self.binSizeSpinBox.setValue(backend_module.Info.bin_size)
            self.intervalSpinBox.setMinimum(backend_module.Info.interval_min)
            self.intervalSpinBox.setMaximum(backend_module.Info.interval_max)
            self.intervalSpinBox.setValue(backend_module.Info.interval)
            self.ppmSpinBox.setMinimum(backend_module.Info.ppm_min)
            self.ppmSpinBox.setMaximum(backend_module.Info.ppm_max)
            self.ppmSpinBox.setValue(backend_module.Info.ppm)
            self.cropSpinBox.setMinimum(backend_module.Info.crop_min)
            self.cropSpinBox.setMaximum(backend_module.Info.crop_max)
            self.cropSpinBox.setValue(backend_module.Info.crop)

        # Setup default values and limits in case that LNB LO is changed
        lnb_lo = settings.value("lnb_lo", 0, float) / 1e6

        start_freq_min = backend_module.Info.start_freq_min + lnb_lo
        start_freq_max = backend_module.Info.start_freq_max + lnb_lo
        start_freq = self.startFreqSpinBox.value()
        stop_freq_min = backend_module.Info.stop_freq_min + lnb_lo
        stop_freq_max = backend_module.Info.stop_freq_max + lnb_lo
        stop_freq = self.stopFreqSpinBox.value()

        self.startFreqSpinBox.setMinimum(start_freq_min if start_freq_min > 0 else 0)
        self.startFreqSpinBox.setMaximum(start_freq_max)
        if start_freq < start_freq_min or start_freq > start_freq_max:
            self.startFreqSpinBox.setValue(start_freq_min)

        self.stopFreqSpinBox.setMinimum(stop_freq_min if stop_freq_min > 0 else 0)
        self.stopFreqSpinBox.setMaximum(stop_freq_max)
        if stop_freq < stop_freq_min or stop_freq > stop_freq_max:
            self.stopFreqSpinBox.setValue(stop_freq_max)

        self.power_thread = backend_module.PowerThread(self.data_storage)
        self.power_thread.powerThreadStarted.connect(self.on_power_thread_started)
        self.power_thread.powerThreadStopped.connect(self.on_power_thread_stopped)

    def setup_speed_hints(self):
        """Annotate the display options that cost redraw time

        Everything starts at its fastest value, so nothing is marked until
        something is switched on. The marker then says what was given up."""
        self.speed_hint_labels = {}
        for name, fastest, severity, why in SPEED_OPTIONS:
            checkbox = getattr(self, name)
            self.speed_hint_labels[name] = checkbox.text()
            checkbox.setToolTip("{}\n\n{}\n{} is fastest.".format(
                checkbox.text().replace("&", ""), why,
                "On" if fastest else "Off"
            ))
            checkbox.toggled.connect(self.update_speed_hints)
        self.update_speed_hints()

    def slower_than_fastest(self):
        """Names of the display options that are not at their fastest value"""
        return [name for name, fastest, _, _ in SPEED_OPTIONS
                if getattr(self, name).isChecked() != fastest]

    def update_speed_hints(self):
        """Mark every display option that is not at its fastest value"""
        for name, fastest, severity, _ in SPEED_OPTIONS:
            checkbox = getattr(self, name)
            text = self.speed_hint_labels[name]
            if checkbox.isChecked() != fastest:
                checkbox.setText("{}   ~ {}".format(text, severity))
                checkbox.setStyleSheet("QCheckBox { color: #d08000; }")
            else:
                checkbox.setText(text)
                checkbox.setStyleSheet("")
        self.update_status()

    # --- browsing recorded sweeps -------------------------------------

    def history_range(self):
        """(oldest, newest) sweep number held in the history buffer"""
        history = self.data_storage.history
        if history is None or not history.history_size:
            return None, None
        return history.counter - history.history_size + 1, history.counter

    def update_history_controls(self):
        """Enable and label the history controls for the current state"""
        oldest, newest = self.history_range()
        browsing = self.browse_counter is not None
        have_history = newest is not None

        self.browseHistoryCheckBox.setEnabled(have_history)
        for widget in (self.historyBackButton, self.historyForwardButton,
                       self.historyStepSpinBox, self.historySlider):
            widget.setEnabled(browsing)

        if not have_history:
            self.historyPositionLabel.setText(self.tr("No recorded sweeps yet"))
            return

        if not browsing:
            self.historyPositionLabel.setText(
                self.tr("Live \u00b7 {} recorded").format(newest - oldest + 1))
            return

        self.historyBackButton.setEnabled(self.browse_counter > oldest)
        self.historyForwardButton.setEnabled(self.browse_counter < newest)
        self.historySlider.blockSignals(True)
        self.historySlider.setRange(oldest, newest)
        self.historySlider.setValue(self.browse_counter)
        self.historySlider.blockSignals(False)
        self.historyPositionLabel.setText(self.tr("Sweep {} \u00b7 {} back of {}").format(
            self.browse_counter, newest - self.browse_counter, newest - oldest + 1))

    def show_browsed_sweep(self):
        """Draw the recorded sweep that is currently selected"""
        oldest, newest = self.history_range()
        if newest is None or self.browse_counter is None:
            return

        # New sweeps keep arriving while browsing, so the oldest ones fall out
        # of the ring buffer. Stay on the same sweep for as long as it is held.
        self.browse_counter = min(max(self.browse_counter, oldest), newest)

        # Copy: get_buffer() is a view into the ring buffer, and later sweeps
        # overwrite that memory in place while we are still showing it
        history = self.data_storage.history.get_buffer()
        y = history[self.browse_counter - oldest].copy()
        if self.data_storage.smooth:
            y = self.data_storage.smooth_data(y)
        self.spectrumPlotWidget.show_sweep(self.data_storage.x, y)
        self.update_history_controls()

    def refresh_browsing(self):
        """Keep the browsed sweep valid as the ring buffer scrolls on"""
        oldest, newest = self.history_range()
        if newest is None or self.browse_counter is None:
            return
        clamped = min(max(self.browse_counter, oldest), newest)
        if clamped != self.browse_counter:
            # The sweep being shown has fallen out of the buffer
            self.browse_counter = clamped
            self.show_browsed_sweep()
        else:
            self.update_history_controls()

    def set_browsing(self, browsing):
        """Switch between the live view and browsing recorded sweeps"""
        oldest, newest = self.history_range()
        if browsing and newest is None:
            browsing = False

        self.browse_counter = newest if browsing else None
        self.spectrumPlotWidget.set_frozen(browsing)
        self.waterfallPlotWidget.set_frozen(browsing)

        if browsing:
            self.show_browsed_sweep()
        else:
            self.update_history_controls()

    def step_history(self, sweeps):
        """Move the browse position by the given number of sweeps"""
        if self.browse_counter is None:
            return
        self.browse_counter += sweeps
        self.show_browsed_sweep()

    @QtCore.Slot(bool)
    def on_browseHistoryCheckBox_toggled(self, checked):
        self.set_browsing(checked)
        if checked != (self.browse_counter is not None):
            # No history to browse yet, so the box could not stay checked
            self.browseHistoryCheckBox.setChecked(False)

    @QtCore.Slot()
    def on_historyBackButton_clicked(self):
        self.step_history(-self.historyStepSpinBox.value())

    @QtCore.Slot()
    def on_historyForwardButton_clicked(self):
        self.step_history(self.historyStepSpinBox.value())

    @QtCore.Slot(int)
    def on_historySlider_valueChanged(self, value):
        if self.browse_counter is not None:
            self.browse_counter = value
            self.show_browsed_sweep()

    def set_dock_size(self, dock, width, height):
        """Ugly hack for resizing QDockWidget (because it doesn't respect minimumSize / sizePolicy set in Designer)
           Link: https://stackoverflow.com/questions/2722939/c-resize-a-docked-qt-qdockwidget-programmatically"""
        old_min_size = dock.minimumSize()
        old_max_size = dock.maximumSize()

        if width >= 0:
            if dock.width() < width:
                dock.setMinimumWidth(width)
            else:
                dock.setMaximumWidth(width)

        if height >= 0:
            if dock.height() < height:
                dock.setMinimumHeight(height)
            else:
                dock.setMaximumHeight(height)

        QtCore.QTimer.singleShot(0, lambda: self.set_dock_size_callback(dock, old_min_size, old_max_size))

    def set_dock_size_callback(self, dock, old_min_size, old_max_size):
        """Return to original QDockWidget minimumSize and maximumSize after running set_dock_size()"""
        dock.setMinimumSize(old_min_size)
        dock.setMaximumSize(old_max_size)

    def load_settings(self):
        """Restore spectrum analyzer settings and window geometry"""
        settings = QtCore.QSettings()
        self.startFreqSpinBox.setValue(settings.value("start_freq", 87.0, float))
        self.stopFreqSpinBox.setValue(settings.value("stop_freq", 108.0, float))
        self.binSizeSpinBox.setValue(settings.value("bin_size", 10.0, float))
        self.intervalSpinBox.setValue(settings.value("interval", 10.0, float))
        self.gainSpinBox.setValue(settings.value("gain", 0, float))
        self.ppmSpinBox.setValue(settings.value("ppm", 0, int))
        self.cropSpinBox.setValue(settings.value("crop", 0, int))
        self.mainCurveCheckBox.setChecked(settings.value("main_curve", 1, int))
        self.peakHoldMaxCheckBox.setChecked(settings.value("peak_hold_max", 0, int))
        self.peakHoldMinCheckBox.setChecked(settings.value("peak_hold_min", 0, int))
        self.averageCheckBox.setChecked(settings.value("average", 0, int))
        self.smoothCheckBox.setChecked(settings.value("smooth", 0, int))
        self.persistenceCheckBox.setChecked(settings.value("persistence", 0, int))
        self.baselineCheckBox.setChecked(settings.value("baseline", 0, int))
        self.subtractBaselineCheckBox.setChecked(settings.value("subtract_baseline", 0, int))

        # Restore window state
        if settings.value("window_state"):
            self.restoreState(settings.value("window_state"))
        if settings.value("plotsplitter_state"):
            self.plotSplitter.restoreState(settings.value("plotsplitter_state"))

        # Migration from older version of config file
        if settings.value("config_version", 1, int) < 2:
            # Make tabs from docks when started for first time
            self.tabifyDockWidget(self.settingsDockWidget, self.levelsDockWidget)
            self.settingsDockWidget.raise_()
            self.set_dock_size(self.controlsDockWidget, 0, 0)
            self.set_dock_size(self.frequencyDockWidget, 0, 0)
            # Update config version
            settings.setValue("config_version", 2)

        # Window geometry has to be restored only after show(), because initial
        # maximization doesn't work otherwise (at least not in some window managers on X11)
        self.show()
        if settings.value("window_geometry"):
            self.restoreGeometry(settings.value("window_geometry"))

    def save_settings(self):
        """Save spectrum analyzer settings and window geometry"""
        settings = QtCore.QSettings()
        settings.setValue("start_freq", self.startFreqSpinBox.value())
        settings.setValue("stop_freq", self.stopFreqSpinBox.value())
        settings.setValue("bin_size", self.binSizeSpinBox.value())
        settings.setValue("interval", self.intervalSpinBox.value())
        settings.setValue("gain", self.gainSpinBox.value())
        settings.setValue("ppm", self.ppmSpinBox.value())
        settings.setValue("crop", self.cropSpinBox.value())
        settings.setValue("main_curve", int(self.mainCurveCheckBox.isChecked()))
        settings.setValue("peak_hold_max", int(self.peakHoldMaxCheckBox.isChecked()))
        settings.setValue("peak_hold_min", int(self.peakHoldMinCheckBox.isChecked()))
        settings.setValue("average", int(self.averageCheckBox.isChecked()))
        settings.setValue("smooth", int(self.smoothCheckBox.isChecked()))
        settings.setValue("persistence", int(self.persistenceCheckBox.isChecked()))
        settings.setValue("baseline", int(self.baselineCheckBox.isChecked()))
        settings.setValue("subtract_baseline", int(self.subtractBaselineCheckBox.isChecked()))

        # Save window state and geometry
        settings.setValue("window_geometry", self.saveGeometry())
        settings.setValue("window_state", self.saveState())
        settings.setValue("plotsplitter_state", self.plotSplitter.saveState())

    def show_status(self, message, timeout=2000):
        """Show message in status bar"""
        self.statusbar.showMessage(message, timeout)

    def update_buttons(self):
        """Update state of control buttons"""
        self.startButton.setEnabled(not self.power_thread.alive)
        self.singleShotButton.setEnabled(not self.power_thread.alive)
        self.stopButton.setEnabled(self.power_thread.alive)

    def update_data(self, data_storage):
        """Update GUI when new data is received

        Only the sweep timing is recorded here. Redrawing the status bar and
        the history controls is left to update_status_timer, because at a few
        hundred sweeps a second there is no point rewriting them per sweep."""
        timestamp = time.time()
        self.prev_sweep_time = timestamp - self.prev_data_timestamp
        self.prev_data_timestamp = timestamp

    def update_status(self):
        """Update status bar"""
        if self.start_timestamp is None or not hasattr(self.power_thread, "params"):
            # Nothing has been measured yet, so there is no sweep rate to show;
            # still report anything that has been traded away for features.
            slower = self.slower_than_fastest()
            if slower:
                self.show_status(self.tr("{} option(s) slower than fastest").format(len(slower)),
                                 timeout=0)
            else:
                self.show_status("", timeout=0)
            return

        timestamp = time.time()
        status = []

        if self.power_thread.params["hops"]:
            status.append(self.tr("Frequency hops: {}").format(self.power_thread.params["hops"]))

        status.append(self.tr("Total time: {} | Sweep time: {:.2f} s ({:.2f} FPS)").format(
            human_time(timestamp - self.start_timestamp),
            self.prev_sweep_time,
            (1 / self.prev_sweep_time) if self.prev_sweep_time else 0
        ))

        slower = self.slower_than_fastest()
        if slower:
            status.append(self.tr("{} option(s) slower than fastest").format(len(slower)))

        if self.browse_counter is not None:
            self.refresh_browsing()
        else:
            self.update_history_controls()

        self.show_status(" | ".join(status), timeout=0)
        self.update_progress(timestamp - self.prev_data_timestamp)

    def update_progress(self, value):
        """Update progress bar"""
        value = int(value * 1000)
        value_max = int(self.intervalSpinBox.value() * 1000)

        if value_max < 1000:
            return

        if value > value_max + 1000:
            self.progressbar.setRange(0, 0)
            value = value_max
        elif value > value_max:
            value = value_max
        else:
            self.progressbar.setRange(0, value_max)

        self.progressbar.setValue(value)

    def on_power_thread_started(self):
        """Update buttons state when power thread is started"""
        self.update_buttons()
        self.progressbar.setVisible(False)

    def on_power_thread_stopped(self):
        """Update buttons state and status bar when power thread is stopped"""
        self.update_buttons()
        self.update_status_timer.stop()
        self.update_status()
        self.progressbar.setVisible(False)

    def start(self, single_shot=False):
        """Start power thread"""
        settings = QtCore.QSettings()

        self.prev_sweep_time = 0
        self.prev_data_timestamp = time.time()
        self.start_timestamp = self.prev_data_timestamp

        if self.intervalSpinBox.value() >= 1:
            self.progressbar.setRange(0, int(self.intervalSpinBox.value() * 1000))
        else:
            self.progressbar.setRange(0, 0)
        self.update_progress(0)
        self.update_status_timer.start(100)

        self.waterfallPlotWidget.history_size = settings.value("waterfall_history_size", 100, int)
        self.waterfallPlotWidget.plot.setYRange(-self.waterfallPlotWidget.history_size, 0)
        self.waterfallPlotWidget.clear_plot()

        self.spectrumPlotWidget.main_curve = bool(self.mainCurveCheckBox.isChecked())
        self.spectrumPlotWidget.main_color = str_to_color(settings.value("main_color", "255, 255, 0, 255"))
        self.spectrumPlotWidget.peak_hold_max = bool(self.peakHoldMaxCheckBox.isChecked())
        self.spectrumPlotWidget.peak_hold_max_color = str_to_color(settings.value("peak_hold_max_color", "255, 0, 0, 255"))
        self.spectrumPlotWidget.peak_hold_min = bool(self.peakHoldMinCheckBox.isChecked())
        self.spectrumPlotWidget.peak_hold_min_color = str_to_color(settings.value("peak_hold_min_color", "0, 0, 255, 255"))
        self.spectrumPlotWidget.average = bool(self.averageCheckBox.isChecked())
        self.spectrumPlotWidget.average_color = str_to_color(settings.value("average_color", "0, 255, 255, 255"))
        self.spectrumPlotWidget.baseline = bool(self.baselineCheckBox.isChecked())
        self.spectrumPlotWidget.baseline_color = str_to_color(settings.value("baseline_color", "255, 0, 255, 255"))
        self.spectrumPlotWidget.persistence = bool(self.persistenceCheckBox.isChecked())
        self.spectrumPlotWidget.persistence_length = settings.value("persistence_length", 5, int)
        self.spectrumPlotWidget.persistence_decay = settings.value("persistence_decay", "exponential")
        self.spectrumPlotWidget.persistence_color = str_to_color(settings.value("persistence_color", "0, 255, 0, 255"))
        self.spectrumPlotWidget.clear_plot()
        self.spectrumPlotWidget.clear_peak_hold_max()
        self.spectrumPlotWidget.clear_peak_hold_min()
        self.spectrumPlotWidget.clear_average()
        self.spectrumPlotWidget.clear_baseline()
        self.spectrumPlotWidget.clear_persistence()

        if self.browse_counter is not None:
            self.browseHistoryCheckBox.setChecked(False)

        self.data_storage.reset()
        self.data_storage.set_smooth(
            bool(self.smoothCheckBox.isChecked()),
            settings.value("smooth_length", 11, int),
            settings.value("smooth_window", "hanning")
        )
        self.data_storage.set_subtract_baseline(
            bool(self.subtractBaselineCheckBox.isChecked()),
            settings.value("baseline_file", None)
        )

        if not self.power_thread.alive:
            self.power_thread.setup(
                float(self.startFreqSpinBox.value()),
                float(self.stopFreqSpinBox.value()),
                float(self.binSizeSpinBox.value()),
                interval=float(self.intervalSpinBox.value()),
                gain=float(self.gainSpinBox.value()),
                ppm=int(self.ppmSpinBox.value()),
                crop=int(self.cropSpinBox.value()) / 100.0,
                single_shot=single_shot,
                device=settings.value("device", ""),
                sample_rate=settings.value("sample_rate", 2560000, float),
                bandwidth=settings.value("bandwidth", 0, float),
                lnb_lo=settings.value("lnb_lo", 0, float)
            )
            self.power_thread.start()

    def stop(self):
        """Stop power thread"""
        if self.power_thread.alive:
            self.power_thread.stop()

    @QtCore.Slot()
    def on_startButton_clicked(self):
        self.start()

    @QtCore.Slot()
    def on_singleShotButton_clicked(self):
        self.start(single_shot=True)

    @QtCore.Slot()
    def on_stopButton_clicked(self):
        self.stop()

    @QtCore.Slot(bool)
    def on_mainCurveCheckBox_toggled(self, checked):
        self.spectrumPlotWidget.set_enabled("plot", checked, self.data_storage)

    @QtCore.Slot(bool)
    def on_peakHoldMaxCheckBox_toggled(self, checked):
        self.spectrumPlotWidget.set_enabled("peak_hold_max", checked, self.data_storage)

    @QtCore.Slot(bool)
    def on_peakHoldMinCheckBox_toggled(self, checked):
        self.spectrumPlotWidget.set_enabled("peak_hold_min", checked, self.data_storage)

    @QtCore.Slot(bool)
    def on_averageCheckBox_toggled(self, checked):
        self.spectrumPlotWidget.set_enabled("average", checked, self.data_storage)

    @QtCore.Slot(bool)
    def on_persistenceCheckBox_toggled(self, checked):
        self.spectrumPlotWidget.set_enabled("persistence", checked, self.data_storage)

    @QtCore.Slot(bool)
    def on_smoothCheckBox_toggled(self, checked):
        settings = QtCore.QSettings()
        self.data_storage.set_smooth(
            checked,
            settings.value("smooth_length", 11, int),
            settings.value("smooth_window", "hanning")
        )

    @QtCore.Slot(bool)
    def on_baselineCheckBox_toggled(self, checked):
        self.spectrumPlotWidget.set_enabled("baseline", checked, self.data_storage)

    @QtCore.Slot(bool)
    def on_subtractBaselineCheckBox_toggled(self, checked):
        settings = QtCore.QSettings()
        self.data_storage.set_subtract_baseline(
            checked,
            settings.value("baseline_file", None)
        )

    @QtCore.Slot()
    def on_baselineButton_clicked(self):
        dialog = QSpectrumAnalyzerBaseline(self)
        if dialog.exec():
            settings = QtCore.QSettings()
            self.data_storage.set_subtract_baseline(
                bool(self.subtractBaselineCheckBox.isChecked()),
                settings.value("baseline_file", None)
            )

    @QtCore.Slot()
    def on_smoothButton_clicked(self):
        dialog = QSpectrumAnalyzerSmoothing(self)
        if dialog.exec():
            settings = QtCore.QSettings()
            self.data_storage.set_smooth(
                bool(self.smoothCheckBox.isChecked()),
                settings.value("smooth_length", 11, int),
                settings.value("smooth_window", "hanning")
            )

    @QtCore.Slot()
    def on_persistenceButton_clicked(self):
        prev_persistence_length = self.spectrumPlotWidget.persistence_length
        dialog = QSpectrumAnalyzerPersistence(self)
        if dialog.exec():
            settings = QtCore.QSettings()
            persistence_length = settings.value("persistence_length", 5, int)
            self.spectrumPlotWidget.persistence_length = persistence_length
            self.spectrumPlotWidget.persistence_decay = settings.value("persistence_decay", "exponential")

            # If only decay function has been changed, just reset colors
            if persistence_length == prev_persistence_length:
                self.spectrumPlotWidget.set_colors()
            else:
                self.spectrumPlotWidget.recalculate_persistence(self.data_storage)

    @QtCore.Slot()
    def on_colorsButton_clicked(self):
        dialog = QSpectrumAnalyzerColors(self)
        if dialog.exec():
            settings = QtCore.QSettings()
            self.spectrumPlotWidget.main_color = str_to_color(settings.value("main_color", "255, 255, 0, 255"))
            self.spectrumPlotWidget.peak_hold_max_color = str_to_color(settings.value("peak_hold_max_color", "255, 0, 0, 255"))
            self.spectrumPlotWidget.peak_hold_min_color = str_to_color(settings.value("peak_hold_min_color", "0, 0, 255, 255"))
            self.spectrumPlotWidget.average_color = str_to_color(settings.value("average_color", "0, 255, 255, 255"))
            self.spectrumPlotWidget.persistence_color = str_to_color(settings.value("persistence_color", "0, 255, 0, 255"))
            self.spectrumPlotWidget.baseline_color = str_to_color(settings.value("baseline_color", "255, 0, 255, 255"))
            self.spectrumPlotWidget.set_colors()

    @QtCore.Slot()
    def on_action_Settings_triggered(self):
        dialog = QSpectrumAnalyzerSettings(self)
        if dialog.exec():
            settings = QtCore.QSettings()
            max_refresh_rate = settings.value("max_refresh_rate", 60, int)
            self.spectrumPlotWidget.set_max_refresh_rate(max_refresh_rate)
            self.waterfallPlotWidget.set_max_refresh_rate(max_refresh_rate)
            self.spectrumPlotWidget.set_antialias(bool(settings.value("antialias", 1, int)))
            self.setup_power_thread()

    @QtCore.Slot()
    def on_action_About_triggered(self):
        QtWidgets.QMessageBox.information(self, self.tr("About - QSpectrumAnalyzer"),
                                          self.tr("QSpectrumAnalyzer {}").format(__version__))

    @QtCore.Slot()
    def on_action_Quit_triggered(self):
        self.close()

    def closeEvent(self, event):
        """Save settings when main window is closed"""
        self.stop()
        self.save_settings()


def main():
    global debug

    # Parse command line arguments
    parser = argparse.ArgumentParser(
        prog="qspectrumanalyzer",
        description="Spectrum analyzer for multiple SDR platforms",
    )
    parser.add_argument("--debug", action="store_true",
                        help="detailed debugging messages")
    parser.add_argument("--version", action="version",
                        version="%(prog)s {}".format(__version__))
    args, unparsed_args = parser.parse_known_args()
    debug = args.debug

    try:
        # Hide console window on Windows
        if sys.platform == 'win32' and not debug:
            from qspectrumanalyzer import windows
            windows.set_attached_console_visible(False)

        # Start PyQt application
        app = QtWidgets.QApplication(sys.argv[:1] + unparsed_args)
        app.setOrganizationName("QSpectrumAnalyzer")
        app.setOrganizationDomain("qspectrumanalyzer.eutopia.cz")
        app.setApplicationName("QSpectrumAnalyzer")
        window = QSpectrumAnalyzerMainWindow()
        sys.exit(app.exec())
    finally:
        # Unhide console window on Windows (we don't want to leave zombies behind)
        if sys.platform == 'win32' and not debug:
            windows.set_attached_console_visible(True)


if __name__ == "__main__":
    main()
