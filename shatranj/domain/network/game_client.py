"""
Game Client - TCP client for connecting to a Shatranj game server.
"""

import socket
import threading
import time
from typing import Optional, Callable
import logging

from shatranj.domain.network.protocol import Message, Command, Response

logger = logging.getLogger(__name__)


class GameClient:
    """TCP client for connecting to and playing on a game server."""

    def __init__(self, server_ip: str, server_port: int, on_message: Callable):
        """
        Initialize the game client.

        Args:
            server_ip: IP address of the game server
            server_port: Port of the game server
            on_message: Callback function(Message) called when server sends messages
        """
        self.server_ip = server_ip
        self.server_port = server_port
        self.on_message = on_message
        self.socket: Optional[socket.socket] = None
        self.connected = False
        self.thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self.authenticated = False

    def connect(self, player_name: str) -> bool:
        """
        Connect to the server and authenticate.

        Args:
            player_name: Name to use for this player

        Returns:
            True if connected and authenticated, False otherwise
        """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)  # Disable Nagle
            self.socket.connect((self.server_ip, self.server_port))
            self.connected = True

            # Start receive loop BEFORE sending AUTH to catch response
            self.thread = threading.Thread(target=self._receive_loop, daemon=False)
            self.thread.start()
            logger.info(f"Receive thread started")

            # Small delay to ensure thread is ready
            time.sleep(0.2)
            
            # Send authentication
            auth_msg = Message.build(Command.AUTH, player_name)
            logger.info(f"Sending AUTH for {player_name}")
            result = self.send(auth_msg)
            logger.info(f"AUTH send result: {result}")

            logger.info(f"Connected to server {self.server_ip}:{self.server_port}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to server: {e}")
            self.connected = False
            return False

    def disconnect(self) -> None:
        """Disconnect from the server."""
        # Send QUIT before setting connected=False  
        if self.connected and self.socket:
            try:
                quit_msg = Message.build(Command.QUIT)
                with self._lock:
                    self.socket.sendall(quit_msg.encode('utf-8'))
            except:
                pass
        
        self.connected = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        if self.thread:
            self.thread.join(timeout=2)
        logger.info("Disconnected from server")

    def send(self, message: str) -> bool:
        """
        Send a message to the server.

        Args:
            message: Message string (should include \\n)

        Returns:
            True if sent successfully, False otherwise
        """
        if not self.connected or not self.socket:
            logger.error(f"Cannot send: connected={self.connected}, socket={self.socket is not None}")
            return False

        try:
            with self._lock:
                self.socket.sendall(message.encode('utf-8'))
            logger.debug(f"Sent: {message.strip()}")
            return True
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            self.connected = False
            return False

    def play_move(self, move: str) -> bool:
        """Send a move to the server.

        Normalize the move string (e.g. uppercase -> lowercase) to avoid
        formatting issues such as `A2-A3` being rejected by the server.
        """
        normalized = move.strip().lower()
        msg = Message.build(Command.MOVE, normalized)
        return self.send(msg)

    def _receive_loop(self) -> None:
        """Main loop: receive messages from the server."""
        buffer = ""
        try:
            while self.connected:
                try:
                    self.socket.settimeout(1)
                    data = self.socket.recv(1024)

                    if not data:
                        logger.info("Server closed connection")
                        self.connected = False
                        break

                    buffer += data.decode('utf-8')

                    # Process complete messages (terminated by \n)
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        if line.strip():
                            try:
                                message = Message.parse(line)
                                logger.debug(f"Received: {message.command}")
                                self.on_message(message)
                            except Exception as e:
                                logger.error(f"Error processing message: {e}")

                except socket.timeout:
                    # Timeout is normal, continue waiting
                    pass
                except Exception as e:
                    if self.connected:
                        logger.error(f"Error receiving: {e}")
                        time.sleep(0.1)

        except Exception as e:
            logger.error(f"Receive loop error: {e}")
        finally:
            self.connected = False
            if self.socket:
                try:
                    self.socket.close()
                except:
                    pass


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    def on_msg(msg):
        print(f"Received: {msg.command} {msg.args}")

    client = GameClient("localhost", 12345, on_msg)
    if client.connect("TestPlayer"):
        try:
            import time
            for i in range(10):
                time.sleep(1)
                client.play_move("e2-e4")
        except KeyboardInterrupt:
            pass
        finally:
            client.disconnect()
