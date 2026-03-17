from dataclasses import dataclass
from typing import Optional


# by default we need
# __init__ (constructor) so we can do move(0, 16, "pawn", "white")
@dataclass(frozen=True)
class Move:
    from_square: int
    to_square: int
    piece_type: str
    color: str
    # captured piece or none
    captured_piece: Optional[str] = None
