"""
Game Server - TCP server managing Shatranj game logic and multi-player coordination.
"""

import socket
import threading
import uuid
from typing import Optional, Dict
import logging

from shatranj.domain.core.board import Board
from shatranj.domain.rules.rules_engine import RulesEngine
from shatranj.domain.network.protocol import (
    Command, Response, InvalidReason, Message, GAME_PORT_DEFAULT
)
from shatranj.domain.network.player_connection import PlayerConnection
from shatranj.utils.constants import WHITE, BLACK

logger = logging.getLogger(__name__)


class GameSession:
    """Represents an active game session."""

    def __init__(self, session_id: str, white: PlayerConnection, black: PlayerConnection,
                 blitz_enabled: bool = False, blitz_time_minutes: int = 30):
        self.session_id = session_id
        self.white = white
        self.black = black
        self.board = Board()
        self.engine = RulesEngine()
        self.current_color = WHITE
        self.blitz_enabled = blitz_enabled

        

    def get_opponent(self, player: PlayerConnection) -> Optional[PlayerConnection]:
        """Get the opponent of a given player."""
        if player == self.white:
            return self.black
        elif player == self.black:
            return self.white
        return None

    def get_player_color(self, player: PlayerConnection) -> Optional[str]:
        """Get the color (WHITE/BLACK) of a player."""
        # Prefer explicit color attribute if set (more robust than object identity)
        if getattr(player, "color", None):
            return player.color

        if player == self.white:
            return WHITE
        elif player == self.black:
            return BLACK
        return None


class GameServer:
    """TCP server for Shatranj multi-player games."""

    def __init__(self, name: str, port: int = GAME_PORT_DEFAULT, max_sessions: int = 10):
        """
        Initialize the game server.

        Args:
            name: Server name (for discovery)
            port: TCP port to listen on
            max_sessions: Maximum simultaneous game sessions
        """
        self.name = name
        self.port = port
        self.max_sessions = max_sessions
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.server_socket: Optional[socket.socket] = None

        # Waiting players and active sessions
        self.waiting_players: Dict[str, PlayerConnection] = {}  # player_id -> connection
        self.active_sessions: Dict[str, GameSession] = {}  # session_id -> session
        self._lock = threading.Lock()

    def start(self) -> None:
        """Start the game server in a background thread."""
        if self.running:
            logger.warning("Game server already running")
            return

        self.running = True
        self.thread = threading.Thread(target=self._server_loop, daemon=True)
        self.thread.start()
        logger.info(f"Game server '{self.name}' started on port {self.port}")

    def stop(self) -> None:
        """Stop the game server."""
        self.running = False

        with self._lock:
            for session in list(self.active_sessions.values()):
                session.white.stop()
                session.black.stop()

            for player in list(self.waiting_players.values()):
                player.stop()

        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass

        if self.thread:
            self.thread.join(timeout=2)

        logger.info("Game server stopped")

    def _server_loop(self) -> None:
        """Main loop: accept incoming connections."""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(("0.0.0.0", self.port))
            self.server_socket.listen(5)

            logger.info(f"Server listening on port {self.port}")

            while self.running:
                try:
                    self.server_socket.settimeout(2)
                    client_socket, addr = self.server_socket.accept()
                    logger.info(f"New connection from {addr}")

                    # Create connection handler
                    connection = PlayerConnection(
                        client_socket, addr,
                        on_message=self._on_player_message
                    )
                    connection.start()

                except socket.timeout:
                    pass
                except Exception as e:
                    if self.running:
                        logger.error(f"Error accepting connection: {e}")

        except Exception as e:
            logger.error(f"Server loop error: {e}")
        finally:
            if self.server_socket:
                try:
                    self.server_socket.close()
                except:
                    pass

    def _on_player_message(self, connection: PlayerConnection, message: Message) -> None:
        """Handle a message from a connected player."""
        logger.info(f"[MSG] Processing {message.command} from {connection.addr}")
        try:
            if message.command == Command.AUTH:
                logger.info(f"[MSG] Handling AUTH from {connection.addr}")
                self._handle_auth(connection, message)
            elif message.command == Command.MOVE:
                self._handle_move(connection, message)
            elif message.command == Command.QUIT:
                self._handle_quit(connection, message)
            else:
                # Unknown command
                connection.send(Message.build(Response.ERROR, f"Unknown command: {message.command}"))
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            connection.send(Message.build(Response.ERROR, str(e)))

    def _handle_auth(self, connection: PlayerConnection, message: Message) -> None:
        """Handle AUTH command - player authentication."""
        logger.info(f"[AUTH] Starting auth handler for {connection.addr}, args={message.args}")
        if not message.args:
            logger.error(f"[AUTH] No args in AUTH message from {connection.addr}")
            connection.send(Message.build(Response.AUTH_FAIL, "reason=invalid_format"))
            return

        player_name = message.args[0]
        player_id = str(uuid.uuid4())[:8]
        logger.info(f"[AUTH] AuthReq from {connection.addr}: player_name={player_name}, player_id={player_id}")

        with self._lock:
            # Check if server is full
            total_players = len(self.waiting_players) + sum(len([connection.white, connection.black]) for _ in self.active_sessions.values())
            if total_players >= self.max_sessions * 2:  # 2 players per session
                connection.send(Message.build(Response.AUTH_FAIL, "reason=server_full"))
                return

            # Determine color based on current waiting players count
            color = WHITE if len(self.waiting_players) == 0 else BLACK

            # Add to waiting players
            connection.player_id = player_id
            connection.color = color
            self.waiting_players[player_id] = connection

            # Check if we should start a game (but don't call it yet)
            should_start_game = len(self.waiting_players) >= 2

        # Start game outside the lock to avoid deadlock
        if should_start_game:
            self._start_game()

        # Confirm authentication
        connection.send(Message.build(Response.AUTH_OK, f"player_id={player_id}", f"color={color}"))
        logger.info(f"Player authenticated: {player_name} (ID: {player_id})")

    def _start_game(self) -> None:
        """Start a new game with two waiting players."""
        with self._lock:
            if len(self.waiting_players) < 2:
                return

            # Get two players
            player_ids = list(self.waiting_players.keys())[:2]
            white_connection = self.waiting_players.pop(player_ids[0])
            black_connection = self.waiting_players.pop(player_ids[1])

            # Create session
            session_id = str(uuid.uuid4())[:8]
            session = GameSession(session_id, white_connection, black_connection)
            self.active_sessions[session_id] = session

        # Notify both players (outside the lock to avoid blocking)
        board_fen = session.board.to_fen()
        white_connection.send(
            Message.build(
                Response.GAME_START,
                "white=You",
                "black=Opponent",
                "blitz=1",
                "time=30",
                f"board={board_fen}",
                "turn=WHITE",
            )
        )
        black_connection.send(
            Message.build(
                Response.GAME_START,
                "white=Opponent",
                "black=You",
                "blitz=1",
                "time=30",
                f"board={board_fen}",
                "turn=WHITE",
            )
        )

        logger.info(f"Game session started: {session_id}")

    def _handle_move(self, connection: PlayerConnection, message: Message) -> None:
        """Handle MOVE command - process a move."""
        if not message.args:
            connection.send(Message.build(Response.INVALID, "reason=invalid_format"))
            return

        move_str = message.args[0]  # e.g., "e2-e4"

        # Find the session
        session = None
        with self._lock:
            for sid, ses in self.active_sessions.items():
                if ses.white == connection or ses.black == connection:
                    session = ses
                    break

        if not session:
            connection.send(Message.build(Response.ERROR, "No active game"))
            return

        # Check if it's this player's turn
        player_color = session.get_player_color(connection)
        if player_color != session.current_color:
            connection.send(Message.build(Response.INVALID, f"reason=not_your_turn", f"turn={session.current_color}"))
            return

        # Parse and validate move
        try:
            from_sq, to_sq = self._parse_move(move_str)
            from shatranj.domain.core.move import Move

            # Get piece at from_sq
            piece = session.board.get_piece_at(from_sq)
            if not piece:
                connection.send(Message.build(Response.INVALID, f"reason=no_piece", f"turn={session.current_color}"))
                return

            piece_type, piece_color = piece
            if piece_color != player_color:
                connection.send(Message.build(Response.INVALID, f"reason=wrong_color", f"turn={session.current_color}"))
                return

            # Create and validate move
            captured = session.board.get_piece_at(to_sq)
            captured_piece = captured[0] if captured else None
            move = Move(from_sq, to_sq, piece_type, player_color, captured_piece)

            if not session.engine.is_valid_move(session.board, move):
                connection.send(Message.build(Response.INVALID, f"reason=illegal_move", f"turn={session.current_color}"))
                return

            # Apply move
            session.board.move_piece(from_sq, to_sq)

            # Determine next turn (after this move)
            next_turn = BLACK if player_color == WHITE else WHITE
            session.current_color = next_turn

            # Get updated board state
            board_fen = session.board.to_fen()

            # Notify both players
            connection.send(
                Message.build(
                    Response.OK,
                    f"board={board_fen}",
                    f"turn={next_turn}",
                )
            )
            opponent = session.get_opponent(connection)
            if opponent:
                opponent.send(
                    Message.build(
                        Response.OPPONENT_MOVE,
                        move_str,
                        f"board={board_fen}",
                        f"turn={next_turn}",
                    )
                )

        except Exception as e:
            logger.error(f"Error processing move: {e}")
            connection.send(Message.build(Response.INVALID, f"reason=invalid_format", f"turn={session.current_color}"))

    def _handle_quit(self, connection: PlayerConnection, message: Message) -> None:
        """Handle QUIT command - player disconnection."""
        with self._lock:
            # Remove from waiting players
            for player_id, conn in list(self.waiting_players.items()):
                if conn == connection:
                    del self.waiting_players[player_id]
                    break

            # Remove from active sessions
            for session_id, session in list(self.active_sessions.items()):
                if session.white == connection or session.black == connection:
                    opponent = session.get_opponent(connection)
                    if opponent:
                        opponent.send(Message.build(Response.RESIGNATION, f"loser={session.get_player_color(connection)}"))
                    del self.active_sessions[session_id]
                    logger.info(f"Game session ended: {session_id}")
                    break

        connection.stop()

    @staticmethod
    def _parse_move(move_str: str) -> tuple[int, int]:
        """Parse a move string like 'e2-e4' into (from_sq, to_sq)."""
        move_str = move_str.strip().lower()
        parts = move_str.split("-")
        if len(parts) != 2:
            raise ValueError(f"Invalid move format: {move_str}")

        from_sq = Board.algebraic_to_square(parts[0])
        to_sq = Board.algebraic_to_square(parts[1])
        return from_sq, to_sq


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    server = GameServer("LocalServer", 12345)
    server.start()
    try:
        while True:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        server.stop()
