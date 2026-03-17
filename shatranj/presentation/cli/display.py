"""
display.py - ASCII display of the Shatranj board

Role: transform a Board object into human-readable text for the terminal.

Why a separate file?
  - Separation of concerns: the Board does not know how to display itself,
    the CLI does not know how to draw. This is the Presentation layer.
  - Easy to test: we can display any Board state without side effects.
"""

import os
import sys

from shatranj.domain.core.board import Board
from shatranj.utils.constants import (
    WHITE,
    BLACK,
    SHAH,
    FERZ,
    ROOK,
    ALFIL,
    KNIGHT,
    PAWN,
)
from shatranj.utils.constants import BOARD_SIZE

# Dictionary: (piece_type, color) -> ASCII letter
# White pieces = UPPERCASE, Black pieces = lowercase
PIECE_SYMBOLS = {
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

# ANSI color codes:
# - white pieces: bright white
# - black pieces: bright cyan (more readable than black on dark background)
ANSI_RESET = "\033[0m"
ANSI_WHITE_PIECE = "\033[97m"
ANSI_BLACK_PIECE = "\033[96m"


def _supports_ansi_color() -> bool:
    """Return True if the current output probably supports ANSI colors."""
    if os.getenv("NO_COLOR"):
        return False
    if os.getenv("TERM", "").lower() == "dumb":
        return False
    return sys.stdout.isatty()


def _colorize_piece(symbol: str, color: str, use_color: bool) -> str:
    """Apply an ANSI color to a piece symbol if requested."""
    if not use_color:
        return symbol
    code = ANSI_WHITE_PIECE if color == WHITE else ANSI_BLACK_PIECE
    return f"{code}{symbol}{ANSI_RESET}"


def board_to_string(board: Board, use_color: bool = False) -> str:
    """
    Return an ASCII representation of the board.

    The board is displayed from rank 8 (top) to rank 1 (bottom),
    from column a (left) to column h (right).

    Example output::

        8  r n a f k a n r
        7  p p p p p p p p
        6  . . . . . . . .
        1  R N A F K A N R
           a b c d e f g h
    """
    lines = []

    # Iterate ranks from 7 (rank 8) down to 0 (rank 1), top to bottom
    for rank in range(BOARD_SIZE - 1, -1, -1):
        # The label displayed on the left (1 to 8)
        row_label = str(rank + 1)
        row_squares = []

        # Iterate columns from 0 (a) to 7 (h)
        for file in range(BOARD_SIZE):
            # Compute the square index: rank * 8 + file
            # Example: rank=1, file=4 -> square 12 (e2)
            square = rank * BOARD_SIZE + file
            piece = board.get_piece_at(square)

            if piece is None:
                row_squares.append(".")  # empty square
            else:
                symbol = PIECE_SYMBOLS[piece]
                row_squares.append(_colorize_piece(symbol, piece[1], use_color))

        # Format: "8  r n a f k a n r"
        lines.append(f"  {row_label}  " + " ".join(row_squares))

    # Column labels at the bottom
    lines.append("     a b c d e f g h")

    return "\n".join(lines)


def print_board(board: Board) -> None:
    """Print the board directly to the terminal."""
    print(board_to_string(board, use_color=_supports_ansi_color()))
