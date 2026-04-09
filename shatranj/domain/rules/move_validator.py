from shatranj.domain.core.board import Board
from shatranj.domain.core.move import Move
from shatranj.domain.rules.BlitzClock import BlitzClock
from shatranj.utils.constants import PAWN, ROOK, KNIGHT, ALFIL
from shatranj.utils.constants import FERZ, SHAH, NUM_SQUARES
from shatranj.domain.rules.piece_validator import (
    PieceValidator,
    PawnValidator,
    RookValidator,
    KnightValidator,
    AlfilValidator,
    FerzValidator,
    ShahValidator,
)


class MoveValidator:
    """
    Validates moves by delegating to piece-specific validators.
    Includes logic for Blitz games to check for time expiration.
    """

    # Map each piece type to its validator (Strategy pattern)
    _validators: dict[str, PieceValidator] = {
        PAWN: PawnValidator(),
        ROOK: RookValidator(),
        KNIGHT: KnightValidator(),
        ALFIL: AlfilValidator(),
        FERZ: FerzValidator(),
        SHAH: ShahValidator(),
    }

    def is_valid_move(self, board: Board, move: Move, clock: BlitzClock = None) -> bool:
        # --- Blitz Logic ---
        # If a clock is used, check if the player ran out of time
        if clock is not None:
            if clock.is_flagged(move.color):
                return False

        # --- General Move Logic ---
        # Bounds check
        if not 0 <= move.from_square < NUM_SQUARES:
            return False
        if not 0 <= move.to_square < NUM_SQUARES:
            return False

        # Cannot stay on the same square
        if move.from_square == move.to_square:
            return False

        # Must have a piece on from_square
        origin = board.get_piece_at(move.from_square)
        if origin is None:
            return False

        # Piece must match the move (type and color)
        piece_type, color = origin
        if (piece_type, color) != (move.piece_type, move.color):
            return False

        # Cannot capture own piece
        target = board.get_piece_at(move.to_square)
        if target is not None and target[1] == color:
            return False

        # Delegate to the appropriate piece validator
        validator = self._validators.get(piece_type)
        if validator is None:
            return False

        return validator.is_valid(board, move)
