"""Flow layout for Qt that mimics GTK FlowBox behavior.

Arranges child widgets in a flow that wraps to the next row when the
current row is full. Based on the well-known Qt FlowLayout pattern.
"""

import logging

logger = logging.getLogger(__name__)

from PySide6.QtCore import Qt, QRect, QSize, QPoint
from PySide6.QtWidgets import QLayout, QLayoutItem, QSizePolicy, QSpacerItem


class FlowLayout(QLayout):
    """A layout that arranges widgets in a flow, wrapping to the next row.

    Children are placed left-to-right. When a row is full (or the available
    width is exceeded), the next child starts a new row. Optionally constrains
    the number of children per line.

    Args:
        parent: Parent widget.
        margin: Layout margin in pixels.
        h_spacing: Horizontal spacing between items.
        v_spacing: Vertical spacing between rows.
    """

    def __init__(self, parent=None, margin=-1, h_spacing=-1, v_spacing=-1):
        logger.debug("FlowLayout.__init__: margin=%s, h_spacing=%s, v_spacing=%s", margin, h_spacing, v_spacing)
        super().__init__(parent)
        if margin != -1:
            self.setContentsMargins(margin, margin, margin, margin)
        self._h_spacing = h_spacing if h_spacing >= 0 else 6
        self._v_spacing = v_spacing if v_spacing >= 0 else 6
        self._items = []
        self._min_columns = 1
        self._max_columns = 0  # 0 = unlimited

    def addItem(self, item):
        logger.debug("FlowLayout.addItem")
        self._items.append(item)

    def horizontalSpacing(self):
        return self._h_spacing

    def verticalSpacing(self):
        return self._v_spacing

    def setHorizontalSpacing(self, spacing):
        logger.debug("FlowLayout.setHorizontalSpacing: spacing=%s", spacing)
        self._h_spacing = spacing
        self.invalidate()

    def setVerticalSpacing(self, spacing):
        logger.debug("FlowLayout.setVerticalSpacing: spacing=%s", spacing)
        self._v_spacing = spacing
        self.invalidate()

    def setMinColumns(self, count):
        """Set the minimum number of children per row."""
        logger.debug("FlowLayout.setMinColumns: count=%s", count)
        self._min_columns = max(1, count)
        self.invalidate()

    def setMaxColumns(self, count):
        """Set the maximum number of children per row (0 = unlimited)."""
        logger.debug("FlowLayout.setMaxColumns: count=%s", count)
        self._max_columns = max(0, count)
        self.invalidate()

    def count(self):
        return len(self._items)

    def itemAt(self, index):
        if 0 <= index < len(self._items):
            return self._items[index]
        return None

    def takeAt(self, index):
        logger.debug("FlowLayout.takeAt: index=%s, count=%s", index, len(self._items))
        if 0 <= index < len(self._items):
            return self._items.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientations(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        logger.debug("FlowLayout.heightForWidth: width=%s", width)
        return self._do_layout(QRect(0, 0, width, 0), test_only=True)

    def setGeometry(self, rect):
        logger.debug("FlowLayout.setGeometry: rect=%s", rect)
        super().setGeometry(rect)
        self._do_layout(rect, test_only=False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        logger.debug("FlowLayout.minimumSize: item_count=%s", len(self._items))
        size = QSize(0, 0)
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        m = self.contentsMargins()
        size += QSize(m.left() + m.right(), m.top() + m.bottom())
        return size

    def invalidate(self):
        logger.debug("FlowLayout.invalidate")
        super().invalidate()

    def items(self):
        """Iterate over all contained items."""
        logger.debug("FlowLayout.items: count=%s", len(self._items))
        return list(self._items)

    def _do_layout(self, rect, test_only):
        logger.debug("FlowLayout._do_layout: rect=%s, test_only=%s, item_count=%s", rect, test_only, len(self._items))
        m = self.contentsMargins()
        effective = rect.adjusted(m.left(), m.top(), -m.right(), -m.bottom())
        x = effective.x()
        y = effective.y()
        line_height = 0

        items_per_line = 0

        for item in self._items:
            wid = item.widget()
            space_x = self._h_spacing
            space_y = self._v_spacing

            next_x = x + item.sizeHint().width() + space_x
            if next_x - space_x > effective.right() + 1 and line_height > 0:
                # Wrapping to a new line
                x = effective.x()
                y = y + line_height + space_y
                next_x = x + item.sizeHint().width() + space_x
                line_height = 0
                items_per_line = 0

            items_per_line += 1

            if self._max_columns > 0 and items_per_line > self._max_columns:
                x = effective.x()
                y = y + line_height + space_y
                next_x = x + item.sizeHint().width() + space_x
                line_height = 0
                items_per_line = 1

            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))

            x = next_x
            line_height = max(line_height, item.sizeHint().height())

        return y + line_height - rect.y() + m.bottom()
