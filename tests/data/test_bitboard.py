import pytest
from shatranj.data.bitboards.bitboard import Bitboard
from shatranj.utils.constants import WHITE, BLACK, ROOK, PAWN


def test_empty_board():
    # bitboard with setup=False starts empty
    bb = Bitboard(setup=False)
    assert bb.get_piece_at(0) is None


def test_set_get_clear():
    # Set a piece, verify it, then clear it
    bb = Bitboard(setup=False)

    bb.set_piece(ROOK, WHITE, 0)
    assert bb.get_piece_at(0) == (ROOK, WHITE)

    bb.clear_piece(0)
    assert bb.get_piece_at(0) is None


def test_starting_position():
    
    bb = Bitboard()
    assert bb.get_piece_at(0) == (ROOK, WHITE)    # a1
    assert bb.get_piece_at(63) == (ROOK, BLACK)   # h8
    assert bb.get_piece_at(8) == (PAWN, WHITE)    # a2
    assert bb.get_piece_at(48) == (PAWN, BLACK)   # a7


def test_white_black_pices():
    bb = Bitboard()
    assert bb.white_pieces != 0
    assert bb.black_pieces != 0
    assert bb.all_pieces == (bb.white_pieces | bb.black_pieces)


def test_square_conversion():
    assert Bitboard.square_to_algebraic(0) == "a1"
    assert Bitboard.square_to_algebraic(63) == "h8"
    assert Bitboard.algebraic_to_square("a1") == 0
    assert Bitboard.algebraic_to_square("h8") == 63


def test_square_conversion_invalid():
    with pytest.raises(ValueError):
        Bitboard.square_to_algebraic(64)

    with pytest.raises(ValueError):
        Bitboard.algebraic_to_square("z9")
