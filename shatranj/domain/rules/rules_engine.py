from shatranj.domain.core.board import Board
from shatranj.domain.core.move import Move
from shatranj.domain.rules.move_generator import MoveGenerator
from shatranj.domain.rules.move_validator import MoveValidator


class RulesEngine:
    """Coordinates move generation and move validation."""

    def __init__(
        self,
        validator: MoveValidator | None = None,
        generator: MoveGenerator | None = None,
    ) -> None:
        self._validator = validator if validator is not None else MoveValidator()
        self._generator = generator if generator is not None else MoveGenerator()

    def is_valid_move(self, board: Board, move: Move) -> bool:
        return self._validator.is_valid_move(board, move)

    def generate_pseudo_legal_moves(self, board: Board, color: str) -> list[Move]:
        moves: list[Move] = []
        generators = (
            self._generator.generate_pawn_moves,
            self._generator.generate_rook_moves,
            self._generator.generate_knight_moves,
            self._generator.generate_alfil_moves,
            self._generator.generate_ferz_moves,
            self._generator.generate_shah_moves,
        )
        for generate in generators:
            moves.extend(generate(board, color))
        return moves

    def generate_legal_moves(self, board: Board, color: str) -> list[Move]:
        return [
            move
            for move in self.generate_pseudo_legal_moves(board, color)
            if self.is_valid_move(board, move)
        ]

    def has_legal_moves(self, board: Board, color: str) -> bool:
        return bool(self.generate_legal_moves(board, color))
