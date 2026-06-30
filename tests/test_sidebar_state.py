"""Tests for the sidebar state-management helpers.

The actual GTK widget construction happens in faugus.launcher.Main and is
exercised manually. The pure-logic helpers in faugus.utils that translate
between user-facing view names, config values, and filter decisions are
tested here.
"""
import pytest

from faugus.utils import (
    VIEW_LIBRARY,
    VIEW_RECENTS,
    VIEW_FAVORITES,
    VALID_VIEWS,
    normalize_view,
)


class TestValidViews:
    def test_all_three_views_present(self):
        assert VIEW_LIBRARY in VALID_VIEWS
        assert VIEW_RECENTS in VALID_VIEWS
        assert VIEW_FAVORITES in VALID_VIEWS

    def test_views_are_lowercase_strings(self):
        for v in VALID_VIEWS:
            assert isinstance(v, str)
            assert v == v.lower()


class TestNormalizeView:
    def test_known_views_passthrough(self):
        assert normalize_view(VIEW_LIBRARY) == VIEW_LIBRARY
        assert normalize_view(VIEW_RECENTS) == VIEW_RECENTS
        assert normalize_view(VIEW_FAVORITES) == VIEW_FAVORITES

    def test_unknown_view_falls_back_to_library(self):
        assert normalize_view("garbage") == VIEW_LIBRARY
        assert normalize_view("") == VIEW_LIBRARY
        assert normalize_view("Library") == VIEW_LIBRARY  # case-sensitive
        assert normalize_view("LIBRARY") == VIEW_LIBRARY

    def test_none_falls_back_to_library(self):
        assert normalize_view(None) == VIEW_LIBRARY

    def test_returns_string(self):
        result = normalize_view("anything")
        assert isinstance(result, str)
