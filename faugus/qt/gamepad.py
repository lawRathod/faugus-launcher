"""Qt gamepad navigation using pygame."""

import logging
import time

import pygame

from PySide6.QtCore import QObject, QTimer, Signal
from PySide6.QtWidgets import QApplication, QPushButton

from faugus.qt.main_window import MainWindow
from faugus.qt.game_card import GameCard

logger = logging.getLogger(__name__)


def get_button_map(joy):
    name = joy.get_name().lower()
    if any(kw in name for kw in ("playstation", "dualshock", "dualsense", "ps4", "ps5")):
        return {"confirm": 0, "back": 1, "square": 2, "triangle": 3, "lb": 9, "rb": 10, "start": 6}
    return {"confirm": 0, "back": 1, "square": 2, "triangle": 3, "lb": 4, "rb": 5, "start": 7}


class GamepadManager(QObject):
    gamepad_connected = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.joystick = None
        self.button_map = None
        self.axis_threshold = 0.7
        self.reset_threshold = 0.3
        self.can_move_x = True
        self.can_move_y = True
        self.held_direction = None
        self.hold_start_time = 0
        self.last_repeat_time = 0
        self.repeat_delay = 0.5
        self.repeat_interval = 0.1
        self._connected = False

        try:
            pygame.init()
            pygame.joystick.init()
            if pygame.joystick.get_count() > 0:
                self._init_joystick(0)
        except Exception as e:
            logger.debug("Gamepad init failed: %s", e)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._poll)
        self._timer.start(50)

    def _init_joystick(self, index):
        try:
            self.joystick = pygame.joystick.Joystick(index)
            self.joystick.init()
            self.button_map = get_button_map(self.joystick)
            self._connected = True
            logger.debug("Gamepad connected: %s", self.joystick.get_name())
        except Exception as e:
            self._connected = False
            logger.debug("Failed to init joystick: %s", e)
        self.gamepad_connected.emit(self._connected)

    def _main(self):
        w = QApplication.activeWindow()
        return w if isinstance(w, MainWindow) else None

    def _sidebar_buttons(self, win):
        if not win or not win.sidebar:
            return []
        nav = []
        for name in ("library", "recents", "favorites"):
            btn = win.sidebar.buttons.get(name)
            if btn:
                nav.append(btn)
        return nav

    def _game_cards(self, win):
        return list(win.game_cards)

    def _settings_btn(self, win):
        return win.sidebar.buttons.get("settings")

    def _focused_widget(self, win):
        return win.focusWidget()

    def _focus_index(self, items, focused):
        for i, w in enumerate(items):
            if w is focused:
                return i
        return -1

    def _navigate_sidebar(self, win, direction):
        btns = self._sidebar_buttons(win)
        if not btns:
            return
        focused = self._focused_widget(win)
        idx = self._focus_index(btns, focused)
        if idx < 0:
            btns[0].setFocus()
            return
        if direction == "up" and idx > 0:
            btns[idx - 1].setFocus()
        elif direction == "down" and idx < len(btns) - 1:
            btns[idx + 1].setFocus()

    def _focus_card(self, card):
        card.setFocus()
        parent = card.parentWidget()
        scroll = parent.parentWidget() if parent else None
        from PySide6.QtWidgets import QScrollArea
        while scroll:
            if isinstance(scroll, QScrollArea):
                scroll.ensureWidgetVisible(card, 20, 20)
                break
            scroll = scroll.parentWidget()

    def _navigate_cards(self, win, direction):
        cards = self._game_cards(win)
        if not cards:
            return
        focused = self._focused_widget(win)
        idx = self._focus_index(cards, focused)
        flow = getattr(win, "flow_layout", None)
        if direction in ("up", "down") and flow:
            new_idx = flow.index_above(idx) if direction == "up" else flow.index_below(idx)
            if new_idx is not None and 0 <= new_idx < len(cards):
                self._focus_card(cards[new_idx])
            return
        if direction == "right":
            if 0 <= idx < len(cards) - 1:
                self._focus_card(cards[idx + 1])
            elif idx < 0:
                self._focus_card(cards[0])
        elif direction == "left":
            if idx > 0:
                self._focus_card(cards[idx - 1])
        elif direction == "down":
            if 0 <= idx < len(cards) - 1:
                self._focus_card(cards[idx + 1])
            elif idx < 0:
                self._focus_card(cards[0])
        elif direction == "up":
            if idx > 0:
                self._focus_card(cards[idx - 1])

    def _on_confirm(self, win):
        focused = self._focused_widget(win)
        if isinstance(focused, GameCard):
            focused.doubleClicked.emit(focused.game)
        elif isinstance(focused, QPushButton):
            focused.animateClick()
        elif focused:
            if hasattr(focused, "click"):
                focused.click()
            elif hasattr(focused, "toggle"):
                focused.toggle()

    def _on_back(self, win):
        cards = self._game_cards(win)
        btns = self._sidebar_buttons(win)
        if cards and isinstance(self._focused_widget(win), GameCard):
            btns and btns[0].setFocus()

    def _on_kill(self, win):
        if hasattr(win, "_on_kill_all"):
            win._on_kill_all()

    def _on_settings(self, win):
        btn = self._settings_btn(win)
        if btn:
            btn.setFocus()
            win.sidebar.set_view("settings")

    def _poll(self):
        for event in pygame.event.get():
            if event.type == pygame.JOYDEVICEADDED:
                self._init_joystick(event.device_index)
                continue
            elif event.type == pygame.JOYDEVICEREMOVED:
                if self.joystick and self.joystick.get_instance_id() == event.instance_id:
                    self.joystick.quit()
                    self.joystick = None
                    self.button_map = None
                    self._connected = False
                    self.gamepad_connected.emit(False)
                    logger.debug("Gamepad disconnected")
                continue

            if not self.joystick or not self.button_map:
                continue

            win = self._main()
            if not win:
                continue

            if event.type == pygame.JOYAXISMOTION:
                self._handle_axis(event, win)
            elif event.type == pygame.JOYHATMOTION:
                self._handle_hat(event.value, win)
            elif event.type == pygame.JOYBUTTONDOWN:
                self._handle_button(event.button, win)

        if self.held_direction is not None:
            now = time.time()
            if now - self.hold_start_time >= self.repeat_delay:
                if now - self.last_repeat_time >= self.repeat_interval:
                    self._dispatch(win, self.held_direction)
                    self.last_repeat_time = now

    def _set_held(self, direction, win):
        if direction is not None:
            if self.held_direction != direction:
                self.held_direction = direction
                self.hold_start_time = time.time()
                self.last_repeat_time = time.time()
                self._dispatch(win, direction)
        else:
            self.held_direction = None

    def _dispatch(self, win, direction):
        focused = self._focused_widget(win)
        btns = self._sidebar_buttons(win)
        cards = self._game_cards(win)
        in_sidebar = focused in btns
        in_cards = focused in cards

        if direction == "up":
            if in_cards:
                if self._focus_index(cards, focused) == 0:
                    btns and btns[0].setFocus()
                else:
                    self._navigate_cards(win, "up")
            elif in_sidebar:
                self._navigate_sidebar(win, "up")
            else:
                btns and btns[0].setFocus()
        elif direction == "down":
            if in_sidebar:
                focused_idx = self._focus_index(btns, focused)
                if focused_idx == len(btns) - 1 and cards:
                    cards[0].setFocus()
                else:
                    self._navigate_sidebar(win, "down")
            elif in_cards:
                self._navigate_cards(win, "down")
            else:
                btns and btns[0].setFocus()
        elif direction == "right":
            if in_sidebar:
                if cards:
                    cards[0].setFocus()
            elif in_cards:
                self._navigate_cards(win, "right")
        elif direction == "left":
            if in_cards:
                self._navigate_cards(win, "left")
                if self._focus_index(cards, self._focused_widget(win)) == 0:
                    btns and btns[0].setFocus()

    def _handle_axis(self, event, win):
        if event.axis == 1:
            if self.can_move_y:
                if event.value < -self.axis_threshold:
                    self._set_held("up", win)
                    self.can_move_y = False
                elif event.value > self.axis_threshold:
                    self._set_held("down", win)
                    self.can_move_y = False
            elif abs(event.value) < self.reset_threshold:
                self.can_move_y = True
                if self.held_direction in ("up", "down"):
                    self._set_held(None, win)
        elif event.axis == 0:
            if self.can_move_x:
                if event.value < -self.axis_threshold:
                    self._set_held("left", win)
                    self.can_move_x = False
                elif event.value > self.axis_threshold:
                    self._set_held("right", win)
                    self.can_move_x = False
            elif abs(event.value) < self.reset_threshold:
                self.can_move_x = True
                if self.held_direction in ("left", "right"):
                    self._set_held(None, win)

    def _handle_hat(self, value, win):
        x, y = value
        direction = None
        if y == 1:
            direction = "up"
        elif y == -1:
            direction = "down"
        elif x == -1:
            direction = "left"
        elif x == 1:
            direction = "right"
        self._set_held(direction, win)

    def _handle_button(self, button, win):
        btn = self.button_map
        if button == btn["confirm"]:
            self._on_confirm(win)
        elif button == btn["back"]:
            self._on_back(win)
        elif button == btn["square"]:
            self._on_kill(win)
        elif button == btn["triangle"]:
            focused = self._focused_widget(win)
            if isinstance(focused, GameCard):
                from PySide6.QtWidgets import QMenu
                menu = QMenu(focused)
                menu.addAction("Play").triggered.connect(
                    lambda: focused.context_action.emit("play", focused.game))
                menu.addAction("Edit").triggered.connect(
                    lambda: focused.context_action.emit("edit", focused.game))
                menu.addAction("Delete").triggered.connect(
                    lambda: focused.context_action.emit("delete", focused.game))
                menu.exec(focused.mapToGlobal(focused.rect().center()))
        elif button == btn["rb"]:
            self._on_settings(win)
