"""
UDP Discovery Client - Listens for server announcements on the local network.

The client maintains a list of available servers received via UDP broadcasts.
"""

import logging
import socket
import threading
import time
from typing import Dict, Optional

from shatranj.domain.network.protocol import DISCOVERY_PORT, SERVER_TIMEOUT

logger = logging.getLogger(__name__)


class ServerInfo:
    """Information about a discovered server."""

    def __init__(self, name: str, ip: str, port: int, version: str):
        self.name = name
        self.ip = ip
        self.port = port
        self.version = version
        self.last_seen = time.time()

    def is_stale(self) -> bool:
        """Check if this server hasn't been seen for SERVER_TIMEOUT seconds."""
        return time.time() - self.last_seen > SERVER_TIMEOUT

    def update_seen(self) -> None:
        """Update the last seen timestamp."""
        self.last_seen = time.time()

    def __repr__(self) -> str:
        return (
            f"ServerInfo({self.name}, {self.ip}:{self.port}, v{self.version})"
        )


class DiscoveryClient:
    """UDP client that discovers available servers on the local network."""

    def __init__(self):
        """Initialize the discovery client."""
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.socket: Optional[socket.socket] = None
        self.servers: Dict[tuple[str, int], ServerInfo] = {}
        self._lock = threading.Lock()

    def start(self) -> None:
        """Start listening for server announcements in a background thread."""
        if self.running:
            logger.warning("Discovery client already running")
            return

        self.running = True
        self.thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.thread.start()
        logger.info("Discovery client started")

    def stop(self) -> None:
        """Stop the discovery client."""
        self.running = False
        if self.socket:
            try:
                self.socket.close()
            except OSError:
                pass
        if self.thread:
            self.thread.join(timeout=2)
        logger.info("Discovery client stopped")

    def get_servers(self) -> list[ServerInfo]:
        """Return a list of currently available servers."""
        with self._lock:
            self.servers = {
                k: v for k, v in self.servers.items() if not v.is_stale()
            }
            return list(self.servers.values())

    def scan(self, duration: float = 2.0) -> list[ServerInfo]:
        """Listen briefly for broadcasts and return discovered servers."""
        self.start()
        try:
            time.sleep(max(0.0, duration))
            return self.get_servers()
        finally:
            self.stop()

    def _listen_loop(self) -> None:
        """Main loop: listen for UDP broadcasts from servers."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind(("", DISCOVERY_PORT))

            logger.debug(f"Listening for broadcasts on port {DISCOVERY_PORT}")

            while self.running:
                try:
                    self.socket.settimeout(2)
                    data, addr = self.socket.recvfrom(1024)
                    message = data.decode("utf-8").strip()

                    if message.startswith("SERVER_ANNOUNCE|"):
                        self._process_announcement(message, addr[0])

                except socket.timeout:
                    continue
                except (OSError, UnicodeDecodeError) as err:
                    if self.running:
                        logger.error("Error receiving broadcast: %s", err)

        except OSError as err:
            logger.error("Discovery client error: %s", err)
        finally:
            if self.socket:
                try:
                    self.socket.close()
                except OSError:
                    pass

    def _process_announcement(self, message: str, sender_ip: str) -> None:
        """Process a SERVER_ANNOUNCE message."""
        try:
            parts = message.split("|")
            if len(parts) < 4:
                logger.warning(f"Invalid announcement format: {message}")
                return

            name = parts[1]
            port = int(parts[2])
            version = parts[3]
            key = (sender_ip, port)

            with self._lock:
                if key in self.servers:
                    self.servers[key].update_seen()
                    logger.debug(
                        f"Updated server: {name} at {sender_ip}:{port}"
                    )
                else:
                    self.servers[key] = ServerInfo(
                        name, sender_ip, port, version
                    )
                    logger.info(
                        f"Discovered server: {name} at {sender_ip}:{port}"
                    )

        except ValueError as err:
            logger.error("Error processing announcement: %s", err)
