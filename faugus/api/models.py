"""Pydantic models for the Faugus Launcher API."""

from pydantic import BaseModel, Field
from typing import Any


class GameCreate(BaseModel):
    title: str = Field(..., min_length=1)
    exe: str = Field(..., min_length=1)
    path: str = Field(..., min_length=1)
    prefix: str = Field(..., min_length=1)
    args: str = ""
    runner: str = ""
    icon: str = ""
    banner: str = ""
    category: list[str] = []
    hidden: bool = False
    settings: dict[str, Any] = {}


class GameUpdate(BaseModel):
    title: str = Field(..., min_length=1)
    exe: str = Field(..., min_length=1)
    path: str = Field(..., min_length=1)
    prefix: str = Field(..., min_length=1)
    args: str = ""
    runner: str = ""
    icon: str = ""
    banner: str = ""
    category: list[str] = []
    hidden: bool = False
    settings: dict[str, Any] = {}


class GameResponse(BaseModel):
    gameid: str
    title: str
    exe: str
    path: str
    args: str
    runner: str
    prefix: str
    icon: str
    banner: str
    category: list[str]
    hidden: bool
    playtime: int
    lastplayed: int
    settings: dict[str, Any]


class CategoryUpdate(BaseModel):
    categories: list[str]


class DuplicateRequest(BaseModel):
    title: str = Field(..., min_length=1)


class CustomOrderRequest(BaseModel):
    order: dict[str, int]


class LaunchResponse(BaseModel):
    process_id: int
    status: str


class ErrorResponse(BaseModel):
    detail: str
