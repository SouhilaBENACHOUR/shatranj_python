import pytest

from shatranj.data.bitboards import bitboard as bb
from shatranj.utils.exceptions import InvalidSquareError


def test_check_square_bounds():
    assert bb.check_square(0)
    assert bb.check_square(63)
    with pytest.raises(InvalidSquareError):
        bb.check_square(-1)
    with pytest.raises(InvalidSquareError):
        bb.check_square(64)


def test_set_get_clear_bit():
    value = 0
    value = bb.set_bit_at(value, 12)
    assert bb.get_bit_at(value, 12) == 1

    value = bb.clear_bit_at(value, 12)
    assert bb.get_bit_at(value, 12) == 0


def test_pop_and_collect_bits():
    value = 0
    for square in (1, 4, 9):
        value = bb.set_bit_at(value, square)

    idx, value = bb.pop_lsb(value)
    assert idx == 1
    assert bb.squares_from_bitboard(value) == [4, 9]
