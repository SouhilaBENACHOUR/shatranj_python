"""
Tests for the network layer: GameServer, GameClient,
DiscoveryClient, DiscoveryServer, PlayerConnection, protocol.
"""
import time
from unittest.mock import MagicMock, patch


from shatranj.domain.network.protocol import (
    Command,
    Message,
    Response,
    GAME_PORT_DEFAULT,
    DISCOVERY_PORT,
    SERVER_TIMEOUT,
    BROADCAST_INTERVAL,
)
from shatranj.domain.network.game_server import GameServer, GameSession
from shatranj.domain.network.game_client import GameClient
from shatranj.domain.network.discovery_client import (
    DiscoveryClient,
    ServerInfo,
)
from shatranj.domain.network.discovery_server import DiscoveryServer
from shatranj.domain.network.player_connection import PlayerConnection
from shatranj.utils.constants import WHITE, BLACK


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_conn(player_id="p1", name="Player"):
    conn = MagicMock(spec=PlayerConnection)
    conn.player_id = player_id
    conn.running = True
    conn.send.return_value = True
    return conn


def _make_server():
    return GameServer("TestServer")


# ---------------------------------------------------------------------------
# protocol.py
# ---------------------------------------------------------------------------

class TestMessageParse:
    def test_simple_command(self):
        msg = Message.parse("CONN|player1")
        assert msg.command == "CONN"
        assert msg.args == ["player1"]

    def test_no_args(self):
        msg = Message.parse("PING")
        assert msg.command == "PING"
        assert msg.args == []

    def test_multiple_args(self):
        msg = Message.parse("PLAYERS_LIST|id1:name1:idle|id2:name2:ingame")
        assert msg.command == "PLAYERS_LIST"
        assert len(msg.args) == 2

    def test_strips_whitespace(self):
        msg = Message.parse("  PING  ")
        assert msg.command == "PING"

    def test_raw_stored(self):
        raw = "CONN|player1"
        msg = Message.parse(raw)
        assert msg.raw == raw


class TestMessageBuild:
    def test_no_args(self):
        assert Message.build("PING") == "PING\n"

    def test_with_args(self):
        assert Message.build("CONN", "player1") == "CONN|player1\n"

    def test_multiple_args(self):
        result = Message.build("GAME_START", "white=You", "black=Opp")
        assert result == "GAME_START|white=You|black=Opp\n"


class TestMessageSerialize:
    def test_no_args(self):
        msg = Message(command="PING", args=[], raw="PING")
        assert msg.serialize() == "PING\n"

    def test_with_args(self):
        msg = Message(command="CONN", args=["p1"], raw="CONN|p1")
        assert msg.serialize() == "CONN|p1\n"


class TestProtocolConstants:
    def test_game_port(self):
        assert GAME_PORT_DEFAULT == 12345

    def test_discovery_port(self):
        assert DISCOVERY_PORT == 12346

    def test_server_timeout_positive(self):
        assert SERVER_TIMEOUT > 0

    def test_broadcast_interval_positive(self):
        assert BROADCAST_INTERVAL > 0

    def test_command_values(self):
        assert Command.CONN == "CONN"
        assert Command.MOVE == "MOVE"
        assert Command.PING == "PING"
        assert Command.QUIT == "QUIT"
        assert Command.PLAYERS == "PLAYERS"
        assert Command.NEW == "NEW"
        assert Command.ACCEPT == "ACCEPT"
        assert Command.DECLINE == "DECLINE"

    def test_response_values(self):
        assert Response.OK == "OK"
        assert Response.CONN_OK == "CONN_OK"
        assert Response.PONG == "PONG"
        assert Response.GAME_START == "GAME_START"
        assert Response.PLAYERS_LIST == "PLAYERS_LIST"
        assert Response.INVITE_RECV == "INVITE_RECV"
        assert Response.INVITE_SENT == "INVITE_SENT"
        assert Response.ERROR == "ERROR"


# ---------------------------------------------------------------------------
# GameSession
# ---------------------------------------------------------------------------

class TestGameSession:
    def _make_session(self):
        white = _make_conn("w", "White")
        black = _make_conn("b", "Black")
        return GameSession("s1", white, black), white, black

    def test_get_opponent_white(self):
        session, white, black = self._make_session()
        assert session.get_opponent(white) is black

    def test_get_opponent_black(self):
        session, white, black = self._make_session()
        assert session.get_opponent(black) is white

    def test_get_opponent_unknown(self):
        session, white, black = self._make_session()
        assert session.get_opponent(MagicMock()) is None

    def test_get_player_color_white(self):
        session, white, black = self._make_session()
        assert session.get_player_color(white) == WHITE

    def test_get_player_color_black(self):
        session, white, black = self._make_session()
        assert session.get_player_color(black) == BLACK

    def test_get_player_color_unknown(self):
        session, white, black = self._make_session()
        assert session.get_player_color(MagicMock()) is None

    def test_initial_color_is_white(self):
        session, _, _ = self._make_session()
        assert session.current_color == WHITE


# ---------------------------------------------------------------------------
# GameServer — handle methods
# ---------------------------------------------------------------------------

class TestGameServerHandleAuth:
    def test_auth_stores_player(self):
        server = _make_server()
        conn = _make_conn()
        msg = Message.parse("CONN|Alice")
        server._handle_auth(conn, msg)
        assert conn.player_id in server.players
        assert server.players[conn.player_id]["name"] == "Alice"

    def test_auth_sends_conn_ok(self):
        server = _make_server()
        conn = _make_conn()
        msg = Message.parse("CONN|Alice")
        server._handle_auth(conn, msg)
        conn.send.assert_called_once()
        sent = conn.send.call_args[0][0]
        assert Response.CONN_OK in sent

    def test_auth_default_name(self):
        server = _make_server()
        conn = _make_conn()
        msg = Message.parse("CONN")
        server._handle_auth(conn, msg)
        pid = conn.player_id
        assert server.players[pid]["name"] in ("Joueur", "Player", "")


class TestGameServerHandlePing:
    def test_ping_sends_pong(self):
        server = _make_server()
        conn = _make_conn()
        msg = Message.parse(f"PING|{time.time()}")
        server._handle_ping(conn, msg)
        sent = conn.send.call_args[0][0]
        assert Response.PONG in sent

    def test_ping_no_args(self):
        server = _make_server()
        conn = _make_conn()
        msg = Message.parse("PING")
        server._handle_ping(conn, msg)
        conn.send.assert_called_once()
        sent = conn.send.call_args[0][0]
        assert Response.PONG in sent


class TestGameServerHandlePlayers:
    def test_players_sends_list(self):
        server = _make_server()
        conn = _make_conn("p1")
        conn2 = _make_conn("p2")
        server.players = {
            "p1": {"conn": conn, "name": "Alice", "status": "idle"},
            "p2": {"conn": conn2, "name": "Bob", "status": "idle"},
        }
        server._handle_players(conn)
        sent = conn.send.call_args[0][0]
        assert Response.PLAYERS_LIST in sent

    def test_players_empty(self):
        server = _make_server()
        conn = _make_conn()
        server.players = {}
        server._handle_players(conn)
        conn.send.assert_called_once()


class TestGameServerHandleInvite:
    def _setup(self):
        server = _make_server()
        sender = _make_conn("sender")
        target = _make_conn("target")
        server.players = {
            "sender": {
                "conn": sender, "name": "Alice", "status": "idle"
            },
            "target": {
                "conn": target, "name": "Bob", "status": "idle"
            },
        }
        return server, sender, target

    def test_invite_sends_invite_recv_to_target(self):
        server, sender, target = self._setup()
        msg = Message.parse("NEW|target")
        server._handle_invite(sender, msg)
        target.send.assert_called_once()
        sent = target.send.call_args[0][0]
        assert Response.INVITE_RECV in sent

    def test_invite_sends_invite_sent_to_sender(self):
        server, sender, target = self._setup()
        msg = Message.parse("NEW|target")
        server._handle_invite(sender, msg)
        sender.send.assert_called_once()
        sent = sender.send.call_args[0][0]
        assert Response.INVITE_SENT in sent

    def test_invite_self_returns_error(self):
        server, sender, target = self._setup()
        msg = Message.parse("NEW|sender")
        server._handle_invite(sender, msg)
        sent = sender.send.call_args[0][0]
        assert Response.ERROR in sent

    def test_invite_unknown_player_returns_error(self):
        server, sender, target = self._setup()
        msg = Message.parse("NEW|nobody")
        server._handle_invite(sender, msg)
        sent = sender.send.call_args[0][0]
        assert Response.ERROR in sent

    def test_invite_busy_player_returns_error(self):
        server, sender, target = self._setup()
        server.players["target"]["status"] = "ingame"
        msg = Message.parse("NEW|target")
        server._handle_invite(sender, msg)
        sent = sender.send.call_args[0][0]
        assert Response.ERROR in sent


class TestGameServerHandleDecline:
    def test_decline_resets_status(self):
        server = _make_server()
        sender = _make_conn("sender")
        target = _make_conn("target")
        server.players = {
            "sender": {
                "conn": sender, "name": "A", "status": "waitgame"
            },
            "target": {
                "conn": target, "name": "B", "status": "waitgame"
            },
        }
        server.invitations["sender"] = {"to": "target", "time": time.time()}
        server._handle_decline(target)
        assert server.players["sender"]["status"] == "idle"
        assert server.players["target"]["status"] == "idle"
        sender.send.assert_called_once()
        sent = sender.send.call_args[0][0]
        assert Response.INVITE_DECLINED in sent


class TestGameServerHandleQuit:
    def test_quit_removes_player(self):
        server = _make_server()
        conn = _make_conn("p1")
        server.players = {
            "p1": {"conn": conn, "name": "A", "status": "idle"}
        }
        server._handle_quit(conn)
        assert "p1" not in server.players

    def test_quit_with_active_session_notifies_opponent(self):
        server = _make_server()
        white = _make_conn("white-id")
        black = _make_conn("black-id")
        server.players = {
            "white-id": {
                "conn": white, "name": "W", "status": "ingame"
            },
            "black-id": {
                "conn": black, "name": "B", "status": "ingame"
            },
        }
        server.active_sessions["s1"] = GameSession("s1", white, black)
        server._handle_quit(white)
        assert "s1" not in server.active_sessions
        black.send.assert_called()


class TestGameServerHandleMove:
    def _setup_game(self):
        server = _make_server()
        white = _make_conn("white-id")
        black = _make_conn("black-id")
        server.players = {
            "white-id": {
                "conn": white, "name": "W", "status": "ingame"
            },
            "black-id": {
                "conn": black, "name": "B", "status": "ingame"
            },
        }
        session = GameSession("s1", white, black)
        server.active_sessions["s1"] = session
        return server, white, black, session

    def test_move_no_session_sends_error(self):
        server = _make_server()
        conn = _make_conn("p1")
        server.players = {
            "p1": {"conn": conn, "name": "A", "status": "idle"}
        }
        msg = Message.parse("MOVE|e2-e4")
        server._handle_move(conn, msg)
        conn.send.assert_called_once()
        sent = conn.send.call_args[0][0]
        assert Response.ERROR in sent

    def test_move_wrong_turn_sends_invalid(self):
        server, white, black, session = self._setup_game()
        msg = Message.parse("MOVE|e7-e5")
        server._handle_move(black, msg)
        sent = black.send.call_args[0][0]
        assert Response.INVALID in sent

    def test_move_valid_relays_to_opponent(self):
        server, white, black, session = self._setup_game()
        msg = Message.parse("MOVE|e2-e4")
        server._handle_move(white, msg)
        black.send.assert_called_once()
        sent = black.send.call_args[0][0]
        assert "e2-e4" in sent

    def test_move_flips_turn(self):
        server, white, black, session = self._setup_game()
        msg = Message.parse("MOVE|e2-e4")
        server._handle_move(white, msg)
        assert session.current_color == BLACK


# ---------------------------------------------------------------------------
# GameClient
# ---------------------------------------------------------------------------

class TestGameClientInit:
    def test_parse_address_with_port(self):
        client = GameClient("127.0.0.1:9999", callback=MagicMock())
        assert client.server_ip == "127.0.0.1"
        assert client.server_port == 9999

    def test_parse_address_without_port(self):
        client = GameClient("127.0.0.1", callback=MagicMock())
        assert client.server_ip == "127.0.0.1"
        assert client.server_port == 12345

    def test_not_connected_initially(self):
        client = GameClient("127.0.0.1", callback=MagicMock())
        assert client.is_connected() is False


class TestGameClientSend:
    def _make_client(self):
        client = GameClient("127.0.0.1", callback=MagicMock())
        client.connected = True
        client.socket = MagicMock()
        return client

    def test_send_not_connected_returns_false(self):
        client = GameClient("127.0.0.1", callback=MagicMock())
        assert client.send("PING\n") is False

    def test_send_appends_newline(self):
        client = self._make_client()
        client.send("PING")
        sent = client.socket.sendall.call_args[0][0]
        assert sent.endswith(b"\n")

    def test_send_socket_error_sets_disconnected(self):
        client = self._make_client()
        client.socket.sendall.side_effect = OSError("broken pipe")
        result = client.send("PING\n")
        assert result is False
        assert client.connected is False


class TestGameClientCommands:
    def _make_client(self):
        client = GameClient("127.0.0.1", callback=MagicMock())
        client.connected = True
        client.socket = MagicMock()
        return client

    def test_ping_sends_ping_command(self):
        client = self._make_client()
        client.ping()
        sent = client.socket.sendall.call_args[0][0].decode()
        assert Command.PING in sent

    def test_get_players_sends_players_command(self):
        client = self._make_client()
        client.get_players()
        sent = client.socket.sendall.call_args[0][0].decode()
        assert Command.PLAYERS in sent

    def test_invite_player_sends_new_command(self):
        client = self._make_client()
        client.invite_player("target-id")
        sent = client.socket.sendall.call_args[0][0].decode()
        assert Command.NEW in sent
        assert "target-id" in sent

    def test_accept_invite_sends_accept(self):
        client = self._make_client()
        client.accept_invite()
        sent = client.socket.sendall.call_args[0][0].decode()
        assert Command.ACCEPT in sent

    def test_decline_invite_sends_decline(self):
        client = self._make_client()
        client.decline_invite()
        sent = client.socket.sendall.call_args[0][0].decode()
        assert Command.DECLINE in sent

    def test_play_move_sends_move_command(self):
        client = self._make_client()
        client.play_move("E2-E4")
        sent = client.socket.sendall.call_args[0][0].decode()
        assert Command.MOVE in sent
        assert "e2-e4" in sent

    def test_disconnect_sends_quit(self):
        client = self._make_client()

        mock_socket = MagicMock()
        client.socket = mock_socket

        client.disconnect()

        mock_socket.sendall.assert_called_once()
        sent = mock_socket.sendall.call_args[0][0].decode()
        assert "QUIT" in sent

# ---------------------------------------------------------------------------
# DiscoveryClient — ServerInfo and pure logic
# ---------------------------------------------------------------------------


class TestServerInfo:
    def test_not_stale_when_fresh(self):
        info = ServerInfo("S", "127.0.0.1", 12345, "1.0")
        assert info.is_stale() is False

    def test_stale_after_timeout(self):
        info = ServerInfo("S", "127.0.0.1", 12345, "1.0")
        info.last_seen = time.time() - SERVER_TIMEOUT - 1
        assert info.is_stale() is True

    def test_update_seen_resets_timestamp(self):
        info = ServerInfo("S", "127.0.0.1", 12345, "1.0")
        info.last_seen = time.time() - SERVER_TIMEOUT - 1
        info.update_seen()
        assert info.is_stale() is False

    def test_repr(self):
        info = ServerInfo("MyServer", "10.0.0.1", 12345, "2.0")
        r = repr(info)
        assert "MyServer" in r
        assert "10.0.0.1" in r


class TestDiscoveryClientLogic:
    def test_get_servers_empty(self):
        client = DiscoveryClient()
        assert client.get_servers() == []

    def test_process_announcement_adds_server(self):
        client = DiscoveryClient()
        msg = "SERVER_ANNOUNCE|TestServer|12345|1.0"
        client._process_announcement(msg, "192.168.1.1")
        servers = client.get_servers()
        assert len(servers) == 1
        assert servers[0].name == "TestServer"
        assert servers[0].ip == "192.168.1.1"
        assert servers[0].port == 12345

    def test_process_announcement_updates_existing(self):
        client = DiscoveryClient()
        msg = "SERVER_ANNOUNCE|TestServer|12345|1.0"
        client._process_announcement(msg, "192.168.1.1")
        old_time = client.servers[("192.168.1.1", 12345)].last_seen
        time.sleep(0.01)
        client._process_announcement(msg, "192.168.1.1")
        new_time = client.servers[("192.168.1.1", 12345)].last_seen
        assert new_time >= old_time

    def test_process_announcement_invalid_format(self):
        client = DiscoveryClient()
        client._process_announcement("INVALID", "192.168.1.1")
        assert client.get_servers() == []

    def test_get_servers_removes_stale(self):
        client = DiscoveryClient()
        msg = "SERVER_ANNOUNCE|OldServer|12345|1.0"
        client._process_announcement(msg, "192.168.1.2")
        client.servers[("192.168.1.2", 12345)].last_seen = (
            time.time() - SERVER_TIMEOUT - 1
        )
        assert client.get_servers() == []

    def test_start_stop(self):
        client = DiscoveryClient()
        client.start()
        assert client.running is True
        client.stop()
        assert client.running is False

    def test_start_twice_is_safe(self):
        client = DiscoveryClient()
        client.start()
        client.start()  # Should not raise
        client.stop()


# ---------------------------------------------------------------------------
# DiscoveryServer — pure logic
# ---------------------------------------------------------------------------

class TestDiscoveryServer:
    def test_init(self):
        server = DiscoveryServer("MyServer", 12345, "1.0")
        assert server.server_name == "MyServer"
        assert server.game_port == 12345
        assert server.version == "1.0"
        assert server.running is False

    def test_start_sets_running(self):
        server = DiscoveryServer("S", 12345)
        with patch.object(server, "_broadcast_loop"):
            server.start()
            assert server.running is True
            server.stop()

    def test_stop_sets_not_running(self):
        server = DiscoveryServer("S", 12345)
        server.running = True
        server.stop()
        assert server.running is False

    def test_start_twice_is_safe(self):
        server = DiscoveryServer("S", 12345)
        with patch.object(server, "_broadcast_loop"):
            server.start()
            server.start()  # Second call should be ignored
            server.stop()


# ---------------------------------------------------------------------------
# PlayerConnection — pure logic
# ---------------------------------------------------------------------------

class TestPlayerConnection:
    def _make_conn(self):
        sock = MagicMock()
        sock.setsockopt = MagicMock()
        addr = ("127.0.0.1", 5000)
        on_message = MagicMock()
        return PlayerConnection(sock, addr, on_message)

    def test_initial_state(self):
        conn = self._make_conn()
        assert conn.running is False
        assert conn.player_id is None

    def test_send_not_running_returns_false(self):
        conn = self._make_conn()
        conn.running = False
        result = conn.send("PING\n")
        assert result is False

    def test_send_running_sends_data(self):
        conn = self._make_conn()
        conn.running = True
        result = conn.send("PING\n")
        assert result is True
        conn.socket.sendall.assert_called_once()

    def test_send_appends_newline(self):
        conn = self._make_conn()
        conn.running = True
        conn.send("PING")
        sent = conn.socket.sendall.call_args[0][0]
        assert sent.endswith(b"\n")

    def test_send_socket_error_returns_false(self):
        conn = self._make_conn()
        conn.running = True
        conn.socket.sendall.side_effect = OSError("broken")
        result = conn.send("PING\n")
        assert result is False
        assert conn.running is False

    def test_stop_closes_socket(self):
        conn = self._make_conn()
        conn.running = True
        conn.stop()
        conn.socket.close.assert_called()

    def test_start_sets_running(self):
        conn = self._make_conn()
        conn.socket.recv.return_value = b""
        conn.start()
        time.sleep(0.05)
        assert conn.thread is not None
