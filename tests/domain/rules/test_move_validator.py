import pytest
from shatranj.domain.core.board import Board
from shatranj.domain.core.move import Move
from shatranj.domain.rules.move_validator import MoveValidator
from shatranj.utils.constants import WHITE, BLACK, PAWN, ROOK
from shatranj.data.bitboards.bitboard import Bitboard



@pytest.fixture
def board_and_validator():
    return Board(), MoveValidator()

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


def test_rook_move_clear_path(board_and_validator):
    _, validator = board_and_validator

    # Board vide -> aucun blocage
    board = Board(Bitboard(setup=False))
    board.place_piece(ROOK, WHITE, 0)

    move = Move(0, 7, ROOK, WHITE)
    assert validator.is_valid_move(board, move)

def test_rook_blocked(board_and_validator):
    board, validator = board_and_validator

    # in the default setup, a2 (square 8) is occupied by a pawn
    # so rook from a1 (0) to a3 (16) is blocked.
    move = Move(0, 16, ROOK, WHITE)
    assert not validator.is_valid_move(board, move)
