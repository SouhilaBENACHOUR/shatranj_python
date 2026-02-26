import pytest
from shatranj.domain.core.board import Board
from shatranj.domain.core.move import Move
from shatranj.domain.rules.move_validator import MoveValidator
from shatranj.utils.constants import WHITE, BLACK, PAWN, ROOK, KNIGHT, ALFIL, FERZ, SHAH


@pytest.fixture
def board_and_validator():
    """board for testing with initial setup"""
    return Board(), MoveValidator()


@pytest.fixture
def empty_board_and_validator():
    """Empty board for testing without initial setup"""
    return Board(setup=False), MoveValidator()


# ================================================================
# PAWN TESTS
# ================================================================

def test_pawn_forward_move(board_and_validator):
    board, validator = board_and_validator
    board.place_piece(PAWN, WHITE, 8)
    move = Move(8, 16, PAWN, WHITE)
    assert validator.is_valid_move(board, move)


def test_pawn_capture_diagonal(board_and_validator):
    board, validator = board_and_validator
    # White pawn at 8 captures black pawn on 17
    board.remove_piece(8)
    board.place_piece(PAWN, WHITE, 8)
    board.remove_piece(17)
    board.place_piece(PAWN, BLACK, 17)
    move = Move(8, 17, PAWN, WHITE)
    assert validator.is_valid_move(board, move)


def test_pawn_invalid_move(board_and_validator):
    board, validator = board_and_validator
    # Pawn cannot jump two squares
    board.remove_piece(8)
    board.place_piece(PAWN, WHITE, 8)
    move = Move(8, 24, PAWN, WHITE)
    assert not validator.is_valid_move(board, move)


def test_pawn_forward_blocked(empty_board_and_validator):
    """Pawn cannot move forward if blocked"""
    board, validator = empty_board_and_validator
    board.place_piece(PAWN, WHITE, 8)   # a2
    board.place_piece(PAWN, BLACK, 16)  # a3 - blocking
    move = Move(8, 16, PAWN, WHITE)
    assert not validator.is_valid_move(board, move)


def test_pawn_diagonal_no_capture(empty_board_and_validator):
    """Pawn cannot move diagonally if no enemy piece"""
    board, validator = empty_board_and_validator
    board.place_piece(PAWN, WHITE, 8)  # a2
    move = Move(8, 17, PAWN, WHITE)    # a2 to b3 (empty)
    assert not validator.is_valid_move(board, move)


def test_pawn_backward_invalid(empty_board_and_validator):
    """Pawn cannot move backward"""
    board, validator = empty_board_and_validator
    board.place_piece(PAWN, WHITE, 16)  # a3
    move = Move(16, 8, PAWN, WHITE)     # a3 to a2 (backward)
    assert not validator.is_valid_move(board, move)


def test_pawn_no_wrap_around(empty_board_and_validator):
    """Pawn should not wrap around board edge"""
    board, validator = empty_board_and_validator
    board.place_piece(PAWN, WHITE, 15)  # h2
    move = Move(15, 24, PAWN, WHITE)    # h2 to "a3" (would wrap)
    assert not validator.is_valid_move(board, move)


def test_black_pawn_forward(empty_board_and_validator):
    """Black pawn moves down"""
    board, validator = empty_board_and_validator
    board.place_piece(PAWN, BLACK, 48)  # a7
    move = Move(48, 40, PAWN, BLACK)    # a7 to a6
    assert validator.is_valid_move(board, move)


def test_black_pawn_capture_diagonal(empty_board_and_validator):
    """Black pawn captures diagonally downward"""
    board, validator = empty_board_and_validator
    board.place_piece(PAWN, BLACK, 48)  # a7
    board.place_piece(PAWN, WHITE, 41)  # b6 - enemy
    move = Move(48, 41, PAWN, BLACK)
    assert validator.is_valid_move(board, move)


def test_black_pawn_cannot_move_up(empty_board_and_validator):
    """Black pawn cannot move upward"""
    board, validator = empty_board_and_validator
    board.place_piece(PAWN, BLACK, 48)  # a7
    move = Move(48, 56, PAWN, BLACK)    # a7 to a8 (backward for black)
    assert not validator.is_valid_move(board, move)


def test_pawn_capture_own_piece_diagonal(empty_board_and_validator):
    """Pawn cannot capture own piece diagonally"""
    board, validator = empty_board_and_validator
    board.place_piece(PAWN, WHITE, 8)   # a2
    board.place_piece(PAWN, WHITE, 17)  # b3 - own piece
    move = Move(8, 17, PAWN, WHITE)
    assert not validator.is_valid_move(board, move)


def test_pawn_lateral_move_invalid(empty_board_and_validator):
    """Pawn cannot move sideways"""
    board, validator = empty_board_and_validator
    board.place_piece(PAWN, WHITE, 8)  # a2
    move = Move(8, 9, PAWN, WHITE)     # a2 to b2
    assert not validator.is_valid_move(board, move)


# ================================================================
# ROOK TESTS
# ================================================================

def test_rook_blocked(board_and_validator):
    board, validator = board_and_validator
    # in the default setup, a2 (square 8) is occupied by a pawn
    # so rook from a1 (0) to a3 (16) is blocked.
    move = Move(0, 16, ROOK, WHITE)
    assert not validator.is_valid_move(board, move)


def test_rook_diagonal_invalid(empty_board_and_validator):
    """Rook cannot move diagonally"""
    board, validator = empty_board_and_validator
    board.place_piece(ROOK, WHITE, 0)  # a1
    move = Move(0, 9, ROOK, WHITE)     # a1 to b2 (diagonal)
    assert not validator.is_valid_move(board, move)


def test_rook_capture_enemy(empty_board_and_validator):
    """Rook can capture enemy piece"""
    board, validator = empty_board_and_validator
    board.place_piece(ROOK, WHITE, 0)   # a1
    board.place_piece(PAWN, BLACK, 7)   # h1 - enemy
    move = Move(0, 7, ROOK, WHITE)
    assert validator.is_valid_move(board, move)


def test_rook_vertical_move(empty_board_and_validator):
    """Rook moves vertically"""
    board, validator = empty_board_and_validator
    board.place_piece(ROOK, WHITE, 0)  # a1
    move = Move(0, 32, ROOK, WHITE)    # a1 to a5
    assert validator.is_valid_move(board, move)


def test_rook_horizontal_move(empty_board_and_validator):
    """Rook moves horizontally"""
    board, validator = empty_board_and_validator
    board.place_piece(ROOK, WHITE, 0)  # a1
    move = Move(0, 7, ROOK, WHITE)     # a1 to h1
    assert validator.is_valid_move(board, move)


def test_rook_blocked_horizontal(empty_board_and_validator):
    """Rook blocked by piece in horizontal path"""
    board, validator = empty_board_and_validator
    board.place_piece(ROOK, WHITE, 0)   # a1
    board.place_piece(PAWN, WHITE, 3)   # d1 - blocking
    move = Move(0, 7, ROOK, WHITE)      # a1 to h1
    assert not validator.is_valid_move(board, move)


def test_rook_blocked_vertical(empty_board_and_validator):
    """Rook blocked by piece in vertical path"""
    board, validator = empty_board_and_validator
    board.place_piece(ROOK, WHITE, 0)   # a1
    board.place_piece(PAWN, WHITE, 16)  # a3 - blocking
    move = Move(0, 32, ROOK, WHITE)     # a1 to a5
    assert not validator.is_valid_move(board, move)


def test_rook_capture_enemy_vertical(empty_board_and_validator):
    """Rook captures enemy vertically"""
    board, validator = empty_board_and_validator
    board.place_piece(ROOK, WHITE, 0)   # a1
    board.place_piece(PAWN, BLACK, 32)  # a5 - enemy
    move = Move(0, 32, ROOK, WHITE)
    assert validator.is_valid_move(board, move)


def test_rook_cannot_capture_own_piece(empty_board_and_validator):
    """Rook cannot capture own piece"""
    board, validator = empty_board_and_validator
    board.place_piece(ROOK, WHITE, 0)   # a1
    board.place_piece(PAWN, WHITE, 32)  # a5 - own piece
    move = Move(0, 32, ROOK, WHITE)
    assert not validator.is_valid_move(board, move)


def test_rook_move_down(empty_board_and_validator):
    """Rook moves downward"""
    board, validator = empty_board_and_validator
    board.place_piece(ROOK, WHITE, 32)  # a5
    move = Move(32, 0, ROOK, WHITE)     # a5 to a1
    assert validator.is_valid_move(board, move)


def test_rook_move_left(empty_board_and_validator):
    """Rook moves left"""
    board, validator = empty_board_and_validator
    board.place_piece(ROOK, WHITE, 7)  # h1
    move = Move(7, 0, ROOK, WHITE)     # h1 to a1
    assert validator.is_valid_move(board, move)


# ================================================================
# KNIGHT TESTS
# ================================================================

def test_knight_invalid_diagonal(empty_board_and_validator):
    """Knight cannot move diagonally one square"""
    board, validator = empty_board_and_validator
    board.place_piece(KNIGHT, WHITE, 1)  # b1
    move = Move(1, 10, KNIGHT, WHITE)    # b1 to c2 (diagonal)
    assert not validator.is_valid_move(board, move)


def test_knight_valid_move_2_1(empty_board_and_validator):
    """Knight moves 2 ranks + 1 file"""
    board, validator = empty_board_and_validator
    board.place_piece(KNIGHT, WHITE, 1)  # b1
    move = Move(1, 16, KNIGHT, WHITE)    # b1 to a3
    assert validator.is_valid_move(board, move)


def test_knight_valid_move_1_2(empty_board_and_validator):
    """Knight moves 1 rank + 2 files"""
    board, validator = empty_board_and_validator
    board.place_piece(KNIGHT, WHITE, 1)  # b1
    move = Move(1, 11, KNIGHT, WHITE)    # b1 to d2
    assert validator.is_valid_move(board, move)


def test_knight_jumps_over_pieces(empty_board_and_validator):
    """Knight can jump over pieces"""
    board, validator = empty_board_and_validator
    board.place_piece(KNIGHT, WHITE, 1)  # b1
    board.place_piece(PAWN, WHITE, 9)    # b2 - in the way
    board.place_piece(PAWN, WHITE, 10)   # c2 - in the way
    move = Move(1, 16, KNIGHT, WHITE)    # b1 to a3
    assert validator.is_valid_move(board, move)


def test_knight_capture_enemy(empty_board_and_validator):
    """Knight captures enemy piece"""
    board, validator = empty_board_and_validator
    board.place_piece(KNIGHT, WHITE, 1)  # b1
    board.place_piece(PAWN, BLACK, 16)   # a3 - enemy
    move = Move(1, 16, KNIGHT, WHITE)
    assert validator.is_valid_move(board, move)


def test_knight_cannot_capture_own(empty_board_and_validator):
    """Knight cannot capture own piece"""
    board, validator = empty_board_and_validator
    board.place_piece(KNIGHT, WHITE, 1)  # b1
    board.place_piece(PAWN, WHITE, 16)   # a3 - own piece
    move = Move(1, 16, KNIGHT, WHITE)
    assert not validator.is_valid_move(board, move)


def test_knight_no_wrap_around(empty_board_and_validator):
    """Knight should not wrap around board edge"""
    board, validator = empty_board_and_validator
    board.place_piece(KNIGHT, WHITE, 31)  # h4
    move = Move(31, 41, KNIGHT, WHITE)    # would wrap to b6
    assert not validator.is_valid_move(board, move)


def test_knight_all_8_moves(empty_board_and_validator):
    """Knight can reach all 8 valid squares from center"""
    board, validator = empty_board_and_validator
    board.place_piece(KNIGHT, WHITE, 27)  # d4 (center)

    valid_destinations = [10, 12, 17, 21, 33, 37, 42, 44]
    for dest in valid_destinations:
        assert validator.is_valid_move(board, Move(27, dest, KNIGHT, WHITE)), \
            f"Knight should reach square {dest}"


# ================================================================
# ALFIL TESTS
# ================================================================

def test_alfil_all_four_directions(empty_board_and_validator):
    """Alfil can jump in all 4 diagonal directions"""
    board, validator = empty_board_and_validator
    board.place_piece(ALFIL, WHITE, 27)  # d4 (center)

    # Northeast: d4 to f6
    assert validator.is_valid_move(board, Move(27, 45, ALFIL, WHITE))
    # Northwest: d4 to b6
    assert validator.is_valid_move(board, Move(27, 41, ALFIL, WHITE))
    # Southeast: d4 to f2
    assert validator.is_valid_move(board, Move(27, 13, ALFIL, WHITE))
    # Southwest: d4 to b2
    assert validator.is_valid_move(board, Move(27, 9, ALFIL, WHITE))


def test_alfil_cannot_move_1(empty_board_and_validator):
    """Alfil cannot move just 1 square"""
    board, validator = empty_board_and_validator
    board.place_piece(ALFIL, WHITE, 0)  # a1
    move = Move(0, 9, ALFIL, WHITE)     # a1 to b2
    assert not validator.is_valid_move(board, move)


def test_alfil_jumps_over_pieces(empty_board_and_validator):
    """Alfil can jump over pieces"""
    board, validator = empty_board_and_validator
    board.place_piece(ALFIL, WHITE, 0)   # a1
    board.place_piece(PAWN, WHITE, 9)    # b2 - in the way
    move = Move(0, 18, ALFIL, WHITE)     # a1 to c3
    assert validator.is_valid_move(board, move)


def test_alfil_capture_enemy(empty_board_and_validator):
    """Alfil captures enemy piece"""
    board, validator = empty_board_and_validator
    board.place_piece(ALFIL, WHITE, 0)   # a1
    board.place_piece(PAWN, BLACK, 18)   # c3 - enemy
    move = Move(0, 18, ALFIL, WHITE)
    assert validator.is_valid_move(board, move)


def test_alfil_cannot_capture_own(empty_board_and_validator):
    """Alfil cannot capture own piece"""
    board, validator = empty_board_and_validator
    board.place_piece(ALFIL, WHITE, 0)   # a1
    board.place_piece(PAWN, WHITE, 18)   # c3 - own piece
    move = Move(0, 18, ALFIL, WHITE)
    assert not validator.is_valid_move(board, move)


def test_alfil_cannot_move_straight(empty_board_and_validator):
    """Alfil cannot move straight"""
    board, validator = empty_board_and_validator
    board.place_piece(ALFIL, WHITE, 0)  # a1
    move = Move(0, 16, ALFIL, WHITE)    # a1 to a3
    assert not validator.is_valid_move(board, move)


def test_alfil_no_wrap_around(empty_board_and_validator):
    """Alfil should not wrap around board edge"""
    board, validator = empty_board_and_validator
    board.place_piece(ALFIL, WHITE, 30)  # g4
    move = Move(30, 48, ALFIL, WHITE)    # would wrap
    assert not validator.is_valid_move(board, move)


# ================================================================
# FERZ TESTS
# ================================================================

def test_ferz_all_four_directions(empty_board_and_validator):
    """Ferz can move in all 4 diagonal directions"""
    board, validator = empty_board_and_validator
    board.place_piece(FERZ, WHITE, 27)  # d4 (center)

    # Northeast: d4 to e5
    assert validator.is_valid_move(board, Move(27, 36, FERZ, WHITE))
    # Northwest: d4 to c5
    assert validator.is_valid_move(board, Move(27, 34, FERZ, WHITE))
    # Southeast: d4 to e3
    assert validator.is_valid_move(board, Move(27, 20, FERZ, WHITE))
    # Southwest: d4 to c3
    assert validator.is_valid_move(board, Move(27, 18, FERZ, WHITE))


def test_ferz_cannot_move_straight(empty_board_and_validator):
    """Ferz cannot move straight"""
    board, validator = empty_board_and_validator
    board.place_piece(FERZ, WHITE, 0)  # a1
    move = Move(0, 8, FERZ, WHITE)     # a1 to a2
    assert not validator.is_valid_move(board, move)


def test_ferz_capture_enemy(empty_board_and_validator):
    """Ferz can capture enemy piece"""
    board, validator = empty_board_and_validator
    board.place_piece(FERZ, WHITE, 0)   # a1
    board.place_piece(PAWN, BLACK, 9)   # b2 - enemy
    move = Move(0, 9, FERZ, WHITE)
    assert validator.is_valid_move(board, move)


def test_ferz_cannot_move_2_diagonal(empty_board_and_validator):
    """Ferz cannot move 2 squares diagonally"""
    board, validator = empty_board_and_validator
    board.place_piece(FERZ, WHITE, 0)  # a1
    move = Move(0, 18, FERZ, WHITE)    # a1 to c3 (2 squares)
    assert not validator.is_valid_move(board, move)


def test_ferz_cannot_capture_own(empty_board_and_validator):
    """Ferz cannot capture own piece"""
    board, validator = empty_board_and_validator
    board.place_piece(FERZ, WHITE, 0)   # a1
    board.place_piece(PAWN, WHITE, 9)   # b2 - own piece
    move = Move(0, 9, FERZ, WHITE)
    assert not validator.is_valid_move(board, move)


def test_ferz_no_wrap_around(empty_board_and_validator):
    """Ferz should not wrap around board edge"""
    board, validator = empty_board_and_validator
    board.place_piece(FERZ, WHITE, 31)  # h4
    move = Move(31, 40, FERZ, WHITE)    # would wrap to a6
    assert not validator.is_valid_move(board, move)


# ================================================================
# SHAH (KING) TESTS
# ================================================================

def test_shah_move_1_square_all_directions(empty_board_and_validator):
    """Shah moves 1 square in all 8 directions"""
    board, validator = empty_board_and_validator
    board.place_piece(SHAH, WHITE, 27)  # d4 (center)

    # North: d4 to d5
    assert validator.is_valid_move(board, Move(27, 35, SHAH, WHITE))
    # South: d4 to d3
    assert validator.is_valid_move(board, Move(27, 19, SHAH, WHITE))
    # East: d4 to e4
    assert validator.is_valid_move(board, Move(27, 28, SHAH, WHITE))
    # West: d4 to c4
    assert validator.is_valid_move(board, Move(27, 26, SHAH, WHITE))
    # Northeast: d4 to e5
    assert validator.is_valid_move(board, Move(27, 36, SHAH, WHITE))
    # Northwest: d4 to c5
    assert validator.is_valid_move(board, Move(27, 34, SHAH, WHITE))
    # Southeast: d4 to e3
    assert validator.is_valid_move(board, Move(27, 20, SHAH, WHITE))
    # Southwest: d4 to c3
    assert validator.is_valid_move(board, Move(27, 18, SHAH, WHITE))


def test_shah_cannot_move_2_squares(empty_board_and_validator):
    """Shah cannot move 2 squares"""
    board, validator = empty_board_and_validator
    board.place_piece(SHAH, WHITE, 0)  # a1
    move = Move(0, 16, SHAH, WHITE)    # a1 to a3
    assert not validator.is_valid_move(board, move)


def test_shah_capture_enemy(empty_board_and_validator):
    """Shah can capture enemy piece"""
    board, validator = empty_board_and_validator
    board.place_piece(SHAH, WHITE, 0)   # a1
    board.place_piece(PAWN, BLACK, 1)   # b1 - enemy
    move = Move(0, 1, SHAH, WHITE)
    assert validator.is_valid_move(board, move)


def test_shah_cannot_capture_own(empty_board_and_validator):
    """Shah cannot capture own piece"""
    board, validator = empty_board_and_validator
    board.place_piece(SHAH, WHITE, 0)   # a1
    board.place_piece(PAWN, WHITE, 1)   # b1 - own piece
    move = Move(0, 1, SHAH, WHITE)
    assert not validator.is_valid_move(board, move)


def test_shah_cannot_move_like_knight(empty_board_and_validator):
    """Shah cannot move in L shape"""
    board, validator = empty_board_and_validator
    board.place_piece(SHAH, WHITE, 0)  # a1
    move = Move(0, 17, SHAH, WHITE)    # a1 to b3 (knight move)
    assert not validator.is_valid_move(board, move)


def test_shah_no_wrap_around(empty_board_and_validator):
    """Shah should not wrap around board edge"""
    board, validator = empty_board_and_validator
    board.place_piece(SHAH, WHITE, 31)  # h4
    move = Move(31, 32, SHAH, WHITE)    # h4 to a5 (wrap)
    assert not validator.is_valid_move(board, move)


def test_shah_cannot_move_2_diagonal(empty_board_and_validator):
    """Shah cannot move 2 squares diagonally"""
    board, validator = empty_board_and_validator
    board.place_piece(SHAH, WHITE, 0)  # a1
    move = Move(0, 18, SHAH, WHITE)    # a1 to c3
    assert not validator.is_valid_move(board, move)


# ================================================================
# GENERAL VALIDATION TESTS
# ================================================================

def test_cannot_capture_own_piece(empty_board_and_validator):
    """Cannot capture your own piece"""
    board, validator = empty_board_and_validator
    board.place_piece(ROOK, WHITE, 0)   # a1
    board.place_piece(PAWN, WHITE, 7)   # h1 - own piece
    move = Move(0, 7, ROOK, WHITE)
    assert not validator.is_valid_move(board, move)


def test_same_square_invalid(empty_board_and_validator):
    """Cannot move to the same square"""
    board, validator = empty_board_and_validator
    board.place_piece(PAWN, WHITE, 8)
    move = Move(8, 8, PAWN, WHITE)
    assert not validator.is_valid_move(board, move)


def test_wrong_piece_on_square(empty_board_and_validator):
    """Move rejected if piece on square doesn't match"""
    board, validator = empty_board_and_validator
    board.place_piece(ROOK, WHITE, 0)   # a1 has a rook
    move = Move(0, 8, PAWN, WHITE)      # but move says it's a pawn
    assert not validator.is_valid_move(board, move)


def test_wrong_color_on_square(empty_board_and_validator):
    """Move rejected if color doesn't match"""
    board, validator = empty_board_and_validator
    board.place_piece(PAWN, BLACK, 8)   # a2 has a black pawn
    move = Move(8, 16, PAWN, WHITE)     # but move says it's white
    assert not validator.is_valid_move(board, move)


def test_out_of_bounds_from(empty_board_and_validator):
    """Move rejected if from_square out of bounds"""
    board, validator = empty_board_and_validator
    move = Move(-1, 8, PAWN, WHITE)
    assert not validator.is_valid_move(board, move)


def test_out_of_bounds_to(empty_board_and_validator):
    """Move rejected if to_square out of bounds"""
    board, validator = empty_board_and_validator
    board.place_piece(PAWN, WHITE, 8)
    move = Move(8, 64, PAWN, WHITE)
    assert not validator.is_valid_move(board, move)


def test_no_piece_on_from_square(empty_board_and_validator):
    """Move rejected if no piece on from_square"""
    board, validator = empty_board_and_validator
    move = Move(8, 16, PAWN, WHITE)     # empty square
    assert not validator.is_valid_move(board, move)