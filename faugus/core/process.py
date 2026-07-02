"""Running process tracking and management.

Provides a clean interface for tracking game processes, managing
playtime, and handling process lifecycle events.
"""

import os
import time


class ProcessManager:
    """Tracks the currently running game process and its metadata.

    This replaces the scattered process state that was previously
    stored as instance attributes on the GTK window class.
    """

    def __init__(self):
        self._process = None
        self._start_time = None
        self._game_id = None
        self._game_title = None

    @property
    def is_running(self):
        """Check if a game process is currently running."""
        return self._process is not None and self._process.poll() is None

    @property
    def game_id(self):
        """Return the gameid of the running game."""
        return self._game_id

    @property
    def game_title(self):
        """Return the title of the running game."""
        return self._game_title

    @property
    def runtime_seconds(self):
        """Return how long the game has been running (or ran)."""
        if self._start_time is None:
            return 0
        return int(time.time() - self._start_time)

    def start(self, process, game_id=None, game_title=None):
        """Register a running game process."""
        self._process = process
        self._start_time = time.time()
        self._game_id = game_id
        self._game_title = game_title

    def stop(self):
        """Unregister the running process and return total runtime."""
        runtime = self.runtime_seconds
        self._process = None
        self._start_time = None
        self._game_id = None
        self._game_title = None
        return runtime

    def get_pid(self):
        """Return the PID of the running process, or None."""
        if self._process:
            return self._process.pid
        return None

    def poll(self):
        """Check if the process has exited. Returns returncode or None."""
        if self._process:
            return self._process.poll()
        return None
