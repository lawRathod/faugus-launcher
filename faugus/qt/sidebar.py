from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import (
    QMenu,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class Sidebar(QWidget):
    """Left-hand sidebar with three view-toggle buttons.

    Parameters
    ----------
    is_big : bool
        When *True* a "Faugus" brand header is shown above the buttons.
    show_sidebar : bool
        Initial visibility of the sidebar.
    """

    view_changed = Signal(str)
    clear_recents_clicked = Signal()

    _NAV_ITEMS = [
        ("library", "Library"),
        ("recents", "Recents"),
        ("favorites", "Favorites"),
    ]

    def __init__(self, is_big=True, show_sidebar=True, parent=None):
        super().__init__(parent)
        self.buttons = {}
        self.setObjectName("sidebar")
        self.setProperty("class", "sidebar")

        self.setFixedWidth(200 if is_big else 140)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 10, 6, 10)
        layout.setSpacing(4)

        # --- Header (big mode only) ---
        if is_big:
            header = QWidget()
            header.setProperty("class", "sidebar-header")
            header_layout = QVBoxLayout(header)
            header_layout.setContentsMargins(6, 4, 6, 8)
            header_label = QPushButton("Faugus")
            header_label.setEnabled(False)
            header_label.setProperty("class", "sidebar-header-label")
            header_layout.addWidget(header_label)
            layout.addWidget(header)

        # --- Navigation buttons ---
        for view_name, label in self._NAV_ITEMS:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setProperty("class", "sidebar-btn")
            btn.clicked.connect(lambda checked, v=view_name: self.set_view(v))

            if view_name == "recents":
                btn.setContextMenuPolicy(Qt.CustomContextMenu)
                btn.customContextMenuRequested.connect(
                    self._show_recents_context_menu
                )

            layout.addWidget(btn)
            self.buttons[view_name] = btn

        layout.addStretch()

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.setVisible(show_sidebar)

    def set_view(self, view_name):
        """Highlight the active button and emit *view_changed*."""
        for name, btn in self.buttons.items():
            btn.setChecked(name == view_name)
            if name == view_name:
                btn.setProperty("class", "sidebar-btn sidebar-active")
            else:
                btn.setProperty("class", "sidebar-btn")
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        self.view_changed.emit(view_name)

    def _show_recents_context_menu(self, pos):
        """Right-click context menu on the Recents button."""
        menu = QMenu(self)
        clear_action = menu.addAction("Clear recents")
        clear_action.triggered.connect(self.clear_recents_clicked.emit)
        menu.exec_(QCursor.pos())
