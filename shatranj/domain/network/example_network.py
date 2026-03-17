"""
Example: Multi-player network demo for Shatranj.

This example demonstrates:
1. Starting a game server with UDP discovery
2. Clients discovering the server
3. Two clients connecting and playing a game

Execution:
    python shatranj/domain/network/example_network.py

This starts:
- 1 server on port 12345 (with UDP discovery on 12346)
- 1 discovery client listening for servers
- 2 game clients connecting to the server
"""

import time
import random
import logging
import threading
from threading import Thread

from shatranj.domain.network import (
    DiscoveryServer,
    DiscoveryClient,
    GameServer,
    GameClient,
    Command,
    Response,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def example_server():
    """Start a game server with discovery announcements."""
    print("\n=== Starting Game Server ===")

    discovery = DiscoveryServer("MyGameServer", 12345, version="1.0")
    discovery.start()

    server = GameServer("MyGameServer", 12345, max_sessions=5)
    server.start()

    try:
        for i in range(120):  # Run for 2 minutes
            time.sleep(1)
            if i % 10 == 0:
                print(f"  Server running... ({i}s)")
    except KeyboardInterrupt:
        print("Server interrupted")
    finally:
        server.stop()
        discovery.stop()


def example_discovery_client():
    """Discover servers on the network."""
    print("\n=== Starting Discovery Client ===")

    client = DiscoveryClient()
    client.start()

    try:
        for i in range(30):
            time.sleep(1)
            servers = client.get_servers()
            print(f"[{i}] Found {len(servers)} server(s):")
            for s in servers:
                print(f"    - {s.name} at {s.ip}:{s.port} (v{s.version})")
    except KeyboardInterrupt:
        print("Discovery client stopped")
    finally:
        client.stop()


def example_game_client(player_name, server_ip="127.0.0.1", server_port=12345):
    """Connect to a game server and play some moves."""
    print(f"\n=== Starting Game Client: {player_name} ===")

    game_started = threading.Event()

    def on_message(msg):
        print(f"  [{player_name}] Received: {msg.command} {msg.args}")
        if msg.command == Response.GAME_START:
            game_started.set()

    client = GameClient(server_ip, server_port, on_message)

    if not client.connect(player_name):
        print(f"  [{player_name}] Failed to connect")
        return

    # Wait for game to start
    if game_started.wait(timeout=10):
        print(f"  [{player_name}] Game started!")
    else:
        print(f"  [{player_name}] Game did not start within timeout")
        client.disconnect()
        return

    # Simulate playing some moves
    moves = ["e2-e4", "d2-d4", "g1-f3"]
    for move in moves:
        time.sleep(random.uniform(1, 3))  # Simulate thinking time
        print(f"  [{player_name}] Playing move: {move}")
        client.play_move(move)

    time.sleep(2)
    client.disconnect()
    print(f"  [{player_name}] Disconnected")


def main():
    """Run the complete example with server and clients."""
    print("\n" + "=" * 60)
    print("  Shatranj Multi-Player Network Architecture Demo")
    print("=" * 60)

    # Start server in background thread
    server_thread = Thread(target=example_server, daemon=True)
    server_thread.start()

    time.sleep(1)  # Let server start

    # Start discovery client in background thread
    discovery_thread = Thread(target=example_discovery_client, daemon=True)
    discovery_thread.start()

    time.sleep(3)  # Discovery should find the server

    # Start two game clients
    client1_thread = Thread(target=example_game_client, args=("Alice",), daemon=True)
    client2_thread = Thread(target=example_game_client, args=("Bob",), daemon=True)

    client1_thread.start()
    time.sleep(1)
    client2_thread.start()

    # Wait for clients to finish
    client1_thread.join(timeout=30)
    client2_thread.join(timeout=30)

    # Wait for discovery to finish
    discovery_thread.join(timeout=5)

    # Stop server
    time.sleep(2)

    print("\n" + "=" * 60)
    print("  Example Complete")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    # Uncomment one of the following to run specific components:

    # Run complete example (server + discovery + clients)
    main()

    # Or run individual components:
    # example_server()
    # example_discovery_client()
    # example_game_client("Test Player")
