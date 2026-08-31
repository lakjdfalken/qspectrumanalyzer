"""Finding a pulse train in a trace that is too noisy to trigger on

A trigger asks one question of every reading: is this one loud? That question
has a hard floor, and it is not set by the receiver but by how many readings
are looked at. The high rate tap reads six hundred thousand times a second, and
the loudest of that many samples of noise stands about six decibels above the
floor inside a single sweep and eleven over a minute of looking — so a pulse
that is only a few decibels up cannot be told from the noise by its height, no
matter where the level is put. That is arithmetic, not a tuning problem.

A pulse train has something noise does not: it comes back. A surveillance radar
sends a pulse every 0.8 to 4 ms, and does it again on the next rotation, and
the interval between them is the same to within a fraction of a microsecond
for hours. Noise never does that. So instead of asking how loud a reading is,
this asks whether the whole trace has a rhythm — and where a trigger gets worse
the longer it looks, this gets better: a thousand pulses added up in step stand
thirty times clear of noise added up out of step.

The search is the one radio astronomy uses on pulsars, for the same reason:
the signal is far below the noise in any single sample and perfectly periodic
across millions of them.

  1. The trace becomes power rather than decibels, with its own median taken
     off, so a pulse adds and the noise averages to nothing.
  2. One Fourier transform turns "does anything repeat" into "is there a line
     at some frequency", for every rate at once.
  3. A short pulse puts almost nothing at its own repetition rate and a little
     at each of its many harmonics, so the harmonics are added back together.
     This is what finds a train whose fundamental is invisible.
  4. Whatever stands out is then folded — the trace cut into lengths of one
     period and stacked — which is both the proof and the measurement: it says
     how wide the pulse is, how many of them there were, and how far the stack
     stands above the noise it was buried in.

Nothing here imports Qt, so the same reading serves the application, the
command line and a saved sweep.
"""

import argparse
import sys

import numpy as np

#: Repetition rates worth searching, in Hz. The top is above any surveillance
#: radar's pulse rate. The bottom used to be 100 Hz, on the assumption that
#: what repeats is individual pulses - but a burst hundreds of microseconds
#: long, which is what a radar using pulse compression sends, repeats far more
#: slowly than that, and a range starting at 100 Hz cannot see it at all. One
#: hertz costs nothing to search and covers both.
DEFAULT_RATES = (1.0, 5000.0)

#: Fewest times a rate must repeat inside the stretch being searched before it
#: is a rhythm rather than an event. Eight is few enough to find something slow
#: in a short recording and enough that folding means something.
MIN_CYCLES = 8

#: Harmonics added together. A one microsecond pulse repeating every
#: millisecond puts its energy into about a thousand harmonics, so no single
#: one of them is visible; thirty-two is where the returns flatten out against
#: what it costs, and it is enough to find a train whose fundamental is not
#: there at all.
HARMONICS = 32

#: Below this, a detection is real but its rate is not to be trusted to the
#: pulse: with only tens of pulses caught, a fraction of the true rate can
#: stack nearly as well as the rate itself, and the report says so rather than
#: quoting an interval that may be five times too long.
FIRM = 15.0

#: A candidate has to be this many times the scatter of the background before
#: it is worth reporting. Five is the usual line for "this is not chance", and
#: the search looks at tens of thousands of rates, so it needs to be.
SIGMA = 5.0

#: Folded profiles are cut this fine at most. One bin per reading is the
#: natural choice — finer says nothing the tap measured — but a slow rate over
#: a long recording would otherwise ask for millions of them.
MAX_BINS = 4096


class Candidate:
    """One repetition rate that stood out, and what folding at it showed"""

    def __init__(self, rate, sigma, profile, step, covered):
        #: Repetitions per second, and the interval that is
        self.rate = rate
        self.sigma = sigma
        #: The trace folded at this period, in dB against its own quiet part
        self.profile = profile
        self.step = step
        #: Seconds of recording that went into it
        self.covered = covered

    @property
    def period(self):
        return 1.0 / self.rate

    @property
    def repeats(self):
        """How many periods were stacked"""
        return int(self.covered / self.period)

    @property
    def peak_db(self):
        return float(np.max(self.profile))

    @property
    def width_seconds(self):
        """How much of the period the pulse takes up

        Measured at half the peak's height in power, which is the width a
        spectrum analyser would quote, and rounded up to one bin: a pulse
        shorter than the tap's own step cannot be measured as narrower than
        one reading, however short it really is."""
        bins = len(self.profile)
        half = self.peak_db - 3.0
        above = int(np.count_nonzero(self.profile >= half))
        return max(above, 1) * self.period / bins

    @property
    def duty(self):
        return self.width_seconds / self.period

    def describe(self):
        return ("{:.2f} Hz ({:.4f} ms apart), pulse {:.2f} us wide, "
                "{} of them stacked, standing {:+.1f} dB above the noise "
                "at {:.1f} sigma".format(
                    self.rate, self.period * 1e3, self.width_seconds * 1e6,
                    self.repeats, self.peak_db, self.sigma))


def on_a_grid(times, power_db):
    """The readings on an evenly spaced grid, as linear power

    The tap produces one reading per group of frames and stamps them from a
    frame counter, so they are already evenly spaced — but a dropped block
    leaves a gap, and a Fourier transform of a trace with a hole in it reads
    the hole as a signal. Gaps are filled with the median, which is the one
    value that adds nothing at any frequency.

    Returns (power, step, covered) with the median already taken off, so that
    silence is zero rather than the noise floor."""
    times = np.asarray(times, dtype=np.float64)
    power_db = np.asarray(power_db, dtype=np.float64)
    if len(times) < 16:
        raise ValueError("too few readings to look for a rhythm in")

    step = float(np.median(np.diff(times)))
    if not step > 0:
        raise ValueError("the readings do not advance in time")

    index = np.rint((times - times[0]) / step).astype(np.int64)
    size = int(index[-1]) + 1
    if size > 4 * len(index):
        raise ValueError("the readings are too gappy to search "
                         "({} readings across {} steps)".format(len(index), size))

    linear = 10.0 ** (power_db / 10.0)
    grid = np.full(size, np.median(linear))
    grid[index] = linear
    grid -= np.median(grid)
    return grid, step, size * step


def rhythm(power, step, rates=DEFAULT_RATES, harmonics=HARMONICS):
    """How strongly the trace repeats, at every rate in the range

    Returns (rate, strength) — the strength being how far each rate's summed
    harmonics stand above the background, in its own scatter."""
    size = len(power)
    # A window, because a pulse train does not divide evenly into the length
    # of a recording and the ends would otherwise ring across the whole search
    spectrum = np.abs(np.fft.rfft(power * np.hanning(size)))
    resolution = 1.0 / (size * step)

    # Flatten whatever slope the background has, so that one number can be
    # compared against every rate rather than against its neighbourhood
    background = np.median(spectrum[1:]) or 1.0
    spectrum = spectrum / background
    spectrum[0] = 0.0                      # what is left of DC after the median

    # A rate has to come round several times inside the piece being searched
    # or there is nothing to stack: bin k of the transform is k cycles in the
    # record, so this is simply "at least MIN_CYCLES of them". Without it the
    # lowest bins report enormous confidence in a rhythm that happened once.
    first = max(MIN_CYCLES, int(rates[0] / resolution))
    last = int(rates[1] / resolution)
    last = min(last, (len(spectrum) - 1) // harmonics)
    if last <= first:
        raise ValueError("the recording is too short to look for rates that low")

    # Add each rate to its own harmonics: a short pulse leaves almost nothing
    # at the rate it repeats and a little at each multiple of it
    summed = np.zeros(last - first, dtype=np.float64)
    for harmonic in range(1, harmonics + 1):
        stride = spectrum[first * harmonic:last * harmonic:harmonic]
        summed += stride[:len(summed)]

    middle = np.median(summed)
    scatter = 1.4826 * np.median(np.abs(summed - middle)) or 1.0
    rate = np.arange(first, last) * resolution
    return rate, (summed - middle) / scatter


def fold(power, step, period, max_bins=MAX_BINS):
    """The trace cut into periods and stacked, in dB against its quiet part

    The whole point of the exercise: a pulse that is invisible in any single
    period lands in the same bin every time, and noise does not."""
    bins = int(min(max(round(period / step), 4), max_bins))
    phase = (np.arange(len(power)) * step) % period
    which = np.minimum((phase / period * bins).astype(np.int64), bins - 1)
    total = np.bincount(which, weights=power, minlength=bins)
    count = np.bincount(which, minlength=bins)
    profile = total / np.maximum(count, 1)

    # Against the quiet part of the profile rather than its mean, so a pulse
    # cannot raise the very floor it is being measured against
    quiet = np.median(profile)
    scatter = 1.4826 * np.median(np.abs(profile - quiet)) or 1e-12
    return 10.0 * np.log10(np.maximum(profile - quiet, 0.0) / scatter + 1e-3)


#: How the recording is cut up before searching. A train that runs through the
#: whole of it is found best by looking at all of it at once; a radar that
#: sweeps past for sixty milliseconds every few seconds is drowned by the
#: silence around it, and is found only by looking at a piece the size of the
#: dwell. Neither length can be guessed in advance, so both are tried - and
#: the total work is the same for each pass, since sixteen transforms of a
#: sixteenth cost what one of the whole does.
PIECES = (1, 4, 16)

#: Readings used when folding to *choose* a rate rather than to report one.
#: Telling one pulse from two needs a few hundred periods, not a million
#: readings, and the choosing does it a few hundred times over.
FOLD_SAMPLES = 262144

#: Two rates are the same train if their ratio is a simple fraction. A pulse
#: train lights up every multiple of its rate, and gets partial credit at
#: fractions like 5/2 where some multiples land on real lines, so a family has
#: to be recognised by more than whole numbers.
SIMPLE_FRACTION = 12


def _peaks(strength, sigma):
    """Indices of local maxima standing at least `sigma` above the background"""
    above = np.flatnonzero(strength >= sigma)
    if not len(above):
        return above
    peak = np.ones(len(above), dtype=bool)
    peak[1:] &= np.diff(above) > 1                  # keep the first of a run
    inner = above[(above > 0) & (above < len(strength) - 1)]
    return above[peak]


def _same_train(rate, other):
    """Whether two rates are one train counted differently

    A train at 1 kHz shows at 2 and 3 kHz because it has those harmonics, at
    500 Hz because folding twice as slowly still stacks it, and weakly at
    2.5 kHz because two of every five multiples of 2.5 land on a real line."""
    ratio = max(rate, other) / min(rate, other)
    for bottom in range(1, SIMPLE_FRACTION + 1):
        top = ratio * bottom
        if abs(top - round(top)) < 0.01 * bottom and round(top) <= 32:
            return True
    return False


def peaks_in(profile, below=3.0):
    """How many separate pulses a folded profile has

    This is what tells the true interval from a fraction of it. Folding a
    train at exactly its own rate stacks every pulse into one place; folding
    at half that rate stacks them into two, a third into three. So the pulse
    interval is the longest one that still gives a single pulse - and both
    look equally convincing until they are counted."""
    if not len(profile):
        return 0
    # Half the height, or `below` down from the top, whichever is lower. A
    # fixed drop from the peak is wrong at both ends: on a strong fold it sits
    # above the second pulse when the two stack a little unevenly, and on a
    # weak one it sits down among the bumps in the noise.
    top = float(np.max(profile))
    edge = min(0.5 * top, top - below)
    above = profile >= edge
    if not above.any():
        return 0
    # Circular, because a profile is one period and its ends are neighbours
    starts = np.flatnonzero(above & ~np.roll(above, 1))
    return max(len(starts), 1)


def _fundamental(power, step, rate, limits):
    """The longest interval that still folds the train into a single pulse

    What the transform finds is rarely the interval itself. Every multiple of
    a train's rate carries a line, and simple fractions of it get partial
    credit when some of their own multiples land on those lines - so a train
    at 632 Hz can be reported at 3919, which is 31/5 of it. Folding settles
    it, because folding is not a matter of degree: at the interval between
    pulses they all land in one place, at half of it they land in two, and at
    a rate that is not the train's at all they do not land anywhere.

    So the candidates are the simple fractions of what was found, and the
    answer is the lowest of them that still shows one pulse and stacks it as
    high as the best does."""
    power = power[:FOLD_SAMPLES]
    trials = set()
    for top in range(1, 33):
        for bottom in range(1, 9):
            trial = rate * bottom / top
            if limits[0] <= trial <= limits[1]:
                trials.add(round(trial, 6))

    scored = []
    for trial in sorted(trials):
        profile = fold(power, step, 1.0 / trial)
        if peaks_in(profile) == 1:
            scored.append((trial, float(np.max(profile))))
    if not scored:
        return rate

    best = max(peak for _, peak in scored)
    for trial, peak in scored:                  # lowest first
        if peak >= best - 6.0:
            return trial
    return rate


def _stacks_worse(power, step, rate, against, by=6.0):
    """Whether folding at `rate` stacks the pulses less well than at `against`

    At the interval between pulses every one of them lands in the same place,
    and so it does at any whole multiple of that rate — so a true fundamental
    never stacks worse than the harmonic it was found through. A fraction that
    is not one, on the other hand, spreads them, and that shows immediately."""
    here = float(np.max(fold(power, step, 1.0 / rate)))
    there = float(np.max(fold(power, step, 1.0 / against)))
    return here < there - by


def _refine(power, step, rate, spread):
    """Sharpen a rate by folding at it, since the transform only bins it

    A segment a tenth of a second long bins rates ten hertz apart, and folding
    a thousand pulses at a rate ten hertz out smears them across the profile.
    The fold itself is the finer instrument: try rates either side and keep
    whichever stacks highest."""
    best, best_peak = rate, -np.inf
    for trial in np.linspace(rate - spread, rate + spread, 41):
        if trial <= 0:
            continue
        peak = float(np.max(fold(power, step, 1.0 / trial)))
        if peak > best_peak:
            best, best_peak = float(trial), peak
    return best


def search(times, power_db, rates=DEFAULT_RATES, harmonics=HARMONICS,
           sigma=SIGMA, limit=4):
    """Look for a pulse train, and fold at whatever is found

    Returns (candidates, covered, step). Each candidate is one train, reported
    at the lowest rate that explains it: a train at 1 kHz is also a peak at 2
    and 3 kHz, and it is the 1 kHz that is the pulse interval."""
    power, step, covered = on_a_grid(times, power_db)

    # Every rate that stood out, in every piece the recording was cut into,
    # with the piece it was found in - a dwell has to be folded over the piece
    # that holds it rather than over the silence on either side
    hits = []
    for pieces in PIECES:
        size = len(power) // pieces
        if size < 4096:
            continue
        for start in range(0, pieces * size, size):
            chunk = power[start:start + size]
            try:
                rate, strength = rhythm(chunk, step, rates, harmonics)
            except ValueError:
                continue
            resolution = 1.0 / (size * step)
            for index in _peaks(strength, sigma):
                hits.append((float(strength[index]), float(rate[index]),
                             start, size, resolution))
    hits.sort(reverse=True)

    found = []
    claimed = []
    for strongest, rate, start, size, resolution in hits:
        if len(found) >= limit:
            break
        if any(_same_train(rate, taken) for taken in claimed):
            continue
        # The lowest rate in the same family is the interval between pulses;
        # everything above it is a harmonic of the same train
        chunk = power[start:start + size]
        # Every multiple of a train's rate carries the same lines, so the
        # transform cannot tell 643 Hz from 1286: both sums are made of the
        # same harmonics. What separates them from a fraction like 100 Hz -
        # which only catches every tenth line and is a different train
        # entirely - is how much of the family's strength they carry. So the
        # interval between pulses is the lowest rate that is nearly as strong
        # as the strongest, and simple fractions are only searched by folding
        # when nothing else in the family was detected at all.
        family = [(r, s) for s, r, _, _, _ in hits if _same_train(r, rate)]
        peak_strength = max(s for _, s in family)
        # Ascending, and the fold has the last word on each: a rate that is
        # half the real one carries plenty of strength - a burst hundreds of
        # microseconds long has few harmonics and they all land on it - but it
        # folds two bursts into the period instead of one, and that is not a
        # matter of degree.
        lowest = rate
        for candidate in sorted(r for r, s in family if s >= 0.6 * peak_strength):
            if peaks_in(fold(chunk, step, 1.0 / candidate)) == 1:
                lowest = candidate
                break
        if len(family) == 1:
            lowest = _fundamental(chunk, step, rate, rates)
        # A fraction that only catches every fifth line can still carry enough
        # of the strength to look like the fundamental. Folding says whether it
        # is one: at the interval between pulses they stack, and at a fifth of
        # it they are spread across five places and the stack is poorer.
        if lowest != rate and _stacks_worse(chunk, step, lowest, rate):
            lowest = rate
        claimed.append(rate)
        if lowest != rate:
            claimed.append(lowest)

        exact = _refine(chunk, step, lowest, resolution * lowest / rate)

        found.append(Candidate(exact, strongest, fold(chunk, step, 1.0 / exact),
                               step, size * step))

    # Strongest first by how well it stacks, not by how it was detected. Sigma
    # says a rhythm is there; the folded height says which rate is the one the
    # pulses actually keep, and a harmonic that was found more easily still
    # stacks them less well than the interval itself.
    found.sort(key=lambda candidate: candidate.peak_db, reverse=True)
    return found, covered, step


def report(times, power_db, header=(), **kwargs):
    """Look for a rhythm and say what was found, as lines of text"""
    lines = list(header)
    try:
        found, covered, step = search(times, power_db, **kwargs)
    except ValueError as error:
        return lines + ["Cannot look for a rhythm here: {}".format(error)]

    lines.append("")
    lines.append("{:.3f} s of trace at {:.2f} us a reading, searched for "
                 "anything repeating between {:g} and {:g} Hz".format(
                     covered, step * 1e6, DEFAULT_RATES[0], DEFAULT_RATES[1]))

    if not found:
        lines.append("")
        lines.append("Nothing repeats. That is a real negative for a pulse "
                     "train transmitting for most of these {:.2f} s — but a "
                     "rotating radar points this way for perhaps sixty "
                     "milliseconds every several seconds, and if its turn did "
                     "not fall inside this recording there was nothing here to "
                     "find.".format(covered))
        if covered < 5.0:
            # The one setting that buys a longer look for nothing, and the
            # reason it is free is not obvious
            lines.append("")
            lines.append("The trace is only {:.2f} s long. A coarser zero span "
                         "step buys more of it at no cost to the pulse: the "
                         "peak detector keeps the loudest frame of each group, "
                         "so a microsecond pulse still reads at full height in "
                         "a ten microsecond reading, and the same buffer then "
                         "holds ten seconds instead of {:.1f}. Set the zero "
                         "span step to 10 us in Settings and run this again."
                         .format(covered, covered))
        return lines

    lines.append("")
    lines.append("{} rhythm{} found:".format(
        len(found), "" if len(found) == 1 else "s"))
    for candidate in found:
        lines.append("  " + candidate.describe())

    best = found[0]
    if best.sigma < FIRM:
        lines.append("")
        lines.append("That is a real repetition, but only {:.0f} pulses were "
                     "caught, and at that strength the interval reported can be "
                     "a whole multiple of the true one — a train every 0.78 ms "
                     "can come out as one every 3.9 ms when only every fifth "
                     "pulse rose clear. Treat it as the rhythm being there "
                     "rather than as a measurement of the interval, and look "
                     "again with a longer trace to pin it down.".format(
                         best.repeats if best.repeats < 1000 else 1000))

    lines.append("")
    lines.append("The strongest, folded:")
    lines.append("  " + _sparkline(best.profile))
    lines.append("  one period, {:.4f} ms across, {:+.1f} dB at the peak"
                 .format(best.period * 1e3, best.peak_db))
    lines.append("")
    lines.append("To look at it in the scope:")
    lines.append("  span          {:.3f} ms, which holds {:.1f} periods".format(
        best.period * 4e3, 4.0))
    lines.append("  trigger       by hand at the peak, not on auto - the "
                 "point of this is that the peak is under the automatic level")
    return lines


def _sparkline(profile, width=64):
    """The folded profile as one line of text, for a terminal"""
    marks = " .:-=+*#@"
    if len(profile) > width:
        edges = np.linspace(0, len(profile), width + 1).astype(int)
        profile = np.array([profile[a:b].max() if b > a else profile[a]
                            for a, b in zip(edges[:-1], edges[1:])])
    low, high = float(np.min(profile)), float(np.max(profile))
    if high <= low:
        return marks[0] * len(profile)
    scaled = (profile - low) / (high - low) * (len(marks) - 1)
    return "".join(marks[int(round(value))] for value in scaled)


def read_sweep(path):
    """The tap readings out of a sweep saved by QSpectrumAnalyzer"""
    times, power, header = [], [], []
    with open(path) as handle:
        for line in handle:
            line = line.strip()
            if line.startswith("#"):
                header.append(line[1:].strip())
                continue
            if not line or line.startswith("time_s"):
                continue
            columns = line.split(",")
            if len(columns) < 3 or columns[2] != "tap":
                continue
            times.append(float(columns[0]))
            power.append(float(columns[1]))
    if not times:
        raise ValueError("no high-rate readings in {} - the sweep was saved "
                         "without the tap".format(path))
    return np.array(times), np.array(power), header


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="qspectrumanalyzer.periodicity",
        description="Look for a pulse train in a sweep saved by QSpectrumAnalyzer")
    parser.add_argument("sweep", nargs="+", help="one or more sweep CSV files")
    parser.add_argument("--from", dest="low", type=float, default=DEFAULT_RATES[0],
                        help="lowest repetition rate to look for, in Hz")
    parser.add_argument("--to", dest="high", type=float, default=DEFAULT_RATES[1],
                        help="highest repetition rate to look for, in Hz")
    parser.add_argument("--sigma", type=float, default=SIGMA,
                        help="how far above the background a rate must stand")
    args = parser.parse_args(argv)

    for path in args.sweep:
        if len(args.sweep) > 1:
            print("=== {} ===".format(path))
        try:
            times, power, header = read_sweep(path)
            print("\n".join(report(times, power, header,
                                   rates=(args.low, args.high), sigma=args.sigma)))
        except (OSError, ValueError) as error:
            print("{}: {}".format(path, error), file=sys.stderr)
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
