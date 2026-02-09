from shatranj.domain.core.board import Board
from shatranj.domain.core.move import Move
from shatranj.utils.constants import WHITE, PAWN, ROOK


class MoveValidator:
    def is_valid_move(self, board: Board, move: Move) -> bool:
        if move.from_square == move.to_square:
            return False

        origin = board.get_piece_at(move.from_square)
        if origin is None:
            return False  #nothing to move

        piece_type, color = origin
        if (piece_type, color) != (move.piece_type, move.color):
            return False  # check if that square have the same piece we want to move

        target = board.get_piece_at(move.to_square)
        if target is not None and target[1] == color:
            return False  # can't capture our own piece

        # Dispatch by piece type (only pawn and rook implemented here)
        if piece_type == PAWN:
            return self._pawn_ok(board, move.from_square, move.to_square, color)

        if piece_type == ROOK:
            return self._rook_ok(board, move.from_square, move.to_square)

        return False  # other pieces not implemented

    def _pawn_ok(self, board: Board, frm: int, to: int, color: str) -> bool:
        # White goes "up" (+8), black goes "down" (-8)
        direction = 1 if color == WHITE else -1
        one_step = 8 * direction

        # Move forward 1: destination must be empty
        if to == frm + one_step:
            return board.get_piece_at(to) is None

        # Capture diagonally: destination must contain an enemy piece
        if to in (frm + 7 * direction, frm + 9 * direction):
            target = board.get_piece_at(to)
            return target is not None and target[1] != color

        return False

    def _rook_ok(self, board: Board, frm: int, to: int) -> bool:
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

