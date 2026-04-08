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
from .display import print_board
from shatranj.persistence import (
    ClockState,
    load_game_file,
    save_game_file,
    strip_save_comments,
)
from shatranj.domain.rules.rules_engine import RulesEngine
from shatranj.domain.network.game_client import GameClient
from shatranj.domain.network.discovery_client import DiscoveryClient
from shatranj.domain.network.game_server import GameServer
from shatranj.utils.constants import (
    WHITE,
    BLACK,
    SHAH,
    FERZ,
    ROOK,
    ALFIL,
    KNIGHT,
    PAWN,
)
from shatranj.utils.exceptions import (
    InvalidSquareError,
    LoadError,
    ShatranjError,
)
from shatranj.domain.ai.ai_player import AIPlayer
from shatranj.domain.ai.hinting import choose_hint_move
from shatranj.domain.core.board import Board
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
    "server list",
    "server start",
    "server stop",
    "server status",
    "join",
    "ping",
    "players",
    "scoreboard",
    "accept",
    "decline",
    "cancel",
    "away",
    "back",
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
    """

    def __init__(
        self,
        verbose: bool = False,
        debug: bool = False,
        blitz: bool = False,
        blitz_time_minutes: int = 30,
    ) -> None:
        self._state: GameState | None = None  # No game at startup
        self._engine = RulesEngine()
        self._running = False
        self._saved = True  # Nothing to save at startup
        self._verbose = verbose
        self._ai_players: dict[str, AIPlayer] = {}
        self._debug = debug

        self._blitz_enabled = blitz
        self._blitz_minutes = max(1, blitz_time_minutes)
        self._increment_seconds = 2 if blitz else 0
        self._time_control_name = "No active game"
        self._clock_seconds = {
            WHITE: 0.0,
            BLACK: 0.0,
        }
        self._turn_started_at: float | None = None
        self._timer_paused = False
        self._reset_blitz_clock()

        # Configure readline for Tab completion (F18)
        readline.set_completer(self._completer)
        readline.parse_and_bind("tab: complete")

    def enable_blitz(self, minutes: int) -> None:
        """Enable blitz mode for subsequent CLI games."""
        self._blitz_enabled = True
        self._blitz_minutes = max(1, minutes)
        self._increment_seconds = 2
        self._time_control_name = f"Blitz {self._blitz_minutes} min"
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

    def _do_decline(self, args: list[str]) -> None:
        """F40: Decline an incoming game invitation."""
        if hasattr(self, "_network_client") and self._network_client:
            self._network_client.decline_invite()
            print(_("Invitation declined."))
        else:
            print(_("No active network connection."))

    def _do_cancel(self, args: list[str]) -> None:
        """F40: Cancel a sent invitation that is still pending."""
        if hasattr(self, "_network_client") and self._network_client:
            self._network_client.send("CANCEL")
            print(_("Invitation canceled."))
        else:
            print(_("No active network connection."))

    def _do_away(self, args: list[str]) -> None:
        """F40: Change status to 'away' to block invitations."""
        if hasattr(self, "_network_client") and self._network_client:
            self._network_client.send("AWAY")
            print(_("Status set to AWAY."))
        else:
            print(_("No active network connection."))

    def _do_back(self, args: list[str]) -> None:
        """F40: Return to 'idle' status from 'away'."""
        if hasattr(self, "_network_client") and self._network_client:
            self._network_client.send("BACK")
            print(_("Status set to BACK (idle)."))
        else:
            print(_("No active network connection."))

    def _stop_turn_timer(self) -> None:
        """Stop the active turn timer."""
        self._turn_started_at = None
        self._timer_paused = False

    def _get_display_time(
        self,
        color: str,
        now: float | None = None,
    ) -> float:
        """Return the visible remaining time for one side."""

        remaining = self._clock_seconds.get(color, 0.0)
        if (
            self._blitz_enabled
            and self._state is not None
            and not self._timer_paused
            and self._state.current_color == color
            and self._turn_started_at is not None
        ):
            if now is None:
                now = time.monotonic()
            remaining -= now - self._turn_started_at
        return max(0.0, remaining)

    def _finish_active_turn(self, moving_color: str) -> bool:
        """Commit the elapsed time for the side that just moved."""

        if not self._blitz_enabled or self._turn_started_at is None:
            return True

        remaining = self._get_display_time(moving_color)
        self._turn_started_at = None

        if remaining <= 0:
            winner = BLACK if moving_color == WHITE else WHITE
            self._clock_seconds[moving_color] = 0.0
            print(_("Time out! {winner} wins!").format(winner=winner))
            self._state = None
            self._stop_turn_timer()
            return False

        self._clock_seconds[moving_color] = remaining + self._increment_seconds
        return True

    def _build_clock_state(self) -> ClockState:
        """Return the current timed-game state for persistence."""

        if not self._blitz_enabled or self._state is None:
            return ClockState()

        now = time.monotonic()
        return ClockState(
            mode="timed",
            label=self._time_control_name,
            base_seconds=float(self._blitz_minutes * 60),
            increment_seconds=self._increment_seconds,
            white_seconds=self._get_display_time(WHITE, now),
            black_seconds=self._get_display_time(BLACK, now),
            paused=self._timer_paused,
        )

    def _apply_loaded_clock_state(self, clock_state: ClockState) -> None:
        """Restore clock data from a saved game."""

        self._stop_turn_timer()
        if clock_state.mode != "timed":
            self._blitz_enabled = False
            self._increment_seconds = 0
            self._time_control_name = "No active game"
            self._clock_seconds = {WHITE: 0.0, BLACK: 0.0}
            return

        base_seconds = max(
            clock_state.base_seconds,
            clock_state.white_seconds,
            clock_state.black_seconds,
        )
        self._blitz_enabled = True
        self._blitz_minutes = max(1, int((base_seconds + 59) // 60))
        self._increment_seconds = clock_state.increment_seconds
        self._time_control_name = clock_state.label
        self._clock_seconds = {
            WHITE: clock_state.white_seconds,
            BLACK: clock_state.black_seconds,
        }
        self._timer_paused = clock_state.paused

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
        current = self._state.current_color
        remaining = self._get_display_time(current, now)
        self._clock_seconds[current] = remaining
        self._turn_started_at = now

        if remaining > 0:
            return False

        winner = BLACK if current == WHITE else WHITE
        print(_("Time out! {winner} wins!").format(winner=winner))
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
        """Start the main shell loop."""
        self._running = True
        print(_("Welcome to Shatranj! Type 'help' to see available commands."))
        print(_("Start a new game with 'new'."))
        print()

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
        """Parse the command line and call the corresponding method."""
        if self._consume_turn_time():
            return

        parts = raw.split()
        if not parts:
            return

        cmd = parts[0].lower()
        args = parts[1:]  # Arguments after the command

        # F38 & F39: Server Management
        if cmd == "server":
            sub = args[0].lower() if args else ""
            if sub == "list":
                self._do_server_list()
            elif sub == "start":
                self._do_server_start(args[1:])
            elif sub == "stop":
                self._do_server_stop()
            elif sub == "status":
                self._do_server_status()
            return

        # F38 & F40: Network Actions
        network_handlers = {
            "join": self._do_join,
            "ping": self._do_ping,
            "players": self._do_players,
            "scoreboard": self._do_scoreboard,
            "accept": self._do_accept,
            "decline": self._do_decline,
            "cancel": self._do_cancel,
            "away": self._do_away,
            "back": self._do_back,
        }

        if cmd in network_handlers:
            network_handlers[cmd](args)
            return

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

        # Expected format: "e2-e4" or "e2xe4"
        if self._looks_like_move(raw):
            self._do_play_move(raw)
            return

        self._error(
            f"Unknown command: '{raw}'." "Type 'help' for the list of commands."
        )

    # ------------------------------------------------------------------
    # Check if a string looks like a move (algebraic notation)
    # ------------------------------------------------------------------

    def _looks_like_move(self, text: str) -> bool:
        """Return True if the text looks like a move in algebraic notation."""
        pattern = r"^[A-Za-z]?[a-h][1-8][-x][a-h][1-8]$"
        return bool(re.match(pattern, text.strip()))

    # ------------------------------------------------------------------
    # Parse a move in algebraic notation -> Move object
    # ------------------------------------------------------------------

    def _parse_move(self, text: str) -> Move | None:
        """Convert a string like "e2-e4" into a Move object."""
        text = text.strip()
        if len(text) == 6 and text[0].isupper():
            text = text[1:]

        if len(text) != 5 or text[2] not in ("-", "x"):
            self._error(f"Invalid move format: '{text}'." "Expected format: e2-e4")
            return None

        from_str = text[0:2]
        to_str = text[3:5]

        try:
            from_sq = Board.algebraic_to_square(from_str)
            to_sq = Board.algebraic_to_square(to_str)
        except InvalidSquareError as err:
            self._error(str(err))
            return None

        piece_info = self._state.board.get_piece_at(from_sq)
        if piece_info is None:
            self._error(f"No piece on {from_str}.")
            return None

        piece_type, color = piece_info

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
        """Play a move entered by the user."""
        if self._state is None:
            self._error("No game in progress.")
            return

        if self._consume_turn_time():
            return

        move = self._parse_move(text)
        if move is None:
            return

        # 2. Vérifier la couleur
        if move.color != self._state.current_color:
            self._error(f"It's {self._state.current_color}'s turn, not {move.color}'s.")
            return

        # 3. Sécurité réseau : tour du joueur
        if (
            hasattr(self, "_network_client")
            and self._network_client
            and self._network_client.connected
        ):
            if hasattr(self, "_my_color") and self._my_color:
                if self._state.current_color != self._my_color:
                    self._error(
                        f"Patience ! C'est au tour de {self._state.current_color} de jouer."
                    )
                    return

        # 4. Validation du coup
        legal_moves = self._engine.generate_legal_moves(
            self._state.board, self._state.current_color
        )

        real_move = None
        for valid_move in legal_moves:
            if (
                valid_move.from_square == move.from_square
                and valid_move.to_square == move.to_square
            ):
                real_move = valid_move
                break

        if real_move is None:
            self._error(f"Illegal move: {text}")
            return

        move = real_move

        moving_color = self._state.current_color
        if not self._finish_active_turn(moving_color):
            return

        self._state.apply_move(move)
        self._saved = False

        print(_("You played: {move}").format(move=self._format_move_with_piece(move)))

        if self._verbose:
            from_alg = self._state.board.square_to_algebraic(move.from_square)
            to_alg = self._state.board.square_to_algebraic(move.to_square)
            captured = f" x {move.captured_piece}" if move.captured_piece else ""
            print(f"[verbose] {move.piece_type} " f"{from_alg} -> {to_alg}{captured}")
            print(f"[verbose] history length: " f"{len(self._state.get_history())}")

        print(f"Vous avez joué : {self._format_move_with_piece(move)}")

        print_board(self._state.board)
        print(_("It's now {color}'s turn.").format(color=self._state.current_color))
        if self._check_game_over():
            return

        self._start_turn_timer()
        self._auto_play_ai_turns()

    def _on_message(self, msg) -> None:
        """Background listener for server data."""
        cmd = str(getattr(msg, "command", msg)).upper()
        args = getattr(msg, "args", [])

        # --- F39 : DÉBUT DE PARTIE ---
        if "GAME_START" in cmd:
            new_board = Board(setup=False)
            board_data = ""
            self._my_color = None
            self._blitz_enabled = False

            for arg in args:
                if arg.startswith("board="):
                    board_data = arg.split("=", 1)[1]
                elif arg == "white=You":
                    self._my_color = "WHITE"
                elif arg == "black=You":
                    self._my_color = "BLACK"
                elif "blitz=" in arg.lower():
                    self._blitz_enabled = True
                    try:
                        self._blitz_minutes = int(arg.split("=")[1])
                    except:
                        self._blitz_minutes = 30

            if board_data:
                pieces_list = board_data.split(",")
                for i, char in enumerate(pieces_list):
                    if char != "." and i < 64:
                        p_type, p_color = self._symbol_to_piece(char)
                        real_square = (7 - (i // 8)) * 8 + (i % 8)
                        new_board.place_piece(p_type, p_color, real_square)

            self._state = GameState()
            self._state.board = new_board

            if self._blitz_enabled:
                self._increment_seconds = 2
                self._time_control_name = f"Blitz {self._blitz_minutes} min"
                self._reset_blitz_clock()
                self._start_turn_timer()

            print("\n" + "=" * 30)
            print(" LE MATCH COMMENCE ! ")

            if self._blitz_enabled:
                print(f" (MODE BLITZ : {self._blitz_minutes} minutes)")

            if self._my_color:
                print(f" >>> VOUS JOUEZ LES {self._my_color}S <<<")
                if self._my_color == "BLACK":
                    print(" (Les Blancs commencent. Veuillez patienter...)")
            print("=" * 30)

            self._do_show_board()
            print(f"\n{PROMPT}", end="", flush=True)
            return

        # --- F39 : RÉCEPTION DU COUP DE L'ADVERSAIRE ---
        if "MOVE" in cmd or "OPPONENT_MOVE" in cmd:
            if self._state is not None:
                move_text = args[0]
                move = self._parse_move(move_text)

                if move is not None:
                    if not self._finish_active_turn(self._state.current_color):
                        return

                    self._state.apply_move(move)
                    self._saved = False

                    self._start_turn_timer()

                    print(f"\n[+] L'adversaire a joué : {move_text}")
                    print_board(self._state.board)
                    print(
                        f"\nC'est maintenant au tour des {self._state.current_color}s."
                    )

                    print(f"\n{PROMPT}", end="", flush=True)
            return

        # --- F40 : RÉCEPTION D'INVITATION ---
        if "INVITE_RECV" in cmd or "INVITATION_RECEIVED" in cmd:
            from_user = args[0] if args else "Inconnu"
            print(f"\n[!] INVITATION REÇUE de : {from_user}")
            print(_("Type 'accept' to play or 'decline' to refuse."))
            print(f"\n{PROMPT}", end="", flush=True)
            return

        if "INVITATION_SENT" in cmd:
            print("\n[+] Invitation envoyée ! En attente de l'adversaire...")
            print(f"\n{PROMPT}", end="", flush=True)
            return

        if "DECLINED" in cmd or "INVITE_DECLINED" in cmd:
            print("\n[!] L'adversaire a refusé l'invitation.")
            print(f"\n{PROMPT}", end="", flush=True)
            return

        if "PLAYERS" in cmd:
            print("\n--- JOUEURS EN LIGNE ---")
            for p in args:
                print(f" -> {p}")
            print("----------------------")
            print(f"\n{PROMPT}", end="", flush=True)
            return

        if "ERROR" in cmd:
            msg_text = args[0] if args else "Erreur réseau."
            if any(
                word in msg_text.lower()
                for word in ["quitt", "quit", "left", "aucune", "fantôme"]
            ):
                if self._state is not None:
                    self._state.undo()
                    print_board(self._state.board)
                    print(f"\n[!] SERVEUR: {msg_text}")
                else:
                    print(f"\n[!] SERVEUR: {msg_text}")
                self._state = None
            else:
                print(f"\n[!] SERVEUR: {msg_text}")
            print(f"\n{PROMPT}", end="", flush=True)
            return

    def _symbol_to_piece(self, char: str):
        """Méthode utilitaire pour convertir 'r' en (ROOK, BLACK), etc."""
        color = WHITE if char.isupper() else BLACK
        c = char.lower()
        mapping = {
            "k": SHAH,
            "f": FERZ,
            "r": ROOK,
            "a": ALFIL,
            "n": KNIGHT,
            "p": PAWN,
        }
        return mapping.get(c, PAWN), color

    def _check_game_over(self) -> bool:
        """Check if the game is over after a move.

        Possible outcomes in Shatranj:
          - Checkmate  -> current player is in check with no legal moves
          - Stalemate  -> not in check but no legal moves (opponent wins)
          - Bare King  -> current player has only their Shah left
        """
        try:
            # If the game is already gone, stop right here
            if self._state is None:
                return True

            current = self._state.current_color

            # We keep your mate's debug print here!
            if hasattr(self, "_debug_print"):
                self._debug_print(f"checking game over for {current}")

            if self._engine.is_checkmate(self._state.board, current):
                opponent = BLACK if current == WHITE else WHITE
                print(_("Checkmate! {color} wins!").format(color=opponent))
                self._state = None
                self._stop_turn_timer()
                return True

            if self._engine.is_stalemate(self._state.board, current):
                opponent = BLACK if current == WHITE else WHITE
                print(_("Stalemate! {color} wins!").format(color=opponent))
                self._state = None
                self._stop_turn_timer()
                return True

            if self._engine.is_bare_king(self._state.board, current):
                opponent = BLACK if current == WHITE else WHITE
                print(_("Bare King! {color} wins!").format(color=opponent))
                self._state = None
                self._stop_turn_timer()
                return True

            if self._is_draw_by_threefold_repetition():
                print(_("Draw by threefold repetition."))
                self._state = None
                self._stop_turn_timer()
                return True

            if self._is_draw_by_fifty_move_rule():
                print(_("Draw by fifty-move rule."))
                self._state = None
                self._stop_turn_timer()
                return True

            return False  # Game continues

        except AttributeError:
            # THE SAFETY NET: If the internet deletes the game while we are checking it, just stop safely!
            return True

    def _do_server_list(self) -> None:
        """F38: List servers found via UDP broadcast."""
        discovery = DiscoveryClient()
        servers = discovery.scan()
        if not servers:
            print(_("No servers found."))
        else:
            for s in servers:
                print(f" - {s.name} at {s.ip}:{s.port}")

    def _on_network_message(self, msg):
        """Handles messages from the GameServer."""
        if msg.command == "OPPONENT_MOVE":  # F39
            move = self._parse_move(msg.args[0])
            if move and self._state:
                self._state.board.move_piece(move.from_square, move.to_square)
                print(_("\nOpponent played: {move}").format(move=msg.args[0]))
                print_board(self._state.board)
                print(f"\nIt's now {self._state.current_color}'s turn.")

    def _do_join(self, args: list[str]) -> None:
        address = args[0] if args else "localhost:12345"
        name = input(_("Enter your name: "))
        try:
            self._network_client = GameClient(address, callback=self._on_message)
            if self._network_client.start_connection(player_name=name):
                print(_("Connected! Waiting for server..."))

                # ---> TURN ON THE BACKGROUND CLOCK <---
                import threading

                threading.Thread(target=self._auto_refresh_players, daemon=True).start()

            else:
                self._error(_("Connection failed."))
        except Exception as e:
            self._error(str(e))

    def _auto_refresh_players(self):
        """Timer in the background that asks for the player list every minute."""
        import time

        # Keep looping as long as the game is running and we are connected
        while (
            self._running
            and hasattr(self, "_network_client")
            and getattr(self._network_client, "connected", False)
        ):
            time.sleep(60)  # Wait 60 seconds

    def _do_ping(self, args: list[str]) -> None:
        """F38: Send PING to server."""
        if hasattr(self, "_network_client") and self._network_client:
            self._network_client.ping()
        else:
            self._error(_("Not connected to a server."))

    def _do_players(self, args: list[str]) -> None:
        """F39/F40: Request the list of connected players"""
        if hasattr(self, "_network_client") and self._network_client:
            self._network_client.get_players()
        else:
            print(_("Not connected to a server."))

    def _do_accept(self, args: list[str]) -> None:
        """F40: Accept an incoming game invitation."""
        if hasattr(self, "_network_client") and self._network_client:
            self._network_client.accept_invite()
            print(_("Accepting invitation..."))
        else:
            self._error(_("Not connected to a server."))

    def _is_draw_by_threefold_repetition(self) -> bool:
        """Detect if the current position has occurred 3 times"""
        if self._state is None:
            return False

        target_color = self._state.current_color
        target_signature = tuple(sorted(self._state.board._boards.items()))
        expected_snapshot_size = len(self._state.board._boards)

        repetitions = 1
        color_at_state = target_color

        for _, snapshot_before_move in reversed(self._state._history):
            color_at_state = BLACK if color_at_state == WHITE else WHITE
            if color_at_state != target_color:
                continue

            if len(snapshot_before_move) != expected_snapshot_size:
                continue

            signature = tuple(sorted(snapshot_before_move.items()))
            if signature == target_signature:
                repetitions += 1
                if repetitions >= THREEFOLD_REPETITION_COUNT:
                    return True

        return False

    def _is_draw_by_fifty_move_rule(self) -> bool:
        """Detect the fifty-move rule"""
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
        """Let the AI play whose turn it is."""
        if self._state is None:
            return

        ai_player = self._ai_players.get(self._state.current_color)
        if ai_player is None:
            return

        print(
            _("AI is thinking...{details}").format(
                details=self._format_ai_details(ai_player)
            )
        )

        search = getattr(ai_player, "_search", None)
        self._debug_print(
            f"AI search starting: algo={getattr(ai_player, 'algorithm', '?')}, "
            f"depth={getattr(search, '_depth', '?')}, "
            f"scoring={getattr(ai_player, 'scoring', '?')}, "
            f"color={self._state.current_color}"
        )

        import time as _time

        _t0 = _time.monotonic()
        move = ai_player.choose_move(self._state.board)
        self._debug_print(f"AI search done in {_time.monotonic() - _t0:.3f}s")

        if move is None:
            self._debug_print("AI found no legal move")
            self._check_game_over()
            return

        moving_color = self._state.current_color
        if not self._finish_active_turn(moving_color):
            return

        self._debug_print(f"AI chose: {self._format_move_with_piece(move)}")

        # display the move played by the AI in algebraic notation
        print(_("AI plays: {move}").format(move=self._format_move_with_piece(move)))

        self._state.apply_move(move)
        self._saved = False

        if self._verbose:
            from_alg = self._state.board.square_to_algebraic(move.from_square)
            to_alg = self._state.board.square_to_algebraic(move.to_square)
            captured = f" x {move.captured_piece}" if move.captured_piece else ""
            print(
                f"[verbose] AI: {move.piece_type} " f"{from_alg} -> {to_alg}{captured}"
            )
            print(f"[verbose] history length: " f"{len(self._state.get_history())}")

        # display the updated board
        print_board(self._state.board)
        print(
            "\n" + _("It's now {color}'s turn.").format(color=self._state.current_color)
        )
        # check if the game is over after the AI's move
        if self._check_game_over():
            return

        self._start_turn_timer()

    def _auto_play_ai_turns(self, max_plies: int = AUTO_PLAY_MAX_PLIES) -> None:
        """
        Chain AI turns as long as the current player is controlled by an AI.

        Used for:
          - human vs AI: play one AI move after the human's move
          - AI vs AI: automatically run through the entire game
        """
        plies = 0
        while self._state is not None and self._state.current_color in self._ai_players:
            if plies >= max_plies:
                print(
                    "\n"
                    + _("Draw by move limit ({max_plies} plies).").format(
                        max_plies=max_plies
                    )
                )
                self._state = None
                self._stop_turn_timer()
                return
            self._do_ai_move()
            plies += 1

    def _do_new(self, args: list[str]) -> None:
        """Start a new game."""
        if self._state is not None and not self._saved:
            answer = input(
                _("Current game is not saved. Start a new game anyway? [y/N] ")
            )
            if answer.strip().lower() not in ("y", "yes"):
                print(_("New game cancelled."))
                return

        if (
            hasattr(self, "_network_client")
            and self._network_client
            and self._network_client.connected
            and args
        ):
            if args[0].lower() not in ("ai", "ai-vs-ai"):
                target_id = args[0]

                # ---> NEW: Check if the player typed -b <---
                blitz_arg = ""
                if len(args) > 1 and args[1] == "-b":
                    mins = args[2] if len(args) > 2 else "30"
                    blitz_arg = f" blitz={mins}"  # We attach this to the target ID!

                print(_("Sending network invitation to {target_id}...").format(target_id=target_id))

                # We sneak the blitz argument into the invite message!
                self._network_client.invite_player(target_id + blitz_arg)
                return

        self._state = GameState()
        self._saved = True
        self._ai_players = {}
        self._timer_paused = False

        if self._blitz_enabled:
            self._time_control_name = f"Blitz {self._blitz_minutes} min"
        self._reset_blitz_clock()

        if len(args) >= 1 and args[0].lower() == "ai-vs-ai":
            self._ai_players[WHITE] = AIPlayer(color=WHITE, depth=2)
            self._ai_players[BLACK] = AIPlayer(color=BLACK, depth=2)
            print(_("New game started! AI plays WHITE and BLACK."))

        elif len(args) >= 2 and args[0].lower() == "ai":
            ai_color = args[1].upper()
            algo = args[2].lower() if len(args) >= 3 else "alphabeta"

            if algo not in ("minimax", "alphabeta", "mcts", "iterative"):
                self._error(
                    f"Unknown algorithm: '{algo}'."
                    "Use minimax, "
                    "alphabeta, mcts or iterative."
                )
                return

            if len(args) >= 4:
                try:
                    depth = int(args[3])
                    if depth < 1:
                        self._error("Depth must be a positive integer.")
                        return
                except ValueError:
                    self._error(
                        f"Invalid depth: '{args[3]}'. " "Expected a positive integer."
                    )
                    return
            else:
                if algo == "alphabeta":
                    depth = 3
                elif algo == "mcts":
                    depth = 100
                else:
                    depth = 3

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
                    _(
                        "New game started! You play WHITE, AI plays BLACK "
                        "({algo}, depth={depth}, scoring={scoring})."
                    ).format(algo=algo, depth=depth, scoring=scoring)
                )

            elif ai_color == "WHITE":
                self._ai_players[WHITE] = AIPlayer(
                    color=WHITE,
                    depth=depth,
                    algorithm=algo,
                    scoring=scoring,
                )
                print(
                    _(
                        "New game started! AI plays WHITE "
                        "({algo}, depth={depth}, scoring={scoring}), "
                        "you play BLACK."
                    ).format(algo=algo, depth=depth, scoring=scoring)
                )
            else:
                self._error(f"Unknown color: '{args[1]}'." "Use 'black' or 'white'.")
                return

        else:
            print(_("New game started! White plays first."))

        if self._blitz_enabled:
            print(
                _("Blitz mode enabled: {minutes} minute(s) per player.").format(
                    minutes=self._blitz_minutes
                )
            )

        print()
        print_board(self._state.board)
        print()
        self._start_turn_timer()
        self._auto_play_ai_turns()

    def _do_contest(
        self,
        path: str,
        algo: str = "alphabeta",
        depth: int = 4,
        scoring: str = "advanced",
    ) -> int:
        import os

        with open(os.devnull, "w", encoding="utf-8") as devnull:
            old_stdout = sys.stdout
            sys.stdout = devnull
            self._do_load([path])
            sys.stdout = old_stdout

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
        """Quit the program."""
        if self._state is not None and not self._saved:
            print(_("Save the game before quitting? [y/N]"), end=" ")
            answer = input().strip().lower()

            if answer in ("y", "yes"):
                # Ask for the file path
                path = input(_("Enter file path to save: ")).strip()
                if path:
                    success = self._save_to_file(path)
                    if not success:
                        # Save failed: ask again (F15)
                        answer2 = (
                            input(_("Save failed. Try to save again? [y/N] "))
                            .strip()
                            .lower()
                        )
                        if answer2 in ("y", "yes"):
                            path2 = input(_("Enter file path to save: ")).strip()
                            self._save_to_file(path2)
                else:
                    print(_("No path given, quitting without saving."))

        # ---> FIX: WAIT BEFORE UNPLUGGING <---
        if (
            hasattr(self, "_network_client")
            and self._network_client
            and self._network_client.connected
        ):
            try:
                # 1. Package the official quit message
                from shatranj.domain.network.protocol import Message, Command

                self._network_client.send(Message.build(Command.QUIT))
            except:
                pass

            # 2. Wait a full second so the computer actually sends it!
            import time

            time.sleep(1.0)

            # 3. Pull the plug safely
            try:
                self._network_client.disconnect()
            except:
                pass

        print("Goodbye!")
        self._running = False

    def _do_help(self, args: list[str]) -> None:
        """Display general help or help for a specific command."""
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
                "quit  -  Quit the program. You'll be asked to " "save if needed."
            ),
            "help": "help [CMD]  -  Show help. With CMD: show help for that "
            "command.",
            "load": (
                "load FILE  -  Load a saved game from FILE " "(.shatranj format)."
            ),
            "save": "save FILE  -  Save the current game to FILE.",
            "hint": "hint  -  Get a move suggestion from the engine.",
            "undo": "undo [N]  -  Undo the last N moves (default 1).",
            "redo": "redo [N]  -  Redo the last N undone moves (default 1).",
            "pause": "pause  -  Pause/resume the blitz timer.",
            "set": ("set PARAM=VALUE  -  Change a setting. E.g.:" " set debug=true"),
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
        """Display the history of played moves."""
        if self._state is None:
            self._error("No game in progress.")
            return

        history = self._state.get_history()
        if not history:
            print(_("No moves played yet."))
            return

        print(_("Move history:"))
        i = 0
        turn = 1
        while i < len(history):
            line = f"  {turn:3}."

            move = history[i]
            from_alg = Board.square_to_algebraic(move.from_square)
            to_alg = Board.square_to_algebraic(move.to_square)
            sep = "x" if move.captured_piece else "-"
            line += f"  W {from_alg}{sep}{to_alg}"
            i += 1

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
                _(
                    "Time display is only available in blitz mode "
                    "(use -b at startup)."
                )
            )
            return

        if self._state is None:
            self._error(_("No game in progress."))
            return

        now = time.monotonic()
        status = (
            _("paused")
            if self._timer_paused
            else (
                _("running ({color} to move)").format(color=self._state.current_color)
            )
        )
        print(
            _("White: {time}").format(
                time=self._format_clock(self._get_display_time(WHITE, now))
            )
        )
        print(
            _("Black: {time}").format(
                time=self._format_clock(self._get_display_time(BLACK, now))
            )
        )
        print(_("Status: {status}").format(status=status))

    def _do_show_configuration(self) -> None:
        """Display the current configuration."""
        print("\n" + _("Current configuration:"))
        print(f"  verbose = {self._verbose}")
        print(f"  debug   = {self._debug}")
        print()

    def _do_undo(self, args: list[str]) -> None:
        """Undo the last move(s)."""
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

        human_vs_ai = len(self._ai_players) == 1
        moves_to_undo = n * 2 if human_vs_ai else n

        undone = 0
        for _move_index in range(moves_to_undo):
            move = self._state.undo()
            if move is None:
                actual = undone // 2 if human_vs_ai else undone
                print(_("Nothing more to undo (undid {n} move(s)).").format(n=actual))
                break
            undone += 1

        if undone > 0:
            actual = undone // 2 if human_vs_ai else undone
            print(_("Undid {n} move(s).").format(n=actual))
            print_board(self._state.board)
            print(
                "\n"
                + _("It's now {color}'s turn.").format(color=self._state.current_color)
            )
            self._saved = False

    def _do_redo(self, args: list[str]) -> None:
        """Redo the last undone move(s)."""
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

        human_vs_ai = len(self._ai_players) == 1
        moves_to_redo = n * 2 if human_vs_ai else n

        redone = 0
        for _move_index in range(moves_to_redo):
            move = self._state.redo()
            if move is None:
                actual = redone // 2 if human_vs_ai else redone
                print(_("Nothing more to redo (redid {n} move(s)).").format(n=actual))
                break
            redone += 1

        if redone > 0:
            actual = redone // 2 if human_vs_ai else redone
            print(_("Redid {n} move(s).").format(n=actual))
            print_board(self._state.board)
            print(
                "\n"
                + _("It's now {color}'s turn.").format(color=self._state.current_color)
            )
            self._saved = False

    def _do_hint(self, args: list[str]) -> None:
        """
        Display an AI-generated move suggestion.
        """
        if self._state is None:
            self._error("No game in progress.")
            return

        suggested = choose_hint_move(
            self._state.board,
            self._state.current_color,
            self._ai_players,
        )
        if suggested is None:
            print(_("No legal moves available."))
            return

        print(_("Hint: {move}").format(move=self._format_move_with_piece(suggested)))

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
        """Load a game from a file."""
        if not args:
            self._error("Usage: load FILE")
            return

        path = args[0]

        try:
            loaded = load_game_file(path)
            self._state = loaded.state
            self._saved = True
            self._verbose = loaded.verbose
            self._debug = loaded.debug
            self._ai_players = loaded.ai_players
            self._apply_loaded_clock_state(loaded.clock)
            if (
                self._state is not None
                and self._blitz_enabled
                and not self._timer_paused
            ):
                self._start_turn_timer()

            print(_("Game loaded from '{path}'.").format(path=path))
            print_board(self._state.board)
            print(
                "\n" + _("It's {color}'s turn.").format(color=self._state.current_color)
            )

        except LoadError as err:
            self._error(str(err))
        except ShatranjError as err:
            self._error(f"Unexpected error loading '{path}': {err}")
        except Exception as err:
            self._error(f"Unexpected error loading '{path}': {err}")

    def _do_scoreboard(self, args: list[str]) -> None:
        """F39: Show the win/loss records of players."""
        print(_("Scoreboard feature not yet implemented!"))

    def _do_save(self, args: list[str]) -> None:
        """Save the current game to a file."""
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
        """Save the game to an ASCII text file (F20-F24)."""
        try:
            save_game_file(
                path,
                state=self._state,
                verbose=self._verbose,
                debug=self._debug,
                clock=self._build_clock_state(),
                ai_players=self._ai_players,
            )
            print(_("Game saved to '{path}'.").format(path=path))
            return True

        except ShatranjError as err:
            self._error(str(err))
            return False

    def _do_pause(self, args: list[str]) -> None:
        """Pause the timer (blitz mode only)."""
        if not self._blitz_enabled:
            print(_("Pause is only available in blitz mode."))
            return

        if self._state is None:
            self._error(_("No game in progress."))
            return

        if self._timer_paused:
            self._timer_paused = False
            self._start_turn_timer()
            print(_("Blitz timer resumed."))
            return

        self._timer_paused = True
        self._turn_started_at = None
        print(_("Blitz timer paused."))

    def _do_set(self, args: list[str]) -> None:
        """Change a configuration parameter."""
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
        """Completion function for readline."""
        options = [c for c in COMMANDS if c.startswith(text)]
        if state < len(options):
            return options[state]
        return None

    # ------------------------------------------------------------------
    # Comment stripping (F21)
    # ------------------------------------------------------------------

    def _strip_comments(self, text: str) -> list[str]:
        """Remove comments from a save file and return clean non-empty lines."""
        return strip_save_comments(text)

    # ------------------------------------------------------------------
    # Error display (F10 of the specification)
    # ------------------------------------------------------------------

    def _error(self, message: str) -> None:
        """Print an error message to stderr (F1 of the specification)."""
        print(f"Error: {message}", file=sys.stderr)

    def _debug_print(self, message: str) -> None:
        """Print a debug message only if --debug is active."""
        if self._debug:
            print(f"[DEBUG] {message}", file=sys.stderr)


if __name__ == "__main__":
    # 1. Create the interface object (F14)
    shell = CLI()

    # 2. Start the interactive loop (F14)
    shell.run()
