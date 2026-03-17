from shatranj.domain.core.board import Board
from shatranj.domain.core.move import Move
from shatranj.domain.rules.rules_engine import RulesEngine
from shatranj.domain.ai.evaluator import Evaluator
from shatranj.domain.ai.minimax import Minimax
from shatranj.domain.ai.alphabeta import AlphaBeta
from shatranj.domain.ai.mcts import MCTS

ALGORITHMS = ("minimax", "alphabeta", "mcts")
SCORING_MODES = ("material", "positional", "advanced")


class AIPlayer:
    """
    Configurable AI player.

    Supports three algorithms : minimax, alphabeta, mcts
    Supports three scoring modes: material, positional, advanced
    """

    def __init__(
        self,
        color    : str,
        depth    : int = 3,
        algorithm: str = "alphabeta",
        scoring  : str = "advanced",
    ) -> None:
        self.color     = color
        self.algorithm = algorithm
        self.scoring   = scoring
        self._engine   = RulesEngine()
        evaluator      = Evaluator(mode=scoring)

        if algorithm == "mcts":
            self._search = MCTS(
                engine      = self._engine,
                simulations = depth,
            )
        elif algorithm == "alphabeta":
            self._search = AlphaBeta(
                engine    = self._engine,
                evaluator = evaluator,
                depth     = depth,
            )
        else:
            self._search = Minimax(
                engine    = self._engine,
                evaluator = evaluator,
                depth     = depth,
            )

    def choose_move(self, board: Board) -> Move | None:
        return self._search.best_move(board, self.color)