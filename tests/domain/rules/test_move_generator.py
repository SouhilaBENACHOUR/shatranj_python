from shatranj.domain.core.board import Board
from shatranj.domain.rules.move_generator import MoveGenerator
from shatranj.utils.constants import WHITE, BLACK, PAWN, ROOK
from shatranj.data.bitboards.bitboard import Bitboard

def test_generate_pawn_capture():
    gen = MoveGenerator()
    board = Board(Bitboard(setup=False))

    board.place_piece(PAWN, WHITE, 8)   # a2
    board.place_piece(PAWN, BLACK, 17)  # b3
    moves = gen.generate_pawn_moves(board, WHITE) #test also moves
    assert any(m.to_square == 17 for m in moves)


def test_generate_rook_moves():
    gen = MoveGenerator()
    board = Board(Bitboard(setup=False))

    board.place_piece(ROOK, WHITE, 0)  # a1
    moves = gen.generate_rook_moves(board, WHITE)
    # rook should be able to go to a2 (8) and b1 (1)
    assert any(m.to_square == 8 for m in moves)
    assert any(m.to_square == 1 for m in moves)
