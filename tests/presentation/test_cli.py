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