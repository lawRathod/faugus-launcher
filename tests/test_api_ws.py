"""Tests for WebSocket endpoints — TDD Red-Green cycle."""

import os


class TestGameLogWebSocket:
    """WS /api/ws/game/{gameid}/log"""

    def test_connect_and_disconnect(self, client) -> None:
        """Can connect and immediately disconnect."""
        with client.websocket_connect("/api/ws/game/test-game/log") as ws:
            data = ws.receive_json()
            assert data["type"] == "connected"
            assert data["gameid"] == "test-game"

    def test_ping_pong(self, client) -> None:
        """Sending ping after log_end returns pong."""
        with client.websocket_connect("/api/ws/game/test-game/log") as ws:
            ws.receive_json()  # connected
            # Drain until log_end
            while True:
                msg = ws.receive_json()
                if msg["type"] == "log_end":
                    break
            # Now in keepalive — send ping
            ws.send_text("ping")
            data = ws.receive_json()
            assert data["type"] == "pong"

    def test_receives_log_lines(self, client, pm) -> None:
        """When log file has content, it's streamed on connect."""
        log_dir = os.path.join(pm.logs_dir, "test-game")
        os.makedirs(log_dir, exist_ok=True)
        with open(os.path.join(log_dir, "proton.log"), "w") as f:
            f.write("line1\nline2\nline3\n")
        with client.websocket_connect("/api/ws/game/test-game/log") as ws:
            data = ws.receive_json()
            assert data["type"] == "connected"
            # Read all log lines
            lines = []
            while True:
                msg = ws.receive_json()
                if msg["type"] == "log_line":
                    lines.append(msg["line"])
                elif msg["type"] == "log_end":
                    break
            assert "line1" in lines
            assert "line2" in lines


class TestGameStatusWebSocket:
    """WS /api/ws/game/{gameid}/status"""

    def test_connect_and_disconnect(self, client) -> None:
        """Can connect and immediately disconnect."""
        with client.websocket_connect("/api/ws/game/test-game/status") as ws:
            data = ws.receive_json()
            assert data["type"] == "connected"
            assert data["gameid"] == "test-game"

    def test_ping_pong(self, client) -> None:
        """Sending ping returns pong."""
        with client.websocket_connect("/api/ws/game/test-game/status") as ws:
            ws.receive_json()  # connected
            ws.send_text("ping")
            data = ws.receive_json()
            assert data["type"] == "pong"
