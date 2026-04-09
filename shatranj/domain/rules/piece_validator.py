from abc import ABC, abstractmethod

from shatranj.domain.core.board import Board
from shatranj.domain.core.move import Move
from shatranj.utils.constants import BOARD_SIZE, WHITE

# ------------------------------------------------------------------ #
#  ABSTRACT BASE CLASS (Strategy interface)                           #
# ------------------------------------------------------------------ #


class PieceValidator(ABC):
    """
    Abstract base class for piece-specific move validators.
    Each piece type implements its own validation strategy.
    """

    @abstractmethod
    def is_valid(self, board: Board, move: Move) -> bool:
        raise NotImplementedError


# ------------------------------------------------------------------ #
#  PAWN                                                               #
# ------------------------------------------------------------------ #


class PawnValidator(PieceValidator):
    """
    Pawn movement rules:

      - Forward: 1 square straight ahead, must be empty
      - Capture: 1 square diagonally forward, must contain enemy piece

    We use divmod to get rank and file separately, preventing edge-wrapping
    bugs.
    """

    def is_valid(self, board: Board, move: Move) -> bool:
        frm_rank, frm_file = divmod(move.from_square, BOARD_SIZE)
        to_rank, to_file = divmod(move.to_square, BOARD_SIZE)

        direction = 1 if move.color == WHITE else -1
        rank_diff = to_rank - frm_rank
        file_diff = abs(to_file - frm_file)

        # Forward move: 1 rank forward, same file, empty square
        if rank_diff == direction and file_diff == 0:
            return board.get_piece_at(move.to_square) is None

        # Diagonal capture: 1 rank forward, 1 file difference, enemy piece
        if rank_diff == direction and file_diff == 1:
            target = board.get_piece_at(move.to_square)
            return target is not None and target[1] != move.color

        return False


# ------------------------------------------------------------------ #
#  ROOK                                                               #
# ------------------------------------------------------------------ #


class RookValidator(PieceValidator):
    """
    Rook moves horizontally or vertically any distance.
    Cannot jump over pieces - we check all intermediate squares.
    """

    def is_valid(self, board: Board, move: Move) -> bool:
        frm_rank, frm_file = divmod(move.from_square, BOARD_SIZE)
        to_rank, to_file = divmod(move.to_square, BOARD_SIZE)

        # Diagonal move -> invalid
        if frm_file != to_file and frm_rank != to_rank:
            return False

        # Determine step direction
        if frm_file == to_file:
            step = 8 if to_rank > frm_rank else -8
        else:
            step = 1 if to_file > frm_file else -1

        # Check all intermediate squares
        sq = move.from_square + step
        while sq != move.to_square:
            if board.get_piece_at(sq) is not None:
                return False
            sq += step

        return True


# ------------------------------------------------------------------ #
#  KNIGHT                                                             #
# ------------------------------------------------------------------ #


class KnightValidator(PieceValidator):
    """
    Knight moves in L-shape: (±1, ±2) or (±2, ±1).
    Can jump over pieces.
    """

    def is_valid(self, board: Board, move: Move) -> bool:
        frm_rank, frm_file = divmod(move.from_square, BOARD_SIZE)
        to_rank, to_file = divmod(move.to_square, BOARD_SIZE)

        rank_diff = abs(to_rank - frm_rank)
        file_diff = abs(to_file - frm_file)

        return (rank_diff == 2 and file_diff == 1) or (
            rank_diff == 1 and file_diff == 2
        )


# ------------------------------------------------------------------ #
#  ALFIL                                                              #
# ------------------------------------------------------------------ #


class AlfilValidator(PieceValidator):
    """
    Alfil jumps exactly 2 squares diagonally.
    Can jump over pieces. Stays on same color squares.
    """

    def is_valid(self, board: Board, move: Move) -> bool:
        frm_rank, frm_file = divmod(move.from_square, BOARD_SIZE)
        to_rank, to_file = divmod(move.to_square, BOARD_SIZE)

        rank_diff = abs(to_rank - frm_rank)
        file_diff = abs(to_file - frm_file)

        return rank_diff == 2 and file_diff == 2


# ------------------------------------------------------------------ #
#  FERZ                                                               #
# ------------------------------------------------------------------ #


class FerzValidator(PieceValidator):
    """
    Ferz moves exactly 1 square diagonally.
    Ancestor of the modern Queen.
    """

    def is_valid(self, board: Board, move: Move) -> bool:
        frm_rank, frm_file = divmod(move.from_square, BOARD_SIZE)
        to_rank, to_file = divmod(move.to_square, BOARD_SIZE)

        rank_diff = abs(to_rank - frm_rank)
        file_diff = abs(to_file - frm_file)

        return rank_diff == 1 and file_diff == 1


# ------------------------------------------------------------------ #
#  SHAH                                                               #
# ------------------------------------------------------------------ #


class ShahValidator(PieceValidator):
    """
    Shah (King) moves exactly 1 square in any direction (8 possibilities).
    Using max(rank_diff, file_diff) == 1 elegantly covers all directions.
    """

    def is_valid(self, board: Board, move: Move) -> bool:
        frm_rank, frm_file = divmod(move.from_square, BOARD_SIZE)
        to_rank, to_file = divmod(move.to_square, BOARD_SIZE)

        rank_diff = abs(to_rank - frm_rank)
        file_diff = abs(to_file - frm_file)

        return max(rank_diff, file_diff) == 1
