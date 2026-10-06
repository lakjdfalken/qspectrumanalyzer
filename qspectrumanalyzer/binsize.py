"""What a bin size means, drawn, and what changing it would do

The bin size is the one control that decides three things at once, and the
three pull against each other. It is the frequency resolution: the span is
cut into bins and each is one point on the trace. It is the time resolution,
because an FFT that splits the spectrum that finely has to look at 1 / bin
seconds of signal at once, and nothing shorter than that can be told apart.
And it is the noise each bin collects. A readout of figures says all of this
and explains none of it, so this window draws the span cut into its bins and
one frame against the pulse being hunted, says in sentences what follows,
and puts the neighbouring bin sizes beside this one so that turning the
control is a choice between rows rather than a guess.

The arithmetic is the backend's own - derive() and pulse_cost() - so the
window cannot describe one bin size while the run uses another.
"""

import math

from PySide6 import QtCore, QtGui, QtWidgets

from qspectrumanalyzer.backends import hackrf_stream as backend

#: A pulse to compare against when none has been named in the settings
SCALE_PULSE = 1e-6

#: FFT lengths either side of the current one that the table offers
NEIGHBOURS = 2


def as_hz(hz):
    if hz >= 1e6:
        return "{:g} MHz".format(round(hz / 1e6, 3))
    if hz >= 1e3:
        return "{:g} kHz".format(round(hz / 1e3, 3))
    return "{:g} Hz".format(round(hz, 1))


def as_seconds(seconds):
    for scale, unit in ((1.0, "s"), (1e-3, "ms"), (1e-6, "µs"), (1e-9, "ns")):
        if seconds >= scale or scale == 1e-9:
            return "{:.3g} {}".format(seconds / scale, unit)


def facts(rate, requested, low, high, pulse=0.0, window="hann", average=None):
    """Everything the window says, worked out without Qt so it can be checked

    `pulse` is the one named in the settings, in seconds, or 0 when none has
    been; a 1 us one is then used for scale and the result says so."""
    d = backend.derive(rate=rate, bin_hz=requested, low=low, high=high,
                       window=window, average=average)
    actual, n = d["bin_hz"], d["fft_size"]
    named = pulse > 0
    pulse = pulse if named else SCALE_PULSE
    cost = backend.PowerThread.pulse_cost(d["frame"], actual, pulse)

    best_n = backend.hackrf_stream.fast_fft_size(rate, 1.0 / pulse)
    best_cost = backend.PowerThread.pulse_cost(best_n / rate, rate / best_n, pulse)

    reach = backend.hackrf_stream.dc_spike_bins(window)
    tune = d["tune"]
    dc = (tune - (reach + 0.5) * actual, tune + (reach + 0.5) * actual)
    dc_on_screen = dc[1] > low and dc[0] < high
    half = backend.hackrf_stream.baseband_filter_bw(0.75 * rate) / 2.0

    rows = []
    # The best size for the pulse is offered too, however far off it is,
    # because that row is the answer to the question the table is asked
    sizes = {n * 2 ** step for step in range(-NEIGHBOURS, NEIGHBOURS + 1)} | {best_n}
    for m in sorted(sizes):
        if m < 16 or m > 2 ** 20:
            continue
        b = rate / m
        rows.append({
            "fft_size": m,
            "bin_hz": b,
            "bins": max(1, int(round(max(0.0, high - low) / b))),
            "frame": m / rate,
            "cost": backend.PowerThread.pulse_cost(m / rate, b, pulse),
            "noise_db": 10 * math.log10(b / actual),
            "now": m == n,
            "best": m == best_n,
        })

    return {
        "requested": requested, "actual": actual, "fft_size": n,
        "rate": rate, "low": low, "high": high,
        "bins": d["bins"], "frame": d["frame"], "sweep": d["sweep"],
        "tune": tune, "centred": d["centred"],
        "dc": dc if dc_on_screen else None, "dc_bins": 2 * reach + 1,
        "passband": (tune - half, tune + half),
        "pulse": pulse, "pulse_named": named, "cost": cost,
        "best_bin": rate / best_n, "best_cost": best_cost,
        "rows": rows,
    }


class FrequencyStrip(QtWidgets.QWidget):
    """The span cut into its bins, with the bins that are not the air shaded"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.f = None
        self.setMinimumHeight(64)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)

    def show_facts(self, f):
        self.f = f
        self.update()

    def paintEvent(self, event):
        f = self.f
        if f is None or f["high"] <= f["low"]:
            return
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing, False)
        pal = self.palette()
        metrics = p.fontMetrics()
        left, right = 4, self.width() - 4
        top, height = 4, self.height() - metrics.height() - 10
        low, high = f["low"], f["high"]

        def x(hz):
            return left + (hz - low) / (high - low) * (right - left)

        bin_hz = f["actual"]
        first = math.floor((low - f["tune"]) / bin_hz - 0.5)
        last = math.ceil((high - f["tune"]) / bin_hz + 0.5)
        width = (right - left) * bin_hz / (high - low)
        light = pal.color(QtGui.QPalette.Highlight)
        dark = QtGui.QColor(light).darker(140)
        if width >= 3:
            for k in range(first, last + 1):
                a = max(low, f["tune"] + (k - 0.5) * bin_hz)
                b = min(high, f["tune"] + (k + 0.5) * bin_hz)
                if b <= a:
                    continue
                p.fillRect(QtCore.QRectF(x(a), top, max(1.0, x(b) - x(a)), height),
                           light if k % 2 else dark)
        else:
            p.fillRect(QtCore.QRectF(left, top, right - left, height), light)
            p.setPen(pal.color(QtGui.QPalette.HighlightedText))
            p.drawText(QtCore.QRectF(left, top, right - left, height),
                       QtCore.Qt.AlignCenter,
                       "{:,} bins — too narrow to draw one by one".format(f["bins"]))

        shade = QtGui.QColor(pal.color(QtGui.QPalette.Window))
        shade.setAlpha(170)
        text = pal.color(QtGui.QPalette.WindowText)
        lo_pass, hi_pass = f["passband"]
        for a, b, label in ((low, lo_pass, "filter"), (hi_pass, high, "filter")):
            if b > a and a < high and b > low:
                rect = QtCore.QRectF(x(max(a, low)), top, x(min(b, high)) - x(max(a, low)), height)
                p.fillRect(rect, shade)
                p.setPen(text)
                if rect.width() > metrics.horizontalAdvance(label) + 4:
                    p.drawText(rect, QtCore.Qt.AlignCenter, label)
        if f["dc"] is not None:
            a, b = max(f["dc"][0], low), min(f["dc"][1], high)
            rect = QtCore.QRectF(x(a), top, max(2.0, x(b) - x(a)), height)
            p.fillRect(rect, QtGui.QBrush(text, QtCore.Qt.BDiagPattern))
            p.setPen(text)
            label = "DC"
            if rect.width() > metrics.horizontalAdvance(label) + 4:
                p.drawText(rect, QtCore.Qt.AlignCenter, label)

        p.setPen(text)
        base = top + height + 4
        p.drawText(QtCore.QRectF(left, base, right - left, metrics.height()),
                   QtCore.Qt.AlignLeft, "{:.3f} MHz".format(low / 1e6))
        p.drawText(QtCore.QRectF(left, base, right - left, metrics.height()),
                   QtCore.Qt.AlignRight, "{:.3f} MHz".format(high / 1e6))
        p.drawText(QtCore.QRectF(left, base, right - left, metrics.height()),
                   QtCore.Qt.AlignHCenter, "one bin = {}".format(as_hz(bin_hz)))
        p.end()


class TimeStrip(QtWidgets.QWidget):
    """One FFT frame drawn against the pulse, on the same time axis"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.f = None
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)

    def sizeHint(self):
        return QtCore.QSize(300, 3 * (self.fontMetrics().height() + 6) + 8)

    def minimumSizeHint(self):
        return self.sizeHint()

    def show_facts(self, f):
        self.f = f
        self.update()

    def paintEvent(self, event):
        f = self.f
        if f is None:
            return
        p = QtGui.QPainter(self)
        pal = self.palette()
        metrics = p.fontMetrics()
        row = metrics.height() + 6
        caption = max(metrics.horizontalAdvance("one frame"),
                      metrics.horizontalAdvance("the pulse")) + 10
        left, right = caption, self.width() - 4
        frame, pulse = f["frame"], f["pulse"]
        # A pulse many frames long is drawn whole with the frames ticked off
        # along it; a frame many pulses long is drawn whole with the pulse a
        # sliver inside it, which is the picture of the loss
        total = max(frame, pulse) * 1.1

        def w(seconds):
            return (right - left) * seconds / total

        text = pal.color(QtGui.QPalette.WindowText)
        light = pal.color(QtGui.QPalette.Highlight)
        p.setPen(text)
        p.drawText(QtCore.QRectF(0, 4, caption, row - 6),
                   QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter, "one frame")
        p.drawText(QtCore.QRectF(0, 4 + row, caption, row - 6),
                   QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter, "the pulse")

        frames = int(min(math.ceil(pulse / frame), 64)) if pulse > frame else 1
        for i in range(frames):
            rect = QtCore.QRectF(left + w(i * frame), 4, max(1.0, w(frame) - 1), row - 6)
            p.fillRect(rect, light if i % 2 == 0 else QtGui.QColor(light).darker(140))
        p.fillRect(QtCore.QRectF(left, 4 + row, max(1.0, w(pulse)), row - 6),
                   QtGui.QColor("#d08000"))

        p.setPen(text)
        if pulse < frame:
            share = 100.0 * pulse / frame
            note = "the pulse fills {:.0f}% of the frame".format(share)
        elif frames > 1:
            note = "the pulse spans {:.3g} frames".format(pulse / frame)
        else:
            note = "the pulse fills the frame"
        p.drawText(QtCore.QRectF(left, 4 + 2 * row, right - left, row),
                   QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter,
                   "frame {}, pulse {} — {}".format(
                       as_seconds(frame), as_seconds(pulse), note))
        p.end()


class BinSizeExplainer(QtWidgets.QWidget):
    """A window beside the plots that redraws as the bin size is turned

    `inputs` is called for the numbers it explains - rate, requested bin,
    span, window, average, and the sweep detector - so it always describes
    the controls as they stand rather than as they were when it opened."""

    def __init__(self, inputs, parent=None):
        super().__init__(parent, QtCore.Qt.Tool)
        self.inputs = inputs
        self.setWindowTitle(self.tr("What the bin size means"))
        self.resize(560, 700)

        outer = QtWidgets.QVBoxLayout(self)
        scroll = QtWidgets.QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        outer.addWidget(scroll)
        body = QtWidgets.QWidget()
        scroll.setWidget(body)
        column = QtWidgets.QVBoxLayout(body)

        # Rich text rather than setFont() throughout: a font set on a widget
        # is fixed at the size it was set at, and fontscale would scale one
        # made after the text size changed a second time
        self.title = QtWidgets.QLabel()
        self.title.setTextFormat(QtCore.Qt.RichText)
        column.addWidget(self.title)
        self.snapped = self.paragraph(column)

        column.addWidget(self.heading(self.tr("Frequency")))
        self.strip = FrequencyStrip()
        column.addWidget(self.strip)
        self.frequency = self.paragraph(column)

        column.addWidget(self.heading(self.tr("Time")))
        self.timeline = TimeStrip()
        column.addWidget(self.timeline)
        self.time = self.paragraph(column)

        pulse_row = QtWidgets.QHBoxLayout()
        pulse_row.addWidget(QtWidgets.QLabel(self.tr("Pulse you are hunting:")))
        self.pulse_box = QtWidgets.QDoubleSpinBox()
        self.pulse_box.setDecimals(2)
        self.pulse_box.setRange(0.0, 100000.0)
        self.pulse_box.setSuffix(" µs")
        self.pulse_box.setSpecialValueText(self.tr("not set"))
        self.pulse_box.setToolTip(self.tr(
            "The same setting as Pulse being hunted in Settings. Left at "
            "“not set”, a 1 µs pulse is used for scale."))
        self.pulse_box.setValue(QtCore.QSettings().value("hunt_pulse_us", 0.0, float))
        self.pulse_box.valueChanged.connect(self.on_pulse_changed)
        pulse_row.addWidget(self.pulse_box)
        pulse_row.addStretch(1)
        column.addLayout(pulse_row)

        column.addWidget(self.heading(self.tr("Noise")))
        self.noise = self.paragraph(column)

        column.addWidget(self.heading(self.tr("What changing it does")))
        self.table = QtWidgets.QLabel()
        self.table.setTextFormat(QtCore.Qt.RichText)
        column.addWidget(self.table)
        self.table_note = self.paragraph(column)

        column.addWidget(self.heading(self.tr("Choosing one")))
        self.choosing = self.paragraph(column)
        column.addStretch(1)

    def heading(self, text):
        label = QtWidgets.QLabel("<b>{}</b>".format(text.upper()))
        label.setStyleSheet("color: palette(mid); padding-top: 8px;")
        return label

    def paragraph(self, column):
        label = QtWidgets.QLabel()
        label.setWordWrap(True)
        label.setTextFormat(QtCore.Qt.RichText)
        column.addWidget(label)
        return label

    def on_pulse_changed(self, value):
        QtCore.QSettings().setValue("hunt_pulse_us", value)
        self.refresh()

    def showEvent(self, event):
        # The setting may have been changed in the Settings dialog meanwhile
        self.pulse_box.blockSignals(True)
        self.pulse_box.setValue(QtCore.QSettings().value("hunt_pulse_us", 0.0, float))
        self.pulse_box.blockSignals(False)
        self.refresh()
        super().showEvent(event)

    def refresh(self):
        if not self.isVisible():
            return
        given = self.inputs()
        try:
            f = facts(given["rate"], given["bin_hz"], given["low"], given["high"],
                      self.pulse_box.value() * 1e-6, given["window"], given["average"])
        except (ValueError, ZeroDivisionError, OverflowError, AttributeError):
            return
        self.show_facts(f, given["detector"])

    def show_facts(self, f, detector):
        tr = self.tr
        bin_hz, frame, pulse = f["actual"], f["frame"], f["pulse"]
        self.title.setText("<big><b>{}</b></big>".format(
            tr("What {} bins mean").format(as_hz(bin_hz))))

        if abs(f["requested"] - bin_hz) > 0.01 * bin_hz:
            sizes = ", ".join(as_hz(f["rate"] / 2 ** k) for k in range(4, 13))
            self.snapped.setText(tr(
                "You asked for {}, and the radio uses {}. The FFT length has "
                "to be a power of two, so at {} the bin sizes on offer are "
                "{}, and so on, halving each time. A request is rounded to "
                "the nearest of them.").format(
                    as_hz(f["requested"]), as_hz(bin_hz), as_hz(f["rate"]), sizes))
            self.snapped.show()
        else:
            self.snapped.hide()

        self.strip.show_facts(f)
        span = f["high"] - f["low"]
        lines = [tr("The {} span is cut into <b>{:,} bins</b> of {}. Each bin is "
                    "one point on the trace: all the power that falls anywhere "
                    "inside its {} is added up into one number. Two signals "
                    "closer together than about two bins ({}) merge into one "
                    "peak.").format(as_hz(span), f["bins"], as_hz(bin_hz),
                                    as_hz(bin_hz), as_hz(2 * bin_hz))]
        if f["dc"] is not None:
            lines.append(tr("The {} hatched bins at the centre are the receiver's "
                            "own carrier, drawn as a straight line rather than "
                            "measured.").format(f["dc_bins"]))
        lo_pass, hi_pass = f["passband"]
        outside = max(0.0, lo_pass - f["low"]) + max(0.0, f["high"] - hi_pass)
        if outside > bin_hz:
            lines.append(tr("The shaded {} at the edges is outside the receiver's "
                            "filter, which passes {:.3f}-{:.3f} MHz: those bins "
                            "slope away whatever the air is doing.").format(
                                as_hz(outside), lo_pass / 1e6, hi_pass / 1e6))
        self.frequency.setText(" ".join(lines))

        self.timeline.show_facts(f)
        which = tr("the pulse you are hunting") if f["pulse_named"] else \
            tr("a 1 µs pulse (none is set below, so this one is for scale)")
        lines = [tr("To split the spectrum into {} bins, each FFT has to look at "
                    "<b>{}</b> of signal at once. The frame is always 1 ÷ the "
                    "bin size: finer bins, longer frames. Nothing shorter than a "
                    "frame can be told apart in time.").format(
                        as_hz(bin_hz), as_seconds(frame))]
        if pulse < frame:
            lines.append(tr("For {}, the frame is too long: the pulse's energy "
                            "is shared with the silence around it, so it reads "
                            "<b>{:.1f} dB</b> weaker than it is.").format(which, f["cost"]))
        elif f["cost"] >= 0.5:
            lines.append(tr("For {}, time is fine, but a pulse that long only "
                            "occupies about {} of spectrum, less than a bin, so "
                            "each bin collects <b>{:.1f} dB</b> more noise than "
                            "the pulse fills.").format(which, as_hz(1.0 / pulse), f["cost"]))
        else:
            lines.append(tr("For {}, this is a match: the frame is about as long "
                            "as the pulse, so nothing is given up.").format(which))
        if detector != "peak" and f["sweep"] > pulse:
            lines.append(tr("The sweep detector is Mean, so on the trace a pulse "
                            "is also averaged over the whole {} sweep. Set it to "
                            "Peak in Settings when hunting pulses.").format(
                                as_seconds(f["sweep"])))
        self.time.setText(" ".join(lines))

        self.noise.setText(tr(
            "Each bin collects the noise from {} of spectrum. Halving the bin "
            "size takes 3 dB off the noise in every bin, so a steady narrow "
            "signal - a carrier - stands 3 dB further out of it, at the cost "
            "of a frame twice as long. A signal wider than a bin (Wi-Fi is "
            "20 MHz) gains nothing from smaller bins: its power per bin "
            "shrinks with the noise.").format(as_hz(bin_hz)))

        head = "<tr>{}<th></th></tr>".format("".join(
            "<th align=right>&nbsp;{}&nbsp;</th>".format(name) for name in (
                tr("bin"), tr("bins"), tr("frame"),
                tr("{} pulse").format(as_seconds(pulse)), tr("noise/bin"))))
        body = []
        for r in f["rows"]:
            mark = []
            if r["now"]:
                mark.append(tr("◀ now"))
            if r["best"]:
                mark.append(tr("★ best for the pulse"))
            cells = (as_hz(r["bin_hz"]), "{:,}".format(r["bins"]), as_seconds(r["frame"]),
                     "−{:.1f} dB".format(r["cost"]) if r["cost"] >= 0.05 else "0 dB",
                     "{:+.0f} dB".format(r["noise_db"]) if r["noise_db"] else "–",
                     " ".join(mark))
            style = " style='font-weight:bold'" if r["now"] else ""
            row = "".join("<td align=right{}>&nbsp;{}&nbsp;</td>".format(style, c)
                          for c in cells[:5])
            row += "<td{}>&nbsp;{}</td>".format(style, cells[5])
            body.append("<tr>{}</tr>".format(row))
        self.table.setText("<table cellspacing=0>{}{}</table>".format(head, "".join(body)))
        self.table_note.setText(tr(
            "Rows run from coarse to fine, each one step of the Bin size "
            "control from the next - apart from the \u2605 row, which is shown "
            "however far away it is. "
            "<i>pulse</i> is what the pulse loses at that size; <i>noise/bin</i> "
            "is the noise in each bin against now - lower means steady signals "
            "stand further out."))

        self.choosing.setText(tr(
            "Pick it for what you are hunting. <b>Short pulses</b> (radar): about "
            "1 ÷ the pulse width - for {} that is {}, costing {:.1f} dB. "
            "<b>Steady narrow signals</b> (carriers): "
            "smaller bins, as fine as you can wait for. <b>Wide signals</b> "
            "(Wi-Fi, a whole channel): enough bins to see the shape, and the "
            "rest does not matter.").format(
                as_seconds(pulse), as_hz(f["best_bin"]), f["best_cost"]))
