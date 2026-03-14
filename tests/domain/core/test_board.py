import pytest
from shatranj.domain.core.board import Board
from shatranj.utils.constants import WHITE, ROOK, PAWN


def test_get_and_place_piece():
    board = Board()
    # make sure square 0 is empty by removing whatever is there
    board.remove_piece(0)
    assert board.get_piece_at(0) is None  # should return None for an empy square

    # white rook on square 0
    board.place_piece(ROOK, WHITE, 0)
    assert board.get_piece_at(0) == (ROOK, WHITE)


def test_move_piece():
    board = Board()

    # we clear square 0 and put a white pawn there
    board.remove_piece(0)
    board.place_piece(PAWN, WHITE, 0)

    # check of moves
    board.move_piece(0, 16)

    # after moving origin is empty, destination has the pawn
    assert board.get_piece_at(0) is None
    assert board.get_piece_at(16) == (PAWN, WHITE)


def test_move_piece_invalid():
    board = Board()

    # moving to the same square should raise an error
    with pytest.raises(ValueError):
        board.move_piece(0, 0)


def test_occupancy():
    board = Board()
    # total occupancy should be the bitwise OR white and black occupancy
    assert board.occupancy == (board.white_occupancy | board.black_occupancy)
