"""Custom exception hierarchy for Shatranj."""


class ShatranjError(Exception):
    """Base exception for all Shatranj errors."""


class BoardError(ShatranjError):
    """Raised for any invalid operation on the board."""


class InvalidSquareError(BoardError):
    """Raised when a square index or notation is invalid."""


class InvalidMoveError(BoardError):
    """Raised when a move cannot be applied on the board."""


class NoPieceError(BoardError):
    """Raised when an operation expects a piece on a square but finds none."""


class MissingShahError(BoardError):
    """Raised when a Shah cannot be found on the board."""


class RulesError(ShatranjError):
    """Raised when a game-rule constraint is violated."""


class IllegalMoveError(RulesError):
    """Raised when a move leaves the Shah in check."""


class AIError(ShatranjError):
    """Raised when the AI engine encounters an unexpected situation."""


class NoMoveAvailableError(AIError):
    """Raised when the AI finds no legal move."""


class EvaluatorError(ShatranjError):
    """Raised when an unknown evaluation mode is requested."""


class PersistenceError(ShatranjError):
    """Base class for file I/O errors."""


class SaveError(PersistenceError):
    """Raised when writing a save file fails."""


class LoadError(PersistenceError):
    """Raised when reading or parsing a save file fails."""

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


class ConfigError(ShatranjError):
    """Raised when the configuration file is invalid."""
