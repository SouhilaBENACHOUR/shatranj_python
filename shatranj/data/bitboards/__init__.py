"""
Low-level bitboard utilities (data layer).

`bitboard.py` exposes pure helper functions on 64-bit integers.
No board state class lives in this package.
"""

from shatranj.data.bitboards.bitboard import (check_square, clear_bit_at,
                                              count_bits, get_bit_at, get_lsb,
                                              inverse_bit_at, pop_lsb,
                                              set_bit_at,
                                              squares_from_bitboard)

__all__ = [
    "check_square",
    "set_bit_at",
    "clear_bit_at",
    "get_bit_at",
    "inverse_bit_at",
    "count_bits",
    "get_lsb",
    "pop_lsb",
    "squares_from_bitboard",
]
