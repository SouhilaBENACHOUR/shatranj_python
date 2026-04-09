import logging
import socket
import threading
import time
import uuid
from typing import Dict, Optional

from shatranj.domain.core.board import Board
from shatranj.domain.network.player_connection import PlayerConnection
from shatranj.domain.network.protocol import (
    Command,
    GAME_PORT_DEFAULT,
    Message,
    Response,
)
from shatranj.utils.constants import BLACK, WHITE

logger = logging.getLogger(__name__)


class GameSession:
    def __init__(
        self,
        session_id: str,
        white: PlayerConnection,
        black: PlayerConnection,
    ):
        self.session_id = session_id
        self.white = white
        self.black = black
        self.board = Board()
        self.current_color = WHITE

    def get_opponent(self, player: PlayerConnection) -> Optional[PlayerConnection]:
        if player == self.white:
            return self.black
        if player == self.black:
            return self.white
        return None

    def get_player_color(self, player: PlayerConnection) -> Optional[str]:
        if player == self.white:
            return WHITE
        if player == self.black:
            return BLACK
        return None


class GameServer:
    def __init__(self, name: str, port: int = GAME_PORT_DEFAULT):
        self.name = name
        self.port = port
        self.running = False
        self.server_socket: socket.socket | None = None
        self.thread: threading.Thread | None = None
        self.players: Dict[str, dict] = {}
        self.active_sessions: Dict[str, GameSession] = {}
        self.invitations: Dict[str, dict] = {}
        self.scoreboard: Dict[str, dict[str, int]] = {}
        self._lock = threading.RLock()

    def start(self):
        if self.running:
            logger.warning("Game server already running on port %s", self.port)
            return
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(("0.0.0.0", self.port))
        self.server_socket.listen(5)
        self.running = True
        self.thread = threading.Thread(target=self._server_loop, daemon=True)
        self.thread.start()
        logger.info("Game server started on port %s", self.port)

    def stop(self):
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except OSError:
                pass
        if self.thread:
            self.thread.join(timeout=2)
        self.thread = None
        self.server_socket = None

    def _server_loop(self):
        if self.server_socket is None:
            self.running = False
            return

        while self.running:
            try:
                self.server_socket.settimeout(1)
                client_socket, addr = self.server_socket.accept()
                conn = PlayerConnection(client_socket, addr, self._on_player_message)
                conn.start()
            except socket.timeout:
                continue
            except OSError as err:
                if self.running:
                    logger.error("Server loop error: %s", err)

    def _on_player_message(self, connection: PlayerConnection, message: Message):
        with self._lock:
            if message.command == Command.CONN:
                self._handle_auth(connection, message)
            elif message.command == Command.PING:
                self._handle_ping(connection, message)
            elif message.command == Command.PLAYERS:
                self._handle_players(connection)
            elif message.command == Command.NEW:
                self._handle_invite(connection, message)
            elif message.command == Command.ACCEPT:
                self._handle_accept(connection)
            elif message.command == Command.DECLINE:
                self._handle_decline(connection)
            elif message.command == Command.CANCEL:
                self._handle_cancel(connection)
            elif message.command == Command.AWAY:
                self._handle_status_update(connection, "away")
            elif message.command == Command.BACK:
                self._handle_status_update(connection, "idle")
            elif message.command == Command.SCOREBOARD:
                self._handle_scoreboard(connection)
            elif message.command == Command.MOVE:
                self._handle_move(connection, message)
            elif message.command == Command.QUIT:
                self._handle_quit(connection)

    def _handle_auth(self, connection: PlayerConnection, message: Message):
        player_name = message.args[0] if message.args else "Player"
        player_id = str(uuid.uuid4())[:8]
        connection.player_id = player_id

        self.players[player_id] = {
            "conn": connection,
            "name": player_name,
            "status": "idle",
        }
        self.scoreboard.setdefault(
            player_name,
            {"games": 0, "wins": 0, "losses": 0, "disconnects": 0},
        )
        connection.send(Message.build(Response.CONN_OK, f"id={player_id}"))

    def _handle_ping(self, connection: PlayerConnection, message: Message):
        if message.args:
            start_time = float(message.args[0])
            delay = int((time.time() - start_time) * 1000)
            connection.send(Message.build(Response.PONG, f"TIME={delay}ms"))
        else:
            connection.send(Message.build(Response.PONG))

    def _handle_players(self, connection: PlayerConnection):
        lines = []
        for pid, data in self.players.items():
            lines.append(f"{pid}:{data['name']}:{data['status']}")
        connection.send(Message.build(Response.PLAYERS_LIST, *lines))

    def _handle_invite(self, connection: PlayerConnection, message: Message):
        if not message.args:
            return

        parts = message.args[0].split()
        if not parts:
            return

        target_id = parts[0]
        sender_id = connection.player_id
        blitz_setting = ""
        if len(parts) > 1 and parts[1].startswith("blitz="):
            blitz_setting = parts[1]

        if target_id == sender_id:
            connection.send(
                Message.build(
                    Response.ERROR,
                    "You cannot invite yourself.",
                )
            )
            return

        if target_id not in self.players or self.players[target_id]["status"] != "idle":
            connection.send(Message.build(Response.ERROR, "Player not available."))
            return

        self.players[sender_id]["status"] = "waitgame"
        self.players[target_id]["status"] = "waitgame"
        self.invitations[sender_id] = {
            "to": target_id,
            "time": time.time(),
            "blitz": blitz_setting,
        }

        target_conn = self.players[target_id]["conn"]
        invite_msg = f"FROM={self.players[sender_id]['name']}"
        if blitz_setting:
            invite_msg += f" ({blitz_setting})"

        target_conn.send(
            Message.build(Response.INVITE_RECV, invite_msg, "EXPIRES=300s")
        )
        connection.send(
            Message.build(
                Response.INVITE_SENT,
                f"PLAYER={self.players[target_id]['name']}",
                "TIMEOUT=300s",
            )
        )

    def _handle_accept(self, connection: PlayerConnection):
        target_id = connection.player_id
        sender_id = None
        blitz_setting = ""

        for sid, invitation in self.invitations.items():
            if invitation["to"] == target_id:
                sender_id = sid
                blitz_setting = invitation.get("blitz", "")
                break

        if sender_id is None:
            return

        del self.invitations[sender_id]
        self.players[sender_id]["status"] = "ingame"
        self.players[target_id]["status"] = "ingame"

        session_id = str(uuid.uuid4())[:8]
        white_conn = self.players[sender_id]["conn"]
        black_conn = connection
        session = GameSession(session_id, white_conn, black_conn)
        self.active_sessions[session_id] = session

        self._bump_games(self.players[sender_id]["name"])
        self._bump_games(self.players[target_id]["name"])

        fen = session.board.to_fen()
        base_args = ("white=You", "black=Opponent", f"board={fen}")
        opponent_args = ("white=Opponent", "black=You", f"board={fen}")

        if blitz_setting:
            white_conn.send(Message.build(Response.GAME_START, *base_args, blitz_setting))
            black_conn.send(
                Message.build(Response.GAME_START, *opponent_args, blitz_setting)
            )
            return

        white_conn.send(Message.build(Response.GAME_START, *base_args))
        black_conn.send(Message.build(Response.GAME_START, *opponent_args))

    def _handle_quit(self, connection: PlayerConnection):
        pid = getattr(connection, "player_id", None)

        for sid, session in list(self.active_sessions.items()):
            if session.white != connection and session.black != connection:
                continue

            opponent = session.get_opponent(connection)
            if opponent is not None:
                opponent.send(
                    Message.build(
                        Response.ERROR,
                        "Opponent left the game.",
                    )
                )
                opponent_id = getattr(opponent, "player_id", None)
                if opponent_id in self.players:
                    self.players[opponent_id]["status"] = "idle"
                    self._record_win(self.players[opponent_id]["name"])

                if pid in self.players:
                    self._record_loss(self.players[pid]["name"], disconnected=True)

            del self.active_sessions[sid]
            break

        if pid is not None:
            outgoing_invite = self.invitations.pop(pid, None)
            if outgoing_invite is not None:
                invited_id = outgoing_invite.get("to")
                if invited_id in self.players:
                    self.players[invited_id]["status"] = "idle"

            for sender_id, invite in list(self.invitations.items()):
                if invite.get("to") != pid:
                    continue
                self.invitations.pop(sender_id, None)
                if sender_id in self.players:
                    self.players[sender_id]["status"] = "idle"

            self.players.pop(pid, None)

        connection.stop()

    def _handle_decline(self, connection: PlayerConnection):
        target_id = connection.player_id
        for sid, invite in list(self.invitations.items()):
            if invite["to"] == target_id:
                self.players[sid]["status"] = "idle"
                self.players[target_id]["status"] = "idle"
                self.players[sid]["conn"].send(Message.build(Response.INVITE_DECLINED))
                del self.invitations[sid]
                break

    def _handle_cancel(self, connection: PlayerConnection):
        sender_id = connection.player_id
        invite = self.invitations.pop(sender_id, None)
        if invite is None:
            return

        target_id = invite.get("to")
        if sender_id in self.players:
            self.players[sender_id]["status"] = "idle"
        if target_id in self.players:
            self.players[target_id]["status"] = "idle"

    def _handle_status_update(
        self,
        connection: PlayerConnection,
        status: str,
    ) -> None:
        player_id = connection.player_id
        if player_id not in self.players:
            return
        current = self.players[player_id]["status"]
        if current == "ingame":
            return
        self.players[player_id]["status"] = status

    def _handle_scoreboard(self, connection: PlayerConnection) -> None:
        rows = [
            "{name}:{wins}:{losses}:{games}:{status}".format(**row)
            for row in self.get_scoreboard()
        ]
        connection.send(Message.build(Response.SCOREBOARD, *rows))

    def _handle_move(self, connection: PlayerConnection, message: Message):
        try:
            if not message.args:
                return
            move_str = message.args[0]

            session = None
            session_id = None
            for sid, active_session in self.active_sessions.items():
                if active_session.white == connection or active_session.black == connection:
                    session = active_session
                    session_id = sid
                    break

            if session is None:
                connection.send(Message.build(Response.ERROR, "No active game."))
                return

            player_color = session.get_player_color(connection)
            if player_color != session.current_color:
                connection.send(
                    Message.build(Response.INVALID, "It is not your turn.")
                )
                return

            opponent = session.get_opponent(connection)
            if opponent is not None:
                success = opponent.send(Message.build(Response.OPPONENT_MOVE, move_str))
                if success is False:
                    connection.send(
                        Message.build(
                            Response.ERROR,
                            "Opponent disconnected.",
                        )
                    )
                    if session_id is not None:
                        del self.active_sessions[session_id]
                    return

            session.current_color = BLACK if player_color == WHITE else WHITE

        except Exception as err:
            logger.error("Move handling error: %s", err)
            connection.send(Message.build(Response.INVALID, f"Technical error: {err}"))

    def get_status(self) -> dict[str, int | str | bool]:
        """Return a lightweight snapshot of the local server state."""
        with self._lock:
            return {
                "name": self.name,
                "port": self.port,
                "running": self.running,
                "players": len(self.players),
                "sessions": len(self.active_sessions),
                "pending_invitations": len(self.invitations),
            }

    def get_scoreboard(self) -> list[dict[str, int | str]]:
        """Return scoreboard rows ordered by score and name."""
        with self._lock:
            online_status = {
                data["name"]: data["status"] for data in self.players.values()
            }
            rows = []
            for name, stats in self.scoreboard.items():
                rows.append(
                    {
                        "name": name,
                        "wins": stats["wins"],
                        "losses": stats["losses"],
                        "games": stats["games"],
                        "status": online_status.get(name, "offline"),
                    }
                )
        rows.sort(
            key=lambda row: (-int(row["wins"]), int(row["losses"]), str(row["name"]))
        )
        return rows

    def _bump_games(self, player_name: str) -> None:
        self.scoreboard.setdefault(
            player_name,
            {"games": 0, "wins": 0, "losses": 0, "disconnects": 0},
        )
        self.scoreboard[player_name]["games"] += 1

    def _record_win(self, player_name: str) -> None:
        self.scoreboard.setdefault(
            player_name,
            {"games": 0, "wins": 0, "losses": 0, "disconnects": 0},
        )
        self.scoreboard[player_name]["wins"] += 1

    def _record_loss(
        self,
        player_name: str,
        *,
        disconnected: bool = False,
    ) -> None:
        self.scoreboard.setdefault(
            player_name,
            {"games": 0, "wins": 0, "losses": 0, "disconnects": 0},
        )
        self.scoreboard[player_name]["losses"] += 1
        if disconnected:
            self.scoreboard[player_name]["disconnects"] += 1
