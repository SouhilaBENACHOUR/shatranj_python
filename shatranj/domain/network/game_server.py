import socket
import threading
import uuid
import time
from typing import Optional, Dict
import logging

# Tes vraies classes pour le jeu !
from shatranj.domain.core.board import Board
from shatranj.domain.rules.rules_engine import RulesEngine
from shatranj.domain.core.move import Move
from shatranj.domain.network.protocol import Command, Response, Message, GAME_PORT_DEFAULT
from shatranj.domain.network.player_connection import PlayerConnection
from shatranj.utils.constants import WHITE, BLACK

logger = logging.getLogger(__name__)

class GameSession:
    def __init__(self, session_id: str, white: PlayerConnection, black: PlayerConnection):
        self.session_id = session_id
        self.white = white
        self.black = black
        self.board = Board()
        self.engine = RulesEngine()
        self.current_color = WHITE

    def get_opponent(self, player: PlayerConnection) -> Optional[PlayerConnection]:
        if player == self.white: return self.black
        if player == self.black: return self.white
        return None

    def get_player_color(self, player: PlayerConnection) -> Optional[str]:
        if player == self.white: return WHITE
        if player == self.black: return BLACK
        return None

class GameServer:
    def __init__(self, name: str, port: int = GAME_PORT_DEFAULT):
        self.name = name
        self.port = port
        self.running = False
        self.server_socket = None
        self.players: Dict[str, dict] = {}
        self.active_sessions: Dict[str, GameSession] = {}
        self.invitations: Dict[str, dict] = {}
        self._lock = threading.Lock()

    def start(self):
        self.running = True
        threading.Thread(target=self._server_loop, daemon=True).start()
        logger.info(f"Serveur démarré sur le port {self.port}")

    def stop(self):
        self.running = False
        if self.server_socket: self.server_socket.close()

    def _server_loop(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(("0.0.0.0", self.port))
        self.server_socket.listen(5)
        
        while self.running:
            try:
                self.server_socket.settimeout(1)
                client_socket, addr = self.server_socket.accept()
                conn = PlayerConnection(client_socket, addr, self._on_player_message)
                conn.start()
            except socket.timeout:
                pass

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
            elif message.command == Command.MOVE:
                self._handle_move(connection, message)
            elif message.command == Command.QUIT:
                self._handle_quit(connection)

    def _handle_auth(self, connection: PlayerConnection, message: Message):
        player_name = message.args[0] if message.args else "Joueur"
        player_id = str(uuid.uuid4())[:8]
        connection.player_id = player_id
        
        self.players[player_id] = {
            "conn": connection,
            "name": player_name,
            "status": "idle"
        }
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
        if not message.args: return
        target_id = message.args[0]
        sender_id = connection.player_id
        
        if target_id not in self.players or self.players[target_id]["status"] != "idle":
            connection.send(Message.build(Response.ERROR, "Joueur non disponible"))
            return
            
        self.players[sender_id]["status"] = "waitgame"
        self.players[target_id]["status"] = "waitgame"
        self.invitations[sender_id] = {"to": target_id, "time": time.time()}
        
        target_conn = self.players[target_id]["conn"]
        target_conn.send(Message.build(Response.INVITE_RECV, f"FROM={self.players[sender_id]['name']}", "EXPIRES=300s"))
        connection.send(Message.build(Response.INVITE_SENT, f"PLAYER={self.players[target_id]['name']}", "TIMEOUT=300s"))

    def _handle_accept(self, connection: PlayerConnection):
        target_id = connection.player_id
        sender_id = None
        
        for sid, inv in self.invitations.items():
            if inv["to"] == target_id:
                sender_id = sid
                break
                
        if sender_id:
            del self.invitations[sender_id]
            self.players[sender_id]["status"] = "ingame"
            self.players[target_id]["status"] = "ingame"
            
            session_id = str(uuid.uuid4())[:8]
            white_conn = self.players[sender_id]["conn"]
            black_conn = connection
            session = GameSession(session_id, white_conn, black_conn)
            self.active_sessions[session_id] = session
            
            fen = session.board.to_fen()
            white_conn.send(Message.build(Response.GAME_START, "white=You", "black=Opponent", f"board={fen}"))
            black_conn.send(Message.build(Response.GAME_START, "white=Opponent", "black=You", f"board={fen}"))

    def _handle_decline(self, connection: PlayerConnection):
        target_id = connection.player_id
        for sid, inv in list(self.invitations.items()):
            if inv["to"] == target_id:
                self.players[sid]["status"] = "idle"
                self.players[target_id]["status"] = "idle"
                self.players[sid]["conn"].send(Message.build(Response.INVITE_DECLINED))
                del self.invitations[sid]
                break

    def _handle_move(self, connection: PlayerConnection, message: Message):
        if not message.args: return
        move_str = message.args[0]
        
        # 1. Trouver la partie
        session = None
        for sid, ses in self.active_sessions.items():
            if ses.white == connection or ses.black == connection:
                session = ses
                break
                
        if not session:
            connection.send(Message.build(Response.ERROR, "Aucune partie en cours"))
            return

        # 2. Vérifier le tour
        player_color = session.get_player_color(connection)
        if player_color != session.current_color:
            connection.send(Message.build(Response.INVALID, "Ce n'est pas ton tour !"))
            return

        # 3. Validation avec TES classes
        try:
            from shatranj.domain.core.board import Board
            from shatranj.domain.core.move import Move
            from shatranj.utils.constants import WHITE, BLACK

            parts = move_str.split("-")
            if len(parts) != 2:
                connection.send(Message.build(Response.INVALID, "Format invalide"))
                return

            from_sq = Board.algebraic_to_square(parts[0])
            to_sq = Board.algebraic_to_square(parts[1])

            piece = session.board.get_piece_at(from_sq)
            if not piece:
                connection.send(Message.build(Response.INVALID, "Pas de pièce ici"))
                return

            piece_type, piece_color = piece
            if piece_color != player_color:
                connection.send(Message.build(Response.INVALID, "Ce n'est pas ta pièce !"))
                return
            
            captured = session.board.get_piece_at(to_sq)
            captured_piece = captured[0] if captured else None
            
            # Création du Move avec la syntaxe de TA classe Move
            move = Move(
                from_square=from_sq, 
                to_square=to_sq, 
                piece_type=piece_type, 
                color=player_color, 
                captured_piece=captured_piece
            )

            # Vérifier les règles avec ton moteur
            if not session.engine.is_valid_move(session.board, move):
                connection.send(Message.build(Response.INVALID, "Coup illégal !"))
                return

            # 4. Appliquer le coup avec TA fonction
            session.board.apply_move(move)

            # 5. Changer le tour
            session.current_color = BLACK if player_color == WHITE else WHITE

            # 6. Récupérer le nouveau plateau et l'envoyer
            nouveau_plateau = session.board.to_fen()
            
            # On envoie OK et le nouveau plateau au joueur qui a joué
            connection.send(Message.build(Response.OK, f"board={nouveau_plateau}"))
            
            # On envoie le coup ET le nouveau plateau à l'adversaire
            opponent = session.get_opponent(connection)
            if opponent:
                opponent.send(Message.build(Response.OPPONENT_MOVE, move_str, f"board={nouveau_plateau}"))

        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Erreur coup: {e}")
            connection.send(Message.build(Response.INVALID, f"Erreur technique: {e}"))

    def _handle_quit(self, connection: PlayerConnection):
        pid = connection.player_id
        if pid in self.players:
            del self.players[pid]
        connection.stop()