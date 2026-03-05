from shatranj.domain.core.board import Board
from shatranj.domain.core.move import Move
from shatranj.utils.constants import BLACK, WHITE
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
      """
       Filtre les coups pseudo-légaux.
       Un coup est légal seulement si après l'avoir joué,
       notre Shah n'est pas en échec.
      """
      legal = []
      for move in self.generate_pseudo_legal_moves(board, color):
        if not self.is_valid_move(board, move):
            continue
        captured = board.apply_move(move)           # joue le coup
        in_check = self._is_in_check(board, color)  # Shah en danger ?
        board.undo_move(move, captured)             # annule le coup
        if not in_check:
            legal.append(move)  # coup légal → on le garde
      return legal

    def has_legal_moves(self, board: Board, color: str) -> bool:
        return bool(self.generate_legal_moves(board, color))
    
    def is_checkmate(self, board: Board, color: str) -> bool:
        """
        Mat : le Shah de 'color' est en échec ET n'a aucun coup légal.
        Les deux conditions doivent être vraies en même temps.
        → La partie est terminée, 'color' a perdu.
        """
        return (
          self._is_in_check(board, color)      # le Shah est attaqué
          and not self.has_legal_moves(board, color)  # et aucun coup ne peut le sauver
        )

    def is_stalemate(self, board: Board, color: str) -> bool:
       """
       Pat : le Shah de 'color' n'est PAS en échec mais n'a aucun coup légal.
    
       
       Le pat est une VICTOIRE pour celui qui l'a provoqué,
       contrairement aux échecs modernes où c'est un match nul.
      """
       return (
        not self._is_in_check(board, color)        # le Shah n'est pas attaqué
        and not self.has_legal_moves(board, color)  # mais aucun coup disponible
    )

    def _is_in_check(self, board: Board, color: str) -> bool:
     """
     Vérifie si le Shah de 'color' est attaqué par l'adversaire.
     """
     shah_square = board.find_shah(color)
     if shah_square is None:
        return True
     opponent = BLACK if color == WHITE else WHITE
     opponent_moves = self.generate_pseudo_legal_moves(board, opponent)
     return any(move.to_square == shah_square for move in opponent_moves)