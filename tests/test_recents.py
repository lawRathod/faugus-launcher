"""Tests for the new recents.json timestamp helpers."""

import os
import time

from faugus.utils import (
    load_recents,
    save_recents,
    touch_recent,
    clear_recents,
    format_recent_age,
)


def test_load_recents_missing_returns_empty(tmp_path):
    """A missing file should not raise; returns an empty dict."""
    recents_file = str(tmp_path / "recents.json")
    assert load_recents(recents_file) == {}


def test_save_then_load_roundtrip(tmp_path):
    """What we save is what we load."""
    recents_file = str(tmp_path / "recents.json")
    data = {"game-a": 1000.0, "game-b": 2000.5}
    save_recents(recents_file, data)
    loaded = load_recents(recents_file)
    assert loaded == data


def test_touch_recent_inserts_new_entry(tmp_path):
    """touch_recent adds a brand-new gameid with a current timestamp."""
    recents_file = str(tmp_path / "recents.json")
    before = time.time()
    recents = touch_recent(recents_file, "game-x")
    after = time.time()
    assert "game-x" in recents
    assert before <= recents["game-x"] <= after


def test_touch_recent_overwrites_existing(tmp_path):
    """touch_recent updates an existing entry instead of duplicating."""
    recents_file = str(tmp_path / "recents.json")
    save_recents(recents_file, {"game-y": 100.0})
    recents = touch_recent(recents_file, "game-y")
    assert len(recents) == 1
    assert recents["game-y"] > 100.0  # updated to ~now


def test_clear_recents_removes_file(tmp_path):
    """clear_recents deletes the file so the next load returns empty."""
    recents_file = str(tmp_path / "recents.json")
    save_recents(recents_file, {"game-z": 1.0})
    assert os.path.exists(recents_file)
    clear_recents(recents_file)
    assert not os.path.exists(recents_file)
    assert load_recents(recents_file) == {}


def test_clear_recents_missing_file_is_noop(tmp_path):
    """clear_recents must not raise if the file is already gone."""
    recents_file = str(tmp_path / "recents.json")
    clear_recents(recents_file)  # no exception


def test_load_recents_handles_corrupt_data(tmp_path):
    """A non-dict file (e.g. someone hand-edited a list) returns empty."""
    recents_file = str(tmp_path / "recents.json")
    with open(recents_file, "w") as f:
        f.write("[1, 2, 3]")  # JSON list, not dict
    assert load_recents(recents_file) == {}


def test_format_recent_age_just_now():
    """A timestamp from 0 seconds ago -> 'just now'."""
    text = format_recent_age(time.time())
    assert text == "just now"


def test_format_recent_age_minutes():
    """A timestamp from 5 minutes ago -> '5 min ago'."""
    text = format_recent_age(time.time() - 5 * 60)
    assert text == "5 min ago"


def test_format_recent_age_hours():
    """A timestamp from 2 hours ago -> '2 h ago'."""
    text = format_recent_age(time.time() - 2 * 3600)
    assert text == "2 h ago"


def test_format_recent_age_yesterday():
    """A timestamp from ~1 day ago -> 'yesterday'."""
    text = format_recent_age(time.time() - 25 * 3600)
    assert text == "yesterday"


def test_format_recent_age_days():
    """A timestamp from 3 days ago -> '3 d ago'."""
    text = format_recent_age(time.time() - 3 * 86400)
    assert text == "3 d ago"


def test_format_recent_age_weeks():
    """A timestamp from 2 weeks ago -> '2 w ago'."""
    text = format_recent_age(time.time() - 14 * 86400)
    assert text == "2 w ago"


def test_format_recent_age_very_old_returns_none():
    """A timestamp from >6 months ago returns None (label hidden)."""
    text = format_recent_age(time.time() - 200 * 86400)
    assert text is None


def test_format_recent_age_future_timestamp():
    """A timestamp slightly in the future returns 'just now' (clock skew)."""
    text = format_recent_age(time.time() + 10)
    assert text == "just now"
