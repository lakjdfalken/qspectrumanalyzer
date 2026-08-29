import argparse
import shlex
import time

import numpy as np
from PySide6 import QtCore

from qspectrumanalyzer.backends import BaseInfo, BasePowerThread

try:
    import hackrf_stream
except ImportError:
    hackrf_stream = None
    print('hackrf_stream module not found!')


class Info(BaseInfo):
    """hackrf_stream device metadata

    One tune covers one sample rate of spectrum, so the span this backend can
    show is limited to the sample rate — 20 MHz at most. Wider than that needs
    retuning, which is what the hackrf_sweep backend is for."""
    sample_rate_min = 2000000
    sample_rate_max = 20000000
    sample_rate = 20000000
    bandwidth_min = 0
    bandwidth_max = 0
    bandwidth = 0
    gain_min = -1
    gain_max = 102
    gain = 40
    start_freq_min = 0
    start_freq_max = 7250
    start_freq = 118
    stop_freq_min = 0
    stop_freq_max = 7250
    stop_freq = 138
    bin_size_min = 0
    bin_size_max = 5000
    bin_size = 40
    interval_min = 0
    interval_max = 3600
    interval = 0
    ppm_min = 0
    ppm_max = 0
    ppm = 0
    crop_min = 0
    crop_max = 0
    crop = 0
    additional_params = '--average 26 --max-rate 100'

    #: One tune cannot be widened, so anything wider goes to the sweeping backend
    fallback = 'hackrf_sweep'

    @classmethod
    def covers(cls, start_freq, stop_freq, sample_rate):
        """True while the requested span fits inside a single tune"""
        sample_rate = min(max(sample_rate, cls.sample_rate_min), cls.sample_rate_max)
        return (stop_freq - start_freq) * 1e6 <= sample_rate

    @classmethod
    def help_params(cls, executable):
        if hackrf_stream is None:
            return 'hackrf_stream module not found!'
        return (
            'hackrf_stream {}, libhackrf {}\n\n'
            'There is no executable: this backend drives the radio in process\n'
            'through libhackrf, so the executable field is ignored.\n\n'
            'It holds one frequency instead of sweeping, which removes the\n'
            'retune that limits hackrf_sweep to about 405 sweeps per second.\n'
            'In exchange the span cannot exceed the sample rate, so 20 MHz at\n'
            'most. A wider range is handed to the hackrf_sweep backend\n'
            'automatically; the status bar says so when that happens.\n\n'
            'Parameters:\n\n'
            '  --average N    FFTs averaged into each spectrum (default 26).\n'
            '                 Every sample is used whatever this is, so a\n'
            '                 larger number is a quieter noise floor rather\n'
            '                 than discarded data. 26 gives about 1500\n'
            '                 spectra/s at 20 MSPS with 512 bins.\n\n'
            '  --max-rate N   Spectra per second handed to the display\n'
            '                 (default 100). Spectra are produced far faster\n'
            '                 than anything can look at, and delivering all of\n'
            '                 them costs enough time that the radio starts\n'
            '                 dropping samples.\n\n'
            '  --dc-bins N    Bins interpolated across the centre of the band\n'
            '                 (default 2), where the receiver\'s own DC offset\n'
            '                 sits. 0 leaves it visible.\n\n'
            '  --window NAME  hann (default), hamming, blackman, bartlett or\n'
            '                 boxcar.\n'
        ).format(hackrf_stream.__version__, hackrf_stream.library_version())


def parse_params(text):
    """Read the backend's additional parameters

    argparse rather than hand-rolled splitting, so a typo is reported instead
    of quietly ignored; anything unparseable falls back to the defaults."""
    parser = argparse.ArgumentParser(prog='hackrf_stream', add_help=False)
    parser.add_argument('--average', type=int, default=26)
    parser.add_argument('--max-rate', dest='max_rate', type=int, default=100)
    parser.add_argument('--dc-bins', dest='dc_bins', type=int, default=2)
    parser.add_argument('--window', default='hann')

    try:
        options, unknown = parser.parse_known_args(shlex.split(text or ''))
    except (SystemExit, ValueError):
        print('hackrf_stream: could not read parameters {!r}, using defaults'.format(text))
        return parser.parse_args([])

    if unknown:
        print('hackrf_stream: ignoring unknown parameters {}'.format(' '.join(unknown)))

    options.average = max(1, options.average)
    options.max_rate = max(1, options.max_rate)
    options.dc_bins = max(0, options.dc_bins)
    return options


class PowerThread(BasePowerThread):
    """Thread which receives spectra from a HackRF held on one frequency"""

    def setup(self, start_freq, stop_freq, bin_size, interval=0.0, gain=-1, ppm=0, crop=0,
              single_shot=False, device="", sample_rate=20000000, bandwidth=0, lnb_lo=0):
        """Setup hackrf_stream params"""
        sample_rate = min(max(float(sample_rate), Info.sample_rate_min), Info.sample_rate_max)

        center_freq = (start_freq + stop_freq) / 2 * 1e6 - lnb_lo

        self.params = {
            "start_freq": start_freq,
            "stop_freq": stop_freq,
            "center_freq": center_freq,
            "hops": 0,
            "device": device,
            "sample_rate": sample_rate,
            "bandwidth": bandwidth,
            "bin_size": bin_size,
            "interval": interval,
            "gain": gain,
            "ppm": 0,
            "crop": 0,
            "single_shot": single_shot,
        }
        self.lnb_lo = lnb_lo
        self.interval = interval
        self.last_spectrum = 0.0
        self.databuffer = {"timestamp": [], "x": [], "y": []}

        self.source = None
        self.x = None
        self.crop_mask = None
        self.latest = None
        self.delivered = 0

    def prepare_axis(self):
        """Work out which bins to keep, and their frequencies once the LNB is added"""
        frequencies = self.source.frequencies + self.lnb_lo
        low = self.params["start_freq"] * 1e6
        high = self.params["stop_freq"] * 1e6

        mask = (frequencies >= low) & (frequencies <= high)
        if not mask.any():
            # The requested range falls outside what one tune can reach; show
            # the whole tune rather than nothing at all
            mask = np.ones_like(frequencies, dtype=bool)

        self.crop_mask = mask
        self.x = frequencies[mask]

    def on_spectrum(self, frequencies, powers_db, timestamp):
        """Called by hackrf_stream for each completed average

        Runs on libhackrf's receive thread, which must not be held up: while
        this is inside DataStorage the radio has nowhere to put samples and
        starts dropping them. So it only hands the spectrum over, and the
        thread's own loop does the delivering."""
        self.latest = (timestamp, powers_db)

    def process_start(self):
        """Open the radio and start receiving"""
        if self.source is not None or not self.params:
            return

        settings = QtCore.QSettings()
        options = parse_params(self.additional_params(Info))

        # Spectra are produced far faster than anything can look at them, and
        # far faster than DataStorage can absorb them. Deliver at a bounded
        # rate; the ones in between are not wasted, since every sample still
        # went through the averaging that produced them.
        self.delivery_interval = max(self.interval, 1.0 / options.max_rate)

        self.source = hackrf_stream.SpectrumSource(
            center_freq=self.params["center_freq"],
            sample_rate=self.params["sample_rate"],
            bin_size=self.params["bin_size"] * 1e3,
            average=options.average,
            gain=self.params["gain"],
            window=options.window,
            dc_bins=options.dc_bins,
            serial=self.params["device"] or None,
        )
        self.source.open()
        self.prepare_axis()

        print('Starting hackrf_stream backend:')
        print('  {:.3f} MHz centre, {:.1f} MHz sample rate, {} bins of {:.2f} kHz, '
              'averaging {}, up to {} spectra/s to the display'
              .format(self.params["center_freq"] / 1e6, self.params["sample_rate"] / 1e6,
                      len(self.x), self.source.bin_size / 1e3,
                      options.average, options.max_rate))
        print()
        self.source.start(self.on_spectrum)

    def deliver(self):
        """Pass the newest spectrum on, no faster than the delivery rate"""
        latest = self.latest
        if latest is None:
            return

        now = time.monotonic()
        if now < self.last_spectrum + self.delivery_interval:
            return
        self.last_spectrum = now
        self.latest = None

        timestamp, powers_db = latest
        self.databuffer = {
            "timestamp": timestamp,
            "x": self.x,
            "y": powers_db[self.crop_mask],
        }
        self.data_storage.update(self.databuffer)
        self.delivered += 1

        if self.params["single_shot"]:
            self.alive = False

    def process_stop(self):
        """Stop receiving and release the radio"""
        with self._shutdown_lock:
            if self.source is not None:
                self.source.close()
                self.source = None

    def run(self):
        """hackrf_stream thread main loop

        There is no output to parse: libhackrf delivers samples on its own
        thread and on_spectrum() forwards them, so this only has to keep the
        radio open until it is asked to stop."""
        if hackrf_stream is None:
            return

        try:
            self.process_start()
        except Exception as error:          # noqa: BLE001 - report, do not crash the GUI
            print('hackrf_stream failed to start: {}'.format(error))
            self.process_stop()
            self.powerThreadStopped.emit()
            return

        self.alive = True
        self.powerThreadStarted.emit()

        while self.alive:
            self.deliver()
            if self.source is not None and self.source.error is not None:
                print('hackrf_stream stopped: {}'.format(self.source.error))
                break
            self.msleep(2)

        self.process_stop()
        self.alive = False
        self.powerThreadStopped.emit()
