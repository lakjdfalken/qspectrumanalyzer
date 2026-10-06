import collections, math, time

import numpy as np
from PySide6 import QtCore, QtGui, QtWidgets
import pyqtgraph as pg

from hackrf_stream.dsp import noise_ceiling
from qspectrumanalyzer.constants import TAP_CAPACITY
from qspectrumanalyzer.data import HistoryBuffer

# Basic PyQtGraph settings
#
# Antialiasing is off globally, which keeps the axes and the crosshair cheap,
# and is turned back on per curve when the setting asks for it. Row-major
# image order lets the waterfall hand its history buffer to ImageItem without
# transposing (and copying) it on every frame.
pg.setConfigOptions(antialias=False, imageAxisOrder='row-major')


def zoom_pixmap(glyph, size=16):
    """A round button face carrying one glyph"""
    ratio = 2
    pixmap = QtGui.QPixmap(size * ratio, size * ratio)
    pixmap.setDevicePixelRatio(ratio)
    pixmap.fill(QtCore.Qt.transparent)
    painter = QtGui.QPainter(pixmap)
    painter.setRenderHint(QtGui.QPainter.Antialiasing)
    painter.setPen(QtGui.QPen(QtGui.QColor(210, 210, 210), 1.2))
    painter.setBrush(QtGui.QColor(40, 40, 40, 210))
    painter.drawEllipse(QtCore.QRectF(0.8, 0.8, size - 1.6, size - 1.6))
    font = painter.font()
    font.setPixelSize(int(size * 0.72))
    font.setBold(True)
    painter.setFont(font)
    painter.drawText(QtCore.QRectF(0, 0, size, size), QtCore.Qt.AlignCenter, glyph)
    painter.end()
    return pixmap


def time_length(seconds):
    """A length of time in whichever unit reads without leading zeros"""
    if seconds < 1e-3:
        return "{:.2f} us".format(seconds * 1e6)
    if seconds < 1.0:
        return "{:.3f} ms".format(seconds * 1e3)
    return "{:.3f} s".format(seconds)


class RelativeTimeAxis(pg.AxisItem):
    """A time axis labelled against a moving reference

    The scope's data is stamped with the time since the run started, and after
    a few minutes that is five digits before anything that changes inside a
    window a millisecond wide — "3.999952" is not a number anybody can measure
    a burst against. A scope does not show elapsed time; it shows time either
    side of now, or either side of whatever the cursor is parked on. Only the
    labels are moved, so the data underneath keeps the coordinates it was
    given and nothing has to be handed to the curves again."""

    #: Divisor and name of each unit the labels may be written in
    UNITS = ((1.0, "s"), (1e-3, "ms"), (1e-6, "\u00b5s"))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.reference = 0.0
        self.factor = 1.0
        self.enableAutoSIPrefix(False)

    def unit_for(self, span):
        """The unit that writes a span of this size in readable numbers"""
        for factor, name in self.UNITS:
            if span >= factor * 0.999:
                return factor, name
        return self.UNITS[-1]

    def configure(self, reference, span):
        """Point the labels at a reference, in a unit that suits the span

        Called from the redraw rather than from tickStrings(), because it can
        change the axis label and that must not happen while painting."""
        factor, name = self.unit_for(abs(span))
        if reference == self.reference and factor == self.factor:
            return
        self.reference, self.factor = reference, factor
        self.setLabel(text=self.labelText, units=name)
        self.picture = None
        self.update()

    def tickStrings(self, values, scale, spacing):
        """Label each tick by how far it is from the reference"""
        if not values:
            return []
        step = abs(spacing) / self.factor
        decimals = 0 if step >= 1 else min(4, int(math.ceil(-math.log10(step))))
        return ["{:.{}f}".format((v - self.reference) / self.factor, decimals)
                for v in values]


class RedrawThrottle:
    """Coalesce redraws down to a maximum rate

    A backend can deliver sweeps far faster than any screen can show them:
    hackrf_sweep runs at ~400 per second, and at that rate redrawing on every
    sweep asks for several times more work than one core can do, so the GUI
    falls behind and stops responding. Frames drawn faster than the display
    refreshes are discarded by the compositor anyway, so drawing them buys
    nothing at all.

    Only drawing is throttled. Every sweep still reaches DataStorage, so the
    history, the average and the peak hold see all of the data; what is
    dropped is redundant repaints of data that is about to be overwritten."""
    def __init__(self, max_refresh_rate, flush):
        self._flush = flush
        self.set_max_refresh_rate(max_refresh_rate)
        self._dirty = set()
        self._storage = None
        self._last_draw = 0.0
        #: Browsing recorded sweeps, so the live view is held still
        self.frozen = False
        #: Not on screen at all, so drawing it would be work for nobody
        self.hidden = False
        self._timer = QtCore.QTimer()
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.flush_now)

    @property
    def stalled(self):
        """Whether anything is currently holding drawing back"""
        return self.frozen or self.hidden

    def schedule(self, kind, data_storage):
        """Mark one kind of curve as needing a redraw"""
        self._storage = data_storage
        self._dirty.add(kind)

        if self.stalled:
            # Keep noting what is stale, but leave the plot alone until
            # whatever is holding it back lets go
            return

        if self._interval <= 0:
            self.flush_now()
            return

        now = time.monotonic()
        due = self._last_draw + self._interval
        if now >= due:
            self.flush_now()
        elif not self._timer.isActive():
            # Draw the newest data once the rate limit allows it. Anything
            # arriving before then just overwrites what is pending.
            self._timer.start(max(0, int((due - now) * 1000)))

    def set_frozen(self, frozen):
        """Stop drawing (while recorded sweeps are being browsed)"""
        self.frozen = frozen
        self.resume_or_hold()

    def set_hidden(self, hidden):
        """Stop drawing (while the plot is not on screen)"""
        self.hidden = hidden
        self.resume_or_hold()

    def resume_or_hold(self):
        """Act on whatever the two holds now add up to"""
        if self.stalled:
            self._timer.stop()
        else:
            self.flush_now()

    def set_max_refresh_rate(self, max_refresh_rate):
        """Change the rate limit"""
        self.max_refresh_rate = max_refresh_rate
        self._interval = 1.0 / max_refresh_rate if max_refresh_rate > 0 else 0.0

    def flush_now(self):
        """Redraw everything that is pending"""
        if self._storage is None or not self._dirty:
            return
        dirty, storage = self._dirty, self._storage
        self._dirty = set()
        self._flush(storage, dirty)
        # Timed from the end of the draw, not the start. A draw that overruns
        # the interval would otherwise already be due again the moment it
        # finished, and the next sweep to arrive would start another one
        # straight away, leaving the GUI thread doing nothing but drawing.
        self._last_draw = time.monotonic()

    def reset(self):
        """Forget anything pending (used when the plot is cleared)"""
        self._timer.stop()
        self._dirty = set()
        self._storage = None
        self._last_draw = 0.0


class ThrottledPlotWidget:
    """A plot whose redraws are coalesced by a RedrawThrottle

    Also owns the Y axis, because pyqtgraph's own auto range fits the data
    exactly and so has to move whenever the data does. See fit_y_range()."""

    #: dB the Y axis snaps to, and the headroom kept above and below the data
    Y_STEP = 10
    Y_MARGIN = 5
    #: Seconds a range has to stay too large before it is pulled in. Growing is
    #: immediate — a signal must never run off the top of the plot — but a peak
    #: that dips for one sweep should not drag the axis in and straight back out.
    Y_SHRINK_DELAY = 2.0

    def __init__(self, layout, max_refresh_rate=60):
        if not isinstance(layout, pg.GraphicsLayoutWidget):
            raise ValueError("layout must be instance of pyqtgraph.GraphicsLayoutWidget")

        self.layout = layout
        self.throttle = RedrawThrottle(max_refresh_rate, self.draw)

        #: False once the user has zoomed or panned the Y axis themselves
        self.auto_y = True
        self.y_range = None
        self.y_oversized_since = None

    def watch_y_axis(self):
        """Follow what the user does to the Y axis (call once self.plot exists)"""
        self.plot.vb.sigRangeChangedManually.connect(self.on_range_changed_manually)
        self.plot.vb.sigStateChanged.connect(self.on_view_state_changed)

    def on_range_changed_manually(self, *args):
        """Stop rescaling the Y axis once the user has taken hold of it"""
        if not self.plot.vb.autoRangeEnabled()[1]:
            self.auto_y = False

    def on_view_state_changed(self, *args):
        """Rescale again when the view's own auto range is switched back on

        That is what the plot's A button and the View All menu entry do, and
        so it is the way back from a manual zoom."""
        if self.plot.vb.autoRangeEnabled()[1]:
            self.auto_y = True
            self.y_range = None

    def reset_y_range(self):
        """Forget the range, so the next data chooses a fresh one"""
        self.y_range = None
        self.y_oversized_since = None

    def fit_y_range(self, low, high):
        """Fit the Y axis to a span of data, in whole steps

        Fitting the data exactly means moving whenever the data moves, and a
        noise floor moves on every sweep. That shows as a trace that vibrates
        instead of one that sits still, and each move costs an axis relayout
        and a repaint of everything in the window — at a hundred sweeps a
        second, enough to make the whole display stutter.

        So the range is snapped to whole steps and kept until the data
        actually leaves it, which is also how a bench analyser behaves."""
        if not self.auto_y or low is None or high is None:
            return
        if not (math.isfinite(low) and math.isfinite(high)):
            return

        step, margin = self.Y_STEP, self.Y_MARGIN
        bottom = math.floor((low - margin) / step) * step
        top = math.ceil((high + margin) / step) * step
        if top - bottom < step:
            top = bottom + step

        target = (bottom, top)
        current = self.y_range
        if current is not None:
            if bottom >= current[0] and top <= current[1]:
                # The data still fits. Pulling the range in is only worth a
                # relayout if it is more than a step too big, and only once it
                # has stayed that way, so that a peak dipping for a sweep or a
                # noise floor wandering over a step boundary changes nothing.
                if (current[1] - current[0]) - (top - bottom) < step:
                    self.y_oversized_since = None
                    return
                now = time.monotonic()
                if self.y_oversized_since is None:
                    self.y_oversized_since = now
                if now - self.y_oversized_since < self.Y_SHRINK_DELAY:
                    return
            else:
                # Widen at once, and to the union of the two, so that a range
                # just pulled in is not immediately pushed back out
                target = (min(bottom, current[0]), max(top, current[1]))

            self.y_oversized_since = None
            if target == current:
                return

        self.y_range = target
        self.plot.vb.setRange(yRange=target, padding=0)

    def draw(self, data_storage, dirty):
        """Redraw whatever the throttle has been holding"""
        raise NotImplementedError

    def set_frozen(self, frozen):
        """Stop redrawing (while recorded sweeps are being browsed)"""
        self.throttle.set_frozen(frozen)

    def set_hidden(self, hidden):
        """Stop redrawing (while this plot is not on screen)

        A hidden plot is still fed, so that what it holds does not go stale
        while it is away, but nothing is painted until it comes back."""
        self.throttle.set_hidden(hidden)

    def cache_axes(self):
        """Let Qt keep each axis as a pixmap instead of redrawing it per frame

        With a grid switched on, pyqtgraph's axis bounding rect is expanded to
        cover the whole plot, so anything changing inside the view — the trace,
        on every single frame — marks the axis dirty as well, and it replays
        its whole recorded picture: ticks, numbers, labels and grid lines,
        about a millisecond a time. Nothing about the axis actually changed.

        Measured at 512 bins and 60 frames a second, that replay was 54% of
        everything the GUI thread did; cached it is 1%. The cache is dropped
        whenever the axis invalidates itself, which is already what happens
        when the range moves, so the numbers still follow the data."""
        for name in ("left", "bottom", "right", "top"):
            axis = self.plot.getAxis(name)
            if axis is not None:
                axis.setCacheMode(
                    QtWidgets.QGraphicsItem.CacheMode.DeviceCoordinateCache)

    #: What one press of a zoom button multiplies the visible span by
    ZOOM_STEP = 1.5

    def add_zoom_buttons(self):
        """Put - and + buttons in the plot's bottom left corner

        Scroll to zoom is most of a touchpad's problem with these plots: the
        gesture is easy to start by accident, hard to stop where you meant to,
        and on some touchpads arrives as one enormous jump."""
        self.zoom_out_button = pg.ButtonItem(zoom_pixmap("\u2212"), 15, self.plot)
        self.zoom_in_button = pg.ButtonItem(zoom_pixmap("+"), 15, self.plot)
        self.zoom_out_button.setToolTip("Show more")
        self.zoom_in_button.setToolTip("Show less")
        self.zoom_out_button.clicked.connect(lambda *_: self.zoom(self.ZOOM_STEP))
        self.zoom_in_button.clicked.connect(lambda *_: self.zoom(1 / self.ZOOM_STEP))
        self.plot.geometryChanged.connect(self.place_zoom_buttons)
        self.place_zoom_buttons()

    def place_zoom_buttons(self):
        """Keep the zoom buttons in the corner, clear of the auto range button"""
        button = getattr(self, "zoom_out_button", None)
        if button is None:
            return
        height = self.plot.mapRectFromItem(button, button.boundingRect()).height()
        y = self.plot.size().height() - height
        self.zoom_out_button.setPos(19, y)
        self.zoom_in_button.setPos(37, y)

    def zoom(self, scale):
        """Scale what the X axis shows about the middle of the view"""
        low, high = self.plot.vb.viewRange()[0]
        middle, half = (low + high) / 2, (high - low) * scale / 2
        self.plot.vb.setXRange(middle - half, middle + half, padding=0)

    def set_max_refresh_rate(self, max_refresh_rate):
        """Change how often this plot may be redrawn"""
        self.throttle.set_max_refresh_rate(max_refresh_rate)


class SpectrumPlotWidget(ThrottledPlotWidget):
    """Main spectrum plot"""

    #: Curves that change slowly enough not to need drawing on every frame,
    #: and how often they are drawn instead. A max hold only ever grows, a min
    #: hold only ever shrinks and an average converges, so at a hundred sweeps
    #: a second they are redrawn dozens of times between visible changes —
    #: several curves' worth of path building and repainting for a picture
    #: that is the same one. The live trace is what has to keep up.
    SLOW_CURVES = frozenset(("peak_hold_max", "peak_hold_min", "average", "baseline"))
    SLOW_INTERVAL = 0.1

    #: kind -> (attribute holding its on/off flag, attribute holding its curve,
    #: attribute on DataStorage holding its data). Persistence has neither a
    #: single curve nor a single array, so it carries None twice and is looked
    #: up through curves_for() and its own deque.
    CURVES = {
        "plot": ("main_curve", "curve", "y"),
        "peak_hold_max": ("peak_hold_max", "curve_peak_hold_max", "peak_hold_max"),
        "peak_hold_min": ("peak_hold_min", "curve_peak_hold_min", "peak_hold_min"),
        "average": ("average", "curve_average", "average"),
        "baseline": ("baseline", "curve_baseline", "baseline"),
        "persistence": ("persistence", None, None),
    }

    def __init__(self, layout, max_refresh_rate=60, antialias=True):
        super().__init__(layout, max_refresh_rate)
        self.antialias = antialias

        # How many samples pyqtgraph should keep per pixel when auto
        # downsampling. Its default is 5, and with peak downsampling that
        # draws ten points into every pixel column: nine of them land on top
        # of each other and cost paint time for nothing. Peak downsampling
        # keeps the minimum and the maximum of each bin, so one bin per
        # physical pixel already draws the full envelope, narrow spikes
        # included. That is a factor of devicePixelRatio, since the factor is
        # applied to the widget's logical width.
        try:
            self.downsample_factor = max(1.0, float(layout.devicePixelRatioF()))
        except AttributeError:
            self.downsample_factor = 1.0

        self.main_curve = True
        self.main_color = pg.mkColor("y")
        self.persistence = False
        self.persistence_length = 5
        self.persistence_decay = "exponential"
        self.persistence_color = pg.mkColor("g")
        self.persistence_data = None
        self.persistence_curves = None
        self.peak_hold_max = False
        self.peak_hold_max_color = pg.mkColor("r")
        self.peak_hold_min = False
        self.peak_hold_min_color = pg.mkColor("b")
        self.average = False
        self.average_color = pg.mkColor("c")
        self.baseline = False
        self.baseline_color = pg.mkColor("m")
        #: When each slow curve was last queued, so it can be held back
        self.slow_drawn = {}

        self.create_plot()

    def create_plot(self):
        """Create main spectrum plot"""
        self.posLabel = self.layout.addLabel(row=0, col=0, justify="right")
        self.plot = self.layout.addPlot(row=1, col=0)
        self.plot.showGrid(x=True, y=True)
        self.plot.setLabel("left", "Power", units="dB")
        self.plot.setLabel("bottom", "Frequency", units="Hz")
        self.plot.setLimits(xMin=0)
        self.plot.showButtons()

        # Draw only what is visible, and only as many points as there are
        # pixels to draw them on
        self.plot.setDownsampling(auto=True, mode="peak")
        self.plot.setClipToView(True)

        self.create_baseline_curve()
        self.create_persistence_curves()
        self.create_average_curve()
        self.create_peak_hold_min_curve()
        self.create_peak_hold_max_curve()
        self.create_main_curve()

        # Create crosshair
        self.vLine = pg.InfiniteLine(angle=90, movable=False)
        self.vLine.setZValue(1000)
        self.hLine = pg.InfiniteLine(angle=0, movable=False)
        self.vLine.setZValue(1000)
        self.plot.addItem(self.vLine, ignoreBounds=True)
        self.plot.addItem(self.hLine, ignoreBounds=True)
        self.mouseProxy = pg.SignalProxy(self.plot.scene().sigMouseMoved,
                                         rateLimit=60, slot=self.mouse_moved)

        # The Y axis is scaled by autoscale_y() rather than by the view's own
        # auto range, so follow what the user does to it
        self.watch_y_axis()

        # The waterfall's frequency axis is linked to this one, so it follows
        self.add_zoom_buttons()
        self.cache_axes()

        self.create_band_region()
        self.create_dc_region()

    def create_band_region(self):
        """The stretch of spectrum the scope pane narrows itself to

        Drawn behind the curves and ignored by the auto range, so that it
        marks a span without changing what the plot shows."""
        self.band_region = pg.LinearRegionItem(brush=(255, 255, 255, 20),
                                               hoverBrush=(255, 255, 255, 45))
        self.band_region.setZValue(-100)
        self.band_region.setVisible(False)
        self.plot.addItem(self.band_region, ignoreBounds=True)
        self.band_region.sigRegionChanged.connect(self.band_moved)
        #: Called with (low_hz, high_hz) whenever the band is dragged
        self.on_band_changed = None

    def band_moved(self):
        """Tell whoever is listening that the band has been dragged"""
        if self.on_band_changed is not None:
            self.on_band_changed(*self.band())

    def band(self):
        """The selected frequency band, low first"""
        low, high = self.band_region.getRegion()
        return (low, high) if low <= high else (high, low)

    def create_dc_region(self):
        """Shade the bins that are interpolated rather than measured

        A straight line drawn across five bins looks exactly like five bins of
        quiet, so the one part of the trace that is not a measurement is also
        the one part that cannot be told from one. Under everything else and
        not draggable: it marks where the radio cannot see, it is not a
        control."""
        self.dc_region = pg.LinearRegionItem(brush=(255, 70, 70, 30),
                                             movable=False)
        self.dc_region.setZValue(-110)
        self.dc_region.setVisible(False)
        self.plot.addItem(self.dc_region, ignoreBounds=True)

    def set_dc_band(self, band):
        """Shade where the receiver's own carrier is, or hide it when it is
        off screen

        Hidden is the good case: it means the tune was offset far enough that
        the spike is outside the span and no bin on screen is a guess."""
        if band is None:
            if self.dc_region.isVisible():
                self.dc_region.setVisible(False)
            return
        if tuple(self.dc_region.getRegion()) != tuple(band):
            self.dc_region.setRegion(band)
        if not self.dc_region.isVisible():
            self.dc_region.setVisible(True)

    def set_band(self, low, high):
        """Move the band without reporting it back as a drag"""
        self.band_region.blockSignals(True)
        self.band_region.setRegion((low, high))
        self.band_region.blockSignals(False)

    def show_band(self, visible, span=None):
        """Show or hide the band selector

        A band that has never been placed, or that the frequency range has
        moved out from under, is put across the middle tenth of `span`. That
        is somewhere to start dragging from rather than a guess at what is
        interesting."""
        if visible and span is not None:
            low, high = self.band()
            if not (span[0] <= low < high <= span[1]):
                middle = (span[0] + span[1]) / 2
                width = (span[1] - span[0]) / 20
                self.set_band(middle - width, middle + width)
        self.band_region.setVisible(visible)

    def all_curves(self):
        """Every curve on the spectrum plot"""
        return [self.curve, self.curve_peak_hold_max, self.curve_peak_hold_min,
                self.curve_average, self.curve_baseline] + list(self.persistence_curves or [])

    def create_curve(self, pen, z_value):
        """Create one curve, downsampled to the resolution of the screen"""
        curve = self.plot.plot(pen=pen)
        curve.setZValue(z_value)
        curve.opts["autoDownsampleFactor"] = self.downsample_factor
        # Antialiasing is off globally, so ask for it per curve. It has to be
        # set on the PlotDataItem: it copies its own value down into the
        # PlotCurveItem it owns on every setData, overwriting anything set
        # there directly.
        curve.opts["antialias"] = self.antialias
        curve.curve.opts["antialias"] = self.antialias
        return curve

    def set_antialias(self, antialias):
        """Turn antialiasing of the curves on or off"""
        self.antialias = antialias
        for curve in self.all_curves():
            if curve is not None:
                curve.opts["antialias"] = antialias
                curve.curve.opts["antialias"] = antialias
                curve.curve.update()

    def create_main_curve(self):
        """Create main spectrum curve"""
        self.curve = self.create_curve(self.main_color, 900)

    def create_peak_hold_max_curve(self):
        """Create max. peak hold curve"""
        self.curve_peak_hold_max = self.create_curve(self.peak_hold_max_color, 800)

    def create_peak_hold_min_curve(self):
        """Create min. peak hold curve"""
        self.curve_peak_hold_min = self.create_curve(self.peak_hold_min_color, 800)

    def create_average_curve(self):
        """Create average curve"""
        self.curve_average = self.create_curve(self.average_color, 700)

    def create_baseline_curve(self):
        """Create baseline curve"""
        self.curve_baseline = self.create_curve(self.baseline_color, 500)

    def create_persistence_curves(self):
        """Create spectrum persistence curves"""
        z_index_base = 600
        decay = self.get_decay()
        self.persistence_curves = []
        for i in range(self.persistence_length):
            alpha = 255 * decay(i + 1, self.persistence_length + 1)
            color = self.persistence_color
            curve = self.create_curve((color.red(), color.green(), color.blue(), alpha),
                                      z_index_base - i)
            self.persistence_curves.append(curve)

    def set_colors(self):
        """Set colors of all curves"""
        self.curve.setPen(self.main_color)
        self.curve_peak_hold_max.setPen(self.peak_hold_max_color)
        self.curve_peak_hold_min.setPen(self.peak_hold_min_color)
        self.curve_average.setPen(self.average_color)
        self.curve_baseline.setPen(self.baseline_color)

        decay = self.get_decay()
        for i, curve in enumerate(self.persistence_curves):
            alpha = 255 * decay(i + 1, self.persistence_length + 1)
            color = self.persistence_color
            curve.setPen((color.red(), color.green(), color.blue(), alpha))

    def decay_linear(self, x, length):
        """Get alpha value for persistence curve (linear decay)"""
        return (-x / length) + 1

    def decay_exponential(self, x, length, const=1 / 3):
        """Get alpha value for persistence curve (exponential decay)"""
        return math.e**(-x / (length * const))

    def get_decay(self):
        """Get decay function"""
        if self.persistence_decay == 'exponential':
            return self.decay_exponential
        else:
            return self.decay_linear

    def draw(self, data_storage, dirty):
        """Redraw every curve that has pending data"""
        for kind in dirty:
            getattr(self, "draw_" + kind)(data_storage)
        self.autoscale_y(data_storage)

    def on_range_changed_manually(self, *args):
        """Stop rescaling the Y axis once the user has taken hold of it"""
        if not self.plot.vb.autoRangeEnabled()[1]:
            self.auto_y = False

    def on_view_state_changed(self, *args):
        """Rescale again when the view's own auto range is switched back on

        That is what the plot's A button and the View All menu entry do, and
        so it is the way back from a manual zoom."""
        if self.plot.vb.autoRangeEnabled()[1]:
            self.auto_y = True
            self.y_range = None

    def visible_bounds(self, data_storage):
        """Lowest and highest power on any curve currently shown

        A curve that is switched off is not given data at all, so whatever it
        last held is stale and must not count towards the axis."""
        low = high = None
        for flag, _, source in self.CURVES.values():
            if not getattr(self, flag):
                continue
            if source is None:
                arrays = self.persistence_data or ()
            else:
                arrays = (getattr(data_storage, source, None),)

            for y in arrays:
                if y is None or not len(y):
                    continue
                bottom, top = float(np.min(y)), float(np.max(y))
                low = bottom if low is None else min(low, bottom)
                high = top if high is None else max(high, top)
        return low, high

    def autoscale_y(self, data_storage):
        """Fit the Y axis to the curves currently on screen

        Peak hold curves used to hide the cost of not doing this: their bounds
        stop moving once they have converged, so they pinned the axis, and
        turning either of them off handed it back to the noise floor."""
        self.fit_y_range(*self.visible_bounds(data_storage))

    def queue_redraw(self, kind, data_storage, force):
        """Draw at once when forced, otherwise let the throttle pick the moment"""
        if force:
            getattr(self, "draw_" + kind)(data_storage, force=True)
            return

        if kind in self.SLOW_CURVES:
            # Held back to its own rate. Skipping it here leaves it out of the
            # throttle's set of pending work, so the frames in between draw
            # only the curves that had something new to show.
            now = time.monotonic()
            if now - self.slow_drawn.get(kind, 0.0) < self.SLOW_INTERVAL:
                return
            self.slow_drawn[kind] = now

        self.throttle.schedule(kind, data_storage)

    def update_plot(self, data_storage, force=False):
        """Queue a redraw of the plot"""
        self.queue_redraw("plot", data_storage, force)

    def update_peak_hold_max(self, data_storage, force=False):
        """Queue a redraw of the peak hold max"""
        self.queue_redraw("peak_hold_max", data_storage, force)

    def update_peak_hold_min(self, data_storage, force=False):
        """Queue a redraw of the peak hold min"""
        self.queue_redraw("peak_hold_min", data_storage, force)

    def update_average(self, data_storage, force=False):
        """Queue a redraw of the average"""
        self.queue_redraw("average", data_storage, force)

    def update_baseline(self, data_storage, force=False):
        """Queue a redraw of the baseline"""
        self.queue_redraw("baseline", data_storage, force)

    def update_persistence(self, data_storage, force=False):
        """Queue a redraw of the persistence"""
        self.queue_redraw("persistence", data_storage, force)

    def draw_curve(self, curve, x, y, enabled, force):
        """Give one curve new data

        A curve that is switched off is left alone, since it is not on screen,
        unless the caller forces it: that happens when the data behind it has
        been recalculated, and then its visibility is set too.

        Either array can still be None by the time this runs: redraws are
        deferred by the throttle, and a reset in between (a new run, or
        changed settings) clears the data that was queued to be drawn."""
        if x is None or y is None:
            return

        if enabled or force:
            curve.setData(x, y)
            if force:
                curve.setVisible(enabled)

    def draw_plot(self, data_storage, force=False):
        """Update main spectrum curve"""
        self.draw_curve(self.curve, data_storage.x, data_storage.y,
                        self.main_curve, force)

    def draw_peak_hold_max(self, data_storage, force=False):
        """Update max. peak hold curve"""
        self.draw_curve(self.curve_peak_hold_max, data_storage.x, data_storage.peak_hold_max,
                        self.peak_hold_max, force)

    def draw_peak_hold_min(self, data_storage, force=False):
        """Update min. peak hold curve"""
        self.draw_curve(self.curve_peak_hold_min, data_storage.x, data_storage.peak_hold_min,
                        self.peak_hold_min, force)

    def draw_average(self, data_storage, force=False):
        """Update average curve"""
        self.draw_curve(self.curve_average, data_storage.x, data_storage.average,
                        self.average, force)

    def draw_baseline(self, data_storage, force=False):
        """Update baseline curve"""
        if data_storage.baseline_x is None or data_storage.baseline is None:
            self.curve_baseline.clear()
            return

        self.draw_curve(self.curve_baseline, data_storage.baseline_x, data_storage.baseline,
                        self.baseline, force)

    def draw_persistence(self, data_storage, force=False):
        """Update persistence curves"""
        if data_storage.x is None or data_storage.y is None:
            return

        if self.persistence or force:
            if self.persistence_data is None:
                self.persistence_data = collections.deque(maxlen=self.persistence_length)
            else:
                for i, y in enumerate(self.persistence_data):
                    curve = self.persistence_curves[i]
                    curve.setData(data_storage.x, y)
                    if force:
                        curve.setVisible(self.persistence)
            self.persistence_data.appendleft(data_storage.y)

    def recalculate_plot(self, data_storage):
        """Recalculate plot from history"""
        if data_storage.x is None:
            return

        # A settings change must show at once, and whatever the throttle was
        # holding is about to be redrawn anyway
        self.throttle.reset()

        QtCore.QTimer.singleShot(0, lambda: self.redraw_all(data_storage))

    def redraw_all(self, data_storage):
        """Redraw every curve except persistence, whatever the throttle says"""
        for kind in ("plot", "average", "baseline", "peak_hold_max", "peak_hold_min"):
            getattr(self, "draw_" + kind)(data_storage, force=True)
        self.autoscale_y(data_storage)

    def recalculate_persistence(self, data_storage):
        """Recalculate persistence data and update persistence curves"""
        if data_storage.x is None:
            return

        self.clear_persistence()
        self.persistence_data = collections.deque(maxlen=self.persistence_length)
        for i in range(min(self.persistence_length, data_storage.history.history_size - 1)):
            data = data_storage.history[-i - 2]
            if data_storage.smooth:
                data = data_storage.smooth_data(data)
            self.persistence_data.append(data)
        QtCore.QTimer.singleShot(0, lambda: self.update_persistence(data_storage, force=True))

    def curves_for(self, kind):
        """Every curve that one kind draws"""
        attribute = self.CURVES[kind][1]
        if attribute is None:
            return list(self.persistence_curves or [])
        return [getattr(self, attribute)]

    def fill_curve(self, kind, data_storage):
        """Give a curve that has never been drawn something to show"""
        if kind == "persistence":
            # Persistence shows past traces, so it is rebuilt from the history
            # rather than from the latest sweep
            self.recalculate_persistence(data_storage)
        else:
            # Forced, so that a slow curve being switched on appears now
            # rather than whenever its own rate next comes round
            getattr(self, "update_" + kind)(data_storage, force=True)

    def set_enabled(self, kind, enabled, data_storage):
        """Show or hide one kind of curve

        While a curve is switched off it is not given data, so one being
        switched on has to be filled in first, or it would stay empty until
        the next sweep arrives."""
        flag = self.CURVES[kind][0]
        setattr(self, flag, enabled)

        curves = self.curves_for(kind)
        if enabled and curves and curves[0].xData is None:
            self.fill_curve(kind, data_storage)

        for curve in curves:
            curve.setVisible(enabled)

        # What is on screen has just changed, so what the axis has to fit has
        # changed with it; waiting for the next sweep would leave the plot
        # wrongly scaled, and leave it that way for good while stopped
        self.autoscale_y(data_storage)

    def show_sweep(self, x, y):
        """Draw a single recorded sweep on the main curve (history browsing)"""
        self.curve.setData(x, y)

    def mouse_moved(self, evt):
        """Update crosshair when mouse is moved"""
        pos = evt[0]
        if self.plot.sceneBoundingRect().contains(pos):
            mousePoint = self.plot.vb.mapSceneToView(pos)
            self.posLabel.setText(
                "<span style='font-size: 12pt'>f={:0.3f} MHz, P={:0.3f} dB</span>".format(
                    mousePoint.x() / 1e6,
                    mousePoint.y()
                )
            )
            self.vLine.setPos(mousePoint.x())
            self.hLine.setPos(mousePoint.y())

    def clear_plot(self):
        """Clear main spectrum curve"""
        self.throttle.reset()
        self.slow_drawn = {}
        self.curve.clear()
        # A new run gets a fresh range rather than the one the last one left
        self.reset_y_range()

    def clear_peak_hold_max(self):
        """Clear max. peak hold curve"""
        self.curve_peak_hold_max.clear()

    def clear_peak_hold_min(self):
        """Clear min. peak hold curve"""
        self.curve_peak_hold_min.clear()

    def clear_average(self):
        """Clear average curve"""
        self.curve_average.clear()

    def clear_baseline(self):
        """Clear baseline curve"""
        self.curve_baseline.clear()

    def clear_persistence(self):
        """Clear spectrum persistence curves"""
        self.persistence_data = None
        for curve in self.persistence_curves:
            curve.clear()
            self.plot.removeItem(curve)
        self.create_persistence_curves()


class ScopePlotWidget(ThrottledPlotWidget):
    """Power over time — the recording seen along its other axis

    A time sink, in the sense a scope pane in an SDR toolkit is one: the
    spectrum plot shows one moment across all frequencies, and this shows all
    of the recording at one place in the spectrum. Stepping through recorded
    sweeps moves a cursor along it, so the shape a signal has in time is on
    screen next to the sweep being looked at.

    Nothing extra is captured for it. The recording is already a spectrogram
    — sweeps by bins — so this is a reduction of it along frequency: over
    every bin when no band is chosen, and over the bins the band covers when
    one is. That makes a signal returning every so often obvious, where
    stepping through thousands of sweeps looking for it is not.

    A backend that can read a band straight off its own frames feeds a
    second, finer trace on top — a zero span view, at 25.6 us a reading on a
    HackRF at 20 MSPS against 10 ms for a delivered sweep. That one only
    covers the band that was selected while it was being recorded, because it
    is measured going forward rather than reduced from the spectra
    afterwards, and it is noisier than they are because far fewer frames go
    into each reading."""

    #: How far behind the sweeps the high rate trace may be before it is
    #: treated as stale rather than merely late. It is drained on a timer, so
    #: a fraction of a second is normal; a whole second means it stopped.
    FAST_LAG_LIMIT = 1.0

    #: Readings the trigger's noise statistics are taken from. They describe
    #: the shape of the noise, not the burst, so a regular sample of the
    #: search window is as good as all of it and costs a fraction as much.
    LEVEL_SAMPLE = 4096

    #: How far above the noise's own ceiling the automatic level sits. The
    #: ceiling is where noise reaches about once per search window, so a level
    #: on it fires about once per window on nothing at all; a few decibels
    #: over turns that into a trigger that waits.
    LEVEL_MARGIN = 3.0

    #: Most points worth handing to a curve. The pane is at most a couple of
    #: thousand pixels wide, and a sweep at the finest step holds twelve
    #: thousand readings for a 20 ms window - so most of them are drawn on
    #: top of each other, at full price.
    CURVE_POINTS = 2000

    #: Fewest delivered sweeps worth joining up inside a sweep window. Two
    #: samples 13 ms apart joined by a straight line say nothing whatever
    #: about the 13 ms in between, and a straight line is exactly what it
    #: looks like: a measurement, rather than the absence of one.
    SWEEP_MIN_POINTS = 3

    #: Most high rate samples kept, at 16 bytes each against 8 per bin per
    #: sweep. 25 seconds at the finest a HackRF can be read (25.6 us), and
    #: minutes at a coarser zero span step. The trace is trimmed to the
    #: recording it sits under anyway, so raising this past the recording
    #: depth buys nothing. The settings dialog works this out for whatever
    #: step is chosen.
    #: Readings kept in the fast buffer. Shared with the backends, which check
    #: a zero span step against how far back it reaches.
    FAST_CAPACITY = TAP_CAPACITY

    def __init__(self, layout, max_refresh_rate=60):
        super().__init__(layout, max_refresh_rate)

        #: (low_hz, high_hz) to reduce over, or None for the whole spectrum
        self.band = None
        #: Power per recorded sweep, aligned with history.get_buffer()
        self.trace = None
        self.trace_bins = None
        self.trace_counter = None
        self.times = None
        #: Where the newest recorded sweep sits on the time axis
        self.newest = None
        #: Whether the time window rolls forward with the newest data. Zooming
        #: in keeps it; panning back into the recording gives it up, so that a
        #: stretch being looked at is not dragged out from under.
        self.following = True
        #: Whether the window is fitted to the whole recording, which
        #: draw_whole_recording() does itself on every redraw. Not pyqtgraph's
        #: auto range: that refits while painting, and the refit asks for a
        #: second paint, so every redraw of the scope was painted twice -
        #: measured at 75 paints a second for 37 redraws, 200 ms of GUI thread
        #: a second, a third of all the display cost. See also FIT_HEADROOM.
        self.fitting_all = True
        #: Seconds the window is to be wide, or None to fit the whole recording
        self.time_span = None
        #: Power in dB a rising edge must cross for the sweep to start, None
        #: to free run, or "auto" to take a level from the data
        self.trigger = None
        #: Where the last sweep was triggered, in recording coordinates
        self.trigger_time = None
        #: What fraction of a triggered window comes before the edge. A rising
        #: edge is the one part of a burst that says how it starts, and with
        #: no lead at all it is the very first reading drawn — on the axis but
        #: with nothing before it to be read against.
        self.trigger_lead = self.TRIGGER_LEAD
        #: Set when the band being watched is not inside what the radio is
        #: tuned to, which is silent otherwise: the tap simply hears nothing
        self.band_outside = False
        #: Set when the band is nothing but the centre of the tune. The tap
        #: leaves the carrier out of a wider band, but here there is nothing
        #: else to read, so the carrier is in every reading at full height
        self.band_at_dc = False
        #: The lowest reading in the last search, for saying when a level is
        #: under the whole trace and so has no rising edge to find
        self.level_trough = None
        #: The level find_trigger() last used, or None if it found nothing,
        #: and the loudest reading it saw — so that a trigger which never
        #: fires can say whether the level is simply above everything
        self.level_used = None
        self.level_peak = None
        #: Whether the sweep on screen is aligned to a trigger
        self.triggered_view = False
        #: Whether the readout is currently explaining an empty sweep
        self.explaining = False
        #: Catch one sweep and hold it, rather than triggering over and over
        self.single = False
        self.armed = False
        self.captured = False
        #: The moment arming took effect. A single shot waits for a burst
        #: that has not happened yet, so an edge already in the buffer must
        #: not count as one; None means arming has not taken effect yet.
        self.armed_at = None
        #: Called with the trigger time when a single shot fires
        self.on_capture = None
        #: Set when a single shot has just fired, so that the draw which
        #: follows can say what it actually caught, then cleared
        self.caught = None
        #: The tap trace at full resolution, which is what a saved sweep is
        #: written from - the curve itself may be holding an envelope of it
        self.fast_points = None
        #: Time each recorded sweep sits at, counted from the epoch
        self.offsets = None
        #: What the sweep currently on screen is drawn relative to, and where
        #: the browsed sweep sits, both in recording coordinates
        self.sweep_origin = None
        self.browse_offset = None
        #: Called with the window's width in seconds whenever the user changes
        #: it by hand, so that a control showing the timebase can follow
        self.on_span_changed = None
        #: (time, power) read off the radio's frames, when a backend can
        self.fast = None
        #: The clock time the tap's readings are counted from. Zero means they
        #: are already on the wall clock, which is what a backend that does not
        #: say otherwise is taken to mean.
        self.fast_epoch = 0.0
        self.fast_dirty = False
        self.fast_bounds = None
        #: What time zero on the axis means. Fixed for the run, so that the
        #: points already drawn keep the coordinates they were given: anchoring
        #: to the newest sweep instead would shift every one of them, and there
        #: can be hundreds of thousands.
        self.epoch = None

        self.create_plot()

    def create_plot(self):
        """Create the power over time plot"""
        self.posLabel = self.layout.addLabel(row=0, col=0, justify="right")
        self.time_axis = RelativeTimeAxis(orientation="bottom")
        self.plot = self.layout.addPlot(row=1, col=0,
                                        axisItems={"bottom": self.time_axis})
        self.plot.showGrid(x=True, y=True)
        self.label_source()
        self.plot.setLabel("bottom", "Time", units="s")
        self.plot.showButtons()
        self.plot.setDownsampling(auto=True, mode="peak")
        self.plot.setClipToView(True)

        self.curve_fast = self.plot.plot(pen=(0, 200, 255))
        self.curve_fast.setZValue(800)
        self.curve = self.plot.plot(pen=(255, 255, 0))
        self.curve.setZValue(900)
        # The X range is fitted by draw_whole_recording(); see fitting_all
        self.plot.vb.disableAutoRange(axis=self.plot.vb.XAxis)

        # Where the history browser is sitting, and a handle to move it
        self.cursor = pg.InfiniteLine(angle=90, movable=True, pen=(255, 0, 0))
        self.cursor.setZValue(1000)
        self.cursor.setVisible(False)
        self.plot.addItem(self.cursor, ignoreBounds=True)
        self.cursor.sigPositionChangeFinished.connect(self.cursor_moved)
        #: Called with an index into the recording when the cursor is dragged
        self.on_time_selected = None

        # A marker that follows the pointer, and reads out against the cursor.
        # Zoomed in far enough to see a burst, the axis is showing six decimal
        # places of the time since the run started, which is no way to measure
        # how long the burst lasted or how often it comes back.
        self.marker = pg.InfiniteLine(angle=90, movable=False, pen=(120, 120, 120))
        self.marker.setZValue(950)
        self.plot.addItem(self.marker, ignoreBounds=True)

        # The level a sweep starts on, shown so that a trigger that never
        # fires is obviously a level set above anything in the trace
        self.trigger_line = pg.InfiniteLine(
            angle=0, movable=False,
            pen=pg.mkPen((0, 220, 120), style=QtCore.Qt.DashLine))
        self.trigger_line.setZValue(940)
        self.trigger_line.setVisible(False)
        self.plot.addItem(self.trigger_line, ignoreBounds=True)
        self.mouseProxy = pg.SignalProxy(self.plot.scene().sigMouseMoved,
                                         rateLimit=60, slot=self.mouse_moved)

        self.watch_y_axis()
        self.add_zoom_buttons()
        self.cache_axes()

    def reference_time(self):
        """What the time axis counts from

        The browsing cursor when there is one, the trigger while the sweep is
        triggered, and otherwise the newest data."""
        if self.time_span:
            # A sweep is already drawn relative to what it was built about,
            # so the axis counts from where the data sits, which is zero
            return 0.0
        if self.cursor.isVisible():
            return self.cursor.value()
        return self.newest if self.newest is not None else 0.0

    def set_trigger(self, trigger):
        """Start each sweep on a rising edge, or None to free run"""
        if trigger == self.trigger:
            return
        self.trigger = trigger
        self.trigger_time = None
        self.release_capture()
        if trigger is None:
            self.trigger_line.setVisible(False)

    def set_single(self, single):
        """Catch one sweep on the next edge and hold it, or keep triggering

        What a scope calls single shot. A burst that happens once, or once a
        minute, cannot be read off a display that has moved on by the time
        anybody looks at it, so the sweep it arrived in is kept until it is
        asked for again."""
        self.single = single
        self.captured = False
        self.armed = single
        self.armed_at = None
        self.announce_arm_state()

    def arm(self):
        """Let go of the held sweep and wait for the next one"""
        self.armed = True
        self.captured = False
        self.armed_at = None
        self.announce_arm_state()

    def release_capture(self):
        """Drop a held sweep, because what it was caught with has changed"""
        if self.captured:
            self.captured = False
            self.armed = self.single
            self.armed_at = None
            self.announce_arm_state()

    def announce_arm_state(self):
        """Refresh the readout after the arm state has been changed by hand"""
        self.update_readout(drew=True)

    def readout_message(self, drew):
        """What the pane most needs to say, or None to say nothing

        In the order it matters: a sweep being held is what the pane is for; a
        trigger that has not fired needs to say why, because a level above the
        whole trace looks exactly like a broken feature; and an empty window
        needs to say that the sweep is shorter than the data."""
        if self.band_outside:
            return ("The band lies outside what the radio is tuned to \u2014 "
                    "move it inside the frequency range, or the range around it")

        if self.band_at_dc:
            return ("The tap is watching only the centre of the tune, where "
                    "the receiver's own carrier is \u2014 so that carrier is "
                    "every reading. Widen the band past it, move it clear of "
                    "the centre, or narrow the frequency range so the tune "
                    "steps aside")

        if self.trigger is not None:
            if self.single and self.captured:
                return "Caught one \u2014 press Arm to wait for the next"

            waiting = (self.single and self.armed) or not self.triggered_view
            if waiting:
                above = (self.level_used is not None and self.level_peak is not None
                         and self.level_peak < self.level_used)
                # A level under the whole trace has no rising edge to find:
                # a trigger fires where the trace crosses upwards, and a trace
                # that is never below the level never crosses it
                below = (self.level_used is not None and self.level_trough is not None
                         and self.level_trough > self.level_used)
                if above:
                    reason = "level {:+.1f} dB is above the trace, which peaks at {:+.1f}".format(
                        self.level_used, self.level_peak)
                elif below:
                    reason = ("level {:+.1f} dB is below the whole trace, which "
                              "never drops under {:+.1f}, so nothing ever rises "
                              "across it").format(self.level_used, self.level_trough)
                elif self.level_used is None:
                    reason = "nothing in the trace stands clear of the noise"
                else:
                    # Say where the trace sits as well as where the level is:
                    # a level a decibel above the floor catches noise within
                    # seconds, and there is nothing else on screen to judge it
                    # against
                    reason = "level {:+.1f} dB, trace floor {:+.1f}".format(
                        self.level_used,
                        self.level_trough if self.level_trough is not None
                        else float("nan"))
                if self.single and self.armed:
                    return "Armed, waiting for a burst \u2014 {}".format(reason)
                return "Waiting for a burst \u2014 {}".format(reason)

        if not drew:
            if self.fast is not None and self.fast.history_size:
                return "Nothing measured in this window yet"
            return ("Sweep shorter than the gap between sweeps \u2014 "
                    "switch on the high-rate tap to fill it")
        return None

    def update_readout(self, drew):
        """Put the pane's own message up, or take it down"""
        message = self.readout_message(drew)
        if message is None:
            self.clear_explanation()
            return
        self.explaining = True
        self.posLabel.setText(
            "<span style='font-size: 10pt; color: #d08000'>{}</span>".format(message))

    def trigger_source(self, width):
        """The finest trace available, over the stretch worth searching

        The high rate trace when a backend feeds one, because a burst is what
        this is looking for and that is the trace with the burst in it.
        Only the last few sweeps' worth: a trigger further back than that is
        one the display has already been through."""
        look_back = max(width * 8, 0.25)
        oldest = self.newest - look_back

        if self.fast is not None and self.fast.history_size and self.epoch is not None:
            rows = self.fast.get_buffer()
            shift = self.fast_shift
            first = int(np.searchsorted(rows[:, 0], oldest - shift, side="left"))
            if len(rows) - first > 2:
                return rows[first:, 0] + shift, rows[first:, 1]

        if self.times is None or self.trace is None:
            return None, None
        offsets = self.times - self.epoch
        first = int(np.searchsorted(offsets, oldest, side="left"))
        count = min(len(offsets), len(self.trace))
        if count - first <= 2:
            return None, None
        return offsets[first:count], self.trace[first:count]

    def trigger_level(self, values):
        """The level a rising edge has to cross

        Half way in dB between the noise the trace sits at and the loudest
        thing in it, which is where a scope's own auto level goes — but never
        so low that the noise itself crosses it. A single frame of noise moves
        by about 3 dB, so half way to its own loudest sample is a level it
        crosses several times a second, and a single shot armed against that
        catches noise instantly instead of waiting for a burst.

        Returns None when nothing in the trace stands clear of the noise, and
        then nothing is triggered on at all — which is the honest answer, and
        says to smooth the trace (a coarser step with the average detector) or
        to set a level by hand."""
        if self.trigger != "auto":
            return float(self.trigger)

        # The peak is every reading: it is the burst being looked for, and a
        # burst can be one reading wide. The floor and the width only describe
        # the noise, which is the same shape in a few thousand readings as in
        # the hundred and fifty thousand a quarter second of the tap holds -
        # and sorting all of them, thirty times a second, for numbers that
        # move by hundredths of a decibel between frames was the most
        # expensive thing this pane did.
        peak = float(np.max(values))
        body = values[::max(1, len(values) // self.LEVEL_SAMPLE)]
        floor = float(np.median(body))
        # Where the noise alone gets to, worked out from the shape of the
        # readings rather than from a multiple of their spread. The spread is
        # not a fixed thing: it is 6 dB at one frame a reading and 1.3 dB at
        # twenty-five, so a level set at a fixed number of spreads asks for
        # +15 dB above the floor at the coarse end and +92 at the fine end,
        # and the fine end can then never trigger on anything at all.
        least = max(noise_ceiling(body, len(values)) + self.LEVEL_MARGIN,
                    floor + 4.0)
        if peak < least:
            return None
        return max(floor + (peak - floor) * 0.5, least)

    def find_trigger(self, width, after=None):
        """When the newest complete sweep started, or None to hold still

        A sweep runs from a rising edge and lasts the whole window, so the
        newest one that can be shown in full is the newest edge with a
        window's worth of measurement after it. Finding none means the signal
        has not come back yet, and a scope holds the last sweep it drew rather
        than sliding — which is the entire point of triggering."""
        times, values = self.trigger_source(width)
        if times is None or not len(times):
            return None
        self.level_peak = float(np.max(values))
        self.level_trough = float(np.min(values))
        level = self.trigger_level(values)
        self.level_used = level
        if level is None:
            return None

        above = values >= level
        rising = np.flatnonzero(~above[:-1] & above[1:]) + 1
        if not len(rising):
            return None

        # The window opens before the edge by however much the pre-trigger
        # asks for, and the same fraction sweep_plan() draws about: an edge
        # can only be shown with a lead if there is that much measurement
        # behind it and a window's worth still to come after it.
        lead = width * self.trigger_lead
        latest = self.newest - (width - lead)
        usable = rising[times[rising] <= latest]
        if after is not None:
            # Waiting for a burst that has not happened yet, so take the first
            # edge after arming rather than the newest edge in the buffer
            usable = usable[times[usable] > after]
            if not len(usable):
                return None
            return float(times[usable[0]])
        if not len(usable):
            return None
        return float(times[usable[-1]])

    def zoom(self, scale):
        """Step the timebase, keeping the newest data where it is

        Not a zoom about the middle of the view, the way it is on the other
        plots: this axis is a timebase, and a timebase grows and shrinks
        against now rather than against whatever happens to be centred."""
        width = self.window_width()
        if width is None:
            low, high = self.plot.vb.viewRange()[0]
            width = high - low
        self.set_time_span(width * scale)
        if self.on_span_changed is not None:
            self.on_span_changed(self.time_span)

    @staticmethod
    def format_time(seconds):
        """A time in the unit that makes it readable"""
        magnitude = abs(seconds)
        if magnitude < 1e-3:
            return "{:.2f} us".format(seconds * 1e6)
        if magnitude < 1.0:
            return "{:.3f} ms".format(seconds * 1e3)
        return "{:.4f} s".format(seconds)

    def mouse_moved(self, evt):
        """Read out the time and power under the pointer

        Against the browsing cursor when there is one, so that parking it on
        the leading edge of a burst turns the pointer into a delta marker:
        the width of the burst, and the gap to the next one, are then read
        straight off instead of subtracted out of two absolute times."""
        pos = evt[0]
        if not self.plot.sceneBoundingRect().contains(pos):
            return
        point = self.plot.vb.mapSceneToView(pos)
        self.marker.setPos(point.x())
        self.explaining = False

        delta = point.x() - self.reference_time()
        text = "t={} &nbsp; P={:0.1f} dB".format(self.format_time(delta), point.y())
        # As a repetition rate too, for reading a gap between bursts off the
        # trace. Not below a microsecond, where it is all rounding.
        if abs(delta) >= 1e-6:
            text += " &nbsp; ({:0.1f} Hz)".format(1.0 / abs(delta))
        self.posLabel.setText("<span style='font-size: 10pt'>{}</span>".format(text))

    def on_range_changed_manually(self, *args):
        """Keep rolling forward only while the window still reaches the data"""
        super().on_range_changed_manually(*args)
        low, high = self.plot.vb.viewRange()[0]
        self.fitting_all = False
        self.following = self.newest is None or self.newest <= high
        # Zooming by hand is the other way of setting the timebase, so a span
        # that was asked for follows the mouse rather than fighting it
        if self.time_span is not None:
            self.time_span = high - low
        if self.on_span_changed is not None:
            self.on_span_changed(high - low)

    def set_time_span(self, span):
        """Fix how much time is on screen, or None to fit the whole recording"""
        self.time_span = span if span else None
        self.following = True
        self.release_capture()
        if self.time_span is None:
            # Back to showing everything; the sweep view had the axis pinned
            self.fitting_all = True
            self.fit_whole_x_range()
            self.fit_x_range()
            low, high = self.plot.vb.viewRange()[0]
            self.time_axis.configure(self.reference_time(), high - low)
        # A sweep is laid out entirely by draw_sweep(), so the caller redraws

    def redraw_now(self, data_storage):
        """Draw at once, for a change the user has just made by hand

        The throttle is there to keep up with a backend, not to make the
        display lag behind its own controls."""
        if self.throttle.hidden:
            self.throttle.schedule("plot", data_storage)
            return
        self.draw(data_storage)

    def window_width(self):
        """How wide the window should be, or None while it fits everything"""
        if self.time_span is not None:
            return self.time_span
        if self.fitting_all:
            return None
        low, high = self.plot.vb.viewRange()[0]
        return high - low

    def on_view_state_changed(self, *args):
        """Fitting the whole recording again also means following it again

        The plot's A button and View All switch pyqtgraph's auto range on.
        That is taken as asking for the whole recording, and handed straight
        back to fitting_all, which fits it without the second paint. From a
        sweep it means leaving the sweep too: the span goes back to zero
        through whoever owns the Span control, so that the control and the
        plot cannot end up saying different things."""
        super().on_view_state_changed(*args)
        if not self.plot.vb.autoRangeEnabled()[0]:
            return
        self.plot.vb.disableAutoRange(axis=self.plot.vb.XAxis)
        if self.time_span is not None:
            if self.on_span_changed is not None:
                self.on_span_changed(0.0)
            else:
                self.set_time_span(None)
            return
        self.fitting_all = True
        self.following = True
        self.fit_whole_x_range()

    #: Room left past the newest sweep when the whole recording is fitted,
    #: and the slack allowed at the old end, as fractions of what is shown.
    #: The window moves only when the data reaches its edge, not on every
    #: redraw: pyqtgraph applies a new range while painting, and the axes it
    #: invalidates there ask for a second paint of the whole plot.
    FIT_HEADROOM = 0.05
    FIT_SLACK = 0.02

    def fit_whole_x_range(self):
        """Fit the window to everything recorded, while that is what is asked

        Done here, before the paint, rather than by pyqtgraph's auto range
        during it; see fitting_all. The recording sets the old end, since the
        tap is only drawn back as far as it reaches; the tap can reach a
        little past the newest sweep, so both count at the new end - read off
        the tap's readings, not its curve, which still holds a sweep's
        coordinates until the next readings arrive. The window is left where
        it is while everything is still inside it with no more than
        FIT_SLACK of it empty at the old end, which is most redraws."""
        if not self.fitting_all or self.time_span is not None or self.offsets is None \
                or not len(self.offsets):
            return
        oldest, newest = float(self.offsets[0]), float(self.offsets[-1])
        if self.fast is not None and self.fast.history_size:
            newest = max(newest, float(self.fast.get_buffer()[-1, 0] + self.fast_shift))
        span = max(newest - oldest, 1e-3)
        low, high = self.plot.vb.viewRange()[0]
        shown = max(high - low, 1e-9)
        if (low <= oldest <= low + self.FIT_SLACK * shown
                and newest <= high <= newest + 2 * self.FIT_HEADROOM * span):
            return
        self.plot.vb.setXRange(oldest, newest + self.FIT_HEADROOM * span, padding=0)

    def fit_x_range(self):
        """Roll the time window forward to keep the newest data on screen

        A recording has no end, but a view that has been zoomed into stays
        exactly where it was left, so everything measured after that moment
        falls off the right-hand edge and the plot goes empty. A scope keeps
        its timebase and scrolls instead: the window holds the width it was
        given and ends at the newest sweep.

        Left alone while recorded sweeps are being browsed — the window
        belongs to the cursor then, and show_cursor() moves it to follow that
        — and while the view is fitting the whole recording by itself."""
        if self.newest is None or self.cursor.isVisible() or not self.following:
            return
        width = self.window_width()
        if width is None:
            return

        low, high = self.plot.vb.viewRange()[0]
        # Already the right width with the newest sample inside it
        if self.newest <= high and abs((high - low) - width) <= width * 1e-6:
            return
        self.plot.vb.setXRange(self.newest - width, self.newest, padding=0)

    def show_trigger_line(self):
        """Mark the level the sweep is triggering at

        Whatever find_trigger() last worked out, rather than working it out
        again: it costs a percentile over the search window and nothing has
        changed since."""
        level = self.level_used
        if level is None:
            self.trigger_line.setVisible(False)
            return
        self.trigger_line.setValue(level)
        self.trigger_line.setVisible(True)

    def label_source(self):
        """Say on the axis which frequencies the trace was reduced from"""
        self.plot.setLabel(
            "left", "Peak power, full span" if self.band is None else "Peak power, band",
            units="dB")

    def set_band(self, band):
        """Choose the frequencies to follow, or None for the whole spectrum

        The trace has to be built again from the recording, since it is a
        different reduction of it; the high rate samples cannot be, because
        they were measured for the band that was selected at the time."""
        if band is not None:
            low, high = band
            band = (low, high) if low <= high else (high, low)
        if band == self.band:
            return
        self.band = band
        self.trace = None
        self.trace_counter = None
        self.release_capture()
        self.clear_fast()
        self.label_source()

    def band_bins(self, data_storage):
        """The bins the trace is reduced over"""
        x = data_storage.x
        if x is None or not len(x):
            return None
        if self.band is None:
            return slice(0, len(x))
        low = int(np.searchsorted(x, self.band[0], side="left"))
        high = int(np.searchsorted(x, self.band[1], side="right"))
        # A band narrower than one bin still has to name a bin
        low = min(max(low, 0), len(x) - 1)
        high = min(max(high, low + 1), len(x))
        return slice(low, high)

    def update_trace(self, data_storage):
        """Extend the trace with whatever has been recorded since last time

        Reducing the whole recording again on every redraw would be several
        milliseconds of work to add one point to it, so only the sweeps that
        have arrived since are reduced. Moving the band is the case that does
        need all of it again."""
        history = data_storage.history
        bins = self.band_bins(data_storage)
        if history is None or bins is None or not history.history_size:
            self.trace = self.trace_counter = None
            return

        buffer = history.get_buffer()
        arrived = 0 if self.trace_counter is None else history.counter - self.trace_counter

        if (self.trace is None or bins != self.trace_bins
                or arrived < 0 or arrived >= history.history_size):
            # The peak across the bins, not the mean: a narrow signal in a
            # wide span should show its own level, not one diluted by the
            # noise either side of it
            self.trace = buffer[:, bins].max(axis=1)
        elif arrived:
            self.trace = np.concatenate(
                (self.trace, buffer[-arrived:, bins].max(axis=1)))[-history.history_size:]

        self.trace_bins = bins
        self.trace_counter = history.counter

    @property
    def fast_shift(self):
        """Seconds to add to a tap reading to put it on the recording's clock

        The tap counts from when its stream began and the recording counts
        from its first sweep, so the two need one constant between them. It is
        applied to a window's edges rather than to every reading, which is the
        whole point: seconds since 1970 in a float are quantised to 0.24 us,
        and a tap reading is 0.8 us wide. Shifting by a quantised constant
        moves the whole trace by up to a quarter of a microsecond and leaves
        the spacing between readings exact; stamping each reading on that
        clock would not."""
        return self.fast_epoch - (self.epoch or 0.0)

    def add_fast_samples(self, samples, epoch=None):
        """Add band power read off the radio's frames, as (time, power) rows

        `epoch` is the clock time those times are counted from; None means
        they are already on the wall clock. A stream that restarts counts from
        a new zero, so whatever was gathered before it belongs to a different
        clock and is dropped rather than drawn in the wrong place."""
        if samples is None or not len(samples):
            return
        # None leaves the clock as it is rather than resetting it: a backend
        # that never names one keeps the wall clock it started with, and one
        # that has not opened its radio yet is not a reason to throw away what
        # has already been gathered
        if epoch is not None and float(epoch) != self.fast_epoch:
            self.fast = None
            self.fast_bounds = None
            self.fast_points = None
            self.fast_epoch = float(epoch)
        if self.fast is None:
            self.fast = HistoryBuffer(2, self.FAST_CAPACITY, dtype=np.float64)
        self.fast.extend(samples)
        self.fast_dirty = True

    def clear_fast(self):
        """Forget the high rate samples (they belong to the band that was set)"""
        self.fast = None
        self.fast_dirty = False
        self.fast_bounds = None
        self.fast_points = None
        self.curve_fast.clear()

    def show_fast(self, x, power):
        """Draw the high rate trace, reduced to something worth drawing

        The readings are kept whole for saving and measuring; what goes to the
        curve is their outline. A 20 ms sweep at the finest step is twelve
        thousand readings across a pane a couple of thousand pixels wide, and
        a whole recording is a million, so most of them are drawn on top of
        one another at full price.

        Copied, not referred to. The readings arrive as a slice of the ring
        buffer the tap is still being written into, so a held sweep that keeps
        the slice does not keep the measurement: the buffer comes round, writes
        new readings into those same slots, and the sweep silently becomes
        whatever the radio heard later. A capture would be drawn correctly,
        report itself correctly, and then save something else entirely."""
        x, power = np.array(x), np.array(power)
        self.fast_points = (x, power)
        self.curve_fast.setData(*self.envelope(x, power, self.CURVE_POINTS // 2))

    @staticmethod
    def envelope(x, y, columns):
        """A trace reduced to its lowest and highest reading per column

        What a scope does with more measurements than it has pixels. An
        average would smooth away the pulse that is the whole reason for
        looking, and taking every nth reading would miss it just as surely;
        keeping both extremes of each column draws the same outline the full
        trace does, from two points per column instead of hundreds."""
        count = len(x)
        if count <= columns * 2:
            return x, y
        per = count // columns
        used = per * columns
        block = y[:used].reshape(columns, per)
        # Both points of a column sit at its middle, so the trace keeps its
        # place on the time axis; lowest first, then highest
        out_x = np.repeat(x[:used].reshape(columns, per)[:, per // 2], 2)
        out_y = np.empty(columns * 2, dtype=y.dtype)
        out_y[0::2] = block.min(axis=1)
        out_y[1::2] = block.max(axis=1)
        if used < count:
            # Whatever did not divide into a column still happened, and at the
            # end of a sweep it is the newest thing on screen
            out_x = np.append(out_x, x[-1])
            out_y = np.append(out_y, y[-1])
        return out_x, out_y

    def draw(self, data_storage, dirty=None):
        """Redraw the power over time trace"""
        self.update_trace(data_storage)
        times = data_storage.recorded_times()

        if self.trace is None or times is None:
            self.curve.clear()
            self.times = self.newest = None
            return

        # The recording is appended to from a worker thread, so the two
        # buffers can be read a row apart; keep only what both have
        count = min(len(times), len(self.trace))
        if count < 1:
            self.curve.clear()
            self.times = self.newest = None
            return
        times, trace = times[-count:], self.trace[-count:]
        self.times = times
        if self.epoch is None:
            self.epoch = float(times[0])
        self.offsets = times - self.epoch
        self.newest = self.newest_drawable(float(self.offsets[-1]))

        if self.time_span:
            self.draw_sweep(trace)
        else:
            self.draw_whole_recording(trace)

    def newest_drawable(self, recorded):
        """The newest moment both traces reach

        The tap is drained on a timer, so it runs a fraction of a second
        behind the sweeps even when it is perfectly healthy. A sweep window
        ending past where it has got to is drawn empty — which looks exactly
        like the tap not working — so the window ends where both have data."""
        if self.fast is None or not self.fast.history_size or self.epoch is None:
            return recorded
        tip = float(self.fast.get_buffer()[-1, 0] + self.fast_shift)
        if 0.0 < recorded - tip < self.FAST_LAG_LIMIT:
            return tip
        return recorded

    def draw_whole_recording(self, trace):
        """Draw everything recorded, on an axis that counts back from now

        What the pane does with no timebase set: useful for finding a signal
        that comes back every few seconds, useless for looking at the shape of
        one, which is what draw_sweep() is for."""
        self.sweep_origin = None
        self.curve.setData(self.offsets, trace)

        low, high = float(np.min(trace)), float(np.max(trace))
        low, high = self.draw_fast(float(self.times[0]), low, high)
        self.fit_y_range(low, high)
        self.fit_whole_x_range()
        self.fit_x_range()

        view_low, view_high = self.plot.vb.viewRange()[0]
        self.time_axis.configure(self.reference_time(), view_high - view_low)

    #: How much of a triggered window comes before the edge by default, so
    #: that the rise itself is on screen rather than hard against the left of
    #: it. `trigger_lead` overrides it from the scope controls.
    TRIGGER_LEAD = 0.1

    def sweep_plan(self, span):
        """Where to draw this sweep about, and how much of it leads that point

        Returns (origin, lead), or (None, None) to leave the pane as it is.

        A trigger that has not fired yet is the case worth being careful with.
        Holding a blank pane until it does is what a scope does, and it is
        also indistinguishable from the feature being broken — which is no
        way to find out that the level was set above the whole trace. So until
        something has actually been caught, the live sweep is shown and the
        readout says what is being waited for."""
        if self.browse_offset is not None:
            return self.browse_offset, span / 2

        lead = span * self.trigger_lead
        if self.trigger is None:
            self.triggered_view = False
            return self.newest, span            # free running: now, at the right

        if self.single and self.captured:
            return None, None                   # frozen on what was caught

        if self.single and not self.armed:
            return self.sweep_origin, lead      # asked to hold, not yet armed

        if self.single and self.armed_at is None:
            # Arming takes effect now, so a burst already in the buffer does
            # not count as the one being waited for
            self.armed_at = self.newest
            self.triggered_view = False
            return self.newest, span

        edge = self.find_trigger(span, after=self.armed_at if self.single else None)
        if edge is None:
            if self.single or self.sweep_origin is None:
                # Nothing caught yet, so keep the trace live and visible
                self.triggered_view = False
                return self.newest, span
            # A sweep has been caught before: hold it rather than sliding
            return self.sweep_origin, lead

        if self.single:
            self.armed = False
            self.captured = True
            self.caught = edge
            if self.on_capture is not None:
                self.on_capture(edge)
        self.triggered_view = True
        return edge, lead

    def draw_sweep(self, trace):
        """Draw one sweep of a fixed length, the way zero span does

        The window is fixed and the measurement is moved into it, rather than
        the window being moved along the measurement. That is what makes a
        burst stand still: every sweep is drawn about the same point in it —
        the trigger — so the axis never moves and neither does the burst."""
        if self.single and self.captured:
            # Frozen on the sweep that was caught: leave every curve, the
            # range and the axis exactly as they were when it arrived
            return

        span = self.time_span
        origin, lead = self.sweep_plan(span)
        if origin is None:
            return

        self.sweep_origin = origin
        start, end = origin - lead, origin - lead + span

        first = int(np.searchsorted(self.offsets, start, side="left"))
        last = int(np.searchsorted(self.offsets, end, side="right"))
        low = high = None
        if last - first >= self.SWEEP_MIN_POINTS:
            piece = trace[first:last]
            self.curve.setData(self.offsets[first:last] - origin, piece)
            low, high = float(np.min(piece)), float(np.max(piece))
        else:
            # A window this short holds one delivered sweep or none, and
            # joining those up would draw a line nobody measured
            self.curve.clear()

        low, high = self.draw_fast_sweep(origin, start, end, low, high)
        if self.caught is not None:
            self.caught = None
            self.report_capture()
        if low is not None:
            if self.level_used is not None and self.trigger is not None:
                # Keep the level on screen, so a level set above everything is
                # visibly above everything rather than clipped off the top
                low, high = min(low, self.level_used), max(high, self.level_used)
            self.fit_y_range(low, high)
        self.update_readout(drew=low is not None)

        self.hold_sweep_view(span, lead)
        self.time_axis.configure(0.0, span)
        if self.trigger is not None:
            self.show_trigger_line()

        # The cursor was placed against whatever the previous sweep was drawn
        # about, so move it onto this one now that its origin is known
        if self.cursor.isVisible() and self.browse_offset is not None:
            self.cursor.blockSignals(True)
            self.cursor.setValue(self.browse_offset - origin)
            self.cursor.blockSignals(False)

    def report_capture(self):
        """Say on the terminal what a single shot has just caught

        A held sweep is the one measurement here that cannot simply be taken
        again, so it is worth a line saying what was in it. The pane fills
        itself with whatever it has, so a window holding nothing but noise
        looks exactly like one holding a burst until the numbers are read: the
        two that matter are how far the window's own peak stands above its
        floor, and whether the reading that fired the trigger is in the window
        at all, where a triggered sweep puts it at zero."""
        x, y = self.fast_points if self.fast_points is not None else (None, None)
        source = "the tap"
        if x is None or y is None or not len(x):
            x, y = self.curve.xData, self.curve.yData
            source = "the delivered sweeps"
        if x is None or y is None or not len(x):
            print("scope: caught a sweep, but nothing is drawn in it")
            return

        x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
        step = float(np.median(np.diff(x))) if len(x) > 1 else 0.0
        floor, peak = float(np.median(y)), float(np.max(y))

        lines = ["scope: caught a sweep on {} - {} readings{}".format(
            source, len(x), " at {} each".format(time_length(step)) if step else "")]
        lines.append("  floor {:+.1f} dB, peak {:+.1f} dB, {:+.1f} above the floor"
                     .format(floor, peak, peak - floor))

        if self.level_used is None:
            lines.append("  no level was in use, so there is nothing to measure "
                         "the length against")
        else:
            crossed = np.flatnonzero(y >= self.level_used)
            if not len(crossed):
                lines.append("  NOTHING in the window reaches {:+.1f} dB"
                             .format(self.level_used))
            else:
                first, last = int(crossed[0]), int(crossed[-1])
                # First crossing to last, and deliberately not the first
                # unbroken run of them. Anything pulsed crosses the level once
                # per pulse, so a run measures one pulse and says nothing about
                # the burst it belongs to: a 119 us squitter caught at 0.8 us a
                # reading reported 0.80 us, because the trigger level was high
                # enough that only the single loudest reading was over it.
                extent = float(x[last]) - float(x[first]) + step
                breaks = np.flatnonzero(np.diff(crossed) != 1)
                starts = np.concatenate(([0], breaks + 1))
                ends = np.concatenate((breaks + 1, [len(crossed)]))
                bursts = len(starts)
                lines.append("  above {:+.1f} dB for {}, from {:+.4f} to "
                             "{:+.4f} ms".format(
                                 self.level_used, time_length(extent),
                                 float(x[first]) * 1e3, float(x[last]) * 1e3))
                if len(crossed) == 1:
                    lines.append("  one reading, which is where the level sits "
                                 "rather than how long anything lasted - lower "
                                 "it to measure the burst")
                elif bursts == 1:
                    lines.append("  one unbroken burst")
                else:
                    lines.append("  {} separate bursts, longest {}, over the "
                                 "level for {:.0f}% of that - pulsed, not one "
                                 "pulse".format(
                                     bursts, time_length(int((ends - starts).max()) * step),
                                     100.0 * len(crossed) / (last - first + 1)))
        print("\n".join(lines))

    def draw_fast_sweep(self, origin, start, end, low, high):
        """Draw the high rate trace across this sweep, and widen the bounds

        Only the readings inside the window are handed over, where the whole
        recording view hands over everything it holds. At a reading every 25 us
        a 2 ms sweep is eighty points against a million, which is most of why
        this view costs so much less than that one."""
        if self.fast is None or not self.fast.history_size or self.epoch is None:
            self.curve_fast.clear()
            return low, high

        rows = self.fast.get_buffer()
        stamps = rows[:, 0]
        shift = self.fast_shift
        first = int(np.searchsorted(stamps, start - shift, side="left"))
        last = int(np.searchsorted(stamps, end - shift, side="right"))
        if last - first < 1:
            self.curve_fast.clear()
            return low, high

        power = rows[first:last, 1]
        self.show_fast(stamps[first:last] + shift - origin, power)
        bottom, top = float(np.min(power)), float(np.max(power))
        if low is None:
            return bottom, top
        return min(low, bottom), max(high, top)

    def clear_explanation(self):
        """Take down a message about an empty sweep, now that one has drawn"""
        if self.explaining:
            self.explaining = False
            self.posLabel.setText("")

    def sweep_data(self):
        """Everything on the pane right now, for writing out

        The curves' own arrays rather than what they display: pyqtgraph hands
        back the downsampled, clipped version from getData(), and a capture
        worth keeping is worth keeping at full resolution.

        Returns None when there is nothing drawn."""
        traces = []
        for name, curve in (("sweep", self.curve), ("tap", self.curve_fast)):
            x, y = curve.xData, curve.yData
            if name == "tap" and self.fast_points is not None and x is not None:
                # What the curve is drawing is an outline of these
                x, y = self.fast_points
            if x is not None and y is not None and len(x):
                traces.append((name, np.asarray(x), np.asarray(y)))
        if not traces:
            return None

        # When t=0 was, on the clock, so a capture can be lined up against
        # anything else that was recorded at the time
        started = None
        if self.epoch is not None:
            started = self.epoch + (self.sweep_origin or 0.0)

        return {"traces": traces, "band": self.band, "span": self.time_span,
                "started": started, "trigger": self.trigger,
                "level": self.level_used, "held": self.single and self.captured}

    def hold_sweep_view(self, span, lead):
        """Keep the window exactly where it is, so nothing on it moves

        Set once and then left alone. Every change of range costs a relayout
        and makes the axis redraw itself, so a view that is already right must
        not be set again."""
        target = (-lead, span - lead)
        low, high = self.plot.vb.viewRange()[0]
        if abs(low - target[0]) < span * 1e-6 and abs(high - target[1]) < span * 1e-6:
            return
        self.plot.vb.setXRange(target[0], target[1], padding=0)

    def draw_fast(self, oldest, low, high):
        """Draw the high rate trace, and widen the bounds to cover it

        Only when there is something new in it. There can be hundreds of
        thousands of samples, and handing them all to the curve again on every
        redraw of the recording would cost more than everything else here."""
        if self.fast is None or not self.fast.history_size:
            self.curve_fast.clear()
            return low, high

        if self.fast_dirty:
            self.fast_dirty = False
            samples = self.fast.get_buffer()
            # Only the stretch the recording also reaches back to, so that the
            # two traces agree about what the time axis covers. They are in
            # time order, so this is a slice rather than a search of all of them
            first = int(np.searchsorted(samples[:, 0], oldest - self.fast_epoch,
                                        side="left"))
            if first >= len(samples):
                self.curve_fast.clear()
                self.fast_bounds = None
                return low, high

            power = samples[first:, 1]
            self.show_fast(samples[first:, 0] + self.fast_shift, power)
            self.fast_bounds = (float(np.min(power)), float(np.max(power)))

        if self.fast_bounds is None:
            return low, high
        return min(low, self.fast_bounds[0]), max(high, self.fast_bounds[1])

    def recorded_offset(self, index):
        """When a recorded sweep arrived, counted from the epoch"""
        if self.offsets is None or not len(self.offsets):
            return None
        index = min(max(index, 0), len(self.offsets) - 1)
        return float(self.offsets[index])

    def time_offset(self, index):
        """Where a recorded sweep sits on the axis as it is drawn now

        In a sweep the data is moved into a fixed window rather than the
        window along the data, so everything on it is drawn relative to
        whatever that sweep was built about."""
        offset = self.recorded_offset(index)
        if offset is None:
            return None
        if self.time_span and self.sweep_origin is not None:
            return offset - self.sweep_origin
        return offset

    def show_cursor(self, index):
        """Put the browsing cursor on a recorded sweep, or hide it when live

        In a sweep this also decides what the window is drawn about: browsing
        is asking to look at one moment, so that moment is what the sweep is
        built around and the cursor sits in the middle of it."""
        self.browse_offset = None if index is None else self.recorded_offset(index)
        offset = None if index is None else self.time_offset(index)
        if offset is None:
            self.cursor.setVisible(False)
            low, high = self.plot.vb.viewRange()[0]
            self.time_axis.configure(self.reference_time(), high - low)
            return
        self.cursor.blockSignals(True)
        self.cursor.setValue(offset)
        self.cursor.blockSignals(False)
        self.cursor.setVisible(True)
        if not self.time_span:
            self.keep_cursor_in_view(offset)
        low, high = self.plot.vb.viewRange()[0]
        self.time_axis.configure(self.reference_time(), high - low)

    def keep_cursor_in_view(self, offset):
        """Scroll a zoomed-in view along to keep the cursor on screen

        Zooming in is how a burst a few sweeps long is looked at, and stepping
        would otherwise walk the cursor straight off the edge of the plot.
        Only when the user has zoomed: while the view is fitting everything
        it already covers the whole recording, cursor included."""
        if self.fitting_all and self.time_span is None:
            return
        low, high = self.plot.vb.viewRange()[0]
        if low <= offset <= high:
            return
        half = (high - low) / 2
        self.plot.vb.setXRange(offset - half, offset + half, padding=0)

    def cursor_moved(self):
        """Report which recorded sweep the cursor was dragged to"""
        if self.on_time_selected is None or self.offsets is None or not len(self.offsets):
            return
        wanted = self.cursor.value()
        if self.time_span and self.sweep_origin is not None:
            wanted += self.sweep_origin
        self.on_time_selected(int(np.argmin(np.abs(self.offsets - wanted))))

    def clear_plot(self):
        """Clear the power over time plot"""
        self.throttle.reset()
        self.curve.clear()
        self.trace = self.trace_counter = self.times = None
        self.epoch = self.newest = None
        self.offsets = self.sweep_origin = self.browse_offset = None
        self.trigger_time = None
        self.captured = False
        self.armed = self.single
        self.armed_at = None
        self.following = True
        self.clear_fast()
        self.reset_y_range()

    def recalculate_plot(self, data_storage):
        """Rebuild the trace after the recording itself has changed"""
        self.trace = self.trace_counter = None
        if self.throttle.hidden:
            # Off screen, so leave it noted and rebuild it on the way back
            self.throttle.schedule("plot", data_storage)
            return
        self.throttle.reset()
        self.draw(data_storage)


class WaterfallPlotWidget(ThrottledPlotWidget):
    """Waterfall plot"""
    def __init__(self, layout, histogram_layout=None, max_refresh_rate=60,
                 levels_meter=True):
        if histogram_layout and not isinstance(histogram_layout, pg.GraphicsLayoutWidget):
            raise ValueError("histogram_layout must be instance of pyqtgraph.GraphicsLayoutWidget")

        super().__init__(layout, max_refresh_rate)
        self.histogram_layout = histogram_layout
        self.levels_meter = levels_meter
        #: Whether the meter is currently following the image, which is the
        #: only state Qt will not tell us and the only state that costs anything
        self.meter_linked = False

        self.history_size = 100
        self.counter = 0

        self.create_plot()
        if histogram_layout:
            histogram_layout.setVisible(levels_meter)

    def create_plot(self):
        """Create waterfall plot"""
        self.plot = self.layout.addPlot()
        self.plot.setLabel("bottom", "Frequency", units="Hz")
        self.plot.setLabel("left", "Time")

        self.plot.setYRange(-self.history_size, 0)
        self.plot.setLimits(xMin=0, yMax=0)
        self.plot.showButtons()
        #self.plot.setAspectLocked(True)

        self.cache_axes()

        # Setup histogram widget (for controlling waterfall plot levels and gradients)
        if self.histogram_layout:
            self.histogram = pg.HistogramLUTItem()
            self.histogram_layout.addItem(self.histogram)
            self.histogram.gradient.loadPreset("flame")
            #self.histogram.setHistogramRange(-50, 0)
            #self.histogram.setLevels(-50, 0)

    def update_plot(self, data_storage):
        """Queue a waterfall redraw (drawn at up to the throttle's rate)

        Skipping a redraw loses nothing: the whole history buffer is drawn
        every time, so the next redraw still shows every row that arrived
        while this one was being held back."""
        self.throttle.schedule("plot", data_storage)

    def visible_history(self, data_storage):
        """The newest rows of the recording, as many as the waterfall shows

        The recording can be much deeper than the waterfall: it is what the
        history browser steps through, and drawing tens of thousands of rows
        into a plot a couple of hundred pixels tall would only cost time."""
        return data_storage.history.get_buffer()[-self.history_size:]

    def draw(self, data_storage, dirty=None):
        """Redraw the waterfall image"""
        # The redraw was queued at a point when there was data; a reset in
        # between (a new run, or changed settings) can have cleared it since
        if data_storage.x is None or data_storage.history is None:
            return

        self.counter += 1

        # Create waterfall image on first run
        if self.counter == 1:
            self.waterfallImg = pg.ImageItem()
            # A new image carries none of the old one's connections
            self.meter_linked = False
            tr = QtGui.QTransform()
            scale_x = (data_storage.x[-1] - data_storage.x[0]) / len(data_storage.x)
            tr.scale(scale_x, 1)
            self.waterfallImg.setTransform(tr)
            self.plot.clear()
            self.plot.addItem(self.waterfallImg)

        # Roll down one and replace leading edge with new data
        # (row-major image order, so no transpose is needed)
        history = self.visible_history(data_storage)
        self.waterfallImg.setImage(history, autoLevels=False, autoRange=False)

        # Move waterfall image to always start at 0
        self.waterfallImg.setPos(data_storage.x[0], -len(history))

        # Set the colour levels on first run (it must be done after the first
        # data has arrived, or they would be taken from an empty image)
        if self.counter == 1:
            self.setup_levels(history)

    def setup_levels(self, history):
        """Give the waterfall its colour levels, now that there is data to scale to

        With the meter shown it owns the levels and the user can drag them.
        With it hidden they are set here and then left alone, because an image
        with no levels of its own rescales to every frame: the waterfall would
        change brightness as the noise moved rather than showing that it had."""
        if self.levels_meter and self.histogram_layout:
            self.link_levels_meter()
        else:
            self.unlink_levels_meter()
            self.waterfallImg.setLevels((float(np.min(history)), float(np.max(history))))

    def link_levels_meter(self):
        """Point the level meter at the current waterfall image

        setImageItem() connects the image's sigImageChanged without checking
        whether it is connected already, so calling it a second time leaves the
        histogram being recomputed twice on every frame, and a third time three
        times. Qt cannot be asked whether a connection exists, so track it."""
        if self.meter_linked:
            # Already following it, but re-scale the levels to the data, which
            # is what a caller asking to link again is after
            self.histogram.imageChanged(autoLevel=True)
            return
        self.histogram.setImageItem(self.waterfallImg)
        self.meter_linked = True

    def unlink_levels_meter(self):
        """Stop the meter following the image, which is all that it costs

        Linked, it recomputes a histogram of the whole waterfall on every
        redraw. Unlinked it costs nothing, and the image keeps the levels it
        was last given."""
        if not self.meter_linked:
            return
        image = getattr(self, "waterfallImg", None)
        if image is not None:
            image.sigImageChanged.disconnect(self.histogram.imageChanged)
        self.meter_linked = False

    def set_levels_meter(self, enabled):
        """Show or hide the level meter beside the waterfall"""
        if enabled == self.levels_meter:
            return
        self.levels_meter = enabled
        if not self.histogram_layout:
            return

        self.histogram_layout.setVisible(enabled)
        if getattr(self, "waterfallImg", None) is not None:
            self.setup_levels(self.waterfallImg.image)

    def clear_plot(self):
        """Clear waterfall plot"""
        self.throttle.reset()
        self.counter = 0

    def recalculate_plot(self, data_storage):
        """Recalculate waterfall plot"""
        if data_storage.x is None or data_storage.history is None or not self.counter:
            return
        if self.throttle.hidden:
            # Off screen, so leave it noted and redraw it on the way back
            self.throttle.schedule("plot", data_storage)
            return

        self.throttle.reset()
        history = self.visible_history(data_storage)
        self.waterfallImg.setImage(history, autoLevels=False, autoRange=False)
        self.waterfallImg.setPos(data_storage.x[0], -len(history))
        # Subtracting a baseline moves every value, so the levels are scaled
        # to the new data rather than left on the old range
        self.setup_levels(history)
