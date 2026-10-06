"""Writing a recording down, and reading it back

A recording is a spectrogram: one row per delivered sweep, one column per bin,
plus the time each row arrived. It was written as CSV, which is readable by
anything and costs four times what the numbers do — twenty seconds of a 20 MHz
tune is 160 MB of ASCII for 40 MB of float32, and reading it back parses seven
million decimal strings. Captures meant to be taken routinely cannot be shaped
like that, so this writes the array as it sits in memory and describes it in a
sidecar.

On the sidecar and SigMF
------------------------

SigMF is the standard for RF recordings and this is deliberately not it, which
is worth being plain about rather than quietly implying otherwise. SigMF
describes *time series samples* — a `.sigmf-data` of digitized IQ and a
`.sigmf-meta` of JSON — and a spectrogram is not that. It is what you compute
from that. There is no conforming way to put one in a SigMF recording, so
calling this SigMF would be claiming a compatibility no reader would find.

What it does instead is borrow the vocabulary: the global/captures/annotations
shape, and the `core:` names for the things that mean the same in both, so
that a person who knows SigMF can read this without a key and so that the day
this program writes IQ — which the frame-timing work will want, since SIFS is
16 us and no spectrogram resolves it — the words already match. Everything
that has no SigMF meaning sits under `qsa:` where it cannot be mistaken for a
field a SigMF reader should understand, and `qsa:conforms_to_sigmf` is false.

Nothing here imports Qt.
"""

import json
import os

import numpy as np


#: The sidecar names this so a reader need not guess, and so that the layout
#: can change later without old files becoming unreadable
LAYOUT = 1

#: One row of the data file: when the sweep arrived, then a power for every
#: bin. The time is float64 because it is a unix time and float32 gives that a
#: quarter of a second of resolution; the powers are float32 because they are
#: decibels whose seventh significant digit is far under the noise, which is
#: the same choice the recording in memory makes.
TIME_DTYPE = "<f8"
POWER_DTYPE = "<f4"


def row_dtype(bins):
    """How one sweep sits in the data file"""
    return np.dtype([("time_s", TIME_DTYPE), ("power_db", POWER_DTYPE, (int(bins),))])


def paths_for(path):
    """(sidecar, data) for a path named as either of them"""
    stem, extension = os.path.splitext(path)
    if extension == ".f32":
        return stem + ".json", path
    if extension != ".json":
        stem = path
    return stem + ".json", stem + ".f32"


def write(path, times, frequencies, powers, meta=None):
    """Write a recording as a binary array and a JSON sidecar

    `path` may name either file or neither; both are written beside each other.
    Returns (sidecar, data, sweeps, bins)."""
    times = np.asarray(times, dtype=np.float64)
    powers = np.asarray(powers)
    frequencies = np.asarray(frequencies, dtype=np.float64)
    sweeps = min(len(times), len(powers))
    if not sweeps or not frequencies.size:
        raise ValueError("nothing to write")
    times, powers = times[:sweeps], powers[:sweeps]
    bins = powers.shape[1]
    if bins != frequencies.size:
        raise ValueError("{} bins but {} frequencies".format(bins, frequencies.size))

    sidecar, data = paths_for(path)
    rows = np.empty(sweeps, dtype=row_dtype(bins))
    rows["time_s"] = times
    rows["power_db"] = powers
    with open(data, "wb") as handle:
        rows.tofile(handle)

    step = float(np.median(np.diff(frequencies))) if bins > 1 else 0.0
    seconds = float(times[-1] - times[0]) if sweeps > 1 else 0.0
    document = {
        "global": {
            "core:datatype": POWER_DTYPE.replace("<f4", "rf32_le"),
            "core:num_channels": int(bins),
            "core:frequency": float((frequencies[0] + frequencies[-1]) / 2),
            "core:sample_rate": (sweeps - 1) / seconds if seconds > 0 else 0.0,
            "core:description": "A spectrogram, not a sample stream: one row "
                                "per delivered sweep, one column per bin. The "
                                "core: names are borrowed from SigMF because "
                                "they mean the same thing here; this is not a "
                                "SigMF recording and no SigMF reader will "
                                "open it.",
            "qsa:conforms_to_sigmf": False,
            "qsa:kind": "spectrogram",
            "qsa:layout": LAYOUT,
            "qsa:row": "one {} time_s then {} {} power_db, C order".format(
                TIME_DTYPE, bins, POWER_DTYPE),
            "qsa:sweeps": int(sweeps),
            "qsa:bins": int(bins),
            "qsa:frequency_start_hz": float(frequencies[0]),
            "qsa:frequency_step_hz": step,
            "qsa:data_file": os.path.basename(data),
        },
        "captures": [{
            "core:sample_start": 0,
            "core:frequency": float((frequencies[0] + frequencies[-1]) / 2),
        }],
        "annotations": [],
    }
    document["global"].update(meta or {})
    with open(sidecar, "w") as handle:
        json.dump(document, handle, indent=2, sort_keys=True)
        handle.write("\n")
    return sidecar, data, sweeps, bins


def read(path):
    """Read a recording back

    Returns (times, frequencies, powers, header, meta) — the header being
    lines of text, so that a report can print what a recording was taken under
    whether it came from a sidecar or from the CSV this used to be written as,
    and the meta being the sidecar itself for the things a reader has to act
    on rather than print."""
    sidecar, data = paths_for(path)
    with open(sidecar) as handle:
        document = json.load(handle)
    top = document.get("global", {})
    bins = int(top["qsa:bins"])
    start = float(top["qsa:frequency_start_hz"])
    step = float(top["qsa:frequency_step_hz"])

    beside = os.path.join(os.path.dirname(sidecar) or ".",
                          top.get("qsa:data_file") or os.path.basename(data))
    rows = np.fromfile(beside, dtype=row_dtype(bins))
    if not rows.size:
        raise ValueError("{}: no sweeps in it".format(beside))

    frequencies = start + np.arange(bins) * step
    powers = np.asarray(rows["power_db"], dtype=np.float64)
    return np.asarray(rows["time_s"]), frequencies, powers, header_lines(top), top


def header_lines(top):
    """The sidecar as the lines of text the CSV used to carry at its top"""
    lines = [str(top.get("qsa:recorder", "QSpectrumAnalyzer recording"))]
    for key in ("core:datetime", "qsa:settings", "qsa:sweep_detector"):
        if top.get(key):
            name = key.split(":", 1)[1].replace("_", " ")
            lines.append("{} {}".format(name, top[key]))
    lines.append("{} sweeps x {} bins".format(
        top.get("qsa:sweeps", "?"), top.get("qsa:bins", "?")))
    return lines
