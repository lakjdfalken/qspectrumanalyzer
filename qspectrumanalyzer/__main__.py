#!/usr/bin/env python

import sys, os, csv, signal, time, argparse

from PySide6 import QtCore, QtGui, QtWidgets

from qspectrumanalyzer import backends
from qspectrumanalyzer.version import __version__
from qspectrumanalyzer.data import DataStorage
from qspectrumanalyzer.plot import (ScopePlotWidget, SpectrumPlotWidget,
                                    WaterfallPlotWidget)
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


# Ready-made settings for jobs that need several controls to agree with each
# other. The bin size decides how short a pulse survives being measured (a 1 us
# pulse smeared over a 25.6 us frame loses 14 dB); the detector decides whether
# it survives at all (a mean destroys it, a peak keeps it); the zero span step
# decides how far back the trace reaches; and the recording depth decides
# whether a whole scan cycle fits on screen. Any one of them wrong quietly
# wastes an evening, so the job is what gets chosen and the settings follow.
#
# Each entry is (label, note printed when chosen, widgets to set, settings to
# write). Widgets are applied in order, so frequency and bin size come before
# anything that is measured in bins.
RADAR_PRESETS = [
    ("Custom \u2014 leave everything alone", None, {}, {}),

    ("Airband voice \u2014 118-137 MHz",
     "The whole airband in one tune, with max hold and the waterfall on. This "
     "is the honest test of a chain: it is a band you already know is busy, "
     "and a telescopic whip is cut for it. Every transmission paints the "
     "waterfall and lifts the scope, which is reading the peak across the "
     "whole 19 MHz. If this shows nothing, the problem is the radio or the "
     "lead, not the frequency you were hunting.",
     {'mainCurveCheckBox': True, 'peakHoldMaxCheckBox': True, 'peakHoldMinCheckBox': False, 'averageCheckBox': False, 'persistenceCheckBox': False, 'smoothCheckBox': False, 'gainSpinBox': 40.0, 'startFreqSpinBox': 118.0, 'stopFreqSpinBox': 137.0, 'binSizeSpinBox': 25.0, 'waterfallCheckBox': True, 'scopeCheckBox': True, 'scopeBandCheckBox': False, 'scopeCentreSpinBox': 127.5, 'scopeWidthSpinBox': 25.0, 'scopeFastCheckBox': True, 'scopeSpanSpinBox': 2000.0, 'scopeTriggerCheckBox': False, 'scopeTriggerSpinBox': -200.0, 'scopeSingleCheckBox': False},
     {"tap_resolution": 1000.0, "tap_detector": "mean", "record_depth": 10000}),

    ("C-band weather radar \u2014 find the channel",
     "Sweeping 5600-5650 MHz with max hold. Leave it for fifteen minutes: the "
     "duty cycle is tiny, so nothing but max hold will paint it. The peak that "
     "appears is the radar's channel.",
     {'mainCurveCheckBox': True, 'peakHoldMaxCheckBox': True, 'peakHoldMinCheckBox': False, 'averageCheckBox': False, 'persistenceCheckBox': False, 'smoothCheckBox': False, 'gainSpinBox': 40.0, 'startFreqSpinBox': 5600.0, 'stopFreqSpinBox': 5650.0, 'binSizeSpinBox': 40.0, 'waterfallCheckBox': True, 'scopeCheckBox': False, 'scopeBandCheckBox': False, 'scopeCentreSpinBox': 5625.0, 'scopeWidthSpinBox': 2000.0, 'scopeFastCheckBox': False, 'scopeSpanSpinBox': 0.0, 'scopeTriggerCheckBox': False, 'scopeTriggerSpinBox': -200.0, 'scopeSingleCheckBox': False},
     {"tap_resolution": 0.0, "tap_detector": "peak", "record_depth": 10000}),

    ("C-band weather radar \u2014 catch a burst",
     "625 kHz bins, so a 1 us pulse loses 2 dB instead of 14; peak detector, "
     "because an average would destroy it; 20 ms sweep armed on a rising edge. "
     "Put the centre on whatever the channel hunt found, press Arm, and wait "
     "for the antenna to come round.",
     {'mainCurveCheckBox': True, 'peakHoldMaxCheckBox': False, 'peakHoldMinCheckBox': False, 'averageCheckBox': False, 'persistenceCheckBox': False, 'smoothCheckBox': False, 'gainSpinBox': 40.0, 'startFreqSpinBox': 5615.0, 'stopFreqSpinBox': 5635.0, 'binSizeSpinBox': 625.0, 'waterfallCheckBox': False, 'scopeCheckBox': True, 'scopeBandCheckBox': True, 'scopeCentreSpinBox': 5625.0, 'scopeWidthSpinBox': 2000.0, 'scopeFastCheckBox': True, 'scopeSpanSpinBox': 20.0, 'scopeTriggerCheckBox': True, 'scopeTriggerSpinBox': -200.0, 'scopeSingleCheckBox': True},
     {"tap_resolution": 0.0, "tap_detector": "peak", "record_depth": 10000}),

    ("C-band weather radar \u2014 time the scan cycle",
     "A 1 ms step with the peak detector keeps every pulse but reaches back "
     "seventeen minutes, and the recording is deepened to match. Look for a "
     "dwell every 15-22 seconds for three minutes, then two minutes of "
     "silence: that five minute cycle is what tells a weather radar from an "
     "airport one.",
     {'mainCurveCheckBox': True, 'peakHoldMaxCheckBox': False, 'peakHoldMinCheckBox': False, 'averageCheckBox': False, 'persistenceCheckBox': False, 'smoothCheckBox': False, 'gainSpinBox': 40.0, 'startFreqSpinBox': 5615.0, 'stopFreqSpinBox': 5635.0, 'binSizeSpinBox': 625.0, 'waterfallCheckBox': False, 'scopeCheckBox': True, 'scopeBandCheckBox': True, 'scopeCentreSpinBox': 5625.0, 'scopeWidthSpinBox': 2000.0, 'scopeFastCheckBox': True, 'scopeSpanSpinBox': 0.0, 'scopeTriggerCheckBox': False, 'scopeTriggerSpinBox': -200.0, 'scopeSingleCheckBox': False},
     {"tap_resolution": 1000.0, "tap_detector": "peak", "record_depth": 85000}),

    ("S-band airport radar \u2014 find the channel",
     "Sweeping 2700-2900 MHz with max hold. That is the band air traffic "
     "primary radar uses, which is not a fact about any particular airport: "
     "plenty of regional fields have no primary radar at all, and a radar head "
     "is often sited miles from the runway. Try the 1030 MHz interrogator "
     "first; it is far easier to catch and it proves there is a radar to look "
     "for. CHECK THE INPUT FIRST: a "
     "surveillance radar a couple of kilometres away can put +18 dBm into the "
     "antenna and a HackRF is linear to about -5 dBm. Gain is set to zero here, "
     "which keeps the reading out of compression but does nothing for the front "
     "end - only an attenuator in the lead does that.",
     {'mainCurveCheckBox': True, 'peakHoldMaxCheckBox': True, 'peakHoldMinCheckBox': False, 'averageCheckBox': False, 'persistenceCheckBox': False, 'smoothCheckBox': False, 'gainSpinBox': 0.0, 'startFreqSpinBox': 2700.0, 'stopFreqSpinBox': 2900.0, 'binSizeSpinBox': 40.0, 'waterfallCheckBox': True, 'scopeCheckBox': False, 'scopeBandCheckBox': False, 'scopeCentreSpinBox': 2800.0, 'scopeWidthSpinBox': 2000.0, 'scopeFastCheckBox': False, 'scopeSpanSpinBox': 0.0, 'scopeTriggerCheckBox': False, 'scopeTriggerSpinBox': -200.0, 'scopeSingleCheckBox': False},
     {"tap_resolution": 0.0, "tap_detector": "peak", "record_depth": 10000}),

    ("S-band airport radar \u2014 catch a burst",
     "The C-band burst settings moved to the channel the hunt found. An "
     "approach radar turns every 4-5 seconds and lights you for about 20 ms "
     "with pulses roughly 1 ms apart, so a 20 ms sweep holds a dozen of them. "
     "The attenuation still applies.",
     {'mainCurveCheckBox': True, 'peakHoldMaxCheckBox': False, 'peakHoldMinCheckBox': False, 'averageCheckBox': False, 'persistenceCheckBox': False, 'smoothCheckBox': False, 'gainSpinBox': 0.0, 'startFreqSpinBox': 2790.0, 'stopFreqSpinBox': 2810.0, 'binSizeSpinBox': 625.0, 'waterfallCheckBox': False, 'scopeCheckBox': True, 'scopeBandCheckBox': True, 'scopeCentreSpinBox': 2800.0, 'scopeWidthSpinBox': 2000.0, 'scopeFastCheckBox': True, 'scopeSpanSpinBox': 20.0, 'scopeTriggerCheckBox': True, 'scopeTriggerSpinBox': -200.0, 'scopeSingleCheckBox': True},
     {"tap_resolution": 0.0, "tap_detector": "peak", "record_depth": 10000}),

    ("Airport transponder replies \u2014 1090 MHz",
     "Every aircraft with a transponder answers on 1090 MHz. A frame lasts "
     "120 us and each aircraft sends a couple a second, so the duty cycle is "
     "tiny and only max hold will paint it - the live trace averages it away "
     "to nothing. The tune is deliberately off centre, because the radio's own "
     "DC offset lands in the middle of a tune and 1090 is what we came for. "
     "Needs an antenna that works at 1090: a telescopic whip is cut for VHF "
     "and is a poor match eight times up.",
     {'mainCurveCheckBox': True, 'peakHoldMaxCheckBox': True, 'peakHoldMinCheckBox': False, 'averageCheckBox': False, 'persistenceCheckBox': False, 'smoothCheckBox': False, 'gainSpinBox': 40.0, 'startFreqSpinBox': 1082.0, 'stopFreqSpinBox': 1102.0, 'binSizeSpinBox': 40.0, 'waterfallCheckBox': True, 'scopeCheckBox': True, 'scopeBandCheckBox': True, 'scopeCentreSpinBox': 1090.0, 'scopeWidthSpinBox': 4000.0, 'scopeFastCheckBox': True, 'scopeSpanSpinBox': 5.0, 'scopeTriggerCheckBox': True, 'scopeTriggerSpinBox': -200.0, 'scopeSingleCheckBox': False},
     {"tap_resolution": 0.0, "tap_detector": "peak", "record_depth": 10000}),

    ("Airport radar interrogator \u2014 1030 MHz",
     "Secondary radar interrogates on 1030 MHz from an antenna that turns with "
     "the primary one, so this finds the radar and times its rotation without "
     "needing to know what band the primary uses. Expect a burst every 4-12 "
     "seconds as the beam comes round. Much easier than 2.8 GHz: lower "
     "frequency, longer pulses, and it transmits all the time rather than only "
     "when pointing at you.",
     {'mainCurveCheckBox': True, 'peakHoldMaxCheckBox': True, 'peakHoldMinCheckBox': False, 'averageCheckBox': False, 'persistenceCheckBox': False, 'smoothCheckBox': False, 'gainSpinBox': 8.0, 'startFreqSpinBox': 1022.0, 'stopFreqSpinBox': 1042.0, 'binSizeSpinBox': 40.0, 'waterfallCheckBox': True, 'scopeCheckBox': True, 'scopeBandCheckBox': True, 'scopeCentreSpinBox': 1030.0, 'scopeWidthSpinBox': 4000.0, 'scopeFastCheckBox': True, 'scopeSpanSpinBox': 0.0, 'scopeTriggerCheckBox': False, 'scopeTriggerSpinBox': -200.0, 'scopeSingleCheckBox': False},
     {"tap_resolution": 0.0, "tap_detector": "peak", "record_depth": 10000}),

    ("Wi-Fi burst \u2014 5 GHz channel 36",
     "A Wi-Fi frame lasts tenths of a millisecond rather than a microsecond, "
     "so this smooths instead of chasing pulses: a 100 us step with the average "
     "detector, which drops the wobble from 3.3 dB to 1.6 and makes the shape "
     "of a frame legible. Free running, so the traffic scrolls past.",
     {'mainCurveCheckBox': True, 'peakHoldMaxCheckBox': False, 'peakHoldMinCheckBox': False, 'averageCheckBox': False, 'persistenceCheckBox': False, 'smoothCheckBox': False, 'gainSpinBox': 20.0, 'startFreqSpinBox': 5170.0, 'stopFreqSpinBox': 5190.0, 'binSizeSpinBox': 40.0, 'waterfallCheckBox': True, 'scopeCheckBox': True, 'scopeBandCheckBox': True, 'scopeCentreSpinBox': 5180.0, 'scopeWidthSpinBox': 20000.0, 'scopeFastCheckBox': True, 'scopeSpanSpinBox': 20.0, 'scopeTriggerCheckBox': False, 'scopeTriggerSpinBox': -200.0, 'scopeSingleCheckBox': False},
     {"tap_resolution": 100.0, "tap_detector": "mean", "record_depth": 10000}),
]


class QSpectrumAnalyzerMainWindow(QtWidgets.QMainWindow, Ui_QSpectrumAnalyzerMainWindow):
    """QSpectrumAnalyzer main window"""

    #: Seconds the sweep rate is averaged over, and how long a backend that has
    #: gone quiet is given before the footer admits to a rate of zero
    RATE_WINDOW = 0.5
    RATE_STALE = 3.0

    #: Slowest the display will redraw itself down to when it is starving the
    #: backend, and how long it must go without a dropped sample before taking
    #: a step back up
    REFRESH_FLOOR = 8
    REFRESH_RECOVER = 15.0

    #: Sweep length given to the scope when a trigger is asked for and none
    #: has been chosen, in milliseconds
    DEFAULT_SWEEP_MS = 10.0

    def __init__(self, parent=None):
        # Initialize UI
        super().__init__(parent)
        self.setupUi(self)

        # Set window icon
        icon_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "qspectrumanalyzer.svg")
        self.setWindowIcon(QtGui.QIcon(icon_path))

        # Splitter index -> the height that pane had when it was last on
        # screen, so that switching it off and back on does not shrink it
        self.pane_heights = {}

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
        self.waterfallPlotWidget = WaterfallPlotWidget(
            self.waterfallPlotLayout, self.histogramPlotLayout,
            max_refresh_rate=max_refresh_rate,
            levels_meter=bool(settings.value("levels_meter", 1, int)))
        self.scopePlotWidget = ScopePlotWidget(self.scopePlotLayout,
                                               max_refresh_rate=max_refresh_rate)
        self.spectrumPlotWidget.on_band_changed = self.on_band_dragged
        self.scopePlotWidget.on_time_selected = self.on_scope_time_selected
        self.scopePlotWidget.on_span_changed = self.on_scope_span_changed
        #: Set while a control and the band region are being kept in step, so
        #: that neither writes back to the other and starts a loop
        self.syncing_band = False
        # The panes the checkboxes control start where the checkboxes do, and
        # load_settings() has the last word on both once it has run
        self.scopePlotLayout.setVisible(False)
        self.scopePlotWidget.set_hidden(True)

        # Keep the waterfall's frequency axis on the spectrum's. The spectrum
        # is the one that is always on screen and the one with real data to
        # scale to, so it leads: linked the other way round, a waterfall that
        # is switched off stops redrawing and freezes the spectrum's axis on
        # whatever range it was showing when it went.
        self.waterfallPlotWidget.plot.setXLink(self.spectrumPlotWidget.plot)

        # Setup power thread and connect signals
        self.update_status_timer = QtCore.QTimer()
        self.update_status_timer.timeout.connect(self.update_status)
        self.update_status_timer.timeout.connect(self.drain_fast_band)
        self.prev_data_timestamp = None
        self.start_timestamp = None
        #: Sweeps counted since the rate was last worked out, and when that was
        self.sweep_count = 0
        self.rate_timestamp = None
        self.sweep_rate = 0.0
        self.data_storage = None
        self.power_thread = None
        self.backend = None
        self.active_backend = None
        self.setup_power_thread()

        # Sweep number currently shown while browsing recorded sweeps
        # (HistoryBuffer.counter of that sweep), or None while live
        self.browse_counter = None

        # What the display has had to give up to keep the backend fed
        self.refresh_rate = None
        self.dropped_seen = 0
        self.dropped_at = None
        self.warned_about_drops = False

        self.populate_presets()
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
        self.data_storage.history_updated.connect(self.update_scope)
        self.data_storage.history_recalculated.connect(self.scopePlotWidget.recalculate_plot)
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

        self.create_power_thread(backend_module, backend)

    def create_power_thread(self, backend_module, name):
        """Build the power thread for one backend and wire up its signals

        Deliberately separate from setup_power_thread(), which also pushes that
        backend's defaults into the spin boxes. Switching automatically must not
        do that: it would throw away the frequency range being asked for."""
        if self.power_thread and self.power_thread.alive:
            self.stop()

        self.power_thread = backend_module.PowerThread(self.data_storage)
        self.power_thread.substituted = name != QtCore.QSettings().value("backend", "soapy_power")
        self.power_thread.powerThreadStarted.connect(self.on_power_thread_started)
        self.power_thread.powerThreadStopped.connect(self.on_power_thread_stopped)
        self.active_backend = name

    def resolve_backend(self):
        """The backend that can actually measure what the spin boxes ask for

        Returns (module, name). A backend that cannot cover the requested range
        names a fallback; this follows that chain rather than assuming who it
        points at."""
        settings = QtCore.QSettings()
        name = settings.value("backend", "soapy_power")
        sample_rate = settings.value("sample_rate", 2560000, float)
        start_freq = float(self.startFreqSpinBox.value())
        stop_freq = float(self.stopFreqSpinBox.value())

        seen = set()
        while name and name not in seen:
            seen.add(name)
            module = getattr(backends, name, None)
            if module is None:
                break
            if module.Info.covers(start_freq, stop_freq, sample_rate):
                return module, name
            name = module.Info.fallback

        # Nothing covers it; keep what was chosen and let the backend cope
        chosen = settings.value("backend", "soapy_power")
        return getattr(backends, chosen, backends.soapy_power), chosen

    def apply_backend_for_range(self):
        """Swap the power thread if the requested range needs a different backend"""
        module, name = self.resolve_backend()
        if name == self.active_backend:
            return

        selected = QtCore.QSettings().value("backend", "soapy_power")
        print('{} cannot cover {:g}-{:g} MHz in one tune, handing over to {}'.format(
            selected, self.startFreqSpinBox.value(), self.stopFreqSpinBox.value(), name))
        self.create_power_thread(module, name)

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
        self.show_scope_cursor()
        self.update_history_controls()

    def update_scope(self, data_storage):
        """Queue a redraw of the power over time plot, if it is showing"""
        if not self.scopePlotLayout.isVisible():
            return
        if self.scopeBandCheckBox.isChecked():
            self.keep_band_in_span()
        self.scopePlotWidget.throttle.schedule("plot", data_storage)

    def keep_band_in_span(self):
        """Move the band back into view if the frequency range left it behind

        The band can be chosen before the first sweep has arrived, and is then
        placed from the spin boxes; the range actually measured can turn out to
        be somewhere else. Only a band with nothing on screen at all is moved,
        so this never takes one back off the user."""
        low, high = self.spectrumPlotWidget.band()
        first, last = self.display_span()
        if low < last and high > first:
            return

        self.spectrumPlotWidget.show_band(True, (first, last))
        self.apply_scope_band()

    def on_band_dragged(self, low, high):
        """The band was dragged on the spectrum plot"""
        self.show_band_in_controls()
        self.apply_scope_band()

    def show_band_in_controls(self):
        """Put the band the region marks into the centre and width boxes"""
        low, high = self.spectrumPlotWidget.band()
        self.syncing_band = True
        self.scopeCentreSpinBox.setValue((low + high) / 2 / 1e6)
        self.scopeWidthSpinBox.setValue((high - low) / 1e3)
        self.syncing_band = False

    def set_band_from_controls(self):
        """Move the band region to what the centre and width boxes say"""
        if self.syncing_band:
            return
        centre = self.scopeCentreSpinBox.value() * 1e6
        half = self.scopeWidthSpinBox.value() * 1e3 / 2
        self.spectrumPlotWidget.set_band(centre - half, centre + half)
        self.apply_scope_band()

    @QtCore.Slot(float)
    def on_scopeCentreSpinBox_valueChanged(self, value):
        self.set_band_from_controls()

    @QtCore.Slot(float)
    def on_scopeWidthSpinBox_valueChanged(self, value):
        self.set_band_from_controls()

    @QtCore.Slot(float)
    def on_scopeSpanSpinBox_valueChanged(self, value):
        """Set how much time the scope shows (zero fits the whole recording)"""
        self.scopePlotWidget.set_time_span(value / 1e3 if value > 0 else None)
        self.scopePlotWidget.redraw_now(self.data_storage)

    def on_scope_span_changed(self, seconds):
        """The scope was zoomed by hand; show the width it ended up with"""
        self.scopeSpanSpinBox.blockSignals(True)
        self.scopeSpanSpinBox.setValue(seconds * 1e3)
        self.scopeSpanSpinBox.blockSignals(False)
        self.scopePlotWidget.time_span = seconds
        self.scopePlotWidget.redraw_now(self.data_storage)

    @QtCore.Slot(bool)
    def on_scopeTriggerCheckBox_toggled(self, checked):
        """Turn the triggered sweep on or off"""
        self.scopeTriggerLabel.setEnabled(checked)
        self.scopeTriggerSpinBox.setEnabled(checked)
        self.scopeSingleCheckBox.setEnabled(checked)
        self.scopeArmButton.setEnabled(checked and self.scopeSingleCheckBox.isChecked())
        if checked and not self.scopeSpanSpinBox.value():
            # A trigger with no sweep length to draw has nothing to do; give
            # it one rather than leaving the control looking broken
            self.scopeSpanSpinBox.setValue(self.DEFAULT_SWEEP_MS)
        self.apply_scope_trigger()
        self.scopePlotWidget.set_single(self.scopeSingleCheckBox.isChecked())

    @QtCore.Slot(float)
    def on_scopeTriggerSpinBox_valueChanged(self, value):
        self.apply_scope_trigger()

    @QtCore.Slot(bool)
    def on_scopeSingleCheckBox_toggled(self, checked):
        """Catch one sweep and hold it, rather than triggering repeatedly"""
        self.scopeArmButton.setEnabled(checked and self.scopeTriggerCheckBox.isChecked())
        self.scopePlotWidget.set_single(checked)
        self.scopePlotWidget.redraw_now(self.data_storage)

    @QtCore.Slot()
    def on_scopeSaveButton_clicked(self):
        """Write the sweep on screen out as CSV"""
        sweep = self.scopePlotWidget.sweep_data()
        if sweep is None:
            self.show_status(self.tr("There is nothing on the scope to save"),
                             timeout=5000)
            return

        suggested = time.strftime("sweep-%Y%m%d-%H%M%S.csv")
        filename = QtWidgets.QFileDialog.getSaveFileName(
            self, self.tr("Save sweep - QSpectrumAnalyzer"), suggested,
            self.tr("Comma separated values (*.csv);;All files (*)"))[0]
        if not filename:
            return

        try:
            rows = self.write_sweep(filename, sweep)
        except OSError as error:
            self.show_status(self.tr("Could not save: {}").format(error), timeout=0)
            return
        self.show_status(self.tr("Saved {} readings to {}").format(
            rows, os.path.basename(filename)), timeout=0)

    def sweep_header(self, sweep):
        """The settings a sweep was taken under, for the top of the file

        Without these the numbers are unreadable a week later: a time axis
        means nothing without knowing what it counts from, and a power means
        nothing without the band it was measured over."""
        settings = QtCore.QSettings()
        step = settings.value("tap_resolution", 0, float)
        band = sweep["band"]

        lines = ["QSpectrumAnalyzer scope sweep",
                 "saved " + time.strftime("%Y-%m-%dT%H:%M:%S%z")]
        if sweep["started"] is not None:
            # Carried by hand, because a fraction that rounds up to a whole
            # second would otherwise print as .1000000 past the second before
            whole = int(sweep["started"])
            micros = int(round((sweep["started"] - whole) * 1e6))
            if micros >= 1000000:
                whole, micros = whole + 1, micros - 1000000
            lines.append("t=0 is {}.{:06d} UTC{}".format(
                time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(whole)), micros,
                " (the trigger)" if sweep["trigger"] is not None else ""))
        lines.append("backend {}, tune {:g}-{:g} MHz, bin size {:g} kHz, gain {:g} dB".format(
            self.active_backend, self.startFreqSpinBox.value(),
            self.stopFreqSpinBox.value(), self.binSizeSpinBox.value(),
            self.gainSpinBox.value()))
        lines.append("band {}".format(
            "{:.6f}-{:.6f} MHz".format(band[0] / 1e6, band[1] / 1e6)
            if band else "the whole tune"))
        lines.append("sweep span {}".format(
            "{:g} ms".format(sweep["span"] * 1e3) if sweep["span"]
            else "the whole recording"))
        if self.scopeFastCheckBox.isChecked():
            lines.append("zero span step {}, {} detector".format(
                "{:g} us".format(step) if step else "finest",
                settings.value("tap_detector", "peak")))
        if sweep["trigger"] is not None:
            lines.append("trigger on a rising edge at {}{}".format(
                "{:.1f} dB".format(sweep["level"]) if sweep["level"] is not None
                else "a level it never reached",
                ", held as a single sweep" if sweep["held"] else ""))
        lines.append("time_s counts from t=0; source 'sweep' is the delivered "
                     "sweeps, 'tap' the high rate readings")
        return lines

    def write_sweep(self, filename, sweep):
        """Write a sweep out, and return how many readings that was"""
        written = 0
        with open(filename, "w", newline="") as handle:
            for line in self.sweep_header(sweep):
                handle.write("# {}\n".format(line))
            out = csv.writer(handle)
            out.writerow(("time_s", "power_db", "source"))
            for name, x, y in sweep["traces"]:
                # writerows over a generator, because the whole recording view
                # can hand over a million readings and a Python loop per row
                # would take longer than the capture did
                out.writerows(("{:.9f}".format(t), "{:.4f}".format(p), name)
                              for t, p in zip(x.tolist(), y.tolist()))
                written += len(x)
        return written

    @QtCore.Slot()
    def on_scopeArmButton_clicked(self):
        """Let go of the held sweep and wait for the next burst"""
        self.scopePlotWidget.arm()
        self.scopePlotWidget.redraw_now(self.data_storage)

    def apply_scope_trigger(self):
        """Tell the scope what to start its sweeps on"""
        if not self.scopeTriggerCheckBox.isChecked():
            self.scopePlotWidget.set_trigger(None)
            self.scopePlotWidget.redraw_now(self.data_storage)
            return
        level = self.scopeTriggerSpinBox.value()
        # The bottom of the range means "work it out from the trace"
        self.scopePlotWidget.set_trigger(
            "auto" if level <= self.scopeTriggerSpinBox.minimum() else level)
        self.scopePlotWidget.redraw_now(self.data_storage)

    @QtCore.Slot(bool)
    def on_scopeFastCheckBox_toggled(self, checked):
        """Turn the backend's high rate band tap on or off"""
        if not checked:
            self.scopePlotWidget.clear_fast()
        self.apply_scope_band()

    def apply_scope_band(self):
        """Point the scope, and any high rate tap, at the chosen frequencies

        With no band placed the scope reduces every bin, so the trace is the
        whole spectrum over time; with one placed it covers only that stretch.
        The high rate tap is pointed at the same frequencies either way, so
        that the two traces are always measuring the same thing."""
        band = (self.spectrumPlotWidget.band()
                if self.scopeBandCheckBox.isChecked() else None)
        self.scopePlotWidget.set_band(band)

        # The high rate samples are measured for whichever band was selected
        # at the time, so they cannot follow it backwards the way the trace
        # reduced from the recording can. Only asked for while the scope is
        # showing and the tap is on: a tap nobody reads is samples gathered
        # and thrown away.
        set_band = getattr(self.power_thread, "set_band", None)
        if set_band is not None:
            if self.scopeCheckBox.isChecked() and self.scopeFastCheckBox.isChecked():
                settings = QtCore.QSettings()
                step = settings.value("tap_resolution", 0, float)
                set_band(*(band if band is not None else self.display_span()),
                         resolution=(step / 1e6) if step > 0 else None,
                         detector=settings.value("tap_detector", "peak"))
            else:
                set_band(None, None)

        self.scopePlotWidget.throttle.schedule("plot", self.data_storage)

    def on_scope_time_selected(self, index):
        """A time was picked on the scope; browse the sweep recorded then"""
        oldest, newest = self.history_range()
        if newest is None:
            return
        if self.browse_counter is None:
            self.browseHistoryCheckBox.setChecked(True)
            if self.browse_counter is None:
                return
        self.browse_counter = min(max(oldest + index, oldest), newest)
        self.show_browsed_sweep()

    def show_scope_cursor(self):
        """Put the scope's cursor on the sweep being browsed"""
        oldest, newest = self.history_range()
        if self.browse_counter is None or newest is None:
            self.scopePlotWidget.show_cursor(None)
        else:
            self.scopePlotWidget.show_cursor(self.browse_counter - oldest)
        # Browsing moves what the sweep is drawn about, so redraw it now
        # rather than leaving the pane a step behind the controls
        self.scopePlotWidget.redraw_now(self.data_storage)

    def drain_fast_band(self):
        """Take whatever high rate band samples the backend has gathered

        Drained rather than pushed: at a reading every 25 us, a signal per
        sample would be more traffic than the samples are worth."""
        if not self.scopePlotLayout.isVisible():
            return
        take = getattr(self.power_thread, "take_band_power", None)
        if take is None:
            return
        samples = take()
        if samples is not None:
            self.scopePlotWidget.add_fast_samples(samples)
            self.scopePlotWidget.throttle.schedule("plot", self.data_storage)

    def display_span(self):
        """The frequency span on screen, in Hz

        From the recorded axis when there is one, and from the spin boxes
        before anything has been measured, so that the band selector can be
        placed before the first sweep arrives."""
        x = self.data_storage.x
        if x is not None and len(x):
            return float(x[0]), float(x[-1])
        return (float(self.startFreqSpinBox.value()) * 1e6,
                float(self.stopFreqSpinBox.value()) * 1e6)

    # --- which plots are on screen ------------------------------------

    @QtCore.Slot(bool)
    def on_waterfallCheckBox_toggled(self, checked):
        """Show or hide the waterfall"""
        self.show_pane(self.waterfallPlotLayout, checked)
        self.waterfallPlotWidget.set_hidden(not checked)
        self.apply_levels_dock()
        if checked:
            # It was still fed while it was away, but nothing was painted, so
            # what it holds is however far behind it was when it went
            self.waterfallPlotWidget.update_plot(self.data_storage)

    @QtCore.Slot(bool)
    def on_scopeCheckBox_toggled(self, checked):
        """Show or hide the power over time plot"""
        self.show_pane(self.scopePlotLayout, checked)
        self.scopePlotWidget.set_hidden(not checked)
        self.scopeGroupBox.setEnabled(checked)
        self.scopeFastCheckBox.setEnabled(checked and self.backend_has_tap())
        self.apply_band_region()
        self.apply_scope_band()

    @QtCore.Slot(bool)
    def on_scopeBandCheckBox_toggled(self, checked):
        """Narrow the scope to one band, or hand it back the whole spectrum"""
        self.apply_band_region()
        self.apply_scope_band()

    def apply_band_region(self):
        """Show the band selector only when there is a scope to steer with it"""
        on = self.scopeBandCheckBox.isChecked()
        self.spectrumPlotWidget.show_band(
            self.scopeCheckBox.isChecked() and on, self.display_span())
        for widget in (self.scopeCentreLabel, self.scopeCentreSpinBox,
                       self.scopeWidthLabel, self.scopeWidthSpinBox):
            widget.setEnabled(on)
        self.show_band_in_controls()

    def backend_has_tap(self):
        """Whether the backend in use can measure a band off its own frames"""
        return getattr(self.power_thread, "set_band", None) is not None

    def show_pane(self, pane, visible):
        """Show or hide one pane of the plot splitter, remembering its height"""
        index = self.plotSplitter.indexOf(pane)
        height = self.plotSplitter.sizes()[index]
        if height:
            self.pane_heights[index] = height
        pane.setVisible(visible)
        if visible:
            self.share_out_panes()

    def share_out_panes(self):
        """Give every plot pane that is on screen some height to be on it with

        Qt leaves a pane that has been hidden with a height of zero, and the
        saved splitter state stores that zero, so switching one back on
        appears to do nothing at all. Hand back the height it had, or a
        quarter of the tallest pane if it has never had one."""
        splitter = self.plotSplitter
        sizes = splitter.sizes()
        changed = False
        for index, size in enumerate(sizes):
            if size or not splitter.widget(index).isVisible():
                continue
            donor = max(range(len(sizes)), key=sizes.__getitem__)
            # Never more than half of what it comes out of: a pane being given
            # its room back must not squeeze the one above it off the screen
            share = min(self.pane_heights.get(index, sizes[donor] // 4),
                        sizes[donor] // 2)
            if share < 1:
                # Nothing laid out yet to take a share of; the pass after the
                # window is shown will have real heights to work with
                continue
            sizes[donor] -= share
            sizes[index] = share
            changed = True
        if changed:
            splitter.setSizes(sizes)

    def apply_levels_dock(self):
        """The waterfall's level meter belongs on screen only with the waterfall"""
        self.levelsDockWidget.setVisible(
            self.waterfallCheckBox.isChecked()
            and bool(QtCore.QSettings().value("levels_meter", 1, int)))

    def apply_plot_visibility(self):
        """Put the panes where the checkboxes say

        Run once the saved window state has been restored, because that state
        carries the levels dock's own visibility and can disagree with a
        waterfall that was switched off when the window was last closed."""
        self.on_waterfallCheckBox_toggled(self.waterfallCheckBox.isChecked())
        self.on_scopeCheckBox_toggled(self.scopeCheckBox.isChecked())
        self.scopePlotWidget.set_time_span(
            self.scopeSpanSpinBox.value() / 1e3 if self.scopeSpanSpinBox.value() else None)
        self.apply_scope_trigger()
        self.scopePlotWidget.set_single(self.scopeSingleCheckBox.isChecked())

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
        # The scope keeps running while browsing: it is what the browsing is
        # being steered by, so freezing it would defeat the point
        if not browsing:
            self.scopePlotWidget.show_cursor(None)

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
        self.waterfallCheckBox.setChecked(settings.value("waterfall", 1, int))
        self.scopeCheckBox.setChecked(settings.value("scope", 0, int))
        self.scopeBandCheckBox.setChecked(settings.value("scope_band", 0, int))
        self.scopeFastCheckBox.setChecked(settings.value("scope_fast", 0, int))
        self.scopeSpanSpinBox.setValue(settings.value("scope_span", 0.0, float))
        self.scopeCentreSpinBox.setValue(settings.value("scope_centre", 0.0, float))
        self.scopeWidthSpinBox.setValue(settings.value("scope_width", 400.0, float))
        self.scopeTriggerCheckBox.setChecked(settings.value("scope_trigger", 0, int))
        self.scopeTriggerSpinBox.setValue(settings.value("scope_trigger_level", -200.0, float))
        self.scopeSingleCheckBox.setChecked(settings.value("scope_single", 0, int))

        # Restore window state
        if settings.value("window_state"):
            self.restoreState(settings.value("window_state"))
        if settings.value("plotsplitter_state"):
            self.plotSplitter.restoreState(settings.value("plotsplitter_state"))
        self.apply_plot_visibility()

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

        # Only now does the splitter have real heights to share out
        QtCore.QTimer.singleShot(0, self.share_out_panes)

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
        settings.setValue("waterfall", int(self.waterfallCheckBox.isChecked()))
        settings.setValue("scope", int(self.scopeCheckBox.isChecked()))
        settings.setValue("scope_band", int(self.scopeBandCheckBox.isChecked()))
        settings.setValue("scope_fast", int(self.scopeFastCheckBox.isChecked()))
        settings.setValue("scope_span", self.scopeSpanSpinBox.value())
        settings.setValue("scope_centre", self.scopeCentreSpinBox.value())
        settings.setValue("scope_width", self.scopeWidthSpinBox.value())
        settings.setValue("scope_trigger", int(self.scopeTriggerCheckBox.isChecked()))
        settings.setValue("scope_trigger_level", self.scopeTriggerSpinBox.value())
        settings.setValue("scope_single", int(self.scopeSingleCheckBox.isChecked()))

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

        Only the arrival is recorded here. Working out the rate, and redrawing
        the status bar and the history controls, is left to
        update_status_timer, because at a few hundred sweeps a second there is
        no point rewriting them per sweep."""
        self.prev_data_timestamp = time.time()
        self.sweep_count += 1

    def update_sweep_rate(self):
        """Work out the sweep rate, once enough time has passed to mean anything

        Sweeps are counted over a window rather than taken from the gap
        between the last two. That gap is a single sample of a quantity that
        jitters, and it is timed when the GUI thread reaches the queued signal
        rather than when the sweep arrived, so a busy moment delivers several
        at once and then nothing. Reading 1/gap on top of that also comes out
        high, because the short gaps within a burst outnumber the long one
        that follows it: a steady 100 sweeps/s used to show as anything from
        50 to 270."""
        now = time.monotonic()
        if self.rate_timestamp is None:
            # Opening the first window. Anything already counted arrived before
            # it began, so it would be a count without a time to divide it by
            self.rate_timestamp = now
            self.sweep_count = 0
            return

        elapsed = now - self.rate_timestamp
        if elapsed < self.RATE_WINDOW:
            return
        if not self.sweep_count and elapsed < self.RATE_STALE:
            # A backend sweeping once a second has not necessarily finished
            # one yet; wait for it rather than reporting a rate of zero
            return

        self.sweep_rate = self.sweep_count / elapsed
        self.sweep_count = 0
        self.rate_timestamp = now

    # --- ready-made settings for a particular job ---------------------

    def populate_presets(self):
        """Offer the jobs, without applying one"""
        self.presetComboBox.blockSignals(True)
        for label, note, _widgets, _settings in RADAR_PRESETS:
            self.presetComboBox.addItem(label)
            if note:
                self.presetComboBox.setItemData(
                    self.presetComboBox.count() - 1, note, QtCore.Qt.ToolTipRole)
        self.presetComboBox.setCurrentIndex(0)
        self.presetComboBox.blockSignals(False)

    @QtCore.Slot(int)
    def on_presetComboBox_currentIndexChanged(self, index):
        """Set every control at once for the chosen job"""
        if not 0 < index < len(RADAR_PRESETS):
            return
        label, note, widgets, values = RADAR_PRESETS[index]

        settings = QtCore.QSettings()
        deepened = ("record_depth" in values
                    and values["record_depth"] != settings.value("record_depth", 1000, int))
        for key, value in values.items():
            settings.setValue(key, value)

        for name, value in widgets.items():
            widget = getattr(self, name)
            if isinstance(widget, QtWidgets.QCheckBox):
                widget.setChecked(bool(value))
            else:
                widget.setValue(value)

        print("{}\n  {}".format(label, note))
        if deepened:
            # The recording is allocated when the run starts, so a new depth
            # needs the data storage built again
            self.setup_power_thread()
            print("  Recording deepened, so acquisition has been reset - press Start.")
        self.apply_scope_band()
        self.apply_scope_trigger()
        self.show_status(self.tr("{} - press Start").format(label), timeout=0)

    def configured_refresh_rate(self):
        """The redraw rate the settings ask for"""
        return QtCore.QSettings().value("max_refresh_rate", 60, int)

    def set_refresh_rate(self, rate):
        """Redraw every plot at this rate"""
        self.refresh_rate = rate
        for widget in (self.spectrumPlotWidget, self.waterfallPlotWidget,
                       self.scopePlotWidget):
            widget.set_max_refresh_rate(rate)

    def adapt_refresh_rate(self):
        """Give frames back to the backend when it is losing samples

        Drawing and demodulating share one interpreter lock, so a display
        redrawing as fast as it can can starve a backend that has to keep up
        with a radio in real time. The two are not worth the same: a frame
        that is never drawn is a frame nobody was going to see anyway, while a
        sample that arrived with nowhere to put it is gone for good. So when
        the backend reports drops the display stands down, halving its rate
        until they stop, and creeps back up once they have."""
        dropped = getattr(self.power_thread, "dropped", 0)
        if self.refresh_rate is None:
            self.set_refresh_rate(self.configured_refresh_rate())

        ceiling = self.configured_refresh_rate()
        if ceiling <= 0:
            # No limit asked for; there is nothing to step down from
            return

        now = time.monotonic()
        if dropped > self.dropped_seen:
            self.dropped_seen = dropped
            self.dropped_at = now
            if self.refresh_rate > self.REFRESH_FLOOR:
                self.set_refresh_rate(max(self.REFRESH_FLOOR, self.refresh_rate // 2))
                if not self.warned_about_drops:
                    self.warned_about_drops = True
                    print("Redrawing at {} Hz instead of {}: the backend was losing "
                          "samples while the display held the interpreter lock."
                          .format(self.refresh_rate, ceiling))
            return

        if (self.dropped_at is not None and self.refresh_rate < ceiling
                and now - self.dropped_at > self.REFRESH_RECOVER):
            # Clean for a while, so try a little more drawing again
            self.dropped_at = now
            self.set_refresh_rate(min(ceiling, max(self.refresh_rate + 1,
                                                   int(self.refresh_rate * 1.5))))

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
        self.update_sweep_rate()
        self.adapt_refresh_rate()

        selected = QtCore.QSettings().value("backend", "soapy_power")
        if self.active_backend and self.active_backend != selected:
            status.append(self.tr("via {}").format(self.active_backend))

        if self.power_thread.params["hops"]:
            status.append(self.tr("Frequency hops: {}").format(self.power_thread.params["hops"]))

        status.append(self.tr("Total time: {} | Sweep time: {:.3f} s ({:.1f} sweeps/s)").format(
            human_time(timestamp - self.start_timestamp),
            (1 / self.sweep_rate) if self.sweep_rate else 0,
            self.sweep_rate
        ))

        slower = self.slower_than_fastest()
        if slower:
            status.append(self.tr("{} option(s) slower than fastest").format(len(slower)))

        if self.refresh_rate is not None and self.refresh_rate < self.configured_refresh_rate():
            status.append(self.tr("redrawing at {} Hz to keep the backend fed")
                          .format(self.refresh_rate))

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

        # The frequency range is only settled now, so this is the first point
        # at which we can tell whether the chosen backend can measure it
        self.apply_backend_for_range()

        self.prev_data_timestamp = time.time()
        self.start_timestamp = self.prev_data_timestamp
        self.sweep_count = 0
        self.rate_timestamp = None
        self.sweep_rate = 0.0

        if self.intervalSpinBox.value() >= 1:
            self.progressbar.setRange(0, int(self.intervalSpinBox.value() * 1000))
        else:
            self.progressbar.setRange(0, 0)
        self.update_progress(0)
        self.update_status_timer.start(100)
        # A new run starts from the rate that was asked for, not from whatever
        # the last one had to stand down to
        self.dropped_seen = 0
        self.dropped_at = None
        self.warned_about_drops = False
        self.set_refresh_rate(self.configured_refresh_rate())
        self.scopePlotWidget.clear_plot()

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

        starting = not self.power_thread.alive
        if starting:
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

        # After setup(), which clears whatever band the backend was watching.
        # Asked for before it, the high rate tap is switched straight back off
        # and never starts, which leaves the scope drawing only the delivered
        # sweeps — one point every 10 ms, which in a 10 ms window is a straight
        # line. The thread has not begun yet, so nothing else is touching it.
        self.apply_scope_band()

        if starting:
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
            self.waterfallPlotWidget.set_levels_meter(
                bool(settings.value("levels_meter", 1, int)))
            self.apply_levels_dock()
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

    # Hand the interpreter lock round more often than the default 5 ms. A
    # backend that transforms samples on its own thread needs the lock in
    # short bursts and needs them on time; the drawing wants it in long ones.
    # At the default a redraw can hold it for a whole slice while the radio
    # fills the buffer that has nowhere to go, and the samples in it are lost
    # for good. Rotating faster costs a little switching overhead and buys
    # back the thing that cannot be recovered.
    sys.setswitchinterval(0.001)

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
