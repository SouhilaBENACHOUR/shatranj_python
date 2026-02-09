from typing import Optional, Tuple
from shatranj.data.bitboards.bitboard import Bitboard


class Board:
    def __init__(self, bitboard: Optional[Bitboard] = None) -> None:
        # If bitboard is None -> create a new Bitboard()
        self._bitboard = bitboard if bitboard is not None else Bitboard()

    def get_piece_at(self, square: int) -> Optional[Tuple[str, str]]:
        # returns the piece on a square, if any.
        #   either a tuple (piece, color) OR None
        return self._bitboard.get_piece_at(square)

    def place_piece(self, piece: str, color: str, square: int) -> None:
        self._bitboard.set_piece(piece, color, square)

    def remove_piece(self, square: int) -> None:
        self._bitboard.clear_piece(square)

    def move_piece(self, from_square: int, to_square: int) -> None:

        if from_square == to_square:
            raise ValueError("can't move to the same square")

        # Try to find a piece at the origin square.
        found = self.get_piece_at(from_square)

        # If there is no piece there we cannot move anything
        if found is None:
            raise ValueError("no piece on from_square")

        # Unpack the tuple (piece, color)
        piece, color = found

        # we clear the origin square, then place the piece on the destination square
        # this move function acts like a capture overwrite it dosn't verify rules
        self._bitboard.clear_piece(from_square)
        self._bitboard.set_piece(piece, color, to_square)

    @property
    def white_occupancy(self) -> int:
        # This is a read-only "property" we can do
        #   board.white_occupancy
        # instead of
        #   board.white_occupancy()
        # returns an int bitboard where bits=1 are occupied squares
        return self._bitboard.white_pieces

    @property
    def black_occupancy(self) -> int:
        # for BLACK pieces
        return self._bitboard.black_pieces

    @property
    def occupancy(self) -> int:
        #   white_pieces | black_pieces
        return self._bitboard.all_pieces
