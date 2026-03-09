from shatranj.domain.core.board import Board
from shatranj.domain.core.move import Move
from shatranj.utils.constants import WHITE, BLACK, PAWN, ROOK, KNIGHT, FERZ, SHAH, ALFIL
from shatranj.utils.constants import BOARD_SIZE, NUM_SQUARES

class MoveGenerator:
    def generate_pawn_moves(self, board: Board, color: str) -> list[Move]:
        moves = []
        direction = 1 if color == WHITE else -1

        # scan all squares for pawns of this color
        for sq in range(NUM_SQUARES):
            piece = board.get_piece_at(sq)
            if piece is None:
                continue
            p_type, p_color = piece
            if p_type != PAWN or p_color != color:
                continue

            # forward one
            to_sq = sq + BOARD_SIZE * direction
            if 0 <= to_sq < NUM_SQUARES and board.get_piece_at(to_sq) is None:
                moves.append(Move(sq, to_sq, PAWN, color))

            # capture diagonals
            from_file = sq % BOARD_SIZE
            for diag in (sq + 7 * direction, sq + 9 * direction):
                if not (0 <= diag < NUM_SQUARES):
                    continue
                if abs((diag % BOARD_SIZE) - from_file) != 1:
                    continue
                target = board.get_piece_at(diag)
                if target is not None and target[1] != color:
                    moves.append(Move(sq, diag, PAWN, color, captured_piece=target[0]))

        return moves

    def generate_rook_moves(self, board: Board, color: str) -> list[Move]:
        moves = []

        for sq in range(NUM_SQUARES):
            piece = board.get_piece_at(sq)
            if piece is None:
                continue
            p_type, p_color = piece
            if p_type != ROOK or p_color != color:
                continue

            # four directions
            for step in (BOARD_SIZE, -BOARD_SIZE, 1, -1):
                cur = sq + step
                while 0 <= cur < NUM_SQUARES:
                    # stop horizontally if file wraps
                    if step in (1, -1) and (cur // BOARD_SIZE) != (sq // BOARD_SIZE):
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
    def generate_knight_moves(self, board: Board, color: str) -> list[Move]:
        moves = []

        # The 8 possible knight jumps expressed as index deltas
        # +/-17 and +/-15 = jump of 2 ranks ± 1 file
        # +/-10 and +/- 6 = jump of 1 rank  ± 2 files
        KNIGHT_DELTAS = [+17, +15, +10, +6, -6, -10, -15, -17]

        for sq in range(NUM_SQUARES):
            # Get whatever is on square sq
            piece = board.get_piece_at(sq)

            # If the square is empty, skip it
            if piece is None:
                continue

            # Unpack the tuple (piece_type, color)
            p_type, p_color = piece

            # Only process knights of the right color
            if p_type != KNIGHT or p_color != color:
                continue

            # divmod(sq, 8) = (rank, file)  e.g: sq=10 → rank=1, file=2
            frm_rank, frm_file = divmod(sq, BOARD_SIZE)

            for delta in KNIGHT_DELTAS:
                to_sq = sq + delta

                # Check 1 : destination square must exist (0..63)
                if not (0 <= to_sq < NUM_SQUARES):
                    continue

                # Check 2 : anti-wrapping
                # A knight jump cannot "cross" the left/right edge of the board
                # Example : knight on h4 (sq=31), delta=+10 → to_sq=41
                #           rank=3→rank=5, file=7→file=1 : file diff = |7-1|=6 → INVALID
                to_rank, to_file = divmod(to_sq, BOARD_SIZE)

                # The file difference MUST be 1 or 2 (never 6 or 7)
                # If |dest_file - src_file| > 2, it's a board wrap → reject
                if abs(to_file - frm_file) > 2:
                    continue

                # Check what is on the destination square
                target = board.get_piece_at(to_sq)

                if target is None:
                    # Empty square → simple move
                    moves.append(Move(sq, to_sq, KNIGHT, color))
                elif target[1] != color:
                    # Square occupied by an enemy → capture
                    # target[1] = color of the target piece
                    moves.append(Move(sq, to_sq, KNIGHT, color, captured_piece=target[0]))
                # If target[1] == color → friendly piece, skip

        return moves
    
    def generate_ferz_moves(self, board: Board, color: str) -> list[Move]:
        moves = []

        # The 4 diagonal directions, one square only
        # +9 = one rank up,   one file right
        # +7 = one rank up,   one file left
        # -7 = one rank down, one file right
        # -9 = one rank down, one file left
        FERZ_DELTAS = [+9, +7, -7, -9]

        for sq in range(NUM_SQUARES):
            # Get whatever is on square sq
            piece = board.get_piece_at(sq)

            # If the square is empty, skip it
            if piece is None:
                continue

            # Unpack the tuple (piece_type, color)
            p_type, p_color = piece

            # Only process ferz of the right color
            if p_type != FERZ or p_color != color:
                continue

            # divmod(sq, 8) = (rank, file)  e.g: sq=28 → rank=3, file=4
            frm_rank, frm_file = divmod(sq, BOARD_SIZE)

            for delta in FERZ_DELTAS:
                to_sq = sq + delta

                # Check 1 : destination square must exist (0..63)
                if not (0 <= to_sq < NUM_SQUARES):
                    continue

                # Check 2 : anti-wrapping
                # exactly like the knight, a diagonal step cannot cross the board edge
                # Example : ferz on h4 (sq=31), delta=+9 → to_sq=40
                #           rank=3→rank=5, file=7→file=0 : file diff = |7-0|=7 → INVALID
                # a valid diagonal step always changes file by exactly 1
                to_rank, to_file = divmod(to_sq, BOARD_SIZE)

                # The file difference MUST be exactly 1
                # If it's 0 (vertical) or 7 (wrap) → reject
                if abs(to_file - frm_file) != 1:
                    continue

                # Check what is on the destination square
                target = board.get_piece_at(to_sq)

                if target is None:
                    # Empty square → simple move
                    moves.append(Move(sq, to_sq, FERZ, color))
                elif target[1] != color:
                    # Square occupied by an enemy → capture
                    moves.append(Move(sq, to_sq, FERZ, color, captured_piece=target[0]))
                # If target[1] == color → friendly piece, skip

        return moves
    
    def generate_shah_moves(self, board: Board, color: str) -> list[Move]:
        moves = []

        # The 8 possible directions : 4 orthogonal + 4 diagonal
        # +8 = one rank up          -8 = one rank down
        # +1 = one file right       -1 = one file left
        # +9 = one rank up,   one file right
        # +7 = one rank up,   one file left
        # -7 = one rank down, one file right
        # -9 = one rank down, one file left
        SHAH_DELTAS = [+8, -8, +1, -1, +9, +7, -7, -9]

        for sq in range(NUM_SQUARES):
            # Get whatever is on square sq
            piece = board.get_piece_at(sq)

            # If the square is empty, skip it
            if piece is None:
                continue

            # Unpack the tuple (piece_type, color)
            p_type, p_color = piece

            # Only process the shah of the right color
            if p_type != SHAH or p_color != color:
                continue

            # divmod(sq, 8) = (rank, file)  e.g: sq=28 → rank=3, file=4
            frm_rank, frm_file = divmod(sq, BOARD_SIZE)

            for delta in SHAH_DELTAS:
                to_sq = sq + delta

                # Check 1 : destination square must exist (0..63)
                if not (0 <= to_sq < NUM_SQUARES):
                    continue

                # Check 2 : anti-wrapping
                # one step can never change the file by more than 1
                # Example : shah on h4 (sq=31), delta=+1 → to_sq=32
                #           rank=3→rank=4, file=7→file=0 : file diff = |7-0|=7 → INVALID
                to_rank, to_file = divmod(to_sq, BOARD_SIZE)

                # The file difference MUST be 0 (vertical) or 1 (diagonal/horizontal)
                # If it's 7 → board wrap → reject
                if abs(to_file - frm_file) > 1:
                    continue

                # Check what is on the destination square
                target = board.get_piece_at(to_sq)

                if target is None:
                    # Empty square → simple move
                    moves.append(Move(sq, to_sq, SHAH, color))
                elif target[1] != color:
                    # Square occupied by an enemy → capture
                    moves.append(Move(sq, to_sq, SHAH, color, captured_piece=target[0]))
                # If target[1] == color → friendly piece, skip

        return moves
    
    def generate_alfil_moves(self, board: Board, color: str) -> list[Move]:
        moves = []

        # The 4 diagonal jumps of exactly 2 squares
        # +18 = two ranks up,   two files right
        # +14 = two ranks up,   two files left
        # -14 = two ranks down, two files right
        # -18 = two ranks down, two files left
        ALFIL_DELTAS = [+18, +14, -14, -18]

        for sq in range(NUM_SQUARES):
            # Get whatever is on square sq
            piece = board.get_piece_at(sq)

            # If the square is empty, skip it
            if piece is None:
                continue

            # Unpack the tuple (piece_type, color)
            p_type, p_color = piece

            # Only process alfil of the right color
            if p_type != ALFIL or p_color != color:
                continue

            # divmod(sq, 8) = (rank, file)  e.g: sq=28 → rank=3, file=4
            frm_rank, frm_file = divmod(sq, BOARD_SIZE)

            for delta in ALFIL_DELTAS:
                to_sq = sq + delta

                # Check 1 : destination square must exist (0..63)
                if not (0 <= to_sq < NUM_SQUARES):
                    continue

                # Check 2 : anti-wrapping
                # a diagonal jump of 2 must always change the file by exactly 2
                # Example : alfil on g4 (sq=30), delta=+18 → to_sq=48
                #           rank=3→rank=6, file=6→file=0 : file diff = |6-0|=6 → INVALID
                # Example : alfil on h4 (sq=31), delta=+14 → to_sq=45
                #           rank=3→rank=5, file=7→file=5 : file diff = |7-5|=2 → VALID
                to_rank, to_file = divmod(to_sq, BOARD_SIZE)

                # The file difference MUST be exactly 2
                # If it's 6 (wrap from file 0 to file 6) → reject
                if abs(to_file - frm_file) != 2:
                    continue

                # Check what is on the destination square
                # Note : the alfil JUMPS, so intermediate squares are ignored
                target = board.get_piece_at(to_sq)

                if target is None:
                    # Empty square → simple move
                    moves.append(Move(sq, to_sq, ALFIL, color))
                elif target[1] != color:
                    # Square occupied by an enemy → capture
                    moves.append(Move(sq, to_sq, ALFIL, color, captured_piece=target[0]))
                # If target[1] == color → friendly piece, skip

        return moves
