import argparse
import shlex
import time

import numpy as np
from PySide6 import QtCore

from qspectrumanalyzer.backends import BaseInfo, BasePowerThread

#: Readings the scope's fast buffer holds, so a zero span step can be checked
#: against how far back it will actually reach. Deliberately a copy of
#: ScopePlotWidget.FAST_CAPACITY rather than an import of it: every module
#: that owns the number pulls in QtGui, and a backend that imports the widget
#: stack cannot be run headless. If one moves, move the other.
TAP_CAPACITY = 1000000

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
    additional_params = '--average auto --max-rate 100'

    #: One tune cannot be widened, so anything wider goes to the sweeping backend
    fallback = 'hackrf_sweep'

    @classmethod
    def list_devices(cls):
        """Attached HackRFs, by serial number"""
        return list_hackrfs()

    @classmethod
    def stage_gains(cls, gain=-1, lna=None, vga=None):
        """The LNA and VGA the radio would actually be set to"""
        if hackrf_stream is None:
            return None
        return hackrf_stream.stage_gains(gain, lna, vga)

    @classmethod
    def help_device(cls, executable, device):
        """What the Device field can be set to"""
        if hackrf_stream is None:
            return 'hackrf_stream module not found!'
        try:
            found = hackrf_stream.devices()
        except Exception as error:          # noqa: BLE001 - report, do not crash the dialog
            return 'Could not list HackRF devices: {}'.format(error)

        text = ['The Device field takes a HackRF serial number.',
                'Leave it empty to use whichever one is found first.', '']
        if not found:
            text.append('No HackRF is attached (or another program has claimed it).')
        else:
            text.append('Attached now:')
            text.append('')
            for entry in found:
                text.append('  {}  {}'.format(entry['board'],
                                              entry['serial'] or '(serial unreadable)'))
        if device:
            text += ['', 'Currently set to: {}'.format(device)]
            if found and device not in [e['serial'] for e in found]:
                text.append('That serial is not attached; opening it will fail.')
        return '\n'.join(text)

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
            '                 either side (default: what the window needs, 1\n'
            '                 for hann), where the receiver\'s own DC offset\n'
            '                 sits. 0 leaves it visible.\n\n'
            '  --offset-tune  auto (default) tunes off to one side so that the\n'
            '                 span asked for misses the DC spike entirely and\n'
            '                 every bin on screen is measured. It needs half\n'
            '                 the tune to spend, so it happens only for a span\n'
            '                 under half the sample rate; wider spans flatten\n'
            '                 the spike instead. off always centres the span.\n\n'
            '  --window NAME  hann (default), hamming, blackman, bartlett or\n'
            '                 boxcar.\n\n'
            '  --peak         Keep the loudest of the frames making up each\n'
            '                 spectrum instead of averaging them. For a signal\n'
            '                 that is always there, averaging is better: it\n'
            '                 lowers the noise floor. For one that is not — a\n'
            '                 radar pulse, a burst transmission — averaging\n'
            '                 spreads it over the frames it did not occur in\n'
            '                 and buries it. With --peak a long --average\n'
            '                 becomes a wider net to catch a pulse in rather\n'
            '                 than a deeper hole to lose it down, and costs no\n'
            '                 more to deliver.\n\n'
            'The gain stages are not parameters: the LNA and VGA have a box\n'
            'each in the Adjustments panel, beside the total they add up to.\n'
        ).format(hackrf_stream.__version__, hackrf_stream.library_version())


def list_hackrfs():
    """Attached HackRFs as (serial, label) pairs, newest listing each time

    Shared with the hackrf_sweep backend: the two drive the same radios, and
    a serial that works for one works for the other."""
    if hackrf_stream is None:
        return []
    try:
        found = hackrf_stream.devices()
    except Exception as error:              # noqa: BLE001 - an empty list is the answer
        print('hackrf_stream: could not list devices: {}'.format(error))
        return []

    devices = []
    for entry in found:
        serial = entry['serial']
        if not serial:
            # Listed but unreadable, so there is no serial to select it by
            continue
        # The leading zeros carry no information and crowd out the part that
        # tells two boards apart
        devices.append((serial, '{} {}'.format(entry['board'], serial.lstrip('0') or serial)))
    return devices


def parse_params(text):
    """Read the backend's additional parameters

    argparse rather than hand-rolled splitting, so a typo is reported instead
    of quietly ignored; anything unparseable falls back to the defaults."""
    parser = argparse.ArgumentParser(prog='hackrf_stream', add_help=False)
    parser.add_argument('--average', default='auto')
    parser.add_argument('--max-rate', dest='max_rate', type=int, default=100)
    parser.add_argument('--dc-bins', dest='dc_bins', type=int, default=None)
    parser.add_argument('--offset-tune', dest='offset_tune', default='auto',
                        choices=('auto', 'off'))
    parser.add_argument('--window', default='hann')
    parser.add_argument('--peak', action='store_true')

    try:
        options, unknown = parser.parse_known_args(shlex.split(text or ''))
    except (SystemExit, ValueError):
        print('hackrf_stream: could not read parameters {!r}, using defaults'.format(text))
        return parser.parse_args([])

    if unknown:
        print('hackrf_stream: ignoring unknown parameters {}'.format(' '.join(unknown)))

    if str(options.average).strip().lower() in ('auto', ''):
        options.average = None
    else:
        try:
            options.average = max(1, int(options.average))
        except ValueError:
            print('hackrf_stream: --average {!r} is not a number, using auto'
                  .format(options.average))
            options.average = None
    options.max_rate = max(1, options.max_rate)
    if options.dc_bins is not None:
        options.dc_bins = max(0, options.dc_bins)
    return options


class PowerThread(BasePowerThread):
    """Thread which receives spectra from a HackRF held on one frequency"""

    # The band can be chosen before anything has been measured, so these have
    # to exist before setup() has run
    source = None
    amp = False
    lna = None
    vga = None
    band = None
    band_resolution = None
    band_detector = "peak"
    reported_band_error = None
    lnb_lo = 0
    offset_tuned = False

    def setup(self, start_freq, stop_freq, bin_size, interval=0.0, gain=-1, ppm=0, crop=0,
              single_shot=False, device="", sample_rate=20000000, bandwidth=0, lnb_lo=0,
              amp=False, lna=None, vga=None):
        """Setup hackrf_stream params"""
        sample_rate = min(max(float(sample_rate), Info.sample_rate_min), Info.sample_rate_max)

        # Provisional: process_start() may tune off to one side of the span
        # once the bin size is known, to keep the DC spike out of it
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
        # What the two analogue stages will actually be set to. Settled here so
        # that the startup message and the radio cannot disagree.
        self.lna, self.vga = hackrf_stream.stage_gains(gain, lna, vga)
        self.amp = bool(amp)
        self.lnb_lo = lnb_lo
        self.interval = interval
        self.delivery_interval = None
        self.last_spectrum = 0.0
        self.databuffer = {"timestamp": [], "x": [], "y": []}

        self.source = None
        self.x = None
        self.crop_mask = None
        self.dropped_edges = 0
        self.latest = None
        #: Highest each bin has reached since the last take_peak_hold(), over
        #: every spectrum made rather than the few that are delivered
        self.peak_hold = None
        self.peak_spectra = 0
        self.delivered = 0
        self.reported_drops = 0
        self.reported_band_error = None
        self.offset_tuned = False
        self.tune_flipped = False
        #: Band being watched in the time domain, in display frequencies, and
        #: the seconds per reading asked for (None for as fine as it goes)
        self.band = None
        self.band_resolution = None
        self.band_detector = "peak"

    #: How long a finished spectrum should cover when the frame count is left
    #: to work itself out. It is what 26 frames came to at the old default of
    #: 40 kHz bins, so nothing changes there; what changes is the fine bins,
    #: where 26 frames is 42 us and finishes twenty-four thousand spectra a
    #: second for a display that is shown a hundred.
    SPECTRUM_SECONDS = 26 * 512 / 20e6

    def frames_averaged(self, asked, fft_size):
        """How many frames go into one delivered spectrum

        A frame count is the wrong thing to hold constant across bin sizes.
        The FFTs cost the same either way, but finishing a spectrum allocates
        an array, calls back into Python and wakes the delivery loop, and at
        625 kHz bins a count meant for 40 kHz bins does that twenty-four
        thousand times a second so that a hundred can be drawn. Measured: the
        DSP falls from 38.4% of a core to 12.3% for the same FFTs, and the
        radio stops losing blocks to a thread that cannot get the lock.

        Nothing is thrown away by averaging more - every sample is in the
        spectrum either way - and the high rate tap is not affected at all,
        because it reads the frames rather than the finished spectra."""
        if asked is not None:
            return asked
        return max(1, int(round(self.SPECTRUM_SECONDS
                                * self.params["sample_rate"] / fft_size)))

    @property
    def delivery_rate(self):
        """Sweeps a second handed to the display

        Known before the radio is open, because a survey has to size its
        recording from it and that is decided before anything starts."""
        if self.delivery_interval:
            return 1.0 / self.delivery_interval
        return float(parse_params(self.additional_params(Info)).max_rate)

    @staticmethod
    def pulse_cost(frame, bin_hz, tau):
        """Signal to noise given up on a pulse of `tau` at this bin size

        Two losses that pull opposite ways and cross at one over the pulse
        width. A frame longer than the pulse shares its energy with the
        silence either side; a bin wider than the pulse's own bandwidth
        collects noise the pulse was never going to fill."""
        return (10 * np.log10(max(1.0, frame / tau))
                + 10 * np.log10(max(1.0, bin_hz * tau)))

    def check_settings(self, options, average):
        """Settings that quietly undo each other, said out loud before the run

        None of these is an error and none of them stops anything. The run
        succeeds, the trace looks reasonable, and it answers a different
        question than the one that was asked - which is exactly what makes
        them expensive, because a wrong one here looks like an empty band and
        an empty band looks like the same thing."""
        rate = self.params["sample_rate"]
        frame = self.source.fft_size / rate
        bin_hz = rate / self.source.fft_size
        sweep = frame * average
        settings = QtCore.QSettings()
        lines = []

        if self.source.mode != "peak":
            lines.append("the sweep detector averages the {} frames behind one "
                         "sweep, so a pulse shorter than {:.1f} us is spread "
                         "across all of it - 1 us loses {:.1f} dB and no bin "
                         "size wins that back. Peak keeps it at its own "
                         "height.".format(average, sweep * 1e6,
                                          10 * np.log10(sweep / 1e-6)))

        # The same guard choose_tune() uses, so the span it names really is
        # one that offset tuning would take
        guard = max((self.source.dc_bins + 1) * bin_hz, 0.002 * rate)
        half = hackrf_stream.baseband_filter_bw(0.75 * rate) / 2.0
        centre = self.params["center_freq"] + self.lnb_lo
        low, high = self.params["start_freq"] * 1e6, self.params["stop_freq"] * 1e6
        outside = max(0.0, (centre - half) - low) + max(0.0, high - (centre + half))
        if outside > bin_hz:
            lines.append("{:.2f} MHz of the span is outside the {:.1f} MHz "
                         "baseband filter, which passes {:.3f}-{:.3f} MHz of "
                         "this tune. Those bins are the filter's own roll-off "
                         "rather than the air, and they slope away exactly as "
                         "a band going quiet at one end does. A span under "
                         "{:.2f} MHz can be offset-tuned to fit inside it."
                         .format(outside / 1e6, 2 * half / 1e6,
                                 (centre - half) / 1e6, (centre + half) / 1e6,
                                 (half - 2 * guard) / 1e6))

        wanted = settings.value("hunt_pulse_us", 0.0, float) * 1e-6
        if wanted > 0:
            best_n = hackrf_stream.fast_fft_size(rate, 1.0 / wanted)
            here = self.pulse_cost(frame, bin_hz, wanted)
            ideal = self.pulse_cost(best_n / rate, rate / best_n, wanted)
            if here - ideal >= 1.0:
                lines.append("the pulse being hunted is {:g} us, which this "
                             "{:.2f} us frame costs {:.1f} dB. {:.0f} kHz bins "
                             "would cost {:.1f} dB - {:.1f} dB better."
                             .format(wanted * 1e6, frame * 1e6, here,
                                     rate / best_n / 1e3, ideal, here - ideal))
        else:
            micro = self.pulse_cost(frame, bin_hz, 1e-6)
            if micro >= 1.0:
                best_n = hackrf_stream.fast_fft_size(rate, 1e6)
                lines.append("nothing is stated about the pulse being hunted, "
                             "so the bin size cannot be checked against it. For "
                             "scale: a 1 us pulse costs {:.1f} dB at this bin "
                             "size and {:.1f} dB at {:.0f} kHz."
                             .format(micro,
                                     self.pulse_cost(best_n / rate,
                                                     rate / best_n, 1e-6),
                                     rate / best_n / 1e3))

        if self.source.band is not None:
            # None means as fine as it goes, which is one frame a reading -
            # and that is exactly the case this check exists for
            step = self.source.band_resolution or frame
            reach = TAP_CAPACITY * step
            if reach < 4.0:
                lines.append("the zero span buffer holds {:.1f} s at {:.2f} us "
                             "a reading. A rotating antenna comes round every "
                             "several seconds, so it will have been and gone "
                             "before the buffer reaches back to it - a coarser "
                             "step costs a pulse nothing on peak, and 10 us "
                             "would reach {:.0f} s."
                             .format(reach, step * 1e6, TAP_CAPACITY * 10e-6))
        return lines

    def describe_radio(self, options, average):
        """Every setting the measurement depends on, as lines of text

        Written out in full because this program has half a dozen settings
        that decide what a measurement can possibly show, they live in three
        different windows, and each of them fails silently: a detector on
        average cannot see a microsecond pulse at all, a zero span step left
        at the finest reaches back a second where a rotating antenna comes
        round every ten, and the DC spike is flattened across a number of
        *bins*, so widening the bins to catch a short pulse quietly widens the
        hole in the middle of the spectrum with them. Every one of those cost
        an hour before it was noticed. None of them can hide from here."""
        rate = self.params["sample_rate"]
        source = self.source
        span = (self.params["start_freq"], self.params["stop_freq"])
        frame = source.fft_size / rate
        spectrum = frame * average

        lines = ["Starting hackrf_stream backend:"]

        def say(label, text):
            lines.append("  {:<10} {}".format(label, text))

        say("radio", "{}, {:.1f} MHz sample rate{}".format(
            self.params["device"] or "the first HackRF found", rate / 1e6,
            ", baseband filter {:.1f} MHz".format(source.filter_bandwidth / 1e6)
            if source.filter_bandwidth else ""))
        say("tuned to", "{:.3f} MHz, covering {:g}-{:g} MHz{}".format(
            (self.params["center_freq"] + self.lnb_lo) / 1e6, span[0], span[1],
            ", LNB LO {:g} MHz".format(self.lnb_lo / 1e6) if self.lnb_lo else ""))
        if self.offset_tuned:
            say("", "off to one side on purpose, so the DC spike and the IQ "
                    "images fall outside the span and every bin shown is "
                    "measured")
        if self.tune_flipped:
            say("", "and to the other side of the passband from the last look, "
                    "so anything at a fixed offset from the tune has moved out "
                    "of the span - this is the second look of a spur check")

        gain = hackrf_stream.describe_gain(source.lna, source.vga, self.amp)
        say("gain", gain[0])
        for line in gain[1:]:
            say("", line.strip())

        say("bins", "{} of {:.2f} kHz kept from a {}-point FFT, {} window".format(
            len(self.x), source.bin_size / 1e3, source.fft_size, options.window))
        if self.dropped_edges:
            say("", "{} more dropped at the bottom of the tune, where the "
                    "Nyquist bin folds the two ends of the passband together "
                    "and reads high whatever the air is doing".format(
                        self.dropped_edges))
        say("frames", "{:.2f} us each, so a pulse shorter than that is spread "
                      "over one".format(frame * 1e6))
        say("sweeps", "{} {} frames = {:.1f} us each, {:.0f} a second made, "
                      "up to {} delivered".format(
                          "peak of" if source.mode == "peak" else "the average of",
                          average, spectrum * 1e6, 1.0 / spectrum, options.max_rate))
        say("", "peak keeps a pulse shorter than a sweep at its own height"
                if source.mode == "peak" else
                "the average spreads a pulse over the whole sweep: a 1 us one "
                "loses {:.0f} dB here".format(10 * np.log10(spectrum / 1e-6)))

        low_dc, high_dc = self.dc_band
        inside = low_dc < self.params["stop_freq"] * 1e6 and \
            high_dc > self.params["start_freq"] * 1e6
        if not inside:
            say("dc spike", "at {:.3f} MHz, outside the span - nothing on "
                            "screen is interpolated".format(
                                (self.params["center_freq"] + self.lnb_lo) / 1e6))
        elif source.dc_bins > 0:
            flattened = 2 * source.dc_bins + 1
            say("dc spike", "{} bins flattened, {:.3f}-{:.3f} MHz ({:.3f} MHz, "
                            "{:.0f}% of the span) - drawn as a straight line, "
                            "and shaded on the plot to say so".format(
                                flattened, low_dc / 1e6, high_dc / 1e6,
                                (high_dc - low_dc) / 1e6,
                                100 * (high_dc - low_dc)
                                / ((span[1] - span[0]) * 1e6)))
        else:
            say("dc spike", "left alone, so the receiver's own carrier is on "
                            "screen at the centre of the tune")
        if inside:
            say("", "the band tap reads raw bins, so a zero span watch over "
                    "there measures the receiver and not the air")

        if source.band is None:
            say("zero span", "no band being watched, so the scope has only the "
                             "delivered sweeps to draw")
        else:
            low, high = source.band
            step = source.band_resolution
            say("zero span", "{:.3f}-{:.3f} MHz, {:.1f} us a reading ({} frame{}), "
                             "{} detector".format(
                                 (low + self.lnb_lo) / 1e6, (high + self.lnb_lo) / 1e6,
                                 step * 1e6, int(round(step / frame)),
                                 "" if round(step / frame) == 1 else "s",
                                 source.band_detector))
        return lines

    def choose_tune(self, options, fft_size):
        """Settle the centre frequency, offsetting it to dodge the DC spike

        The spike is at the centre of the tune because the centre of the tune
        is zero hertz at baseband. Centring the span on what you want to look
        at therefore puts the one part of the spectrum that is not a
        measurement exactly on it, which is the wrong way round. Tuning off to
        one side instead costs half the tune and buys back every bin on
        screen — and folds the IQ image of everything shown into the half
        being discarded, so mirrors stop appearing too.

        It only works when the span fits in one half of the tune. There is no
        offset that helps a span wider than that, because half of it is always
        on the far side of the centre, and narrowing the span to make it fit
        would answer a different question than the one that was asked. Those
        fall back to flattening, and say so."""
        rate = self.params["sample_rate"]
        centre = None
        if options.offset_tune != "off":
            # Clear of the flattened bins with a bin to spare, and never so
            # tight a guard that the offset is spent for nothing
            bin_size = rate / fft_size
            guard = max((hackrf_stream.dc_spike_bins(options.window) + 1) * bin_size,
                        0.002 * rate)
            # The passband is the baseband filter, not the sample rate: at
            # 20 MSPS the radio passes 15 MHz, and a span placed by Nyquist
            # alone puts its top in the roll-off
            centre = hackrf_stream.offset_tune(
                self.params["start_freq"] * 1e6 - self.lnb_lo,
                self.params["stop_freq"] * 1e6 - self.lnb_lo, rate, guard,
                usable=hackrf_stream.baseband_filter_bw(0.75 * rate))

        # A survey checking for receiver spurs looks at each slice twice, and
        # asks for the second look from the other side of the passband: the
        # span moves from the upper half of the tune to the lower one. Half a
        # passband is a whole number of bins at every FFT size this uses, so
        # the two looks land on the same absolute grid and can be compared bin
        # for bin - and anything sitting at a fixed offset from the tune has
        # moved right out of the span.
        if centre is not None and QtCore.QSettings().value("survey_tune_flip", 0, int):
            centre += hackrf_stream.baseband_filter_bw(0.75 * rate) / 2.0
            self.tune_flipped = True
        else:
            self.tune_flipped = False

        self.offset_tuned = centre is not None
        if centre is not None:
            self.params["center_freq"] = centre

    def set_gain(self, gain=None, lna=None, vga=None, amp=None):
        """Change the gain on a radio that is already running

        Kept in step whether or not the radio is open: the stages settled here
        are the ones a later start will use, so a gain changed while stopped
        is not lost and a gain changed while running is not deferred."""
        if gain is not None or lna is not None or vga is not None:
            self.lna, self.vga = hackrf_stream.stage_gains(
                -1 if gain is None else gain,
                self.lna if lna is None else lna,
                self.vga if vga is None else vga)
        if amp is not None:
            self.amp = bool(amp)
        if self.source is not None:
            self.source.set_gain(self.lna, self.vga, self.amp)
        return self.lna, self.vga, self.amp

    @property
    def dc_band(self):
        """Where the receiver's own carrier is, in the frequencies shown

        None before the radio is open. Outside the span when the tune has been
        offset, which is the point of offsetting it."""
        if self.source is None:
            return None
        low, high = self.source.dc_band
        return (low + self.lnb_lo, high + self.lnb_lo)

    def measured_bins(self, frequencies):
        """The bins that are a measurement of the air rather than of the radio

        The lowest bin of a tune is not a measurement. It is the Nyquist bin,
        where the two ends of the passband meet, and it sits high at a fixed
        level whatever the air is doing - so it turns up in a survey as a
        narrow signal that is *always on*, which is the one description no
        real signal ever has. Measured on this receiver at 5180 MHz: the
        outermost bin stood 13.9 dB over the floor for the whole dwell.

        The window spreads it inwards exactly as it spreads the DC spike, so
        the same count goes with it - at 39 kHz bins the second bin was still
        9 dB high while the third was already back on the floor.

        Only the bottom, and only a bin or two: the top of the tune measured
        clean, and cropping to the baseband filter instead would take a
        quarter of every tune and leave gaps between the slices of a survey."""
        keep = np.ones(len(frequencies), dtype=bool)
        keep[:1 + max(0, self.source.dc_bins)] = False
        return keep

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

        # Never widen what was asked for, and never hand back nothing: a tune
        # narrower than the filter has no roll-off in it to drop
        measured = mask & self.measured_bins(frequencies)
        self.dropped_edges = int(mask.sum() - measured.sum())
        if measured.any():
            mask = measured

        self.crop_mask = mask
        self.x = frequencies[mask]

    def on_spectrum(self, frequencies, powers_db, timestamp):
        """Called by hackrf_stream for each completed average

        Runs on libhackrf's receive thread, which must not be held up: while
        this is inside DataStorage the radio has nowhere to put samples and
        starts dropping them. So it only hands the spectrum over, and the
        thread's own loop does the delivering."""
        self.latest = (timestamp, powers_db)

        # A survey looking for something rare wants every spectrum, not the
        # hundred a second the display is given: the delivery cap is there to
        # keep DataStorage and the drawing from being swamped, and neither is
        # involved in a max. One pass over an array already in cache is the
        # whole cost, so it is affordable even here.
        hold = self.peak_hold
        if hold is None or hold.shape != powers_db.shape:
            self.peak_hold = powers_db.copy()
        else:
            np.maximum(hold, powers_db, out=hold)
        self.peak_spectra += 1

    def take_peak_hold(self):
        """The highest each bin reached since the last call, and how many
        spectra went into that

        Returned in the bins the display uses, so it lines up with the x axis
        and with the delivered history.

        No lock: this thread is the only writer, and the only thing the reader
        does is swap a fresh accumulator in. That can lose the single spectrum
        being maxed at the instant of the swap, which happens once at the end
        of a survey slice - not worth making the radio's own thread wait for."""
        hold, seen = self.peak_hold, self.peak_spectra
        self.peak_hold, self.peak_spectra = None, 0
        if hold is None or self.crop_mask is None:
            return None, seen
        return hold[self.crop_mask], seen

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

        fft_size = hackrf_stream.fast_fft_size(self.params["sample_rate"],
                                               self.params["bin_size"] * 1e3)
        average = self.frames_averaged(options.average, fft_size)
        self.choose_tune(options, fft_size)

        self.source = hackrf_stream.SpectrumSource(
            center_freq=self.params["center_freq"],
            sample_rate=self.params["sample_rate"],
            bin_size=self.params["bin_size"] * 1e3,
            average=average,
            lna=self.lna,
            vga=self.vga,
            window=options.window,
            dc_bins=options.dc_bins,
            amp=self.amp,
            serial=self.params["device"] or None,
            # --peak in the params still works; the setting is the way to
            # reach it without editing a command line
            mode='peak' if (options.peak
                            or settings.value("sweep_detector", "mean") == "peak")
                 else 'mean',
        )
        self.source.open()
        self.prepare_axis()
        if self.band is not None:
            self.source.set_band(self.band[0] - self.lnb_lo, self.band[1] - self.lnb_lo,
                                 self.band_resolution, self.band_detector)

        lines = self.describe_radio(options, average)
        for line in self.check_settings(options, average):
            lines.append("  {:<10} {}".format("check", line))
        for line in lines:
            print(line)
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

    def set_band(self, low, high, resolution=None, detector="peak"):
        """Watch one band's power in the time domain — a zero span view

        The band arrives in the frequencies the display shows, which include
        the LNB offset; the radio only knows about the ones it is tuned to.
        `resolution` asks for seconds per reading; None gives the finest the
        radio can be read at, which is one FFT frame. Pass None for either
        edge to stop watching, which is what it costs nothing to do."""
        if low is None or high is None:
            self.band = self.band_resolution = None
            if self.source is not None:
                self.source.set_band(None, None)
            return

        self.band = (low, high)
        self.band_resolution = resolution
        self.band_detector = detector
        if self.source is not None:
            self.source.set_band(low - self.lnb_lo, high - self.lnb_lo,
                                 resolution, detector)

    @property
    def dropped(self):
        """Sample blocks lost because the DSP could not be given the CPU"""
        return self.source.dropped if self.source is not None else 0

    @property
    def tap_resolution(self):
        """Seconds each band reading covers, once snapped to whole frames"""
        if self.source is None:
            return None
        return self.source.band_resolution

    @property
    def tap_epoch(self):
        """The clock time the band readings are counted from, or None

        They are counted from the start of the stream rather than stamped on
        the wall clock, because a float holding seconds since 1970 cannot
        resolve better than 0.24 us in this decade and the readings are 0.8 us
        apart. The display keeps the two apart and adds this once per window."""
        return self.source.stream_start if self.source is not None else None

    def take_band_power(self):
        """Band samples gathered since the last call, as (time, power) rows

        Times are seconds from tap_epoch, not from the epoch."""
        if self.source is None:
            return None
        return self.source.take_band_power()

    def report_drops(self):
        """Say so when samples are being lost, and say which problem it is

        Dropped samples are the one thing that shows on screen as a spectrum
        that jumps rather than as a spectrum that is late, so it is worth
        saying out loud instead of leaving it to be guessed at.

        There are two quite different reasons for it and they need opposite
        fixes, so the message reports what the FFT thread was measured doing
        rather than guessing. Busy most of real time means the DSP genuinely
        cannot keep up. Busy hardly any of it means it could not get on the
        CPU, which in Python means something else held the interpreter lock —
        a repaint, almost always."""
        if self.source is None:
            return
        dropped = self.source.dropped
        if dropped <= self.reported_drops:
            return
        # Once per doubling, so a machine that cannot keep up says so early
        # and then stays quiet instead of filling the terminal
        if dropped < self.reported_drops * 2 and self.reported_drops:
            return
        self.reported_drops = dropped

        busy = self.source.busy_fraction
        cpu = self.source.cpu_fraction
        lost = dropped * self.source.transfer_seconds
        # Since the last message, not since the run began: the queue fills
        # while the display builds itself, and a lifetime peak would report
        # that first second for the rest of the evening
        peak = self.source.take_queue_peak()
        if cpu > 0.7:
            advice = ('the DSP cannot keep up. Raise the bin size (fewer, '
                      'shorter FFTs) or lower the sample rate.')
        elif busy > 0.5:
            advice = ('the DSP has headroom but cannot get on the CPU: it is '
                      'waiting for the interpreter lock, which the drawing '
                      'holds. The display is giving frames back; if that is '
                      'not enough, turn off the curves the status bar calls '
                      'slower.')
        else:
            advice = ('neither the DSP nor the lock looks busy, so the stall '
                      'was somewhere else - a resize, or the machine sleeping.')
        print('hackrf_stream: dropped {} blocks ({:.1f} s of signal). FFT thread '
              'on the CPU {:.0f}% of real time, inside its work {:.0f}%, queue '
              'peaked at {}/{} since the last of these - {}'.format(
                  dropped, lost, cpu * 100, busy * 100, peak,
                  self.source.statistics().get("queue_depth", 0), advice))

    def report_band_error(self):
        """Say so if the high rate tap stopped, without stopping the radio"""
        error = self.source.band_error if self.source is not None else None
        if error is None or error is self.reported_band_error:
            return
        self.reported_band_error = error
        print('hackrf_stream: the high-rate tap stopped ({}: {}). Spectra are '
              'unaffected; untick and retick it to start it again.'
              .format(type(error).__name__, error))

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
            self.report_drops()
            self.report_band_error()
            self.msleep(2)

        self.process_stop()
        self.alive = False
        self.powerThreadStopped.emit()
