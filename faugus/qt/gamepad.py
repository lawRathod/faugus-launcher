"""Qt gamepad navigation using pygame."""

import logging
import time

import pygame

from PySide6.QtCore import QEvent, QObject, Qt, QTimer, Signal
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QApplication

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
        self.last_focus_path = None
        self.axis_threshold = 0.7
        self.reset_threshold = 0.3
        self.can_move_x = True
        self.can_move_y = True
        self.held_direction = None
        self.hold_start_time = 0
        self.last_repeat_time = 0
        self.repeat_delay = 0.5
        self.repeat_interval = 0.1

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
            logger.debug("Gamepad connected: %s", self.joystick.get_name())
            self.gamepad_connected.emit(True)
        except Exception as e:
            logger.debug("Failed to init joystick: %s", e)

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
                    self.gamepad_connected.emit(False)
                    logger.debug("Gamepad disconnected")
                continue

            if not self.joystick or not self.button_map:
                continue

            if event.type == pygame.JOYAXISMOTION:
                self._handle_axis(event)
            elif event.type == pygame.JOYHATMOTION:
                self._handle_hat(event.value)
            elif event.type == pygame.JOYBUTTONDOWN:
                self._handle_button(event.button)

        if self.held_direction is not None:
            now = time.time()
            if now - self.hold_start_time >= self.repeat_delay:
                if now - self.last_repeat_time >= self.repeat_interval:
                    self._dispatch_navigation(self.held_direction)
                    self.last_repeat_time = now

    def _set_held(self, direction):
        if direction is not None:
            if self.held_direction != direction:
                self.held_direction = direction
                self.hold_start_time = time.time()
                self.last_repeat_time = time.time()
                self._dispatch_navigation(direction)
        else:
            self.held_direction = None

    def _dispatch_navigation(self, direction):
        win = QApplication.activeWindow()
        if not win:
            return
        if direction == "up":
            self._focus_previous(win)
        elif direction == "down":
            self._focus_next(win)
        elif direction == "left":
            self._focus_left(win)
        elif direction == "right":
            self._focus_right(win)

    def _handle_axis(self, event):
        if event.axis == 1:
            if self.can_move_y:
                if event.value < -self.axis_threshold:
                    self._set_held("up")
                    self.can_move_y = False
                elif event.value > self.axis_threshold:
                    self._set_held("down")
                    self.can_move_y = False
            elif abs(event.value) < self.reset_threshold:
                self.can_move_y = True
                if self.held_direction in ("up", "down"):
                    self._set_held(None)
        elif event.axis == 0:
            if self.can_move_x:
                if event.value < -self.axis_threshold:
                    self._set_held("left")
                    self.can_move_x = False
                elif event.value > self.axis_threshold:
                    self._set_held("right")
                    self.can_move_x = False
            elif abs(event.value) < self.reset_threshold:
                self.can_move_x = True
                if self.held_direction in ("left", "right"):
                    self._set_held(None)

    def _handle_hat(self, value):
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
        self._set_held(direction)

    def _handle_button(self, button):
        btn = self.button_map
        win = QApplication.activeWindow()
        if not win:
            return
        focused = win.focusWidget()
        if button == btn["confirm"]:
            if focused:
                if hasattr(focused, "animateClick"):
                    focused.animateClick()
                elif hasattr(focused, "click"):
                    focused.click()
                elif hasattr(focused, "toggle"):
                    focused.toggle()
        elif button == btn["back"]:
            if hasattr(win, "reject"):
                win.reject()
        elif button == btn["square"]:
            self._trigger_action(win, "kill")
        elif button == btn["triangle"]:
            if focused:
                menu = getattr(focused, "context_menu", None)
                if menu:
                    menu.exec(focused.mapToGlobal(focused.rect().center()))
        elif button == btn["lb"]:
            self._trigger_action(win, "add")
        elif button == btn["rb"]:
            self._trigger_action(win, "settings")

    def _trigger_action(self, win, name):
        from faugus.qt.main_window import MainWindow
        if isinstance(win, MainWindow):
            if name == "kill":
                win._on_kill_all()
            elif name == "settings":
                win.sidebar.set_view("settings")
            elif name == "add":
                win.sidebar.set_view("add")

    def _focus_previous(self, win):
        focused = win.focusWidget()
        if focused:
            QApplication.postEvent(focused, QKeyEvent(QEvent.KeyPress, Qt.Key_Up, Qt.NoModifier))

    def _focus_next(self, win):
        focused = win.focusWidget()
        if focused:
            QApplication.postEvent(focused, QKeyEvent(QEvent.KeyPress, Qt.Key_Down, Qt.NoModifier))

    def _focus_left(self, win):
        focused = win.focusWidget()
        if focused:
            QApplication.postEvent(focused, QKeyEvent(QEvent.KeyPress, Qt.Key_Left, Qt.NoModifier))

    def _focus_right(self, win):
        focused = win.focusWidget()
        if focused:
            QApplication.postEvent(focused, QKeyEvent(QEvent.KeyPress, Qt.Key_Right, Qt.NoModifier))
