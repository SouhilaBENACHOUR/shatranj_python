"""
Player Connection - Manages TCP communication with a single connected player.
"""

import logging
import socket
import threading
from typing import Callable, Optional

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
            on_message: Callback function(PlayerConnection, Message).
        """
        self.socket = socket
        self.socket.setsockopt(
            6, 1, 1
        )  # Disable Nagle algorithm (IPPROTO_TCP=6, TCP_NODELAY=1)
        self.addr = addr
        self.player_id: Optional[str] = None
        self.color: Optional[str] = None
        self.on_message = on_message
        self.running = False
        self.thread: Optional[threading.Thread] = None

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
        self.running = False
        try:
            self.socket.close()
        except OSError:
            pass

        if self.thread and self.thread != threading.current_thread():
            try:
                self.thread.join(timeout=1)
            except RuntimeError:
                pass

    def send(self, message) -> bool:
        if not self.running:
            return False

        try:
            data = (
                message.encode()
                if hasattr(message, "encode")
                else str(message).encode("utf-8")
            )
            if not data.endswith(b"\n"):
                data += b"\n"
            self.socket.sendall(data)
            return True
        except OSError:
            self.running = False
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
                    logger.info(
                        f"[RECV] {self.addr} - Got {len(data) if data else 0} bytes: {repr(data[:100]) if data else 'EMPTY'}"
                    )

                    if not data:
                        logger.info(f"Player {self.addr} disconnected")
                        self.running = False
                        break

                    buffer += data.decode("utf-8")

                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        if not line.strip():
                            continue
                        try:
                            message = Message.parse(line)
                            logger.debug(
                                f"[RECV] {self.addr} - Parsed: {message.command}"
                            )
                            self.on_message(self, message)
                        except Exception as err:
                            logger.error(
                                "Error processing message from %s: %s",
                                self.addr,
                                err,
                            )

                except socket.timeout:
                    continue
                except OSError as err:
                    if self.running:
                        logger.error("Error receiving from %s: %s", self.addr, err)

        except OSError as err:
            logger.error("Receive loop error for %s: %s", self.addr, err)
        finally:
            self.running = False
            try:
                self.socket.close()
            except OSError:
                pass
            logger.info(f"[RECV] {self.addr} - Receive loop ended")
