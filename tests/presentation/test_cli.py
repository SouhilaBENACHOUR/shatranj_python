"""
test_cli.py - Tests unitaires pour le CLI

On teste chaque composant indépendamment (unitaire) :
  - le parsing de coups
  - le dispatch des commandes
  - game_state (undo/redo)
  - display

Pourquoi tester chaque méthode séparément ?
  Si un test échoue, on sait exactement quelle partie est cassée.
  C'est le principe des tests unitaires.

Lancement :
  pytest tests/test_cli.py -v
"""

import pytest
from unittest.mock import patch, MagicMock


class TestGameState:
    """Tests pour la classe GameState."""

    def setup_method(self):
        """Appelé avant chaque test. Crée un état de jeu frais."""
        from shatranj.presentation.cli.game_state import GameState        
        self.state = GameState()

    def test_initial_turn_is_white(self):
        """Au début, c'est aux blancs de jouer."""
        from shatranj.utils.constants import WHITE
        assert self.state.current_color == WHITE

    def test_apply_move_switches_turn(self):
        """Après un coup blanc, c'est aux noirs de jouer."""
        from shatranj.utils.constants import WHITE, BLACK
        from shatranj.domain.core.move import Move
        from shatranj.utils.constants import PAWN

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
        """Après undo, c'est à nouveau aux blancs de jouer."""
        from shatranj.utils.constants import WHITE, BLACK
        from shatranj.domain.core.move import Move
        from shatranj.utils.constants import PAWN

        move = Move(
            from_square=12,  # e2
            to_square=20,    # e3
            piece_type=PAWN,
            color=WHITE,
        )
        self.state.apply_move(move)
        assert self.state.current_color == BLACK

        self.state.undo()
        assert self.state.current_color == WHITE

    def test_undo_empty_history_returns_none(self):
        """Undo sans historique retourne None sans planter."""
        result = self.state.undo()
        assert result is None

    def test_redo_empty_returns_none(self):
        """Redo sans undo préalable retourne None."""
        result = self.state.redo()
        assert result is None

    def test_history_is_empty_at_start(self):
        """L'historique est vide au démarrage."""
        assert self.state.get_history() == []

    def test_apply_clears_redo_stack(self):
        """Jouer un nouveau coup après undo efface le redo stack."""
        from shatranj.utils.constants import WHITE, BLACK
        from shatranj.domain.core.move import Move
        from shatranj.utils.constants import PAWN

        move1 = Move(from_square=12, to_square=20, piece_type=PAWN, color=WHITE)
        self.state.apply_move(move1)
        self.state.undo()
        assert self.state.can_redo()

        # On joue un coup différent
        move2 = Move(from_square=11, to_square=19, piece_type=PAWN, color=WHITE)
        self.state.apply_move(move2)

        # Le redo stack doit être vide
        assert not self.state.can_redo()


class TestDisplay:
    """Tests pour l'affichage ASCII du plateau."""

    def test_board_to_string_has_8_rows(self):
        """Le plateau affiché a bien 8 lignes de pièces + 1 ligne de colonnes."""
        from shatranj.domain.core.board import Board
        from shatranj.presentation.cli.display import board_to_string 

        board = Board(setup=True)
        result = board_to_string(board)
        lines = result.strip().split("\n")
        # 8 rangs + 1 ligne de légende (a b c d e f g h)
        assert len(lines) == 9

    def test_board_to_string_contains_pieces(self):
        """Le plateau en position initiale contient les pièces attendues."""
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



class TestMoveParser:
    """Tests pour la notation algébrique."""

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
        with pytest.raises(ValueError):
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
        from shatranj.domain.core.move import Move
        from shatranj.utils.constants import WHITE, PAWN

        move = Move(from_square=12, to_square=20, piece_type=PAWN, color=WHITE)
        assert self.validator.is_valid_move(self.board, move)

    def test_pawn_e2_e4_is_invalid(self):
        """Un pion ne peut pas avancer de 2 cases au Shatranj (pas de double pas)."""
        from shatranj.domain.core.move import Move
        from shatranj.utils.constants import WHITE, PAWN

        move = Move(from_square=12, to_square=28, piece_type=PAWN, color=WHITE)
        assert not self.validator.is_valid_move(self.board, move)

    def test_pawn_cannot_move_backward(self):
        """Un pion ne peut pas reculer."""
        from shatranj.domain.core.move import Move
        from shatranj.utils.constants import WHITE, PAWN

        # De e2 (12) vers e1 (4) : vers l'arrière
        move = Move(from_square=12, to_square=4, piece_type=PAWN, color=WHITE)
        assert not self.validator.is_valid_move(self.board, move)

    def test_move_from_empty_square_invalid(self):
        """On ne peut pas bouger depuis une case vide."""
        from shatranj.domain.core.move import Move
        from shatranj.utils.constants import WHITE, PAWN

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
        from shatranj.utils.constants import WHITE

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
        from shatranj.utils.constants import BLACK

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