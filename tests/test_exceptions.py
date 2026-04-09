"""
test_exceptions.py - Unit tests for custom exception hierarchy

Tests the exception classes defined in shatranj/utils/exceptions.py.
"""

import pytest

from shatranj.utils.exceptions import (AIError, BoardError, ConfigError,
                                       EvaluatorError, IllegalMoveError,
                                       InvalidMoveError, InvalidSquareError,
                                       LoadError, MissingShahError,
                                       NoMoveAvailableError, NoPieceError,
                                       PersistenceError, RulesError, SaveError,
                                       ShatranjError)


class TestBaseException:
    """Tests for the base exception class."""

    def test_shatranj_error_is_exception(self):
        """ShatranjError inherits from Exception."""
        assert issubclass(ShatranjError, Exception)

    def test_shatranj_error_can_be_raised(self):
        """ShatranjError can be raised and caught."""
        with pytest.raises(ShatranjError):
            raise ShatranjError("Test error")

    def test_shatranj_error_message(self):
        """ShatranjError stores the error message."""
        error = ShatranjError("Something went wrong")
        assert str(error) == "Something went wrong"


class TestBoardErrors:
    """Tests for board-level errors."""

    def test_board_error_inheritance(self):
        """BoardError inherits from ShatranjError."""
        assert issubclass(BoardError, ShatranjError)

    def test_invalid_square_error(self):
        """InvalidSquareError inherits from BoardError."""
        assert issubclass(InvalidSquareError, BoardError)

        error = InvalidSquareError("Square 64 is invalid")
        assert str(error) == "Square 64 is invalid"

    def test_invalid_move_error(self):
        """InvalidMoveError inherits from BoardError."""
        assert issubclass(InvalidMoveError, BoardError)

        error = InvalidMoveError("Cannot move to the same square")
        assert str(error) == "Cannot move to the same square"

    def test_no_piece_error(self):
        """NoPieceError inherits from BoardError."""
        assert issubclass(NoPieceError, BoardError)

        error = NoPieceError("No piece on square 12")
        assert str(error) == "No piece on square 12"

    def test_missing_shah_error(self):
        """MissingShahError inherits from BoardError."""
        assert issubclass(MissingShahError, BoardError)

        error = MissingShahError("Shah not found on board")
        assert str(error) == "Shah not found on board"


class TestRulesErrors:
    """Tests for rules-level errors."""

    def test_rules_error_inheritance(self):
        """RulesError inherits from ShatranjError."""
        assert issubclass(RulesError, ShatranjError)

    def test_illegal_move_error(self):
        """IllegalMoveError inherits from RulesError."""
        assert issubclass(IllegalMoveError, RulesError)

        error = IllegalMoveError("Move leaves Shah in check")
        assert str(error) == "Move leaves Shah in check"


class TestAIErrors:
    """Tests for AI errors."""

    def test_ai_error_inheritance(self):
        """AIError inherits from ShatranjError."""
        assert issubclass(AIError, ShatranjError)

    def test_no_move_available_error(self):
        """NoMoveAvailableError inherits from AIError."""
        assert issubclass(NoMoveAvailableError, AIError)

        error = NoMoveAvailableError("No legal moves for BLACK")
        assert str(error) == "No legal moves for BLACK"


class TestEvaluatorError:
    """Tests for evaluator errors."""

    def test_evaluator_error_inheritance(self):
        """EvaluatorError inherits from ShatranjError."""
        assert issubclass(EvaluatorError, ShatranjError)

    def test_evaluator_error_message(self):
        """EvaluatorError stores the error message."""
        error = EvaluatorError("Unknown mode 'invalid'")
        assert str(error) == "Unknown mode 'invalid'"


class TestPersistenceErrors:
    """Tests for persistence (save/load) errors."""

    def test_persistence_error_inheritance(self):
        """PersistenceError inherits from ShatranjError."""
        assert issubclass(PersistenceError, ShatranjError)

    def test_save_error(self):
        """SaveError inherits from PersistenceError."""
        assert issubclass(SaveError, PersistenceError)

        error = SaveError("Could not write to file")
        assert str(error) == "Could not write to file"

    def test_load_error_basic(self):
        """LoadError inherits from PersistenceError."""
        assert issubclass(LoadError, PersistenceError)

        error = LoadError("Invalid board format")
        assert str(error) == "Invalid board format"
        assert error.path == ""
        assert error.line is None

    def test_load_error_with_path(self):
        """LoadError can store a file path."""
        error = LoadError("Invalid board row", path="game.shj")
        assert str(error) == "Invalid board row | file='game.shj'"
        assert error.path == "game.shj"
        assert error.line is None

    def test_load_error_with_line(self):
        """LoadError can store a line number."""
        error = LoadError("Invalid board row", line=12)
        assert str(error) == "Invalid board row | line=12"
        assert error.path == ""
        assert error.line == 12

    def test_load_error_with_path_and_line(self):
        """LoadError can store both path and line number."""
        error = LoadError("Invalid board row", path="game.shj", line=12)
        assert str(error) == "Invalid board row | file='game.shj' | line=12"
        assert error.path == "game.shj"
        assert error.line == 12


class TestConfigError:
    """Tests for configuration errors."""

    def test_config_error_inheritance(self):
        """ConfigError inherits from ShatranjError."""
        assert issubclass(ConfigError, ShatranjError)

    def test_config_error_message(self):
        """ConfigError stores the error message."""
        error = ConfigError("Unknown ai-mode 'invalid'")
        assert str(error) == "Unknown ai-mode 'invalid'"


class TestExceptionCatching:
    """Tests for exception hierarchy and catching patterns."""

    def test_catch_base_exception(self):
        """Catching ShatranjError catches all custom exceptions."""
        with pytest.raises(ShatranjError):
            raise InvalidSquareError("Invalid")

        with pytest.raises(ShatranjError):
            raise InvalidMoveError("Invalid")

        with pytest.raises(ShatranjError):
            raise IllegalMoveError("Illegal")

        with pytest.raises(ShatranjError):
            raise LoadError("Load failed")

    def test_catch_board_error(self):
        """Catching BoardError catches board-level exceptions."""
        with pytest.raises(BoardError):
            raise InvalidSquareError("Invalid")

        with pytest.raises(BoardError):
            raise InvalidMoveError("Invalid")

        with pytest.raises(BoardError):
            raise NoPieceError("No piece")

        with pytest.raises(BoardError):
            raise MissingShahError("Missing shah")

    def test_catch_rules_error(self):
        """Catching RulesError catches rules-level exceptions."""
        with pytest.raises(RulesError):
            raise IllegalMoveError("Illegal")

    def test_catch_ai_error(self):
        """Catching AIError catches AI-level exceptions."""
        with pytest.raises(AIError):
            raise NoMoveAvailableError("No moves")

    def test_catch_persistence_error(self):
        """Catching PersistenceError catches save/load exceptions."""
        with pytest.raises(PersistenceError):
            raise SaveError("Save failed")

        with pytest.raises(PersistenceError):
            raise LoadError("Load failed")

    def test_catch_save_error_specifically(self):
        """Catching SaveError catches only save errors."""
        with pytest.raises(SaveError):
            raise SaveError("Save failed")

        with pytest.raises(LoadError):
            raise LoadError("Load failed")

    def test_load_error_with_path_and_line_formats_correctly(self):
        """LoadError __str__ formats correctly with path and line."""
        error = LoadError("Invalid move", path="save.shj", line=5)
        assert "Invalid move" in str(error)
        assert "file='save.shj'" in str(error)
        assert "line=5" in str(error)

    def test_load_error_empty_path(self):
        """LoadError with empty path doesn't include file in string."""
        error = LoadError("Error", path="", line=10)
        assert "file=" not in str(error)
        assert "line=10" in str(error)

    def test_load_error_empty_line(self):
        """LoadError with None line doesn't include line in string."""
        error = LoadError("Error", path="game.shj", line=None)
        assert "file='game.shj'" in str(error)
        assert "line" not in str(error)
