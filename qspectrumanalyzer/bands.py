"""Several bands swept as one, instead of a single start-stop range

A sweep's time goes on the spectrum it covers, so sweeping 2.4 and 5 GHz Wi-Fi
as two bands instead of everything from 2400 to 5850 MHz is 4.3 times faster
on a HackRF (measured: 10.1 sweeps a second against 2.3). hackrf_sweep takes
up to ten ranges and goes through them in order, one after another, so a
sweep still starts at the lowest band and ends at the top of the highest.

Nothing is measured between the bands. A sweep fills that stretch with NaN
bins at the same spacing, so the frequency axis stays evenly spaced (the
waterfall depends on it), the curve breaks there, and the waterfall shows a
blank strip, which is how the gap actually looks: unmeasured."""

import math
import re

import numpy as np

#: hackrf_sweep takes -f at most this many times
MAX_BANDS = 10


def parse_bands(text):
    """Bands in MHz from text such as "2400-2500, 5150-5850"

    Returns [(low, high), ...] sorted and with overlapping bands joined, or []
    for empty text. Raises ValueError saying what is wrong otherwise."""
    bands = []
    for part in re.split(r"[,;\s]+", text.strip()):
        if not part:
            continue
        match = re.fullmatch(r"(\d+(?:\.\d*)?)\s*[-:]\s*(\d+(?:\.\d*)?)", part)
        if not match:
            raise ValueError('"{}" is not a band; write it as low-high in MHz, '
                             'such as 2400-2500'.format(part))
        low, high = float(match.group(1)), float(match.group(2))
        if high <= low:
            raise ValueError('"{}" ends before it starts'.format(part))
        bands.append((low, high))
    bands = merge(bands)
    if len(bands) > MAX_BANDS:
        raise ValueError("{} bands, but a sweep can take at most {}".format(
            len(bands), MAX_BANDS))
    return bands


def format_bands(bands):
    """The text parse_bands() reads back as these bands"""
    return ", ".join("{:g}-{:g}".format(low, high) for low, high in bands)


def merge(bands):
    """Sorted, with bands that overlap or touch joined into one"""
    merged = []
    for low, high in sorted(bands):
        if merged and low <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], high))
        else:
            merged.append((low, high))
    return merged


def whole_steps(bands, step):
    """The bands as hackrf_sweep will sweep them, in MHz

    It takes whole MHz and sweeps whole steps from each band's start, so a
    band's top is rounded up to the step after it. Rounding can make two bands
    overlap, and overlapping ranges would sweep the overlap twice, so they are
    joined again afterwards."""
    swept = []
    for low, high in bands:
        low = math.floor(low)
        steps = max(1, math.ceil((high - low) / step))
        swept.append((low, low + steps * step))
    return merge(swept)


def fill_gaps(x, y, step):
    """x and y with NaN bins put in wherever the bins are further apart than one step

    x must be sorted. The bins put in are spaced evenly across the gap, as
    close to `step` as fits, so the whole axis stays evenly spaced to within a
    fraction of a bin."""
    jumps = np.flatnonzero(np.diff(x) > 1.5 * step)
    if not len(jumps):
        return x, y
    xs, ys, start = [], [], 0
    for jump in jumps:
        xs.append(x[start:jump + 1])
        ys.append(y[start:jump + 1])
        width = x[jump + 1] - x[jump]
        missing = int(round(width / step)) - 1
        xs.append(x[jump] + width * np.arange(1, missing + 1) / (missing + 1))
        ys.append(np.full(missing, np.nan, dtype=y.dtype))
        start = jump + 1
    xs.append(x[start:])
    ys.append(y[start:])
    return np.concatenate(xs), np.concatenate(ys)
