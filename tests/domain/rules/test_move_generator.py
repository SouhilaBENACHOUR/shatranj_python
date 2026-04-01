from shatranj.domain.core.board import Board
from shatranj.domain.rules.move_generator import MoveGenerator
from shatranj.utils.constants import WHITE, BLACK, PAWN, ROOK
from shatranj.utils.constants import KNIGHT, FERZ, SHAH, ALFIL


def test_generate_pawn_capture():
    gen = MoveGenerator()
    board = Board(setup=False)

    board.place_piece(PAWN, WHITE, 8)  # a2
    board.place_piece(PAWN, BLACK, 17)  # b3
    moves = gen.generate_pawn_moves(board, WHITE)  # test also moves
    assert any(m.to_square == 17 for m in moves)


def test_generate_rook_moves():
    gen = MoveGenerator()
    board = Board(setup=False)

    board.place_piece(ROOK, WHITE, 0)  # a1
    moves = gen.generate_rook_moves(board, WHITE)
    # rook should be able to go to a2 (8) and b1 (1)
    assert any(m.to_square == 8 for m in moves)
    assert any(m.to_square == 1 for m in moves)


def test_generate_knight_moves():
    gen = MoveGenerator()
    board = Board(setup=False)

    board.place_piece(KNIGHT, WHITE, 27)  # d4
    moves = gen.generate_knight_moves(board, WHITE)

    # knight on d4 can reach : e6(37→+10? non)
    # sq=27 : +17=44, +15=42, +10=37, +6=33, -6=21, -10=17, -15=12, -17=10
    assert any(m.to_square == 44 for m in moves)  # f6
    assert any(m.to_square == 42 for m in moves)  # e6
    assert any(m.to_square == 37 for m in moves)  # f5
    assert any(m.to_square == 33 for m in moves)  # b5
    assert len(moves) == 8  # all 8 jumps valid from center


def test_generate_knight_no_wrap():
    gen = MoveGenerator()
    board = Board(setup=False)

    board.place_piece(KNIGHT, WHITE, 7)  # h1 - corner, wrap risk
    moves = gen.generate_knight_moves(board, WHITE)

    # from h1 (sq=7) only 2 valid squares: g3(22) and f2(13)
    assert len(moves) == 2
    assert any(m.to_square == 22 for m in moves)  # g3
    assert any(m.to_square == 13 for m in moves)  # f2


def test_generate_knight_capture():
    gen = MoveGenerator()
    board = Board(setup=False)

    board.place_piece(KNIGHT, WHITE, 27)  # d4
    board.place_piece(PAWN, BLACK, 44)  # enemy on f6
    moves = gen.generate_knight_moves(board, WHITE)

    # the capture move must exist and have captured_piece set
    capture = next((m for m in moves if m.to_square == 44), None)
    assert capture is not None
    assert capture.captured_piece == PAWN


def test_generate_ferz_moves():
    gen = MoveGenerator()
    board = Board(setup=False)

    board.place_piece(FERZ, WHITE, 27)  # d4
    moves = gen.generate_ferz_moves(board, WHITE)

    # sq=27 : +9=36, +7=34, -7=20, -9=18
    assert any(m.to_square == 36 for m in moves)  # e5
    assert any(m.to_square == 34 for m in moves)  # c5
    assert any(m.to_square == 20 for m in moves)  # e3
    assert any(m.to_square == 18 for m in moves)  # c3
    assert len(moves) == 4  # exactly 4 diagonal squares


def test_generate_ferz_no_wrap():
    gen = MoveGenerator()
    board = Board(setup=False)

    board.place_piece(FERZ, WHITE, 7)  # h1 - corner, wrap risk
    moves = gen.generate_ferz_moves(board, WHITE)

    # from h1 (sq=7) only 1 valid square : g2(14)
    assert len(moves) == 1
    assert any(m.to_square == 14 for m in moves)  # g2


def test_generate_shah_moves():
    gen = MoveGenerator()
    board = Board(setup=False)

    board.place_piece(SHAH, WHITE, 27)  # d4
    moves = gen.generate_shah_moves(board, WHITE)

    # sq=27 : +8=35, -8=19, +1=28, -1=26, +9=36, +7=34, -7=20, -9=18
    assert len(moves) == 8  # all 8 directions valid from center


def test_generate_shah_no_wrap():
    gen = MoveGenerator()
    board = Board(setup=False)

    board.place_piece(SHAH, WHITE, 7)  # h1 - corner, wrap risk
    moves = gen.generate_shah_moves(board, WHITE)

    # from h1 (sq=7) only 3 valid squares : g1(6), g2(14), h2(15)
    assert len(moves) == 3


def test_generate_alfil_moves():
    gen = MoveGenerator()
    board = Board(setup=False)

    board.place_piece(ALFIL, WHITE, 27)  # d4
    moves = gen.generate_alfil_moves(board, WHITE)

    # sq=27 : +18=45, +14=41, -14=13, -18=9
    assert any(m.to_square == 45 for m in moves)  # f6
    assert any(m.to_square == 41 for m in moves)  # b6
    assert any(m.to_square == 13 for m in moves)  # f2
    assert any(m.to_square == 9 for m in moves)  # b2
    assert len(moves) == 4


def test_generate_alfil_no_wrap():
    gen = MoveGenerator()
    board = Board(setup=False)

    board.place_piece(ALFIL, WHITE, 7)  # h1 - corner, wrap risk
    moves = gen.generate_alfil_moves(board, WHITE)

    # from h1 (sq=7) : +18=25(b4? no → rank=0→2, file=7→1 diff=6 → INVALID)
    #                   +14=21(f3  → rank=0→2, file=7→5 diff=2 → VALID)
    #                   -14 and -18 → negative → out of board
    assert len(moves) == 1
    assert any(m.to_square == 21 for m in moves)  # f3
