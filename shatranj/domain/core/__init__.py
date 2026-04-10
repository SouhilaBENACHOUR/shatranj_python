"""
Core domain objects for Shatranj.

Classes:
  - Board : 64-square board represented with 12 bitboards
            (6 piece types × 2 colors)
  - Move  : immutable value object representing a single move
            (from_square, to_square, piece_type, color, captured_piece)
"""

__all__ = []