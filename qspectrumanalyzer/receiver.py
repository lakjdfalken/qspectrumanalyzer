"""Whether the receiver is set up to hear what it is pointed at

The known-answer checks that otherwise get learned by hand, one evening at a
time, done by a button:

The gain. Turning it up by a known amount and watching what follows is the
one test that needs no reference signal. Where the radio's own noise, from
the stages after the gain, is what sets the floor, more gain lifts the signals
and leaves that noise behind, so they stand further out of it: the gain was
too low. Where the floor rises as much as the gain did, the noise is arriving
with the signal and more gain shows nothing new. And where the strongest
signal rises by less than the gain did, the receiver has run out of room and
is compressing it: the gain is too high.

The access point. On a Wi-Fi channel a beacon goes out every 102.4 ms
whatever else happens, so finding that rhythm in the wide bursts says the
receiver hears the access point at all - see interference.beacons().

Nothing here imports Qt.
"""

import numpy as np

from qspectrumanalyzer import interference

#: How far the gain is stepped either side of where it is, in dB
STEP_DB = 10.0

#: How much of a step a level may fall short of and still count as following
#: it. Generous, because a few sweeps of noise wander by a decibel or two
SLACK_DB = 3.0

#: How far over the floor the strongest signal has to stand before its rise is
#: worth reading: below this it is mostly noise and rises with the floor
SIGNAL_DB = 10.0

#: Where Wi-Fi is, in Hz: 2.4 GHz, 5 GHz, and 6 GHz
WIFI_BANDS = ((2400e6, 2484e6), (5150e6, 5895e6), (5925e6, 7125e6))


def levels(rows):
    """The floor and the strongest steady signal in a stack of sweeps, in dB

    The floor is the median across the span of each bin's median down the
    sweeps: what the span sits at when nothing is on. The strongest steady
    signal is the loudest bin's median, which only something on for more than
    half the sweeps can lift. A busier statistic was tried and read traffic
    instead of gain: on a Wi-Fi channel the loudest moments of two seconds
    differ by more between one two seconds and the next than a 10 dB gain
    step moves them, and the check called a quieter spell "overload". Sweeps
    of another length - a tune that changed under the check - are left out
    rather than mixed in."""
    lengths = [len(row) for row in rows]
    if not lengths:
        raise ValueError("no sweeps arrived")
    common = max(set(lengths), key=lengths.count)
    stack = np.array([row for row in rows if len(row) == common], dtype=np.float64)
    medians = np.median(stack, axis=0)
    floor = float(np.median(medians))
    strongest = float(np.max(medians))
    return floor, strongest, len(stack)


def judge(points, current, step=STEP_DB, slack=SLACK_DB, signal=SIGNAL_DB,
          names=None):
    """Say whether the gain `current` is too low, too high or right

    `points` maps gain to (floor, strongest) as levels() measured them, and
    holds `current` and either or both of the gains `step` either side.
    `names` may map a gain to how the radio divided it between its stages,
    which matters: a lower total can mean more of the later stage, and a
    higher floor than the next gain up.
    Returns (verdict, suggestion, lines): verdict is "low", "high" or "good",
    suggestion the gain to move to or None, and lines say why in words."""
    gains = sorted(points)
    lines = []
    for gain in gains:
        floor, strongest = points[gain]
        lines.append("  at {}: noise floor {:+.1f} dB, strongest steady signal "
                     "{:+.1f} dB".format((names or {}).get(gain, "{:g} dB".format(gain)),
                                         floor, strongest))

    def rise(low, high):
        """How far the floor and the strongest rose from `low` to `high`,
        against how far the gain did, and whether there is a signal to read"""
        (f0, s0), (f1, s1) = points[low], points[high]
        return high - low, f1 - f0, s1 - s0, s0 - f0 >= signal

    below = [gain for gain in gains if gain < current]
    above = [gain for gain in gains if gain > current]
    floor, strongest = points[current]
    if strongest - floor < signal:
        lines.append("Nothing steady stood {:g} dB over the noise, so overload "
                     "could not be tested - signals that come and go change "
                     "more between one setting and the next than the gain "
                     "does.".format(signal))

    # Compressing already: from the step below to here, the strongest signal
    # did not keep up with the gain
    if below:
        moved, floor_up, strongest_up, readable = rise(below[-1], current)
        if readable and strongest_up < moved - slack:
            lines.append("From {:g} to {:g} dB the strongest steady signal rose {:.1f} dB "
                         "for {:g} dB of gain: the receiver is running out of "
                         "room and squashing it.".format(
                             below[-1], current, strongest_up, moved))
            return "high", below[-1], lines

    if above:
        moved, floor_up, strongest_up, readable = rise(current, above[0])
        compressing = readable and strongest_up < moved - slack
        if floor_up < moved - slack and not compressing:
            lines.append("From {:g} to {:g} dB the noise floor rose only {:.1f} dB "
                         "for {:g} dB of gain, so signals would stand {:.1f} dB "
                         "further out of the noise: the radio's own noise is what "
                         "limits you now.".format(current, above[0], floor_up,
                                                  moved, moved - floor_up))
            return "low", above[0], lines
        if compressing:
            lines.append("At {:g} dB the strongest steady signal would rise only {:.1f} "
                         "dB for {:g} dB more gain: this is as high as it can "
                         "usefully go.".format(above[0], strongest_up, moved))
        else:
            lines.append("From {:g} to {:g} dB the noise rose nearly as much as "
                         "the gain ({:.1f} of {:g} dB): the noise is mostly "
                         "arriving with the signal, and more gain would lift "
                         "signals out of it by only {:.1f} dB.".format(
                             current, above[0], floor_up, moved,
                             max(moved - floor_up, 0.0)))
    elif below:
        moved, floor_up, _, _ = rise(below[-1], current)
        if floor_up < moved - slack:
            lines.append("This is the most gain the radio has, and it still "
                         "needs it: from {:g} dB the floor rose only {:.1f} dB "
                         "for {:g} dB of gain.".format(below[-1], floor_up, moved))
        else:
            lines.append("From {:g} dB the noise rose as much as the gain: the "
                         "lower setting would show the same.".format(below[-1]))
    return "good", None, lines


def on_wifi(low, high, bands=WIFI_BANDS):
    """Whether a tune from `low` to `high` Hz lies on a Wi-Fi band"""
    return any(low < top and high > bottom for bottom, top in bands)


def beacon_check(times, frequencies, powers, passband=None, detector="mean"):
    """Beacons heard, beacons expected, and wide bursts, in a kept recording

    The same reading the interference report starts with, on spectra kept
    while the check ran. Bins outside `passband` are the baseband filter's
    roll-off and are left out, as interference.analyse() leaves them out."""
    frequencies = np.asarray(frequencies)
    powers = np.asarray(powers)
    if passband:
        keep = (frequencies >= passband[0]) & (frequencies <= passband[1])
        if keep.sum() > 1:
            powers = powers[:, keep]
    margin = interference.MARGINS.get(detector, interference.MARGIN)
    labels, _, _ = interference.classify(powers, margin=margin)
    return interference.beacons(times, labels)
