from unittest.mock import MagicMock

from shatranj.domain.network.game_server import GameServer, GameSession
from shatranj.domain.network.protocol import Message, Response


def test_handle_quit_cleans_active_session_and_notifies_opponent():
    server = GameServer("TestServer")

    white = MagicMock()
    white.player_id = "white-id"
    black = MagicMock()
    black.player_id = "black-id"

    server.players = {
        "white-id": {"conn": white, "name": "White", "status": "ingame"},
        "black-id": {"conn": black, "name": "Black", "status": "ingame"},
    }
    server.active_sessions["session-1"] = GameSession("session-1", white, black)

    server._handle_quit(white)

    assert "session-1" not in server.active_sessions
    assert "white-id" not in server.players
    assert server.players["black-id"]["status"] == "idle"
    black.send.assert_called_once()
    white.stop.assert_called_once()


def test_handle_scoreboard_sends_ranked_rows():
    server = GameServer("TestServer")
    conn = MagicMock()
    server.players = {
        "p1": {"conn": conn, "name": "Alice", "status": "idle"},
        "p2": {"conn": MagicMock(), "name": "Bob", "status": "away"},
    }
    server.scoreboard = {
        "Alice": {"games": 3, "wins": 2, "losses": 1, "disconnects": 0},
        "Bob": {"games": 3, "wins": 1, "losses": 2, "disconnects": 1},
    }

    server._handle_scoreboard(conn)

    payload = conn.send.call_args[0][0]
    message = Message.parse(payload.strip())
    assert message.command == Response.SCOREBOARD
    assert "Alice:2:1:3:idle" in message.args
    assert "Bob:1:2:3:away" in message.args
