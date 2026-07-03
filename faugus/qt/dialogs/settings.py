"""Settings dialog for Faugus Launcher (Qt)."""

import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from faugus.core.config import AppConfig
from faugus.path_manager import PathManager


class SettingsDialog(QDialog):
    """Application settings dialog."""

    def __init__(self, parent, cfg: AppConfig):
        super().__init__(parent)
        self.cfg = cfg
        self.setWindowTitle("Settings")
        self.setMinimumSize(500, 550)
        self.setModal(True)

        layout = QVBoxLayout(self)

        tabs = QTabWidget()

        # General tab
        tabs.addTab(self._build_general_tab(), "General")
        # Appearance tab
        tabs.addTab(self._build_appearance_tab(), "Appearance")
        # Runner tab
        tabs.addTab(self._build_runner_tab(), "Runner")
        # Advanced tab
        tabs.addTab(self._build_advanced_tab(), "Advanced")

        layout.addWidget(tabs, 1)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_ok)
        buttons.rejected.connect(self.reject)
        ok_btn = buttons.button(QDialogButtonBox.Ok)
        ok_btn.setProperty("class", "primary-btn")
        ok_btn.style().unpolish(ok_btn)
        ok_btn.style().polish(ok_btn)
        layout.addWidget(buttons)

        self._load_values()

    def _build_general_tab(self):
        w = QWidget()
        form = QFormLayout(w)
        form.setSpacing(10)

        self.chk_close_on_launch = QCheckBox("Close launcher when game starts")
        form.addRow(self.chk_close_on_launch)

        self.chk_show_labels = QCheckBox("Show game labels")
        form.addRow(self.chk_show_labels)

        self.chk_show_hidden = QCheckBox("Show hidden games")
        form.addRow(self.chk_show_hidden)

        self.chk_show_categories = QCheckBox("Show categories")
        form.addRow(self.chk_show_categories)

        self.chk_gamepad = QCheckBox("Gamepad navigation")
        form.addRow(self.chk_gamepad)

        self.chk_prevent_sleep = QCheckBox("Prevent sleep while gaming")
        form.addRow(self.chk_prevent_sleep)

        return w

    def _build_appearance_tab(self):
        w = QWidget()
        form = QFormLayout(w)
        form.setSpacing(10)

        self.cmb_interface = QComboBox()
        self.cmb_interface.addItems(["List", "Blocks", "Banners"])
        form.addRow("Interface mode:", self.cmb_interface)

        self.chk_system_tray = QCheckBox("Enable system tray icon")
        form.addRow(self.chk_system_tray)

        self.chk_mono_icon = QCheckBox("Use mono tray icon")
        form.addRow(self.chk_mono_icon)

        self.chk_show_sidebar = QCheckBox("Show sidebar")
        form.addRow(self.chk_show_sidebar)

        self.cmb_behavior = QComboBox()
        self.cmb_behavior.addItems(["None", "Remember", "Maximized", "Fullscreen"])
        form.addRow("Window behavior:", self.cmb_behavior)

        return w

    def _build_runner_tab(self):
        w = QWidget()
        form = QFormLayout(w)
        form.setSpacing(10)

        self.cmb_runner = QComboBox()
        proton_cachyos = PathManager.system_data("steam/compatibilitytools.d/proton-cachyos-slr/")
        compat_dir = os.path.expanduser("~/.local/share/Steam/compatibilitytools.d")
        from faugus.core.utils import build_runner_list
        for r in build_runner_list(proton_cachyos, compat_dir):
            self.cmb_runner.addItem(r)
        form.addRow("Default runner:", self.cmb_runner)

        self.txt_prefix = QLineEdit()
        form.addRow("Default prefix:", self.txt_prefix)

        self.chk_mangohud = QCheckBox("Enable MangoHud by default")
        form.addRow(self.chk_mangohud)

        self.chk_gamemode = QCheckBox("Enable GameMode by default")
        form.addRow(self.chk_gamemode)

        self.chk_disable_hidraw = QCheckBox("Disable HIDRAW by default")
        form.addRow(self.chk_disable_hidraw)

        self.chk_wayland = QCheckBox("Enable Wayland driver")
        form.addRow(self.chk_wayland)

        self.chk_wow64 = QCheckBox("Enable WoW64")
        form.addRow(self.chk_wow64)

        return w

    def _build_advanced_tab(self):
        w = QWidget()
        form = QFormLayout(w)
        form.setSpacing(10)

        self.chk_logging = QCheckBox("Enable Proton logging")
        form.addRow(self.chk_logging)

        self.chk_disable_updates = QCheckBox("Disable component updates")
        form.addRow(self.chk_disable_updates)

        self.chk_splash = QCheckBox("Disable splash screen")
        form.addRow(self.chk_splash)

        self.chk_donate = QCheckBox("Show donate reminder")
        form.addRow(self.chk_donate)

        return w

    def _load_values(self):
        self.chk_close_on_launch.setChecked(self.cfg.close_on_launch)
        self.chk_show_labels.setChecked(self.cfg.show_labels)
        self.chk_show_hidden.setChecked(self.cfg.show_hidden)
        self.chk_show_categories.setChecked(self.cfg.show_categories)
        self.chk_gamepad.setChecked(self.cfg.gamepad_navigation)
        self.chk_prevent_sleep.setChecked(self.cfg.prevent_sleep)

        idx = self.cmb_interface.findText(self.cfg.interface_mode)
        if idx >= 0:
            self.cmb_interface.setCurrentIndex(idx)
        self.chk_system_tray.setChecked(self.cfg.system_tray)
        self.chk_mono_icon.setChecked(self.cfg.mono_icon)
        self.chk_show_sidebar.setChecked(self.cfg.show_sidebar)
        idx = self.cmb_behavior.findText(self.cfg.window_behavior)
        if idx >= 0:
            self.cmb_behavior.setCurrentIndex(idx)

        idx = self.cmb_runner.findText(self.cfg.default_runner)
        if idx >= 0:
            self.cmb_runner.setCurrentIndex(idx)
        self.txt_prefix.setText(self.cfg.default_prefix)
        self.chk_mangohud.setChecked(self.cfg.mangohud)
        self.chk_gamemode.setChecked(self.cfg.gamemode)
        self.chk_disable_hidraw.setChecked(self.cfg.disable_hidraw)
        self.chk_wayland.setChecked(self.cfg.wayland_driver)
        self.chk_wow64.setChecked(self.cfg.enable_wow64)

        self.chk_logging.setChecked(self.cfg.enable_logging)
        self.chk_disable_updates.setChecked(self.cfg.disable_updates)
        self.chk_splash.setChecked(self.cfg.splash_disable)
        self.chk_donate.setChecked(self.cfg.show_donate)

    def _on_ok(self):
        self.cfg.set("close-onlaunch", self.chk_close_on_launch.isChecked())
        self.cfg.set("show-labels", self.chk_show_labels.isChecked())
        self.cfg.set("show-hidden", self.chk_show_hidden.isChecked())
        self.cfg.set("show-categories", self.chk_show_categories.isChecked())
        self.cfg.set("gamepad-navigation", self.chk_gamepad.isChecked())
        self.cfg.set("prevent-sleep", self.chk_prevent_sleep.isChecked())

        self.cfg.set("interface-mode", self.cmb_interface.currentText())
        self.cfg.set("system-tray", self.chk_system_tray.isChecked())
        self.cfg.set("mono-icon", self.chk_mono_icon.isChecked())
        self.cfg.set("show-sidebar", self.chk_show_sidebar.isChecked())
        self.cfg.set("window-behavior", self.cmb_behavior.currentText())

        runner_text = self.cmb_runner.currentText()
        if runner_text.endswith(" (default)"):
            runner_text = runner_text.replace(" (default)", "")
        self.cfg.set("default-runner", runner_text)
        self.cfg.set("default-prefix", self.txt_prefix.text())
        self.cfg.set("mangohud", self.chk_mangohud.isChecked())
        self.cfg.set("gamemode", self.chk_gamemode.isChecked())
        self.cfg.set("disable-hidraw", self.chk_disable_hidraw.isChecked())
        self.cfg.set("wayland-driver", self.chk_wayland.isChecked())
        self.cfg.set("enable-wow64", self.chk_wow64.isChecked())

        self.cfg.set("enable-logging", self.chk_logging.isChecked())
        self.cfg.set("disable-updates", self.chk_disable_updates.isChecked())
        self.cfg.set("splash-disable", self.chk_splash.isChecked())
        self.cfg.set("show-donate", self.chk_donate.isChecked())

        self.cfg.save()
        self.accept()
