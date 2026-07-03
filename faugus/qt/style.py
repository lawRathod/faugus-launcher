"""Qt QSS stylesheet for Faugus Launcher — modern glassmorphism dark theme."""


def get_stylesheet():
    return """
        /* -- Global ------------------------------------ */
        QWidget {
            color: #e8e0f0;
            font-size: 14px;
            font-family: "Segoe UI", "SF Pro Display", "Ubuntu", "Cantarell", sans-serif;
        }

        /* -- Main window ------------------------------ */
        QMainWindow, QWidget#centralWidget {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #0c0a14, stop:0.3 #120e20, stop:0.7 #0e0b1a, stop:1 #080610);
        }

        /* -- Sidebar ---------------------------------- */
        .sidebar {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(16, 12, 28, 0.95), stop:0.5 rgba(12, 9, 22, 0.98), stop:1 rgba(8, 6, 16, 1));
            border-right: 1px solid rgba(138, 92, 246, 0.08);
        }
        .sidebar QPushButton {
            border-radius: 10px;
            margin: 3px 8px;
            padding: 11px 14px;
            background: transparent;
            border: none;
            color: rgba(200, 184, 224, 0.7);
            font-size: 14px;
            font-weight: 500;
            text-align: left;
        }
        .sidebar QPushButton:hover {
            background: rgba(138, 92, 246, 0.08);
            color: rgba(224, 216, 240, 0.95);
        }
        .sidebar QPushButton:checked,
        .sidebar QPushButton.sidebar-active {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 rgba(138, 92, 246, 0.15), stop:1 rgba(138, 92, 246, 0.05));
            color: #ffffff;
            font-weight: 600;
            border-left: 3px solid #8a5cf6;
            border-radius: 0 10px 10px 0;
            margin-left: 0;
            padding-left: 18px;
        }

        /* -- Toolbar buttons -------------------------- */
        QPushButton.flash-btn {
            border-radius: 10px;
            min-width: 34px;
            min-height: 34px;
            padding: 4px;
            background: rgba(138, 92, 246, 0.06);
            border: 1px solid rgba(138, 92, 246, 0.12);
            color: rgba(200, 184, 224, 0.7);
        }
        QPushButton.flash-btn:hover {
            background: rgba(138, 92, 246, 0.15);
            border-color: rgba(138, 92, 246, 0.3);
            color: #ffffff;
        }
        QPushButton.flash-btn:pressed {
            background: rgba(138, 92, 246, 0.25);
        }

        /* -- Search ----------------------------------- */
        QLineEdit {
            border-radius: 12px;
            padding: 10px 16px;
            border: 1px solid rgba(138, 92, 246, 0.1);
            background: rgba(138, 92, 246, 0.04);
            color: #e8e0f0;
            font-size: 14px;
            selection-background-color: rgba(138, 92, 246, 0.3);
        }
        QLineEdit:focus {
            border-color: rgba(138, 92, 246, 0.4);
            background: rgba(138, 92, 246, 0.08);
        }
        QLineEdit::placeholder {
            color: rgba(200, 184, 224, 0.35);
        }

        /* -- Bottom bar buttons ----------------------- */
        QPushButton.bottom-bar-button {
            border-radius: 10px;
            padding: 8px 16px;
            background: rgba(138, 92, 246, 0.05);
            border: 1px solid rgba(138, 92, 246, 0.1);
            color: rgba(200, 184, 224, 0.7);
            font-size: 13px;
            font-weight: 500;
        }
        QPushButton.bottom-bar-button:hover {
            background: rgba(138, 92, 246, 0.12);
            border-color: rgba(138, 92, 246, 0.25);
            color: #ffffff;
        }

        /* -- Scrollbar -------------------------------- */
        QScrollArea { border: none; background: transparent; }
        QScrollBar:vertical {
            width: 6px; background: transparent; margin: 0;
        }
        QScrollBar::handle:vertical {
            background: rgba(138, 92, 246, 0.15);
            border-radius: 3px; min-height: 40px;
        }
        QScrollBar::handle:vertical:hover {
            background: rgba(138, 92, 246, 0.3);
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }

        /* -- Slider ----------------------------------- */
        QSlider::groove:horizontal {
            height: 3px; background: rgba(138, 92, 246, 0.12); border-radius: 2px;
        }
        QSlider::handle:horizontal {
            border-radius: 7px; width: 14px; height: 14px;
            margin: -6px 0; background: qradialgradient(cx:0.5, cy:0.5, radius:0.5,
                stop:0 #a78bfa, stop:1 #7c3aed);
        }
        QSlider::sub-page:horizontal {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #7c3aed, stop:1 #a78bfa);
            border-radius: 2px;
        }

        /* -- Dialogs ---------------------------------- */
        QDialog {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #140e24, stop:1 #0c0918);
        }
        QLabel { color: #e8e0f0; }
        QGroupBox {
            color: rgba(200, 184, 224, 0.8);
            border: 1px solid rgba(138, 92, 246, 0.1);
            border-radius: 8px;
            margin-top: 10px; padding-top: 14px;
        }
        QGroupBox::title {
            subcontrol-origin: margin; padding: 0 8px;
        }
        QCheckBox {
            color: rgba(200, 184, 224, 0.8); spacing: 10px; font-size: 14px;
        }
        QCheckBox::indicator {
            width: 20px; height: 20px; border-radius: 5px;
            border: 1.5px solid rgba(138, 92, 246, 0.3);
            background: rgba(138, 92, 246, 0.05);
        }
        QCheckBox::indicator:checked {
            background: qradialgradient(cx:0.5, cy:0.5, radius:0.5,
                stop:0 #a78bfa, stop:1 #7c3aed);
            border-color: #7c3aed;
        }
        QComboBox {
            padding: 8px 14px; border-radius: 10px;
            border: 1px solid rgba(138, 92, 246, 0.12);
            background: rgba(138, 92, 246, 0.04);
            color: #e8e0f0; min-height: 22px; font-size: 14px;
        }
        QComboBox:hover { border-color: rgba(138, 92, 246, 0.3); }
        QComboBox::drop-down { border: none; width: 28px; }
        QComboBox QAbstractItemView {
            background: #1a1230; color: #e8e0f0;
            border: 1px solid rgba(138, 92, 246, 0.15);
            selection-background-color: rgba(138, 92, 246, 0.2);
            border-radius: 8px; padding: 4px;
        }
        QSpinBox {
            padding: 6px 10px; border-radius: 8px;
            border: 1px solid rgba(138, 92, 246, 0.12);
            background: rgba(138, 92, 246, 0.04); color: #e8e0f0; font-size: 14px;
        }
        QPushButton {
            color: #e8e0f0; font-size: 14px;
        }
        QPushButton:hover {
            background: rgba(138, 92, 246, 0.1);
        }

        /* -- Menus ------------------------------------ */
        QMenu {
            background: rgba(20, 14, 36, 0.97);
            color: #e8e0f0;
            border: 1px solid rgba(138, 92, 246, 0.12);
            border-radius: 10px; padding: 6px;
        }
        QMenu::item {
            padding: 9px 28px; border-radius: 6px; font-size: 14px;
        }
        QMenu::item:selected {
            background: rgba(138, 92, 246, 0.15);
        }
        QMenu::separator {
            height: 1px; background: rgba(138, 92, 246, 0.08); margin: 4px 10px;
        }

        /* -- Tabs ------------------------------------- */
        QTabWidget::pane {
            border: 1px solid rgba(138, 92, 246, 0.1);
            border-radius: 8px; background: rgba(12, 9, 22, 0.5);
        }
        QTabBar::tab {
            background: rgba(138, 92, 246, 0.04);
            color: rgba(200, 184, 224, 0.5);
            padding: 10px 20px; border: none;
            border-bottom: 2px solid transparent;
            font-size: 14px; font-weight: 500;
        }
        QTabBar::tab:selected {
            color: #ffffff; border-bottom-color: #8a5cf6;
        }
        QTabBar::tab:hover { color: rgba(224, 216, 240, 0.8); }

        /* -- Dialog buttons --------------------------- */
        QMessageBox QPushButton, QDialogButtonBox QPushButton {
            min-width: 100px; padding: 10px 22px;
            border-radius: 8px;
            background: rgba(138, 92, 246, 0.08);
            border: 1px solid rgba(138, 92, 246, 0.15);
            color: #e8e0f0; font-size: 14px; font-weight: 500;
        }
        QMessageBox QPushButton:hover, QDialogButtonBox QPushButton:hover {
            background: rgba(138, 92, 246, 0.2);
            border-color: rgba(138, 92, 246, 0.35);
            color: #ffffff;
        }
        QDialogButtonBox QPushButton.primary-btn {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #7c3aed, stop:1 #a78bfa);
            border-color: #8a5cf6;
            color: #ffffff;
            font-weight: 600;
        }
        QDialogButtonBox QPushButton.primary-btn:hover {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #8b5cf6, stop:1 #b79cfb);
        }
    """
