from shatranj.domain.core.board import Board
from shatranj.domain.core.move import Move
from shatranj.domain.rules.rules_engine import RulesEngine
from shatranj.domain.ai.evaluator import Evaluator
from shatranj.domain.ai.minmax import Minimax
from shatranj.domain.ai.alphabeta import AlphaBeta
from shatranj.domain.ai.mcts import MCTS
from shatranj.domain.ai.iterative_deepening import IterativeDeepening

ALGORITHMS = ("minimax", "alphabeta", "mcts", "iterative")
SCORING_MODES = ("material", "positional", "advanced")


class AIPlayer:
    """
    Configurable AI player.

    Supports four algorithms:
      - minimax   : Minimax + TT, depth 3
      - alphabeta : Alpha-Beta + TT, depth 4
      - mcts      : Monte Carlo Tree Search, 500 simulations
      - iterative : Iterative Deepening + Alpha-Beta + TT, depth 4
    """

    def __init__(
        self,
        color: str,
        depth: int = 3,
        algorithm: str = "alphabeta",
        scoring: str = "advanced",
    ) -> None:
        self.color = color
        self.algorithm = algorithm
        self.scoring = scoring
        self._engine = RulesEngine()
        evaluator = Evaluator(mode=scoring)

        if algorithm == "mcts":
            self._search = MCTS(
                engine=self._engine,
                simulations=depth,
            )
        elif algorithm == "alphabeta":
            self._search = AlphaBeta(
                engine=self._engine,
                evaluator=evaluator,
                depth=depth,
            )
        elif algorithm == "iterative":
            self._search = IterativeDeepening(
                engine=self._engine,
                evaluator=evaluator,
                depth=depth,
                time_limit=5.0,  # 5 secondes par coup par défaut
            )
        else:
            # minimax default
            self._search = Minimax(
                engine=self._engine,
                evaluator=evaluator,
                depth=depth,
            )

    def choose_move(self, board: Board) -> Move | None:
        search_board = board.copy()
        return self._search.best_move(search_board, self.color)
