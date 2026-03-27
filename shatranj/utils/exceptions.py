"""
exceptions.py - Custom exception hierarchy for Shatranj

All exceptions inherit from ShatranjError so that callers can catch
either the base class (broad) or a specific subclass (precise).

Hierarchy:
  ShatranjError
  ├── BoardError
  │   ├── InvalidSquareError
  │   ├── InvalidMoveError
  │   └── NoPieceError
  ├── RulesError
  │   └── IllegalMoveError
  ├── AIError
  │   └── NoMoveAvailableError
  ├── EvaluatorError
  ├── PersistenceError
  │   ├── SaveError
  │   └── LoadError
  ├── ConfigError
  └── MissingShahError
"""


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------


class ShatranjError(Exception):
    """Base exception for all Shatranj errors."""


# ---------------------------------------------------------------------------
# Board-level errors
# ---------------------------------------------------------------------------


class BoardError(ShatranjError):
    """Raised for any invalid operation on the board."""


class InvalidSquareError(BoardError):
    """Raised when a square index is outside [0, 63].

    Example::
        raise InvalidSquareError(f"Square {sq} must be in [0, 63]")
    """


class InvalidMoveError(BoardError):
    """Raised when a move cannot be applied (same square, empty source, …).

    Example::
        raise InvalidMoveError("Cannot move to the same square")
    """


class NoPieceError(BoardError):
    """Raised when an operation expects a piece on a square but finds none.

    Example::
        raise NoPieceError(f"No piece on square {square}")
    """


class MissingShahError(BoardError):
    """Raised when a Shah cannot be found on the board."""
# ---------------------------------------------------------------------------
# Rules errors
# ---------------------------------------------------------------------------


class RulesError(ShatranjError):
    """Raised when a game-rule constraint is violated."""


class IllegalMoveError(RulesError):
    """Raised when a move is pseudo-legal but leaves the Shah in check.

    Example::
        raise IllegalMoveError(f"Move {move} leaves Shah in check")
    """


# ---------------------------------------------------------------------------
# AI errors
# ---------------------------------------------------------------------------


class AIError(ShatranjError):
    """Raised when the AI engine encounters an unexpected situation."""


class NoMoveAvailableError(AIError):
    """Raised when the AI finds no legal move (checkmate or stalemate).

    Example::
        raise NoMoveAvailableError("No legal move for BLACK")
    """


# ---------------------------------------------------------------------------
# Evaluator errors
# ---------------------------------------------------------------------------


class EvaluatorError(ShatranjError):
    """Raised when an unknown evaluation mode is requested.

    Example::
        raise EvaluatorError(f"Unknown mode '{mode}'")
    """


# ---------------------------------------------------------------------------
# Persistence errors (save / load)
# ---------------------------------------------------------------------------


class PersistenceError(ShatranjError):
    """Base class for file I/O errors."""


class SaveError(PersistenceError):
    """Raised when writing a save file fails.

    Example::
        raise SaveError(f"Could not write to '{path}': {err}")
    """


class LoadError(PersistenceError):
    """Raised when reading or parsing a save file fails.

    Attributes
    ----------
    path : str
        Path of the file that could not be loaded.
    line : int | None
        Line number where the error was detected (None if unknown).

    Example::
        raise LoadError("Invalid board row 3", path="game.shj", line=12)
    """

    def __init__(
        self,
        message: str,
        path: str = "",
        line: int | None = None,
    ) -> None:
        super().__init__(message)
        self.path = path
        self.line = line

    def __str__(self) -> str:
        base = super().__str__()
        parts = [base]
        if self.path:
            parts.append(f"file='{self.path}'")
        if self.line is not None:
            parts.append(f"line={self.line}")
        return " | ".join(parts)


# ---------------------------------------------------------------------------
# Configuration errors
# ---------------------------------------------------------------------------


class ConfigError(ShatranjError):
    """Raised when the .shatranjrc configuration file is invalid.

    Example::
        raise ConfigError(f"Unknown ai-mode '{value}'")
    """
