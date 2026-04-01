import socket
import threading
import time
import logging

from shatranj.domain.network.protocol import Message, Command, Response

logger = logging.getLogger(__name__)

class GameClient:
    # Fix: Ensure the arguments match what the CLI sends
    def __init__(self, address: str, callback):
        """
        address: format "localhost:12345" or "127.0.0.1"
        callback: the _on_message function from CLI
        """
        # F38: Parse IP and Port
        if ":" in address:
            self.server_ip, port_str = address.split(":")
            self.server_port = int(port_str)
        else:
            self.server_ip = address
            self.server_port = 12345  # Default port (F38)

        self.on_message = callback
        self.socket = None
        self.connected = False
        self.thread = None

    def is_connected(self) -> bool:
        """Check if the TCP connection is alive."""
        return self.connected

    # Rename connect to match your CLI's usage if necessary, 
    # but usually, we call this inside the CLI
    def start_connection(self, player_name: str = "Player") -> bool:
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.server_ip, self.server_port))
            self.connected = True

            # F39: Start a thread to listen for server messages while user types
            self.thread = threading.Thread(target=self._receive_loop, daemon=True)
            self.thread.start()
            
            # F38: Send initial connection/auth message
            return self.send(Message.build(Command.CONN, player_name))
        except Exception as e:
            logger.error(f"Connection error: {e}")
            return False

    def send(self, message: str) -> bool:
        """F38: Send ASCII message followed by newline."""
        if not self.connected or not self.socket: return False
        try:
            # Ensure message ends with \n as per specs
            if not message.endswith("\n"):
                message += "\n"
            self.socket.sendall(message.encode('utf-8'))
            return True
        except:
            self.connected = False
            return False

    # ... (Keep your other methods like ping(), get_players(), etc.)

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