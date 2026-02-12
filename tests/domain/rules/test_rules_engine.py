from types import SimpleNamespace

from shatranj.data.bitboards.bitboard import Bitboard
from shatranj.domain.core.board import Board
from shatranj.domain.core.move import Move
from shatranj.domain.rules.rules_engine import RulesEngine
from shatranj.utils.constants import BLACK, KNIGHT, PAWN, ROOK, WHITE


def make_validator(allowed_moves: set[tuple[int, int]]):
    def is_valid_move(board: Board, move: Move) -> bool:
        return (move.from_square, move.to_square) in allowed_moves

    return SimpleNamespace(is_valid_move=is_valid_move)


def make_generator(moves: list[Move]):
    called_methods: list[str] = []

    def record(method_name: str) -> list[Move]:
        called_methods.append(method_name)
        return moves

    def generate_pawn_moves(board: Board, color: str) -> list[Move]:
        return record("pawn")

    def generate_rook_moves(board: Board, color: str) -> list[Move]:
        return record("rook")

    def generate_knight_moves(board: Board, color: str) -> list[Move]:
        return record("knight")

    def generate_alfil_moves(board: Board, color: str) -> list[Move]:
        return record("alfil")

    def generate_ferz_moves(board: Board, color: str) -> list[Move]:
        return record("ferz")

    def generate_shah_moves(board: Board, color: str) -> list[Move]:
        return record("shah")

    generator = SimpleNamespace(
        generate_pawn_moves=generate_pawn_moves,
        generate_rook_moves=generate_rook_moves,
        generate_knight_moves=generate_knight_moves,
        generate_alfil_moves=generate_alfil_moves,
        generate_ferz_moves=generate_ferz_moves,
        generate_shah_moves=generate_shah_moves,
    )
    return generator, called_methods


def test_is_valid_move_delegates_to_validator():
    board = Board(Bitboard(setup=False))
    move = Move(8, 16, PAWN, WHITE)
    validator = make_validator({(8, 16)})
    engine = RulesEngine(validator=validator)
    assert engine.is_valid_move(board, move)


def test_generate_pseudo_legal_moves_aggregates_all_generators():
    board = Board(Bitboard(setup=False))
    move = Move(8, 16, PAWN, WHITE)
    generator, called_methods = make_generator([move])
    engine = RulesEngine(generator=generator)
    moves = engine.generate_pseudo_legal_moves(board, WHITE)
    assert len(moves) == 6
    assert all(m == move for m in moves)
    assert called_methods == ["pawn", "rook", "knight", "alfil", "ferz", "shah"]


def test_generate_legal_moves_filters_with_validator():
    board = Board(Bitboard(setup=False))
    board.place_piece(PAWN, WHITE, 8)
    board.place_piece(PAWN, BLACK, 17)

    legal = Move(8, 17, PAWN, WHITE)
    illegal = Move(8, 24, PAWN, WHITE)
    generator, _ = make_generator([legal, illegal])
    validator = make_validator({(8, 17)})
    engine = RulesEngine(validator=validator, generator=generator)
    assert engine.generate_legal_moves(board, WHITE) == [legal] * 6


def test_has_legal_moves_with_real_generator_and_validator():
    board = Board(Bitboard(setup=False))
    board.place_piece(ROOK, WHITE, 0)
    board.place_piece(KNIGHT, BLACK, 10)
    engine = RulesEngine()
    assert engine.has_legal_moves(board, WHITE)
