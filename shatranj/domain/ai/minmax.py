from shatranj.domain.core.board import Board
from shatranj.domain.core.move import Move
from shatranj.domain.rules.rules_engine import RulesEngine
from shatranj.domain.ai.evaluator import Evaluator
from shatranj.domain.ai.transposition_table import (
    ZobristHasher,
    TranspositionTable,
    EXACT,
)
from shatranj.utils.constants import WHITE, BLACK


class Minimax:
    """
    Minimax algorithm with configurable depth and Transposition Table.

    Principle:
      - MAX: the AI tries to maximize its score
      - MIN: the opponent tries to minimize the AI's score

    At each level we alternate MAX and MIN.
    We explore up to the requested depth,
    then evaluate the position with Evaluator.

    The transposition table avoids re-evaluating positions
    already seen during the search (5x-10x speedup).
    """

    def __init__(
        self,
        engine: RulesEngine,
        evaluator: Evaluator,
        depth: int = 3,
    ) -> None:
        self._engine = engine
        self._evaluator = evaluator
        self._depth = depth
        self._hasher = ZobristHasher()
        self._tt = TranspositionTable()

    def best_move(self, board: Board, color: str) -> Move | None:
        """
        Return the best move for 'color' in the current position.
        Returns None if no move is available (checkmate or stalemate).
        """
        # clear the table at the start of each search
        self._tt.clear()

        # compute initial Zobrist key
        key = self._hasher.compute_key(board, color)

        best_score = float("-inf")
        best_moves: list[Move] = []
        legal_moves = self._engine.generate_legal_moves(board, color)

        if not legal_moves:
            return None

        eps = 1e-9
        opponent = BLACK if color == WHITE else WHITE

        for move in legal_moves:
            captured = board.apply_move(move)
            result_piece = board.get_piece_at(move.to_square)[0]

            # update Zobrist key after the move
            captured_piece = captured[0] if captured else None
            captured_color = captured[1] if captured else None
            new_key = self._hasher.update_key(
                key=key,
                piece=move.piece_type,
                color=color,
                from_square=move.from_square,
                to_square=move.to_square,
                captured_piece=captured_piece,
                captured_color=captured_color,
                result_piece=result_piece,
            )

            score = self._minimax(
                board=board,
                depth=self._depth - 1,
                is_maximizing=False,
                ai_color=color,
                current_color=opponent,
                key=new_key,
            )

            board.undo_move(move, captured)

            if score > best_score + eps:
                best_score = score
                best_moves = [move]
            if abs(score - best_score) <= eps:
                best_moves.append(move)

        if not best_moves:
            return None
        return self._select_most_active_move(board, color, best_moves)

    def _select_most_active_move(
        self,
        board: Board,
        color: str,
        moves: list[Move],
    ) -> Move:
        """
        Break ties between equal-score moves to avoid passive back-and-forth.

        Priorities:
          1) capture
          2) AI mobility after the move
          3) move distance
        """
        best_move = moves[0]
        best_activity = self._activity_score(board, color, best_move)

        for move in moves[1:]:
            activity = self._activity_score(board, color, move)
            if activity > best_activity:
                best_activity = activity
                best_move = move

        return best_move

    def _activity_score(
        self,
        board: Board,
        color: str,
        move: Move,
    ) -> tuple[int, int, int, int, int]:
        """
        Compute an activity score for a move to break ties deterministically.
        """
        captured = board.apply_move(move)
        mobility_after = len(self._engine.generate_legal_moves(board, color))
        board.undo_move(move, captured)

        from_rank, from_file = divmod(move.from_square, 8)
        to_rank, to_file = divmod(move.to_square, 8)
        distance = abs(to_rank - from_rank) + abs(to_file - from_file)
        is_capture = 1 if move.captured_piece is not None else 0

        return (
            is_capture,
            mobility_after,
            distance,
            move.to_square,
            -move.from_square,
        )

    def _minimax(
        self,
        board: Board,
        depth: int,
        is_maximizing: bool,
        ai_color: str,
        current_color: str,
        key: int,
    ) -> float:
        """
        Recursive Minimax function with Transposition Table lookup.

        depth          -> remaining depth (stops at 0)
        is_maximizing  -> True if it is the AI's turn (MAX)
        ai_color       -> the AI's color (never changes)
        current_color  -> the color playing at this level
        key            -> current Zobrist hash key
        """
        # --- Transposition Table lookup ---
        tt_score, should_use = self._tt.get(
            key, depth, float("-inf"), float("+inf")
        )
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
            # AI looks for maximum score
            best = float("-inf")
            for move in legal_moves:
                captured = board.apply_move(move)
                result_piece = board.get_piece_at(move.to_square)[0]
                captured_color = opponent if captured else None
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

                score = self._minimax(
                    board=board,
                    depth=depth - 1,
                    is_maximizing=False,
                    ai_color=ai_color,
                    current_color=opponent,
                    key=new_key,
                )
                board.undo_move(move, captured)
                best = max(best, score)

            # store result in Transposition Table
            self._tt.store(key, best, depth, EXACT)
            return best

        # opponent looks for minimum score
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

            score = self._minimax(
                board=board,
                depth=depth - 1,
                is_maximizing=True,
                ai_color=ai_color,
                current_color=opponent,
                key=new_key,
            )
            board.undo_move(move, captured)
            best = min(best, score)

        # store result in Transposition Table
        self._tt.store(key, best, depth, EXACT)
        return best
