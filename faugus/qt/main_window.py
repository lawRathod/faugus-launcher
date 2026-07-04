"""Qt main window assembling sidebar, game grid, toolbar, and controls."""

import json
import logging
import os
import shutil
import subprocess
import sys
from functools import partial

logger = logging.getLogger(__name__)

from PySide6.QtCore import Qt, QTimer, QUrl, QSize
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from faugus.core.config import AppConfig
from faugus.core.models import Game
from faugus.core.repository import GameRepository, RecentsRepository
from faugus.core.utils import (
    VIEW_LIBRARY,
    VIEW_FAVORITES,
    VIEW_RECENTS,
    normalize_view,
    view_filter_matches,
    format_recent_age,
    version_key,
    build_runner_list,
)
from faugus.path_manager import PathManager
from faugus.qt.flow_layout import FlowLayout
from faugus.qt.game_card import GameCard
from faugus.qt.sidebar import Sidebar
from faugus.qt.style import get_stylesheet

VERSION = "2.0.0"

# Paths
_games_json = PathManager.user_config("faugus-launcher/games.json")
_recents_json = PathManager.user_config("faugus-launcher/recents.json")
_latest_games = PathManager.user_config("faugus-launcher/latest-games.txt")
_custom_order = PathManager.user_config("faugus-launcher/custom-order.json")
_running_games = PathManager.user_data("faugus-launcher/running_games.json")
_logs_dir = PathManager.user_config("faugus-launcher/logs")
_faugus_banner = PathManager.system_data("faugus-launcher/faugus-banner.png")
_compatibility_dir = os.path.expanduser("~/.local/share/Steam/compatibilitytools.d")
_proton_cachyos = PathManager.system_data("steam/compatibilitytools.d/proton-cachyos-slr/")
_icons_dir = PathManager.user_config("faugus-launcher/icons")

os.makedirs(os.path.dirname(_games_json), exist_ok=True)


class MainWindow(QMainWindow):
    """The main application window."""

    def __init__(self, cfg: AppConfig, start_hidden=False):
        logger.debug("MainWindow.__init__: start_hidden=%s, interface_mode=%s", start_hidden, cfg.interface_mode)
        super().__init__()
        self.cfg = cfg
        self.setWindowTitle(f"Faugus Launcher {VERSION}")
        self.setMinimumSize(800, 500)

        # State
        self.games = []
        self.game_cards = []
        self.running = {}
        self.processes = {}
        self.current_view = normalize_view(cfg.current_view)
        self.interface_mode = cfg.interface_mode
        self.banner_size = cfg.banner_size
        self.current_sort_id = cfg.sort
        raw = cfg.category
        self.current_category = "" if raw in ("all", "", None) else raw
        self.show_categories = cfg.show_categories
        self.show_labels = cfg.show_labels
        self.playtime_data = {}
        self.latest_games_order = {}
        self.recent_games = {}
        self.custom_order_data = {}
        self.show_sidebar = cfg.show_sidebar

        # Ensure running_games file exists
        if not os.path.exists(_running_games):
            from faugus.core.utils import save_json_file
            save_json_file({}, _running_games)
        from faugus.core.utils import load_json_file
        self.running = load_json_file(_running_games, {})
        if not isinstance(self.running, dict):
            self.running = {}

        # Repositories
        self.game_repo = GameRepository(_games_json)
        self.recents_repo = RecentsRepository(_recents_json)

        # Apply stylesheet
        self.setStyleSheet(get_stylesheet())

        # Build UI
        self._build_ui()

        # Load data
        self._load_sort_data()
        self._load_games()

        # Timer for checking running processes
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._check_running)
        self._timer.start(1000)

        # Window size
        if cfg.window_behavior == "Remember":
            self.resize(cfg.width, cfg.height)
        else:
            self.resize(1280, 720)

        if start_hidden:
            self.showMinimized()
        else:
            self.show()

    def _build_ui(self):
        """Build the complete UI layout."""
        logger.debug("MainWindow._build_ui: interface_mode=%s, show_sidebar=%s", self.interface_mode, self.show_sidebar)
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        is_big = self.interface_mode in ("Blocks", "Banners")

        # Sidebar
        self.sidebar = Sidebar(is_big=is_big, show_sidebar=self.show_sidebar)
        self.sidebar.view_changed.connect(self._on_view_changed)
        self.sidebar.clear_recents_clicked.connect(self._on_clear_recents)
        main_layout.addWidget(self.sidebar)

        # Right side
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        # Top toolbar
        toolbar = self._build_toolbar(is_big)
        right_layout.addWidget(toolbar)

        # Divider
        right_layout.addSpacing(6)
        divider = QFrame()
        divider.setFixedHeight(1)
        divider.setStyleSheet("background: rgba(138, 92, 246, 0.08);")
        right_layout.addWidget(divider)

        # Content area (game grid or empty state)
        self.stack = QStackedWidget()

        # Scroll area with game grid
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setFrameShape(QScrollArea.NoFrame)

        self.flow_container = QWidget()
        self.flow_layout = FlowLayout(self.flow_container, margin=16, h_spacing=16, v_spacing=16)
        scroll.setWidget(self.flow_container)
        self.stack.addWidget(scroll)

        # Empty state
        self.empty_widget = self._build_empty_state()
        self.stack.addWidget(self.empty_widget)

        # Settings view
        from faugus.qt.dialogs.settings import SettingsView
        self.settings_view = SettingsView(self.cfg)
        self.settings_view.settings_changed.connect(self._on_settings_changed)
        self.stack.addWidget(self.settings_view)

        # Add game view
        from faugus.qt.dialogs.add_game import AddGameView
        self.add_game_view = AddGameView(self.cfg)
        self.add_game_view.game_saved.connect(self._on_game_saved)
        self.add_game_view.back_requested.connect(lambda: self.sidebar.set_view("library"))
        self.stack.addWidget(self.add_game_view)

        right_layout.addWidget(self.stack, 1)

        # Bottom bar
        bottom_bar = self._build_bottom_bar(is_big)
        right_layout.addWidget(bottom_bar)

        main_layout.addWidget(right, 1)

        # Set initial view
        self.sidebar.set_view(self.current_view)

    def _build_toolbar(self, is_big):
        """Build the top toolbar with buttons and search."""
        logger.debug("MainWindow._build_toolbar: is_big=%s", is_big)
        from faugus.qt.icons import get_icon

        toolbar = QWidget()
        toolbar.setFixedHeight(80)
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(12, 20, 12, 20)
        layout.setSpacing(6)

        def make_button(icon_name, callback, tooltip=None, size=34):
            btn = QPushButton()
            btn.setFixedSize(size, size)
            btn.setIcon(get_icon(icon_name, size - 8))
            btn.setIconSize(QSize(size - 10, size - 10))
            btn.setProperty("class", "flash-btn")
            if tooltip:
                btn.setToolTip(tooltip)
            btn.clicked.connect(callback)
            return btn

        self.btn_sidebar = make_button("menu", self._toggle_sidebar, "Toggle sidebar")
        self.btn_kill = make_button("kill", self._on_kill_all, "Force close all running games")
        self.btn_play = make_button("play", self._on_play, "Play selected game")

        layout.addWidget(self.btn_sidebar)
        layout.addSpacing(2)
        layout.addWidget(self.btn_kill)
        layout.addSpacing(4)
        layout.addWidget(self.btn_play)

        layout.addStretch()

        # Search
        self.search_entry = QLineEdit()
        self.search_entry.setPlaceholderText("Search games...")
        self.search_entry.setFixedWidth(220)
        self.search_entry.setFixedHeight(48)
        self.search_entry.textChanged.connect(self._on_search_changed)
        layout.addWidget(self.search_entry)

        # Sort
        self.sort_map = {
            "alpha": "A-Z",
            "playtime": "Playtime",
            "lastplayed": "Recent",
            "custom": "Custom",
        }
        self.btn_sort = QPushButton(self.sort_map.get(self.current_sort_id, "A-Z"))
        self.btn_sort.setIcon(get_icon("sort", 14))
        self.btn_sort.setIconSize(QSize(14, 14))
        self.btn_sort.setProperty("class", "bottom-bar-button")
        self.btn_sort.setFixedHeight(48)
        self.btn_sort.clicked.connect(self._show_sort_menu)
        layout.addWidget(self.btn_sort)



        return toolbar

    def _build_bottom_bar(self, is_big):
        """Bottom bar placeholder (can be extended)."""
        logger.debug("MainWindow._build_bottom_bar")
        bar = QWidget()
        bar.setFixedHeight(1)
        return bar

    def _build_empty_state(self):
        """Build the empty state placeholder widget."""
        logger.debug("MainWindow._build_empty_state")
        widget = QWidget()
        widget.setProperty("class", "empty-state")
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(12)
        layout.setContentsMargins(0, 40, 0, 40)

        icon_label = QLabel("\U0001f3ae")
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("font-size: 64px; background: transparent;")
        layout.addWidget(icon_label)

        self.empty_title = QLabel("Your library is empty")
        self.empty_title.setAlignment(Qt.AlignCenter)
        self.empty_title.setStyleSheet(
            "font-size: 24px; font-weight: 600; color: rgba(232, 224, 240, 0.8);"
            " background: transparent;"
        )
        layout.addWidget(self.empty_title)

        self.empty_subtitle = QLabel("Click + to add your first game")
        self.empty_subtitle.setAlignment(Qt.AlignCenter)
        self.empty_subtitle.setStyleSheet(
            "font-size: 15px; color: rgba(200, 184, 224, 0.4);"
            " background: transparent;"
        )
        layout.addWidget(self.empty_subtitle)

        return widget

    # ------------------------------------------------------------------ #
    # Data loading                                                         #
    # ------------------------------------------------------------------ #

    def _load_sort_data(self):
        """Load playtime, latest-games, and custom order data."""
        logger.debug("MainWindow._load_sort_data")
        self.playtime_data.clear()
        self.latest_games_order.clear()
        self.custom_order_data.clear()

        games = self.game_repo.load_all()
        for g in games:
            self.playtime_data[g.gameid] = g.playtime or 0

        if os.path.exists(_latest_games):
            try:
                with open(_latest_games) as f:
                    for idx, gid in enumerate(l.strip() for l in f):
                        self.latest_games_order[gid] = idx
            except Exception:
                pass

        if os.path.exists(_custom_order):
            try:
                with open(_custom_order) as f:
                    self.custom_order_data.update(json.load(f))
            except Exception:
                pass

        self.recent_games = self.recents_repo.load()

    def _load_games(self):
        """Load games from JSON and populate the grid."""
        self.games = self.game_repo.load_all()
        logger.debug("MainWindow._load_games: count=%s", len(self.games))
        self._rebuild_grid()

    def _rebuild_grid(self):
        """Clear and rebuild the game card grid."""
        logger.debug("MainWindow._rebuild_grid: view=%s, sort=%s", self.current_view, self.current_sort_id)
        # Clear existing cards
        while self.flow_layout.count():
            item = self.flow_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.game_cards.clear()

        # Filter and sort
        filtered = self._get_filtered_sorted_games()

        # Create cards
        for game in filtered:
            card = GameCard(
                game,
                mode=self.interface_mode,
                zoom_pct=self.banner_size,
            )
            card.context_action.connect(self._on_context_action)
            card.doubleClicked.connect(self._on_card_double_clicked)

            # Set age label for recents view
            if self.current_view == VIEW_RECENTS:
                ts = self.recent_games.get(game.gameid)
                age_text = format_recent_age(ts)
                if age_text:
                    card.set_age_label(age_text)

            # Set playing state
            if game.gameid in self.running:
                card.set_playing(True)

            self.flow_layout.addWidget(card)
            self.game_cards.append(card)

        # Update empty state
        self._update_empty_state()

    def _get_filtered_sorted_games(self):
        """Return games filtered by view/search/category and sorted."""
        search = self.search_entry.text().lower() if hasattr(self, 'search_entry') else ""
        logger.debug("MainWindow._get_filtered_sorted_games: search=%s, category=%s", search, self.current_category)

        filtered = []
        for game in self.games:
            # Search filter
            if search and search not in game.title.lower():
                continue

            # Category filter
            if self.show_categories and self.current_category:
                raw_cat = game.category
                if isinstance(raw_cat, str):
                    game_cats = [raw_cat]
                elif isinstance(raw_cat, list):
                    game_cats = raw_cat
                else:
                    game_cats = []

                if self.current_category == "Uncategorized":
                    if game_cats and game_cats != ["None"]:
                        continue
                else:
                    if not game_cats:
                        game_cats = ["None"]
                    if self.current_category not in game_cats:
                        continue

            # View filter
            recent_ids = set(self.recent_games.keys())
            if not view_filter_matches(
                {"gameid": game.gameid, "title": game.title, "favorite": getattr(game, 'favorite', False)},
                self.current_view,
                recent_ids,
            ):
                continue

            filtered.append(game)

        # Sort
        def sort_key(g):
            if self.current_sort_id == "playtime":
                return -self.playtime_data.get(g.gameid, 0)
            elif self.current_sort_id == "lastplayed":
                ts = self.recent_games.get(g.gameid)
                if ts is not None:
                    return -ts
                idx = self.latest_games_order.get(g.gameid, float('inf'))
                return idx
            elif self.current_sort_id == "custom":
                return self.custom_order_data.get(g.gameid, 999999)
            return g.title.lower()

        filtered.sort(key=sort_key)
        return filtered

    def _update_empty_state(self):
        """Show/hide the empty state based on whether games are visible."""
        has_games = self.flow_layout.count() > 0
        logger.debug("MainWindow._update_empty_state: has_games=%s, view=%s", has_games, self.current_view)
        if has_games:
            self.stack.setCurrentIndex(0)
        else:
            if self.current_view == VIEW_RECENTS:
                self.empty_title.setText("No recently played games")
                self.empty_subtitle.setText("Launch a game to see it here")
            elif self.current_view == VIEW_FAVORITES:
                self.empty_title.setText("No favorites yet")
                self.empty_subtitle.setText("Right-click a game to add it to favorites")
            else:
                self.empty_title.setText("Your library is empty")
                self.empty_subtitle.setText("Add a game to get started")
            self.stack.setCurrentIndex(1)

    # ------------------------------------------------------------------ #
    # Sidebar & view                                                       #
    # ------------------------------------------------------------------ #

    def _on_view_changed(self, view_name):
        logger.debug("MainWindow._on_view_changed: view_name=%s", view_name)
        if view_name == "settings":
            self.stack.setCurrentWidget(self.settings_view)
            return
        if view_name == "add":
            self._on_add_game()
            return
        self.current_view = view_name
        self.cfg.set("current-view", view_name)
        self.cfg.save()
        self._rebuild_grid()

    def _on_clear_recents(self):
        logger.debug("MainWindow._on_clear_recents")
        self.recents_repo.clear()
        self.recent_games.clear()
        self.cfg.set("current-view", VIEW_LIBRARY)
        self.cfg.save()
        self.current_view = VIEW_LIBRARY
        self.sidebar.set_view(VIEW_LIBRARY)

    def _toggle_sidebar(self):
        self.show_sidebar = not self.show_sidebar
        logger.debug("MainWindow._toggle_sidebar: show_sidebar=%s", self.show_sidebar)
        self.sidebar.setVisible(self.show_sidebar)
        self.cfg.set("show-sidebar", self.show_sidebar)
        self.cfg.save()

    def _update_play_button(self):
        """Update play/stop button based on selected card's running state."""
        logger.debug("MainWindow._update_play_button")
        from faugus.qt.icons import get_icon
        card = self._selected_card()
        if card and card.game.gameid in self.running:
            self.btn_play.setIcon(get_icon("stop", 16))
            self.btn_play.setToolTip("Stop selected game")
        else:
            self.btn_play.setIcon(get_icon("play", 16))
            self.btn_play.setToolTip("Play selected game")

    # ------------------------------------------------------------------ #
    # Search & filter                                                      #
    # ------------------------------------------------------------------ #

    def _on_search_changed(self, text):
        logger.debug("MainWindow._on_search_changed: text=%s", text)
        self._rebuild_grid()

    # ------------------------------------------------------------------ #
    # Sort & category                                                      #
    # ------------------------------------------------------------------ #

    def _show_sort_menu(self):
        logger.debug("MainWindow._show_sort_menu")
        menu = QMenu(self)
        for s_id, s_label in self.sort_map.items():
            action = menu.addAction(s_label)
            action.triggered.connect(partial(self._set_sort, s_id))
        menu.exec_(self.btn_sort.mapToGlobal(self.btn_sort.rect().bottomLeft()))

    def _set_sort(self, sort_id):
        logger.debug("MainWindow._set_sort: sort_id=%s", sort_id)
        self.current_sort_id = sort_id
        self.btn_sort.setText(self.sort_map[sort_id])
        self.cfg.set("sort", sort_id)
        self.cfg.save()
        self._load_sort_data()
        self._rebuild_grid()



    # ------------------------------------------------------------------ #
    # Game actions                                                         #
    # ------------------------------------------------------------------ #

    def _on_play(self):
        logger.debug("MainWindow._on_play")
        card = self._selected_card()
        if card:
            if card.game.gameid in self.running:
                self._stop_game(card.game)
            else:
                self._launch_game(card.game)

    def _on_card_double_clicked(self, game):
        logger.debug("MainWindow._on_card_double_clicked: gameid=%s, title=%s", game.gameid, game.title)
        if game.gameid in self.running:
            self._show_already_running(game.title)
        else:
            self._launch_game(game)

    def _launch_game(self, game):
        if game.gameid in self.running:
            logger.debug("MainWindow._launch_game: game %s already running, returning", game.gameid)
            return
        logger.debug("MainWindow._launch_game: gameid=%s, title=%s", game.gameid, game.title)

        from faugus.core.utils import save_json_file
        self.running[game.gameid] = True
        save_json_file(self.running, _running_games)

        # Update card overlay
        for card in self.game_cards:
            if card.game.gameid == game.gameid:
                card.set_playing(True)
                break

        # Launch in subprocess
        cmd = [sys.executable, "-m", "faugus.runner", "--game", game.gameid]
        proc = subprocess.Popen(cmd)
        self.processes[game.gameid] = proc

        # Update recents
        self.recents_repo.touch(game.gameid)
        self.recent_games = self.recents_repo.load()

        # Update latest games
        self._update_latest_games(game.gameid)

        # Refresh sort data
        self._load_sort_data()

        # Update play button
        self._update_play_button()

        # Close on launch
        if self.cfg.close_on_launch:
            QTimer.singleShot(500, self.close)

    def _update_latest_games(self, gameid):
        """Add gameid to the top of latest-games.txt."""
        logger.debug("MainWindow._update_latest_games: gameid=%s", gameid)
        entries = []
        if os.path.exists(_latest_games):
            try:
                with open(_latest_games) as f:
                    entries = [l.strip() for l in f if l.strip()]
            except Exception:
                pass
        if gameid in entries:
            entries.remove(gameid)
        entries.insert(0, gameid)
        with open(_latest_games, "w") as f:
            f.write("\n".join(entries) + "\n")

    def _show_already_running(self, title):
        logger.debug("MainWindow._show_already_running: title=%s", title)
        QMessageBox.information(self, "Faugus Launcher", f"{title} is already running!")

    def _selected_card(self):
        """Return the currently focused GameCard, or None."""
        logger.debug("MainWindow._selected_card")
        focused = QApplication.focusWidget()
        if isinstance(focused, GameCard):
            return focused
        # Try parent
        if focused and focused.parentWidget() and isinstance(focused.parentWidget(), GameCard):
            return focused.parentWidget()
        return None

    # ------------------------------------------------------------------ #
    # Context actions                                                      #
    # ------------------------------------------------------------------ #

    def _on_context_action(self, action, game):
        logger.debug("MainWindow._on_context_action: action=%s, gameid=%s", action, game.gameid)
        if action == "play":
            self._launch_game(game)
        elif action == "edit":
            self._edit_game(game)
        elif action == "delete":
            self._delete_game(game)
        elif action == "duplicate":
            self._duplicate_game(game)
        elif action == "hide":
            game.hidden = not game.hidden
            self.game_repo.update_game(game)
            self._rebuild_grid()
        elif action == "favorite":
            new_val = not getattr(game, 'favorite', False)
            game.favorite = new_val
            self.game_repo.update_game(game)
            self._rebuild_grid()
        elif action == "game_location":
            game_dir = os.path.dirname(game.path) if game.path else ""
            if game_dir:
                QDesktopServices.openUrl(QUrl.fromLocalFile(game_dir))
        elif action == "prefix_location":
            if game.prefix and os.path.isdir(game.prefix):
                QDesktopServices.openUrl(QUrl.fromLocalFile(game.prefix))
        elif action == "run_file":
            self._run_file_in_prefix(game)
        elif action == "show_logs":
            proton_log = f"{_logs_dir}/{game.gameid}/proton.log"
            if os.path.exists(proton_log):
                QDesktopServices.openUrl(QUrl.fromLocalFile(proton_log))
        elif action == "category":
            if isinstance(game, tuple):
                # (game, category) tuple from context menu
                g, cat = game
                cats = getattr(g, 'category', [])
                if isinstance(cats, str):
                    cats = [cats] if cats else []
                if cat in cats:
                    cats.remove(cat)
                else:
                    cats.append(cat)
                g.category = cats
                self.game_repo.update_game(g)
                self._rebuild_grid()

    def _edit_game(self, game):
        """Open the edit game view."""
        logger.debug("MainWindow._edit_game: gameid=%s, title=%s", game.gameid, game.title)
        self.add_game_view.load_game(game)
        self.stack.setCurrentWidget(self.add_game_view)

    def _delete_game(self, game):
        """Confirm and delete a game."""
        logger.debug("MainWindow._delete_game: gameid=%s, title=%s", game.gameid, game.title)
        reply = QMessageBox.question(
            self, "Delete Game",
            f"Are you sure you want to delete '{game.title}'?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.game_repo.delete_game(game.gameid)
            self._load_games()

    def _duplicate_game(self, game):
        """Duplicate a game with a new title."""
        logger.debug("MainWindow._duplicate_game: gameid=%s, title=%s", game.gameid, game.title)
        from PySide6.QtWidgets import QInputDialog
        title, ok = QInputDialog.getText(self, "Duplicate Game", "New title:", text=game.title)
        if ok and title:
            new_game = Game.from_dict(game.to_dict())
            new_game.gameid = f"{game.gameid}-copy"
            new_game.title = title
            self.game_repo.add_game(new_game)
            self._load_games()

    def _run_file_in_prefix(self, game):
        """Open a file chooser to run a file inside the game's prefix."""
        logger.debug("MainWindow._run_file_in_prefix: gameid=%s", game.gameid)
        from PySide6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getOpenFileName(
            self, "Select a file to run", "",
            "Windows executables (*.exe *.msi *.bat);;All files (*)"
        )
        if path:
            runner_cmd = f"{sys.executable} -m faugus.runner '{path}'"
            subprocess.Popen(runner_cmd, shell=True)

    # ------------------------------------------------------------------ #
    # Kill all                                                             #
    # ------------------------------------------------------------------ #

    def _on_kill_all(self):
        logger.debug("MainWindow._on_kill_all: running_count=%s", len(self.running))
        if not self.running:
            return
        reply = QMessageBox.question(
            self, "Force Close",
            "This will force close all running games. Continue?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            import signal
            for gameid in list(self.running.keys()):
                proc = self.processes.get(gameid)
                if proc:
                    try:
                        proc.terminate()
                    except Exception:
                        pass
            self.running.clear()
            self.processes.clear()
            from faugus.core.utils import save_json_file
            save_json_file({}, _running_games)
            self._rebuild_grid()
            self._update_play_button()

    def _stop_game(self, game):
        """Stop a running game."""
        gameid = game.gameid
        logger.debug("MainWindow._stop_game: gameid=%s", gameid)
        proc = self.processes.get(gameid)
        if proc:
            try:
                proc.terminate()
            except Exception:
                pass
        self.running.pop(gameid, None)
        self.processes.pop(gameid, None)
        from faugus.core.utils import save_json_file
        save_json_file(self.running, _running_games)
        for card in self.game_cards:
            if card.game.gameid == gameid:
                card.set_playing(False)
                break
        self._update_play_button()

    # ------------------------------------------------------------------ #
    # Check running                                                        #
    # ------------------------------------------------------------------ #

    def _check_running(self):
        logger.debug("MainWindow._check_running: tracked=%s", len(self.processes))
        changed = False
        for gameid, proc in list(self.processes.items()):
            if proc.poll() is not None:
                del self.processes[gameid]
                self.running.pop(gameid, None)
                changed = True

        if changed:
            from faugus.core.utils import save_json_file
            save_json_file(self.running, _running_games)
            self._rebuild_grid()
            self._update_play_button()

    # ------------------------------------------------------------------ #
    # Add game / Settings                                                  #
    # ------------------------------------------------------------------ #

    def _on_add_game(self):
        logger.debug("MainWindow._on_add_game")
        self.add_game_view.is_edit = False
        self.add_game_view.edit_game = None
        self.add_game_view.txt_title.clear()
        self.add_game_view.txt_path.clear()
        self.add_game_view.txt_prefix.clear()
        self.add_game_view.txt_banner.clear()
        self.add_game_view.txt_launch_args.clear()
        self.add_game_view.txt_game_args.clear()
        self.add_game_view.txt_env_vars.clear()
        self.add_game_view.txt_protonfix.clear()
        self.add_game_view.chk_mangohud.setChecked(False)
        self.add_game_view.chk_gamemode.setChecked(False)
        self.add_game_view.chk_disable_hidraw.setChecked(False)
        self.add_game_view.chk_prevent_sleep.setChecked(False)
        self.add_game_view.cmb_runner.setCurrentIndex(0)
        try:
            shutil.copyfile(_faugus_banner, self.add_game_view.banner_path_temp)
        except Exception:
            pass
        self.add_game_view._load_banner()
        self.stack.setCurrentWidget(self.add_game_view)

    def _on_game_saved(self):
        logger.debug("MainWindow._on_game_saved")
        self._load_games()
        self.sidebar.set_view("library")

    def _on_settings_changed(self):
        logger.debug("MainWindow._on_settings_changed: interface_mode=%s, show_categories=%s",
                     self.cfg.interface_mode, self.cfg.show_categories)
        self.interface_mode = self.cfg.interface_mode
        self.show_categories = self.cfg.show_categories
        self.show_labels = self.cfg.show_labels
        self.show_sidebar = self.cfg.show_sidebar
        self.sidebar.setVisible(self.show_sidebar)
        is_big = self.interface_mode in ("Blocks", "Banners")
        self.sidebar.set_big_mode(is_big)

    # ------------------------------------------------------------------ #
    # Window close                                                         #
    # ------------------------------------------------------------------ #

    def closeEvent(self, event):
        if self.cfg.window_behavior == "Remember":
            self.cfg.set("width", self.width())
            self.cfg.set("height", self.height())
        self.cfg.set("current-view", self.current_view)
        self.cfg.set("sort", self.current_sort_id)
        self.cfg.set("banner-size", self.banner_size)
        logger.debug("closeEvent: current_view=%s, interface_mode=%s, show_sidebar=%s",
                     self.current_view, self.cfg.interface_mode, self.cfg.show_sidebar)
        self.cfg.save()
        super().closeEvent(event)
