from dataclasses import dataclass

# ============================================================================
# UDP Discovery Protocol (Port 12346)
# ============================================================================
DISCOVERY_PORT = 12346
BROADCAST_ADDRESS = "255.255.255.255"
BROADCAST_INTERVAL = 10
SERVER_TIMEOUT = 30

# ============================================================================
# TCP Game Protocol
# ============================================================================
GAME_PORT_DEFAULT = 12345


class Command:
    CONN = "CONN"
    MOVE = "MOVE"
    UNDO = "UNDO"
    HINT = "HINT"
    RESIGN = "RESIGN"
    DRAW_OFFER = "DRAW_OFFER"
    DRAW_ACCEPT = "DRAW_ACCEPT"
    DRAW_REJECT = "DRAW_REJECT"
    CHAT = "CHAT"
    QUIT = "QUIT"
    # Nouveaux ajouts
    PING = "PING"
    PLAYERS = "PLAYERS"
    NEW = "NEW"
    ACCEPT = "ACCEPT"
    DECLINE = "DECLINE"
    CANCEL = "CANCEL"
    AWAY = "AWAY"
    BACK = "BACK"
    SCOREBOARD = "SCOREBOARD"


class Response:
    OK = "OK"
    INVALID = "INVALID"
    OPPONENT_MOVE = "OPPONENT_MOVE"
    BOARD_STATE = "BOARD_STATE"
    CHECK = "CHECK"
    CHECKMATE = "CHECKMATE"
    STALEMATE = "STALEMATE"
    BARE_KING = "BARE_KING"
    TIMEOUT = "TIMEOUT"
    HINT = "HINT"
    CHAT = "CHAT"
    DRAW_OFFER = "DRAW_OFFER"
    DRAW_ACCEPTED = "DRAW_ACCEPTED"
    DRAW_REJECTED = "DRAW_REJECTED"
    RESIGNATION = "RESIGNATION"
    CONN_OK = "CONN_OK"
    CONN_FAIL = "CONN_FAIL"
    GAME_START = "GAME_START"
    ERROR = "ERROR"
    # Nouveaux ajouts
    PONG = "PONG"
    PLAYERS_LIST = "PLAYERS_LIST"
    INVITE_SENT = "INVITE_SENT"
    INVITE_RECV = "INVITE_RECV"
    INVITE_ACCEPTED = "INVITE_ACCEPTED"
    INVITE_DECLINED = "INVITE_DECLINED"
    SCOREBOARD = "SCOREBOARD"


class InvalidReason:
    NOT_YOUR_TURN = "not_your_turn"
    ILLEGAL_MOVE = "illegal_move"
    WOULD_BE_CHECK = "would_be_check"
    INVALID_FORMAT = "invalid_format"
    NO_PIECE = "no_piece"
    WRONG_COLOR = "wrong_color"


@dataclass
class Message:
    command: str
    args: list[str]
    raw: str

    @classmethod
    def parse(cls, line: str) -> "Message":
        parts = line.strip().split("|")
        command = parts[0]
        args = parts[1:]
        return cls(command=command, args=args, raw=line)

    def serialize(self) -> str:
        if self.args:
            return self.command + "|" + "|".join(self.args) + "\n"
        return self.command + "\n"

    @staticmethod
    def build(command: str, *args: str) -> str:
        if args:
            return command + "|" + "|".join(args) + "\n"
        return command + "\n"
