"""
Docstring for shatranj.data.bitboards.operations
A bitboard is a 64-bit integer where each bit represents a square on an 8×8 board
Square indices go from 0 to 63.
1 << square creates a mask with only that square’s bit set.
         square = 0  ->  ...0001
         square = 3  ->  ...1000
"""

### check if the square is within the valid range
def check_square(square:int) -> None:
    if square <0 or square >=64:
        raise ValueError("must be in [0-63]")

### (1 << square) create a mask at pos square // if square = 0 -> ..001
### combined to our bitboard, or forces that bit to 1
### bitboard:      00100001
### mask:          00001000
### OR result:     00101001
def set_bit_at(bitboard: int, square:int) -> int:
    check_square(square)
    return bitboard | (1 << square)

""" turn the bit to 0 for square
bitboard:        00101101
~(1<<square):    11110111
AND result:      00100101"""
def clear_bit_at(bitboard: int, square: int) -> int:
    check_square(square)
    return bitboard & ~(1 << square)

### read the bit at 'square' returns 0 or 1;
### example (square = 3):
### bitboard:        00101101
### bitboard >> 3:   00000101
### & 1:             00000001  -> returns 1
def get_bit_at(bitboard: int,square: int) -> int:
    check_square(square)
    return (bitboard >> square) & 1

"""when our bit is on 0, nothing changes
0 ^ 0 = 0
1 ^ 0 = 1 

if it's our square 
0 ^ 1 = 1
1 ^ 1 = 0"""
def inverse_bit_at(bitboard: int, square: int) -> int:
    check_square(square)
    return bitboard ^ (1 << square)

# useful for how many pieces / occupied squares
def count_bits(bitboard: int) -> int:
    return bitboard.bit_count()


### to get ONE occupied square without modifying the bitboard
### - also what is the first set square in this bitboard?
### LSB = the lowest-index bit that is 1 
###  -bb is the two's complement of bb: invert bits + add 1
"""
 bb  = 00101100
 ~bb = 11010011        (bitwise NOT: flip every bit)
 -bb = ~bb + 1
     = 11010011 + 1
     = 11010100

 bb & -bb:
   00101100
 & 11010100
 = 00000100            (only the lowest 1-bit remains)
"""
### then bit_length()-1 gives its index:
### 00000100 has bit_length 3 -> 3-1 = 2
def get_lsb(bitboard: int) -> int:
    if bitboard == 0:
        return -1
    return (bitboard& -bitboard).bit_length() - 1


def pop_lsb(bitboard: int) -> tuple[int, int]:
    idx = get_lsb(bitboard)
    if idx == -1:
        return -1, 0
    ### XOR toggle bits, and since lsb is 1 only there:
    ### 1 ^ 1 = 0 
    ### other bits ^0 stay the same
    return idx, bitboard ^ (1 << idx)

### list of squares occupied by a piece type 
def squares_from_bitboard(bitboard: int) -> list[int]:
    squares = []
    bb = bitboard #working on a copy
    while bb:
                # pop_lsb returns:
        #idx: the index of LSB -> one occupied square
        #bb: the bitboard with that bit removed to contunue the loop
        idx, bb = pop_lsb(bb)
        squares.append(idx)
    return squares
