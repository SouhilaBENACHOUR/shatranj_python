"""
Low-level bitboard helpers.

A bitboard is a 64-bit integer where each bit represents a square (0..63).
"""


def check_square(square: int) -> bool:
    if square < 0 or square >= 64:
        raise ValueError("must be in [0-63]")
    return True


def set_bit_at(bitboard: int, square: int) -> int:
    check_square(square)
    return bitboard | (1 << square)


def clear_bit_at(bitboard: int, square: int) -> int:
    check_square(square)
    return bitboard & ~(1 << square)


def get_bit_at(bitboard: int, square: int) -> int:
    check_square(square)
    return (bitboard >> square) & 1


def inverse_bit_at(bitboard: int, square: int) -> int:
    check_square(square)
    return bitboard ^ (1 << square)


def count_bits(bitboard: int) -> int:
    return bitboard.bit_count()


def get_lsb(bitboard: int) -> int:
    if bitboard == 0:
        return -1
    return (bitboard & -bitboard).bit_length() - 1


def pop_lsb(bitboard: int) -> tuple[int, int]:
    idx = get_lsb(bitboard)
    if idx == -1:
        return -1, 0
    return idx, bitboard ^ (1 << idx)


def squares_from_bitboard(bitboard: int) -> list[int]:
    squares: list[int] = []
    bb = bitboard
    while bb:
        idx, bb = pop_lsb(bb)
        squares.append(idx)
    return squares
