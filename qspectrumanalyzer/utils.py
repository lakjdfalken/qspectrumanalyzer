import numpy as np

from PySide6 import QtCore, QtGui, QtWidgets


def smooth(x, window_len=11, window='hanning'):
    """Smooth 1D signal using specified window with given size"""
    x = np.array(x)
    if window_len < 3:
        return x

    if x.size < window_len:
        raise ValueError("Input data length must be greater than window size")

    if window not in ['rectangular', 'hanning', 'hamming', 'bartlett', 'blackman']:
        raise ValueError("Window must be 'rectangular', 'hanning', 'hamming', 'bartlett' or 'blackman'")

    if window == 'rectangular':
        # Moving average
        w = np.ones(window_len, 'd')
    else:
        w = getattr(np, window)(window_len)

    s = np.r_[2 * x[0] - x[window_len:1:-1], x, 2 * x[-1] - x[-1:-window_len:-1]]
    y = np.convolve(w / w.sum(), s, mode='same')

    return y[window_len - 1:-window_len + 1]


def str_to_color(color_string):
    """Create QColor from comma sepparated RGBA string"""
    return QtGui.QColor(*[int(c.strip()) for c in color_string.split(',')])


def color_to_str(color):
    """Create comma separated RGBA string from QColor"""
    return ", ".join([str(color.red()), str(color.green()), str(color.blue()), str(color.alpha())])


def human_time(seconds):
    """Format time in seconds to human readable form (e.g. 1 h 2 min 3 s)"""
    seconds = int(seconds)
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)

    if h > 0:
        timestr = '{:.0f} h {:.0f} min {:.0f} s'.format(h, m, s)
    elif m > 0:
        timestr = '{:.0f} min {:.0f} s'.format(m, s)
    else:
        timestr = '{:.0f} s'.format(s)

    return timestr


class WheelGuard(QtCore.QObject):
    """Stops the wheel changing a value the pointer only passed over

    A panel of settings has to scroll, and a spin box under the pointer takes
    the wheel before the scroll area does. So scrolling down the controls
    moves the gain, or the bin size, or the trigger level, and the only sign
    is that a later measurement comes out wrong - the same failure as every
    other one in this program, where a setting that changed without saying so
    looks exactly like a band with nothing in it.

    A box now moves only once it has been clicked into. Tab still reaches them
    all, because the focus policy is strong rather than none, and a box that
    really does have the focus still takes the wheel.

"""

    #: Deliberately not QAbstractSlider: a scroll bar is one, and swallowing
    #: its wheel would break the scrolling this exists to protect.
    KINDS = (QtWidgets.QAbstractSpinBox, QtWidgets.QComboBox)

    def eventFilter(self, watched, event):
        if event.type() == QtCore.QEvent.Type.Wheel and not watched.hasFocus():
            event.ignore()
            return True
        return super().eventFilter(watched, event)


def guard_against_the_wheel(window):
    """Fit every spin box and drop-down in `window` with a WheelGuard

    The guard is parented to the window so it lives as long as the widgets it
    is filtering, and returned so a caller can keep it if it would rather."""
    guard = WheelGuard(window)
    for kind in WheelGuard.KINDS:
        for widget in window.findChildren(kind):
            widget.setFocusPolicy(QtCore.Qt.StrongFocus)
            widget.installEventFilter(guard)
    return guard
