"""
Move generation and rule validation for Shatranj.

Classes:
  - MoveGenerator  : generates pseudo-legal moves for each piece type
                     (pawn, rook, knight, ferz, shah, alfil)
  - MoveValidator  : validates move geometry (no wrap-around, correct pattern)
  - PieceValidator : piece-specific validation helpers
  - RulesEngine    : coordinates generation + legality filtering
                     (removes moves that leave the Shah in check)

Key methods (RulesEngine):
  - generate_pseudo_legal_moves : fast, no check detection
  - generate_legal_moves        : filters out moves leaving Shah in check
  - is_checkmate                : no legal moves + in check
  - is_stalemate                : no legal moves + not in check
  - is_bare_king                : only Shah remaining
"""

__all__ = []
