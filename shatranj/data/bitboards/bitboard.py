"""
Docstring for shatranj.data.bitboards.bitboard
This module stores a Shatranj position using 12 bitboards (64-bit integers).
Each bit corresponds to one square (0..63). A bit set to 1 means “occupied”.

We keep one bitboard per (piece, color) in self._boards:
    self._boards[(PAWN, WHITE)] -> all white pawns, etc.
    
-white_pieces / black_pieces / all_pieces: occupancy bitboards (computed on demand)
-square_to_algebraic() and algebraic_to_square(): convert between 0..63 and "e4" style coords
"""
from shatranj.utils.constants import (
    BOARD_SIZE, NUM_SQUARES,          
    WHITE, BLACK,                   
    SHAH, FERZ, ROOK, ALFIL, KNIGHT, PAWN,
    FILES, RANKS)
from shatranj.data.bitboards.operations import (
    set_bit_at, clear_bit_at, get_bit_at)

PIECES = (SHAH, FERZ, ROOK, ALFIL, KNIGHT, PAWN)
COLORS = (WHITE, BLACK)
START_BACK_RANK = (ROOK, KNIGHT, ALFIL, FERZ, SHAH, ALFIL, KNIGHT, ROOK)

class Bitboard:
    def __init__(self, setup: bool = True) -> None:
        # One bitboard per (piece, color
        # self._boards[(PAWN, WHITE)] holds all white pawns...etc
        self._boards = {(p, c): 0 for p in PIECES for c in COLORS}

        # If setup=True pieces in the initial position
        if setup:
            self.setup_starting_position()

    def clear(self) -> None:
        # we set every piece bitboard to 0.
        for key in self._boards:
            self._boards[key] = 0

    def setup_starting_position(self) -> None:
        #starting position
        self.clear()

        #file_idx goes 0..7 (a..h)
        for file_idx, piece in enumerate(START_BACK_RANK):
            # White back rank a1..h1 are squares 0..7
            self.set_piece(piece, WHITE, file_idx)

            # White pawns a2..h2 are squares 8..15 (add BOARD_SIZE)
            self.set_piece(PAWN, WHITE, file_idx + BOARD_SIZE)

            # Black back rank: a8..h8 are squares 56-63 (64 - 8 = 56)
            self.set_piece(piece, BLACK, file_idx + (NUM_SQUARES - BOARD_SIZE))

            # Black pawns a7..h7 are squares 48-55 (64 - 16 = 48)
            self.set_piece(PAWN, BLACK, file_idx + (NUM_SQUARES - 2 * BOARD_SIZE))

    def set_piece(self, piece: str, color: str, square: int) -> None:
        # verify the square is empty first 
        self.clear_piece(square)

        # Then set the bit in the correct (piece, color) bitboard with set_bit_at()
        key = (piece, color)
        self._boards[key] = set_bit_at(self._boards[key], square)

    def clear_piece(self, square: int) -> None:
        # remove any piece from this square
        for key in self._boards:
            self._boards[key] = clear_bit_at(self._boards[key], square)

    # Returns (piece, color) or None if empty.
    def get_piece_at(self, square: int):
        for (piece, color), bb in self._boards.items():
            if get_bit_at(bb, square):
                return piece, color
        return None

    # we turn these methods into computed attribute
    @property
    def white_pieces(self) -> int:
        # Bitboard of all white occupied squares 
        bb = 0
        for piece in PIECES:
            # |= combine bits
            bb |= self._boards[(piece, WHITE)]
        return bb

    @property
    def black_pieces(self) -> int:
        # Bitboard of all black occupied squares
        bb = 0
        for piece in PIECES:
            bb |= self._boards[(piece, BLACK)]
        return bb
    
    @property
    #all pices 
    def all_pieces(self) -> int:
        return self.white_pieces | self.black_pieces
    

    #Bitboard.square_to_algebraic(28) -> "e4"
    #Bitboard.algebraic_to_square("e4") -> 28  for being static no need to self
    @staticmethod
    def square_to_algebraic(square: int) -> str:
        #FILE = column letter (a..h)
        #RANK = row number   (1..8)
        ### square % 8  -> gives the file index (0..7)
        ### square // 8 -> gives the rank index (0..7)

        ### square = 28
        # 28 % 8  = 4  -> FILES[4] = "e"
        # 28 // 8 = 3  -> RANKS[3] = "4"
        # -> "e4"
        if not 0 <= square < NUM_SQUARES:
            raise ValueError("must be in [0, 63]")

        return FILES[square % BOARD_SIZE] + RANKS[square // BOARD_SIZE]

    @staticmethod
    def algebraic_to_square(pos: str) -> int:
        #"e4" back to square index (0..63)
        ### - pos[0] must be in FILES ("a".."h")
        ### - pos[1] must be in RANKS ("1".."8")
        ### file_idx = FILES.index("e") = 4
        ### rank_idx = RANKS.index("4") = 3
        ### square = 4 + 8*3 = 28
        if len(pos) != 2 or pos[0] not in FILES or pos[1] not in RANKS:
            raise ValueError("pos must be like 'e4'")
        
        ### square = file_idx + 8 * rank_idx
        return FILES.index(pos[0]) + BOARD_SIZE * RANKS.index(pos[1])
