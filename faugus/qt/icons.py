"""SVG icons for the toolbar — minimal, crisp at any size."""

import logging

logger = logging.getLogger(__name__)

from PySide6.QtGui import QImage, QPixmap
from PySide6.QtCore import QSize
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtGui import QPainter, QColor


def _render_svg(svg_data, size=20, color="#e0d8f0"):
    """Render an SVG string to a QPixmap at the given size and color."""
    logger.debug("_render_svg: size=%s, color=%s, svg_len=%s", size, color, len(svg_data))
    # Replace hardcoded colors with the target color
    svg_data = svg_data.replace("FILLCOLOR", color)
    renderer = QSvgRenderer(bytearray(svg_data.encode()))
    image = QImage(QSize(size, size), QImage.Format_ARGB32)
    image.fill(0)
    painter = QPainter(image)
    renderer.render(painter)
    painter.end()
    return QPixmap.fromImage(image)


# --- Icons (20x20 base, SVG paths) ---

ICON_MENU = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="FILLCOLOR" d="M3 6h18v2H3zm0 5h18v2H3zm0 5h18v2H3z"/></svg>'

ICON_ADD = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="FILLCOLOR" d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6z"/></svg>'

ICON_SETTINGS = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="FILLCOLOR" d="M19.14 12.94c.04-.3.06-.61.06-.94 0-.32-.02-.64-.07-.94l2.03-1.58a.49.49 0 00.12-.61l-1.92-3.32a.49.49 0 00-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54a.484.484 0 00-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96a.49.49 0 00-.59.22L2.74 8.87c-.12.21-.08.47.12.61l2.03 1.58c-.05.3-.07.62-.07.94s.02.64.07.94l-2.03 1.58a.49.49 0 00-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.47-.12-.61zM12 15.6A3.6 3.6 0 1112 8.4a3.6 3.6 0 010 7.2z"/></svg>'

ICON_STOP = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="FILLCOLOR" d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>'

ICON_PLAY = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="FILLCOLOR" d="M8 5v14l11-7z"/></svg>'

ICON_PLAY_SQUARE = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="FILLCOLOR" d="M8 5v14l11-7z"/></svg>'

ICON_KILL = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="FILLCOLOR" d="M6 6h12v12H6z"/></svg>'

ICON_SEARCH = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="FILLCOLOR" d="M15.5 14h-.79l-.28-.27A6.47 6.47 0 0016 9.5 6.5 6.5 0 109.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/></svg>'

ICON_SORT = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="FILLCOLOR" d="M3 18h6v-2H3v2zM3 6v2h18V6H3zm0 7h12v-2H3v2z"/></svg>'

ICON_CATEGORY = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="FILLCOLOR" d="M12 2l-5.5 9h11zm0 3.84L13.93 9h-3.87zm-5.41 3.16L12 20.27 19.41 9H6.59zM12 5.5L7.86 12h8.28z"/></svg>'


def get_icon(name, size=20, color="#e0d8f0"):
    """Get a QPixmap icon by name."""
    logger.debug("get_icon: name=%s, size=%s", name, size)
    icons = {
        "menu": ICON_MENU,
        "add": ICON_ADD,
        "settings": ICON_SETTINGS,
        "stop": ICON_STOP,
        "play": ICON_PLAY,
        "kill": ICON_KILL,
        "search": ICON_SEARCH,
        "sort": ICON_SORT,
        "category": ICON_CATEGORY,
    }
    svg = icons.get(name)
    if svg:
        return _render_svg(svg, size, color)
    return QPixmap()
