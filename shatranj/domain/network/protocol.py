"""
Network Protocol for Shatranj - Message format and definitions.

All messages are text-based and terminated with \n for easy parsing and debugging.
"""

from dataclasses import dataclass
from typing import Optional

# ============================================================================
# UDP Discovery Protocol (Port 12346)
# ============================================================================

# Format: SERVER_ANNOUNCE|server_name|port|version
# Example: SERVER_ANNOUNCE|Alice|12345|1.0

DISCOVERY_PORT = 12346
BROADCAST_ADDRESS = "255.255.255.255"
BROADCAST_INTERVAL = 10  # seconds
SERVER_TIMEOUT = 30  # seconds - remove server if no announce received


# ============================================================================
# TCP Game Protocol
# ============================================================================

GAME_PORT_DEFAULT = 12345

# Client -> Server Commands
class Command:
    AUTH = "AUTH"  # AUTH|player_name
    MOVE = "MOVE"  # MOVE|e2-e4
    UNDO = "UNDO"
    HINT = "HINT"
    RESIGN = "RESIGN"
    DRAW_OFFER = "DRAW_OFFER"
    DRAW_ACCEPT = "DRAW_ACCEPT"
    DRAW_REJECT = "DRAW_REJECT"
    CHAT = "CHAT"  # CHAT|message
    QUIT = "QUIT"


# Server -> Client Responses
class Response:
    OK = "OK"  # Move accepted
    INVALID = "INVALID"  # INVALID|reason=...
    OPPONENT_MOVE = "OPPONENT_MOVE"  # OPPONENT_MOVE|e7-e5
    BOARD_STATE = "BOARD_STATE"  # BOARD_STATE|fen_string
    CHECK = "CHECK"
    CHECKMATE = "CHECKMATE"  # CHECKMATE|winner=white
    STALEMATE = "STALEMATE"
    BARE_KING = "BARE_KING"  # BARE_KING|winner=white
    TIMEOUT = "TIMEOUT"  # TIMEOUT|loser=white
    HINT = "HINT"  # HINT|d2-d4
    CHAT = "CHAT"  # CHAT|opponent|message
    DRAW_OFFER = "DRAW_OFFER"  # Draw offer from opponent
    DRAW_ACCEPTED = "DRAW_ACCEPTED"
    DRAW_REJECTED = "DRAW_REJECTED"
    RESIGNATION = "RESIGNATION"  # RESIGNATION|loser=black
    AUTH_OK = "AUTH_OK"  # AUTH_OK|player_id=1|color=white
    AUTH_FAIL = "AUTH_FAIL"  # AUTH_FAIL|reason=server_full
    GAME_START = "GAME_START"  # GAME_START|white=Alice|black=Bob|blitz=0|time=30
    ERROR = "ERROR"  # ERROR|message


# Invalid move reasons
class InvalidReason:
    NOT_YOUR_TURN = "not_your_turn"
    ILLEGAL_MOVE = "illegal_move"
    WOULD_BE_CHECK = "would_be_check"
    INVALID_FORMAT = "invalid_format"
    NO_PIECE = "no_piece"
    WRONG_COLOR = "wrong_color"


@dataclass
class Message:
    """Represents a network message."""
    command: str
    args: list[str]
    raw: str

    @classmethod
    def parse(cls, line: str) -> "Message":
        """Parse a message from a network line."""
        parts = line.strip().split("|")
        command = parts[0]
        args = parts[1:]
        return cls(command=command, args=args, raw=line)

    def serialize(self) -> str:
        """Serialize to network format."""
        if self.args:
            return self.command + "|" + "|".join(self.args) + "\n"
        return self.command + "\n"

    @staticmethod
    def build(command: str, *args: str) -> str:
        """Build a message string."""
        if args:
            return command + "|" + "|".join(args) + "\n"
        return command + "\n"
