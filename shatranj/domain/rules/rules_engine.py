from shatranj.domain.core.board import Board
from shatranj.domain.core.move import Move
from shatranj.domain.rules.move_generator import MoveGenerator
from shatranj.domain.rules.move_validator import MoveValidator
from shatranj.utils.constants import BLACK, WHITE, SHAH
from shatranj.utils.exceptions import MissingShahError


class RulesEngine:
    """Coordinates move generation and move validation."""

    def __init__(
        self,
        validator: MoveValidator | None = None,
        generator: MoveGenerator | None = None,
    ) -> None:
        self._validator = (
            validator if validator is not None else MoveValidator()
        )
        self._generator = (
            generator if generator is not None else MoveGenerator()
        )

    def is_valid_move(self, board: Board, move: Move) -> bool:
        return self._validator.is_valid_move(board, move)

    def generate_pseudo_legal_moves(
        self, board: Board, color: str
    ) -> list[Move]:
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
        """
        Filter pseudo-legal moves.
        A move is legal only if, after playing it,
        our Shah is not in check.
        """
        legal = []
        for move in self.generate_pseudo_legal_moves(board, color):
            if not self.is_valid_move(board, move):
                continue
            captured = board.apply_move(move)  # joue le coup
            in_check = self._is_in_check(board, color)  # Shah en danger ?
            board.undo_move(move, captured)  # annule le coup
            if not in_check:
                legal.append(move)  # coup légal → on le garde
        return legal

    def has_legal_moves(self, board: Board, color: str) -> bool:
        return bool(self.generate_legal_moves(board, color))

    def _is_in_check(self, board: Board, color: str) -> bool:
        """
        Check if the Shah of 'color' is attacked by the opponent.
        1. Find the Shah's square
        2. Generate all opponent moves
        3. If any move reaches the Shah's square → check
        """
        try:
            shah_square = board.find_shah(color)
        except MissingShahError:
            return True  # Shah not found = in check by definition
        opponent = BLACK if color == WHITE else WHITE
        opponent_moves = self.generate_pseudo_legal_moves(board, opponent)
        return any(move.to_square == shah_square for move in opponent_moves)

    def is_checkmate(self, board: Board, color: str) -> bool:
        """
        Checkmate: the Shah is in check AND no legal move can save it.
        The game is over, 'color' has lost.
        """
        if not self._is_in_check(board, color):
            return False
        return not self.has_legal_moves(board, color)

    def is_stalemate(self, board: Board, color: str) -> bool:
        """
        Stalemate: the Shah is NOT in check but no legal move is available.
        In Shatranj, stalemate is a VICTORY for the player who caused it
        """
        if self._is_in_check(board, color):
            return False
        return not self.has_legal_moves(board, color)

    def is_bare_king(self, board: Board, color: str) -> bool:
        """
        Shatranj-specific rule:
        If the opponent has only their Shah left → 'color' wins.
        Compare the bitboard of all opponent pieces
        with the bitboard of the opponent's Shah alone.
        If they are identical → only the Shah remains.
        """
        opponent = BLACK if color == WHITE else WHITE
        opponent_bitboard = (
            board.black_pieces if opponent == BLACK else board.white_pieces
        )
        shah_bitboard = board._boards[(SHAH, opponent)]
        return opponent_bitboard == shah_bitboard and shah_bitboard != 0
