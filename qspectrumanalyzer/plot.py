import collections, math, time

from PySide6 import QtCore, QtGui
import pyqtgraph as pg

# Basic PyQtGraph settings
#
# Antialiasing is off globally, which keeps the axes and the crosshair cheap,
# and is turned back on per curve when the setting asks for it. Row-major
# image order lets the waterfall hand its history buffer to ImageItem without
# transposing (and copying) it on every frame.
pg.setConfigOptions(antialias=False, imageAxisOrder='row-major')


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
        self.frozen = False
        self._timer = QtCore.QTimer()
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.flush_now)

    def schedule(self, kind, data_storage):
        """Mark one kind of curve as needing a redraw"""
        self._storage = data_storage
        self._dirty.add(kind)

        if self.frozen:
            # Browsing recorded sweeps: keep noting what is stale, but leave
            # the plot alone until the live view is resumed
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
        if frozen:
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
        self._last_draw = time.monotonic()
        self._flush(storage, dirty)

    def reset(self):
        """Forget anything pending (used when the plot is cleared)"""
        self._timer.stop()
        self._dirty = set()
        self._storage = None
        self._last_draw = 0.0


class ThrottledPlotWidget:
    """A plot whose redraws are coalesced by a RedrawThrottle"""
    def __init__(self, layout, max_refresh_rate=60):
        if not isinstance(layout, pg.GraphicsLayoutWidget):
            raise ValueError("layout must be instance of pyqtgraph.GraphicsLayoutWidget")

        self.layout = layout
        self.throttle = RedrawThrottle(max_refresh_rate, self.draw)

    def draw(self, data_storage, dirty):
        """Redraw whatever the throttle has been holding"""
        raise NotImplementedError

    def set_frozen(self, frozen):
        """Stop redrawing (while recorded sweeps are being browsed)"""
        self.throttle.set_frozen(frozen)

    def set_max_refresh_rate(self, max_refresh_rate):
        """Change how often this plot may be redrawn"""
        self.throttle.set_max_refresh_rate(max_refresh_rate)


class SpectrumPlotWidget(ThrottledPlotWidget):
    """Main spectrum plot"""
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

    def queue_redraw(self, kind, data_storage, force):
        """Draw at once when forced, otherwise let the throttle pick the moment"""
        if force:
            getattr(self, "draw_" + kind)(data_storage, force=True)
        else:
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
        self.curve.clear()

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


class WaterfallPlotWidget(ThrottledPlotWidget):
    """Waterfall plot"""
    def __init__(self, layout, histogram_layout=None, max_refresh_rate=60):
        if histogram_layout and not isinstance(histogram_layout, pg.GraphicsLayoutWidget):
            raise ValueError("histogram_layout must be instance of pyqtgraph.GraphicsLayoutWidget")

        super().__init__(layout, max_refresh_rate)
        self.histogram_layout = histogram_layout

        self.history_size = 100
        self.counter = 0

        self.create_plot()

    def create_plot(self):
        """Create waterfall plot"""
        self.plot = self.layout.addPlot()
        self.plot.setLabel("bottom", "Frequency", units="Hz")
        self.plot.setLabel("left", "Time")

        self.plot.setYRange(-self.history_size, 0)
        self.plot.setLimits(xMin=0, yMax=0)
        self.plot.showButtons()
        #self.plot.setAspectLocked(True)

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

        # Link histogram widget to waterfall image on first run
        # (must be done after first data is received or else levels would be wrong)
        if self.counter == 1 and self.histogram_layout:
            self.histogram.setImageItem(self.waterfallImg)

    def clear_plot(self):
        """Clear waterfall plot"""
        self.throttle.reset()
        self.counter = 0

    def recalculate_plot(self, data_storage):
        """Recalculate waterfall plot"""
        if data_storage.x is None or data_storage.history is None or not self.counter:
            return

        self.throttle.reset()
        history = self.visible_history(data_storage)
        self.waterfallImg.setImage(history, autoLevels=False, autoRange=False)
        self.waterfallImg.setPos(data_storage.x[0], -len(history))
        self.histogram.setImageItem(self.waterfallImg)
