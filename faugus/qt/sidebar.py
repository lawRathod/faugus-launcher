"""Sidebar widget — modern design with active indicator."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import (
    QMenu, QPushButton, QVBoxLayout, QWidget, QLabel, QFrame,
)


class Sidebar(QWidget):
    view_changed = Signal(str)
    clear_recents_clicked = Signal()

    _NAV_ITEMS = [
        ("library", "\U0001f4da  Library"),
        ("recents", "\U0001f552  Recents"),
        ("favorites", "\u2b50  Favorites"),
    ]

    def __init__(self, is_big=True, show_sidebar=True, parent=None):
        super().__init__(parent)
        self.buttons = {}
        self.setObjectName("sidebar")
        self.setProperty("class", "sidebar")

        self.setFixedWidth(230 if is_big else 160)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        if is_big:
            header = QWidget()
            header_layout = QVBoxLayout(header)
            header_layout.setContentsMargins(20, 20, 20, 24)
            header_layout.setSpacing(4)

            brand = QLabel("Faugus")
            brand.setStyleSheet(
                "font-size: 22px; font-weight: 700; color: #ffffff;"
                " letter-spacing: 0.5px; background: transparent;"
            )
            header_layout.addWidget(brand)

            subtitle = QLabel("umu frontend")
            subtitle.setStyleSheet(
                "font-size: 12px; color: rgba(200, 184, 224, 0.4);"
                " background: transparent;"
            )
            header_layout.addWidget(subtitle)

            layout.addWidget(header)

            # Divider
            div = QFrame()
            div.setFixedHeight(1)
            div.setStyleSheet("background: rgba(138, 92, 246, 0.08);")
            layout.addWidget(div)

        layout.addSpacing(8)

        # Navigation
        for view_name, label in self._NAV_ITEMS:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setProperty("class", "sidebar-btn")
            btn.clicked.connect(lambda checked, v=view_name: self.set_view(v))

            if view_name == "recents":
                btn.setContextMenuPolicy(Qt.CustomContextMenu)
                btn.customContextMenuRequested.connect(
                    self._show_recents_context_menu)

            layout.addWidget(btn)
            self.buttons[view_name] = btn

        layout.addStretch()

        # Footer version label
        ver = QLabel("v2.0.0")
        ver.setStyleSheet(
            "font-size: 11px; color: rgba(200, 184, 224, 0.2);"
            " background: transparent; padding: 8px 20px;"
        )
        layout.addWidget(ver)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.setVisible(show_sidebar)

    def set_view(self, view_name):
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
        menu = QMenu(self)
        clear_action = menu.addAction("\U0001f5d1  Clear recents")
        clear_action.triggered.connect(self.clear_recents_clicked.emit)
        menu.exec_(QCursor.pos())
