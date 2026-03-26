"""
cli.py - Interactive shell for the Shatranj game

Role: entry point of the CLI interface.
      Reads user commands and calls the appropriate methods.

Why an interactive shell?
  The specification (F14) requires a shell with a ">>" prompt.
  readline (F16, F17, F18) automatically handles line editing, history,
  and Tab completion.

General structure:
  - run()          : main loop (read -> parse -> execute)
  - _do_XXX()      : one method per command
  - _parse_move()  : converts "e2-e4" into a Move object
"""

import builtins
import readline  # Enables line editing, history, and Tab completion
import re  # For parsing algebraic notation with a regex
import sys  # For sys.exit() and sys.stderr
import time

from shatranj.domain.core.move import Move
from shatranj.domain.rules.rules_engine import RulesEngine
from shatranj.utils.constants import WHITE, BLACK, SHAH, FERZ, ROOK
from shatranj.utils.constants import ALFIL, KNIGHT, PAWN
from shatranj.domain.ai.ai_player import AIPlayer
from shatranj.domain.core.board import Board

# Import our own modules
# We use relative imports because we are in the same package
from .display import print_board
from .game_state import GameState

# i18n: use _() installed by gettext, fallback to identity if not set
_ = builtins.__dict__.get("_", lambda x: x)


# ---------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------

PROMPT = ">> "  # Prompt displayed to the user (F14)
AUTO_PLAY_MAX_PLIES = 400  # Safety limit to avoid infinite AI loops
THREEFOLD_REPETITION_COUNT = 3
FIFTY_MOVE_RULE_PLIES = 100  # 50 full moves = 100 half-moves (plies)

# List of all recognized commands (for Tab completion, F18)
COMMANDS = [
    "new",
    "help",
    "quit",
    "load",
    "save",
    "pause",
    "hint",
    "undo",
    "redo",
    "show board",
    "show history",
    "show time",
    "show configuration",
    "set",
]

PIECE_LABELS = {
    PAWN: "pawn",
    ROOK: "rook",
    KNIGHT: "knight",
    ALFIL: "alfil",
    FERZ: "ferz",
    SHAH: "shah",
}


# ---------------------------------------------------------------------
# Main CLI class
# ---------------------------------------------------------------------


class CLI:
    """
    Interactive shell for playing Shatranj on the command line.

    Attributes:
      _state   : current game state (GameState)
      _engine  : rules engine (RulesEngine)
      _running : True while the main loop is running
      _saved   : True if the game has been saved since the last move
      _verbose : True if verbose mode is enabled
    """

    def __init__(self, verbose: bool = False, debug: bool = False) -> None:
        self._state: GameState | None = None  # No game at startup
        self._engine = RulesEngine()
        self._running = False
        self._saved = True  # Nothing to save at startup
        self._verbose = verbose
        self._ai_players: dict[str, AIPlayer] = {}
        self._debug = debug
        self._blitz_enabled = False
        self._blitz_minutes = 30
        self._clock_seconds = {
            WHITE: 0.0,
            BLACK: 0.0,
        }
        self._turn_started_at: float | None = None
        self._timer_paused = False

        # Configure readline for Tab completion (F18)
        readline.set_completer(self._completer)
        readline.parse_and_bind("tab: complete")

        # Configure readline for history (F17)
        # Ctrl+R is handled automatically by readline

    def enable_blitz(self, minutes: int) -> None:
        """Enable blitz mode for subsequent CLI games."""

        self._blitz_enabled = True
        self._blitz_minutes = max(1, minutes)
        self._reset_blitz_clock()

    def _reset_blitz_clock(self) -> None:
        """Reset both clocks to the configured blitz duration."""

        if self._blitz_enabled:
            base_seconds = float(self._blitz_minutes * 60)
            self._clock_seconds = {
                WHITE: base_seconds,
                BLACK: base_seconds,
            }
        else:
            self._clock_seconds = {
                WHITE: 0.0,
                BLACK: 0.0,
            }
        self._turn_started_at = None
        self._timer_paused = False

    def _start_turn_timer(self) -> None:
        """Start timing the current turn when blitz is active."""

        if self._blitz_enabled and self._state is not None:
            self._turn_started_at = time.monotonic()
        else:
            self._turn_started_at = None

    def _stop_turn_timer(self) -> None:
        """Stop the active turn timer."""

        self._turn_started_at = None
        self._timer_paused = False

    def _consume_turn_time(self) -> bool:
        """Deduct elapsed time from the active player and detect timeout."""

        if (
            not self._blitz_enabled
            or self._state is None
            or self._timer_paused
            or self._turn_started_at is None
        ):
            return False

        now = time.monotonic()
        elapsed = max(0.0, now - self._turn_started_at)
        current = self._state.current_color
        remaining = self._clock_seconds[current] - elapsed
        self._clock_seconds[current] = max(0.0, remaining)
        self._turn_started_at = now

        if remaining > 0:
            return False

        winner = BLACK if current == WHITE else WHITE
        print(f"Time out! {winner} wins!")
        self._state = None
        self._stop_turn_timer()
        return True

    def _format_clock(self, seconds: float) -> str:
        """Format remaining blitz time as MM:SS."""

        rounded = max(0, int(seconds + 0.999))
        minutes, seconds = divmod(rounded, 60)
        return f"{minutes:02d}:{seconds:02d}"

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self) -> None:
        """
        Start the main shell loop.

        Displays a welcome message, then reads commands one by one
        until the user types "quit".
        """
        self._running = True
        print(_("Welcome to Shatranj! Type 'help' to see available commands."))
        print(_("Start a new game with 'new'."))
        print()

        # launch AI game if configured from command line (-a flag)
        if hasattr(self, "_pending_new"):
            self._do_new(self._pending_new)
            del self._pending_new

        while self._running:
            try:
                raw = input(PROMPT).strip()
            except EOFError:
                print()
                self._do_quit([])
                break
            except KeyboardInterrupt:
                print()
                continue

            if not raw:
                continue

            readline.add_history(raw)
            self._dispatch(raw)

    # ------------------------------------------------------------------
    # Dispatcher: parses the command and calls the right method
    # ------------------------------------------------------------------

    def _dispatch(self, raw: str) -> None:
        """
        Parse the command line and call the corresponding method.

        Splits the input into words, then looks at the first word
        to identify the command.

        Special cases:
          - "show board" and "show history" are two-word commands
          - A move like "e2-e4" is not a keyword
        """
        if self._consume_turn_time():
            return

        parts = raw.split()
        if not parts:
            return

        cmd = parts[0].lower()
        args = parts[1:]  # Arguments after the command

        # Two-word commands: "show board", "show history", ...
        if cmd == "show":
            sub = args[0].lower() if args else ""
            if sub == "board":
                self._do_show_board()
            elif sub == "history":
                self._do_show_history()
            elif sub == "time":
                self._do_show_time()
            elif sub == "configuration":
                self._do_show_configuration()
            else:
                self._error(f"Unknown subcommand: show {sub}")
            return

        # Single-word commands
        handlers = {
            "new": self._do_new,
            "help": self._do_help,
            "quit": self._do_quit,
            "q": self._do_quit,
            "load": self._do_load,
            "save": self._do_save,
            "pause": self._do_pause,
            "hint": self._do_hint,
            "undo": self._do_undo,
            "redo": self._do_redo,
            "set": self._do_set,
        }

        if cmd in handlers:
            handlers[cmd](args)
            return

        # If not a known command, try to parse a move
        # Expected format: "e2-e4" or "e2xe4"
        if self._looks_like_move(raw):
            self._do_play_move(raw)
            return

        # Unknown command
        self._error(
            f"Unknown command: '{raw}'."
            "Type 'help' for the list of commands."
        )

    # ------------------------------------------------------------------
    # Check if a string looks like a move (algebraic notation)
    # ------------------------------------------------------------------

    def _looks_like_move(self, text: str) -> bool:
        """
        Return True if the text looks like a move in algebraic notation.

        Accepted formats (F19 of the specification):
          - "e2-e4"  : simple move
          - "e2xe4"  : capture (lowercase x)
          - "Ng8-f6" : with optional piece prefix
        """
        # Regex: optionally a piece letter, then square-separator-square
        pattern = r"^[A-Za-z]?[a-h][1-8][-x][a-h][1-8]$"
        return bool(re.match(pattern, text.strip()))

    # ------------------------------------------------------------------
    # Parse a move in algebraic notation -> Move object
    # ------------------------------------------------------------------

    def _parse_move(self, text: str) -> Move | None:
        """
        Convert a string like "e2-e4" into a Move object.

        Returns None if the format is invalid.

        Example:
          "e2-e4"  -> from_square=12, to_square=28
          "e2xe4"  -> same (capture is detected automatically by the board)

        Why Board.algebraic_to_square?
          This method converts "e2" -> 12 (rank=1, file=4 -> 1*8+4=12).
          It is already implemented in board.py, so we reuse it.
        """

        # Strip the piece prefix if present (e.g. "N" in "Ng8-f6")
        text = text.strip()
        if len(text) == 6 and text[0].isupper():
            text = text[1:]  # Remove "N": "Ng8-f6" -> "g8-f6"

        # Accept "-" or "x" as separator
        if len(text) != 5 or text[2] not in ("-", "x"):
            self._error(
                f"Invalid move format: '{text}'."
                "Expected format: e2-e4"
            )
            return None

        from_str = text[0:2]  # "e2"
        to_str = text[3:5]  # "e4"

        try:
            from_sq = Board.algebraic_to_square(from_str)
            to_sq = Board.algebraic_to_square(to_str)
        except ValueError as err:
            self._error(str(err))
            return None

        # Get the piece on the source square to build the Move
        piece_info = self._state.board.get_piece_at(from_sq)
        if piece_info is None:
            self._error(f"No piece on {from_str}.")
            return None

        piece_type, color = piece_info

        # Get the captured piece if any
        target = self._state.board.get_piece_at(to_sq)
        captured = target[0] if target is not None else None

        return Move(
            from_square=from_sq,
            to_square=to_sq,
            piece_type=piece_type,
            color=color,
            captured_piece=captured,
        )

    # ------------------------------------------------------------------
    # Commands
    # ------------------------------------------------------------------

    def _do_play_move(self, text: str) -> None:
        """
        Play a move entered by the user, then let the AI play if it is
        its turn.

        Steps:
          1. Check that a game is in progress
          2. Parse the move (algebraic notation -> Move)
          3. Check that it is the right player's turn
          4. Check that the move is legal
          5. Apply the move
          6. Check if the game is over
          7. Let the AI play if it is its turn
        """
        if self._state is None:
            self._error("No game in progress. Type 'new' to start a game.")
            return

        move = self._parse_move(text)
        if move is None:
            return

        # Check that the right player is moving
        if move.color != self._state.current_color:
            self._error(
                f"It's {self._state.current_color}'s turn,"
                f" not {move.color}'s."
            )
            return

        # Full legality check: geometry + Shah safety (no self-check)
        legal_moves = self._engine.generate_legal_moves(
            self._state.board, self._state.current_color
        )
        if move not in legal_moves:
            self._error(f"Illegal move: {text}")
            return

        # Apply the player's move
        self._state.apply_move(move)
        self._saved = False

        print(
            _("You played: {move}").format(
                move=self._format_move_with_piece(move)
            )
        )

        # Display the updated board
        print_board(self._state.board)
        print(
            _("It's now {color}'s turn.").format(
                color=self._state.current_color
            )
        )

        # Check if the game is over after the player's move
        if self._check_game_over():
            return

        self._start_turn_timer()

        # If the next turn is controlled by an AI, chain it automatically
        self._auto_play_ai_turns()

    def _check_game_over(self) -> bool:
        """
        Check if the game is over after a move.

        Returns True if the game is finished, False otherwise.

        Possible outcomes in Shatranj:
          - Checkmate  -> current player is in check with no legal moves
          - Stalemate  -> not in check but no legal moves (opponent wins)
          - Bare King  -> current player has only their Shah left
        """
        current = self._state.current_color

        # Checkmate -> current player loses
        if self._engine.is_checkmate(self._state.board, current):
            opponent = BLACK if current == WHITE else WHITE
            print(_("Checkmate! {color} wins!").format(color=opponent))
            self._state = None
            self._stop_turn_timer()
            return True

        # Stalemate -> victory for the one who caused it (Shatranj rule)
        if self._engine.is_stalemate(self._state.board, current):
            opponent = BLACK if current == WHITE else WHITE
            print(_("Stalemate! {color} wins!").format(color=opponent))
            self._state = None
            self._stop_turn_timer()
            return True

        # Bare King -> current player has only their Shah left
        if self._engine.is_bare_king(self._state.board, current):
            opponent = BLACK if current == WHITE else WHITE
            print(_("Bare King! {color} wins!").format(color=opponent))
            self._state = None
            self._stop_turn_timer()
            return True

        # Draw by threefold repetition (as in modern chess)
        if self._is_draw_by_threefold_repetition():
            print(_("Draw by threefold repetition."))
            self._state = None
            self._stop_turn_timer()
            return True

        # Fifty-move rule: no pawn moved and no capture
        if self._is_draw_by_fifty_move_rule():
            print(_("Draw by fifty-move rule."))
            self._state = None
            self._stop_turn_timer()
            return True

        return False  # Game continues

    def _is_draw_by_threefold_repetition(self) -> bool:
        """
        Detect if the current position has occurred 3 times
        (same piece placement + same player to move).
        """
        if self._state is None:
            return False

        target_color = self._state.current_color
        target_signature = tuple(sorted(self._state.board._boards.items()))
        expected_snapshot_size = len(self._state.board._boards)

        repetitions = 1  # current position counts as 1
        color_at_state = target_color

        for _, snapshot_before_move in reversed(self._state._history):
            # Previous state -> turn is inverted
            color_at_state = BLACK if color_at_state == WHITE else WHITE
            if color_at_state != target_color:
                continue

            # Some states loaded from file use empty snapshots
            if len(snapshot_before_move) != expected_snapshot_size:
                continue

            signature = tuple(sorted(snapshot_before_move.items()))
            if signature == target_signature:
                repetitions += 1
                if repetitions >= THREEFOLD_REPETITION_COUNT:
                    return True

        return False

    def _is_draw_by_fifty_move_rule(self) -> bool:
        """
        Detect the fifty-move rule:
        100 consecutive half-moves without a pawn move or capture.
        """
        if self._state is None:
            return False

        halfmoves_without_progress = 0
        for move, _ in reversed(self._state._history):
            if move.piece_type == PAWN or move.captured_piece is not None:
                break
            halfmoves_without_progress += 1
            if halfmoves_without_progress >= FIFTY_MOVE_RULE_PLIES:
                return True

        return False

    def _do_ai_move(self) -> None:
        """
        Let the AI play whose turn it is.

        1. Get the AI for the current color
        2. Display which algorithm the AI uses
        3. The AI calculates the best move
        4. If no move available -> end of game
        5. Otherwise apply the move and display the board
        6. Check if the game is over after the AI's move
        """
        if self._state is None:
            return

        # get the AI that plays the current color
        ai_player = self._ai_players.get(self._state.current_color)
        if ai_player is None:
            return

        # display which algorithm and depth the AI uses
        print(
            _("AI is thinking...{details}").format(
                details=self._format_ai_details(ai_player)
            )
        )

        move = ai_player.choose_move(self._state.board)
        if self._consume_turn_time():
            return

        # no move available -> end of game
        if move is None:
            self._check_game_over()
            return

        # display the move played by the AI in algebraic notation
        print(
            _("AI plays: {move}").format(
                move=self._format_move_with_piece(move)
            )
        )

        # apply the move on the board
        self._state.apply_move(move)
        self._saved = False

        # display the updated board
        print_board(self._state.board)
        print(f"\nIt's now {self._state.current_color}'s turn.")

        # check if the game is over after the AI's move
        if self._check_game_over():
            return

        self._start_turn_timer()

    def _auto_play_ai_turns(
        self, max_plies: int = AUTO_PLAY_MAX_PLIES
    ) -> None:
        """
        Chain AI turns as long as the current player is controlled by an AI.

        Used for:
          - human vs AI: play one AI move after the human's move
          - AI vs AI: automatically run through the entire game
        """
        plies = 0
        while (
            self._state is not None
            and self._state.current_color in self._ai_players
        ):
            if plies >= max_plies:
                print(f"\nDraw by move limit ({max_plies} plies).")
                self._state = None
                self._stop_turn_timer()
                return
            self._do_ai_move()
            plies += 1

    def _do_new(self, args: list[str]) -> None:
        """
        Start a new game.

        If an unsaved game is in progress, ask for confirmation.

        Usage from CLI :
          new
          new ai black
          new ai white minimax
          new ai black alphabeta 4
          new ai white mcts 500 advanced
          new ai-vs-ai

        Usage from main.py :
          _do_new(["ai", "black", "minimax", "6", "material"])
        """
        if self._state is not None and not self._saved:
            answer = input(
                "Current game is not saved."
                "Start a new game anyway? [y/N] "
            )
            if answer.strip().lower() not in ("y", "yes"):
                print("New game cancelled.")
                return

        self._state = GameState()
        self._saved = True
        self._ai_players = {}  # Reset AI players
        self._reset_blitz_clock()

        if len(args) >= 1 and args[0].lower() == "ai-vs-ai":
            self._ai_players[WHITE] = AIPlayer(color=WHITE, depth=2)
            self._ai_players[BLACK] = AIPlayer(color=BLACK, depth=2)
            print("New game started! AI plays WHITE and BLACK.")

        elif len(args) >= 2 and args[0].lower() == "ai":
            ai_color = args[1].upper()

            # optional algorithm as 3rd argument (default: alphabeta)
            algo = args[2].lower() if len(args) >= 3 else "alphabeta"

            if algo not in ("minimax", "alphabeta", "mcts"):
                self._error(
                    f"Unknown algorithm: '{algo}'."
                    "Use minimax, " "alphabeta or mcts."
                )
                return

            # optional depth as 4th argument
            if len(args) >= 4:
                try:
                    depth = int(args[3])
                    if depth < 1:
                        self._error("Depth must be a positive integer.")
                        return
                except ValueError:
                    self._error(
                        f"Invalid depth: '{args[3]}'. "
                        "Expected a positive integer."
                    )
                    return
            else:
                # default depth depending on algorithm
                if algo == "alphabeta":
                    depth = 3
                elif algo == "mcts":
                    depth = 100
                else:
                    depth = 3

            # optional scoring as 5th argument (default: advanced)
            scoring = args[4].lower() if len(args) >= 5 else "advanced"

            if scoring not in ("material", "positional", "advanced"):
                self._error(
                    f"Unknown scoring: '{scoring}'. Use material,"
                    " positional or advanced."
                )
                return

            if ai_color == "BLACK":
                self._ai_players[BLACK] = AIPlayer(
                    color=BLACK,
                    depth=depth,
                    algorithm=algo,
                    scoring=scoring,
                )
                print(
                    f"New game started! You play WHITE, AI plays BLACK "
                    f"({algo}, depth={depth}, scoring={scoring})."
                )

            elif ai_color == "WHITE":
                self._ai_players[WHITE] = AIPlayer(
                    color=WHITE,
                    depth=depth,
                    algorithm=algo,
                    scoring=scoring,
                )
                print(
                    f"New game started! AI plays WHITE "
                    f"({algo}, depth={depth}, scoring={scoring}),"
                    " you play BLACK."
                )
            else:
                self._error(
                    f"Unknown color: '{args[1]}'."
                    "Use 'black' or 'white'."
                )
                return

        else:
            print("New game started! White plays first.")

        if self._blitz_enabled:
            print(
                f"Blitz mode enabled: {self._blitz_minutes} minute(s) "
                "per player."
            )

        print()
        print_board(self._state.board)
        print()
        self._start_turn_timer()
        # If the current player is controlled by an AI, it plays immediately
        self._auto_play_ai_turns()

    def _do_contest(
        self,
        path: str,
        algo: str = "alphabeta",
        depth: int = 4,
        scoring: str = "advanced",
    ) -> int:
        # Redirects stdout to /dev/null during loading
        import os

        devnull = open(os.devnull, "w")
        old_stdout = sys.stdout
        sys.stdout = devnull

        self._do_load([path])

        sys.stdout = old_stdout
        devnull.close()

        if self._state is None:
            return 1

        ai = AIPlayer(
            color=self._state.current_color,
            depth=depth,
            algorithm=algo,
            scoring=scoring,
        )
        move = ai.choose_move(self._state.board)
        if move is None:
            print("no_move")
            return 0

        frm = Board.square_to_algebraic(move.from_square)
        to = Board.square_to_algebraic(move.to_square)
        sep = "x" if move.captured_piece else "-"
        print(f"{frm}{sep}{to}")
        return 0

    def _do_quit(self, args: list[str]) -> None:
        """
        Quit the program.

        If the game is not saved, offer to save it (F15).
        If the user does not clearly answer, quit without saving
        (default is N, as specified in F15).
        """
        if self._state is not None and not self._saved:
            print("Save the game before quitting? [y/N]", end=" ")
            answer = input().strip().lower()

            if answer in ("y", "yes"):
                # Ask for the file path
                path = input("Enter file path to save: ").strip()
                if path:
                    success = self._save_to_file(path)
                    if not success:
                        # Save failed: ask again (F15)
                        answer2 = (
                            input("Save failed. Try to save again? [y/N] ")
                            .strip()
                            .lower()
                        )
                        if answer2 in ("y", "yes"):
                            path2 = input("Enter file path to save: ").strip()
                            self._save_to_file(path2)
                else:
                    print("No path given, quitting without saving.")

        print(_("Goodbye!"))
        self._running = False

    def _do_help(self, args: list[str]) -> None:
        """
        Display general help or help for a specific command.

        Usage: help [CMD]
        """
        if args:
            cmd = args[0].lower()
            self._print_command_help(cmd)
        else:
            self._print_general_help()

    def _print_general_help(self) -> None:
        """Display the list of all available commands."""
        print("""
Available commands:
  new [ARGS]          Start a new game (e.g. ai white, ai black, ai-vs-ai)
  help [CMD]          Show this help or help for CMD
  quit                Quit the program
  load FILE           Load a game from a file
  save FILE           Save the current game to a file
  pause               Pause the blitz timer
  hint                Show a move suggestion
  undo [N]            Undo the last N moves (default: 1)
  redo [N]            Redo the last N undone moves (default: 1)
  show board          Display the current board
  show history        Display the move history
  show time           Display remaining time (blitz mode)
  show configuration  Display current configuration
  set PARAM=VALUE     Change a configuration parameter

To play a move, type it in algebraic notation: e.g. e2-e4 or e2xe4
""")

    def _print_command_help(self, cmd: str) -> None:
        """Display detailed help for a specific command."""
        help_texts = {
            "new": (
                "new [ARGS]  -  Start a new game. "
                "Args: 'ai white', 'ai black', 'ai-vs-ai'."
            ),
            "quit": (
                "quit  -  Quit the program. You'll be asked to save if needed."
            ),
            "help": "help [CMD]  -  Show help. With CMD: show help for that "
            "command.",
            "load": (
                "load FILE  -  Load a saved game from FILE (.shatranj format)."
            ),
            "save": "save FILE  -  Save the current game to FILE.",
            "hint": "hint  -  Get a move suggestion from the engine.",
            "undo": "undo [N]  -  Undo the last N moves (default 1).",
            "redo": "redo [N]  -  Redo the last N undone moves (default 1).",
            "pause": "pause  -  Pause/resume the blitz timer.",
            "set": (
                "set PARAM=VALUE  -  Change a setting. E.g.: set debug=true"
            )
        }
        if cmd in help_texts:
            print(help_texts[cmd])
        else:
            self._error(f"Unknown command: '{cmd}'")

    def _do_show_board(self) -> None:
        """Display the current state of the board."""
        if self._state is None:
            self._error("No game in progress. Type 'new' to start a game.")
            return
        print()
        print_board(self._state.board)
        print()

    def _do_show_history(self) -> None:
        """
        Display the history of played moves.

        Format (F24 of the specification):
          W e2-e4 B Ng8-f6
          W d2-d4 B Nf6xe4
          ...
        """
        if self._state is None:
            self._error("No game in progress.")
            return

        history = self._state.get_history()
        if not history:
            print(_("No moves played yet."))
            return

        print(_("Move history:"))
        # Group moves in pairs (white, black)
        i = 0
        turn = 1
        while i < len(history):
            line = f"  {turn:3}."

            # White move
            move = history[i]
            from_alg = Board.square_to_algebraic(move.from_square)
            to_alg = Board.square_to_algebraic(move.to_square)
            sep = "x" if move.captured_piece else "-"
            line += f"  W {from_alg}{sep}{to_alg}"
            i += 1

            # Black move (if it exists)
            if i < len(history):
                move = history[i]
                from_alg = Board.square_to_algebraic(move.from_square)
                to_alg = Board.square_to_algebraic(move.to_square)
                sep = "x" if move.captured_piece else "-"
                line += f"  B {from_alg}{sep}{to_alg}"
                i += 1

            print(line)
            turn += 1
        print()

    def _do_show_time(self) -> None:
        """Display remaining time (blitz mode only)."""
        if not self._blitz_enabled:
            print(
                "Time display is only available in blitz mode "
                "(use -b at startup)."
            )
            return

        if self._state is None:
            self._error("No game in progress.")
            return

        status = "paused" if self._timer_paused else (
            f"running ({self._state.current_color} to move)"
        )
        print(f"White: {self._format_clock(self._clock_seconds[WHITE])}")
        print(f"Black: {self._format_clock(self._clock_seconds[BLACK])}")
        print(f"Status: {status}")

    def _do_show_configuration(self) -> None:
        """Display the current configuration."""
        print("\nCurrent configuration:")
        print(f"  verbose = {self._verbose}")
        print(f"  debug   = {self._debug}")
        print()

    def _do_undo(self, args: list[str]) -> None:
        """
        Undo the last move(s).

        In human vs AI mode, undo 2 moves per undo call:
          1. the AI's move
          2. the player's move
        Otherwise undo 1 move (player vs player mode).
        """
        if self._state is None:
            self._error("No game in progress.")
            return

        n = 1
        if args:
            try:
                n = int(args[0])
                if n < 1:
                    self._error("N must be a positive integer.")
                    return
            except ValueError:
                self._error(f"Invalid number: '{args[0]}'")
                return

        # In human vs AI mode, undo in pairs (player + AI)
        human_vs_ai = len(self._ai_players) == 1
        moves_to_undo = n * 2 if human_vs_ai else n

        undone = 0
        for _ in range(moves_to_undo):
            move = self._state.undo()
            if move is None:
                actual = undone // 2 if human_vs_ai else undone
                print(f"Nothing more to undo (undid {actual} move(s)).")
                break
            undone += 1

        if undone > 0:
            actual = undone // 2 if human_vs_ai else undone
            print(f"Undid {actual} move(s).")
            print_board(self._state.board)
            print(f"\nIt's now {self._state.current_color}'s turn.")
            self._saved = False

    def _do_redo(self, args: list[str]) -> None:
        """
        Redo the last undone move(s).

        In human vs AI mode, redo 2 moves per redo call:
          1. the player's move
          2. the AI's move
        Otherwise redo 1 move (player vs player mode).
        """
        if self._state is None:
            self._error("No game in progress.")
            return

        n = 1
        if args:
            try:
                n = int(args[0])
                if n < 1:
                    self._error("N must be a positive integer.")
                    return
            except ValueError:
                self._error(f"Invalid number: '{args[0]}'")
                return

        # In human vs AI mode, redo in pairs (player + AI)
        human_vs_ai = len(self._ai_players) == 1
        moves_to_redo = n * 2 if human_vs_ai else n

        redone = 0
        for _ in range(moves_to_redo):
            move = self._state.redo()
            if move is None:
                actual = redone // 2 if human_vs_ai else redone
                print(f"Nothing more to redo (redid {actual} move(s)).")
                break
            redone += 1

        if redone > 0:
            actual = redone // 2 if human_vs_ai else redone
            print(f"Redid {actual} move(s).")
            print_board(self._state.board)
            print(f"\nIt's now {self._state.current_color}'s turn.")
            self._saved = False

    def _do_hint(self, args: list[str]) -> None:
        """
        Display a move suggestion.

        For now: returns the first legal move found.
        A real AI would use Minimax or MCTS (F31-F35).
        """
        if self._state is None:
            self._error("No game in progress.")
            return

        legal_moves = self._engine.generate_legal_moves(
            self._state.board, self._state.current_color
        )
        if not legal_moves:
            print("No legal moves available.")
            return

        # Take the first legal move (simple, no AI for now)
        suggested = legal_moves[0]
        print(f"Hint: {self._format_move_with_piece(suggested)}")

    def _format_move_with_piece(self, move: Move) -> str:
        """Return a human-readable move: 'pawn e2-e3' or 'rook a1xa8'."""
        piece_name = PIECE_LABELS.get(move.piece_type, move.piece_type.lower())
        from_alg = Board.square_to_algebraic(move.from_square)
        to_alg = Board.square_to_algebraic(move.to_square)
        sep = "x" if move.captured_piece else "-"
        return f"{piece_name} {from_alg}{sep}{to_alg}"

    def _format_ai_details(self, ai_player: object) -> str:
        """Return optional algorithm metadata for an AI player."""
        search = getattr(ai_player, "_search", None)
        if search is None:
            return ""

        algo = type(search).__name__
        depth = getattr(search, "_depth", None)
        scoring = getattr(ai_player, "scoring", None)

        if depth is None:
            return f" (algorithm: {algo})"
        if scoring is None:
            return f" (algorithm: {algo}, depth: {depth})"
        return f" (algorithm: {algo}, depth: {depth}, scoring: {scoring})"

    def _do_load(self, args: list[str]) -> None:
        """
        Load a game from a file.

        Usage: load FILE
        """
        if not args:
            self._error("Usage: load FILE")
            return

        path = args[0]

        try:
            with open(path, "r", encoding="ascii") as f:
                raw = f.read()
        except OSError as err:
            self._error(f"Could not open '{path}': {err}")
            return

        # Remove comments and empty lines
        lines = self._strip_comments(raw)

        try:
            # --- Find sections ---
            idx_settings = lines.index("[settings]")
            idx_game = lines.index("[game]")
            idx_history = lines.index("[history]")

            # --- Read [settings] ---
            for line in lines[idx_settings + 1: idx_game]:
                if "=" in line:
                    key, _, val = line.partition("=")
                    key = key.strip().lower()
                    val = val.strip().lower()
                    if key == "verbose":
                        self._verbose = val in ("true", "1", "yes")
                    elif key == "debug":
                        self._debug = val in ("true", "1", "yes")

            # --- Read [game] ---
            game_lines = lines[idx_game + 1: idx_history]

            # First line = current player color
            color_letter = game_lines[0].strip().upper()
            if color_letter not in ("W", "B"):
                self._error(f"Invalid player color: '{color_letter}'")
                return
            current_color = WHITE if color_letter == "W" else BLACK

            # Next 8 lines = the board (rank 8 at top, rank 1 at bottom)
            board_lines = game_lines[1:9]
            if len(board_lines) != 8:
                self._error("Invalid board format: expected 8 rows")
                return

            # Map piece symbols to (piece_type, color)
            SYMBOL_MAP = {
                "K": (SHAH, WHITE),
                "F": (FERZ, WHITE),
                "R": (ROOK, WHITE),
                "A": (ALFIL, WHITE),
                "N": (KNIGHT, WHITE),
                "P": (PAWN, WHITE),
                "k": (SHAH, BLACK),
                "f": (FERZ, BLACK),
                "r": (ROOK, BLACK),
                "a": (ALFIL, BLACK),
                "n": (KNIGHT, BLACK),
                "p": (PAWN, BLACK),
            }

            new_board = Board(setup=False)

            for rank_idx, board_line in enumerate(board_lines):
                # rank 8 is at top (rank_idx=0) -> rank=7
                # rank 1 is at bottom (rank_idx=7) -> rank=0
                rank = 7 - rank_idx
                symbols = board_line.split()
                if len(symbols) != 8:
                    self._error(f"Invalid board row {rank_idx + 1}: '{
                        board_line}'")
                    return
                for file_idx, symbol in enumerate(symbols):
                    if symbol == "_":
                        continue  # empty square
                    if symbol not in SYMBOL_MAP:
                        self._error(
                            f"Unknown piece symbol: '{symbol}'"
                            f" at row {rank_idx + 1}"
                        )
                        return
                    piece, color = SYMBOL_MAP[symbol]
                    square = rank * 8 + file_idx
                    new_board.place_piece(piece, color, square)

            # --- Read [history] ---
            history_moves = []
            for line in lines[idx_history + 1:]:
                # Format: "W e2-e3 B e7-e6"
                tokens = line.split()
                i = 0
                while i + 1 < len(tokens):
                    color_tok = tokens[i].upper()
                    move_tok = tokens[i + 1]
                    i += 2

                    color = WHITE if color_tok == "W" else BLACK

                    # Parse "e2-e3" or "e2xe3"
                    if len(move_tok) != 5 or move_tok[2] not in ("-", "x"):
                        self._error(f"Invalid move in history: '{move_tok}'")
                        return

                    try:
                        from_sq = Board.algebraic_to_square(move_tok[0:2])
                        to_sq = Board.algebraic_to_square(move_tok[3:5])
                    except ValueError as err:
                        self._error(f"Invalid square in history: {err}")
                        return

                    # Determine if it is a capture
                    captured = None
                    if move_tok[2] == "x":
                        captured = "unknown"

                    # Get piece type from the reconstructed board
                    piece_info = new_board.get_piece_at(from_sq)
                    if piece_info is not None:
                        piece_type = piece_info[0]
                    else:
                        piece_type = PAWN  # fallback

                    history_moves.append(
                        Move(from_sq, to_sq, piece_type, color, captured)
                    )

            # --- Build GameState from loaded data ---
            from shatranj.presentation.cli.game_state import GameState

            new_state = GameState.__new__(GameState)
            new_state.board = new_board
            new_state.current_color = current_color
            new_state._history = [(move, {}) for move in history_moves]
            new_state._redo_stack = []

            self._state = new_state
            self._saved = True
            self._ai_players = {}

            print(f"Game loaded from '{path}'.")
            print_board(self._state.board)
            print(f"\nIt's {self._state.current_color}'s turn.")

        except ValueError as err:
            self._error(f"Error parsing file '{path}': {err}")
        except Exception as err:
            self._error(f"Unexpected error loading '{path}': {err}")

    def _do_save(self, args: list[str]) -> None:
        """
        Save the current game to a file.

        Usage: save FILE
        """
        if self._state is None:
            self._error("No game in progress.")
            return
        if not args:
            self._error("Usage: save FILE")
            return

        path = args[0]
        success = self._save_to_file(path)
        if success:
            self._saved = True

    def _save_to_file(self, path: str) -> bool:
        """
        Save the game to an ASCII text file (F20-F24).

        Returns True if the save succeeded, False otherwise.

        File format::

            [settings]
            verbose=false
            debug=false

            [game]
            W
            R N A F K A N R
            P P P P P P P P
            ...

            [history]
            W e2-e4 B e7-e5
            ...
        """

        # Piece symbols for saving (F23)
        SYMBOLS = {
            (SHAH, WHITE): "K",
            (FERZ, WHITE): "F",
            (ROOK, WHITE): "R",
            (ALFIL, WHITE): "A",
            (KNIGHT, WHITE): "N",
            (PAWN, WHITE): "P",
            (SHAH, BLACK): "k",
            (FERZ, BLACK): "f",
            (ROOK, BLACK): "r",
            (ALFIL, BLACK): "a",
            (KNIGHT, BLACK): "n",
            (PAWN, BLACK): "p",
        }

        try:
            with open(path, "w", encoding="ascii") as f:
                # --- Section [settings] ---
                f.write("[settings]\n")
                f.write(f"verbose={str(self._verbose).lower()}\n")
                f.write(f"debug={str(self._debug).lower()}\n")
                f.write("\n")

                # --- Section [game] ---
                f.write("[game]\n")
                # Current player color
                f.write(f"{self._state.current_color[0].upper()}\n")

                # Board rank by rank (from rank 8 to rank 1, F23)
                for rank in range(7, -1, -1):
                    row = []
                    for file in range(8):
                        sq = rank * 8 + file
                        piece = self._state.board.get_piece_at(sq)
                        if piece is None:
                            row.append("_")
                        else:
                            row.append(SYMBOLS[piece])
                    f.write(" ".join(row) + "\n")
                f.write("\n")

                # --- Section [history] ---
                f.write("[history]\n")
                history = self._state.get_history()
                # Group by pairs (white, black) on the same line (F24)
                i = 0
                while i < len(history):
                    line_parts = []
                    move = history[i]
                    color_letter = "W" if move.color == WHITE else "B"
                    from_alg = Board.square_to_algebraic(move.from_square)
                    to_alg = Board.square_to_algebraic(move.to_square)
                    sep = "x" if move.captured_piece else "-"
                    line_parts.append(
                        f"{color_letter} {from_alg}{sep}{to_alg}"
                    )
                    i += 1

                    if i < len(history):
                        move = history[i]
                        color_letter = "W" if move.color == WHITE else "B"
                        from_alg = Board.square_to_algebraic(move.from_square)
                        to_alg = Board.square_to_algebraic(move.to_square)
                        sep = "x" if move.captured_piece else "-"
                        line_parts.append(
                            f"{color_letter} {from_alg}{sep}{to_alg}"
                        )
                        i += 1

                    f.write(" ".join(line_parts) + "\n")

            print(f"Game saved to '{path}'.")
            return True

        except OSError as err:
            # OSError covers write errors (disk full, permissions, ...)
            self._error(f"Could not save to '{path}': {err}")
            return False

    def _do_pause(self, args: list[str]) -> None:
        """Pause the timer (blitz mode only)."""
        if not self._blitz_enabled:
            print("Pause is only available in blitz mode.")
            return

        if self._state is None:
            self._error("No game in progress.")
            return

        if self._timer_paused:
            self._timer_paused = False
            self._start_turn_timer()
            print("Blitz timer resumed.")
            return

        self._timer_paused = True
        self._turn_started_at = None
        print("Blitz timer paused.")

    def _do_set(self, args: list[str]) -> None:
        """
        Change a configuration parameter.

        Usage: set PARAM=VALUE
        Example: set debug=true
        """
        if not args:
            self._error("Usage: set PARAM=VALUE")
            return

        setting = args[0]
        if "=" not in setting:
            self._error(f"Invalid format: '{setting}'. Expected: PARAM=VALUE")
            return

        param, _, value = setting.partition("=")
        param = param.strip().lower()
        value = value.strip().lower()

        if param == "verbose":
            self._verbose = value in ("true", "1", "yes")
            print(f"verbose = {self._verbose}")
        elif param == "debug":
            self._debug = value in ("true", "1", "yes")
            print(f"debug = {self._debug}")
        else:
            self._error(f"Unknown parameter: '{param}'")

    # ------------------------------------------------------------------
    # Tab completion (F18)
    # ------------------------------------------------------------------

    def _completer(self, text: str, state: int) -> str | None:
        """
        Completion function for readline.

        readline calls this with state=0, 1, 2, ... until None is returned.
        Returns commands that start with `text`.

        Example:
          The user types "sh" then Tab.
          readline calls _completer("sh", 0) -> "show board"
          readline calls _completer("sh", 1) -> "show history"
          readline calls _completer("sh", 2) -> "show time"
          readline calls _completer("sh", 3) -> None  (end)
        """
        options = [c for c in COMMANDS if c.startswith(text)]
        if state < len(options):
            return options[state]
        return None

    # ------------------------------------------------------------------
    # Comment stripping (F21)
    # ------------------------------------------------------------------

    def _strip_comments(self, text: str) -> list[str]:
        """
        Remove comments from a save file and return clean non-empty lines.

        Two comment types (F21):
          - Inline  : from '#' to end of line
          - Block   : from '{' to '}' (may span multiple lines)
        """
        result = []
        i = 0
        current_line: list[str] = []

        while i < len(text):
            ch = text[i]

            # Block comment: skip everything until matching '}'
            if ch == "{":
                i += 1
                while i < len(text) and text[i] != "}":
                    i += 1
                # skip the closing '}'
                i += 1
                continue

            # Inline comment: skip rest of line
            if ch == "#":
                while i < len(text) and text[i] != "\n":
                    i += 1
                continue

            # End of line: flush the current line buffer
            if ch == "\n":
                line = "".join(current_line).strip()
                if line:
                    result.append(line)
                current_line = []
                i += 1
                continue

            current_line.append(ch)
            i += 1

        # Flush last line if file doesn't end with '\n'
        line = "".join(current_line).strip()
        if line:
            result.append(line)

        return result

    # ------------------------------------------------------------------
    # Error display (F10 of the specification)
    # ------------------------------------------------------------------

    def _error(self, message: str) -> None:
        """
        Print an error message to stderr (F1 of the specification).

        The specification requires that error messages go to stderr,
        not stdout.
        """
        print(f"Error: {message}", file=sys.stderr)

    def _debug_print(self, message: str) -> None:
        """Print a debug message only if --debug is active."""
        if self._debug:
            print(f"[DEBUG] {message}", file=sys.stderr)
