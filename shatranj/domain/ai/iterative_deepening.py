"""
iterative_deepening.py - Iterative Deepening Search

Role: search at increasing depths until time runs out.

Advantages:
  - Always has a valid move (even if time runs out)
  - Better move ordering (uses previous depth results)
  - Combines well with Alpha-Beta + Transposition Table
"""

import time
from shatranj.domain.core.board import Board
from shatranj.domain.core.move import Move
from shatranj.domain.rules.rules_engine import RulesEngine
from shatranj.domain.ai.evaluator import Evaluator
from shatranj.domain.ai.alphabeta import AlphaBeta


class IterativeDeepening:
    """
    Iterative Deepening Search.

    Searches at depth 1, 2, 3, ... until max_depth or time limit.

    At each depth:
      - Uses Alpha-Beta + Transposition Table
      - The TT stores results from previous depths
        → move ordering improves at each iteration
        → deeper search is faster thanks to better pruning

    Attributes:
      _engine    : rules engine
      _evaluator : evaluation function
      _depth     : maximum depth (also stored as _depth for _do_ai_move)
      _time_limit: max seconds per move (None = no limit)
    """

    def __init__(
        self,
        engine: RulesEngine,
        evaluator: Evaluator,
        depth: int = 4,
        time_limit: float = None,
    ) -> None:
        self._engine = engine
        self._evaluator = evaluator
        self._depth = depth  # max depth
        self._time_limit = time_limit  # seconds (None = no limit)
        self._ab = AlphaBeta(
            engine=engine,
            evaluator=evaluator,
            depth=depth,
        )

    def best_move(self, board: Board, color: str) -> Move | None:
        """
        Return the best move using Iterative Deepening.

        Searches at depth 1, 2, ..., self._depth.
        If time limit is set, stops when time runs out.
        Always returns the best move found so far.
        """
        legal_moves = self._engine.generate_legal_moves(board, color)
        if not legal_moves:
            return None

        best_move = legal_moves[0]  # fallback: first legal move
        start_time = time.time()

        for current_depth in range(1, self._depth + 1):

            # check time limit before starting a new depth
            if self._time_limit is not None:
                elapsed = time.time() - start_time
                if elapsed >= self._time_limit:
                    break  # time is up → return best move from previous depth

            # search at current depth using Alpha-Beta
            self._ab._depth = current_depth
            move = self._ab.best_move(board, color)

            if move is not None:
                best_move = move  # update best move

            # check time limit after finishing a depth
            if self._time_limit is not None:
                if time.time() - start_time >= self._time_limit:
                    break

        return best_move
