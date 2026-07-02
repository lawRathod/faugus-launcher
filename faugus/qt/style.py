"""Qt QSS stylesheet for Faugus Launcher — dark purple gradient theme."""


def get_stylesheet():
    return """
        /* -- Global ------------------------------------ */
        QWidget {
            color: #e0d8f0;
            font-size: 13px;
        }

        /* -- Main window background ------------------- */
        QMainWindow {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #120c1c, stop:0.5 #1a1030, stop:1 #0f0a1a);
        }
        QWidget#centralWidget {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #120c1c, stop:0.5 #1a1030, stop:1 #0f0a1a);
        }

        /* -- Sidebar ---------------------------------- */
        .sidebar {
            border-right: 1px solid rgba(138, 92, 246, 0.15);
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(20, 14, 32, 0.9), stop:1 rgba(15, 10, 24, 0.95));
        }
        .sidebar QPushButton {
            border-radius: 8px;
            margin: 2px 6px;
            padding: 8px 6px;
            background: transparent;
            border: none;
            color: #c8b8e0;
            font-size: 13px;
            text-align: left;
        }
        .sidebar QPushButton:hover {
            background: rgba(138, 92, 246, 0.12);
            color: #e8ddf8;
        }
        .sidebar QPushButton:checked,
        .sidebar QPushButton.sidebar-active {
            background: rgba(138, 92, 246, 0.22);
            color: #ffffff;
            font-weight: 600;
        }

        /* -- Flash buttons (toolbar) ------------------ */
        QPushButton.flash-btn {
            border-radius: 8px;
            min-width: 36px;
            min-height: 36px;
            padding: 6px;
            background: rgba(138, 92, 246, 0.1);
            border: 1px solid rgba(138, 92, 246, 0.2);
            color: #d8ccf0;
        }
        QPushButton.flash-btn:hover {
            background: rgba(138, 92, 246, 0.25);
            border-color: rgba(138, 92, 246, 0.4);
            color: #ffffff;
        }

        /* -- Search entry ----------------------------- */
        QLineEdit {
            border-radius: 8px;
            padding: 6px 12px;
            border: 1px solid rgba(138, 92, 246, 0.2);
            background: rgba(30, 20, 48, 0.8);
            color: #e0d8f0;
            font-size: 13px;
        }
        QLineEdit:focus {
            border-color: #8a5cf6;
            background: rgba(40, 28, 62, 0.9);
        }
        QLineEdit::placeholder {
            color: rgba(200, 184, 224, 0.5);
        }

        /* -- Bottom bar buttons (sort/category) ------- */
        QPushButton.bottom-bar-button {
            border-radius: 8px;
            padding: 6px 12px;
            background: rgba(138, 92, 246, 0.08);
            border: 1px solid rgba(138, 92, 246, 0.15);
            color: #c8b8e0;
            font-size: 12px;
        }
        QPushButton.bottom-bar-button:hover {
            background: rgba(138, 92, 246, 0.2);
            border-color: rgba(138, 92, 246, 0.35);
            color: #ffffff;
        }

        /* -- Empty state ------------------------------ */
        .empty-state-title {
            font-size: 18px;
            font-weight: 600;
            color: #e0d8f0;
        }
        .empty-state-subtitle {
            font-size: 13px;
            color: rgba(200, 184, 224, 0.6);
        }

        /* -- Scroll area ------------------------------ */
        QScrollArea {
            border: none;
            background: transparent;
        }
        QScrollBar:vertical {
            width: 8px;
            background: transparent;
        }
        QScrollBar::handle:vertical {
            background: rgba(138, 92, 246, 0.25);
            border-radius: 4px;
            min-height: 30px;
        }
        QScrollBar::handle:vertical:hover {
            background: rgba(138, 92, 246, 0.4);
        }
        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {
            height: 0px;
        }

        /* -- Slider ----------------------------------- */
        QSlider::groove:horizontal {
            height: 4px;
            background: rgba(138, 92, 246, 0.2);
            border-radius: 2px;
        }
        QSlider::handle:horizontal {
            border-radius: 50%;
            min-width: 14px;
            min-height: 14px;
            margin: -5px 0;
            background: #8a5cf6;
        }
        QSlider::sub-page:horizontal {
            background: #8a5cf6;
            border-radius: 2px;
        }

        /* -- Dialogs ---------------------------------- */
        QDialog {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #1e1432, stop:1 #140e22);
        }
        QLabel {
            color: #e0d8f0;
        }
        QGroupBox {
            color: #e0d8f0;
            border: 1px solid rgba(138, 92, 246, 0.2);
            border-radius: 6px;
            margin-top: 8px;
            padding-top: 12px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            padding: 0 6px;
            color: #c8b8e0;
        }
        QCheckBox {
            color: #c8b8e0;
            spacing: 8px;
        }
        QCheckBox::indicator {
            width: 18px;
            height: 18px;
            border-radius: 4px;
            border: 1px solid rgba(138, 92, 246, 0.35);
            background: rgba(30, 20, 48, 0.6);
        }
        QCheckBox::indicator:checked {
            background: #8a5cf6;
            border-color: #8a5cf6;
        }
        QComboBox {
            padding: 6px 12px;
            border-radius: 8px;
            border: 1px solid rgba(138, 92, 246, 0.2);
            background: rgba(30, 20, 48, 0.7);
            color: #e0d8f0;
            min-height: 20px;
        }
        QComboBox:hover {
            border-color: rgba(138, 92, 246, 0.45);
        }
        QComboBox::drop-down {
            border: none;
            width: 24px;
        }
        QComboBox QAbstractItemView {
            background: #251a3a;
            color: #e0d8f0;
            border: 1px solid rgba(138, 92, 246, 0.25);
            selection-background-color: rgba(138, 92, 246, 0.35);
        }
        QSpinBox {
            padding: 4px 8px;
            border-radius: 6px;
            border: 1px solid rgba(138, 92, 246, 0.2);
            background: rgba(30, 20, 48, 0.7);
            color: #e0d8f0;
        }
        QPushButton {
            color: #e0d8f0;
        }
        QPushButton:hover {
            background: rgba(138, 92, 246, 0.15);
        }

        /* -- Menu ------------------------------------- */
        QMenu {
            background-color: #251a3a;
            color: #e0d8f0;
            border: 1px solid rgba(138, 92, 246, 0.25);
            border-radius: 8px;
            padding: 4px;
        }
        QMenu::item {
            padding: 6px 24px;
            border-radius: 4px;
        }
        QMenu::item:selected {
            background: rgba(138, 92, 246, 0.3);
        }
        QMenu::separator {
            height: 1px;
            background: rgba(138, 92, 246, 0.15);
            margin: 4px 8px;
        }

        /* -- Tab widget ------------------------------- */
        QTabWidget::pane {
            border: 1px solid rgba(138, 92, 246, 0.15);
            border-radius: 6px;
            background: rgba(20, 14, 32, 0.5);
        }
        QTabBar::tab {
            background: rgba(138, 92, 246, 0.06);
            color: rgba(200, 184, 224, 0.6);
            padding: 8px 16px;
            border: none;
            border-bottom: 2px solid transparent;
        }
        QTabBar::tab:selected {
            color: #ffffff;
            border-bottom-color: #8a5cf6;
        }
        QTabBar::tab:hover {
            color: #e0d8f0;
        }

        /* -- Message box / buttons -------------------- */
        QMessageBox QPushButton,
        QDialogButtonBox QPushButton {
            min-width: 80px;
            padding: 6px 16px;
            border-radius: 6px;
            background: rgba(138, 92, 246, 0.12);
            border: 1px solid rgba(138, 92, 246, 0.25);
            color: #e0d8f0;
        }
        QMessageBox QPushButton:hover,
        QDialogButtonBox QPushButton:hover {
            background: rgba(138, 92, 246, 0.3);
            border-color: rgba(138, 92, 246, 0.5);
            color: #ffffff;
        }
    """
