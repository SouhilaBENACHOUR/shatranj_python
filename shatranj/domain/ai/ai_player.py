from shatranj.domain.core.board import Board
from shatranj.domain.core.move import Move
from shatranj.domain.rules.rules_engine import RulesEngine
from shatranj.domain.ai.evaluator import Evaluator
from shatranj.domain.ai.minmax import Minimax
from shatranj.domain.ai.alphabeta import AlphaBeta
from shatranj.domain.ai.mcts import MCTS


# algorithmes disponibles
ALGORITHMS = ("minimax", "alphabeta", "mcts")


class AIPlayer:
    """
    Joueur IA configurable.

    Supporte trois algorithmes :
      - minimax   : Minimax pur, profondeur 3
      - alphabeta : Minimax + Alpha-Beta, profondeur 4 (plus fort)
      - mcts      : Monte Carlo Tree Search, 1000 simulations (différent)
    """

    def __init__(
        self,
        color    : str,
        depth    : int = 3,
        algorithm: str = "alphabeta",
    ) -> None:
        self.color     = color
        self.algorithm = algorithm
        self._engine   = RulesEngine()
        evaluator      = Evaluator()

        if algorithm == "mcts":
            # MCTS utilise des simulations au lieu d'une profondeur
            self._search = MCTS(
                engine      = self._engine,
                simulations = 500,
            )
        elif algorithm == "alphabeta":
            self._search = AlphaBeta(
                engine    = self._engine,
                evaluator = evaluator,
                depth     = depth if depth != 3 else 4,
            )
        else:
            # minimax par défaut
            self._search = Minimax(
                engine    = self._engine,
                evaluator = evaluator,
                depth     = depth,
            )

    def choose_move(self, board: Board) -> Move | None:
        """
        Choisit le meilleur coup pour la couleur de l'IA.
        Retourne None si aucun coup n'est disponible.
        """
        return self._search.best_move(board, self.color)