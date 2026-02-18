import pytest
from shatranj.data.bitboards import bitboard as ops


def test_check_square_invalid():
    # check_square() should reject out-of-range square indices
    with pytest.raises(ValueError):
        ops.check_square(-1)
    with pytest.raises(ValueError):
        ops.check_square(64)
    assert ops.check_square(4)
    

def test_set_get_clear():
    # start from an empty bitboard
    bb = 0

    # Set bit at square 3 -> should become 1
    bb = ops.set_bit_at(bb, 3)
    assert ops.get_bit_at(bb, 3) == 1

    # Clear bit at square 3 -> should become 0 again
    bb = ops.clear_bit_at(bb, 3)
    assert ops.get_bit_at(bb, 3) == 0


def test_inverse_bit_at():
    # inverse_bit_at() toggles a bit: 0->1, then 1->0
    bb = 0

    bb = ops.inverse_bit_at(bb, 5)
    assert ops.get_bit_at(bb, 5) == 1

    bb = ops.inverse_bit_at(bb, 5)
    assert ops.get_bit_at(bb, 5) == 0


def test_count_bits():
    # count_bits() returns how many bits are set to 1 in the bitboard
    bb = 0
    bb = ops.set_bit_at(bb, 1)
    bb = ops.set_bit_at(bb, 4)
    bb = ops.set_bit_at(bb, 7)

    assert ops.count_bits(bb) == 3


def test_get_lsb():
    # get_lsb() returns the index of the least-significant set bit
    # 0b101000 has bits set at squares 3 and 5 -> LSB is 3
    bb = 0b101000
    assert ops.get_lsb(bb) == 3

    assert ops.get_lsb(0) == -1


def test_pop_lsb():
    # pop_lsb() returns (lsb_index, bitboard_without_that_bit)
    # 0b101000 -> lsb is at 3, removing it leaves 0b100000
    bb = 0b101000
    idx, new_bb = ops.pop_lsb(bb)

    assert idx == 3
    assert new_bb == 0b100000


def test_squares_from_bitboard():
    # squares_from_bitboard() should return all set-bit indices in ascending order
    bb = 0
    for sq in (0, 2, 5):
        bb = ops.set_bit_at(bb, sq)

    assert ops.squares_from_bitboard(bb) == [0, 2, 5]
