"""Shared save/load helpers for CLI and GUI."""

from dataclasses import dataclass, field

from shatranj.domain.core.board import Board
from shatranj.domain.core.move import Move
from shatranj.presentation.cli.game_state import GameState
from shatranj.utils.constants import (ALFIL, BLACK, FERZ, KNIGHT, PAWN, ROOK,
                                      SHAH, WHITE)
from shatranj.utils.exceptions import InvalidSquareError, LoadError, SaveError

PIECE_TO_SYMBOL = {
    (SHAH, WHITE): "K",
    (FERZ, WHITE): "F",
    (ROOK, WHITE): "R",
    (ALFIL, WHITE): "A",
    (KNIGHT, WHITE): "N",
    (PAWN, WHITE): "P",
    (SHAH, BLACK): "k",
    (FERZ, BLACK): "f",
    (ROOK, BLACK): "r",
    (ALFIL, BLACK): "a",
    (KNIGHT, BLACK): "n",
    (PAWN, BLACK): "p",
}
SYMBOL_TO_PIECE = {symbol: piece for piece, symbol in PIECE_TO_SYMBOL.items()}
PIECE_TYPE_TO_TOKEN = {
    SHAH: "K",
    FERZ: "F",
    ROOK: "R",
    ALFIL: "A",
    KNIGHT: "N",
    PAWN: "P",
}
TOKEN_TO_PIECE_TYPE = {
    token: piece for piece, token in PIECE_TYPE_TO_TOKEN.items()
}


@dataclass(slots=True)
class ClockState:
    """Serialized clock data persisted with a saved game."""

    mode: str = "idle"
    label: str = "No active game"
    base_seconds: float = 0.0
    increment_seconds: int = 0
    white_seconds: float = 0.0
    black_seconds: float = 0.0
    paused: bool = False


@dataclass(slots=True)
class LoadedGame:
    """All data recovered from a saved game."""

    state: GameState
    verbose: bool = False
    debug: bool = False
    clock: ClockState = field(default_factory=ClockState)
    ai_players: dict = field(default_factory=dict)


def strip_save_comments(text: str) -> list[str]:
    """Return non-empty save-file lines without inline or block comments."""

    return [
        line for _line_number, line in _strip_save_comments_with_numbers(text)
    ]


def _strip_save_comments_with_numbers(text: str) -> list[tuple[int, str]]:
    """
    Return non-empty save-file lines together with their source line number.
    """

    result = []
    block_depth = 0

    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        chars = []
        i = 0
        while i < len(raw_line):
            ch = raw_line[i]

            if block_depth > 0:
                if ch == "{":
                    block_depth += 1
                elif ch == "}":
                    block_depth -= 1
                i += 1
                continue

            if ch == "#":
                break
            if ch == "{":
                block_depth = 1
                i += 1
                continue

            chars.append(ch)
            i += 1

        line = "".join(chars).strip()
        if line:
            result.append((line_number, line))

    return result


def load_game_file(path: str) -> LoadedGame:
    """Load a saved game from disk."""

    try:
        with open(path, "r", encoding="ascii") as handle:
            raw = handle.read()
    except OSError as err:
        raise LoadError(f"Could not open '{path}': {err}", path=path) from err

    line_entries = _strip_save_comments_with_numbers(raw)
    lines = [line for _line_number, line in line_entries]

    try:
        idx_settings = lines.index("[settings]")
        idx_game = lines.index("[game]")
        idx_history = lines.index("[history]")
    except ValueError as err:
        raise LoadError(
            "Invalid save format: missing section.", path=path
        ) from err

    settings = _parse_settings(lines[idx_settings + 1: idx_game])
    state = _parse_game_state(
        game_lines=line_entries[idx_game + 1: idx_history],
        history_lines=line_entries[idx_history + 1:],
        path=path,
    )
    return LoadedGame(
        state=state,
        verbose=_parse_bool(settings.get("verbose"), False),
        debug=_parse_bool(settings.get("debug"), False),
        clock=_parse_clock_state(settings),
        ai_players=_parse_ai_players(settings),
    )


def save_game_file(
    path: str,
    *,
    state: GameState,
    verbose: bool = False,
    debug: bool = False,
    clock: ClockState | None = None,
    ai_players: dict | None = None,
) -> None:
    """Save a game to disk."""
    if ai_players is None:
        ai_players = {}

    if state is None:
        raise SaveError("No game in progress.")

    try:
        with open(path, "w", encoding="ascii") as handle:
            handle.write("[settings]\n")
            handle.write(f"verbose={str(verbose).lower()}\n")
            handle.write(f"debug={str(debug).lower()}\n")
            for color, ai in ai_players.items():
                color_key = "white" if color == WHITE else "black"
                handle.write(f"ai-color={color_key}\n")
                handle.write(
                    f"ai-mode={getattr(ai, 'algorithm', 'alphabeta')}\n"
                )
                depth = getattr(getattr(ai, "_search", None), "_depth", 3)
                handle.write(f"ai-depth={depth}\n")
                handle.write(
                    f"ai-scoring={getattr(ai, 'scoring', 'advanced')}\n"
                )
            if clock is not None and clock.mode == "timed":
                base_seconds = max(
                    0.0,
                    clock.base_seconds,
                    clock.white_seconds,
                    clock.black_seconds,
                )
                handle.write("clock_mode=timed\n")
                handle.write(f"time_control_name={clock.label}\n")
                handle.write(f"base_seconds={base_seconds:.3f}\n")
                inc = int(max(0, clock.increment_seconds))
                handle.write(f"increment_seconds={inc}\n")
                white_s = max(0.0, clock.white_seconds)
                handle.write(f"white_remaining_seconds={white_s:.3f}\n")
                black_s = max(0.0, clock.black_seconds)
                handle.write(f"black_remaining_seconds={black_s:.3f}\n")
                handle.write(f"timer_paused={str(clock.paused).lower()}\n")
            handle.write("\n")

            handle.write("[game]\n")
            handle.write(f"{state.current_color[0].upper()}\n")
            for rank in range(7, -1, -1):
                row = []
                for file in range(8):
                    square = rank * 8 + file
                    piece = state.board.get_piece_at(square)
                    row.append(
                        "_" if piece is None else PIECE_TO_SYMBOL[piece]
                    )
                handle.write(" ".join(row) + "\n")
            handle.write("\n")

            handle.write("[history]\n")
            history = state.get_history()
            for index in range(0, len(history), 2):
                line_parts = [_serialize_move(history[index])]
                if index + 1 < len(history):
                    line_parts.append(_serialize_move(history[index + 1]))
                handle.write(" ".join(line_parts) + "\n")
    except OSError as err:
        raise SaveError(f"Could not write to '{path}': {err}") from err


def _parse_settings(lines: list[str]) -> dict[str, str]:
    settings = {}
    for line in lines:
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        settings[key.strip().lower()] = value.strip()
    return settings


def _parse_game_state(
    *,
    game_lines: list[tuple[int, str]],
    history_lines: list[tuple[int, str]],
    path: str,
) -> GameState:
    if not game_lines:
        raise LoadError("Missing current player color.", path=path)

    color_line, color_value = game_lines[0]
    color_letter = color_value.strip().upper()
    if color_letter not in ("W", "B"):
        raise LoadError(
            f"Invalid player color: '{color_letter}'",
            path=path,
            line=color_line,
        )
    current_color = WHITE if color_letter == "W" else BLACK

    board_lines = game_lines[1:9]
    if len(board_lines) != 8:
        raise LoadError(
            "Invalid board format: expected 8 rows",
            path=path,
            line=board_lines[-1][0] if board_lines else color_line,
        )

    board = Board(setup=False)
    for rank_idx, (line_number, board_line) in enumerate(board_lines, start=1):
        symbols = board_line.split()
        if len(symbols) != 8:
            raise LoadError(
                f"Invalid board row {rank_idx}: '{board_line}'",
                path=path,
                line=line_number,
            )

        rank = 8 - rank_idx
        for file_idx, symbol in enumerate(symbols):
            if symbol == "_":
                continue
            if symbol not in SYMBOL_TO_PIECE:
                raise LoadError(
                    f"Unknown piece symbol: '{symbol}' at row {rank_idx}",
                    path=path,
                    line=line_number,
                )
            piece_type, color = SYMBOL_TO_PIECE[symbol]
            board.place_piece(piece_type, color, rank * 8 + file_idx)

    history = _parse_history(history_lines, board, path)

    state = GameState.__new__(GameState)
    state.board = board
    state.current_color = current_color
    state._history = [(move, {}) for move in history]
    state._redo_stack = []
    return state


def _parse_history(
    history_lines: list[tuple[int, str]],
    board: Board,
    path: str,
) -> list[Move]:
    history = []

    for line_number, line in history_lines:
        tokens = line.split()
        i = 0
        while i + 1 < len(tokens):
            color_token = tokens[i].upper()
            move_token = tokens[i + 1]
            i += 2

            if color_token not in ("W", "B"):
                raise LoadError(
                    f"Invalid move color in history: '{color_token}'",
                    path=path,
                    line=line_number,
                )

            color = WHITE if color_token == "W" else BLACK
            move_part, captured = _parse_history_move_token(
                move_token,
                path,
                line_number,
            )
            if len(move_part) != 5 or move_part[2] not in ("-", "x"):
                raise LoadError(
                    f"Invalid move in history: '{move_token}'",
                    path=path,
                    line=line_number,
                )

            try:
                from_square = Board.algebraic_to_square(move_part[0:2])
                to_square = Board.algebraic_to_square(move_part[3:5])
            except InvalidSquareError as err:
                raise LoadError(
                    f"Invalid square in history: {err}",
                    path=path,
                    line=line_number,
                ) from err

            piece_info = board.get_piece_at(from_square)
            piece_type = PAWN if piece_info is None else piece_info[0]
            history.append(
                Move(
                    from_square,
                    to_square,
                    piece_type,
                    color,
                    captured,
                )
            )

    return history


def _parse_history_move_token(
    move_token: str,
    path: str,
    line_number: int,
) -> tuple[str, str | None]:
    """Parse one saved move token and its optional captured-piece suffix."""
    move_part, separator, capture_token = move_token.partition(":")
    if len(move_part) != 5 or move_part[2] not in ("-", "x"):
        return move_token, None

    if move_part[2] != "x":
        if separator:
            raise LoadError(
                f"Unexpected capture detail in history: '{move_token}'",
                path=path,
                line=line_number,
            )
        return move_part, None

    if not separator:
        return move_part, "unknown"

    piece = TOKEN_TO_PIECE_TYPE.get(capture_token.upper())
    if piece is None:
        raise LoadError(
            f"Invalid captured piece in history: '{move_token}'",
            path=path,
            line=line_number,
        )
    return move_part, piece


def _parse_clock_state(settings: dict[str, str]) -> ClockState:
    if settings.get("clock_mode", "").strip().lower() != "timed":
        return ClockState()

    base_seconds = max(0.0, _parse_float(settings.get("base_seconds"), 0.0))
    white_seconds = max(
        0.0,
        _parse_float(settings.get("white_remaining_seconds"), base_seconds),
    )
    black_seconds = max(
        0.0,
        _parse_float(settings.get("black_remaining_seconds"), base_seconds),
    )
    return ClockState(
        mode="timed",
        label=settings.get("time_control_name", "Loaded Game"),
        base_seconds=base_seconds,
        increment_seconds=max(
            0,
            _parse_int(settings.get("increment_seconds"), 0),
        ),
        white_seconds=white_seconds,
        black_seconds=black_seconds,
        paused=_parse_bool(settings.get("timer_paused"), False),
    )


def _serialize_move(move: Move) -> str:
    color_letter = "W" if move.color == WHITE else "B"
    from_square = Board.square_to_algebraic(move.from_square)
    to_square = Board.square_to_algebraic(move.to_square)
    separator = "x" if move.captured_piece else "-"
    if not move.captured_piece:
        return f"{color_letter} {from_square}{separator}{to_square}"

    capture_token = PIECE_TYPE_TO_TOKEN.get(move.captured_piece)
    if capture_token is None:
        return f"{color_letter} {from_square}{separator}{to_square}"

    return (
        f"{color_letter} {from_square}{separator}{to_square}:{capture_token}"
    )


def _parse_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in ("true", "1", "yes", "on")


def _parse_int(value: str | None, default: int) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _parse_float(value: str | None, default: float) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _parse_ai_players(settings: dict[str, str]) -> dict:
    """Reconstruct AI players from saved settings."""
    from shatranj.domain.ai.ai_player import AIPlayer

    color_str = settings.get("ai-color", "").strip().lower()
    if not color_str:
        return {}

    color = WHITE if color_str == "white" else BLACK
    algo = settings.get("ai-mode", "alphabeta").strip().lower()
    depth = _parse_int(settings.get("ai-depth"), 3)
    scoring = settings.get("ai-scoring", "advanced").strip().lower()

    return {
        color: AIPlayer(
            color=color,
            depth=depth,
            algorithm=algo,
            scoring=scoring,
        )
    }
