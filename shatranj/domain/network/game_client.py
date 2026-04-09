import logging
import socket
import threading
import time

from shatranj.domain.network.protocol import Command, Message

logger = logging.getLogger(__name__)


class GameClient:
    def __init__(self, address: str, callback):
        """
        address: format "localhost:12345" or "127.0.0.1"
        callback: the _on_message function from CLI
        """
        if ":" in address:
            self.server_ip, port_str = address.split(":")
            self.server_port = int(port_str)
        else:
            self.server_ip = address
            self.server_port = 12345

        self.on_message = callback
        self.socket: socket.socket | None = None
        self.connected = False
        self.thread: threading.Thread | None = None

    def is_connected(self) -> bool:
        """Check if the TCP connection is alive."""
        return self.connected

    def start_connection(self, player_name: str = "Player") -> bool:
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.server_ip, self.server_port))
            self.connected = True

            self.thread = threading.Thread(
                target=self._receive_loop, daemon=True
            )
            self.thread.start()
            return self.send(Message.build(Command.CONN, player_name))
        except OSError as err:
            self.connected = False
            self.socket = None
            logger.error("Connection error: %s", err)
            return False

    def send(self, message: str) -> bool:
        """Send one protocol message terminated by a newline."""
        if not self.connected or not self.socket:
            return False

        try:
            if not message.endswith("\n"):
                message += "\n"
            self.socket.sendall(message.encode("utf-8"))
            return True
        except OSError:
            self.connected = False
            return False

    def ping(self):
        """Send a ping request to the server."""
        return self.send(Message.build(Command.PING, str(time.time())))

    def get_players(self):
        """Request the list of connected players."""
        return self.send(Message.build(Command.PLAYERS))

    def invite_player(self, player_id: str):
        """Invite a player by id."""
        return self.send(Message.build(Command.NEW, player_id))

    def accept_invite(self):
        """Accept the current invitation."""
        return self.send(Message.build(Command.ACCEPT))

    def decline_invite(self):
        """Decline the current invitation."""
        return self.send(Message.build(Command.DECLINE))

    def cancel_invite(self):
        """Cancel the invitation currently waiting for a reply."""
        return self.send(Message.build(Command.CANCEL))

    def set_away(self):
        """Mark the player as temporarily unavailable."""
        return self.send(Message.build(Command.AWAY))

    def set_back(self):
        """Mark the player as available again."""
        return self.send(Message.build(Command.BACK))

    def get_scoreboard(self):
        """Request the current server scoreboard."""
        return self.send(Message.build(Command.SCOREBOARD))

    def play_move(self, move: str):
        """Send a move to the server."""
        return self.send(Message.build(Command.MOVE, move.strip().lower()))

    def disconnect(self):
        """Close the TCP connection cleanly."""
        if self.connected:
            self.send(Message.build(Command.QUIT))
        self.connected = False
        if self.socket:
            try:
                self.socket.close()
            except OSError:
                pass
            self.socket = None

    def _receive_loop(self):
        """Receive newline-delimited protocol messages."""
        sock = self.socket
        if sock is None:
            self.connected = False
            return

        buffer = ""
        while self.connected:
            try:
                sock.settimeout(1)
                data = sock.recv(1024)
                if not data:
                    break

                buffer += data.decode("utf-8")
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    if line.strip():
                        self.on_message(Message.parse(line))
            except socket.timeout:
                continue
            except (OSError, UnicodeDecodeError):
                break

        self.connected = False
