from shatranj.domain.core.board import Board
from shatranj.domain.core.move import Move
from shatranj.utils.constants import WHITE, PAWN, ROOK, KNIGHT, ALFIL, FERZ, SHAH


class MoveValidator:
    def is_valid_move(self, board: Board, move: Move) -> bool:
        if move.from_square == move.to_square:
            return False

        origin = board.get_piece_at(move.from_square)
        if origin is None:
            return False  #nothing to mov
        piece_type, color = origin
        if (piece_type, color) != (move.piece_type, move.color):
            return False  # check if that square have the same piece we want to move

        target = board.get_piece_at(move.to_square)
        if target is not None and target[1] == color:
            return False  # can't capture our own piece

        if piece_type == PAWN:
            return self._pawn_ok(board, move.from_square, move.to_square, color)

        if piece_type == ROOK:
            return self._rook_ok(board, move.from_square, move.to_square)

        if piece_type == KNIGHT:
            return self._knight_ok(move.from_square, move.to_square)
        
        if piece_type == ALFIL:
            return self._alfil_ok(move.from_square, move.to_square)
        
        if piece_type == FERZ:
            return self._ferz_ok(move.from_square, move.to_square)
        
        if piece_type == SHAH:
            return self._shah_ok(move.from_square, move.to_square)
        
        return False  # other pieces not implemented

    # ------------------------------------------------------------------ #
    #  PAWN                                                                #
    # ------------------------------------------------------------------ #

    def _pawn_ok(self, board: Board, frm: int, to: int, color: str) -> bool:
        """
        Pawn movement rules:
          - Forward: 1 square straight ahead, must be empty
          - Capture: 1 square diagonally forward, must contain enemy piece
       
        We use divmod to get rank and file separately, preventing edge-wrapping bugs.
        """
        frm_rank, frm_file = divmod(frm, 8)
        to_rank,  to_file  = divmod(to,  8)

        direction = 1 if color == WHITE else -1  # White moves up, Black moves down
        rank_diff = to_rank - frm_rank   # Signed: +1 forward, -1 backward
        file_diff = abs(to_file - frm_file)

        # Forward move: 1 rank forward, same file, empty square
        if rank_diff == direction and file_diff == 0:
            return board.get_piece_at(to) is None

        # Diagonal capture: 1 rank forward, 1 file difference, enemy piece
        if rank_diff == direction and file_diff == 1:
            target = board.get_piece_at(to)
            return target is not None and target[1] != color

        return False

    # ------------------------------------------------------------------ #
    #  ROOK                                                                #
    # ------------------------------------------------------------------ #

    def _rook_ok(self, board: Board, frm: int, to: int) -> bool:
        
        """
        Rook moves horizontally or vertically any distance.
        Cannot jump over pieces - we check all intermediate squares.
        """
        
        #   rank = square // 8  (row 0..7)
        #   file = square % 8   (column 0..7)
        #  divmod(28, 8) = (3, 4)
        #  rank=3, file=4 
        frm_rank, frm_file = divmod(frm, 8)
        to_rank, to_file = divmod(to, 8)

        # if file and rank change then it's a diagonal rook move -> invalid 
        if frm_file != to_file and frm_rank != to_rank:
            return False
        # vertical move 
        # going up one rank changes the index by +8
        # going down one rank changes the index by -8

        # Horizontal move (same rank):
        # going right one file changes the index by +1
        # going left one file changes the index by -1
        if frm_file == to_file:
            step = 8 if to_rank > frm_rank else -8
        else:
            step = 1 if to_file > frm_file else -1

        # Rooks cannot jump over pieces
        # So we check every square between from and to
        # We start with frm + step
        # and we stop right before reaching to
        sq = frm + step
        while sq != to:
            # if any square is occupied -> invalid move.
            if board.get_piece_at(sq) is not None:
                return False
            sq += step  # move to reach to 

        #valid rook move 
        return True

    # ------------------------------------------------------------------ #
    #  KNIGHT                                                              #
    # ------------------------------------------------------------------ #

    def _knight_ok(self, frm: int, to: int) -> bool:
        """
        Knight moves in L-shape: (±1, ±2) or (±2, ±1).
        Can jump over pieces.
        """
        frm_rank, frm_file = divmod(frm, 8)
        to_rank,  to_file  = divmod(to,  8)

        rank_diff = abs(to_rank - frm_rank)
        file_diff = abs(to_file - frm_file)

        return (rank_diff == 2 and file_diff == 1) or \
               (rank_diff == 1 and file_diff == 2)

    # ------------------------------------------------------------------ #
    #  ALFIL                                                               #
    # ------------------------------------------------------------------ #

    def _alfil_ok(self, frm: int, to: int) -> bool:
        """
        Alfil jumps exactly 2 squares diagonally.
        Can jump over pieces. Stays on same color squares.
        """
        frm_rank, frm_file = divmod(frm, 8)
        to_rank,  to_file  = divmod(to,  8)

        rank_diff = abs(to_rank - frm_rank)
        file_diff = abs(to_file - frm_file)

        return rank_diff == 2 and file_diff == 2

    # ------------------------------------------------------------------ #
    #  FERZ                                                                #
    # ------------------------------------------------------------------ #

    def _ferz_ok(self, frm: int, to: int) -> bool:
        """
        Ferz moves exactly 1 square diagonally.
        Ancestor of the modern Queen.
        """
        frm_rank, frm_file = divmod(frm, 8)
        to_rank,  to_file  = divmod(to,  8)

        rank_diff = abs(to_rank - frm_rank)
        file_diff = abs(to_file - frm_file)

        return rank_diff == 1 and file_diff == 1

    # ------------------------------------------------------------------ #
    #  SHAH                                                                #
    # ------------------------------------------------------------------ #

    def _shah_ok(self, frm: int, to: int) -> bool:
        """
        Shah (King) moves exactly 1 square in any direction (8 possibilities).
        Using max(rank_diff, file_diff) == 1 elegantly covers all directions.
        """
        frm_rank, frm_file = divmod(frm, 8)
        to_rank,  to_file  = divmod(to,  8)

        rank_diff = abs(to_rank - frm_rank)
        file_diff = abs(to_file - frm_file)

        return max(rank_diff, file_diff) == 1
