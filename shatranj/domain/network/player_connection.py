"""
Player Connection - Manages TCP communication with a single connected player.
"""

import socket
import threading
from typing import Optional, Callable
import logging

from shatranj.domain.network.protocol import Message

logger = logging.getLogger(__name__)


class PlayerConnection:
    """Manages TCP communication with a connected player."""

    def __init__(self, socket: socket.socket, addr: tuple, on_message: Callable):
        """
        Initialize a player connection.

        Args:
            socket: Connected TCP socket
            addr: Address tuple (ip, port)
            on_message: Callback function(PlayerConnection, Message) called on received messages
        """
        self.socket = socket
        self.socket.setsockopt(6, 1, 1)  # Disable Nagle algorithm (IPPROTO_TCP=6, TCP_NODELAY=1)
        self.addr = addr
        self.player_id: Optional[str] = None
        self.color: Optional[str] = None
        self.on_message = on_message
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

    def start(self) -> None:
        """Start listening for messages from this player."""
        if self.running:
            logger.warning(f"Player {self.addr} already connected")
            return

        self.running = True
        self.thread = threading.Thread(target=self._receive_loop, daemon=True)
        self.thread.start()
        logger.info(f"Player connection started: {self.addr}")

    def stop(self) -> None:
        """Stop communication with this player."""
        self.running = False
        try:
            self.socket.close()
        except:
            pass
        if self.thread:
            self.thread.join(timeout=2)
        logger.info(f"Player connection closed: {self.addr}")

    def send(self, message: str) -> bool:
        """
        Send a message to the player.

        Args:
            message: Message string (should include \\n)

        Returns:
            True if sent successfully, False otherwise
        """
        try:
            with self._lock:
                self.socket.sendall(message.encode('utf-8'))
            return True
        except Exception as e:
            logger.error(f"Error sending to {self.addr}: {e}")
            return False

    def _receive_loop(self) -> None:
        """Main loop: receive messages from the player."""
        buffer = ""
        logger.info(f"[RECV] {self.addr} - Starting receive loop")
        try:
            while self.running:
                try:
                    self.socket.settimeout(2)
                    data = self.socket.recv(1024)
                    logger.info(f"[RECV] {self.addr} - Got {len(data) if data else 0} bytes: {repr(data[:100]) if data else 'EMPTY'}")

                    if not data:
                        logger.info(f"Player {self.addr} disconnected")
                        self.running = False
                        break

                    buffer += data.decode('utf-8')

                    # Process complete messages (terminated by \n)
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        if line.strip():
                            try:
                                message = Message.parse(line)
                                logger.debug(f"[RECV] {self.addr} - Parsed: {message.command}")
                                self.on_message(self, message)
                            except Exception as e:
                                logger.error(f"Error processing message from {self.addr}: {e}")

                except socket.timeout:
                    # Timeout is expected, just continue
                    pass
                except Exception as e:
                    if self.running:
                        logger.error(f"Error receiving from {self.addr}: {e}")

        except Exception as e:
            logger.error(f"Receive loop error for {self.addr}: {e}")
        finally:
            self.running = False
            try:
                self.socket.close()
            except:
                pass
            logger.info(f"[RECV] {self.addr} - Receive loop ended")
