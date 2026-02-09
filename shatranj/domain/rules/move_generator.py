from shatranj.domain.core.board import Board
from shatranj.domain.core.move import Move
from shatranj.utils.constants import WHITE, BLACK, PAWN, ROOK


class MoveGenerator:
    def generate_pawn_moves(self, board: Board, color: str) -> list[Move]:
        moves = []
        direction = 1 if color == WHITE else -1

        # scan all squares for pawns of this color
        for sq in range(64):
            piece = board.get_piece_at(sq)
            if piece is None:
                continue
            p_type, p_color = piece
            if p_type != PAWN or p_color != color:
                continue

            # forward one
            to_sq = sq + 8 * direction
            if 0 <= to_sq < 64 and board.get_piece_at(to_sq) is None:
                moves.append(Move(sq, to_sq, PAWN, color))

            # capture diagonals
            for diag in (sq + 7 * direction, sq + 9 * direction):
                if 0 <= diag < 64:
                    target = board.get_piece_at(diag)
                    if target is not None and target[1] != color:
                        moves.append(Move(sq, diag, PAWN, color, captured_piece=target[0]))

        return moves

    def generate_rook_moves(self, board: Board, color: str) -> list[Move]:
        moves = []

        for sq in range(64):
            piece = board.get_piece_at(sq)
            if piece is None:
                continue
            p_type, p_color = piece
            if p_type != ROOK or p_color != color:
                continue

            # four directions
            for step in (8, -8, 1, -1):
                cur = sq + step
                while 0 <= cur < 64:
                    # stop horizontally if file wraps
                    if step in (1, -1) and (cur // 8) != (sq // 8):
                        break

                    target = board.get_piece_at(cur)
                    if target is None:
                        moves.append(Move(sq, cur, ROOK, color))
                    else:
                        if target[1] != color:
                            moves.append(Move(sq, cur, ROOK, color, captured_piece=target[0]))
                        break  # blocked

                    cur += step

        return moves
