"""
evaluator.py - Evaluation functions for Shatranj positions

Three evaluation functions:
  - material    : counts piece values only
  - positional  : material + bonus/malus based on piece position
  - advanced    : positional + mobility + center control + shah safety
"""

from shatranj.domain.core.board import Board
from shatranj.domain.rules.rules_engine import RulesEngine
from shatranj.utils.exceptions import EvaluatorError
from shatranj.utils.constants import (
    WHITE,
    BLACK,
    PAWN,
    ROOK,
    KNIGHT,
    FERZ,
    SHAH,
    ALFIL,
)

# Material values
PIECE_VALUES = {
    PAWN: 1,
    ALFIL: 2,
    FERZ: 2,
    KNIGHT: 6,
    ROOK: 9,
    SHAH: 0,
}

# Positional bonus tables (64 squares, rank 0 = a1, rank 7 = h8)
# Positive = good for WHITE, will be mirrored for BLACK

PAWN_TABLE = [
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    5,
    5,
    5,
    5,
    5,
    5,
    5,
    5,
    1,
    1,
    2,
    3,
    3,
    2,
    1,
    1,
    0,
    0,
    1,
    2,
    2,
    1,
    0,
    0,
    0,
    0,
    0,
    2,
    2,
    0,
    0,
    0,
    0,
    -1,
    -1,
    0,
    0,
    -1,
    -1,
    0,
    0,
    1,
    1,
    -2,
    -2,
    1,
    1,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
]

KNIGHT_TABLE = [
    -5,
    -4,
    -3,
    -3,
    -3,
    -3,
    -4,
    -5,
    -4,
    -2,
    0,
    0,
    0,
    0,
    -2,
    -4,
    -3,
    0,
    1,
    2,
    2,
    1,
    0,
    -3,
    -3,
    1,
    2,
    3,
    3,
    2,
    1,
    -3,
    -3,
    0,
    2,
    3,
    3,
    2,
    0,
    -3,
    -3,
    1,
    1,
    2,
    2,
    1,
    1,
    -3,
    -4,
    -2,
    0,
    1,
    1,
    0,
    -2,
    -4,
    -5,
    -4,
    -3,
    -3,
    -3,
    -3,
    -4,
    -5,
]

ROOK_TABLE = [
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    1,
    2,
    2,
    2,
    2,
    2,
    2,
    1,
    -1,
    0,
    0,
    0,
    0,
    0,
    0,
    -1,
    -1,
    0,
    0,
    0,
    0,
    0,
    0,
    -1,
    -1,
    0,
    0,
    0,
    0,
    0,
    0,
    -1,
    -1,
    0,
    0,
    0,
    0,
    0,
    0,
    -1,
    -1,
    0,
    0,
    0,
    0,
    0,
    0,
    -1,
    0,
    0,
    0,
    1,
    1,
    0,
    0,
    0,
]

FERZ_TABLE = [
    -2,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -2,
    -1,
    0,
    0,
    0,
    0,
    0,
    0,
    -1,
    -1,
    0,
    1,
    1,
    1,
    1,
    0,
    -1,
    -1,
    0,
    1,
    2,
    2,
    1,
    0,
    -1,
    -1,
    0,
    1,
    2,
    2,
    1,
    0,
    -1,
    -1,
    0,
    1,
    1,
    1,
    1,
    0,
    -1,
    -1,
    0,
    1,
    0,
    0,
    1,
    0,
    -1,
    -2,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -2,
]

ALFIL_TABLE = [
    -2,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -2,
    -1,
    0,
    0,
    0,
    0,
    0,
    0,
    -1,
    -1,
    0,
    1,
    1,
    1,
    1,
    0,
    -1,
    -1,
    0,
    1,
    2,
    2,
    1,
    0,
    -1,
    -1,
    0,
    1,
    2,
    2,
    1,
    0,
    -1,
    -1,
    0,
    1,
    1,
    1,
    1,
    0,
    -1,
    -1,
    0,
    0,
    0,
    0,
    0,
    0,
    -1,
    -2,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -2,
]

SHAH_TABLE_MIDGAME = [
    -3,
    -4,
    -4,
    -5,
    -5,
    -4,
    -4,
    -3,
    -3,
    -4,
    -4,
    -5,
    -5,
    -4,
    -4,
    -3,
    -3,
    -4,
    -4,
    -5,
    -5,
    -4,
    -4,
    -3,
    -3,
    -4,
    -4,
    -5,
    -5,
    -4,
    -4,
    -3,
    -2,
    -3,
    -3,
    -4,
    -4,
    -3,
    -3,
    -2,
    -1,
    -2,
    -2,
    -2,
    -2,
    -2,
    -2,
    -1,
    2,
    2,
    0,
    0,
    0,
    0,
    2,
    2,
    2,
    3,
    1,
    0,
    0,
    1,
    3,
    2,
]

POSITION_TABLES = {
    PAWN: PAWN_TABLE,
    KNIGHT: KNIGHT_TABLE,
    ROOK: ROOK_TABLE,
    FERZ: FERZ_TABLE,
    ALFIL: ALFIL_TABLE,
    SHAH: SHAH_TABLE_MIDGAME,
}

# Center squares bonus for advanced evaluation
CENTER_SQUARES = {27, 28, 35, 36}  # d4, e4, d5, e5
NEAR_CENTER = {18, 19, 20, 21, 26, 29, 34, 37, 42, 43, 44, 45}


class Evaluator:
    """
    Evaluation functions for Shatranj positions.

    Three modes:
      material   → piece values only (fast)
      positional → material + position tables (medium)
      advanced   → positional + mobility + center + shah safety (slow)
    """

    def __init__(self, mode: str = "advanced") -> None:
        if mode not in ("material", "positional", "advanced"):
            raise EvaluatorError(
                f"Unknown evaluation mode: '{mode}'. "
                "Use material, positional or advanced."
            )
        self._mode = mode

    def evaluate(self, board: Board, color: str) -> float:
        """
        Return a score for the position from 'color' perspective.

        Positive = good for color, negative = good for opponent.
        """
        if self._mode == "material":
            return self._eval_material(board, color)
        if self._mode == "positional":
            return self._eval_positional(board, color)
        return self._eval_advanced(board, color)

    # ------------------------------------------------------------------
    # Function 1: Material evaluation
    # ------------------------------------------------------------------

    def _eval_material(self, board: Board, color: str) -> float:
        """
        Count the material value of all pieces.

        Score = sum of own pieces - sum of opponent pieces.
        """
        opponent = BLACK if color == WHITE else WHITE
        score = 0

        for piece, value in PIECE_VALUES.items():
            own_bb = board._boards.get((piece, color), 0)
            opp_bb = board._boards.get((piece, opponent), 0)
            score += value * bin(own_bb).count("1")
            score -= value * bin(opp_bb).count("1")

        return score

    # ------------------------------------------------------------------
    # Function 2: Positional evaluation
    # ------------------------------------------------------------------

    def _eval_positional(self, board: Board, color: str) -> float:
        """
        Material + bonus/malus based on piece position.

        Each piece gets a bonus depending on which square it occupies.
        Positions are mirrored for BLACK (rank 0 becomes rank 7).
        """
        opponent = BLACK if color == WHITE else WHITE
        score = self._eval_material(board, color)

        for piece, table in POSITION_TABLES.items():
            # own pieces: use table directly
            own_bb = board._boards.get((piece, color), 0)
            sq = 0
            bb = own_bb
            while bb:
                lsb = bb & (-bb)
                sq = lsb.bit_length() - 1
                # mirror for BLACK (rank 7-rank)
                idx = sq if color == WHITE else (7 - sq // 8) * 8 + sq % 8
                score += table[idx] * 0.1
                bb &= bb - 1

            # opponent pieces: subtract
            opp_bb = board._boards.get((piece, opponent), 0)
            bb = opp_bb
            while bb:
                lsb = bb & (-bb)
                sq = lsb.bit_length() - 1
                idx = sq if opponent == WHITE else (7 - sq // 8) * 8 + sq % 8
                score -= table[idx] * 0.1
                bb &= bb - 1

        return score

    # ------------------------------------------------------------------
    # Function 3: Advanced evaluation
    # ------------------------------------------------------------------

    def _eval_advanced(self, board: Board, color: str) -> float:
        """
        Positional + mobility + center control + shah safety.

        Mobility    : more legal moves = better position
        Center      : pieces near the center get a bonus
        Shah safety : shah far from center = safer
        """
        opponent = BLACK if color == WHITE else WHITE
        score = self._eval_positional(board, color)

        # --- Mobility ---
        # count pieces that have moves available (approximation without full
        # legal gen)
        own_mobility = self._count_mobility(board, color)
        opp_mobility = self._count_mobility(board, opponent)
        score += (own_mobility - opp_mobility) * 0.05

        # --- Center control ---
        own_center = self._center_control(board, color)
        opp_center = self._center_control(board, opponent)
        score += (own_center - opp_center) * 0.15

        # --- Shah safety ---
        own_safety = self._shah_safety(board, color)
        opp_safety = self._shah_safety(board, opponent)
        score += (own_safety - opp_safety) * 0.1

        return score

    def _count_mobility(self, board: Board, color: str) -> int:
        """
        Count the number of squares reachable by all pieces of 'color'.
        Uses a fast approximation (pseudo-legal moves count).
        """

        gen = RulesEngine()
        moves = gen.generate_pseudo_legal_moves(board, color)
        return len(moves)

    def _center_control(self, board: Board, color: str) -> int:
        """
        Count pieces of 'color' on center or near-center squares.

        Center squares (d4, e4, d5, e5) → 2 points each
        Near-center squares              → 1 point each
        """
        score = 0
        for piece in PIECE_VALUES:
            bb = board._boards.get((piece, color), 0)
            while bb:
                sq = (bb & -bb).bit_length() - 1
                if sq in CENTER_SQUARES:
                    score += 2
                if sq in NEAR_CENTER:
                    score += 1
                bb &= bb - 1
        return score

    def _shah_safety(self, board: Board, color: str) -> int:
        """
        Evaluate shah safety.

        A shah on the back rank is safer (positive score).
        A shah in the center is dangerous (negative score).
        """
        from shatranj.data.bitboards.bitboard import get_lsb

        shah_bb = board._boards.get((SHAH, color), 0)
        if not shah_bb:
            return 0

        sq = get_lsb(shah_bb)
        rank = sq // 8

        # back rank (rank 0 for WHITE, rank 7 for BLACK) = safest
        if color == WHITE:
            return 3 - rank  # rank 0 → +3, rank 7 → -4
        return rank - 4  # rank 7 → +3, rank 0 → -4
