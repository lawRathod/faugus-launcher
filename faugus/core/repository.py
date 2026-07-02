"""Centralized JSON file I/O for game data.

This module provides a single place for all games.json and recents.json
operations, replacing scattered load/save calls throughout the codebase.
"""

import os
from faugus.core.utils import (
    load_json_file,
    save_json_file,
    load_recents,
    save_recents,
    touch_recent,
    clear_recents,
    GAME_FIELDS,
    GAME_DEFAULTS,
)
from faugus.core.models import Game


class GameRepository:
    """Manages persistence of game data to games.json.

    All game CRUD operations go through this class, ensuring consistent
    serialization and preventing file I/O from being scattered across
    the codebase.
    """

    def __init__(self, games_file):
        self._games_file = games_file

    def load_all(self):
        """Load all games from games.json and return a list of Game objects.

        Returns an empty list if the file is missing or malformed.
        """
        raw = load_json_file(self._games_file, [])
        if not isinstance(raw, list):
            return []
        return [Game.from_dict(entry) for entry in raw if isinstance(entry, dict)]

    def save_all(self, games):
        """Persist a list of Game objects to games.json."""
        data = [game.to_save_dict() for game in games]
        save_json_file(data, self._games_file)

    def find_by_id(self, gameid):
        """Find a single game by its gameid.

        Returns the Game object or None if not found.
        """
        games = self.load_all()
        for game in games:
            if game.gameid == gameid:
                return game
        return None

    def add_game(self, game):
        """Add a new game and persist. Returns the updated list."""
        games = self.load_all()
        games.append(game)
        self.save_all(games)
        return games

    def update_game(self, game):
        """Update an existing game (matched by gameid) and persist.

        Returns the updated list, or the original list if gameid not found.
        """
        games = self.load_all()
        for i, existing in enumerate(games):
            if existing.gameid == game.gameid:
                games[i] = game
                self.save_all(games)
                return games
        return games

    def delete_game(self, gameid):
        """Remove a game by gameid and persist. Returns the updated list."""
        games = self.load_all()
        games = [g for g in games if g.gameid != gameid]
        self.save_all(games)
        return games

    def set_favorite(self, gameid, favorite):
        """Set the favorite flag for a single game. Returns True if found."""
        games = self.load_all()
        updated = False
        for game in games:
            if game.gameid == gameid:
                game.favorite = bool(favorite)
                updated = True
                break
        if updated:
            self.save_all(games)
        return updated

    def update_playtime(self, gameid, seconds):
        """Add seconds to a game's playtime. Returns True if found."""
        games = self.load_all()
        updated = False
        for game in games:
            if game.gameid == gameid:
                game.playtime = (game.playtime or 0) + seconds
                updated = True
                break
        if updated:
            self.save_all(games)
        return updated

    def get_all_gameids(self):
        """Return a set of all gameids for fast lookup."""
        raw = load_json_file(self._games_file, [])
        if not isinstance(raw, list):
            return set()
        return {entry.get("gameid") for entry in raw if isinstance(entry, dict)}

    def count(self):
        """Return the number of games."""
        raw = load_json_file(self._games_file, [])
        if not isinstance(raw, list):
            return 0
        return len(raw)


class RecentsRepository:
    """Manages the recents.json file (recently launched games)."""

    def __init__(self, recents_file):
        self._recents_file = recents_file

    def load(self):
        """Load the recents map. Returns ``{gameid: timestamp}``."""
        return load_recents(self._recents_file)

    def save(self, recents):
        """Persist the recents map."""
        save_recents(self._recents_file, recents)

    def touch(self, gameid):
        """Record that a game was just launched."""
        return touch_recent(self._recents_file, gameid)

    def clear(self):
        """Remove the recents file."""
        clear_recents(self._recents_file)

    def get_recent_ids(self):
        """Return a list of gameids in reverse-chronological order."""
        recents = self.load()
        return sorted(recents.keys(), key=lambda k: recents[k], reverse=True)
