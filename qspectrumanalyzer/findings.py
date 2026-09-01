"""Reading a survey back and saying what stood out in it

A survey writes down what every bin ever reached and how often it stood clear
of its own noise. That is the raw material for an answer, not the answer: three
hundred rows of numbers still have to be turned into "there is something at
2817 MHz, three megahertz wide, and here is how to go and look at it".

This does that turning, and deliberately stops there. It reports what was
measured — where, how wide, how far above the noise, how often — and leaves
the question of what the signal *is* to whoever reads it. A list that
confidently says "radar" and is wrong is worse than no list at all.

Nothing here imports Qt, so the same reading serves the application and the
command line.
"""

import argparse
import sys

import numpy as np


class Finding:
    """One stretch of spectrum that behaved differently from its neighbours"""

    def __init__(self, low_hz, high_hz, peak_db, floor_db, duty, active, sweeps, bins):
        self.low_hz = low_hz
        self.high_hz = high_hz
        self.peak_db = peak_db
        self.floor_db = floor_db
        #: The largest fraction of sweeps any of its bins was active in, and
        #: the count behind it: one sweep out of thousands is noise brushing
        #: the threshold, however striking the percentage looks
        self.duty = duty
        self.active = active
        self.sweeps = sweeps
        self.bins = bins

    @property
    def centre_hz(self):
        return (self.low_hz + self.high_hz) / 2

    @property
    def width_hz(self):
        return self.high_hz - self.low_hz

    @property
    def above_db(self):
        return self.peak_db - self.floor_db

    @property
    def steady(self):
        """Whether it was there all the time rather than coming and going

        A carrier never stands clear of its own median, however loud it is, so
        one that is loud and never active is a signal that is simply always on.
        """
        return self.duty <= 0.0

    def describe(self):
        """One line, in the terms the survey measured it in"""
        return ("{:9.3f} MHz  {:6.2f} MHz wide  {:+5.1f} dB above the floor  "
                "{}".format(self.centre_hz / 1e6, self.width_hz / 1e6, self.above_db,
                            "always on" if self.steady
                            else "in {} of {} sweeps ({:.2f}%)".format(
                                self.active, self.sweeps, self.duty * 100)))


def read_survey(path):
    """Read a survey file, returning the columns and the header lines"""
    header, rows = [], []
    with open(path) as handle:
        for line in handle:
            if line.startswith("#"):
                header.append(line[1:].strip())
                continue
            if not line[:1].isdigit():
                continue                    # the column names
            a, b, c, d = line.split(",")
            rows.append((float(a), float(b), int(c), int(d)))
    if not rows:
        raise ValueError("{}: no readings in it".format(path))
    columns = np.array(rows, dtype=np.float64)
    return columns[:, 0], columns[:, 1], columns[:, 2], columns[:, 3], header


#: When no bin was ever quiet, the floor is taken from this fraction of the
#: quietest bins instead. A quarter is enough to be a median rather than a
#: minimum, and few enough that something covering three quarters of the span
#: still cannot set the level it is measured against.
QUIET_FRACTION = 0.25


def noise_floor(loudest, active):
    """Where the survey's own noise sat

    Taken from the bins that were never active, so that a band full of signals
    does not raise the level everything else is measured against.

    When every bin was active there is nothing quiet to compare with, and the
    median of the lot is *not* the best that can be done - it is the worst,
    because a signal wide enough to fill the span then sets its own reference
    and reports itself as a few dB over a floor made of itself. Measured on a
    5622-5628 MHz survey where all nineteen bins were active: the median of
    the lot gave -24.2 dB and the emitter read +3.9 dB over it, while the
    quietest bins gave -27.5 dB and the same emitter read +7.1. The quietest
    quarter is the fallback: still a median, so one odd bin cannot set it, but
    taken from the part of the span the signal had least of."""
    quiet = loudest[active == 0]
    if quiet.size:
        return float(np.median(quiet))
    keep = max(1, int(round(loudest.size * QUIET_FRACTION)))
    return float(np.median(np.sort(loudest)[:keep]))


#: What a candidate has to manage before it is worth reporting: either enough
#: separate sweeps to be more than one unlucky sample of noise, or enough
#: height that a single sighting still means something
MIN_ACTIVE = 3
MIN_ABOVE = 6.0


def find(frequency, loudest, active, total, margin=6.0, bridge=1):
    """Group the bins that stood out into candidates, strongest first

    A bin is worth looking at if it was ever active, or if it reached `margin`
    decibels above the noise without ever being active — which is what a
    signal that is always on looks like. Neighbouring bins are joined up,
    across a gap of `bridge` bins, because one emission covers several and
    reporting each separately would bury the answer in its own detail."""
    floor = noise_floor(loudest, active)
    interesting = (active > 0) | (loudest > floor + margin)
    if not interesting.any():
        return [], floor

    step = float(np.median(np.diff(frequency))) if frequency.size > 1 else 0.0
    groups, current = [], []
    gap = 0
    for i, flag in enumerate(interesting):
        if flag:
            current.append(i)
            gap = 0
        elif current:
            gap += 1
            if gap > bridge:
                groups.append(current)
                current, gap = [], 0
    if current:
        groups.append(current)

    out = []
    for group in groups:
        idx = np.array(group)
        duty = float((active[idx] / np.maximum(total[idx], 1)).max())
        seen = int(active[idx].max())
        candidate = Finding(
            low_hz=float(frequency[idx].min()) - step / 2,
            high_hz=float(frequency[idx].max()) + step / 2,
            peak_db=float(loudest[idx].max()),
            floor_db=floor,
            duty=duty,
            active=seen,
            sweeps=int(total[idx].max()),
            bins=len(group))
        if seen >= MIN_ACTIVE or candidate.above_db >= MIN_ABOVE:
            out.append(candidate)
    out.sort(key=lambda f: f.above_db, reverse=True)
    return out, floor


def report(path, limit=12):
    """Read a survey and say what is in it, as lines of text"""
    frequency, loudest, active, total, header = read_survey(path)
    found, floor = find(frequency, loudest, active, total)

    lines = [line for line in header if not line.startswith("loudest_db")]
    lines.append("")
    lines.append("{:d} bins, {:.1f}-{:.1f} MHz, noise floor {:+.1f} dB".format(
        len(frequency), frequency.min() / 1e6, frequency.max() / 1e6, floor))

    if not found:
        lines.append("")
        lines.append("Nothing stood out. The loudest bin reached {:+.1f} dB, "
                     "{:+.1f} above the floor.".format(
                         loudest.max(), loudest.max() - floor))
        lines.append("That is a real negative only if the settings above could "
                     "have found what you were looking for.")
        return lines

    lines.append("")
    lines.append("{} worth looking at:".format(len(found)))
    for finding in found[:limit]:
        lines.append("  " + finding.describe())
    if len(found) > limit:
        lines.append("  ... and {} more".format(len(found) - limit))

    best = found[0]
    lines.append("")
    lines.append("To look at the strongest:")
    lines.append("  tune          {:.3f} to {:.3f} MHz".format(
        (best.centre_hz - 10e6) / 1e6, (best.centre_hz + 10e6) / 1e6))
    lines.append("  band centre   {:.3f} MHz, width {:.0f} kHz".format(
        best.centre_hz / 1e6, max(best.width_hz, 1e6) / 1e3))
    lines.append("  trigger       on a rising edge at the automatic level")
    lines.append("  span          20 ms, single sweep, then Arm and wait")
    return lines


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="qspectrumanalyzer.findings",
        description="Say what stood out in a survey written by QSpectrumAnalyzer")
    parser.add_argument("survey", nargs="+", help="one or more survey CSV files")
    args = parser.parse_args(argv)
    for path in args.survey:
        if len(args.survey) > 1:
            print("=== {} ===".format(path))
        try:
            print("\n".join(report(path)))
        except (OSError, ValueError) as error:
            print("{}: {}".format(path, error), file=sys.stderr)
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
