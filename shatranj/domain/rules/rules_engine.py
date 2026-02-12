from shatranj.data.bitboards.bitboard import Bitboard
from shatranj.domain.core.board import Board
from shatranj.domain.core.move import Move
from shatranj.domain.rules.rules_engine import RulesEngine
from shatranj.utils.constants import BLACK, KNIGHT, PAWN, ROOK, WHITE


# Stub version of a move validator used for testing.
# Instead of real chess logic, it simply checks if a move's (from, to)
# tuple exists in a predefined allowed_moves set.
class StubValidator:
    def __init__(self, allowed_moves: set[tuple[int, int]] | None = None) -> None:
        # If no allowed moves provided, default to empty set.
        self.allowed_moves = allowed_moves if allowed_moves is not None else set()

    # This simulates the real validator's method.
    # It ignores board state and just checks square pairs.
    def is_valid_move(self, board: Board, move: Move) -> bool:
        return (move.from_square, move.to_square) in self.allowed_moves


# Stub version of a move generator used for testing.
# Instead of generating real moves, it always returns a fixed list of moves.
# It also records which generator methods were called.
class StubGenerator:
    def __init__(self, moves: list[Move]) -> None:
        self.moves = moves  # predefined moves to return
        self.called_methods: list[str] = []  # tracks which generators were called

    # Internal helper that records which piece generator was invoked.
    def _record(self, method_name: str) -> list[Move]:
        self.called_methods.append(method_name)
        return self.moves

    # Each piece-type generator calls _record with its name.
    def generate_pawn_moves(self, board: Board, color: str) -> list[Move]:
        return self._record("pawn")

    def generate_rook_moves(self, board: Board, color: str) -> list[Move]:
        return self._record("rook")

    def generate_knight_moves(self, board: Board, color: str) -> list[Move]:
        return self._record("knight")

    def generate_alfil_moves(self, board: Board, color: str) -> list[Move]:
        return self._record("alfil")

    def generate_ferz_moves(self, board: Board, color: str) -> list[Move]:
        return self._record("ferz")

    def generate_shah_moves(self, board: Board, color: str) -> list[Move]:
        return self._record("shah")


# Test that RulesEngine.is_valid_move simply delegates
# the validation logic to the injected validator.
def test_is_valid_move_delegates_to_validator():
    board = Board(Bitboard(setup=False))
    move = Move(8, 16, PAWN, WHITE)
    validator = StubValidator({(8, 16)})
    engine = RulesEngine(validator=validator)

    # Should return True because stub validator allows this move.
    assert engine.is_valid_move(board, move)


# Test that generate_pseudo_legal_moves calls all piece generators
# and aggregates their returned moves.
def test_generate_pseudo_legal_moves_aggregates_all_generators():
    board = Board(Bitboard(setup=False))
    move = Move(8, 16, PAWN, WHITE)
    generator = StubGenerator([move])
    engine = RulesEngine(generator=generator)

    moves = engine.generate_pseudo_legal_moves(board, WHITE)

    # Since there are 6 piece generators and each returns [move],
    # total moves should be 6.
    assert len(moves) == 6

    # Every returned move should equal the stub move.
    assert all(m == move for m in moves)

    # Ensure all generator methods were called in expected order.
    assert generator.called_methods == ["pawn", "rook", "knight", "alfil", "ferz", "shah"]


# Test that generate_legal_moves filters pseudo-legal moves
# using the validator.
def test_generate_legal_moves_filters_with_validator():
    board = Board(Bitboard(setup=False))
    board.place_piece(PAWN, WHITE, 8)
    board.place_piece(PAWN, BLACK, 17)

    legal = Move(8, 17, PAWN, WHITE)
    illegal = Move(8, 24, PAWN, WHITE)

    # Generator always returns both moves.
    generator = StubGenerator([legal, illegal])

    # Validator only allows one of them.
    validator = StubValidator({(8, 17)})

    engine = RulesEngine(validator=validator, generator=generator)

    # Since there are 6 piece generators and only one move is allowed,
    # we expect 6 copies of the legal move.
    assert engine.generate_legal_moves(board, WHITE) == [legal] * 6


# Integration-style test using real generator and validator.
# Ensures has_legal_moves returns True when a real legal move exists.
def test_has_legal_moves_with_real_generator_and_validator():
    board = Board(Bitboard(setup=False))
    board.place_piece(ROOK, WHITE, 0)
    board.place_piece(KNIGHT, BLACK, 10)
    engine = RulesEngine()

    # White rook should have at least one legal move.
    assert engine.has_legal_moves(board, WHITE)
