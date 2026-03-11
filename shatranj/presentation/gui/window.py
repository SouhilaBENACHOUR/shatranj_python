"""
window.py - Main window of the Shatranj GUI

Contains:
  - Menu bar (File, Game, Help)
  - Keyboard shortcuts (F28)
  - Main layout (board + right panel)
"""

import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gio
from shatranj.presentation.gui.board_widget import BoardWidget
from shatranj.domain.rules.rules_engine import RulesEngine
from shatranj.presentation.cli.game_state import GameState
from shatranj.utils.constants import WHITE, BLACK

class ShatranjWindow(Gtk.ApplicationWindow):
    """Main application window."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        self.set_title("Shatranj")
        self.set_default_size(800, 600)
        self._engine = RulesEngine()
        self._state: GameState | None = None
        self._build_ui()
        self._build_menu()
        self._build_shortcuts()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        """Builds the main layout."""
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_child(vbox)

        hbox = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=10,
            margin_top=10,
            margin_bottom=10,
            margin_start=10,
            margin_end=10,
        )
        vbox.append(hbox)

        # --- Board placeholder ---
        self._board_widget = BoardWidget(self._engine)
        self._board_widget.set_size_request(480, 480)
        self._board_widget.set_hexpand(False)
        self._board_widget.set_vexpand(True)
        self._board_widget.on_move_played = self._on_move_played
        hbox.append(self._board_widget)

        # --- Right panel ---
        right_panel = self._build_right_panel()
        hbox.append(right_panel)

    def _build_right_panel(self) -> Gtk.Box:
        """Right panel: timer + move history + buttons."""
        panel = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=8,
            width_request=200,
        )

        # Timer
        self._timer_label = Gtk.Label(label="00:00")
        panel.append(self._timer_label)

        # Move history
        history_label = Gtk.Label(label="Move History")
        history_label.set_halign(Gtk.Align.START)
        panel.append(history_label)

        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        self._history_list = Gtk.ListBox()
        self._history_list.set_selection_mode(Gtk.SelectionMode.NONE)
        scroll.set_child(self._history_list)
        panel.append(scroll)

        # Undo / Hint buttons
        undo_btn = Gtk.Button(label="Undo")
        undo_btn.connect("clicked", self._on_undo)
        panel.append(undo_btn)

        hint_btn = Gtk.Button(label="Hint")
        hint_btn.connect("clicked", self._on_hint)
        panel.append(hint_btn)

        return panel

    # ------------------------------------------------------------------
    # Menu bar (F27)
    # ------------------------------------------------------------------

    def _build_menu(self) -> None:
        """Builds the menu bar."""
        menu = Gio.Menu()

        file_menu = Gio.Menu()
        file_menu.append("New Game",      "win.new-game")
        file_menu.append("Load Game",     "win.load-game")
        file_menu.append("Save Game",     "win.save-game")
        file_menu.append("Configuration", "win.configuration")
        file_menu.append("Info",          "win.info")
        file_menu.append("Quit",          "app.quit")
        menu.append_submenu("File", file_menu)

        game_menu = Gio.Menu()
        game_menu.append("Undo",  "win.undo")
        game_menu.append("Redo",  "win.redo")
        game_menu.append("Pause", "win.pause")
        game_menu.append("Hint",  "win.hint")
        menu.append_submenu("Game", game_menu)

        help_menu = Gio.Menu()
        help_menu.append("Help", "win.help")
        menu.append_submenu("Help", help_menu)

        actions = {
            "new-game":      self._on_new_game,
            "load-game":     self._on_load_game,
            "save-game":     self._on_save_game,
            "configuration": self._on_configuration,
            "info":          self._on_info,
            "undo":          self._on_undo,
            "redo":          self._on_redo,
            "pause":         self._on_pause,
            "hint":          self._on_hint,
            "help":          self._on_help,
        }
        for name, callback in actions.items():
            action = Gio.SimpleAction.new(name, None)
            action.connect("activate", callback)
            self.add_action(action)

        self.get_application().set_menubar(menu)
        self.set_show_menubar(True)

    # ------------------------------------------------------------------
    # Keyboard shortcuts (F28)
    # ------------------------------------------------------------------

    def _build_shortcuts(self) -> None:
        """Configures keyboard shortcuts."""
        app = self.get_application()
        shortcuts = {
            "app.quit":          ["<Ctrl>q"],
            "win.new-game":      ["<Ctrl>n"],
            "win.load-game":     ["<Ctrl>l"],
            "win.save-game":     ["<Ctrl>s"],
            "win.configuration": ["<Ctrl>comma"],
            "win.info":          ["<Ctrl>i"],
            "win.undo":          ["<Ctrl>u"],
            "win.redo":          ["<Ctrl>r"],
            "win.pause":         ["<Ctrl>p"],
            "win.hint":          ["<Ctrl>h"],
        }
        for action, accels in shortcuts.items():
            app.set_accels_for_action(action, accels)

    # ------------------------------------------------------------------
    # Callbacks (placeholders for now)
    # ------------------------------------------------------------------

    def _on_new_game(self, *_) -> None:
        self._state = GameState()
        self._board_widget.set_board(self._state.board, self._state.current_color)
    def _on_load_game(self, *_) -> None:
        dialog = Gtk.FileDialog()
        dialog.set_title("Load Game")
        dialog.open(self, None, self._on_load_game_finish)

    def _on_load_game_finish(self, dialog, result) -> None:
        try:
            file = dialog.open_finish(result)
            if file is None:
                return
            path = file.get_path()
            # Reuse CLI _do_load logic
            from shatranj.presentation.cli.cli import CLI
            cli = CLI()
            cli._do_load([path])
            if cli._state is not None:
                self._state = cli._state
                self._board_widget.set_board(
                    self._state.board, self._state.current_color
                )
                self._update_history()
        except Exception:
            pass

    def _on_save_game(self, *_) -> None:
        if self._state is None:
            return
        dialog = Gtk.FileDialog()
        dialog.set_title("Save Game")
        dialog.save(self, None, self._on_save_game_finish)

    def _on_save_game_finish(self, dialog, result) -> None:
        try:
            file = dialog.save_finish(result)
            if file is None:
                return
            path = file.get_path()
            from shatranj.presentation.cli.cli import CLI
            cli = CLI()
            cli._state = self._state
            cli._save_to_file(path)
        except Exception:
            pass
    def _on_configuration(self, *_) -> None: print("Configuration")
    def _on_info(self, *_)          -> None: print("Info")
    def _on_undo(self, *_) -> None:
        if self._state is None:
            return
        self._state.undo()
        self._board_widget.set_board(self._state.board, self._state.current_color)
        self._update_history()
    def _on_redo(self, *_)          -> None: print("Redo")
    def _on_pause(self, *_)         -> None: print("Pause")
    def _on_hint(self, *_) -> None:
        if self._state is None:
            return
        moves = self._engine.generate_legal_moves(
            self._state.board, self._state.current_color
        )
        if not moves:
            return
        move = moves[0]
        from shatranj.domain.core.board import Board as B
        frm = B.square_to_algebraic(move.from_square)
        to  = B.square_to_algebraic(move.to_square)
        dialog = Gtk.AlertDialog()
        dialog.set_message("Hint")
        dialog.set_detail(f"Try: {frm}-{to}")
        dialog.show(self)
    def _on_help(self, *_)          -> None: print("Help")
    def _on_move_played(self, move) -> None:
        if self._state is None:
            return
        self._state.apply_move(move)
        self._board_widget.set_board(self._state.board, self._state.current_color)
        self._update_history()
        self._check_game_over()

    def _update_history(self) -> None:
        """Refresh the move history list."""
        from shatranj.domain.core.board import Board as B
        # Clear existing rows
        while True:
            row = self._history_list.get_row_at_index(0)
            if row is None:
                break
            self._history_list.remove(row)
        # Add moves
        for i, move in enumerate(self._state.get_history()):
            color = "W" if move.color == "WHITE" else "B"
            frm = B.square_to_algebraic(move.from_square)
            to  = B.square_to_algebraic(move.to_square)
            sep = "x" if move.captured_piece else "-"
            label = Gtk.Label(label=f"{i+1}. {color} {frm}{sep}{to}")
            label.set_halign(Gtk.Align.START)
            self._history_list.append(label)

    def _check_game_over(self) -> bool:
        """Check if the game is over after a move."""
        if self._state is None:
            return False

        current  = self._state.current_color
        opponent = BLACK if current == WHITE else WHITE

        if self._engine.is_checkmate(self._state.board, current):
            self._show_game_over_dialog(f"Checkmate! {opponent} wins!")
            return True

        if self._engine.is_stalemate(self._state.board, current):
            self._show_game_over_dialog(f"Stalemate! {opponent} wins!")
            return True

        if self._engine.is_bare_king(self._state.board, current):
            self._show_game_over_dialog(f"Bare King! {opponent} wins!")
            return True

        return False

    def _show_game_over_dialog(self, message: str) -> None:
        """Show a dialog when the game is over."""
        dialog = Gtk.AlertDialog()
        dialog.set_message("Game Over")
        dialog.set_detail(message)
        dialog.show(self)
        self._state = None
        self._board_widget.set_board(None, WHITE)        