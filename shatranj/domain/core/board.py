from shatranj.data.bitboards.bitboard import clear_bit_at, get_bit_at, set_bit_at, get_lsb
from shatranj.domain.core.move import Move
from shatranj.utils.constants import (
    ALFIL,
    BLACK,
    BOARD_SIZE,
    FERZ,
    FILES,
    KNIGHT,
    NUM_SQUARES,
    PAWN,
    RANKS,
    ROOK,
    SHAH,
    WHITE,
)


PIECES = (SHAH, FERZ, ROOK, ALFIL, KNIGHT, PAWN)
COLORS = (WHITE, BLACK)
START_BACK_RANK = (ROOK, KNIGHT, ALFIL, FERZ, SHAH, ALFIL, KNIGHT, ROOK)


class Board:
    def __init__(self, setup: bool = True) -> None:
        self._boards = {(piece, color): 0 for piece in PIECES for color in COLORS}
        if setup:
            self.setup_starting_position()

    def clear(self) -> None:
        for key in self._boards:
            self._boards[key] = 0

    def setup_starting_position(self) -> None:
        self.clear()

        for file_idx, piece in enumerate(START_BACK_RANK):
            self.set_piece(piece, WHITE, file_idx)
            self.set_piece(PAWN, WHITE, file_idx + BOARD_SIZE)
            self.set_piece(piece, BLACK, file_idx + (NUM_SQUARES - BOARD_SIZE))
            self.set_piece(PAWN, BLACK, file_idx + (NUM_SQUARES - 2 * BOARD_SIZE))

    def set_piece(self, piece: str, color: str, square: int) -> None:
        self.clear_piece(square)
        key = (piece, color)
        self._boards[key] = set_bit_at(self._boards[key], square)

    def place_piece(self, piece: str, color: str, square: int) -> None:
        self.set_piece(piece, color, square)

    def clear_piece(self, square: int) -> None:
        for key in self._boards:
            self._boards[key] = clear_bit_at(self._boards[key], square)

    def remove_piece(self, square: int) -> None:
        self.clear_piece(square)

    def get_piece_at(self, square: int) -> tuple[str, str] | None:
        for (piece, color), bitboard in self._boards.items():
            if get_bit_at(bitboard, square):
                return piece, color
        return None

    def move_piece(self, from_square: int, to_square: int) -> None:
        if from_square == to_square:
            raise ValueError("can't move to the same square")

        found = self.get_piece_at(from_square)
        if found is None:
            raise ValueError("no piece on from_square")

        piece, color = found
        self.clear_piece(from_square)
        self.set_piece(piece, color, to_square)

    @property
    def white_pieces(self) -> int:
        bitboard = 0
        for piece in PIECES:
            bitboard |= self._boards[(piece, WHITE)]
        return bitboard

    @property
    def black_pieces(self) -> int:
        bitboard = 0
        for piece in PIECES:
            bitboard |= self._boards[(piece, BLACK)]
        return bitboard

    @property
    def all_pieces(self) -> int:
        return self.white_pieces | self.black_pieces

    @property
    def white_occupancy(self) -> int:
        return self.white_pieces

    @property
    def black_occupancy(self) -> int:
        return self.black_pieces

    @property
    def occupancy(self) -> int:
        return self.all_pieces

    @staticmethod
    def square_to_algebraic(square: int) -> str:
        if not 0 <= square < NUM_SQUARES:
            raise ValueError("must be in [0, 63]")
        return FILES[square % BOARD_SIZE] + RANKS[square // BOARD_SIZE]

    @staticmethod
    def algebraic_to_square(pos: str) -> int:
        if len(pos) != 2 or pos[0] not in FILES or pos[1] not in RANKS:
            raise ValueError("pos must be like 'e4'")
        return FILES.index(pos[0]) + BOARD_SIZE * RANKS.index(pos[1])
    
    def find_shah(self, color: str) -> int | None:
     """
     Retourne la case du Shah de la couleur donnée
     """
     bitboard = self._boards[(SHAH, color)]
     if bitboard == 0:
        return None
     return get_lsb(bitboard)
    
   

    def find_shah(self, color: str) -> int | None:
        """
        Retourne la case du Shah de la couleur donnée.
        """
        bitboard = self._boards[(SHAH, color)]
        if bitboard == 0:
            return None
        return get_lsb(bitboard)

    def apply_move(self, move: Move) -> tuple[str, str] | None:
        """
        Joue le coup sur le board.
        Retourne la pièce capturée ou None.
        """
        captured = self.get_piece_at(move.to_square)       # sauvegarde la pièce capturée
        self.move_piece(move.from_square, move.to_square)  # déplace la pièce
        return captured                                     # nécessaire pour undo_move

    def undo_move(self, move: Move, captured: tuple[str, str] | None) -> None:
        """
        Annule le coup joué par apply_move.
        Remet la pièce à l'origine et restore la pièce capturée.
        """
        self.move_piece(move.to_square, move.from_square)  # remet la pièce à l'origine
        if captured is not None:
            piece, color = captured
            self.set_piece(piece, color, move.to_square)   # restore la pièce capturée
    
