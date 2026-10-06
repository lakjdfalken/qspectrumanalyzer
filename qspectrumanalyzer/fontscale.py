"""Making every piece of text in the app bigger or smaller at once

Setting the application font reaches every widget that takes its font from
its parent, but not the ones that were given a font of their own: the
monospaced readout, the small section headings, the report pages. Those keep
the size they were handed and would stay small while everything round them
grew. So each of those is scaled by hand as well, and marked with the scale
it is at, so that it is never scaled twice.

That walk covers the widgets that exist. A window opened afterwards that
asks the platform for its fixed-width font gets it at the platform's size,
so it is given one through set_fixed_font() instead. No event filter
catches new windows: one on the application runs Python for every event in
the app, repaints included, and those already hold the interpreter lock
longer than the radio can wait.
"""

from PySide6 import QtCore, QtGui

#: Steps the size goes through, as fractions of the platform's own
STEPS = (0.75, 0.85, 1.0, 1.15, 1.3, 1.5, 1.75, 2.0)

_PROPERTY = "qsa_font_scale"

#: The scale in force, for set_fixed_font()
_scale = 1.0


def set_fixed_font(widget, smaller=0.0):
    """Give a widget the platform's fixed-width font, at the size the rest of
    the text is at, less `smaller` points of the platform's size"""
    font = QtGui.QFontDatabase.systemFont(QtGui.QFontDatabase.FixedFont)
    if font.pointSizeF() > 0:
        font.setPointSizeF(max(8.0, font.pointSizeF() - smaller) * _scale)
    widget.setFont(font)
    widget.setProperty(_PROPERTY, _scale)


class FontScale:
    """Holds the scale and keeps every widget's text at it

    Made after the main window is built, while every font in it is still at
    the platform's size: a widget that had set its own font from an already
    scaled one could not be told apart from one that had not, and would be
    scaled twice."""

    def __init__(self, app, scale=1.0):
        self.app = app
        #: The font the platform gave the app, which every scale is taken from
        self.base = QtGui.QFont(app.font())
        self.scale = 1.0
        self.set_scale(scale)

    def set_scale(self, scale):
        """Put every piece of text at this fraction of the platform's size"""
        global _scale
        scale = min(max(scale, STEPS[0]), STEPS[-1])
        self.scale = _scale = scale
        font = QtGui.QFont(self.base)
        font.setPointSizeF(self.base.pointSizeF() * scale)
        self.app.setFont(font)
        for widget in self.app.allWidgets():
            self.fix(widget)

    def bigger(self):
        self.set_scale(next((s for s in STEPS if s > self.scale + 1e-6), STEPS[-1]))

    def smaller(self):
        self.set_scale(next((s for s in reversed(STEPS) if s < self.scale - 1e-6), STEPS[0]))

    def reset(self):
        self.set_scale(1.0)

    def fix(self, widget):
        """Scale a widget that was given a font of its own, if it is not yet

        One given its font through set_fixed_font() is marked with the scale
        it was made at, so it is scaled only by what has changed since."""
        if not widget.testAttribute(QtCore.Qt.WA_SetFont):
            return
        done = widget.property(_PROPERTY) or 1.0
        if abs(done - self.scale) < 1e-6:
            return
        font = widget.font()
        if font.pointSizeF() > 0:
            font.setPointSizeF(font.pointSizeF() * self.scale / done)
        elif font.pixelSize() > 0:
            font.setPixelSize(max(1, round(font.pixelSize() * self.scale / done)))
        widget.setFont(font)
        widget.setProperty(_PROPERTY, self.scale)
