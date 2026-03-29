"""
alphabeta.py - Minimax with Alpha-Beta pruning + Transposition Table
"""

from shatranj.domain.core.board import Board
from shatranj.domain.core.move import Move
from shatranj.domain.rules.rules_engine import RulesEngine
from shatranj.domain.ai.evaluator import Evaluator
from shatranj.domain.ai.transposition_table import (
    ZobristHasher,
    TranspositionTable,
    EXACT,
    LOWER_BOUND,
    UPPER_BOUND,
)
from shatranj.utils.constants import WHITE, BLACK


class AlphaBeta:
    """
    Minimax with Alpha-Beta pruning and Transposition Table.

    The transposition table avoids re-evaluating positions
    already seen during the search (5x-10x speedup).
    """

    def __init__(
        self,
        engine: RulesEngine,
        evaluator: Evaluator,
        depth: int = 4,
    ) -> None:
        self._engine = engine
        self._evaluator = evaluator
        self._depth = depth
        self._hasher = ZobristHasher()
        self._tt = TranspositionTable()

    def best_move(self, board: Board, color: str) -> Move | None:
        """
        Return the best move for 'color' using Alpha-Beta + TT.
        """
        legal_moves = self._engine.generate_legal_moves(board, color)
        if not legal_moves:
            return None

        # clear the table at the start of each search
        self._tt.clear()

        # compute initial Zobrist key
        key = self._hasher.compute_key(board, color)

        best = None
        alpha = float("-inf")
        beta = float("+inf")

        opponent = BLACK if color == WHITE else WHITE

        for move in legal_moves:
            captured = board.apply_move(move)
            result_piece = board.get_piece_at(move.to_square)[0]

            # update Zobrist key after the move
            captured_color = opponent if captured else None
            new_key = self._hasher.update_key(
                key=key,
                piece=move.piece_type,
                color=color,
                from_square=move.from_square,
                to_square=move.to_square,
                captured_piece=captured,
                captured_color=captured_color,
                result_piece=result_piece,
            )

            score = self._alphabeta(
                board=board,
                depth=self._depth - 1,
                alpha=alpha,
                beta=beta,
                is_maximizing=False,
                ai_color=color,
                current_color=opponent,
                key=new_key,
            )

            board.undo_move(move, captured)

            if score > alpha:
                alpha = score
                best = move

        return best

    def _alphabeta(
        self,
        board: Board,
        depth: int,
        alpha: float,
        beta: float,
        is_maximizing: bool,
        ai_color: str,
        current_color: str,
        key: int,
    ) -> float:
        """
        Recursive Alpha-Beta with Transposition Table lookup.
        """
        original_alpha = alpha

        # --- Transposition Table lookup ---
        tt_score, should_use = self._tt.get(key, depth, alpha, beta)
        if should_use:
            return tt_score

        # --- Base case: depth reached ---
        if depth == 0:
            return self._evaluator.evaluate(board, ai_color)

        legal_moves = self._engine.generate_legal_moves(board, current_color)

        # --- Base case: no moves ---
        if not legal_moves:
            if self._engine._is_in_check(board, current_color):
                return 9999.0 if not is_maximizing else -9999.0
            return 0.0

        opponent = BLACK if current_color == WHITE else WHITE

        if is_maximizing:
            best = float("-inf")
            for move in legal_moves:
                captured = board.apply_move(move)
                result_piece = board.get_piece_at(move.to_square)[0]
                captured_piece = captured[0] if captured else None
                captured_color = captured[1] if captured else None
                new_key = self._hasher.update_key(
                    key=key,
                    piece=move.piece_type,
                    color=current_color,
                    from_square=move.from_square,
                    to_square=move.to_square,
                    captured_piece=captured_piece,
                    captured_color=captured_color,
                    result_piece=result_piece,
                )

                score = self._alphabeta(
                    board=board,
                    depth=depth - 1,
                    alpha=alpha,
                    beta=beta,
                    is_maximizing=False,
                    ai_color=ai_color,
                    current_color=opponent,
                    key=new_key,
                )
                board.undo_move(move, captured)

                best = max(best, score)
                alpha = max(alpha, best)

                if beta <= alpha:
                    break  # beta cutoff

            # --- Store in Transposition Table ---
            if best <= original_alpha:
                flag = UPPER_BOUND
            if best >= beta:
                flag = LOWER_BOUND
            else:
                flag = EXACT
            self._tt.store(key, best, depth, flag)

            return best

        best = float("+inf")
        for move in legal_moves:
            captured = board.apply_move(move)
            result_piece = board.get_piece_at(move.to_square)[0]
            captured_color = current_color if captured else None
            new_key = self._hasher.update_key(
                key=key,
                piece=move.piece_type,
                color=current_color,
                from_square=move.from_square,
                to_square=move.to_square,
                captured_piece=captured,
                captured_color=captured_color,
                result_piece=result_piece,
            )

            score = self._alphabeta(
                board=board,
                depth=depth - 1,
                alpha=alpha,
                beta=beta,
                is_maximizing=True,
                ai_color=ai_color,
                current_color=opponent,
                key=new_key,
            )
            board.undo_move(move, captured)

            best = min(best, score)
            beta = min(beta, best)

            if beta <= alpha:
                break  # alpha cutoff

        # --- Store in Transposition Table ---
        if best <= original_alpha:
            flag = UPPER_BOUND
        if best >= beta:
            flag = LOWER_BOUND
        else:
            flag = EXACT
        self._tt.store(key, best, depth, flag)

        return best
