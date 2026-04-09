import pytest

from shatranj.domain.core.board import Board
from shatranj.domain.core.move import Move
from shatranj.domain.rules.piece_validator import (AlfilValidator,
                                                   FerzValidator,
                                                   KnightValidator,
                                                   PawnValidator,
                                                   RookValidator,
                                                   ShahValidator)
from shatranj.utils.constants import (ALFIL, BLACK, FERZ, KNIGHT, PAWN, ROOK,
                                      SHAH, WHITE)


@pytest.fixture
def empty_board():
    """Empty board for testing without initial setup"""
    return Board(setup=False)


# ================================================================
# PAWN VALIDATOR TESTS
# ================================================================


class TestPawnValidator:
    """Tests for PawnValidator called directly."""

    def setup_method(self):
        self.validator = PawnValidator()

    def test_forward_move_valid(self, empty_board):
        """White pawn moves forward one square"""
        empty_board.place_piece(PAWN, WHITE, 8)  # a2
        move = Move(8, 16, PAWN, WHITE)  # a2 to a3
        assert self.validator.is_valid(empty_board, move)

    def test_forward_blocked(self, empty_board):
        """Pawn cannot move forward if blocked"""
        empty_board.place_piece(PAWN, WHITE, 8)  # a2
        empty_board.place_piece(PAWN, BLACK, 16)  # a3 - blocking
        move = Move(8, 16, PAWN, WHITE)
        assert not self.validator.is_valid(empty_board, move)

    def test_backward_invalid(self, empty_board):
        """Pawn cannot move backward"""
        empty_board.place_piece(PAWN, WHITE, 16)  # a3
        move = Move(16, 8, PAWN, WHITE)  # a3 to a2 (backward)
        assert not self.validator.is_valid(empty_board, move)

    def test_capture_diagonal_valid(self, empty_board):
        """Pawn captures diagonally"""
        empty_board.place_piece(PAWN, WHITE, 8)  # a2
        empty_board.place_piece(PAWN, BLACK, 17)  # b3 - enemy
        move = Move(8, 17, PAWN, WHITE)
        assert self.validator.is_valid(empty_board, move)

    def test_diagonal_empty_invalid(self, empty_board):
        """Pawn cannot move diagonally if no enemy piece"""
        empty_board.place_piece(PAWN, WHITE, 8)  # a2
        move = Move(8, 17, PAWN, WHITE)  # b3 empty
        assert not self.validator.is_valid(empty_board, move)

    def test_lateral_invalid(self, empty_board):
        """Pawn cannot move sideways"""
        empty_board.place_piece(PAWN, WHITE, 8)  # a2
        move = Move(8, 9, PAWN, WHITE)  # a2 to b2
        assert not self.validator.is_valid(empty_board, move)

    def test_black_pawn_forward(self, empty_board):
        """Black pawn moves down"""
        empty_board.place_piece(PAWN, BLACK, 48)  # a7
        move = Move(48, 40, PAWN, BLACK)  # a7 to a6
        assert self.validator.is_valid(empty_board, move)

    def test_black_pawn_cannot_move_up(self, empty_board):
        """Black pawn cannot move upward"""
        empty_board.place_piece(PAWN, BLACK, 48)  # a7
        move = Move(48, 56, PAWN, BLACK)  # a7 to a8 (backward for black)
        assert not self.validator.is_valid(empty_board, move)

    def test_black_pawn_capture_diagonal(self, empty_board):
        """Black pawn captures diagonally downward"""
        empty_board.place_piece(PAWN, BLACK, 48)  # a7
        empty_board.place_piece(PAWN, WHITE, 41)  # b6 - enemy
        move = Move(48, 41, PAWN, BLACK)
        assert self.validator.is_valid(empty_board, move)

    def test_no_wrap_around(self, empty_board):
        """Pawn should not wrap around board edge"""
        empty_board.place_piece(PAWN, WHITE, 15)  # h2
        move = Move(15, 24, PAWN, WHITE)  # would wrap to a3
        assert not self.validator.is_valid(empty_board, move)


# ================================================================
# ROOK VALIDATOR TESTS
# ================================================================


class TestRookValidator:
    """Tests for RookValidator called directly."""

    def setup_method(self):
        self.validator = RookValidator()

    def test_vertical_valid(self, empty_board):
        """Rook moves vertically"""
        empty_board.place_piece(ROOK, WHITE, 0)  # a1
        move = Move(0, 32, ROOK, WHITE)  # a1 to a5
        assert self.validator.is_valid(empty_board, move)

    def test_horizontal_valid(self, empty_board):
        """Rook moves horizontally"""
        empty_board.place_piece(ROOK, WHITE, 0)  # a1
        move = Move(0, 7, ROOK, WHITE)  # a1 to h1
        assert self.validator.is_valid(empty_board, move)

    def test_diagonal_invalid(self, empty_board):
        """Rook cannot move diagonally"""
        empty_board.place_piece(ROOK, WHITE, 0)  # a1
        move = Move(0, 9, ROOK, WHITE)  # a1 to b2 (diagonal)
        assert not self.validator.is_valid(empty_board, move)

    def test_blocked_vertical(self, empty_board):
        """Rook blocked by piece in vertical path"""
        empty_board.place_piece(ROOK, WHITE, 0)  # a1
        empty_board.place_piece(PAWN, WHITE, 16)  # a3 - blocking
        move = Move(0, 32, ROOK, WHITE)  # a1 to a5
        assert not self.validator.is_valid(empty_board, move)

    def test_blocked_horizontal(self, empty_board):
        """Rook blocked by piece in horizontal path"""
        empty_board.place_piece(ROOK, WHITE, 0)  # a1
        empty_board.place_piece(PAWN, WHITE, 3)  # d1 - blocking
        move = Move(0, 7, ROOK, WHITE)  # a1 to h1
        assert not self.validator.is_valid(empty_board, move)

    def test_move_down(self, empty_board):
        """Rook moves downward"""
        empty_board.place_piece(ROOK, WHITE, 32)  # a5
        move = Move(32, 0, ROOK, WHITE)  # a5 to a1
        assert self.validator.is_valid(empty_board, move)

    def test_move_left(self, empty_board):
        """Rook moves left"""
        empty_board.place_piece(ROOK, WHITE, 7)  # h1
        move = Move(7, 0, ROOK, WHITE)  # h1 to a1
        assert self.validator.is_valid(empty_board, move)


# ================================================================
# KNIGHT VALIDATOR TESTS
# ================================================================


class TestKnightValidator:
    """Tests for KnightValidator called directly."""

    def setup_method(self):
        self.validator = KnightValidator()

    def test_valid_2_1(self, empty_board):
        """Knight moves 2 ranks + 1 file"""
        empty_board.place_piece(KNIGHT, WHITE, 1)  # b1
        move = Move(1, 16, KNIGHT, WHITE)  # b1 to a3
        assert self.validator.is_valid(empty_board, move)

    def test_valid_1_2(self, empty_board):
        """Knight moves 1 rank + 2 files"""
        empty_board.place_piece(KNIGHT, WHITE, 1)  # b1
        move = Move(1, 11, KNIGHT, WHITE)  # b1 to d2
        assert self.validator.is_valid(empty_board, move)

    def test_diagonal_invalid(self, empty_board):
        """Knight cannot move diagonally one square"""
        empty_board.place_piece(KNIGHT, WHITE, 1)  # b1
        move = Move(1, 10, KNIGHT, WHITE)  # b1 to c2 (diagonal)
        assert not self.validator.is_valid(empty_board, move)

    def test_no_wrap_around(self, empty_board):
        """Knight should not wrap around board edge"""
        empty_board.place_piece(KNIGHT, WHITE, 31)  # h4
        move = Move(31, 41, KNIGHT, WHITE)  # would wrap to b6
        assert not self.validator.is_valid(empty_board, move)

    def test_jumps_over_pieces(self, empty_board):
        """Knight can jump over pieces"""
        empty_board.place_piece(KNIGHT, WHITE, 1)  # b1
        empty_board.place_piece(PAWN, WHITE, 9)  # b2 - in the way
        empty_board.place_piece(PAWN, WHITE, 10)  # c2 - in the way
        move = Move(1, 16, KNIGHT, WHITE)  # b1 to a3
        assert self.validator.is_valid(empty_board, move)

    def test_all_8_moves(self, empty_board):
        """Knight can reach all 8 valid squares from center"""
        empty_board.place_piece(KNIGHT, WHITE, 27)  # d4 (center)
        valid_destinations = [10, 12, 17, 21, 33, 37, 42, 44]
        for dest in valid_destinations:
            move = Move(27, dest, KNIGHT, WHITE)
            assert self.validator.is_valid(
                empty_board, move
            ), f"Knight should reach square {dest}"


# ================================================================
# ALFIL VALIDATOR TESTS
# ================================================================


class TestAlfilValidator:
    """Tests for AlfilValidator called directly."""

    def setup_method(self):
        self.validator = AlfilValidator()

    def test_valid_jump(self, empty_board):
        """Alfil jumps 2 squares diagonally"""
        empty_board.place_piece(ALFIL, WHITE, 0)  # a1
        move = Move(0, 18, ALFIL, WHITE)  # a1 to c3
        assert self.validator.is_valid(empty_board, move)

    def test_all_four_directions(self, empty_board):
        """Alfil can jump in all 4 diagonal directions"""
        empty_board.place_piece(ALFIL, WHITE, 27)  # d4
        assert self.validator.is_valid(empty_board, Move(27, 45, ALFIL, WHITE))
        assert self.validator.is_valid(empty_board, Move(27, 41, ALFIL, WHITE))
        assert self.validator.is_valid(empty_board, Move(27, 13, ALFIL, WHITE))
        assert self.validator.is_valid(empty_board, Move(27, 9, ALFIL, WHITE))

    def test_one_square_invalid(self, empty_board):
        """Alfil cannot move just 1 square"""
        empty_board.place_piece(ALFIL, WHITE, 0)  # a1
        move = Move(0, 9, ALFIL, WHITE)  # a1 to b2
        assert not self.validator.is_valid(empty_board, move)

    def test_straight_invalid(self, empty_board):
        """Alfil cannot move straight"""
        empty_board.place_piece(ALFIL, WHITE, 0)  # a1
        move = Move(0, 16, ALFIL, WHITE)  # a1 to a3
        assert not self.validator.is_valid(empty_board, move)

    def test_jumps_over_pieces(self, empty_board):
        """Alfil can jump over pieces"""
        empty_board.place_piece(ALFIL, WHITE, 0)  # a1
        empty_board.place_piece(PAWN, WHITE, 9)  # b2 - in the way
        move = Move(0, 18, ALFIL, WHITE)  # a1 to c3
        assert self.validator.is_valid(empty_board, move)

    def test_no_wrap_around(self, empty_board):
        """Alfil should not wrap around board edge"""
        empty_board.place_piece(ALFIL, WHITE, 30)  # g4
        move = Move(30, 48, ALFIL, WHITE)  # would wrap
        assert not self.validator.is_valid(empty_board, move)


# ================================================================
# FERZ VALIDATOR TESTS
# ================================================================


class TestFerzValidator:
    """Tests for FerzValidator called directly."""

    def setup_method(self):
        self.validator = FerzValidator()

    def test_valid_diagonal(self, empty_board):
        """Ferz moves 1 square diagonally"""
        empty_board.place_piece(FERZ, WHITE, 27)  # d4
        move = Move(27, 36, FERZ, WHITE)  # d4 to e5
        assert self.validator.is_valid(empty_board, move)

    def test_all_four_directions(self, empty_board):
        """Ferz can move in all 4 diagonal directions"""
        empty_board.place_piece(FERZ, WHITE, 27)  # d4
        assert self.validator.is_valid(empty_board, Move(27, 36, FERZ, WHITE))
        assert self.validator.is_valid(empty_board, Move(27, 34, FERZ, WHITE))
        assert self.validator.is_valid(empty_board, Move(27, 20, FERZ, WHITE))
        assert self.validator.is_valid(empty_board, Move(27, 18, FERZ, WHITE))

    def test_straight_invalid(self, empty_board):
        """Ferz cannot move straight"""
        empty_board.place_piece(FERZ, WHITE, 0)  # a1
        move = Move(0, 8, FERZ, WHITE)  # a1 to a2
        assert not self.validator.is_valid(empty_board, move)

    def test_two_squares_invalid(self, empty_board):
        """Ferz cannot move 2 squares diagonally"""
        empty_board.place_piece(FERZ, WHITE, 0)  # a1
        move = Move(0, 18, FERZ, WHITE)  # a1 to c3
        assert not self.validator.is_valid(empty_board, move)

    def test_no_wrap_around(self, empty_board):
        """Ferz should not wrap around board edge"""
        empty_board.place_piece(FERZ, WHITE, 31)  # h4
        move = Move(31, 40, FERZ, WHITE)  # would wrap to a6
        assert not self.validator.is_valid(empty_board, move)


# ================================================================
# SHAH VALIDATOR TESTS
# ================================================================


class TestShahValidator:
    """Tests for ShahValidator called directly."""

    def setup_method(self):
        self.validator = ShahValidator()

    def test_valid_all_directions(self, empty_board):
        """Shah moves 1 square in all 8 directions"""
        empty_board.place_piece(SHAH, WHITE, 27)  # d4
        destinations = [35, 19, 28, 26, 36, 34, 20, 18]
        for dest in destinations:
            move = Move(27, dest, SHAH, WHITE)
            assert self.validator.is_valid(
                empty_board, move
            ), f"Shah should reach square {dest}"

    def test_two_squares_invalid(self, empty_board):
        """Shah cannot move 2 squares"""
        empty_board.place_piece(SHAH, WHITE, 0)  # a1
        move = Move(0, 16, SHAH, WHITE)  # a1 to a3
        assert not self.validator.is_valid(empty_board, move)

    def test_two_diagonal_invalid(self, empty_board):
        """Shah cannot move 2 squares diagonally"""
        empty_board.place_piece(SHAH, WHITE, 0)  # a1
        move = Move(0, 18, SHAH, WHITE)  # a1 to c3
        assert not self.validator.is_valid(empty_board, move)

    def test_knight_move_invalid(self, empty_board):
        """Shah cannot move in L shape"""
        empty_board.place_piece(SHAH, WHITE, 0)  # a1
        move = Move(0, 17, SHAH, WHITE)  # a1 to b3
        assert not self.validator.is_valid(empty_board, move)

    def test_no_wrap_around(self, empty_board):
        """Shah should not wrap around board edge"""
        empty_board.place_piece(SHAH, WHITE, 31)  # h4
        move = Move(31, 32, SHAH, WHITE)  # h4 to a5 (wrap)
        assert not self.validator.is_valid(empty_board, move)
