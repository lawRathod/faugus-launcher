"""Pydantic models for the Faugus Launcher API.

Field names match the canonical GAME_FIELDS in utils.py so the API maps cleanly
to the existing games.json data model.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator


class GameCreate(BaseModel):
    """Fields required to create a new game entry.

    Matches the canonical GAME_FIELDS subset that makes sense at creation time.
    Omitted fields (mangohud, gamemode, lossless_*, addapp_*, etc.) default
    to safe empty/false values when created through the API.
    """
    title: str = Field(..., min_length=1)
    path: str = Field(..., min_length=1, description="Path to the .exe")
    prefix: str = Field(..., min_length=1, description="Wine/Proton prefix path")
    launch_arguments: str = ""
    game_arguments: str = ""
    runner: str = ""
    protonfix: str = ""
    icon: str = ""
    banner: str = ""
    category: list[str] = []
    hidden: bool = False
    mangohud: bool = False
    gamemode: bool = False
    disable_hidraw: bool = False
    prevent_sleep: bool = False
    settings: dict[str, Any] = {}

    @field_validator("path", "prefix")
    @classmethod
    def no_path_traversal(cls, v: str) -> str:
        if ".." in v:
            raise ValueError("Path traversal not allowed")
        return v


class GameUpdate(BaseModel):
    """Fields the API client provides when updating.

    The server merges these into the existing record — fields not sent
    are preserved from the original entry.
    """
    title: str = Field(..., min_length=1)
    path: str = Field(..., min_length=1, description="Path to the .exe")
    prefix: str = Field(..., min_length=1, description="Wine/Proton prefix path")
    launch_arguments: str = ""
    game_arguments: str = ""
    runner: str = ""
    protonfix: str = ""
    icon: str = ""
    banner: str = ""
    category: list[str] = []
    hidden: bool = False
    mangohud: bool = False
    gamemode: bool = False
    disable_hidraw: bool = False
    prevent_sleep: bool = False
    settings: dict[str, Any] = {}

    @field_validator("path", "prefix")
    @classmethod
    def no_path_traversal(cls, v: str) -> str:
        if ".." in v:
            raise ValueError("Path traversal not allowed")
        return v


class GameResponse(BaseModel):
    """Full game record returned by the API."""
    gameid: str
    title: str
    path: str
    prefix: str
    launch_arguments: str
    game_arguments: str
    runner: str
    protonfix: str
    icon: str
    banner: str
    category: list[str]
    hidden: bool
    mangohud: bool | str
    gamemode: bool | str
    disable_hidraw: bool | str
    prevent_sleep: bool
    playtime: int
    lastplayed: int
    addapp_checkbox: bool | str
    addapp: str
    addapp_bat: str
    addapp_delay: str
    addapp_first: str
    lossless_enabled: bool | str
    lossless_multiplier: str
    lossless_flow: str
    lossless_performance: str
    lossless_hdr: str
    lossless_present: str
    settings: dict[str, Any]


class CategoryUpdate(BaseModel):
    categories: list[str]


class DuplicateRequest(BaseModel):
    title: str = Field(..., min_length=1)


class CustomOrderRequest(BaseModel):
    order: dict[str, int]


class ErrorResponse(BaseModel):
    detail: str
