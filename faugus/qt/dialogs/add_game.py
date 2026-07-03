"""Add/Edit game dialog for Faugus Launcher (Qt)."""

import logging
import os
import shutil
import subprocess
import threading
import uuid

logger = logging.getLogger(__name__)

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QIcon, QImage, QPixmap
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
    QMenu,
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

_faugus_banner = PathManager.system_data("faugus-launcher/faugus-banner.png")
_banners_dir = PathManager.user_config("faugus-launcher/banners")


class AddGameDialog(QDialog):
    """Dialog for adding or editing a game."""

    banner_ready = Signal()

    def __init__(self, parent, cfg: AppConfig, edit_game=None):
        super().__init__(parent)
        self.cfg = cfg
        self.edit_game = edit_game
        self.is_edit = edit_game is not None
        logger.debug("AddGameDialog.__init__: is_edit=%s, edit_game=%s", self.is_edit,
                     edit_game.title if edit_game else None)

        if not os.path.exists(_banners_dir):
            os.makedirs(_banners_dir)

        self.banner_path_temp = os.path.join(_banners_dir, "banner_temp.png")
        self._banner_lock = threading.Lock()
        logger.debug("Banner paths: _faugus_banner=%s, _banners_dir=%s, banner_path_temp=%s",
                     _faugus_banner, _banners_dir, self.banner_path_temp)
        logger.debug("_faugus_banner exists: %s", os.path.isfile(_faugus_banner))
        try:
            shutil.copyfile(_faugus_banner, self.banner_path_temp)
            logger.debug("Copied default banner to temp path, exists: %s, size: %s",
                         os.path.isfile(self.banner_path_temp),
                         os.path.getsize(self.banner_path_temp) if os.path.isfile(self.banner_path_temp) else 0)
        except Exception as e:
            logger.debug("Failed to copy default banner: %s", e)

        self.setWindowTitle("Edit Game" if self.is_edit else "Add Game")
        self.setMinimumSize(600, 560)
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
        ok_btn = buttons.button(QDialogButtonBox.Ok)
        ok_btn.setIcon(QIcon())
        ok_btn.setProperty("class", "primary-btn")
        ok_btn.style().unpolish(ok_btn)
        ok_btn.style().polish(ok_btn)
        cancel_btn = buttons.button(QDialogButtonBox.Cancel)
        cancel_btn.setIcon(QIcon())
        layout.addWidget(buttons)

        self.banner_ready.connect(self._load_banner)

        if self.is_edit:
            self._load_edit_values()

        self._load_banner()

    def _build_game_tab(self):
        logger.debug("AddGameDialog._build_game_tab")
        w = QWidget()
        hbox = QHBoxLayout(w)
        hbox.setSpacing(16)

        form = QFormLayout()
        form.setSpacing(10)

        self.txt_title = QLineEdit()
        self._title_timer = QTimer()
        self._title_timer.setSingleShot(True)
        self._title_timer.timeout.connect(self._on_title_changed)
        self.txt_title.textChanged.connect(lambda: self._title_timer.start(600))
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
        self.txt_banner.textChanged.connect(self._on_banner_path_changed)
        btn_banner = QPushButton("Browse...")
        btn_banner.setFixedWidth(80)
        btn_banner.clicked.connect(self._browse_banner)
        banner_row = QHBoxLayout()
        banner_row.addWidget(self.txt_banner, 1)
        banner_row.addWidget(btn_banner)
        form.addRow("Banner:", banner_row)

        hbox.addLayout(form, 1)

        # Banner preview
        self.banner_label = QLabel()
        self.banner_label.setFixedSize(172, 258)
        self.banner_label.setAlignment(Qt.AlignCenter)
        self.banner_label.setStyleSheet(
            "background: rgba(138, 92, 246, 0.06);"
            " border: 1px solid rgba(138, 92, 246, 0.12);"
            " border-radius: 8px;"
        )
        self.banner_label.setCursor(Qt.PointingHandCursor)
        self.banner_label.mousePressEvent = self._on_banner_clicked
        hbox.addWidget(self.banner_label)

        return w

    def _build_runner_tab(self):
        logger.debug("AddGameDialog._build_runner_tab")
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
        logger.debug("AddGameDialog._build_options_tab")
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
        logger.debug("AddGameDialog._browse_game")
        path, _ = QFileDialog.getOpenFileName(
            self, "Select game executable", "",
            "Windows executables (*.exe);;All files (*)"
        )
        if path:
            self.txt_path.setText(path)
            if not self.txt_title.text():
                self.txt_title.setText(os.path.splitext(os.path.basename(path))[0])

    def _browse_prefix(self):
        logger.debug("AddGameDialog._browse_prefix")
        path = QFileDialog.getExistingDirectory(self, "Select Wine prefix")
        if path:
            self.txt_prefix.setText(path)

    def _browse_banner(self):
        logger.debug("AddGameDialog._browse_banner")
        path, _ = QFileDialog.getOpenFileName(
            self, "Select banner image", "",
            "Images (*.png *.jpg *.jpeg);;All files (*)"
        )
        if path:
            self.txt_banner.setText(path)

    def _on_title_changed(self):
        title = self.txt_title.text().strip()
        logger.debug("AddGameDialog._on_title_changed: title=%s", title)
        if title:
            self._fetch_banner(title)

    def _on_banner_path_changed(self, path):
        logger.debug("_on_banner_path_changed: path=%s, exists=%s", path, os.path.isfile(path))
        if os.path.isfile(path):
            self._load_banner_preview(path)

    def _on_banner_clicked(self, event):
        logger.debug("AddGameDialog._on_banner_clicked")
        QLabel.mousePressEvent(self.banner_label, event)
        menu = QMenu(self)
        refresh_action = menu.addAction("Refresh")
        refresh_action.triggered.connect(self._on_banner_refresh)
        load_file_action = menu.addAction("Load from file")
        load_file_action.triggered.connect(self._on_load_banner_file)
        load_url_action = menu.addAction("Load from URL")
        load_url_action.triggered.connect(self._on_load_banner_url)
        menu.exec_(self.banner_label.mapToGlobal(event.pos()))

    def _on_banner_refresh(self):
        title = self.txt_title.text().strip()
        logger.debug("AddGameDialog._on_banner_refresh: title=%s", title)
        if title:
            self._fetch_banner(title)
        else:
            try:
                shutil.copyfile(_faugus_banner, self.banner_path_temp)
            except Exception:
                pass
            self._load_banner()

    def _on_load_banner_file(self):
        logger.debug("AddGameDialog._on_load_banner_file")
        path, _ = QFileDialog.getOpenFileName(
            self, "Select banner image", "",
            "Images (*.png *.jpg *.jpeg *.bmp *.gif);;All files (*)"
        )
        if path:
            self.txt_banner.setText(path)

    def _on_load_banner_url(self):
        logger.debug("AddGameDialog._on_load_banner_url")
        dlg = QDialog(self)
        dlg.setWindowTitle("Enter the image URL")
        dlg.setModal(True)
        dlg.setFixedSize(420, 120)
        lyt = QVBoxLayout(dlg)
        entry = QLineEdit()
        entry.setPlaceholderText("https://example.com/banner.png")
        lyt.addWidget(entry)
        btn_lyt = QHBoxLayout()
        btn_ok = QPushButton("OK")
        btn_cancel = QPushButton("Cancel")
        btn_lyt.addStretch()
        btn_lyt.addWidget(btn_ok)
        btn_lyt.addWidget(btn_cancel)
        lyt.addLayout(btn_lyt)
        btn_ok.clicked.connect(dlg.accept)
        btn_cancel.clicked.connect(dlg.reject)
        if dlg.exec() == QDialog.Accepted:
            url = entry.text().strip()
            if url:
                self._download_banner(url)
        dlg.deleteLater()

    def _set_banner_loading(self, loading=True):
        logger.debug("AddGameDialog._set_banner_loading: loading=%s", loading)
        if loading:
            self.banner_label.setText("Searching...")
            self.banner_label.setPixmap(QPixmap())
        else:
            self._load_banner()

    def _load_banner(self):
        logger.debug("_load_banner: path=%s, exists=%s",
                     self.banner_path_temp, os.path.isfile(self.banner_path_temp))
        if not os.path.isfile(self.banner_path_temp):
            self.banner_label.setText("No banner")
            return
        img = QImage(self.banner_path_temp)
        logger.debug("QImage null=%s, size=%dx%d", img.isNull(), img.width(), img.height())
        if img.isNull():
            self.banner_label.setText("No banner")
            return
        pixmap = QPixmap.fromImage(img)
        pixmap = pixmap.scaled(172, 258, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.banner_label.setPixmap(pixmap)
        logger.debug("Banner set on label successfully")

    def _load_banner_preview(self, path):
        logger.debug("_load_banner_preview: path=%s, exists=%s", path, os.path.isfile(path))
        if not os.path.isfile(path):
            return
        shutil.copyfile(path, self.banner_path_temp)
        logger.debug("Copied to temp, temp exists=%s", os.path.isfile(self.banner_path_temp))
        self._load_banner()

    def _fetch_banner(self, game_name):
        logger.debug("_fetch_banner: game_name=%s", game_name)
        self._set_banner_loading(True)

        def fetch():
            api_url = f"https://steamgrid.usebottles.com/api/search/{game_name}"
            logger.debug("Fetching banner from API: %s", api_url)
            try:
                import requests
                response = requests.get(api_url, timeout=10)
                response.raise_for_status()
                image_url = response.text.strip('"')
                logger.debug("API response image_url=%s", image_url)
                if not image_url:
                    QTimer.singleShot(0, lambda: self._set_banner_loading(False))
                    return
                img_data = requests.get(image_url, timeout=10).content
                logger.debug("Downloaded image: %d bytes", len(img_data))
                with self._banner_lock:
                    with open(self.banner_path_temp, "wb") as f:
                        f.write(img_data)
                logger.debug("Written to %s, exists=%s, size=%s",
                             self.banner_path_temp,
                             os.path.isfile(self.banner_path_temp),
                             os.path.getsize(self.banner_path_temp) if os.path.isfile(self.banner_path_temp) else 0)
                self.banner_ready.emit()
            except Exception as e:
                logger.debug("Error fetching banner: %s", e)
                self.banner_ready.emit()

        threading.Thread(target=fetch, daemon=True).start()

    def _download_banner(self, url):
        logger.debug("AddGameDialog._download_banner: url=%s", url)
        self._set_banner_loading(True)

        def download():
            try:
                import requests
                req = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
                req.raise_for_status()
                with self._banner_lock:
                    with open(self.banner_path_temp, "wb") as f:
                        f.write(req.content)
                self.banner_ready.emit()
            except Exception as e:
                print(f"Error downloading banner: {e}")
                self.banner_ready.emit()

        threading.Thread(target=download, daemon=True).start()

    def _load_edit_values(self):
        logger.debug("AddGameDialog._load_edit_values: title=%s, path=%s", self.edit_game.title, self.edit_game.path)
        g = self.edit_game
        self.txt_title.setText(g.title)
        self.txt_path.setText(g.path)
        self.txt_prefix.setText(g.prefix)
        banner_path = g.banner or ""
        logger.debug("_load_edit_values: banner_path=%s, exists=%s", banner_path, os.path.isfile(banner_path))
        self.txt_banner.setText(banner_path)
        if banner_path and os.path.isfile(banner_path):
            shutil.copyfile(banner_path, self.banner_path_temp)
            logger.debug("Copied game banner to temp")
        elif os.path.isfile(_faugus_banner):
            shutil.copyfile(_faugus_banner, self.banner_path_temp)
            logger.debug("Copied default banner to temp (edit fallback)")

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
        logger.debug("AddGameDialog._on_ok: title=%s, is_edit=%s", title, self.is_edit)
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

        title_formatted = title.replace(" ", "_").lower()
        banner_final = ""
        if os.path.isfile(self.banner_path_temp):
            banner_final = os.path.join(_banners_dir, f"{title_formatted}.png")
            command_magick = shutil.which("magick") or shutil.which("convert")
            if command_magick:
                try:
                    subprocess.run(
                        [command_magick, self.banner_path_temp, "-resize", "230x345", banner_final],
                        check=True,
                    )
                except Exception:
                    shutil.copyfile(self.banner_path_temp, banner_final)
            else:
                shutil.copyfile(self.banner_path_temp, banner_final)

        if self.is_edit:
            game = self.edit_game
            game.title = title
            game.path = path
            game.prefix = self.txt_prefix.text().strip()
            game.banner = banner_final
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
                banner=banner_final,
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


class AddGameView(QWidget):
    """Embeddable add/edit game widget for sidebar view."""

    game_saved = Signal()
    back_requested = Signal()
    banner_ready = Signal()

    def __init__(self, cfg: AppConfig, parent=None):
        super().__init__(parent)
        self.cfg = cfg
        self.edit_game = None
        self.is_edit = False
        logger.debug("AddGameView.__init__")

        if not os.path.exists(_banners_dir):
            os.makedirs(_banners_dir)

        self.banner_path_temp = os.path.join(_banners_dir, "banner_temp.png")
        self._banner_lock = threading.Lock()
        try:
            shutil.copyfile(_faugus_banner, self.banner_path_temp)
        except Exception:
            pass

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_game_tab(), "Game")
        self.tabs.addTab(self._build_runner_tab(), "Runner")
        self.tabs.addTab(self._build_options_tab(), "Options")
        layout.addWidget(self.tabs, 1)

        # Bottom bar with Save/Back
        bar = QWidget()
        bar_layout = QHBoxLayout(bar)
        bar_layout.setContentsMargins(16, 8, 16, 8)

        btn_back = QPushButton("Back")
        btn_back.setFixedWidth(100)
        btn_back.clicked.connect(self.back_requested.emit)

        btn_save = QPushButton("Save")
        btn_save.setProperty("class", "primary-btn")
        btn_save.setFixedWidth(100)
        btn_save.clicked.connect(self._on_save)

        bar_layout.addWidget(btn_back)
        bar_layout.addStretch()
        bar_layout.addWidget(btn_save)
        layout.addWidget(bar)

        self.banner_ready.connect(self._load_banner)

    def _build_game_tab(self):
        w = QWidget()
        hbox = QHBoxLayout(w)
        hbox.setSpacing(16)

        form = QFormLayout()
        form.setSpacing(10)

        self.txt_title = QLineEdit()
        self._title_timer = QTimer()
        self._title_timer.setSingleShot(True)
        self._title_timer.timeout.connect(self._on_title_changed)
        self.txt_title.textChanged.connect(lambda: self._title_timer.start(600))
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
        self.txt_banner.textChanged.connect(self._on_banner_path_changed)
        btn_banner = QPushButton("Browse...")
        btn_banner.setFixedWidth(80)
        btn_banner.clicked.connect(self._browse_banner)
        banner_row = QHBoxLayout()
        banner_row.addWidget(self.txt_banner, 1)
        banner_row.addWidget(btn_banner)
        form.addRow("Banner:", banner_row)

        hbox.addLayout(form, 1)

        self.banner_label = QLabel()
        self.banner_label.setFixedSize(172, 258)
        self.banner_label.setAlignment(Qt.AlignCenter)
        self.banner_label.setStyleSheet(
            "background: rgba(138, 92, 246, 0.06);"
            " border: 1px solid rgba(138, 92, 246, 0.12);"
            " border-radius: 8px;"
        )
        self.banner_label.setCursor(Qt.PointingHandCursor)
        self.banner_label.mousePressEvent = self._on_banner_clicked
        hbox.addWidget(self.banner_label)

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

    def load_game(self, game):
        """Load a game for editing."""
        self.edit_game = game
        self.is_edit = game is not None
        logger.debug("AddGameView.load_game: title=%s", game.title if game else None)

        if not game:
            return

        self.txt_title.setText(game.title)
        self.txt_path.setText(game.path)
        self.txt_prefix.setText(game.prefix)
        banner_path = game.banner or ""
        self.txt_banner.setText(banner_path)
        if banner_path and os.path.isfile(banner_path):
            shutil.copyfile(banner_path, self.banner_path_temp)
        elif os.path.isfile(_faugus_banner):
            shutil.copyfile(_faugus_banner, self.banner_path_temp)

        runner = game.runner
        if runner == "Proton-CachyOS Latest":
            runner = "Proton-CachyOS Latest (default)"
        idx = self.cmb_runner.findText(runner)
        if idx >= 0:
            self.cmb_runner.setCurrentIndex(idx)

        self.txt_launch_args.setText(game.launch_arguments)
        self.txt_game_args.setText(game.game_arguments)
        self.txt_protonfix.setText(game.protonfix)
        self.chk_mangohud.setChecked(bool(game.mangohud))
        self.chk_gamemode.setChecked(bool(game.gamemode))
        self.chk_disable_hidraw.setChecked(bool(game.disable_hidraw))
        self.chk_prevent_sleep.setChecked(bool(game.prevent_sleep))

        self._load_banner()

    def _on_save(self):
        logger.debug("AddGameView._on_save")
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

        title_formatted = title.replace(" ", "_").lower()
        banner_final = ""
        if os.path.isfile(self.banner_path_temp):
            banner_final = os.path.join(_banners_dir, f"{title_formatted}.png")
            command_magick = shutil.which("magick") or shutil.which("convert")
            if command_magick:
                try:
                    subprocess.run(
                        [command_magick, self.banner_path_temp, "-resize", "230x345", banner_final],
                        check=True,
                    )
                except Exception:
                    shutil.copyfile(self.banner_path_temp, banner_final)
            else:
                shutil.copyfile(self.banner_path_temp, banner_final)

        repo = GameRepository(PathManager.user_config("faugus-launcher/games.json"))

        if self.is_edit:
            game = self.edit_game
            game.title = title
            game.path = path
            game.prefix = self.txt_prefix.text().strip()
            game.banner = banner_final
            game.runner = runner
            game.launch_arguments = self.txt_launch_args.text().strip()
            game.game_arguments = self.txt_game_args.text().strip()
            game.protonfix = self.txt_protonfix.text().strip()
            game.mangohud = self.chk_mangohud.isChecked()
            game.gamemode = self.chk_gamemode.isChecked()
            game.disable_hidraw = self.chk_disable_hidraw.isChecked()
            game.prevent_sleep = self.chk_prevent_sleep.isChecked()
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
                banner=banner_final,
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
            repo.add_game(game)

        logger.debug("AddGameView._on_save: is_edit=%s, title=%s, banner=%s", self.is_edit, title, banner_final)
        self.game_saved.emit()

    def _browse_game(self):
        logger.debug("AddGameView._browse_game")
        path, _ = QFileDialog.getOpenFileName(
            self, "Select game executable", "",
            "Windows executables (*.exe);;All files (*)"
        )
        if path:
            logger.debug("  selected: %s", path)
            self.txt_path.setText(path)
            if not self.txt_title.text():
                title = os.path.splitext(os.path.basename(path))[0]
                logger.debug("  auto-title: %s", title)
                self.txt_title.setText(title)

    def _browse_prefix(self):
        logger.debug("AddGameView._browse_prefix")
        path = QFileDialog.getExistingDirectory(self, "Select Wine prefix")
        if path:
            logger.debug("  selected: %s", path)
            self.txt_prefix.setText(path)

    def _browse_banner(self):
        logger.debug("AddGameView._browse_banner")
        path, _ = QFileDialog.getOpenFileName(
            self, "Select banner image", "",
            "Images (*.png *.jpg *.jpeg);;All files (*)"
        )
        if path:
            logger.debug("  selected: %s", path)
            self.txt_banner.setText(path)

    def _on_title_changed(self):
        title = self.txt_title.text().strip()
        logger.debug("AddGameView._on_title_changed: title=%s", title)
        if title:
            self._fetch_banner(title)

    def _on_banner_path_changed(self, path):
        logger.debug("AddGameView._on_banner_path_changed: path=%s, exists=%s", path, os.path.isfile(path))
        if os.path.isfile(path):
            self._load_banner_preview(path)

    def _on_banner_clicked(self, event):
        logger.debug("AddGameView._on_banner_clicked")
        QLabel.mousePressEvent(self.banner_label, event)
        menu = QMenu(self)
        refresh_action = menu.addAction("Refresh")
        refresh_action.triggered.connect(self._on_banner_refresh)
        load_file_action = menu.addAction("Load from file")
        load_file_action.triggered.connect(self._on_load_banner_file)
        load_url_action = menu.addAction("Load from URL")
        load_url_action.triggered.connect(self._on_load_banner_url)
        menu.exec_(self.banner_label.mapToGlobal(event.pos()))

    def _on_banner_refresh(self):
        logger.debug("AddGameView._on_banner_refresh")
        title = self.txt_title.text().strip()
        if title:
            self._fetch_banner(title)
        else:
            try:
                shutil.copyfile(_faugus_banner, self.banner_path_temp)
            except Exception:
                pass
            self._load_banner()

    def _on_load_banner_file(self):
        logger.debug("AddGameView._on_load_banner_file")
        path, _ = QFileDialog.getOpenFileName(
            self, "Select banner image", "",
            "Images (*.png *.jpg *.jpeg *.bmp *.gif);;All files (*)"
        )
        if path:
            logger.debug("  selected: %s", path)
            self.txt_banner.setText(path)

    def _on_load_banner_url(self):
        logger.debug("AddGameView._on_load_banner_url")
        dlg = QDialog(self)
        dlg.setWindowTitle("Enter the image URL")
        dlg.setModal(True)
        dlg.setFixedSize(420, 120)
        lyt = QVBoxLayout(dlg)
        entry = QLineEdit()
        entry.setPlaceholderText("https://example.com/banner.png")
        lyt.addWidget(entry)
        btn_lyt = QHBoxLayout()
        btn_ok = QPushButton("OK")
        btn_cancel = QPushButton("Cancel")
        btn_lyt.addStretch()
        btn_lyt.addWidget(btn_ok)
        btn_lyt.addWidget(btn_cancel)
        lyt.addLayout(btn_lyt)
        btn_ok.clicked.connect(dlg.accept)
        btn_cancel.clicked.connect(dlg.reject)
        if dlg.exec() == QDialog.Accepted:
            url = entry.text().strip()
            logger.debug("  URL: %s", url)
            if url:
                self._download_banner(url)
        dlg.deleteLater()

    def _load_banner_preview(self, path):
        logger.debug("AddGameView._load_banner_preview: path=%s, exists=%s", path, os.path.isfile(path))
        if not os.path.isfile(path):
            return
        shutil.copyfile(path, self.banner_path_temp)
        self._load_banner()

    def _load_banner(self):
        logger.debug("AddGameView._load_banner: path=%s, exists=%s",
                     self.banner_path_temp, os.path.isfile(self.banner_path_temp))
        if not os.path.isfile(self.banner_path_temp):
            self.banner_label.setText("No banner")
            return
        img = QImage(self.banner_path_temp)
        logger.debug("  QImage null=%s, size=%dx%d", img.isNull(), img.width(), img.height())
        if img.isNull():
            self.banner_label.setText("No banner")
            return
        pixmap = QPixmap.fromImage(img)
        pixmap = pixmap.scaled(172, 258, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.banner_label.setPixmap(pixmap)

    def _set_banner_loading(self, loading=True):
        logger.debug("AddGameView._set_banner_loading: loading=%s", loading)
        if loading:
            self.banner_label.setText("Searching...")
            self.banner_label.setPixmap(QPixmap())
        else:
            self._load_banner()

    def _fetch_banner(self, game_name):
        logger.debug("AddGameView._fetch_banner: game_name=%s", game_name)
        self._set_banner_loading(True)

        def fetch():
            api_url = f"https://steamgrid.usebottles.com/api/search/{game_name}"
            logger.debug("  API: %s", api_url)
            try:
                import requests
                response = requests.get(api_url, timeout=10)
                response.raise_for_status()
                image_url = response.text.strip('"')
                logger.debug("  image_url=%s", image_url)
                if not image_url:
                    self.banner_ready.emit()
                    return
                img_data = requests.get(image_url, timeout=10).content
                with self._banner_lock:
                    with open(self.banner_path_temp, "wb") as f:
                        f.write(img_data)
                self.banner_ready.emit()
            except Exception as e:
                logger.debug("  Error: %s", e)
                self.banner_ready.emit()

        threading.Thread(target=fetch, daemon=True).start()

    def _download_banner(self, url):
        logger.debug("AddGameView._download_banner: url=%s", url)
        self._set_banner_loading(True)

        def download():
            try:
                import requests
                req = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
                req.raise_for_status()
                with self._banner_lock:
                    with open(self.banner_path_temp, "wb") as f:
                        f.write(req.content)
                self.banner_ready.emit()
            except Exception as e:
                logger.debug("  Error: %s", e)
                self.banner_ready.emit()

        threading.Thread(target=download, daemon=True).start()
