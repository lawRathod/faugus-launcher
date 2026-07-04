"""Tests for WebSocket endpoints — TDD Red-Green cycle."""

import json


class TestGameLogWebSocket:
    """WS /api/ws/game/{gameid}/log"""

    def test_connect_and_disconnect(self, client) -> None:
        """Can connect and immediately disconnect."""
        with client.websocket_connect("/api/ws/game/test-game/log") as ws:
            data = ws.receive_json()
            assert data["type"] == "connected"
            assert data["gameid"] == "test-game"


class TestGameStatusWebSocket:
    """WS /api/ws/game/{gameid}/status"""

    def test_connect_and_disconnect(self, client) -> None:
        """Can connect and immediately disconnect."""
        with client.websocket_connect("/api/ws/game/test-game/status") as ws:
            data = ws.receive_json()
            assert data["type"] == "connected"
            assert data["gameid"] == "test-game"
