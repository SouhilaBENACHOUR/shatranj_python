"""
board_widget.py - Chess board drawing widget

Role: draws the board and pieces using Cairo + SVG images.
      Handles click-to-move, drag'n'drop, and highlights valid squares.
"""

import os
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Rsvg", "2.0")
from gi.repository import Gtk, Rsvg
import cairo

from shatranj.domain.core.board import Board
from shatranj.domain.core.move import Move
from shatranj.domain.rules.rules_engine import RulesEngine
from shatranj.utils.constants import (
    WHITE, BLACK, BOARD_SIZE,
    SHAH, FERZ, ROOK, ALFIL, KNIGHT, PAWN,
)

# Colors
LIGHT_SQUARE = (0.94, 0.85, 0.71)       # beige
DARK_SQUARE  = (0.71, 0.53, 0.39)       # brown
HIGHLIGHT    = (0.20, 0.70, 0.50, 0.6)  # green (selected)
HINT_COLOR   = (0.20, 0.70, 0.50, 0.3)  # green (valid destination)


class BoardWidget(Gtk.DrawingArea):
    """
    Widget that draws the Shatranj board and handles user interaction.

    Interaction flow (click-to-move):
      1. User clicks a square with a piece → piece selected, valid moves highlighted
      2. User clicks a highlighted square  → move played
      3. User clicks elsewhere             → selection cleared

    Interaction flow (drag'n'drop):
      1. User drags a piece → piece follows the mouse, valid moves highlighted
      2. User drops on a valid square → move played
      3. User drops elsewhere         → drag cancelled
    """

    def __init__(self, engine: RulesEngine) -> None:
        super().__init__()

        self._engine = engine
        self._board: Board | None = None
        self._current_color: str = WHITE

        # Click-to-move state
        self._selected_square: int | None = None
        self._valid_moves: list[Move] = []

        # Drag'n'drop state
        self._drag_square: int | None = None
        self._drag_x: float = 0.0
        self._drag_y: float = 0.0
        self._dragging: bool = False

        # Callback called when a move is played: fn(move: Move)
        self.on_move_played = None

        # Load SVG piece images
        self._pieces = self._load_pieces()

        # Drawing
        self.set_draw_func(self._draw)

        # Click handler (click-to-move)
        click = Gtk.GestureClick.new()
        click.connect("pressed", self._on_click)
        self.add_controller(click)

        # Drag handler (drag'n'drop)
        drag = Gtk.GestureDrag.new()
        drag.connect("drag-begin",  self._on_drag_begin)
        drag.connect("drag-update", self._on_drag_update)
        drag.connect("drag-end",    self._on_drag_end)
        self.add_controller(drag)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_board(self, board: Board, current_color: str) -> None:
        """Update the board state and redraw."""
        self._board = board
        self._current_color = current_color
        self._selected_square = None
        self._valid_moves = []
        self._dragging = False
        self._drag_square = None
        self.queue_draw()

    def clear_selection(self) -> None:
        """Clear the current selection and redraw."""
        self._selected_square = None
        self._valid_moves = []
        self.queue_draw()

    # ------------------------------------------------------------------
    # SVG loading
    # ------------------------------------------------------------------

    def _load_pieces(self) -> dict:
        """Load SVG piece images from the pieces/ directory."""
        pieces_dir = os.path.join(os.path.dirname(__file__), "pieces")
        file_map = {
            (SHAH,   WHITE): "wK.svg",
            (FERZ,   WHITE): "wF.svg",
            (ROOK,   WHITE): "wR.svg",
            (ALFIL,  WHITE): "wA.svg",
            (KNIGHT, WHITE): "wN.svg",
            (PAWN,   WHITE): "wP.svg",
            (SHAH,   BLACK): "bK.svg",
            (FERZ,   BLACK): "bF.svg",
            (ROOK,   BLACK): "bR.svg",
            (ALFIL,  BLACK): "bA.svg",
            (KNIGHT, BLACK): "bN.svg",
            (PAWN,   BLACK): "bP.svg",
        }
        handles = {}
        for key, filename in file_map.items():
            path = os.path.join(pieces_dir, filename)
            if os.path.exists(path):
                handles[key] = Rsvg.Handle.new_from_file(path)
        return handles

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def _draw(self, area, cr: cairo.Context, width: int, height: int) -> None:
        """Main draw function called by GTK."""
        if self._board is None:
            return

        square_size = min(width, height) / BOARD_SIZE

        self._draw_squares(cr, square_size)
        self._draw_highlights(cr, square_size)
        self._draw_pieces(cr, square_size)
        self._draw_coordinates(cr, square_size)

    def _draw_squares(self, cr: cairo.Context, sq: float) -> None:
        """Draw the 64 squares."""
        for rank in range(BOARD_SIZE):
            for file in range(BOARD_SIZE):
                x = file * sq
                y = (BOARD_SIZE - 1 - rank) * sq

                if (rank + file) % 2 == 0:
                    cr.set_source_rgb(*LIGHT_SQUARE)
                else:
                    cr.set_source_rgb(*DARK_SQUARE)

                cr.rectangle(x, y, sq, sq)
                cr.fill()

    def _draw_highlights(self, cr: cairo.Context, sq: float) -> None:
        """Highlight selected square and valid destinations."""
        selected = self._selected_square
        if self._dragging and self._drag_square is not None:
            selected = self._drag_square

        if selected is None:
            return

        rank, file = divmod(selected, BOARD_SIZE)
        x = file * sq
        y = (BOARD_SIZE - 1 - rank) * sq
        cr.set_source_rgba(*HIGHLIGHT)
        cr.rectangle(x, y, sq, sq)
        cr.fill()

        for move in self._valid_moves:
            rank, file = divmod(move.to_square, BOARD_SIZE)
            x = file * sq
            y = (BOARD_SIZE - 1 - rank) * sq
            cr.set_source_rgba(*HINT_COLOR)
            cr.rectangle(x, y, sq, sq)
            cr.fill()

    def _draw_pieces(self, cr: cairo.Context, sq: float) -> None:
        """Draw each piece using its SVG image."""
        for rank in range(BOARD_SIZE):
            for file in range(BOARD_SIZE):
                square = rank * BOARD_SIZE + file

                # Skip the piece being dragged (drawn separately at end)
                if self._dragging and square == self._drag_square:
                    continue

                piece = self._board.get_piece_at(square)
                if piece is None:
                    continue

                handle = self._pieces.get(piece)
                if handle is None:
                    continue

                x = file * sq
                y = (BOARD_SIZE - 1 - rank) * sq

                has_size, svg_w, svg_h = handle.get_intrinsic_size_in_pixels()
                if not has_size or svg_w == 0 or svg_h == 0:
                    svg_w, svg_h = 45.0, 45.0

                scale = sq / max(svg_w, svg_h)

                cr.save()
                cr.translate(x, y)
                cr.scale(scale, scale)
                handle.render_cairo(cr)
                cr.restore()

        # Draw the dragged piece on top at mouse position
        if self._dragging and self._drag_square is not None:
            piece = self._board.get_piece_at(self._drag_square)
            if piece is not None:
                handle = self._pieces.get(piece)
                if handle is not None:
                    has_size, svg_w, svg_h = handle.get_intrinsic_size_in_pixels()
                    if not has_size or svg_w == 0 or svg_h == 0:
                        svg_w, svg_h = 45.0, 45.0
                    scale = sq / max(svg_w, svg_h)
                    cr.save()
                    cr.translate(self._drag_x - sq / 2, self._drag_y - sq / 2)
                    cr.scale(scale, scale)
                    handle.render_cairo(cr)
                    cr.restore()

    def _draw_coordinates(self, cr: cairo.Context, sq: float) -> None:
        """Draw rank numbers and file letters around the board."""
        cr.set_font_size(sq * 0.18)

        for i in range(BOARD_SIZE):
            cr.set_source_rgb(0.3, 0.3, 0.3)
            cr.move_to(2, (BOARD_SIZE - 1 - i) * sq + sq * 0.25)
            cr.show_text(str(i + 1))

            cr.move_to(i * sq + sq * 0.8, BOARD_SIZE * sq - 2)
            cr.show_text(chr(ord("a") + i))

    # ------------------------------------------------------------------
    # Click-to-move handling
    # ------------------------------------------------------------------

    def _on_click(self, gesture, n_press, x, y) -> None:
        """Handle a click on the board."""
        if self._board is None:
            return

        sq_size = min(self.get_width(), self.get_height()) / BOARD_SIZE
        file = int(x / sq_size)
        rank = BOARD_SIZE - 1 - int(y / sq_size)

        if not (0 <= file < BOARD_SIZE and 0 <= rank < BOARD_SIZE):
            return

        clicked_square = rank * BOARD_SIZE + file

        # Case 1: a valid destination is clicked → play the move
        for move in self._valid_moves:
            if move.to_square == clicked_square:
                self._selected_square = None
                self._valid_moves = []
                self.queue_draw()
                if self.on_move_played:
                    self.on_move_played(move)
                return

        # Case 2: a piece of the current player is clicked → select it
        piece = self._board.get_piece_at(clicked_square)
        if piece is not None and piece[1] == self._current_color:
            self._selected_square = clicked_square
            self._valid_moves = [
                m for m in self._engine.generate_legal_moves(
                    self._board, self._current_color
                )
                if m.from_square == clicked_square
            ]
            self.queue_draw()
            return

        # Case 3: anything else → clear selection
        self._selected_square = None
        self._valid_moves = []
        self.queue_draw()

    # ------------------------------------------------------------------
    # Drag'n'drop handling
    # ------------------------------------------------------------------

    def _on_drag_begin(self, gesture, x, y) -> None:
        """User starts dragging — select the piece."""
        if self._board is None:
            return

        sq_size = min(self.get_width(), self.get_height()) / BOARD_SIZE
        file = int(x / sq_size)
        rank = BOARD_SIZE - 1 - int(y / sq_size)

        if not (0 <= file < BOARD_SIZE and 0 <= rank < BOARD_SIZE):
            return

        square = rank * BOARD_SIZE + file
        piece = self._board.get_piece_at(square)

        if piece is None or piece[1] != self._current_color:
            return

        self._drag_square = square
        self._drag_x = x
        self._drag_y = y
        self._dragging = True
        self._selected_square = None

        self._valid_moves = [
            m for m in self._engine.generate_legal_moves(
                self._board, self._current_color
            )
            if m.from_square == square
        ]
        self.queue_draw()

    def _on_drag_update(self, gesture, dx, dy) -> None:
        """Mouse moved while dragging — update piece position."""
        if not self._dragging:
            return

        ok, start_x, start_y = gesture.get_start_point()
        if not ok:
            return

        self._drag_x = start_x + dx
        self._drag_y = start_y + dy
        self.queue_draw()

    def _on_drag_end(self, gesture, dx, dy) -> None:
        """User releases — play the move if dropped on a valid square."""
        if not self._dragging:
            return

        sq_size = min(self.get_width(), self.get_height()) / BOARD_SIZE
        ok, start_x, start_y = gesture.get_start_point()
        if not ok:
            self._dragging = False
            self._drag_square = None
            self._valid_moves = []
            self.queue_draw()
            return

        end_x = start_x + dx
        end_y = start_y + dy

        file = int(end_x / sq_size)
        rank = BOARD_SIZE - 1 - int(end_y / sq_size)

        self._dragging = False
        self._drag_square = None

        if not (0 <= file < BOARD_SIZE and 0 <= rank < BOARD_SIZE):
            self._valid_moves = []
            self.queue_draw()
            return

        target_square = rank * BOARD_SIZE + file

        for move in self._valid_moves:
            if move.to_square == target_square:
                self._valid_moves = []
                self.queue_draw()
                if self.on_move_played:
                    self.on_move_played(move)
                return

        self._valid_moves = []
        self.queue_draw()