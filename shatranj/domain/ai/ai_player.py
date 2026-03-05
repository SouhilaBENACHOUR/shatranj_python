from shatranj.domain.core.board import Board
from shatranj.domain.core.move import Move
from shatranj.domain.rules.rules_engine import RulesEngine
from shatranj.domain.ai.evaluator import Evaluator
from shatranj.domain.ai.minmax import Minimax


class AIPlayer:
    """
    Joueur IA configurable.
    
    Utilise Minimax pour choisir le meilleur coup.
    La couleur et la profondeur sont configurables.
    """

    def __init__(self, color: str, depth: int = 3) -> None:
        self.color = color         # couleur de l'IA (WHITE ou BLACK)
        self._engine = RulesEngine()
        self._minimax = Minimax(
            engine=self._engine,
            evaluator=Evaluator(),
            depth=depth,           # profondeur de recherche
        )

    def choose_move(self, board: Board) -> Move | None:
        """
        Choisit le meilleur coup pour la couleur de l'IA.
        Retourne None si aucun coup n'est disponible.
        """
        return self._minimax.best_move(board, self.color)
