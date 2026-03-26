import socket
import threading
import time
import logging

from shatranj.domain.network.protocol import Message, Command, Response

logger = logging.getLogger(__name__)

class GameClient:
    def __init__(self, server_ip: str, server_port: int, on_message):
        self.server_ip = server_ip
        self.server_port = server_port
        self.on_message = on_message
        self.socket = None
        self.connected = False
        self.thread = None

    def connect(self, player_name: str) -> bool:
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.server_ip, self.server_port))
            self.connected = True

            self.thread = threading.Thread(target=self._receive_loop, daemon=True)
            self.thread.start()
            
            return self.send(Message.build(Command.CONN, player_name))
        except Exception as e:
            logger.error(f"Erreur de connexion : {e}")
            return False

    def send(self, message: str) -> bool:
        if not self.connected or not self.socket: return False
        try:
            self.socket.sendall(message.encode('utf-8'))
            return True
        except:
            self.connected = False
            return False

    # Nouvelles commandes réseau
    def ping(self):
        """Envoie un test de connexion."""
        return self.send(Message.build(Command.PING, str(time.time())))

    def get_players(self):
        """Demande la liste des joueurs connectés."""
        return self.send(Message.build(Command.PLAYERS))

    def invite_player(self, player_id: str):
        """Invite un joueur via son ID."""
        return self.send(Message.build(Command.NEW, player_id))

    def accept_invite(self):
        """Accepte l'invitation reçue."""
        return self.send(Message.build(Command.ACCEPT))

    def decline_invite(self):
        """Refuse l'invitation reçue."""
        return self.send(Message.build(Command.DECLINE))

    def play_move(self, move: str):
        return self.send(Message.build(Command.MOVE, move.strip().lower()))

    def disconnect(self):
        if self.connected:
            self.send(Message.build(Command.QUIT))
        self.connected = False
        if self.socket: self.socket.close()

    def _receive_loop(self):
        buffer = ""
        while self.connected:
            try:
                self.socket.settimeout(1)
                data = self.socket.recv(1024)
                if not data: break
                
                buffer += data.decode('utf-8')
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    if line.strip():
                        msg = Message.parse(line)
                        self.on_message(msg)
            except socket.timeout:
                pass
            except:
                break
        self.connected = False