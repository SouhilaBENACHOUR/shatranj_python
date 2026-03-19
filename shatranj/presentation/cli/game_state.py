"""
game_state.py - Complete state of a Shatranj game

Role: holds EVERYTHING that defines a game in progress:
  - the board (Board)
  - whose turn it is (WHITE or BLACK)
  - the move history for undo/redo

Why a separate class from Board?
  Board = just the pieces on the squares.
  GameState = Board + game context (turn, history, ...).
  This is the Business Logic layer described in the preliminary report.
"""

from shatranj.domain.core.board import Board
from shatranj.domain.core.move import Move
from shatranj.utils.constants import WHITE, BLACK


class GameState:
    """
    Represents the complete state of a game.

    Attributes:
      board         : the current board
      current_color : color of the player whose turn it is (WHITE or BLACK)
      _history      : list of played moves (for display and undo)
      _redo_stack   : stack of undone moves (for redo)
    """

    def __init__(self) -> None:
        # Create a new board with the starting position
        self.board = Board(setup=True)

        # White always moves first (Shatranj rule)
        self.current_color: str = WHITE

        # Move history: list of (move, board_snapshot)
        # We save a snapshot of the board BEFORE each move
        # so we can go back (undo)
        self._history: list[tuple[Move, dict]] = []

        # Redo stack: undone moves that can be replayed
        self._redo_stack: list[tuple[Move, dict]] = []

    # ------------------------------------------------------------------
    # Apply a move
    # ------------------------------------------------------------------

    def apply_move(self, move: Move) -> None:
        """
        Apply a move on the board and switch to the next player.

        The board state BEFORE the move is saved in the history.
        When a new move is played, the redo stack is cleared
        (you cannot redo moves after playing a different one).
        """
        # Save the current state (snapshot of the bitboards)
        snapshot = self._take_snapshot()

        # Apply the move on the board
        self.board.apply_move(move)

        # Add to history
        self._history.append((move, snapshot))

        # A new move clears the undone moves
        self._redo_stack.clear()

        # Switch turn
        self._switch_turn()

    # ------------------------------------------------------------------
    # Undo / Redo
    # ------------------------------------------------------------------

    def undo(self) -> Move | None:
        """
        Undo the last played move.

        Returns the undone move, or None if history is empty.

        Principle: restore the snapshot saved BEFORE that move.
        """
        if not self._history:
            return None  # Nothing to undo

        move, snapshot = self._history.pop()

        # Push the undone move onto the redo stack
        self._redo_stack.append((move, self._take_snapshot()))

        # Restore the board to the state before the move
        self._restore_snapshot(snapshot)

        # Switch back to the previous player
        self._switch_turn()

        return move

    def redo(self) -> Move | None:
        """
        Replay the last undone move.

        Returns the replayed move, or None if nothing to redo.
        """
        if not self._redo_stack:
            return None  # Nothing to redo

        move, _ = self._redo_stack.pop()

        # Re-apply the move (like apply_move but without clearing redo stack)
        snapshot = self._take_snapshot()
        self.board.apply_move(move)
        self._history.append((move, snapshot))
        self._switch_turn()

        return move

    def can_undo(self) -> bool:
        """Return True if there is at least one move to undo."""
        return len(self._history) > 0

    def can_redo(self) -> bool:
        """Return True if there is at least one move to redo."""
        return len(self._redo_stack) > 0

    # ------------------------------------------------------------------
    # History
    # ------------------------------------------------------------------

    def get_history(self) -> list[Move]:
        """Return the list of played moves (without snapshots)."""
        return [move for move, _ in self._history]

    # ------------------------------------------------------------------
    # Private methods
    # ------------------------------------------------------------------

    def _switch_turn(self) -> None:
        """Switch the turn from WHITE to BLACK or from BLACK to WHITE."""
        self.current_color = BLACK if self.current_color == WHITE else WHITE

    def _take_snapshot(self) -> dict:
        """
        Save the current state of the board's bitboards.

        We copy the _boards dictionary of the Board.
        This is a shallow copy but it is sufficient because the values
        are integers (immutable in Python).
        """
        return dict(self.board._boards)

    def _restore_snapshot(self, snapshot: dict) -> None:
        """Restore the board's bitboards from a snapshot."""
        self.board._boards = dict(snapshot)
