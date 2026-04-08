import math
import random

from shatranj.domain.core.board import Board
from shatranj.domain.core.move import Move
from shatranj.domain.rules.rules_engine import RulesEngine
from shatranj.domain.ai.transposition_table import (
    ZobristHasher,
    TranspositionTable,
    EXACT,
)
from shatranj.utils.constants import WHITE, BLACK


class MCTSNode:
    """
    A node in the MCTS tree.

    Each node represents a game position after a move.

    Attributes:
      move     -> the move that led to this position (None for root)
      parent   -> the parent node (None for root)
      children -> explored child nodes
      wins     -> number of simulated wins from this node
      visits   -> number of times this node was visited
      untried  -> moves not yet explored from this position
      color    -> color of the player who just played this move
    """

    def __init__(
        self,
        move: Move | None,
        parent: "MCTSNode | None",
        color: str,
    ) -> None:
        self.move = move
        self.parent = parent
        self.color = color
        self.children: list["MCTSNode"] = []
        self.wins: float = 0.0
        self.visits: int = 0
        self.untried: list[Move] = []

    def is_fully_expanded(self) -> bool:
        """Return True if all moves have been explored."""
        return len(self.untried) == 0

    def best_child(self, exploration: float = 1.41) -> "MCTSNode":
        """
        Choose the best child using the UCB1 formula.

        UCB1 = wins/visits + exploration * sqrt(ln(parent.visits) / visits)
        """
        return max(
            self.children,
            key=lambda c: (c.wins / c.visits)
            + exploration * math.sqrt(math.log(self.visits) / c.visits),
        )

    def best_move_child(self) -> "MCTSNode":
        """
        Return the most visited child.
        Used at the end to choose the final move.
        Most visited is more robust than best UCB1.
        """
        return max(self.children, key=lambda c: c.visits)


class MCTS:
    """
    Monte Carlo Tree Search with Transposition Table.

    Each simulation:
      1. SELECTION  -> descend the tree using UCB1
      2. EXPANSION  -> explore an untried move
      3. SIMULATION -> play randomly until end (rollout)
      4. BACKPROP   -> propagate the result up the tree

    The transposition table caches rollout results to avoid
    re-simulating positions already seen.
    """

    def __init__(
        self,
        engine: RulesEngine,
        simulations: int = 500,
    ) -> None:
        self._engine = engine
        self._simulations = simulations
        self._depth = simulations  # for compatibility with _do_ai_move
        self._hasher = ZobristHasher()
        self._tt = TranspositionTable()

    def best_move(self, board: Board, color: str) -> Move | None:
        """
        Return the best move for 'color' using MCTS + TT.
        Returns None if no move is available.
        """
        legal_moves = self._engine.generate_legal_moves(board, color)
        if not legal_moves:
            return None

        # clear the table at the start of each search
        self._tt.clear()

        # create the root node
        root = MCTSNode(move=None, parent=None, color=color)
        root.untried = list(legal_moves)
        root.visits = 1

        for _ in range(self._simulations):
            node = root
            board_copy = self._copy_board(board)
            sim_color = color

            # ----------------------------------------------------------
            # 1. SELECTION
            # ----------------------------------------------------------
            while node.is_fully_expanded() and node.children:
                node = node.best_child()
                board_copy.apply_move(node.move)
                sim_color = BLACK if sim_color == WHITE else WHITE

            # ----------------------------------------------------------
            # 2. EXPANSION
            # ----------------------------------------------------------
            if node.untried:
                move = random.choice(node.untried)
                node.untried.remove(move)
                board_copy.apply_move(move)
                sim_color = BLACK if sim_color == WHITE else WHITE

                child = MCTSNode(move=move, parent=node, color=sim_color)
                legal_child = self._engine.generate_legal_moves(board_copy, sim_color)
                child.untried = list(legal_child)
                node.children.append(child)
                node = child

            # ----------------------------------------------------------
            # 3. SIMULATION (rollout) with TT
            # ----------------------------------------------------------
            result = self._rollout(board_copy, sim_color, color)

            # ----------------------------------------------------------
            # 4. BACKPROPAGATION
            # ----------------------------------------------------------
            self._backpropagate(node, result)

        if not root.children:
            return random.choice(legal_moves)
        return root.best_move_child().move

    def _rollout(
        self,
        board: Board,
        current_color: str,
        ai_color: str,
        max_moves: int = 50,
    ) -> float:
        """
        Simulate a random game until the end.

        Checks the TT first to avoid redundant rollouts.

        Returns:
          1.0 -> AI wins
          0.0 -> AI loses
          0.5 -> draw
        """
        color = current_color

        # check TT for this position
        key = self._hasher.compute_key(board, color)
        tt_score, should_use = self._tt.get(key, 0, float("-inf"), float("+inf"))
        if should_use:
            return tt_score

        for _ in range(max_moves):
            legal_moves = self._engine.generate_legal_moves(board, color)

            # no moves -> checkmate or stalemate
            if not legal_moves:
                if self._engine._is_in_check(board, color):
                    opponent = BLACK if color == WHITE else WHITE
                    result = 1.0 if opponent == ai_color else 0.0
                else:
                    result = 0.5
                self._tt.store(key, result, 0, EXACT)
                return result

            # bare king -> opponent wins
            if self._engine.is_bare_king(board, color):
                opponent = BLACK if color == WHITE else WHITE
                result = 1.0 if opponent == ai_color else 0.0
                self._tt.store(key, result, 0, EXACT)
                return result

            # play a random move
            move = random.choice(legal_moves)
            board.apply_move(move)
            color = BLACK if color == WHITE else WHITE

        # move limit reached -> draw
        self._tt.store(key, 0.5, 0, EXACT)
        return 0.5

    def _backpropagate(self, node: "MCTSNode", result: float) -> None:
        """
        Propagate the result from the leaf node up to the root.

        Each ancestor node receives:
          - +1 visit
          - +result wins (or +1-result for the parent)
        """
        while node is not None:
            node.visits += 1
            node.wins += result
            result = 1.0 - result
            node = node.parent

    def _copy_board(self, board: Board) -> Board:
        """
        Create a copy of the board for simulations.
        Only copies the bitboards — sufficient for move simulation.
        """
        new_board = Board(setup=False)
        new_board._boards = dict(board._boards)
        return new_board
