"""Add/Edit game dialog for Faugus Launcher (Qt)."""

import os
import uuid

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
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
from faugus.core.models import Game
from faugus.core.utils import build_runner_list
from faugus.path_manager import PathManager


class AddGameDialog(QDialog):
    """Dialog for adding or editing a game."""

    def __init__(self, parent, cfg: AppConfig, edit_game=None):
        super().__init__(parent)
        self.cfg = cfg
        self.edit_game = edit_game
        self.is_edit = edit_game is not None

        self.setWindowTitle("Edit Game" if self.is_edit else "Add Game")
        self.setMinimumSize(550, 500)
        self.setModal(True)

        layout = QVBoxLayout(self)

        tabs = QTabWidget()
        tabs.addTab(self._build_game_tab(), "Game")
        tabs.addTab(self._build_runner_tab(), "Runner")
        tabs.addTab(self._build_options_tab(), "Options")
        layout.addWidget(tabs, 1)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_ok)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        if self.is_edit:
            self._load_edit_values()

    def _build_game_tab(self):
        w = QWidget()
        form = QFormLayout(w)
        form.setSpacing(10)

        self.txt_title = QLineEdit()
        form.addRow("Title:", self.txt_title)

        self.txt_path = QLineEdit()
        btn_browse = QPushButton("Browse...")
        btn_browse.setFixedWidth(80)
        btn_browse.clicked.connect(self._browse_game)
        path_row = QHBoxLayout()
        path_row.addWidget(self.txt_path, 1)
        path_row.addWidget(btn_browse)
        form.addRow("Game path:", path_row)

        self.txt_prefix = QLineEdit()
        btn_browse_prefix = QPushButton("Browse...")
        btn_browse_prefix.setFixedWidth(80)
        btn_browse_prefix.clicked.connect(self._browse_prefix)
        prefix_row = QHBoxLayout()
        prefix_row.addWidget(self.txt_prefix, 1)
        prefix_row.addWidget(btn_browse_prefix)
        form.addRow("Wine prefix:", prefix_row)

        self.txt_banner = QLineEdit()
        btn_banner = QPushButton("Browse...")
        btn_banner.setFixedWidth(80)
        btn_banner.clicked.connect(self._browse_banner)
        banner_row = QHBoxLayout()
        banner_row.addWidget(self.txt_banner, 1)
        banner_row.addWidget(btn_banner)
        form.addRow("Banner:", banner_row)

        return w

    def _build_runner_tab(self):
        w = QWidget()
        form = QFormLayout(w)
        form.setSpacing(10)

        self.cmb_runner = QComboBox()
        proton_cachyos = PathManager.system_data("steam/compatibilitytools.d/proton-cachyos-slr/")
        compat_dir = os.path.expanduser("~/.local/share/Steam/compatibilitytools.d")
        for r in build_runner_list(proton_cachyos, compat_dir):
            self.cmb_runner.addItem(r)
        form.addRow("Runner:", self.cmb_runner)

        self.txt_launch_args = QLineEdit()
        form.addRow("Launch arguments:", self.txt_launch_args)

        self.txt_game_args = QLineEdit()
        form.addRow("Game arguments:", self.txt_game_args)

        self.txt_protonfix = QLineEdit()
        self.txt_protonfix.setPlaceholderText("e.g. 12345")
        form.addRow("ProtonFix Game ID:", self.txt_protonfix)

        return w

    def _build_options_tab(self):
        w = QWidget()
        form = QFormLayout(w)
        form.setSpacing(10)

        self.chk_mangohud = QCheckBox("MangoHud")
        form.addRow(self.chk_mangohud)

        self.chk_gamemode = QCheckBox("GameMode")
        form.addRow(self.chk_gamemode)

        self.chk_disable_hidraw = QCheckBox("Disable HIDRAW")
        form.addRow(self.chk_disable_hidraw)

        self.chk_prevent_sleep = QCheckBox("Prevent sleep")
        form.addRow(self.chk_prevent_sleep)

        return w

    def _browse_game(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select game executable", "",
            "Windows executables (*.exe);;All files (*)"
        )
        if path:
            self.txt_path.setText(path)
            if not self.txt_title.text():
                self.txt_title.setText(os.path.splitext(os.path.basename(path))[0])

    def _browse_prefix(self):
        path = QFileDialog.getExistingDirectory(self, "Select Wine prefix")
        if path:
            self.txt_prefix.setText(path)

    def _browse_banner(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select banner image", "",
            "Images (*.png *.jpg *.jpeg);;All files (*)"
        )
        if path:
            self.txt_banner.setText(path)

    def _load_edit_values(self):
        g = self.edit_game
        self.txt_title.setText(g.title)
        self.txt_path.setText(g.path)
        self.txt_prefix.setText(g.prefix)
        self.txt_banner.setText(g.banner)

        runner = g.runner
        if runner == "Proton-CachyOS Latest":
            runner = "Proton-CachyOS Latest (default)"
        idx = self.cmb_runner.findText(runner)
        if idx >= 0:
            self.cmb_runner.setCurrentIndex(idx)

        self.txt_launch_args.setText(g.launch_arguments)
        self.txt_game_args.setText(g.game_arguments)
        self.txt_protonfix.setText(g.protonfix)
        self.chk_mangohud.setChecked(bool(g.mangohud))
        self.chk_gamemode.setChecked(bool(g.gamemode))
        self.chk_disable_hidraw.setChecked(bool(g.disable_hidraw))
        self.chk_prevent_sleep.setChecked(bool(g.prevent_sleep))

    def _on_ok(self):
        title = self.txt_title.text().strip()
        if not title:
            QMessageBox.warning(self, "Error", "Title is required.")
            return

        path = self.txt_path.text().strip()
        if not path:
            QMessageBox.warning(self, "Error", "Game path is required.")
            return

        runner = self.cmb_runner.currentText()
        if runner == "Proton-CachyOS Latest (default)":
            runner = "Proton-CachyOS Latest"

        if self.is_edit:
            game = self.edit_game
            game.title = title
            game.path = path
            game.prefix = self.txt_prefix.text().strip()
            game.banner = self.txt_banner.text().strip()
            game.runner = runner
            game.launch_arguments = self.txt_launch_args.text().strip()
            game.game_arguments = self.txt_game_args.text().strip()
            game.protonfix = self.txt_protonfix.text().strip()
            game.mangohud = self.chk_mangohud.isChecked()
            game.gamemode = self.chk_gamemode.isChecked()
            game.disable_hidraw = self.chk_disable_hidraw.isChecked()
            game.prevent_sleep = self.chk_prevent_sleep.isChecked()

            from faugus.core.repository import GameRepository
            repo = GameRepository(PathManager.user_config("faugus-launcher/games.json"))
            repo.update_game(game)
        else:
            game = Game(
                gameid=str(uuid.uuid4()),
                title=title,
                path=path,
                prefix=self.txt_prefix.text().strip(),
                launch_arguments=self.txt_launch_args.text().strip(),
                game_arguments=self.txt_game_args.text().strip(),
                mangohud=self.chk_mangohud.isChecked(),
                gamemode=self.chk_gamemode.isChecked(),
                disable_hidraw=self.chk_disable_hidraw.isChecked(),
                protonfix=self.txt_protonfix.text().strip(),
                runner=runner,
                addapp_checkbox=False,
                addapp="",
                addapp_bat="",
                addapp_delay="",
                addapp_first=False,
                banner=self.txt_banner.text().strip(),
                lossless_enabled=False,
                lossless_multiplier=1,
                lossless_flow=100,
                lossless_performance=False,
                lossless_hdr=False,
                lossless_present=False,
                playtime=0,
                hidden=False,
                prevent_sleep=self.chk_prevent_sleep.isChecked(),
                category=[],
                icon="",
                favorite=False,
            )

            from faugus.core.repository import GameRepository
            repo = GameRepository(PathManager.user_config("faugus-launcher/games.json"))
            repo.add_game(game)

        self.accept()
