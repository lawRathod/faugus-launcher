"""Game data model with validation and serialization.

This module provides the Game dataclass and related utilities for
constructing, validating, and serializing game entries.
"""

from faugus.core.utils import GAME_FIELDS, GAME_DEFAULTS


class Game:
    """Represents a single game/application entry.

    Attributes are kept in sync with GAME_FIELDS for JSON round-tripping.
    Use ``from_dict()`` to construct from JSON data and ``to_dict()`` to
    serialize back.
    """

    __slots__ = GAME_FIELDS

    def __init__(
        self,
        gameid,
        title,
        path,
        prefix,
        launch_arguments,
        game_arguments,
        mangohud,
        gamemode,
        disable_hidraw,
        protonfix,
        runner,
        addapp_checkbox,
        addapp,
        addapp_bat,
        addapp_delay,
        addapp_first,
        banner,
        lossless_enabled,
        lossless_multiplier,
        lossless_flow,
        lossless_performance,
        lossless_hdr,
        lossless_present,
        playtime,
        hidden,
        prevent_sleep,
        category,
        icon,
        favorite=False,
    ):
        self.gameid = gameid
        self.title = title
        self.path = path
        self.launch_arguments = launch_arguments
        self.game_arguments = game_arguments
        self.mangohud = mangohud
        self.gamemode = gamemode
        self.prefix = prefix
        self.disable_hidraw = disable_hidraw
        self.protonfix = protonfix
        self.runner = runner
        self.addapp_checkbox = addapp_checkbox
        self.addapp = addapp
        self.addapp_bat = addapp_bat
        self.addapp_delay = addapp_delay
        self.addapp_first = addapp_first
        self.banner = banner
        self.lossless_enabled = lossless_enabled
        self.lossless_multiplier = lossless_multiplier
        self.lossless_flow = lossless_flow
        self.lossless_performance = lossless_performance
        self.lossless_hdr = lossless_hdr
        self.lossless_present = lossless_present
        self.playtime = playtime
        self.hidden = hidden
        self.prevent_sleep = prevent_sleep
        self.category = category
        self.icon = icon
        self.favorite = favorite

    # -- Construction helpers ------------------------------------------------

    @classmethod
    def from_dict(cls, data):
        """Construct a Game from a raw JSON dict.

        Missing fields are filled with defaults so legacy games.json
        entries never cause construction errors.
        """
        defaults = {f: "" for f in GAME_FIELDS}
        defaults.update(GAME_DEFAULTS)
        kwargs = {f: data.get(f, defaults[f]) for f in GAME_FIELDS}
        return cls(**kwargs)

    # -- Serialization -------------------------------------------------------

    def to_dict(self):
        """Serialize to a plain dict using GAME_FIELDS order."""
        return {field: getattr(self, field) for field in GAME_FIELDS}

    def to_save_dict(self, hidden=None):
        """Serialize for persistence, normalizing boolean fields to match
        the legacy games.json format.
        """
        d = self.to_dict()
        d["mangohud"] = True if self.mangohud else ""
        d["gamemode"] = True if self.gamemode else ""
        d["disable_hidraw"] = True if self.disable_hidraw else ""
        d["addapp_checkbox"] = "addapp_enabled" if self.addapp_checkbox else ""
        if hidden is not None:
            d["hidden"] = hidden
        return d

    # -- Query helpers -------------------------------------------------------

    @property
    def display_name(self):
        """Return the title stripped of whitespace."""
        return self.title.strip() if self.title else ""

    @property
    def is_installed(self):
        """Check if the game executable path exists."""
        import os
        return bool(self.path) and os.path.isfile(self.path)

    @property
    def has_addapp(self):
        """Check if an additional application is configured."""
        return bool(self.addapp_checkbox) and bool(self.addapp)

    @property
    def has_lossless(self):
        """Check if Lossless Scaling is enabled."""
        return bool(self.lossless_enabled)

    @property
    def formatted_playtime(self):
        """Return a human-readable playtime string."""
        if not self.playtime:
            return "0m"
        hours = self.playtime // 3600
        minutes = (self.playtime % 3600) // 60
        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"

    # -- Dunder methods ------------------------------------------------------

    def __repr__(self):
        return f"Game(gameid={self.gameid!r}, title={self.title!r})"

    def __eq__(self, other):
        if not isinstance(other, Game):
            return NotImplemented
        return self.gameid == other.gameid

    def __hash__(self):
        return hash(self.gameid)
