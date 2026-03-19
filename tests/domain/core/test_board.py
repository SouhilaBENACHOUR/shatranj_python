import pytest
from shatranj.domain.core.board import Board
from shatranj.domain.core.move import Move
from shatranj.utils.constants import WHITE, BLACK, ROOK, PAWN, FERZ


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


def test_apply_move_promotes_pawn_to_ferz():
    board = Board(setup=False)
    board.place_piece(PAWN, WHITE, 48)  # a7

    move = Move(48, 56, PAWN, WHITE)

    board.apply_move(move)

    assert board.get_piece_at(56) == (FERZ, WHITE)
    assert board.get_piece_at(48) is None


def test_undo_move_restores_pawn_after_promotion():
    board = Board(setup=False)
    board.place_piece(PAWN, WHITE, 48)  # a7
    board.place_piece(ROOK, BLACK, 57)  # b8

    move = Move(48, 57, PAWN, WHITE, captured_piece=ROOK)
    captured = board.apply_move(move)
    board.undo_move(move, captured)

    assert board.get_piece_at(48) == (PAWN, WHITE)
    assert board.get_piece_at(57) == (ROOK, BLACK)
