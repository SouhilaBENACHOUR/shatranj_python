"""
transposition_table.py - Zobrist Hashing + Transposition Table

Role: avoid recalculating already-seen positions.

Zobrist Hashing:
  - Each (piece, color, square) combination gets a random 64-bit number
  - The position key = XOR of all pieces on the board
  - When a move is played, update the key in O(1) with XOR

Transposition Table:
  - key   -> {score, depth, flag}
  - flag  : EXACT, LOWER_BOUND, UPPER_BOUND
  - Size  : fixed at MAX_SIZE entries (oldest entries are overwritten)
"""

import random
from shatranj.utils.constants import WHITE, BLACK, PAWN, ROOK, KNIGHT, FERZ, SHAH, ALFIL

# --- Flags for transposition table entries ---
EXACT = 0  # exact score (all children explored)
LOWER_BOUND = 1  # score is at least this value (beta cutoff)
UPPER_BOUND = 2  # score is at most this value (alpha cutoff)

# --- Constants ---
MAX_SIZE = 10_000  # maximum number of entries in the table
ALL_PIECES = [PAWN, ROOK, KNIGHT, FERZ, SHAH, ALFIL]
ALL_COLORS = [WHITE, BLACK]
NUM_SQUARES = 64


class ZobristHasher:
    """
    Computes and updates Zobrist hash keys for board positions.

    The key uniquely identifies a position:
      key = XOR of zobrist_table[piece][color][square] for all pieces
          XOR black_to_move (if it is BLACK's turn)

    Updating after a move is O(1):
      key XOR= zobrist_table[piece][color][from_square]  # remove piece
      key XOR= zobrist_table[piece][color][to_square]    # place piece
      key XOR= black_to_move_key                         # flip turn
    """

    def __init__(self) -> None:
        rng = random.Random(42)  # fixed seed for reproducibility

        # random 64-bit number for each (piece, color, square)
        self._table: dict[tuple, int] = {}
        for piece in ALL_PIECES:
            for color in ALL_COLORS:
                for square in range(NUM_SQUARES):
                    self._table[(piece, color, square)] = rng.getrandbits(64)

        # random number for BLACK to move
        self._black_to_move = rng.getrandbits(64)

    def compute_key(self, board, color: str) -> int:
        """
        Compute the full Zobrist key for the current position.

        Called once at the start of a search.
        After that, use update_key() for incremental updates.
        """
        key = 0

        for piece in ALL_PIECES:
            for c in ALL_COLORS:
                bb = board._boards.get((piece, c), 0)
                while bb:
                    sq = (bb & -bb).bit_length() - 1
                    key ^= self._table[(piece, c, sq)]
                    bb &= bb - 1

        if color == BLACK:
            key ^= self._black_to_move

        return key

    def update_key(
        self,
        key: int,
        piece: str,
        color: str,
        from_square: int,
        to_square: int,
        captured_piece: str | None,
        captured_color: str | None,
        result_piece: str | None = None,
    ) -> int:
        """
        Update the Zobrist key after a move in O(1).
        """
        # remove piece from source square
        key ^= self._table[(piece, color, from_square)]

        # place piece on destination square
        key ^= self._table[(result_piece or piece, color, to_square)]

        # remove captured piece if any
        if captured_piece is not None and captured_color is not None:
            # captured_piece may be a tuple (piece_type, color) or just a string
            if isinstance(captured_piece, tuple):
                actual_piece = captured_piece[0]
                actual_color = captured_piece[1]
            else:
                actual_piece = captured_piece
                actual_color = captured_color
            key ^= self._table[(actual_piece, actual_color, to_square)]

        # flip turn
        key ^= self._black_to_move

        return key


class TranspositionTable:
    """
    Hash table that stores previously evaluated positions.

    Each entry stores:
      score : float  -> the evaluated score
      depth : int    -> at which depth it was evaluated
      flag  : int    -> EXACT, LOWER_BOUND, or UPPER_BOUND

    When the table is full, new entries overwrite old ones
    (simple replacement strategy).
    """

    def __init__(self, max_size: int = MAX_SIZE) -> None:
        self._max_size = max_size
        self._table: dict[int, dict] = {}

    def get(self, key: int, depth: int, alpha: float, beta: float):
        """
        Look up a position in the table.

        Returns (score, should_use) where should_use is True if the
        entry is valid and can be used to prune the search.

        An entry is valid if:
          - it exists in the table
          - it was evaluated at least as deep as requested
          - the flag matches the current alpha/beta window
        """
        entry = self._table.get(key)
        if entry is None:
            return None, False

        # only use entries evaluated at sufficient depth
        if entry["depth"] < depth:
            return None, False

        score = entry["score"]
        flag = entry["flag"]

        if flag == EXACT:
            return score, True

        if flag == LOWER_BOUND and score >= beta:
            return score, True

        if flag == UPPER_BOUND and score <= alpha:
            return score, True

        return None, False

    def store(self, key: int, score: float, depth: int, flag: int) -> None:
        """
        Store a position evaluation in the table.

        If the table is full, overwrite the existing entry
        (always-replace strategy — simple but effective).
        """
        # if full and key not already present, make room
        if len(self._table) >= self._max_size and key not in self._table:
            # remove a random entry (simple eviction policy)
            oldest_key = next(iter(self._table))
            del self._table[oldest_key]

        self._table[key] = {
            "score": score,
            "depth": depth,
            "flag": flag,
        }

    def clear(self) -> None:
        """Clear all entries from the table."""
        self._table.clear()

    def size(self) -> int:
        """Return the number of entries currently in the table."""
        return len(self._table)
