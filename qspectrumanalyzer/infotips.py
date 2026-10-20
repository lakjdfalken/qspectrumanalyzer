"""An [i] beside every control that has a tooltip, saying what the control is when clicked

A tooltip only shows itself to someone who hovers and waits, and goes again
as soon as the mouse moves. So each control that has one gets a small button
on its left, or on its label's left when it has a label: clicking the button
opens the explanation, and clicking it again closes it. The explanation is
the control's own tooltip, read when the button is clicked, so code that
changes a tooltip as things change goes on working; only the hover is
turned off."""

from PySide6 import QtCore, QtGui, QtWidgets


def containing_layout(widget):
    """The layout that has widget directly in it, or None"""
    parent = widget.parentWidget()
    if parent is None or parent.layout() is None:
        return None
    pending = [parent.layout()]
    while pending:
        layout = pending.pop()
        if layout.indexOf(widget) >= 0:
            return layout
        for index in range(layout.count()):
            inner = layout.itemAt(index).layout()
            if inner is not None:
                pending.append(inner)
    return None


def replace_in_layout(layout, widget, holder):
    """Put holder where widget is in layout, at the same position and span

    Returns False, leaving everything as it was, for a layout it cannot do."""
    if isinstance(layout, QtWidgets.QGridLayout):
        position = layout.getItemPosition(layout.indexOf(widget))
        layout.removeWidget(widget)
        layout.addWidget(holder, *position)
    elif isinstance(layout, QtWidgets.QFormLayout):
        row, role = layout.getWidgetPosition(widget)
        layout.removeWidget(widget)
        layout.setWidget(row, role, holder)
    elif isinstance(layout, QtWidgets.QBoxLayout):
        index = layout.indexOf(widget)
        stretch = layout.stretch(index)
        layout.removeWidget(widget)
        layout.insertWidget(index, holder, stretch)
    else:
        return False
    return True


class InfoTips(QtCore.QObject):
    """The [i] buttons under one window, and the one explanation open at a time"""

    def __init__(self, root):
        super().__init__(root)
        #: Controls whose hover is turned off, and the button beside each
        #: control or label that has one
        self.silenced = set()
        self.buttons = {}
        self.popup = None
        self.open_button = None
        self.watched_window = None

        labels = {label.buddy(): label for label in root.findChildren(QtWidgets.QLabel)
                  if label.buddy() is not None}
        for target in root.findChildren(QtWidgets.QWidget):
            # A tool button is an icon whose tooltip is its name, and a
            # popup is no place for that
            if not target.toolTip() or isinstance(target, QtWidgets.QToolButton):
                continue
            anchor = labels.get(target, target)
            # A label and its control can both have one; the label's button
            # serves both
            if anchor not in self.buttons and not self.attach(anchor):
                continue
            self.silenced.update((target, anchor))
            target.installEventFilter(self)

        self.line_up_labels()

        # The panels scroll, and an open explanation should go with its button
        for area in root.findChildren(QtWidgets.QAbstractScrollArea):
            for bar in (area.verticalScrollBar(), area.horizontalScrollBar()):
                bar.valueChanged.connect(self.follow)

    def attach(self, anchor):
        """Put an [i] on anchor's left, where anchor was; False if it cannot"""
        layout = containing_layout(anchor)
        if layout is None:
            return False
        holder = QtWidgets.QWidget(anchor.parentWidget())
        holder.setSizePolicy(anchor.sizePolicy())
        if not replace_in_layout(layout, anchor, holder):
            holder.deleteLater()
            return False
        line = QtWidgets.QHBoxLayout(holder)
        line.setContentsMargins(0, 0, 0, 0)
        line.setSpacing(2)
        button = QtWidgets.QToolButton(holder)
        button.setText("ⓘ")
        button.setAutoRaise(True)
        button.setCheckable(True)
        button.setFocusPolicy(QtCore.Qt.NoFocus)
        button.setAccessibleName(self.tr("What is this?"))
        button.clicked.connect(lambda checked, button=button: self.toggle(button, checked))
        line.addWidget(button)
        line.addWidget(anchor, 1)
        button.setHidden(anchor.isHidden())
        self.buttons[anchor] = button
        # The button comes and goes with what it explains
        anchor.installEventFilter(self)
        return True

    def line_up_labels(self):
        """Indent a form's labels that have no [i] to line up with those that do"""
        for anchor, button in self.buttons.items():
            holder = button.parentWidget()
            layout = containing_layout(holder)
            if not isinstance(layout, QtWidgets.QFormLayout):
                continue
            indent = button.sizeHint().width() + holder.layout().spacing()
            for row in range(layout.rowCount()):
                item = layout.itemAt(row, QtWidgets.QFormLayout.LabelRole)
                label = item.widget() if item is not None else None
                if isinstance(label, QtWidgets.QLabel):
                    label.setIndent(indent)

    def text_for(self, button):
        anchor = next(anchor for anchor, own in self.buttons.items() if own is button)
        for widget in (anchor.buddy() if isinstance(anchor, QtWidgets.QLabel) else None, anchor):
            if widget is not None and widget.toolTip():
                return widget.toolTip()
        return ""

    def toggle(self, button, checked):
        self.close()
        if checked:
            self.open(button)

    def open(self, button):
        window = button.window()
        # A window of its own, at the tooltip level: a child of the main
        # window is drawn under the plots and the panels' scroll areas
        popup = QtWidgets.QLabel(self.text_for(button), window,
                                 QtCore.Qt.ToolTip | QtCore.Qt.FramelessWindowHint)
        popup.setWordWrap(True)
        popup.setTextFormat(QtCore.Qt.AutoText)
        # Solid black on white, or white on near-black in dark mode, rather
        # than the style's pale tooltip yellow
        dark = window.palette().color(QtGui.QPalette.Window).lightness() < 128
        popup.setStyleSheet(
            "QLabel {{ background: {}; color: {}; border: 1px solid {}; padding: 8px; }}".format(
                *(("#1c1c1e", "#ffffff", "#8e8e93") if dark else ("#ffffff", "#000000", "#3a3a3c"))))
        popup.setCursor(QtCore.Qt.PointingHandCursor)
        # A click on the explanation closes it too
        popup.mousePressEvent = lambda event: self.close()
        self.popup, self.open_button, self.watched_window = popup, button, window
        button.setChecked(True)
        window.installEventFilter(self)
        self.follow()
        popup.show()
        popup.raise_()

    def close(self):
        if self.popup is not None:
            self.watched_window.removeEventFilter(self)
            self.popup.deleteLater()
        if self.open_button is not None:
            self.open_button.setChecked(False)
        self.popup = self.open_button = self.watched_window = None

    def follow(self):
        """Keep the open explanation under its button, or close it once the button is out of sight"""
        button, popup = self.open_button, self.popup
        if popup is None:
            return
        if not button.isVisible() or button.visibleRegion().isEmpty():
            self.close()
            return
        screen = button.screen().availableGeometry()
        width = min(button.fontMetrics().averageCharWidth() * 60, screen.width() - 16)
        popup.setFixedWidth(max(width, 100))
        popup.setFixedHeight(popup.heightForWidth(popup.width()))
        top = button.mapToGlobal(QtCore.QPoint(0, 0))
        x = max(screen.left() + 8, min(top.x(), screen.right() - popup.width() - 8))
        y = top.y() + button.height() + 2
        if y + popup.height() > screen.bottom() - 8:
            y = max(screen.top() + 8, top.y() - popup.height() - 2)
        popup.move(x, y)

    def eventFilter(self, watched, event):
        kind = event.type()
        if kind == QtCore.QEvent.ToolTip and watched in self.silenced:
            return True
        if kind in (QtCore.QEvent.Show, QtCore.QEvent.Hide) and watched in self.buttons:
            self.buttons[watched].setHidden(watched.isHidden())
            if watched.isHidden() and self.open_button is self.buttons[watched]:
                self.close()
        if self.popup is not None and watched is self.watched_window:
            if kind in (QtCore.QEvent.Move, QtCore.QEvent.Resize, QtCore.QEvent.LayoutRequest):
                self.follow()
            elif kind in (QtCore.QEvent.WindowDeactivate, QtCore.QEvent.Hide):
                # Floating on top of other applications' windows otherwise
                self.close()
        return super().eventFilter(watched, event)
