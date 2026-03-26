
# Shatranj Multi-Player: Network Architecture

## 1. Overview
The Shatranj network architecture provides a seamless, secure, and configuration-free multi-player experience. It uses a dual-stack approach: **UDP** for local discovery and **TCP** for reliable game state sync.

---

## 2. Core Components

### A. Automatic Discovery (UDP)
Eliminates manual IP entry by broadcasting server presence on the Local Area Network (LAN).

* **Port:** `12346`
* **Protocol:** UDP Broadcast
* **Interval:** Every 10 seconds
* **Timeout:** Servers are removed after 30s of inactivity.

#### Server-Side (Announcer)
```python
from shatranj.domain.network import DiscoveryServer

# Initialize and launch the discovery beacon
discovery = DiscoveryServer(
    server_name="Grandmaster_Room", 
    game_port=12345, 
    version="1.0"
)
discovery.start()
```

#### Client-Side (Listener)
```python
from shatranj.domain.network import DiscoveryClient

client = DiscoveryClient()
client.start()

# Retrieves a dynamic list of active local servers
active_servers = client.get_servers()
```

### B. Game Communication (TCP)
A persistent connection ensuring moves are received in the correct order without data loss.

* **Port:** `12345` (Default)
* **Format:** ASCII text terminated by `\n` (LF).
* **Concurrency:** Multi-threaded; one dedicated thread per client.

---

## 3. Communication Protocol
Messages use a pipe-delimited format: `COMMAND|arg1|arg2|...`

### Client → Server Commands
| Command | Format | Purpose |
| :--- | :--- | :--- |
| `CONN` | `CONN\|name` | Log in to the server |
| `MOVE` | `MOVE\|e2-e4` | Submit a move |
| `UNDO` | `UNDO` | Request to revert a move |

| `QUIT` | `QUIT` | Disconnect |

### Server → Client Responses
| Response | Format | Description |
| :--- | :--- | :--- |
| `CONN_OK` | `CONN_OK\|id=1\|color=w` | Login successful |
| `GAME_START` | `GAME_START\|w=A\|b=B` | Match paired and started |
| `INVALID` | `INVALID\|reason=err` | Move rejected by engine |
| `OPP_MOVE` | `OPP_MOVE\|e7-e5` | Syncs opponent's move |
| `CHECKMATE` | `CHECKMATE\|winner=w` | Game over notification |

---

## 4. Multi-Threaded Architecture

The system uses three levels of threading to keep the UI responsive:

1.  **Main Acceptor Thread:** Listens for and accepts new TCP connections.
2.  **Client Worker Threads:** Each player has a thread to parse messages and validate moves.
3.  **Discovery Thread:** A background heartbeat thread for UDP broadcasts.






## 5. Security & Anti-Cheat
Shatranj follows a **"Server-as-Authority"** model. The server verifies every `MOVE`:
* **Turn Validation:** Ensures the player isn't moving out of turn.
* **Move Legality:** Uses `ShatranjEngine` to verify piece movement rules.
* **King Safety:** Confirms the move doesn't leave the Shah in check.

---

## 6. Future Roadmap
* [ ] **SSL/TLS Support:** Encrypted streams for WAN play.
* [ ] **Spectator Mode:** Allow users to watch live matches.
* [ ] **Elo Ratings:** Integration for player rankings.
