"""Telling non-Wi-Fi energy from Wi-Fi energy, without decoding either

A Wi-Fi transmission fills its whole channel. That is not a habit it could
break, it is the modulation: the OFDM carriers are spread across the full
20 MHz and every frame lights all of them together, from its first symbol to
its last. So in a recording of a Wi-Fi channel, Wi-Fi is the energy that
arrives across the whole span at once — and energy appreciably narrower than
the span is something else. A Bluetooth hop, a video sender, a cordless
phone, a baby monitor, a jammer: the things no station on the network will
ever report, because nothing on the network can hear them.

This is a classification and not a subtraction, and the difference matters.
There is no way to take a recording of a busy channel and hand back what it
would have looked like with the Wi-Fi taken out: that needs every burst
attributed to a transmitter, attribution needs the header, and the header
needs a demodulator. What can be done without one is to say which sweeps
carried narrowband energy and what that energy was, which is the question
worth asking anyway.

Two things this cannot see, and they are worth knowing before trusting it:

  * A non-Wi-Fi emission that is also wide. A radar pulse or a microwave oven
    inside the channel looks exactly like a frame from here. Those are told
    apart by their timing rather than their width, which is what the zero span
    tap and the repeating pulse search are for.
  * A narrowband signal that only ever transmits underneath a frame. It is
    seen in the gaps between frames instead, so a channel that is busy half
    the time still shows it half the time — but a duty cycle read off this is
    a floor, not a measurement.

Nothing here imports Qt, so the same reading serves the application and the
command line.
"""

import argparse
import sys

import numpy as np

from qspectrumanalyzer import findings, recording


#: How far over its own median a bin has to stand before it counts as carrying
#: something, for each way a sweep can be reduced from its frames. Sized
#: against the noise rather than guessed, because the two detectors are not
#: close: a recording of ten thousand sweeps across five hundred bins is five
#: million readings, so the level to clear is where noise alone reaches about
#: once in ten million, and measured over 26 frames that is 7.5 dB for a peak
#: and 3.5 dB for a mean.
#:
#: Which is worth saying plainly, because it is a setting and not a fact of
#: the radio: **a peak detector costs about 4 dB of sensitivity to narrowband
#: interference.** The peak of 26 samples of noise is a wide distribution and
#: every bin gets to draw from it; the mean of the same 26 is a narrow one.
#: For catching a pulse the peak is the right detector and this is the price;
#: for finding what else is on a channel, the mean is.
MARGINS = {"peak": 8.0, "mean": 4.5}

#: Used when the recording does not say which detector made it
MARGIN = MARGINS["peak"]


def margin_for(header):
    """The margin to measure a recording against, and the detector it was made with

    Read from the recording's own header rather than asked for, so that a
    recording taken with a peak detector is not quietly measured against a
    level that only a mean earns."""
    for line in header:
        if line.startswith("sweep detector "):
            detector = line[len("sweep detector "):].strip()
            if detector in MARGINS:
                return MARGINS[detector], detector
            return MARGIN, detector
    return MARGIN, None


#: What fraction of the span has to be lit at once for a sweep to be carrying
#: something that fills the channel. Not 1.0: the edges of a channel roll off
#: into its spectral mask, the tune rarely lines up exactly with the channel,
#: and a frame near the noise loses its weakest bins first.
WIDE_FRACTION = 0.5


#: And how little of the span may be lit for the sweep to be carrying
#: something that plainly does not fill the channel. A quarter of 20 MHz is
#: 5 MHz, which is wider than Bluetooth, ZigBee, DECT or any analogue sender,
#: and narrower than the narrowest thing Wi-Fi transmits.
NARROW_FRACTION = 0.25


#: How much of a sweep's lit bins the widest unbroken stretch of them has to
#: account for before the sweep is called narrowband.
#:
#: Counting lit bins alone is not enough, and a real capture is what said so.
#: A Wi-Fi frame near the noise does not light the whole channel evenly - it
#: lights the parts of it that happened to be over the threshold, scattered
#: across the span, and a fifth of the bins scattered is still only a fifth
#: of the bins. Twelve "findings" came out of one 20 s capture that way, at
#: 5619, 5621, 5624 and 5626 MHz, and the giveaway was that thirty-nine of
#: the same forty-two sweeps carried nearly all of them at once. Nothing
#: narrow transmits in four places simultaneously; one weak wide thing does.
#:
#: So narrowband has to mean *contiguous*: one stretch, not a fifth of the
#: span in crumbs. Seven tenths leaves room for a bin or two of stray noise
#: beside a real emission without letting a scattered frame through.
NARROW_CONTIGUOUS = 0.7


def read_recording(path):
    """Read a recording saved by QSpectrumAnalyzer

    Returns (times, frequencies, powers, header) with powers as sweeps by
    bins — the spectrogram itself, which is what makes the question askable:
    one sweep says what was on the air, and the column headings say where.

    Both shapes are read: the binary the program writes now, and the CSV it
    used to. Recordings already taken are the point of that - a format change
    that makes yesterday's captures unreadable is a format change that throws
    away the measurements, which are the expensive part."""
    if not path.endswith(".csv"):
        return recording.read(path)
    header, frequencies, times, rows = [], None, [], []
    with open(path) as handle:
        for line in handle:
            line = line.strip()
            if line.startswith("#"):
                header.append(line[1:].strip())
                continue
            if not line:
                continue
            columns = line.split(",")
            if frequencies is None:
                if columns[0] != "time_s":
                    raise ValueError("{}: no column headings - this reads a "
                                     "saved recording, not a saved sweep".format(path))
                frequencies = np.array([float(f) for f in columns[1:]])
                continue
            times.append(float(columns[0]))
            rows.append([float(v) for v in columns[1:]])
    if frequencies is None or not rows:
        raise ValueError("{}: no sweeps in it".format(path))
    powers = np.array(rows, dtype=np.float64)
    if powers.shape[1] != frequencies.size:
        raise ValueError("{}: {} headings for {} columns".format(
            path, frequencies.size, powers.shape[1]))
    return np.array(times), frequencies, powers, header, {}


#: What a sweep was carrying. Kept as names rather than numbers because every
#: one of them ends up in a sentence somebody has to read.
QUIET, NARROW, WIDE, MIXED = "quiet", "narrow", "wide", "mixed"


def classify(powers, margin=MARGIN, wide=WIDE_FRACTION, narrow=NARROW_FRACTION):
    """What each sweep was carrying, and which bins were carrying it

    The floor is each bin's own median down the recording. Per bin rather than
    one number for the span, because a receiver is not flat and a tilt of a few
    decibels across the tune would otherwise be read as signal at one end and
    nothing at the other. Down the recording rather than across the span,
    because a signal that fills the span sets its own reference if you let it.

    A median only measures the floor while the bin is quiet more often than
    not. Something transmitting more than half the time becomes its own floor
    and goes unseen — which is the one failure worth naming out loud, because
    it is silent and it looks exactly like a clean channel."""
    floor = np.median(powers, axis=0)
    active = powers > floor + margin
    lit = active.sum(axis=1)
    fraction = lit / active.shape[1]
    run = widest_run(active)

    labels = np.full(len(powers), MIXED, dtype=object)
    labels[lit == 0] = QUIET
    labels[(lit > 0) & (fraction <= narrow)
           & (run >= NARROW_CONTIGUOUS * np.maximum(lit, 1))] = NARROW
    labels[fraction >= wide] = WIDE
    return labels, active, floor


def widest_run(active):
    """The longest unbroken stretch of lit bins in each sweep

    What tells one narrow emission from a wide one seen in pieces. Done on the
    edges rather than a loop per sweep, because a capture is tens of thousands
    of sweeps and this is asked of every one."""
    sweeps, bins = active.shape
    padded = np.zeros((sweeps, bins + 2), dtype=np.int8)
    padded[:, 1:-1] = active
    edges = np.diff(padded, axis=1)
    starts = np.argwhere(edges == 1)
    ends = np.argwhere(edges == -1)
    longest = np.zeros(sweeps, dtype=np.int64)
    if starts.size:
        # argwhere returns row-major order and every run that starts also
        # ends, so the two line up entry for entry
        np.maximum.at(longest, starts[:, 0], ends[:, 1] - starts[:, 1])
    return longest


def separate(frequencies, powers, labels, active, limit=12):
    """Group what the narrowband sweeps carried into findings

    Only the sweeps that carried narrowband energy contribute, so a bin that
    is only ever lit as part of a frame contributes nothing at all. The
    grouping is findings.find(), the same one the survey report uses, so a
    stretch of spectrum is described here in the terms it is described in
    there rather than in a second set of words for the same thing."""
    chosen = labels == NARROW
    if not chosen.any():
        return [], float(np.median(powers))

    seen = active & chosen[:, None]
    counts = seen.sum(axis=0)
    # The loudest each bin ever reached while it was the narrowband one. Bins
    # that were never that get the floor, so they cannot be reported as loud
    loudest = np.where(counts > 0,
                       np.max(np.where(seen, powers, -np.inf), axis=0),
                       np.median(powers, axis=0))
    total = np.full(frequencies.size, int(chosen.sum()))
    found, floor = findings.find(frequencies, loudest, counts, total)
    return found[:limit], floor


def steady(frequencies, floor, limit=12):
    """The bins whose own floor stands above the span's, in findings

    classify() measures every bin against its own past, and that is blind by
    construction to anything transmitting more than half the time: a carrier
    that is nearly always there *is* its own median, so it never stands over
    it. The blindness is total rather than partial — at 51% duty it sees
    nothing at all — and the things it hides are the ones worth finding, since
    a video sender, a leaky oscillator or a jammer is exactly a narrow signal
    that never stops.

    Such a thing is only visible across the span instead of down it: its floor
    is high where its neighbours' are not. So the same grouping runs a second
    time on the floors themselves, with nothing ever marked active — which is
    the case findings.find() already describes as a signal that is simply
    always on."""
    never = np.zeros(frequencies.size, dtype=np.int64)
    once = np.ones(frequencies.size, dtype=np.int64)
    found, level = findings.find(frequencies, floor, never, once)
    return found[:limit], level


#: How often an access point sends a beacon: 100 time units of 1.024 ms. It
#: can be configured, but almost never is, which makes it the one thing on a
#: Wi-Fi channel whose timing is known in advance.
BEACON_INTERVAL = 0.1024


def wide_events(times, labels):
    """When each burst of wide sweeps began

    A frame longer than a sweep lights several in a row, and one frame should
    count once, so consecutive wide sweeps are one event, timed by its first."""
    wide = labels == WIDE
    starts = np.flatnonzero(wide & ~np.concatenate(([False], wide[:-1])))
    return np.asarray(times)[starts]


def beacons(times, labels, interval=BEACON_INTERVAL, slots=64):
    """Whether the wide bursts include an access point's beacons

    The receiver check. Beacons are sent on a fixed rhythm whatever else is
    happening, so folding every burst's start time at the beacon interval
    piles the beacons up at one phase while the rest of the traffic spreads
    evenly round it. Finding that pile says two things a recording cannot say
    any other way: that the receiver hears the access point on this channel
    at all, and that what it classifies as wide includes real Wi-Fi.

    Returns (heard, expected, events): beacons found, beacons an access point
    would have sent in the time recorded, and wide bursts in all. heard is 0
    when no pile stands out of the spread."""
    events = wide_events(times, labels)
    seconds = float(times[-1] - times[0]) if len(times) > 1 else 0.0
    expected = int(seconds / interval)
    if events.size < 3 or not expected:
        return 0, expected, int(events.size)
    phase = np.floor((events % interval) / interval * slots).astype(int) % slots
    counts = np.bincount(phase, minlength=slots)
    # A beacon near a slot edge lands either side of it, so look at pairs
    pairs = counts + np.roll(counts, -1)
    best = int(pairs.max())
    # What a pair of slots holds when nothing lines up, and how far over that
    # chance alone reaches: five standard deviations, Poisson
    spread = 2.0 * (events.size - best) / max(slots - 2, 1)
    if best < max(5, spread + 5.0 * np.sqrt(spread + 1.0)):
        return 0, expected, int(events.size)
    # Traffic that happened to land in the beacons' slots is not beacons
    return min(expected, int(round(best - spread))), expected, int(events.size)


def analyse(path, limit=12, margin=None):
    """Everything report() says about one recording, before it is said"""
    times, frequencies, powers, header, meta = read_recording(path)
    dropped, passband = 0, meta.get("qsa:passband_hz")
    if passband:
        # The bins outside the baseband filter are the filter's own roll-off
        # rather than the air. They slope away exactly as a band going quiet
        # at one end does, and grouped into findings they read as emissions at
        # the edges of the tune - which is what a real capture reported, at
        # 5615 and 5634 MHz of a tune whose filter passed 5617.5 to 5632.5.
        keep = ((frequencies >= float(passband[0]))
                & (frequencies <= float(passband[1])))
        dropped = int((~keep).sum())
        if keep.sum() > 1:
            frequencies, powers = frequencies[keep], powers[:, keep]

    wanted, detector = margin_for(header)
    margin = wanted if margin is None else margin
    labels, active, floor = classify(powers, margin=margin)
    always, level = steady(frequencies, floor, limit)
    found, narrow_floor = separate(frequencies, powers, labels, active, limit)
    step = (float(times[-1] - times[0]) / max(len(times) - 1, 1)
            if len(times) > 1 else 0.0)
    return {
        "path": path, "times": times, "frequencies": frequencies,
        "header": header, "meta": meta, "passband": passband,
        "dropped": dropped, "margin": margin, "detector": detector,
        "labels": labels, "step": step,
        "counts": {name: int((labels == name).sum())
                   for name in (QUIET, NARROW, WIDE, MIXED)},
        "always": always, "level": level, "found": found,
        "narrow_floor": narrow_floor,
        "beacons": beacons(times, labels),
        "tune": meta.get("qsa:tune_centre_hz"),
    }


def compare(first, second, shift, tolerance, always_on=False):
    """Which findings stayed put when the tune moved, and which did not

    The one test that tells the air from the receiver. Something on the air
    is at the same frequency whatever the radio is tuned to. The receiver's
    own spurs are not: they come from its frequency synthesis and move when
    the tune does - though not by the same amount, which a HackRF measured on
    the bench showed plainly, a pair at the tune +-2.50 MHz landing at
    +-2.75 MHz a megahertz further up. So the test is only "did it stay".

    For a signal that is always on that settles it, because a transmitter on
    the air that never stops would still be there after the retune. For one
    that comes and goes, missing from one half can just as well mean it was
    not transmitting then, so that stays unconfirmed. Returns (finding,
    verdict) for every finding in either half."""
    def gone(half):
        if always_on:
            return ("the receiver's own - always on, yet not at this frequency "
                    "{} the {:+.3f} MHz retune, which nothing on the air "
                    "could do".format("after" if half == "first" else "before",
                                      shift / 1e6))
        return "seen in the {} half only - not confirmed".format(half)

    verdicts, claimed = [], set()
    for finding in first:
        verdict = gone("first")
        for index, other in enumerate(second):
            if index not in claimed and abs(other.centre_hz - finding.centre_hz) <= tolerance:
                verdict = "on the air - stayed put when the tune moved"
                claimed.add(index)
                break
        verdicts.append((finding, verdict))
    for index, other in enumerate(second):
        if index not in claimed:
            verdicts.append((other, gone("second")))
    return verdicts


def report(path, limit=12, margin=None, retuned=None):
    """Read a recording and say what in it was not Wi-Fi, as lines of text

    `retuned` is a second recording of the same channel taken with the tune
    moved, which is what lets a finding be called on the air rather than the
    receiver's own."""
    halves = [analyse(path, limit, margin)]
    if retuned:
        halves.append(analyse(retuned, limit, margin))
    first = halves[0]

    lines = list(first["header"])
    for half in halves:
        lines.append("")
        frequencies, times = half["frequencies"], half["times"]
        seconds = float(times[-1] - times[0]) if len(times) > 1 else 0.0
        lines.append("{}{} sweeps x {} bins, {:.3f}-{:.3f} MHz, {:.1f} s at {:.2f} ms "
                     "a sweep".format(
                         "" if len(halves) == 1 else
                         ("first half:  " if half is first else "second half: "),
                         len(times), frequencies.size, frequencies[0] / 1e6,
                         frequencies[-1] / 1e6, seconds, half["step"] * 1e3))
        if half["dropped"]:
            lines.append("  {} bins dropped outside the {:.3f}-{:.3f} MHz the "
                         "baseband filter passes - the filter's own roll-off, not "
                         "the air".format(half["dropped"],
                                          float(half["passband"][0]) / 1e6,
                                          float(half["passband"][1]) / 1e6))

    counts = {name: sum(half["counts"][name] for half in halves)
              for name in (QUIET, NARROW, WIDE, MIXED)}
    total = max(sum(counts.values()), 1)
    detector = first["detector"]
    lines.append("")
    lines.append("What each sweep was carrying, {:g} dB over each bin's own "
                 "median{}:".format(
                     first["margin"], "" if detector is None
                     else " (the level a {} detector earns)".format(detector)))
    for name, what in ((QUIET, "nothing above the floor"),
                       (WIDE, "the whole span at once - Wi-Fi, or something as wide"),
                       (NARROW, "a narrow part of the span - not Wi-Fi"),
                       (MIXED, "between the two, claimed by neither")):
        lines.append("  {:<8} {:7d} sweeps {:5.1f}%   {}".format(
            name, counts[name], 100.0 * counts[name] / total, what))

    # The receiver check, before any finding is believed
    heard = sum(half["beacons"][0] for half in halves)
    expected = sum(half["beacons"][1] for half in halves)
    events = sum(half["beacons"][2] for half in halves)
    lines.append("")
    if heard:
        lines.append("Receiver check: {} wide bursts fall on the {:.1f} ms beacon "
                     "rhythm - {} of the {} beacons an access point sends in this "
                     "time. The receiver hears an access point on this channel, "
                     "and what it calls wide includes real Wi-Fi.".format(
                         heard, BEACON_INTERVAL * 1e3, heard, expected))
        if heard < 0.5 * expected:
            lines.append("  Only {:.0f}% of them, though: the receiver is on the "
                         "edge of hearing it, and anything weaker than the access "
                         "point will be missed. More gain would make this a "
                         "stronger test.".format(100.0 * heard / max(expected, 1)))
    else:
        lines.append("Receiver check: FAILED. {} wide bursts, none of them on the "
                     "{:.1f} ms rhythm an access point's beacons keep. If there is "
                     "an access point on this channel the receiver is not hearing "
                     "it, and nothing below can be trusted in either direction - "
                     "a quiet result here means a deaf receiver as easily as a "
                     "clean channel. Raise the gain (RF amp on, LNA 32 at 5 GHz) "
                     "and record again.".format(events, BEACON_INTERVAL * 1e3))

    if detector == "peak":
        lines.append("")
        lines.append("NOTE: a peak detector made this. The peak of 26 frames of "
                     "noise stands 7.5 dB over its own median where the mean of "
                     "the same 26 stands 3.5, so this recording gives up about "
                     "4 dB of sensitivity to anything narrow.")
    if first["step"] > 2e-3:
        lines.append("")
        lines.append("NOTE: {:.1f} ms a sweep is slower than a Wi-Fi frame, so a "
                     "busy channel puts a frame in nearly every sweep and hides "
                     "the gaps that narrowband energy is seen in. Recordings made "
                     "by the capture button with hackrf_stream keep every "
                     "spectrum instead.".format(first["step"] * 1e3))

    # Findings, each with what the retune said about it when there was one
    shift = None
    if len(halves) == 2 and first["tune"] is not None and halves[1]["tune"] is not None:
        shift = float(halves[1]["tune"]) - float(first["tune"])
    bins = first["frequencies"]
    tolerance = max(2.0 * abs(float(bins[1] - bins[0])) if bins.size > 1 else 0.0, 50e3)

    def unique(half, kind):
        # A bin that is always on is a finding in both lists, and belongs in
        # the first: drop it from the coming-and-going one
        if kind == "always":
            return half["always"]
        return [finding for finding in half["found"]
                if not any(abs(finding.centre_hz - steady.centre_hz) <= tolerance
                           for steady in half["always"])]

    def listed(kind):
        if shift is None:
            return [(finding, None) for finding in unique(first, kind)]
        return compare(unique(first, kind), unique(halves[1], kind), shift,
                       tolerance, always_on=(kind == "always"))

    on_air = []
    # Counted from the first half, since every spur is also in the second at
    # its new frequency; from the second only if the first had none
    own = {"first": 0, "second": 0}
    for kind, title in (("always", "Narrow and never off"),
                        ("found", "Narrow and coming and going")):
        entries = listed(kind)
        lines.append("")
        if not entries:
            lines.append("{}: nothing.".format(title))
            continue
        lines.append("{}:".format(title))
        for finding, verdict in entries:
            lines.append("  " + finding.describe())
            if verdict:
                lines.append("      " + verdict)
                if verdict.startswith("on the air"):
                    on_air.append(finding)
                elif verdict.startswith("the receiver's own"):
                    own["second" if "before the" in verdict else "first"] += 1
            else:
                on_air.append(finding)
    if shift is None:
        lines.append("")
        lines.append("NOTE: one tune only, so nothing above has been checked "
                     "against the receiver's own spurs - a pair either side of "
                     "the tune centre is the usual sign of one.")

    # What it comes to, said plainly
    lines.append("")
    lines.append("What this means:")
    if not heard:
        lines.append("  Nothing yet - the receiver check failed, so record again "
                     "with more gain before reading anything into this.")
        return lines
    lines.append("  Wi-Fi-wide energy filled {:.1f}% of the sweeps, which is "
                 "roughly the share of the time the channel was busy.".format(
                     100.0 * counts[WIDE] / total))
    spurs = own["first"] or own["second"]
    if spurs:
        lines.append("  {} always-on signal(s) did not stay put when the tune "
                     "moved, so they are the receiver's own and can be ignored."
                     .format(spurs))
    if on_air:
        best = max(on_air, key=lambda finding: finding.above_db)
        confirmed = "confirmed on the air" if shift is not None else "not yet checked by a retune"
        lines.append("  Something narrow, so not Wi-Fi, at {:.3f} MHz ({}). To "
                     "look at it, tune {:.3f} to {:.3f} MHz.".format(
                         best.centre_hz / 1e6, confirmed,
                         *(edge / 1e6 for edge in findings.aim(best.centre_hz, 20e6))))
    else:
        lines.append("  Nothing narrow was on the air while this recorded. That "
                     "is a real negative for anything narrow transmitting in the "
                     "channel's quiet moments; it says nothing about anything as "
                     "wide as a frame.")
    return lines


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="qspectrumanalyzer.interference",
        description="Say what in a saved recording was not Wi-Fi, by its width")
    parser.add_argument("recording", nargs="+", help="one or more recordings: the .json written beside each .f32, or an older .csv")
    parser.add_argument("--margin", type=float, default=None,
                        help="dB over a bin's own median before it counts as "
                             "carrying (default: from the sweep detector the "
                             "recording names)")
    parser.add_argument("--limit", type=int, default=12,
                        help="most findings to report")
    parser.add_argument("--retuned", default=None,
                        help="a second recording of the same channel with the "
                             "tune moved, to tell the air from the receiver")
    args = parser.parse_args(argv)

    for path in args.recording:
        if len(args.recording) > 1:
            print("=== {} ===".format(path))
        try:
            print("\n".join(report(path, limit=args.limit, margin=args.margin,
                                   retuned=args.retuned)))
        except (OSError, ValueError) as error:
            print("{}".format(error), file=sys.stderr)
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
