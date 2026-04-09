"""
UDP Discovery Server - Broadcasts server availability on the local network.

The server periodically sends announcements on the broadcast address so clients
can discover it without manual configuration.
"""

import logging
import socket
import threading
import time
from typing import Optional

from shatranj.domain.network.protocol import (
    BROADCAST_ADDRESS,
    BROADCAST_INTERVAL,
    DISCOVERY_PORT,
)

logger = logging.getLogger(__name__)


class DiscoveryServer:
    """UDP server that broadcasts server availability periodically."""

    def __init__(self, server_name: str, game_port: int, version: str = "1.0"):
        self.server_name = server_name
        self.game_port = game_port
        self.version = version
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.socket: Optional[socket.socket] = None

    def start(self) -> None:
        """Start the discovery server in a background thread."""
        if self.running:
            logger.warning("Discovery server already running")
            return

        self.running = True
        self.thread = threading.Thread(target=self._broadcast_loop, daemon=True)
        self.thread.start()
        logger.info(
            f"Discovery server started for '{self.server_name}' on port {self.game_port}"
        )

    def stop(self) -> None:
        """Stop the discovery server."""
        self.running = False
        if self.socket:
            try:
                self.socket.close()
            except OSError:
                pass
        if self.thread:
            self.thread.join(timeout=2)
        logger.info("Discovery server stopped")

    def _broadcast_loop(self) -> None:
        """Main loop: broadcast announcements periodically."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

            while self.running:
                try:
                    message = (
                        f"SERVER_ANNOUNCE|{self.server_name}|"
                        f"{self.game_port}|{self.version}\n"
                    )
                    self.socket.sendto(
                        message.encode("utf-8"),
                        (BROADCAST_ADDRESS, DISCOVERY_PORT),
                    )
                    logger.debug(f"Broadcast announcement: {message.strip()}")

                    for _ in range(BROADCAST_INTERVAL):
                        if not self.running:
                            break
                        time.sleep(1)

                except OSError as err:
                    logger.error("Error broadcasting: %s", err)
                    if self.running:
                        time.sleep(1)

        except OSError as err:
            logger.error("Discovery server error: %s", err)
        finally:
            if self.socket:
                try:
                    self.socket.close()
                except OSError:
                    pass
