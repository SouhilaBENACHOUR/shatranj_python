"""

window.py - Main application window

Role: builds the main window with a welcome screen, menu bar, board widget,

      and right panel. Handles all game logic callbacks.

"""

import gi

gi.require_version("Gtk", "4.0")

from gi.repository import Gtk, Gio, GLib  # noqa: E402

from shatranj.domain.rules.rules_engine import RulesEngine  # noqa: E402

from shatranj.domain.ai.ai_player import AIPlayer  # noqa: E402

from shatranj.presentation.cli.game_state import GameState  # noqa: E402

from shatranj.presentation.gui.board_widget import BoardWidget  # noqa: E402

from shatranj.utils.constants import WHITE, BLACK  # noqa: E402

import threading  # noqa: E402
import time  # noqa: E402


class NewGameDialog(Gtk.Dialog):
    """

    Dialog for configuring a new game.

    Allows the user to choose:

      - Game mode: Human vs Human, Human vs AI, AI vs AI

      - If AI involved: which algorithm (Minimax, Alpha-Beta, MCTS)

      - If AI involved: which color the AI plays

    """

    def __init__(self, parent) -> None:

        super().__init__(title="New Game", transient_for=parent, modal=True)

        self.set_default_size(400, 300)

        self.add_button("Cancel", Gtk.ResponseType.CANCEL)

        self.add_button("Start", Gtk.ResponseType.OK)

        box = self.get_content_area()

        box.set_spacing(12)

        box.set_margin_top(16)

        box.set_margin_bottom(16)

        box.set_margin_start(16)

        box.set_margin_end(16)

        # --- Game mode ---

        mode_label = Gtk.Label(label="Game Mode")

        mode_label.set_halign(Gtk.Align.START)

        box.append(mode_label)

        self._mode_combo = Gtk.DropDown.new_from_strings(
            [
                "Human vs Human",
                "Human vs AI",
                "AI vs AI",
            ]
        )

        self._mode_combo.set_selected(0)

        self._mode_combo.connect("notify::selected", self._on_mode_changed)

        box.append(self._mode_combo)

        # --- AI color (only for Human vs AI) ---

        self._color_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

        color_label = Gtk.Label(label="AI plays")

        color_label.set_halign(Gtk.Align.START)

        self._color_box.append(color_label)

        self._color_combo = Gtk.DropDown.new_from_strings(["Black", "White"])

        self._color_combo.set_selected(0)

        self._color_box.append(self._color_combo)

        box.append(self._color_box)

        # --- AI algorithm ---

        self._algo_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

        algo_label = Gtk.Label(label="AI Algorithm")

        algo_label.set_halign(Gtk.Align.START)

        self._algo_box.append(algo_label)

        self._algo_combo = Gtk.DropDown.new_from_strings(
            [
                "Alpha-Beta (recommended)",
                "Minimax",
                "MCTS",
            ]
        )

        self._algo_combo.set_selected(0)

        self._algo_box.append(self._algo_combo)

        box.append(self._algo_box)

        # Initially hide AI options (Human vs Human selected)

        self._update_visibility()

    def _on_mode_changed(self, *_) -> None:
        """Show/hide AI options depending on the selected mode."""

        self._update_visibility()

    def _update_visibility(self) -> None:
        """Show AI color selector only for Human vs AI mode."""

        mode = self._mode_combo.get_selected()

        # mode 0 = Human vs Human → hide everything

        # mode 1 = Human vs AI    → show algo + color

        # mode 2 = AI vs AI       → show algo only

        self._algo_box.set_visible(mode in (1, 2))

        self._color_box.set_visible(mode == 1)

    def get_config(self) -> dict:
        """

        Return the selected configuration as a dictionary.

        Keys:

          mode      → "hvh", "hvai", "aivai"

          ai_color  → "BLACK" or "WHITE" (for hvai mode only)

          algorithm → "alphabeta", "minimax", "mcts"

        """

        mode_idx = self._mode_combo.get_selected()

        modes = ["hvh", "hvai", "aivai"]

        mode = modes[mode_idx]

        color_idx = self._color_combo.get_selected()

        ai_color = "BLACK" if color_idx == 0 else "WHITE"

        algo_idx = self._algo_combo.get_selected()

        algos = ["alphabeta", "minimax", "mcts"]

        algorithm = algos[algo_idx]

        return {
            "mode": mode,
            "ai_color": ai_color,
            "algorithm": algorithm,
        }


class ShatranjWindow(Gtk.ApplicationWindow):
    """

    Main application window.

    Two states:

      1. Welcome screen — shown at startup, before any game

      2. Game screen    — shown when a game is in progress

    Contains:

      - A menu bar (File, Game, Help)

      - A stack switching between welcome screen and game screen

      - A board widget (left of game screen)

      - A right panel (timer, move history, undo/hint buttons)

    """

    def __init__(self, **kwargs) -> None:

        # Initialize the parent Gtk.ApplicationWindow

        super().__init__(**kwargs)

        # Title displayed in the window title bar

        self.set_title("Shatranj")

        # Default window size in pixels (width x height)

        self.set_default_size(900, 650)

        # Rules engine — validates moves, detects end of game

        self._engine = RulesEngine()

        # Current game state (None = no game started)

        self._state: GameState | None = None

        # AI players dict: color → AIPlayer (empty = human vs human)

        self._ai_players: dict[str, AIPlayer] = {}

        self._timer_source_id: int | None = None
        self._timer_started_at: float | None = None

        # Build the interface in order

        self._build_ui()  # layout and widgets

        self._build_menu()  # menu bar

        self._build_shortcuts()  # keyboard shortcuts

    # ------------------------------------------------------------------

    # UI construction

    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        """Builds the main layout with a stack (welcome ↔ game)."""

        # Vertical box — main container of the window

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        self.set_child(vbox)

        # Stack — switches between welcome screen and game screen

        # without recreating widgets

        self._stack = Gtk.Stack()

        self._stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)

        self._stack.set_transition_duration(300)

        vbox.append(self._stack)

        # Build the two screens and add them to the stack

        self._stack.add_named(self._build_welcome_screen(), "welcome")

        self._stack.add_named(self._build_game_screen(), "game")

        # Show welcome screen at startup

        self._stack.set_visible_child_name("welcome")

    def _build_welcome_screen(self) -> Gtk.Box:
        """

        Builds the welcome screen shown at startup.

        Contains the game title and a "New Game" button.

        """

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)

        box.set_halign(Gtk.Align.CENTER)

        box.set_valign(Gtk.Align.CENTER)

        box.set_hexpand(True)

        box.set_vexpand(True)

        # Game title

        title = Gtk.Label(label="Shatranj")

        title.add_css_class("title-1")  # GTK4 large title style

        box.append(title)

        # Subtitle

        subtitle = Gtk.Label(label="Indian Chess")

        subtitle.add_css_class("dim-label")

        box.append(subtitle)

        # Spacing

        box.append(Gtk.Box())

        # "New Game" button — opens the config dialog

        new_btn = Gtk.Button(label="New Game")

        new_btn.add_css_class("suggested-action")  # blue button in GTK4

        new_btn.set_size_request(200, 48)

        new_btn.connect("clicked", self._on_new_game)

        box.append(new_btn)

        # "Load Game" button

        load_btn = Gtk.Button(label="Load Game")

        load_btn.set_size_request(200, 48)

        load_btn.connect("clicked", self._on_load_game)

        box.append(load_btn)

        return box

    def _build_game_screen(self) -> Gtk.Box:
        """

        Builds the game screen with the board and right panel.

        """

        hbox = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=10,
        )

        hbox.set_margin_top(10)

        hbox.set_margin_bottom(10)

        hbox.set_margin_start(10)

        hbox.set_margin_end(10)

        # Our custom board widget

        self._board_widget = BoardWidget(self._engine)

        self._board_widget.set_size_request(480, 480)

        self._board_widget.set_hexpand(False)

        self._board_widget.set_vexpand(True)

        # When the user plays a move, BoardWidget calls this callback

        self._board_widget.on_move_played = self._on_move_played

        hbox.append(self._board_widget)

        # Build and add the right panel

        right_panel = self._build_right_panel()

        hbox.append(right_panel)

        return hbox

    def _build_right_panel(self) -> Gtk.Box:
        """Right panel: timer + move history + buttons."""

        panel = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=8,
        )

        panel.set_size_request(200, -1)

        # Timer label — shows "00:00" for now

        self._timer_label = Gtk.Label(label="00:00")

        panel.append(self._timer_label)

        # "Move History" label aligned to the left

        history_label = Gtk.Label(label="Move History")

        history_label.set_halign(Gtk.Align.START)

        panel.append(history_label)

        # ScrolledWindow with move list

        scroll = Gtk.ScrolledWindow()

        scroll.set_vexpand(True)

        self._history_list = Gtk.ListBox()

        self._history_list.set_selection_mode(Gtk.SelectionMode.NONE)

        scroll.set_child(self._history_list)

        panel.append(scroll)

        # Undo button

        undo_btn = Gtk.Button(label="Undo")

        undo_btn.connect("clicked", self._on_undo)

        panel.append(undo_btn)

        # Hint button

        hint_btn = Gtk.Button(label="Hint")

        hint_btn.connect("clicked", self._on_hint)

        panel.append(hint_btn)

        # Back to menu button

        menu_btn = Gtk.Button(label="Back to Menu")

        menu_btn.connect("clicked", self._on_back_to_menu)

        panel.append(menu_btn)

        return panel

    # ------------------------------------------------------------------

    # Timer

    # ------------------------------------------------------------------

    def _start_timer(self) -> None:
        """Start the elapsed game timer from zero."""

        self._stop_timer(reset=True)
        self._timer_started_at = time.monotonic()
        self._timer_source_id = GLib.timeout_add_seconds(1, self._on_timer_tick)
        self._on_timer_tick()

    def _stop_timer(self, reset: bool = False) -> None:
        """Stop the timer and optionally reset the label."""

        if self._timer_source_id is not None:
            GLib.source_remove(self._timer_source_id)
            self._timer_source_id = None

        self._timer_started_at = None

        if reset:
            self._timer_label.set_label("00:00")

    def _on_timer_tick(self) -> bool:
        """Refresh the elapsed time label while a game is running."""

        if self._state is None or self._timer_started_at is None:
            self._timer_source_id = None
            return False

        elapsed = int(time.monotonic() - self._timer_started_at)
        minutes, seconds = divmod(elapsed, 60)
        self._timer_label.set_label(f"{minutes:02d}:{seconds:02d}")
        return True

    # ------------------------------------------------------------------

    # Menu bar (F27)

    # ------------------------------------------------------------------

    def _build_menu(self) -> None:
        """Builds the menu bar."""

        menu = Gio.Menu()

        file_menu = Gio.Menu()

        file_menu.append("New Game", "win.new-game")

        file_menu.append("Load Game", "win.load-game")

        file_menu.append("Save Game", "win.save-game")

        file_menu.append("Configuration", "win.configuration")

        file_menu.append("Info", "win.info")

        file_menu.append("Quit", "app.quit")

        menu.append_submenu("File", file_menu)

        game_menu = Gio.Menu()

        game_menu.append("Undo", "win.undo")

        game_menu.append("Redo", "win.redo")

        game_menu.append("Pause", "win.pause")

        game_menu.append("Hint", "win.hint")

        menu.append_submenu("Game", game_menu)

        help_menu = Gio.Menu()

        help_menu.append("Help", "win.help")

        menu.append_submenu("Help", help_menu)

        actions = {
            "new-game": self._on_new_game,
            "load-game": self._on_load_game,
            "save-game": self._on_save_game,
            "configuration": self._on_configuration,
            "info": self._on_info,
            "undo": self._on_undo,
            "redo": self._on_redo,
            "pause": self._on_pause,
            "hint": self._on_hint,
            "help": self._on_help,
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
            "app.quit": ["<Ctrl>q"],
            "win.new-game": ["<Ctrl>n"],
            "win.load-game": ["<Ctrl>l"],
            "win.save-game": ["<Ctrl>s"],
            "win.configuration": ["<Ctrl>comma"],
            "win.info": ["<Ctrl>i"],
            "win.undo": ["<Ctrl>u"],
            "win.redo": ["<Ctrl>r"],
            "win.pause": ["<Ctrl>p"],
            "win.hint": ["<Ctrl>h"],
        }

        for action, accels in shortcuts.items():

            app.set_accels_for_action(action, accels)

    # ------------------------------------------------------------------

    # Game setup

    # ------------------------------------------------------------------

    def _start_game(self, config: dict) -> None:
        """

        Start a new game with the given configuration.

        config keys:

          mode      → "hvh", "hvai", "aivai"

          ai_color  → "BLACK" or "WHITE"

          algorithm → "alphabeta", "minimax", "mcts"

        """

        # Create a fresh game state

        self._state = GameState()

        self._ai_players = {}

        mode = config["mode"]

        algo = config["algorithm"]

        # depth depends on algorithm

        depth = 100 if algo == "mcts" else 3

        if mode == "hvai":

            # One AI player

            ai_color = config["ai_color"]

            self._ai_players[ai_color] = AIPlayer(
                color=ai_color,
                depth=depth,
                algorithm=algo,
                scoring="advanced",
            )

        elif mode == "aivai":

            # Both players are AI

            self._ai_players[WHITE] = AIPlayer(
                color=WHITE, depth=depth, algorithm=algo, scoring="advanced"
            )

            self._ai_players[BLACK] = AIPlayer(
                color=BLACK, depth=depth, algorithm=algo, scoring="advanced"
            )

        # Update board display and clear history

        self._board_widget.set_board(self._state.board, self._state.current_color)

        self._update_history()

        self._start_timer()

        # Switch to game screen

        self._stack.set_visible_child_name("game")

        # If white is AI, let it play immediately

        self._auto_play_ai_turns()

    def _auto_play_ai_turns(self) -> None:
        """Let AI play in a background thread to avoid freezing the UI."""

        if self._state is None:

            return

        if self._state.current_color not in self._ai_players:

            return

        def ai_thread():

            while (
                self._state is not None
                and self._state.current_color in self._ai_players
            ):

                ai = self._ai_players[self._state.current_color]

                move = ai.choose_move(self._state.board)

                if move is None:

                    break

                # GLib.idle_add ensures GTK updates happen in the main thread

                from gi.repository import GLib

                GLib.idle_add(self._apply_ai_move, move)

                # Wait a tiny bit so the UI can refresh between moves

                import time

                time.sleep(0.3)

                # Wait until the move is applied before continuing

                # (avoids race conditions in AI vs AI)

                import time as t

                deadline = t.time() + 5

                while (
                    self._state is not None
                    and self._state.current_color in self._ai_players
                    and t.time() < deadline
                ):

                    time.sleep(0.05)

        thread = threading.Thread(target=ai_thread, daemon=True)

        thread.start()

    def _apply_ai_move(self, move) -> bool:
        """Apply an AI move in the GTK main thread.\

         Returns False to remove from idle."""

        if self._state is None:

            return False

        self._state.apply_move(move)

        self._board_widget.set_board(self._state.board, self._state.current_color)

        self._update_history()

        self._check_game_over()

        return False  # GLib.idle_add requires returning False to stop repeating

    # ------------------------------------------------------------------

    # Callbacks

    # ------------------------------------------------------------------

    def _on_new_game(self, *_) -> None:
        """Open the new game configuration dialog."""

        dialog = NewGameDialog(self)

        dialog.connect("response", self._on_new_game_response)

        dialog.present()

    def _on_new_game_response(self, dialog, response) -> None:
        """Called when the user closes the new game dialog."""

        if response == Gtk.ResponseType.OK:

            config = dialog.get_config()

            dialog.destroy()

            self._start_game(config)

        else:

            dialog.destroy()

    def _on_back_to_menu(self, *_) -> None:
        """Go back to the welcome screen."""

        self._stop_timer(reset=True)

        self._state = None

        self._ai_players = {}

        self._stack.set_visible_child_name("welcome")

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

            from shatranj.presentation.cli.cli import CLI

            cli = CLI()

            cli._do_load([path])

            if cli._state is not None:

                self._state = cli._state

                self._ai_players = {}

                self._board_widget.set_board(
                    self._state.board, self._state.current_color
                )

                self._update_history()

                self._start_timer()

                # Switch to game screen after loading

                self._stack.set_visible_child_name("game")

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

    def _on_configuration(self, *_) -> None:

        print("Configuration")

    def _on_info(self, *_) -> None:

        print("Info")

    def _on_undo(self, *_) -> None:

        if self._state is None:

            return

        self._state.undo()

        self._board_widget.set_board(self._state.board, self._state.current_color)

        self._update_history()

    def _on_redo(self, *_) -> None:

        print("Redo")

    def _on_pause(self, *_) -> None:

        print("Pause")

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

        to = B.square_to_algebraic(move.to_square)

        dialog = Gtk.AlertDialog()

        dialog.set_message("Hint")

        dialog.set_detail(f"Try: {frm}-{to}")

        dialog.show(self)

    def _on_help(self, *_) -> None:

        print("Help")

    def _on_move_played(self, move) -> None:
        """Called by BoardWidget when the user plays a move."""

        if self._state is None:

            return

        self._state.apply_move(move)

        self._board_widget.set_board(self._state.board, self._state.current_color)

        self._update_history()

        if self._check_game_over():

            return

        # Let AI play if it's its turn

        self._auto_play_ai_turns()

    def _update_history(self) -> None:
        """Refresh the move history list in the right panel."""

        from shatranj.domain.core.board import Board as B

        # Clear existing rows

        while True:

            row = self._history_list.get_row_at_index(0)

            if row is None:

                break

            self._history_list.remove(row)

        if self._state is None:

            return

        # Refill with all moves

        for i, move in enumerate(self._state.get_history()):

            color = "W" if move.color == WHITE else "B"

            frm = B.square_to_algebraic(move.from_square)

            to = B.square_to_algebraic(move.to_square)

            sep = "x" if move.captured_piece else "-"

            label = Gtk.Label(label=f"{i+1}. {color} {frm}{sep}{to}")

            label.set_halign(Gtk.Align.START)

            self._history_list.append(label)

    def _check_game_over(self) -> bool:
        """Check if the game is over after a move."""

        if self._state is None:

            return False

        current = self._state.current_color

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
        """Show a dialog when the game is over, then return to menu."""

        dialog = Gtk.AlertDialog()

        dialog.set_message("Game Over")

        dialog.set_detail(message)

        dialog.show(self)

        self._stop_timer()

        # Keep the board visible — don't clear it

        self._state = None

        self._ai_players = {}
