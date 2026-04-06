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
        
        # ---> FIX: Use scissors to cut the string into parts! <---
        raw_target = message.args[0]
        parts = raw_target.split() # This splits the text wherever there is a space
        
        target_id = parts[0] # The first part is the real ID
        sender_id = connection.player_id
        
        blitz_setting = ""
        # The second part (if it exists) is our secret blitz note!
        if len(parts) > 1 and parts[1].startswith("blitz="):
            blitz_setting = parts[1]

        if target_id == sender_id:
            connection.send(Message.build(Response.ERROR, "Vous ne pouvez pas vous inviter vous-même !"))
            return
            
        if target_id not in self.players or self.players[target_id]["status"] != "idle":
            connection.send(Message.build(Response.ERROR, "Joueur non disponible"))
            return
            
        self.players[sender_id]["status"] = "waitgame"
        self.players[target_id]["status"] = "waitgame"
        
        # Save the blitz setting in the server's memory
        self.invitations[sender_id] = {"to": target_id, "time": time.time(), "blitz": blitz_setting}
        
        target_conn = self.players[target_id]["conn"]
        
        # Tell the receiver if it is a blitz game!
        invite_msg = f"FROM={self.players[sender_id]['name']}"
        if blitz_setting:
            invite_msg += f" ({blitz_setting})"
            
        target_conn.send(Message.build(Response.INVITE_RECV, invite_msg, "EXPIRES=300s"))
        connection.send(Message.build(Response.INVITE_SENT, f"PLAYER={self.players[target_id]['name']}", "TIMEOUT=300s"))

    def _handle_accept(self, connection: PlayerConnection):
        target_id = connection.player_id
        sender_id = None
        blitz_setting = ""
        
        for sid, inv in self.invitations.items():
            if inv["to"] == target_id:
                sender_id = sid
                blitz_setting = inv.get("blitz", "") # ---> NEW: Get the secret note out of memory
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
            
            # ---> NEW: Send the blitz setting to BOTH players so they turn on their clocks! <---
            if blitz_setting:
                white_conn.send(Message.build(Response.GAME_START, "white=You", "black=Opponent", f"board={fen}", blitz_setting))
                black_conn.send(Message.build(Response.GAME_START, "white=Opponent", "black=You", f"board={fen}", blitz_setting))
            else:
                white_conn.send(Message.build(Response.GAME_START, "white=You", "black=Opponent", f"board={fen}"))
                black_conn.send(Message.build(Response.GAME_START, "white=Opponent", "black=You", f"board={fen}"))
    
    def _handle_quit(self, connection: PlayerConnection):
        try:
            # 1. Tell the opponent and destroy the game session
            for sid, ses in list(self.active_sessions.items()):
                if ses.white == connection or ses.black == connection:
                    opponent = ses.get_opponent(connection)
                    if opponent:
                        opponent.send(Message.build(Response.ERROR, "L'adversaire a quitté la partie !"))
                    del self.active_sessions[sid]
                    break

            # 2. Remove the player from the lobby
            pid = getattr(connection, 'player_id', None)
            if pid and pid in self.players:
                del self.players[pid]
                
            connection.running = False
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Erreur de quit: {e}")

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
            try:
                if not message.args: return
                move_str = message.args[0]
                
                # 1. Find the active game session
                session = None
                session_id = None
                for sid, ses in self.active_sessions.items():
                    if ses.white == connection or ses.black == connection:
                        session = ses
                        session_id = sid
                        break
                        
                if not session:
                    connection.send(Message.build(Response.ERROR, "Aucune partie en cours"))
                    return

                # 2. Verify it is actually this player's turn
                player_color = session.get_player_color(connection)
                if player_color != session.current_color:
                    connection.send(Message.build(Response.INVALID, "Ce n'est pas ton tour !"))
                    return

                # 3. RELAY THE MOVE AND CHECK FOR ZOMBIES! 
                opponent = session.get_opponent(connection)
                if opponent:
                    success = opponent.send(Message.build(Response.OPPONENT_MOVE, move_str))
                    
                    # THE FIX: If sending failed, the opponent pulled the plug without telling us!
                    if success is False:
                        connection.send(Message.build(Response.ERROR, "L'adversaire s'est déconnecté (Fantôme) !"))
                        del self.active_sessions[session_id]
                        return

                # 4. Flip the turn only if the opponent is actually alive
                session.current_color = BLACK if player_color == WHITE else WHITE

            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Erreur coup: {e}")
                connection.send(Message.build(Response.INVALID, f"Erreur technique: {e}"))

    def _handle_quit(self, connection: PlayerConnection):
        pid = connection.player_id
        if pid in self.players:
            del self.players[pid]
        connection.stop()