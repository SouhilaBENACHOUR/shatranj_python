"""
test_cli.py - Unit tests for the CLI

Each component is tested independently (unit tests):
  - move parsing
  - command dispatch
  - game_state (undo/redo)
  - display

Why test each method separately?
  If a test fails, we know exactly which part is broken.
  This is the principle of unit testing.

Run with:
  pytest tests/test_cli.py -v
"""

import pytest
import os
from unittest.mock import patch, MagicMock
from shatranj.domain.core.move import Move
from io import StringIO
from shatranj.presentation.cli.cli import CLI
from shatranj.presentation.cli.game_state import GameState
from shatranj.utils.constants import WHITE, BLACK, SHAH, ROOK, PAWN, FERZ
from shatranj.utils.exceptions import InvalidSquareError


class TestGameState:
    """Tests for the GameState class."""
    def setup_method(self):
        """Called before each test. Creates a fresh game state."""
        from shatranj.presentation.cli.game_state import GameState

        self.state = GameState()

    def test_initial_turn_is_white(self):
        """At the start, it's White's turn."""
        assert self.state.current_color == WHITE

    def test_apply_move_switches_turn(self):
        """After a White move, it's Black's turn."""
        # Coup : pion blanc de e2 (case 12) vers e3 (case 20)
        move = Move(
            from_square=12,
            to_square=20,
            piece_type=PAWN,
            color=WHITE,
        )
        self.state.apply_move(move)
        assert self.state.current_color == BLACK

    def test_undo_restores_turn(self):
        """After undo, it's White's turn again."""
        move = Move(
            from_square=12,  # e2
            to_square=20,  # e3
            piece_type=PAWN,
            color=WHITE,
        )
        self.state.apply_move(move)
        assert self.state.current_color == BLACK

        self.state.undo()
        assert self.state.current_color == WHITE

    def test_undo_empty_history_returns_none(self):
        """Undo with empty history returns None without crashing."""
        result = self.state.undo()
        assert result is None

    def test_redo_empty_returns_none(self):
        """Redo without prior undo returns None."""
        result = self.state.redo()
        assert result is None

    def test_history_is_empty_at_start(self):
        """History is empty at start."""
        assert self.state.get_history() == []

    def test_apply_clears_redo_stack(self):
        """Playing a new move after undo clears the redo stack."""
        move1 = Move(
            from_square=12, to_square=20, piece_type=PAWN, color=WHITE
        )
        self.state.apply_move(move1)
        self.state.undo()
        assert self.state.can_redo()

        # On joue un coup différent
        move2 = Move(
            from_square=11, to_square=19, piece_type=PAWN, color=WHITE
        )
        self.state.apply_move(move2)

        # Le redo stack doit être vide
        assert not self.state.can_redo()

    def test_apply_move_promotes_pawn_to_ferz(self):
        """A pawn on the last rank becomes a ferz."""
        from shatranj.domain.core.board import Board

        self.state.board = Board(setup=False)
        self.state.board.place_piece(PAWN, WHITE, 48)  # a7
        move = Move(from_square=48, to_square=56, piece_type=PAWN, color=WHITE)

        self.state.apply_move(move)

        assert self.state.board.get_piece_at(56) == (FERZ, WHITE)
        assert self.state.current_color == BLACK


class TestDisplay:
    """Tests for ASCII board display."""
    def test_board_to_string_has_8_rows(self):
        """The displayed board has 8 piece rows and 1 column label row."""
        from shatranj.domain.core.board import Board
        from shatranj.presentation.cli.display import board_to_string

        board = Board(setup=True)
        result = board_to_string(board)
        lines = result.strip().split("\n")
        # 8 rangs + 1 ligne de légende (a b c d e f g h)
        assert len(lines) == 9

    def test_board_to_string_contains_pieces(self):
        """Initial board contains expected pieces."""
        from shatranj.domain.core.board import Board
        from shatranj.presentation.cli.display import board_to_string

        board = Board(setup=True)
        result = board_to_string(board)
        assert "R" in result  # Tour blanche
        assert "r" in result  # Tour noire
        assert "K" in result  # Shah blanc
        assert "k" in result  # Shah noir
        assert "P" in result  # Pion blanc
        assert "p" in result  # Pion noir

    def test_board_to_string_with_color_contains_ansi_codes(self):
        """Color mode injects ANSI sequences around pieces."""
        from shatranj.domain.core.board import Board
        from shatranj.presentation.cli.display import board_to_string

        board = Board(setup=True)
        result = board_to_string(board, use_color=True)

        assert "\033[" in result

    def test_board_to_string_with_color_keeps_layout_simple(self):
        """Color mode adds a square background for readability."""
        from shatranj.domain.core.board import Board
        from shatranj.presentation.cli.display import board_to_string

        board = Board(setup=True)
        result = board_to_string(board, use_color=True)

        assert "\033[47m" not in result
        assert "\033[100m" not in result


class TestMoveParser:
    """Tests for algebraic notation."""

    def setup_method(self):
        from shatranj.domain.core.board import Board

        self.board = Board(setup=True)

    def test_algebraic_to_square_e2(self):
        """e2 doit correspondre à la case 12 (rang 1, colonne 4)."""
        from shatranj.domain.core.board import Board

        assert Board.algebraic_to_square("e2") == 12

    def test_algebraic_to_square_a1(self):
        """a1 = case 0."""
        from shatranj.domain.core.board import Board

        assert Board.algebraic_to_square("a1") == 0

    def test_algebraic_to_square_h8(self):
        """h8 = case 63."""
        from shatranj.domain.core.board import Board

        assert Board.algebraic_to_square("h8") == 63

    def test_square_to_algebraic_12(self):
        """Case 12 -> 'e2'."""
        from shatranj.domain.core.board import Board

        assert Board.square_to_algebraic(12) == "e2"

    def test_invalid_square_raises(self):
        """Une case invalide lève ValueError."""
        from shatranj.domain.core.board import Board

        with pytest.raises(InvalidSquareError):
            Board.algebraic_to_square("z9")

    def test_looks_like_move_valid(self):
        """'e2-e4' est reconnu comme un coup valide."""
        import re

        pattern = r"^[A-Za-z]?[a-h][1-8][-x][a-h][1-8]$"
        assert re.match(pattern, "e2-e4")
        assert re.match(pattern, "e2xe4")
        assert re.match(pattern, "Ng8-f6")

    def test_looks_like_move_invalid(self):
        """'hello' n'est pas un coup."""
        import re

        pattern = r"^[A-Za-z]?[a-h][1-8][-x][a-h][1-8]$"
        assert not re.match(pattern, "hello")
        assert not re.match(pattern, "new")
        assert not re.match(pattern, "e2e4")


class TestMoveValidatorIntegration:
    """Tests d'intégration entre Board et MoveValidator."""

    def setup_method(self):
        from shatranj.domain.core.board import Board
        from shatranj.domain.rules.move_validator import MoveValidator

        self.board = Board(setup=True)
        self.validator = MoveValidator()

    def test_pawn_e2_e3_is_valid(self):
        """Un pion blanc peut avancer d'une case."""

        move = Move(from_square=12, to_square=20, piece_type=PAWN, color=WHITE)
        assert self.validator.is_valid_move(self.board, move)

    def test_pawn_e2_e4_is_invalid(self):
        """Un pion ne peut pas avancer de 2 cases au Shatranj (pas de double
        pas)."""

        move = Move(from_square=12, to_square=28, piece_type=PAWN, color=WHITE)
        assert not self.validator.is_valid_move(self.board, move)

    def test_pawn_cannot_move_backward(self):
        """Un pion ne peut pas reculer."""

        # De e2 (12) vers e1 (4) : vers l'arrière
        move = Move(from_square=12, to_square=4, piece_type=PAWN, color=WHITE)
        assert not self.validator.is_valid_move(self.board, move)

    def test_move_from_empty_square_invalid(self):
        """On ne peut pas bouger depuis une case vide."""

        # La case e4 (28) est vide en position initiale
        move = Move(from_square=28, to_square=36, piece_type=PAWN, color=WHITE)
        assert not self.validator.is_valid_move(self.board, move)


class TestDoLoad:
    """Tests for the _do_load method of the CLI."""

    def setup_method(self):
        """Creates a fresh CLI before each test."""
        from shatranj.presentation.cli.cli import CLI

        self.cli = CLI()

    def _write_file(self, path, content):
        """Helper: writes a temporary file."""
        with open(path, "w", encoding="ascii") as f:
            f.write(content)

    # ----------------------------------------------------------------
    # Valid file
    # ----------------------------------------------------------------

    def test_load_valid_file(self, tmp_path):
        """Loading a valid file reconstructs the correct state."""

        content = (
            "[settings]\n"
            "verbose=false\n"
            "debug=false\n"
            "[game]\n"
            "W\n"
            "r n a f k a n r\n"
            "p p p p p p p p\n"
            "_ _ _ _ _ _ _ _\n"
            "_ _ _ _ _ _ _ _\n"
            "_ _ _ _ _ _ _ _\n"
            "_ _ _ _ _ _ _ _\n"
            "P P P P P P P P\n"
            "R N A F K A N R\n"
            "[history]\n"
        )
        save_file = tmp_path / "game.shatranj"
        self._write_file(save_file, content)

        self.cli._do_load([str(save_file)])

        assert self.cli._state is not None
        assert self.cli._state.current_color == WHITE
        assert self.cli._saved is True

    def test_load_restores_current_color_black(self, tmp_path):
        """Current player is BLACK if the file says B."""

        content = (
            "[settings]\n"
            "verbose=false\n"
            "debug=false\n"
            "[game]\n"
            "B\n"
            "r n a f k a n r\n"
            "p p p p p p p p\n"
            "_ _ _ _ _ _ _ _\n"
            "_ _ _ _ _ _ _ _\n"
            "_ _ _ _ _ _ _ _\n"
            "_ _ _ _ _ _ _ _\n"
            "P P P P P P P P\n"
            "R N A F K A N R\n"
            "[history]\n"
        )
        save_file = tmp_path / "game.shatranj"
        self._write_file(save_file, content)

        self.cli._do_load([str(save_file)])

        assert self.cli._state.current_color == BLACK

    def test_load_restores_settings(self, tmp_path):
        """Verbose and debug settings are correctly restored."""
        content = (
            "[settings]\n"
            "verbose=true\n"
            "debug=true\n"
            "[game]\n"
            "W\n"
            "r n a f k a n r\n"
            "p p p p p p p p\n"
            "_ _ _ _ _ _ _ _\n"
            "_ _ _ _ _ _ _ _\n"
            "_ _ _ _ _ _ _ _\n"
            "_ _ _ _ _ _ _ _\n"
            "P P P P P P P P\n"
            "R N A F K A N R\n"
            "[history]\n"
        )
        save_file = tmp_path / "game.shatranj"
        self._write_file(save_file, content)

        self.cli._do_load([str(save_file)])

        assert self.cli._verbose is True
        assert self.cli._debug is True

    def test_load_restores_history(self, tmp_path):
        """Move history is correctly restored from file."""
        content = (
            "[settings]\n"
            "verbose=false\n"
            "debug=false\n"
            "[game]\n"
            "B\n"
            "r n a f k a n r\n"
            "p p p p p p p p\n"
            "_ _ _ _ _ _ _ _\n"
            "_ _ _ _ _ _ _ _\n"
            "_ _ _ _ _ _ _ _\n"
            "_ _ P _ _ _ _ _\n"
            "P P _ P P P P P\n"
            "R N A F K A N R\n"
            "[history]\n"
            "W c2-c3\n"
        )
        save_file = tmp_path / "game.shatranj"
        self._write_file(save_file, content)

        self.cli._do_load([str(save_file)])

        history = self.cli._state.get_history()
        assert len(history) == 1

    def test_load_restores_history_two_moves(self, tmp_path):
        """History with 2 moves is correctly restored."""
        content = (
            "[settings]\n"
            "verbose=false\n"
            "debug=false\n"
            "[game]\n"
            "W\n"
            "r n a f k a n r\n"
            "p p p _ p p p p\n"
            "_ _ _ p _ _ _ _\n"
            "_ _ _ _ _ _ _ _\n"
            "_ _ _ _ P _ _ _\n"
            "_ _ _ _ _ _ _ _\n"
            "P P P P _ P P P\n"
            "R N A F K A N R\n"
            "[history]\n"
            "W e2-e4 B d7-d6\n"
        )
        save_file = tmp_path / "game.shatranj"
        self._write_file(save_file, content)

        self.cli._do_load([str(save_file)])

        history = self.cli._state.get_history()
        assert len(history) == 2

    def test_load_with_comments(self, tmp_path):
        """Comments in the file are ignored."""
        content = (
            "# This is a comment\n"
            "[settings]\n"
            "verbose=false\n"
            "# another comment\n"
            "debug=false\n"
            "[game]\n"
            "W\n"
            "r n a f k a n r\n"
            "p p p p p p p p\n"
            "_ _ _ _ _ _ _ _\n"
            "_ _ _ _ _ _ _ _\n"
            "_ _ _ _ _ _ _ _\n"
            "_ _ _ _ _ _ _ _\n"
            "P P P P P P P P\n"
            "R N A F K A N R\n"
            "[history]\n"
        )
        save_file = tmp_path / "game.shatranj"
        self._write_file(save_file, content)

        self.cli._do_load([str(save_file)])

        assert self.cli._state is not None

    # ----------------------------------------------------------------
    # Errors
    # ----------------------------------------------------------------

    def test_load_no_args(self):
        """No argument provided shows an error."""
        from unittest.mock import patch
        from io import StringIO

        stderr = StringIO()
        with patch("sys.stderr", stderr):
            self.cli._do_load([])

        assert "Usage" in stderr.getvalue()
        assert self.cli._state is None

    def test_load_file_not_found(self):
        """Non-existent file shows an error."""
        from unittest.mock import patch
        from io import StringIO

        stderr = StringIO()
        with patch("sys.stderr", stderr):
            self.cli._do_load(["fichier_inexistant.shatranj"])

        assert "Could not open" in stderr.getvalue()
        assert self.cli._state is None

    def test_load_invalid_color(self, tmp_path):
        """Invalid color in file shows an error."""
        from unittest.mock import patch
        from io import StringIO

        content = (
            "[settings]\n"
            "verbose=false\n"
            "debug=false\n"
            "[game]\n"
            "X\n"  # invalid color
            "r n a f k a n r\n"
            "p p p p p p p p\n"
            "_ _ _ _ _ _ _ _\n"
            "_ _ _ _ _ _ _ _\n"
            "_ _ _ _ _ _ _ _\n"
            "_ _ _ _ _ _ _ _\n"
            "P P P P P P P P\n"
            "R N A F K A N R\n"
            "[history]\n"
        )
        save_file = tmp_path / "game.shatranj"
        self._write_file(save_file, content)

        stderr = StringIO()
        with patch("sys.stderr", stderr):
            self.cli._do_load([str(save_file)])

        assert "Invalid player color" in stderr.getvalue()

    def test_load_invalid_board_row(self, tmp_path):
        """Invalid board row shows an error."""
        from unittest.mock import patch
        from io import StringIO

        content = (
            "[settings]\n"
            "verbose=false\n"
            "debug=false\n"
            "[game]\n"
            "W\n"
            "r n a f k a n r\n"
            "p p p p p p p\n"  # only 7 pieces
            "_ _ _ _ _ _ _ _\n"
            "_ _ _ _ _ _ _ _\n"
            "_ _ _ _ _ _ _ _\n"
            "_ _ _ _ _ _ _ _\n"
            "P P P P P P P P\n"
            "R N A F K A N R\n"
            "[history]\n"
        )
        save_file = tmp_path / "game.shatranj"
        self._write_file(save_file, content)

        stderr = StringIO()
        with patch("sys.stderr", stderr):
            self.cli._do_load([str(save_file)])

        assert "Invalid board row" in stderr.getvalue()

    def test_load_invalid_piece_symbol(self, tmp_path):
        """Unknown piece symbol shows an error."""
        from unittest.mock import patch
        from io import StringIO

        content = (
            "[settings]\n"
            "verbose=false\n"
            "debug=false\n"
            "[game]\n"
            "W\n"
            "r n a f k a n r\n"
            "p p p p p p p p\n"
            "_ _ _ _ _ _ _ _\n"
            "_ _ _ _ _ _ _ _\n"
            "_ _ _ _ _ _ _ _\n"
            "_ _ _ _ _ _ _ _\n"
            "P P P P P P P X\n"  # X is invalid
            "R N A F K A N R\n"
            "[history]\n"
        )
        save_file = tmp_path / "game.shatranj"
        self._write_file(save_file, content)

        stderr = StringIO()
        with patch("sys.stderr", stderr):
            self.cli._do_load([str(save_file)])

        assert "Unknown piece symbol" in stderr.getvalue()

    def test_load_invalid_move_in_history(self, tmp_path):
        """Invalid move in history shows an error."""
        from unittest.mock import patch
        from io import StringIO

        content = (
            "[settings]\n"
            "verbose=false\n"
            "debug=false\n"
            "[game]\n"
            "B\n"
            "r n a f k a n r\n"
            "p p p p p p p p\n"
            "_ _ _ _ _ _ _ _\n"
            "_ _ _ _ _ _ _ _\n"
            "_ _ _ _ _ _ _ _\n"
            "_ _ _ _ _ _ _ _\n"
            "P P P P P P P P\n"
            "R N A F K A N R\n"
            "[history]\n"
            "W invalid_move\n"  # invalid move
        )
        save_file = tmp_path / "game.shatranj"
        self._write_file(save_file, content)

        stderr = StringIO()
        with patch("sys.stderr", stderr):
            self.cli._do_load([str(save_file)])

        assert "Invalid move in history" in stderr.getvalue()


class TestCliMoveLegality:
    """Tests for full move legality checks in CLI."""

    def test_reject_shah_move_into_attacked_square(self):

        cli = CLI()
        cli._state = GameState()
        board = cli._state.board
        board.clear()

        # White Shah on e1, black rook on e8 attacks the e-file.
        board.place_piece(SHAH, WHITE, 4)  # e1
        board.place_piece(SHAH, BLACK, 63)  # h8
        board.place_piece(ROOK, BLACK, 60)  # e8
        cli._state.current_color = WHITE

        stderr = StringIO()
        with patch("sys.stderr", stderr):
            cli._do_play_move("e1-e2")

        assert "Illegal move: e1-e2" in stderr.getvalue()
        assert board.get_piece_at(4) == (SHAH, WHITE)
        assert board.get_piece_at(12) is None
        assert cli._state.current_color == WHITE


class TestCliAIVsAI:
    """Tests for AI vs AI mode."""

    def test_new_ai_vs_ai_configures_two_ai_players(self):

        cli = CLI()
        with (
            patch("shatranj.presentation.cli.cli.print_board"),
            patch.object(CLI, "_auto_play_ai_turns") as auto_play,
        ):
            cli._do_new(["ai-vs-ai"])

        assert set(cli._ai_players.keys()) == {WHITE, BLACK}
        auto_play.assert_called_once()

    def test_auto_play_ai_turns_applies_two_plies(self):

        class ScriptedAI:
            def __init__(self, color: str, scripted_move: Move) -> None:
                self.color = color
                self._scripted_move = scripted_move

            def choose_move(self, board):
                return self._scripted_move

        cli = CLI()
        cli._state = GameState()
        state = cli._state
        cli._ai_players = {
            WHITE: ScriptedAI(WHITE, Move(12, 20, PAWN, WHITE)),  # e2-e3
            BLACK: ScriptedAI(BLACK, Move(52, 44, PAWN, BLACK)),  # e7-e6
        }

        with patch("shatranj.presentation.cli.cli.print_board"):
            cli._auto_play_ai_turns(max_plies=2)

        history = state.get_history()
        assert len(history) == 2
        assert history[0].from_square == 12 and history[0].to_square == 20
        assert history[1].from_square == 52 and history[1].to_square == 44
        assert cli._state is None

    def test_do_ai_move_displays_piece_name(self, capsys):

        class ScriptedAI:
            def __init__(self, scripted_move: Move) -> None:
                self._scripted_move = scripted_move

            def choose_move(self, board):
                return self._scripted_move

        cli = CLI()
        cli._state = GameState()
        cli._ai_players = {
            WHITE: ScriptedAI(Move(12, 20, PAWN, WHITE)),
        }

        with patch("shatranj.presentation.cli.cli.print_board"):
            cli._do_ai_move()

        out = capsys.readouterr().out
        assert "AI plays: pawn e2-e3" in out


class TestCliDrawRules:
    """Tests for draw rules used to stop infinite AI loops."""

    def test_threefold_repetition_is_detected_and_ends_game(self):

        cli = CLI()
        cli._state = GameState()
        board = cli._state.board
        board.clear()
        board.place_piece(SHAH, WHITE, 4)  # e1
        board.place_piece(ROOK, WHITE, 0)  # a1
        board.place_piece(SHAH, BLACK, 60)  # e8
        board.place_piece(ROOK, BLACK, 63)  # h8
        cli._state.current_color = WHITE

        cycle = [
            Move(4, 12, SHAH, WHITE),  # e1-e2
            Move(60, 52, SHAH, BLACK),  # e8-e7
            Move(12, 4, SHAH, WHITE),  # e2-e1
            Move(52, 60, SHAH, BLACK),  # e7-e8
        ]
        for move in cycle + cycle:
            cli._state.apply_move(move)

        assert cli._is_draw_by_threefold_repetition()
        assert cli._check_game_over()
        assert cli._state is None

    def test_fifty_move_rule_detected(self):

        cli = CLI()
        cli._state = GameState()
        cli._state._history = []

        for i in range(100):
            color = WHITE if i % 2 == 0 else BLACK
            cli._state._history.append((Move(4, 12, SHAH, color), {}))

        assert cli._is_draw_by_fifty_move_rule()


class TestCliBlitzMode:
    """Tests for blitz mode timing in the CLI."""

    def test_enable_blitz_initializes_timers_on_new_game(self):
        cli = CLI()
        cli.enable_blitz(5)

        with (
            patch("shatranj.presentation.cli.cli.print_board"),
            patch.object(CLI, "_auto_play_ai_turns"),
        ):
            cli._do_new([])

        assert cli._clock_seconds[WHITE] == 300.0
        assert cli._clock_seconds[BLACK] == 300.0
        assert cli._turn_started_at is not None

    def test_show_time_displays_remaining_time_in_blitz(self, capsys):
        cli = CLI()
        cli.enable_blitz(3)
        cli._state = GameState()
        cli._clock_seconds[WHITE] = 179.1
        cli._clock_seconds[BLACK] = 95.1

        cli._do_show_time()

        out = capsys.readouterr().out
        assert "White: 03:00" in out
        assert "Black: 01:36" in out
        assert "Status: running (WHITE to move)" in out

    def test_pause_toggles_blitz_timer(self, capsys):
        cli = CLI()
        cli.enable_blitz(3)
        cli._state = GameState()
        cli._start_turn_timer()

        cli._do_pause([])
        paused = capsys.readouterr().out
        assert "Blitz timer paused." in paused
        assert cli._timer_paused is True
        assert cli._turn_started_at is None

        cli._do_pause([])
        resumed = capsys.readouterr().out
        assert "Blitz timer resumed." in resumed
        assert cli._timer_paused is False
        assert cli._turn_started_at is not None

    def test_timeout_ends_the_game(self, capsys):
        cli = CLI()
        cli.enable_blitz(1)
        cli._state = GameState()
        cli._clock_seconds[WHITE] = 0.05

        with patch(
            "shatranj.presentation.cli.cli.time.monotonic",
            side_effect=[10.0, 10.2],
        ):
            cli._start_turn_timer()
            timed_out = cli._consume_turn_time()

        out = capsys.readouterr().out
        assert timed_out is True
        assert "Time out! BLACK wins!" in out
        assert cli._state is None


class TestFormatClock:
    """Tests for _format_clock method."""

    def setup_method(self):
        self.cli = CLI()

    def test_zero(self):
        """Format zero seconds."""
        assert self.cli._format_clock(0.0) == "00:00"

    def test_one_minute(self):
        """Format 60 seconds."""
        assert self.cli._format_clock(60.0) == "01:00"

    def test_ninety_seconds(self):
        """Format 90 seconds (1:30)."""
        assert self.cli._format_clock(90.0) == "01:30"

    def test_negative_clamps(self):
        """Negative seconds clamp to zero."""
        assert self.cli._format_clock(-5.0) == "00:00"

    def test_rounds_up(self):
        """Seconds are rounded up to nearest integer."""
        assert self.cli._format_clock(9.1) == "00:10"


class TestDispatch:
    """Tests for _dispatch command routing."""

    def setup_method(self):
        self.cli = CLI()
        self.cli._state = GameState()

    def test_dispatch_show_board(self):
        """'show board' routes to _do_show_board."""
        with patch.object(self.cli, "_do_show_board") as mock:
            self.cli._dispatch("show board")
            mock.assert_called_once()

    def test_dispatch_show_history(self):
        """'show history' routes to _do_show_history."""
        with patch.object(self.cli, "_do_show_history") as mock:
            self.cli._dispatch("show history")
            mock.assert_called_once()

    def test_dispatch_show_time(self):
        """'show time' routes to _do_show_time."""
        with patch.object(self.cli, "_do_show_time") as mock:
            self.cli._dispatch("show time")
            mock.assert_called_once()

    def test_dispatch_show_configuration(self):
        """'show configuration' routes to _do_show_configuration."""
        with patch.object(self.cli, "_do_show_configuration") as mock:
            self.cli._dispatch("show configuration")
            mock.assert_called_once()

    def test_dispatch_show_unknown_subcommand(self):
        """Unknown 'show' subcommand prints error."""
        stderr = StringIO()
        with patch("sys.stderr", stderr):
            self.cli._dispatch("show unknown")
        assert "Unknown subcommand" in stderr.getvalue()

    def test_dispatch_unknown_command(self):
        """Unknown command prints error."""
        stderr = StringIO()
        with patch("sys.stderr", stderr):
            self.cli._dispatch("foobar")
        assert "Unknown command" in stderr.getvalue()

    def test_dispatch_move(self):
        """Move notation routes to _do_play_move."""
        with patch.object(self.cli, "_do_play_move") as mock:
            self.cli._dispatch("e2-e3")
            mock.assert_called_once_with("e2-e3")


class TestParseMoveEdgeCases:
    """Edge cases for _parse_move method."""

    def setup_method(self):
        self.cli = CLI()
        self.cli._state = GameState()

    def test_invalid_format_returns_none(self):
        """Invalid format like 'e2e4' returns None."""
        stderr = StringIO()
        with patch("sys.stderr", stderr):
            result = self.cli._parse_move("e2e4")
        assert result is None

    def test_invalid_square_returns_none(self):
        """Square 'z9' is invalid."""
        stderr = StringIO()
        with patch("sys.stderr", stderr):
            result = self.cli._parse_move("z9-a1")
        assert result is None

    def test_no_piece_on_square_returns_none(self):
        """Moving from empty square returns None."""
        stderr = StringIO()
        with patch("sys.stderr", stderr):
            result = self.cli._parse_move("e5-e6")
        assert result is None

    def test_piece_prefix_stripped(self):
        """Piece prefix like 'P' is stripped."""
        result = self.cli._parse_move("Pe2-e3")
        assert result is not None
        assert result.from_square == 12
        assert result.to_square == 20

    def test_valid_capture_move(self):
        """Capture notation 'x' is parsed correctly."""
        board = self.cli._state.board
        board.clear()
        board.place_piece(PAWN, WHITE, 12)
        board.place_piece(PAWN, BLACK, 21)
        result = self.cli._parse_move("e2xf3")
        assert result is not None
        assert result.captured_piece == PAWN


class TestDoPlayMoveEdgeCases:
    """Edge cases for _do_play_move method."""

    def setup_method(self):
        self.cli = CLI()
        self.cli._state = GameState()

    def test_no_game_in_progress(self):
        """Playing a move without a game shows error."""
        self.cli._state = None
        stderr = StringIO()
        with patch("sys.stderr", stderr):
            self.cli._do_play_move("e2-e3")
        assert "No game in progress" in stderr.getvalue()

    def test_wrong_color_turn(self):
        """Playing with wrong color shows error."""
        self.cli._state.current_color = WHITE
        stderr = StringIO()
        with patch("sys.stderr", stderr):
            with patch.object(self.cli, "_parse_move",
                              return_value=Move(52, 44, PAWN, BLACK)):
                self.cli._do_play_move("e7-e6")
        assert "turn" in stderr.getvalue().lower()

    def test_legal_move_applied(self):
        """Legal move is applied and turn switches."""
        with patch("shatranj.presentation.cli.cli.print_board"):
            self.cli._do_play_move("e2-e3")
        assert self.cli._state.current_color == BLACK

    def test_illegal_move_rejected(self):
        """Illegal move is rejected with error message."""
        stderr = StringIO()
        with patch("sys.stderr", stderr):
            self.cli._do_play_move("e2-e5")
        assert "Illegal move" in stderr.getvalue()


class TestDoNewEdgeCases:
    """Edge cases for _do_new method."""

    def setup_method(self):
        self.cli = CLI()

    def test_new_human_vs_human(self):
        """Default new game is human vs human."""
        with (
            patch("shatranj.presentation.cli.cli.print_board"),
            patch.object(self.cli, "_auto_play_ai_turns"),
        ):
            self.cli._do_new([])
        assert self.cli._state is not None
        assert self.cli._ai_players == {}

    def test_new_ai_black_alphabeta(self):
        """AI as black with alphabeta algorithm."""
        with (
            patch("shatranj.presentation.cli.cli.print_board"),
            patch.object(self.cli, "_auto_play_ai_turns"),
        ):
            self.cli._do_new(["ai", "BLACK", "alphabeta", "3", "advanced"])
        assert BLACK in self.cli._ai_players

    def test_new_unknown_algorithm(self):
        """Unknown algorithm shows error."""
        stderr = StringIO()
        with patch("sys.stderr", stderr):
            self.cli._do_new(["ai", "BLACK", "unknown_algo"])
        assert "Unknown algorithm" in stderr.getvalue()

    def test_new_invalid_depth(self):
        """Invalid depth value shows error."""
        stderr = StringIO()
        with patch("sys.stderr", stderr):
            self.cli._do_new(["ai", "BLACK", "alphabeta", "abc"])
        assert "Invalid depth" in stderr.getvalue()

    def test_new_unknown_scoring(self):
        """Unknown scoring function shows error."""
        stderr = StringIO()
        with patch("sys.stderr", stderr):
            self.cli._do_new(["ai", "BLACK", "alphabeta", "3", "unknown"])
        assert "Unknown scoring" in stderr.getvalue()

    def test_new_with_blitz(self):
        """New game with blitz mode enabled."""
        self.cli.enable_blitz(5)
        with (
            patch("shatranj.presentation.cli.cli.print_board"),
            patch.object(self.cli, "_auto_play_ai_turns"),
        ):
            self.cli._do_new([])
        assert self.cli._clock_seconds[WHITE] == 300.0


class TestDoQuit:
    """Tests for _do_quit method."""

    def test_quit_no_game(self):
        """Quit without game just exits."""
        cli = CLI()
        cli._running = True
        cli._do_quit([])
        assert cli._running is False

    def test_quit_saved_game_no_prompt(self):
        """Quit with saved game exits without prompt."""
        cli = CLI()
        cli._running = True
        cli._state = GameState()
        cli._saved = True
        cli._do_quit([])
        assert cli._running is False

    def test_quit_unsaved_game_user_says_no(self):
        """Quit with unsaved game prompts user."""
        cli = CLI()
        cli._running = True
        cli._state = GameState()
        cli._saved = False
        with patch("builtins.input", return_value="n"):
            cli._do_quit([])
        assert cli._running is False


class TestDoHelp:
    """Tests for _do_help method."""

    def setup_method(self):
        self.cli = CLI()

    def test_general_help(self, capsys):
        """General help shows all commands."""
        self.cli._do_help([])
        out = capsys.readouterr().out
        assert "new" in out
        assert "quit" in out

    def test_command_help_new(self, capsys):
        """Help for 'new' command shows syntax."""
        self.cli._do_help(["new"])
        out = capsys.readouterr().out
        assert "new" in out.lower()

    def test_command_help_unknown(self):
        """Help for unknown command shows error."""
        stderr = StringIO()
        with patch("sys.stderr", stderr):
            self.cli._do_help(["unknown_cmd"])
        assert "Unknown command" in stderr.getvalue()


class TestDoShowCommands:
    """Tests for display commands: board, history, configuration."""

    def setup_method(self):
        self.cli = CLI()
        self.cli._state = GameState()

    def test_show_board_no_game(self):
        """Show board without game shows error."""
        self.cli._state = None
        stderr = StringIO()
        with patch("sys.stderr", stderr):
            self.cli._do_show_board()
        assert "No game" in stderr.getvalue()

    def test_show_history_no_game(self):
        """Show history without game shows error."""
        self.cli._state = None
        stderr = StringIO()
        with patch("sys.stderr", stderr):
            self.cli._do_show_history()
        assert "No game" in stderr.getvalue()

    def test_show_history_empty(self, capsys):
        """Empty history shows message."""
        self.cli._do_show_history()
        out = capsys.readouterr().out
        assert "No moves" in out

    def test_show_history_with_moves(self, capsys):
        """History shows moves after they are played."""
        move = Move(12, 20, PAWN, WHITE)
        self.cli._state.apply_move(move)
        self.cli._do_show_history()
        out = capsys.readouterr().out
        assert "e2" in out

    def test_show_configuration(self, capsys):
        """Configuration shows current settings."""
        self.cli._do_show_configuration()
        out = capsys.readouterr().out
        assert "verbose" in out


class TestUndoRedoEdgeCases:
    """Edge cases for undo and redo operations."""

    def setup_method(self):
        self.cli = CLI()
        self.cli._state = GameState()

    def test_undo_no_game(self):
        """Undo without game shows error."""
        self.cli._state = None
        stderr = StringIO()
        with patch("sys.stderr", stderr):
            self.cli._do_undo([])
        assert "No game" in stderr.getvalue()

    def test_undo_invalid_n(self):
        """Undo with invalid number shows error."""
        stderr = StringIO()
        with patch("sys.stderr", stderr):
            self.cli._do_undo(["abc"])
        assert "Invalid number" in stderr.getvalue()

    def test_redo_no_game(self):
        """Redo without game shows error."""
        self.cli._state = None
        stderr = StringIO()
        with patch("sys.stderr", stderr):
            self.cli._do_redo([])
        assert "No game" in stderr.getvalue()

    def test_undo_then_redo(self):
        """Undo then redo restores the move."""
        move = Move(12, 20, PAWN, WHITE)
        self.cli._state.apply_move(move)
        with patch("shatranj.presentation.cli.cli.print_board"):
            self.cli._do_undo([])
            self.cli._do_redo([])
        assert self.cli._state.current_color == BLACK


class TestDoHint:
    """Tests for hint command."""

    def setup_method(self):
        self.cli = CLI()

    def test_hint_no_game(self):
        """Hint without game shows error."""
        self.cli._state = None
        stderr = StringIO()
        with patch("sys.stderr", stderr):
            self.cli._do_hint([])
        assert "No game" in stderr.getvalue()

    def test_hint_shows_move(self, capsys):
        """Hint shows a suggested move."""
        self.cli._state = GameState()
        self.cli._do_hint([])
        out = capsys.readouterr().out
        assert "Hint:" in out

    def test_hint_uses_ai_best_move(self, capsys):
        """Hint should use the AI, not just the first legal move."""
        from shatranj.domain.core.board import Board

        board = Board(setup=False)
        board.place_piece(SHAH, WHITE, 0)  # a1
        board.place_piece(ROOK, WHITE, 1)  # b1
        board.place_piece(SHAH, BLACK, 63)  # h8
        board.place_piece(PAWN, BLACK, 2)  # c1

        self.cli._state = GameState()
        self.cli._state.board = board
        self.cli._state.current_color = WHITE
        self.cli._state._history = []
        self.cli._state._redo_stack = []

        self.cli._do_hint([])
        out = capsys.readouterr().out

        assert "Hint: rook b1xc1" in out


class TestDoSave:
    """Tests for save game functionality."""

    def setup_method(self):
        self.cli = CLI()
        self.cli._state = GameState()

    def test_save_no_game(self):
        """Save without game shows error."""
        self.cli._state = None
        stderr = StringIO()
        with patch("sys.stderr", stderr):
            self.cli._do_save(["game.shj"])
        assert "No game" in stderr.getvalue()

    def test_save_no_path(self):
        """Save without filename shows usage."""
        stderr = StringIO()
        with patch("sys.stderr", stderr):
            self.cli._do_save([])
        assert "Usage" in stderr.getvalue()

    def test_save_and_load_roundtrip(self, tmp_path):
        """Save then load restores the same game state."""
        path = str(tmp_path / "game.shj")
        move = Move(12, 20, PAWN, WHITE)
        self.cli._state.apply_move(move)
        self.cli._do_save([path])
        assert os.path.exists(path)

        cli2 = CLI()
        cli2._do_load([path])
        assert cli2._state is not None
        assert cli2._state.current_color == BLACK


class TestDoSet:
    """Tests for configuration commands."""

    def setup_method(self):
        self.cli = CLI()

    def test_set_verbose_true(self):
        """Set verbose to true."""
        self.cli._do_set(["verbose=true"])
        assert self.cli._verbose is True

    def test_set_verbose_false(self):
        """Set verbose to false."""
        self.cli._verbose = True
        self.cli._do_set(["verbose=false"])
        assert self.cli._verbose is False

    def test_set_no_args(self):
        """Set without arguments shows usage."""
        stderr = StringIO()
        with patch("sys.stderr", stderr):
            self.cli._do_set([])
        assert "Usage" in stderr.getvalue()

    def test_set_invalid_format(self):
        """Invalid format shows error."""
        stderr = StringIO()
        with patch("sys.stderr", stderr):
            self.cli._do_set(["verbosefalse"])
        assert "Invalid format" in stderr.getvalue()

    def test_set_unknown_param(self):
        """Unknown parameter shows error."""
        stderr = StringIO()
        with patch("sys.stderr", stderr):
            self.cli._do_set(["unknown=value"])
        assert "Unknown parameter" in stderr.getvalue()


class TestCompleter:
    """Tests for command completion."""

    def setup_method(self):
        self.cli = CLI()

    def test_completer_new(self):
        """Complete 'ne' to 'new'."""
        assert self.cli._completer("ne", 0) == "new"

    def test_completer_show_multiple(self):
        """Multiple completions for 'show'."""
        results = []
        i = 0
        while True:
            r = self.cli._completer("show", i)
            if r is None:
                break
            results.append(r)
            i += 1
        assert "show board" in results

    def test_completer_no_match(self):
        """No match returns None."""
        assert self.cli._completer("zzz", 0) is None


class TestStripComments:
    """Tests for comment stripping utility."""

    def setup_method(self):
        self.cli = CLI()

    def test_inline_comment_removed(self):
        """Inline # comments are removed."""
        result = self.cli._strip_comments("hello # comment\nworld\n")
        assert result == ["hello", "world"]

    def test_empty_lines_ignored(self):
        """Empty lines are filtered out."""
        result = self.cli._strip_comments("\n\nhello\n\n")
        assert result == ["hello"]

    def test_no_comment(self):
        """Text without comments passes through."""
        result = self.cli._strip_comments("[settings]\nverbose=false\n")
        assert result == ["[settings]", "verbose=false"]


class TestFormatAiDetails:
    """Tests for AI details formatting."""

    def setup_method(self):
        self.cli = CLI()

    def test_no_search_attribute(self):
        """AI without search returns empty string."""
        ai = MagicMock(spec=[])
        result = self.cli._format_ai_details(ai)
        assert result == ""

    def test_with_depth_and_scoring(self):
        """AI with depth and scoring shows both."""
        search = MagicMock()
        search._depth = 4
        ai = MagicMock()
        ai._search = search
        ai.scoring = "advanced"
        result = self.cli._format_ai_details(ai)
        assert "4" in result
        assert "advanced" in result


class TestDoContest:
    """Tests for contest mode."""

    def test_contest_invalid_file_returns_1(self, tmp_path):
        """Invalid file returns error code 1."""
        cli = CLI()
        result = cli._do_contest(path=str(tmp_path / "missing.shj"))
        assert result == 1


class TestFormatClockExtended:
    """Additional tests for _format_clock method."""

    def setup_method(self):
        self.cli = CLI()

    def test_format_clock_rounds_correctly(self):
        assert self.cli._format_clock(9.1) == "00:10"
        assert self.cli._format_clock(9.0) == "00:09"

    def test_format_clock_large_value(self):
        assert self.cli._format_clock(3661) == "61:01"


class TestUndoRedoHumanVsAI:
    """Tests for undo/redo in human vs AI mode."""

    def setup_method(self):
        self.cli = CLI()
        self.cli._state = GameState()

    def test_undo_in_human_vs_ai_undoes_two_moves(self):
        self.cli._ai_players[BLACK] = MagicMock()

        self.cli._state.apply_move(Move(12, 20, PAWN, WHITE))
        self.cli._state.apply_move(Move(52, 44, PAWN, BLACK))

        with patch("shatranj.presentation.cli.cli.print_board"):
            self.cli._do_undo(["1"])

        assert self.cli._state.get_history() == []

    def test_undo_with_n_greater_than_history(self, capsys):
        self.cli._state.apply_move(Move(12, 20, PAWN, WHITE))

        self.cli._do_undo(["5"])
        out = capsys.readouterr().out
        assert "undid 1 move" in out


class TestDoNewUnsavedConfirmation:
    """Tests for new game confirmation when unsaved."""

    def setup_method(self):
        self.cli = CLI()

    def test_new_asks_confirmation_when_unsaved(self):
        self.cli._state = GameState()
        self.cli._saved = False

        with patch("builtins.input", return_value="y"):
            with patch("shatranj.presentation.cli.cli.print_board"):
                with patch.object(self.cli, "_auto_play_ai_turns"):
                    self.cli._do_new([])

        assert self.cli._state is not None

    def test_new_cancelled_when_user_says_no(self):
        self.cli._state = GameState()
        self.cli._saved = False

        with patch("builtins.input", return_value="n"):
            with patch("builtins.print") as mock_print:
                self.cli._do_new([])
                mock_print.assert_any_call("New game cancelled.")


class TestDoQuitSaveFlow:
    """Tests for save flow when quitting."""

    def setup_method(self):
        self.cli = CLI()
        self.cli._state = GameState()
        self.cli._saved = False
        self.cli._running = True

    def test_quit_unsaved_user_saves_success(self):
        with patch("builtins.input", side_effect=["y", "test.sav"]):
            with patch.object(self.cli, "_save_to_file", return_value=True):
                self.cli._do_quit([])

        assert self.cli._running is False

    def test_quit_unsaved_save_fails_then_succeeds(self):
        with patch(
            "builtins.input",
            side_effect=["y", "fail.sav", "y", "ok.sav"]
        ):
            with patch.object(
                self.cli, "_save_to_file",
                side_effect=[False, True]
            ):
                self.cli._do_quit([])

        assert self.cli._running is False


class TestDispatchEdgeCases:
    """Edge cases for command dispatch."""

    def setup_method(self):
        self.cli = CLI()
        self.cli._state = GameState()

    def test_dispatch_q_quits(self):
        self.cli._running = True
        with patch.object(self.cli, "_do_quit") as mock:
            self.cli._dispatch("q")
            mock.assert_called_once()

    def test_dispatch_empty_input(self):
        self.cli._dispatch("")  # should not crash


class TestStripCommentsBlock:
    """Tests for block comment stripping."""

    def setup_method(self):
        self.cli = CLI()

    def test_block_comment_multiline(self):
        content = "[settings]\n{ multi\nline\ncomment }\nverbose=true\n"
        result = self.cli._strip_comments(content)
        assert result == ["[settings]", "verbose=true"]

    def test_nested_block_comments_not_supported(self):
        content = "[settings]\n{ outer { inner } }\nverbose=true\n"
        result = self.cli._strip_comments(content)
        assert any("verbose" in line for line in result)


class TestCliAITimeout:
    """Tests for AI timeout during blitz."""

    def test_ai_move_aborts_on_timeout(self):
        cli = CLI()
        cli.enable_blitz(1)
        cli._state = GameState()
        cli._ai_players[WHITE] = MagicMock()
        cli._clock_seconds[WHITE] = 0.5
        cli._turn_started_at = 1000.0

        with patch("time.monotonic", return_value=1001.0):
            with patch("builtins.print") as mock_print:
                cli._do_ai_move()
                assert any(
                    "Time out" in str(call)
                    for call in mock_print.call_args_list
                )


class TestDoSaveEdgeCases:
    """Edge cases for save command."""

    def setup_method(self):
        self.cli = CLI()
        self.cli._state = GameState()

    def test_save_without_filename(self):
        cli = CLI()
        cli._state = GameState()

        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            cli._do_save([])

        assert "Usage" in mock_stderr.getvalue()


class TestDoSetExtended:
    """Extended tests for set command with boolean variants."""

    def setup_method(self):
        self.cli = CLI()

    @pytest.mark.parametrize("value", ["true", "yes", "1"])
    def test_set_verbose_accepts_truthy_values(self, value):
        self.cli._do_set([f"verbose={value}"])
        assert self.cli._verbose is True

    @pytest.mark.parametrize("value", ["false", "no", "0", "off"])
    def test_set_verbose_accepts_falsy_values(self, value):
        self.cli._verbose = True
        self.cli._do_set([f"verbose={value}"])
        assert self.cli._verbose is False


class TestDoShowTimeEdgeCases:
    """Edge cases for show time command."""

    def setup_method(self):
        self.cli = CLI()

    def test_show_time_without_blitz(self, capsys):
        self.cli._blitz_enabled = False
        self.cli._state = GameState()

        self.cli._do_show_time()
        out = capsys.readouterr().out
        assert "only available in blitz mode" in out


class TestDoPauseEdgeCases:
    """Edge cases for pause command."""

    def setup_method(self):
        self.cli = CLI()

    def test_pause_without_blitz(self, capsys):
        self.cli._blitz_enabled = False
        self.cli._state = GameState()

        self.cli._do_pause([])
        out = capsys.readouterr().out
        assert "only available in blitz mode" in out
