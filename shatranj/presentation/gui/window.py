"""

window.py - Main application window

Role: builds the main window with a welcome screen, menu bar, board widget,

      and right panel. Handles all game logic callbacks.

"""

import builtins
import os

import gi

gi.require_version("Gtk", "4.0")

import threading  # noqa: E402
import time  # noqa: E402

from gi.repository import Gdk, Gio, GLib, Gtk  # noqa: E402

from shatranj.domain.ai.ai_player import AIPlayer  # noqa: E402
from shatranj.domain.ai.hinting import choose_hint_move  # noqa: E402
from shatranj.domain.core.board import Board  # noqa: E402
from shatranj.domain.core.move import Move  # noqa: E402
from shatranj.domain.network.game_client import GameClient  # noqa: E402
from shatranj.persistence import (
    ClockState,
    load_game_file,
    save_game_file,
)  # noqa: E402
from shatranj.domain.rules.rules_engine import RulesEngine  # noqa: E402
from shatranj.presentation.cli.game_state import GameState  # noqa: E402
from shatranj.presentation.gui.board_widget import (  # noqa: E402
    BoardWidget,
    get_piece_asset_path,
)
from shatranj.utils.constants import (  # noqa: E402
    ALFIL,
    BLACK,
    FERZ,
    KNIGHT,  # noqa: E402
    PAWN,
    ROOK,
    SHAH,
    WHITE,
)
from shatranj.utils.exceptions import (  # noqa: E402
    InvalidSquareError,
    LoadError,
    ShatranjError,
)

_ = builtins.__dict__.get("_", lambda x: x)

PLAYER_MODE_OPTIONS = (
    ("Human vs Human", "hvh"),
    ("Human vs AI", "hvai"),
    ("AI vs AI", "aivai"),
)

ALGORITHM_OPTIONS = (
    ("Alpha-Beta", "alphabeta"),
    ("Minimax", "minimax"),
    ("MCTS", "mcts"),
    ("Iterative Deepening", "iterative"),
)

TIME_CONTROL_GROUPS = {
    "bullet": {
        "label": "Bullet",
        "presets": (
            {
                "label": "1 min",
                "base_seconds": 60,
                "increment_seconds": 0,
            },
            {
                "label": "1 | 1",
                "base_seconds": 60,
                "increment_seconds": 1,
            },
            {
                "label": "2 | 1",
                "base_seconds": 120,
                "increment_seconds": 1,
            },
        ),
    },
    "blitz": {
        "label": "Blitz",
        "presets": (
            {
                "label": "3 min",
                "base_seconds": 180,
                "increment_seconds": 0,
            },
            {
                "label": "3 | 2",
                "base_seconds": 180,
                "increment_seconds": 2,
            },
            {
                "label": "5 min",
                "base_seconds": 300,
                "increment_seconds": 0,
            },
        ),
    },
    "rapid": {
        "label": "Rapid",
        "presets": (
            {
                "label": "10 min",
                "base_seconds": 600,
                "increment_seconds": 0,
            },
            {
                "label": "15 | 10",
                "base_seconds": 900,
                "increment_seconds": 10,
            },
            {
                "label": "30 min",
                "base_seconds": 1800,
                "increment_seconds": 0,
            },
        ),
    },
    "custom": {
        "label": "Custom",
        "presets": (),
    },
}

TIME_CONTROL_ORDER = ("bullet", "blitz", "rapid", "custom")

WINDOW_SHORTCUTS = {
    "win.quit": ["<Ctrl>q"],
    "win.new-game": ["<Ctrl>n"],
    "win.load-game": ["<Ctrl>l"],
    "win.save-game": ["<Ctrl>s"],
    "win.configuration": ["<Ctrl>comma"],
    "win.info": ["<Ctrl>i"],
    "win.help": ["F1"],
    "win.undo": ["<Ctrl>u"],
    "win.redo": ["<Ctrl>r"],
    "win.pause": ["<Ctrl>p"],
    "win.hint": ["<Ctrl>h"],
}

MODE_HINTS = {
    "hvh": "Two human players on the same board.",
    "hvai": "Human plays White. AI plays Black.",
    "aivai": "Both sides are controlled by the selected AI algorithm.",
}

PIECE_LABELS = {
    SHAH: "Shah",
    FERZ: "Ferz",
    ROOK: "Rook",
    ALFIL: "Alfil",
    KNIGHT: "Knight",
    PAWN: "Pawn",
}
CAPTURE_DISPLAY_ORDER = (ROOK, KNIGHT, ALFIL, FERZ, PAWN)
STARTING_PIECE_COUNTS = {
    FERZ: 1,
    ROOK: 2,
    ALFIL: 2,
    KNIGHT: 2,
    PAWN: 8,
}

CLOCK_CSS = """
.welcome-root,
.game-root {
  padding: 18px;
  background-image: linear-gradient(
    180deg,
    rgba(245, 237, 221, 0.92),
    rgba(229, 214, 188, 0.88)
  );
}

.welcome-board-frame {
  padding: 18px;
  border-radius: 30px;
  border: 1px solid rgba(86, 58, 31, 0.20);
  background-image: linear-gradient(
    180deg,
    rgba(255, 249, 239, 0.98),
    rgba(240, 226, 199, 0.94)
  );
  box-shadow: 0 20px 44px rgba(58, 37, 20, 0.10);
}

.welcome-sidebar {
  min-width: 250px;
  padding: 18px;
  border-radius: 28px;
  border: 1px solid rgba(86, 58, 31, 0.18);
  background-image: linear-gradient(
    180deg,
    rgba(255, 252, 246, 0.98),
    rgba(243, 231, 209, 0.95)
  );
}

.welcome-kicker {
  font-size: 11px;
  font-weight: 900;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: #7b5a33;
}

.welcome-title {
  font-size: 34px;
  font-weight: 900;
  letter-spacing: 0.03em;
  color: #2f1c10;
}

.welcome-subtitle {
  font-size: 14px;
  line-height: 1.4;
  color: rgba(47, 28, 16, 0.78);
}

.welcome-meta {
  font-size: 12px;
  font-weight: 700;
  color: #705332;
}

.captured-strip {
  min-height: 24px;
}

.welcome-action {
  min-height: 46px;
}

.clock-panel {
  padding: 12px;
  border-radius: 20px;
  border: 1px solid rgba(108, 76, 43, 0.18);
  background-image: linear-gradient(
    180deg,
    rgba(251, 247, 237, 0.96),
    rgba(238, 228, 207, 0.92)
  );
}

.clock-title {
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #6d5436;
}

.time-control-pill {
  padding: 6px 10px;
  border-radius: 999px;
  background-color: rgba(108, 76, 43, 0.10);
  color: #5d4428;
  font-size: 12px;
  font-weight: 700;
}

.clock-card {
  padding: 12px 14px;
  border-radius: 18px;
  border: 1px solid rgba(60, 39, 24, 0.18);
}

.clock-card-white {
  background-image: linear-gradient(
    180deg,
    #fffdf8 0%,
    #f5e6c7 58%,
    #e9d2a7 100%
  );
}

.clock-card-black {
  background-image: linear-gradient(
    180deg,
    #3b3028 0%,
    #201813 62%,
    #120d0b 100%
  );
}

.clock-card-active {
  border: 2px solid #c7963e;
}

.clock-card-critical {
  border-color: #b54033;
}

.clock-side {
  font-size: 11px;
  font-weight: 900;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}

.clock-card-white .clock-side,
.clock-card-white .clock-time {
  color: #2e1f13;
}

.clock-card-white .clock-status {
  color: rgba(46, 31, 19, 0.72);
}

.clock-card-black .clock-side,
.clock-card-black .clock-time {
  color: #f7ead4;
}

.clock-card-black .clock-status {
  color: rgba(247, 234, 212, 0.75);
}

.clock-time {
  margin-top: 4px;
  font-family: Monospace;
  font-size: 30px;
  font-weight: 900;
  letter-spacing: 1px;
}

.clock-status {
  margin-top: 3px;
  font-size: 12px;
  font-weight: 600;
}

.clock-time-critical {
  color: #ad2f22;
}

.clock-card-black .clock-time-critical {
  color: #ff8d78;
}

.config-dialog-body {
  padding: 20px;
  background-image: linear-gradient(
    180deg,
    rgba(249, 243, 231, 0.98),
    rgba(235, 223, 196, 0.96)
  );
}

.config-hero {
  padding: 16px 18px;
  border-radius: 24px;
  border: 1px solid rgba(86, 58, 31, 0.18);
  background-image: linear-gradient(
    180deg,
    rgba(255, 251, 244, 0.98),
    rgba(243, 231, 209, 0.94)
  );
  box-shadow: 0 16px 34px rgba(58, 37, 20, 0.08);
}

.config-kicker {
  font-size: 11px;
  font-weight: 900;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: #7b5a33;
}

.config-title {
  font-size: 28px;
  font-weight: 900;
  color: #2f1c10;
}

.config-subtitle {
  font-size: 13px;
  line-height: 1.45;
  color: rgba(47, 28, 16, 0.76);
}

.config-card {
  padding: 14px 16px;
  border-radius: 22px;
  border: 1px solid rgba(86, 58, 31, 0.16);
  background-image: linear-gradient(
    180deg,
    rgba(255, 252, 246, 0.98),
    rgba(244, 233, 212, 0.94)
  );
}

.config-section-title {
  font-size: 11px;
  font-weight: 900;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: #7b5a33;
}

.config-section-description {
  font-size: 12px;
  line-height: 1.4;
  color: rgba(70, 51, 32, 0.72);
}

.config-subsection-title {
  font-size: 12px;
  font-weight: 800;
  color: #5f472b;
}

.config-note {
  font-size: 12px;
  line-height: 1.35;
  color: rgba(70, 51, 32, 0.64);
}

.config-choice-row {
  margin-top: 2px;
}

.config-choice {
  min-height: 38px;
  padding: 6px 10px;
  border-radius: 14px;
  background-color: rgba(255, 255, 255, 0.44);
}

.config-input {
  min-height: 42px;
}

.config-field-label {
  font-size: 12px;
  font-weight: 700;
  color: #5f472b;
}

.config-summary {
  padding: 10px 12px;
  border-radius: 16px;
  border: 1px solid rgba(108, 76, 43, 0.16);
  background-color: rgba(108, 76, 43, 0.10);
  color: #5d4428;
  font-size: 12px;
  font-weight: 700;
}

.config-action {
  min-height: 46px;
  min-width: 132px;
  padding: 0 20px;
  border-radius: 999px;
  border: 1px solid rgba(86, 58, 31, 0.18);
  box-shadow: 0 10px 22px rgba(58, 37, 20, 0.08);
  font-weight: 800;
}

.config-action > label {
  letter-spacing: 0.04em;
}

.dialog-secondary-action {
  background-image: linear-gradient(
    180deg,
    rgba(255, 255, 255, 0.96),
    rgba(241, 233, 217, 0.92)
  );
  color: #5c4428;
}

.dialog-secondary-action:hover {
  background-image: linear-gradient(
    180deg,
    rgba(255, 255, 255, 1.0),
    rgba(245, 237, 224, 0.96)
  );
}

.dialog-primary-action {
  background-image: linear-gradient(
    180deg,
    #6d4927 0%,
    #4c2f18 100%
  );
  color: #f9edd9;
  border-color: rgba(52, 31, 16, 0.48);
  box-shadow: 0 14px 28px rgba(76, 47, 24, 0.22);
}

.dialog-primary-action:hover {
  background-image: linear-gradient(
    180deg,
    #7b542f 0%,
    #56341a 100%
  );
}

.dialog-primary-action:disabled {
  background-image: linear-gradient(
    180deg,
    rgba(122, 95, 68, 0.85),
    rgba(92, 67, 45, 0.82)
  );
  color: rgba(249, 237, 217, 0.72);
  box-shadow: none;
}
"""


def _format_clock(seconds: float, show_tenths: bool = False) -> str:
    """Format a number of seconds as MM:SS."""

    remaining = max(0.0, seconds)
    if show_tenths and remaining < 20:
        whole_seconds = int(remaining)
        tenths = int((remaining - whole_seconds) * 10)
        minutes, seconds = divmod(whole_seconds, 60)
        return f"{minutes:02d}:{seconds:02d}.{tenths}"

    rounded = max(0, int(remaining + 0.999))
    minutes, seconds = divmod(rounded, 60)
    return f"{minutes:02d}:{seconds:02d}"


def _display_color(color: str | None) -> str:
    """Return a user-facing color label."""

    if color == WHITE:
        return "White"
    if color == BLACK:
        return "Black"
    return "--"


def _move_to_network_text(move: Move) -> str:
    """Serialize a GUI move using the network protocol notation."""

    frm = Board.square_to_algebraic(move.from_square)
    to = Board.square_to_algebraic(move.to_square)
    separator = "x" if move.captured_piece else "-"
    return f"{frm}{separator}{to}"


def _move_from_network_text(board: Board, text: str) -> Move | None:
    """Build a move object from a network move string and the live board."""

    raw = text.strip().lower()
    separator = "x" if "x" in raw else "-"
    parts = raw.split(separator)
    if len(parts) != 2:
        return None

    try:
        from_square = Board.algebraic_to_square(parts[0])
        to_square = Board.algebraic_to_square(parts[1])
    except InvalidSquareError:
        return None

    piece_info = board.get_piece_at(from_square)
    if piece_info is None:
        return None

    target = board.get_piece_at(to_square)
    piece_type, color = piece_info
    captured_piece = target[0] if target is not None else None
    return Move(
        from_square=from_square,
        to_square=to_square,
        piece_type=piece_type,
        color=color,
        captured_piece=captured_piece,
    )


def _build_network_invite_target(
    target_id: str,
    blitz_minutes: int | None = None,
) -> str:
    """Build the payload expected by the TCP invite command."""

    payload = target_id.strip()
    if not payload:
        return ""
    if blitz_minutes is None:
        return payload
    return f"{payload} blitz={max(1, int(blitz_minutes))}"


def _build_network_clock_config(blitz_minutes: int | None) -> dict | None:
    """Return a GUI clock config for online blitz games."""

    if blitz_minutes is None:
        return None
    minutes = max(1, int(blitz_minutes))
    return {
        "mode": "hvh",
        "ai_color": BLACK,
        "algorithm": "alphabeta",
        "speed_label": "Custom",
        "time_control_label": f"{minutes} min",
        "base_seconds": minutes * 60,
        "increment_seconds": 2,
    }


def _parse_network_game_start(args: list[str]) -> dict[str, object]:
    """Extract board state, local color, and blitz settings from a message."""

    board = Board()
    my_color = None
    blitz_minutes = None

    for arg in args:
        if arg.startswith("board="):
            board = Board.from_fen(arg.split("=", 1)[1])
        elif arg == "white=You":
            my_color = WHITE
        elif arg == "black=You":
            my_color = BLACK
        elif arg.lower().startswith("blitz="):
            try:
                blitz_minutes = max(1, int(arg.split("=", 1)[1]))
            except ValueError:
                blitz_minutes = 30

    return {
        "board": board,
        "my_color": my_color,
        "blitz_minutes": blitz_minutes,
    }


def _format_network_players(args: list[str]) -> str:
    """Format the server's PLAYERS list into a readable multiline string."""

    if not args:
        return "No players reported by the server."

    lines = []
    for entry in args:
        parts = entry.split(":", 2)
        if len(parts) == 3:
            player_id, name, status = parts
            lines.append(f"{player_id} | {name} | {status}")
        else:
            lines.append(entry)
    return "\n".join(lines)


def _can_interact_with_board(
    state: GameState | None,
    *,
    game_paused: bool,
    ai_players: dict[str, AIPlayer],
    network_player_color: str | None = None,
) -> bool:
    """Return whether the local user is allowed to move pieces now."""

    if state is None or game_paused:
        return False
    if state.current_color in ai_players:
        return False
    if network_player_color is not None and state.current_color != network_player_color:
        return False
    return True


def _should_flip_board(network_player_color: str | None) -> bool:
    """Show black at the bottom only for the online black player."""

    return network_player_color == BLACK


def _display_side_order(
    network_player_color: str | None,
) -> tuple[str, str]:
    """Return which side colors are shown at the top and bottom."""

    if _should_flip_board(network_player_color):
        return WHITE, BLACK
    return BLACK, WHITE


def _captured_piece_colors_for_display(
    network_player_color: str | None,
) -> tuple[str, str]:
    """Return captured-piece colors shown above and below the board."""

    top_side, bottom_side = _display_side_order(network_player_color)
    top_captured_color = WHITE if top_side == BLACK else BLACK
    bottom_captured_color = WHITE if bottom_side == BLACK else BLACK
    return top_captured_color, bottom_captured_color


def _sort_captured_piece_types(piece_types: list[str]) -> list[str]:
    """Keep captured pieces in a stable visual order."""
    counts = {piece: 0 for piece in CAPTURE_DISPLAY_ORDER}
    for piece in piece_types:
        if piece in counts:
            counts[piece] += 1

    ordered = []
    for piece in CAPTURE_DISPLAY_ORDER:
        ordered.extend([piece] * counts[piece])
    return ordered


def _captured_pieces_from_history(history) -> dict[str, list[str]] | None:
    """Derive captured pieces from move history when details are available."""
    captured = {
        WHITE: [],
        BLACK: [],
    }
    for move in history:
        if not move.captured_piece:
            continue
        if move.captured_piece not in STARTING_PIECE_COUNTS:
            return None

        captured_color = BLACK if move.color == WHITE else WHITE
        captured[captured_color].append(move.captured_piece)

    return {
        color: _sort_captured_piece_types(captured[color]) for color in (WHITE, BLACK)
    }


def _captured_pieces_from_board(board) -> dict[str, list[str]]:
    """Fallback capture view for legacy saves without capture detail."""
    remaining = {
        WHITE: {piece: 0 for piece in STARTING_PIECE_COUNTS},
        BLACK: {piece: 0 for piece in STARTING_PIECE_COUNTS},
    }
    for square in range(64):
        piece_info = board.get_piece_at(square)
        if piece_info is None:
            continue

        piece, color = piece_info
        if piece in STARTING_PIECE_COUNTS:
            remaining[color][piece] += 1

    captured = {
        WHITE: [],
        BLACK: [],
    }
    for color in (WHITE, BLACK):
        for piece in CAPTURE_DISPLAY_ORDER:
            missing = STARTING_PIECE_COUNTS[piece] - remaining[color][piece]
            captured[color].extend([piece] * max(0, missing))
    return captured


def _captured_pieces_for_display(
    state: GameState | None,
) -> dict[str, list[str]]:
    """Return captured pieces indexed by the color that was captured."""
    if state is None:
        return {WHITE: [], BLACK: []}

    from_history = _captured_pieces_from_history(state.get_history())
    if from_history is not None:
        return from_history
    return _captured_pieces_from_board(state.board)


class NewGameDialog(Gtk.Dialog):
    """Dialog for choosing the player mode and time control."""

    def __init__(self, parent) -> None:

        super().__init__(title=_("New Game"), transient_for=parent, modal=True)

        self.set_default_size(520, 560)
        self.set_resizable(True)

        self.add_button(_("Back"), Gtk.ResponseType.CANCEL)
        self.add_button(_("Start Match"), Gtk.ResponseType.OK)
        self.set_default_response(Gtk.ResponseType.OK)

        self._cancel_button = self.get_widget_for_response(Gtk.ResponseType.CANCEL)
        self._start_button = self.get_widget_for_response(Gtk.ResponseType.OK)
        if self._cancel_button is not None:
            self._cancel_button.add_css_class("config-action")
            self._cancel_button.add_css_class("dialog-secondary-action")
        self._start_button.add_css_class("config-action")
        self._start_button.add_css_class("dialog-primary-action")
        self._start_button.set_sensitive(False)

        self._selected_mode = "hvh"
        self._selected_algorithm = "alphabeta"
        self._selected_speed: str | None = None
        self._selected_preset: dict | None = None
        self._custom_minutes_spin: Gtk.SpinButton | None = None
        self._custom_increment_spin: Gtk.SpinButton | None = None

        content_area = self.get_content_area()
        content_area.set_spacing(0)
        content_area.set_margin_top(0)
        content_area.set_margin_bottom(0)
        content_area.set_margin_start(0)
        content_area.set_margin_end(0)

        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        scroll.set_hexpand(True)
        content_area.append(scroll)

        box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=14,
        )
        box.add_css_class("config-dialog-body")
        box.set_margin_top(16)
        box.set_margin_bottom(16)
        box.set_margin_start(16)
        box.set_margin_end(16)
        scroll.set_child(box)

        hero = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=6,
        )
        hero.add_css_class("config-hero")

        kicker = Gtk.Label(label="MATCH SETTINGS")
        kicker.set_halign(Gtk.Align.START)
        kicker.set_xalign(0.0)
        kicker.add_css_class("config-kicker")
        hero.append(kicker)

        title = Gtk.Label(label="Shape the next duel")
        title.set_halign(Gtk.Align.START)
        title.set_xalign(0.0)
        title.add_css_class("config-title")
        hero.append(title)

        subtitle = Gtk.Label(
            label=(
                "Pick the players, tune the engine, and lock in a time "
                "control before the first move."
            )
        )
        subtitle.set_halign(Gtk.Align.START)
        subtitle.set_xalign(0.0)
        subtitle.set_wrap(True)
        subtitle.add_css_class("config-subtitle")
        hero.append(subtitle)

        box.append(hero)

        mode_section = self._create_section(
            "Game Mode",
            "Choose who commands each army.",
        )

        mode_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=8,
        )
        group_button = None
        default_mode_button = None
        for label, mode in PLAYER_MODE_OPTIONS:
            button = Gtk.CheckButton(label=label)
            button.set_halign(Gtk.Align.START)
            button.add_css_class("config-choice")
            if group_button is not None:
                button.set_group(group_button)
            else:
                group_button = button
            button.connect("toggled", self._on_mode_changed, mode)
            mode_box.append(button)
            if mode == "hvh":
                default_mode_button = button
        mode_section.append(mode_box)

        self._mode_hint = Gtk.Label(label=MODE_HINTS[self._selected_mode])
        self._mode_hint.set_halign(Gtk.Align.START)
        self._mode_hint.set_xalign(0.0)
        self._mode_hint.set_wrap(True)
        self._mode_hint.add_css_class("config-note")
        mode_section.append(self._mode_hint)
        box.append(mode_section)

        self._algorithm_section = self._create_section(
            "AI Algorithm",
            "Used whenever at least one side is controlled by the engine.",
        )

        self._algorithm_combo = Gtk.DropDown.new_from_strings(
            [label for label, _ in ALGORITHM_OPTIONS]
        )
        self._algorithm_combo.add_css_class("config-input")
        self._algorithm_combo.set_selected(0)
        self._algorithm_combo.connect(
            "notify::selected",
            self._on_algorithm_changed,
        )
        self._algorithm_section.append(self._algorithm_combo)

        algorithm_hint = Gtk.Label(
            label=(
                "Alpha-Beta is balanced, Minimax is classic, "
                "MCTS is more exploratory."
            )
        )
        algorithm_hint.set_halign(Gtk.Align.START)
        algorithm_hint.set_xalign(0.0)
        algorithm_hint.set_wrap(True)
        algorithm_hint.add_css_class("config-note")
        self._algorithm_section.append(algorithm_hint)
        box.append(self._algorithm_section)

        if default_mode_button is not None:
            default_mode_button.set_active(True)

        time_section = self._create_section(
            "Time Control",
            "Select a tempo, then a preset that fits the pace you want.",
        )

        time_mode_label = Gtk.Label(label="Game Speed")
        time_mode_label.set_halign(Gtk.Align.START)
        time_mode_label.set_xalign(0.0)
        time_mode_label.add_css_class("config-subsection-title")
        time_section.append(time_mode_label)

        self._time_mode_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=8,
        )
        speed_group = None
        speed_buttons = []
        for speed_key in TIME_CONTROL_ORDER:
            label = TIME_CONTROL_GROUPS[speed_key]["label"]
            button = Gtk.CheckButton(label=label)
            button.add_css_class("config-choice")
            if speed_group is not None:
                button.set_group(speed_group)
            else:
                speed_group = button
            button.connect("toggled", self._on_speed_changed, speed_key)
            speed_buttons.append(button)
        self._append_choice_rows(self._time_mode_box, speed_buttons, columns=2)
        time_section.append(self._time_mode_box)

        preset_label = Gtk.Label(label="Presets")
        preset_label.set_halign(Gtk.Align.START)
        preset_label.set_xalign(0.0)
        preset_label.add_css_class("config-subsection-title")
        time_section.append(preset_label)

        self._preset_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=8,
        )
        time_section.append(self._preset_box)

        self._time_summary = Gtk.Label(label="Choose a speed to unlock its presets.")
        self._time_summary.set_halign(Gtk.Align.START)
        self._time_summary.set_xalign(0.0)
        self._time_summary.set_wrap(True)
        self._time_summary.add_css_class("config-summary")
        time_section.append(self._time_summary)

        box.append(time_section)

        self._update_ai_options_visibility()

    def _create_section(
        self,
        title: str,
        description: str | None = None,
    ) -> Gtk.Box:
        """Return a styled vertical section container."""

        section = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=10,
        )
        section.add_css_class("config-card")

        title_label = Gtk.Label(label=title)
        title_label.set_halign(Gtk.Align.START)
        title_label.set_xalign(0.0)
        title_label.add_css_class("config-section-title")
        section.append(title_label)

        if description is not None:
            desc_label = Gtk.Label(label=description)
            desc_label.set_halign(Gtk.Align.START)
            desc_label.set_xalign(0.0)
            desc_label.set_wrap(True)
            desc_label.add_css_class("config-section-description")
            section.append(desc_label)

        return section

    def _append_choice_rows(
        self,
        container: Gtk.Box,
        buttons: list[Gtk.CheckButton],
        columns: int = 2,
    ) -> None:
        """Append buttons to the container in evenly spaced rows."""

        row = None
        for index, button in enumerate(buttons):
            if index % columns == 0:
                row = Gtk.Box(
                    orientation=Gtk.Orientation.HORIZONTAL,
                    spacing=10,
                )
                row.add_css_class("config-choice-row")
                container.append(row)
            button.set_hexpand(True)
            row.append(button)

    def _on_mode_changed(self, button: Gtk.CheckButton, mode: str) -> None:
        """Update the selected player mode."""

        if not button.get_active():
            return

        self._selected_mode = mode
        self._mode_hint.set_label(MODE_HINTS[mode])
        self._update_ai_options_visibility()

    def _on_algorithm_changed(self, *_args) -> None:
        """Store the selected AI algorithm."""

        algo_idx = self._algorithm_combo.get_selected()
        self._selected_algorithm = ALGORITHM_OPTIONS[algo_idx][1]

    def _update_ai_options_visibility(self) -> None:
        """Show algorithm options only when at least one AI is playing."""

        self._algorithm_section.set_visible(self._selected_mode != "hvh")

    def _on_speed_changed(
        self,
        button: Gtk.CheckButton,
        speed_key: str,
    ) -> None:
        """Refresh the available presets for the selected time mode."""

        if not button.get_active():
            return

        self._selected_speed = speed_key
        self._selected_preset = None
        self._start_button.set_sensitive(False)
        if speed_key == "custom":
            self._build_custom_controls()
        else:
            self._build_preset_buttons(speed_key)
            self._time_summary.set_label(
                "Choose one of the presets below to start the game."
            )

    def _clear_time_controls(self) -> None:
        """Remove all current time-control widgets."""

        child = self._preset_box.get_first_child()
        while child is not None:
            next_child = child.get_next_sibling()
            self._preset_box.remove(child)
            child = next_child

    def _build_preset_buttons(self, speed_key: str) -> None:
        """Render the preset buttons for the selected time mode."""

        self._clear_time_controls()
        self._custom_minutes_spin = None
        self._custom_increment_spin = None

        preset_grid = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=8,
        )
        self._preset_box.append(preset_grid)

        preset_group = None
        preset_buttons = []
        for preset in TIME_CONTROL_GROUPS[speed_key]["presets"]:
            button = Gtk.CheckButton(label=preset["label"])
            button.add_css_class("config-choice")
            if preset_group is not None:
                button.set_group(preset_group)
            else:
                preset_group = button
            button.connect("toggled", self._on_preset_changed, preset)
            preset_buttons.append(button)
        self._append_choice_rows(preset_grid, preset_buttons, columns=2)

    def _build_custom_controls(self) -> None:
        """Render inputs for a custom time control."""

        self._clear_time_controls()

        custom_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=10,
        )
        custom_box.add_css_class("config-card")
        self._preset_box.append(custom_box)

        minutes_row = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=8,
        )
        custom_box.append(minutes_row)

        minutes_label = Gtk.Label(label="Minutes per player")
        minutes_label.set_halign(Gtk.Align.START)
        minutes_label.set_hexpand(True)
        minutes_label.add_css_class("config-field-label")
        minutes_row.append(minutes_label)

        minutes_adjustment = Gtk.Adjustment(
            value=30,
            lower=1,
            upper=180,
            step_increment=1,
            page_increment=5,
            page_size=0,
        )
        self._custom_minutes_spin = Gtk.SpinButton(
            adjustment=minutes_adjustment,
            climb_rate=1,
            digits=0,
        )
        self._custom_minutes_spin.add_css_class("config-input")
        self._custom_minutes_spin.connect(
            "value-changed",
            self._on_custom_time_changed,
        )
        minutes_row.append(self._custom_minutes_spin)

        increment_row = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=8,
        )
        custom_box.append(increment_row)

        increment_label = Gtk.Label(label="Increment per move (seconds)")
        increment_label.set_halign(Gtk.Align.START)
        increment_label.set_hexpand(True)
        increment_label.add_css_class("config-field-label")
        increment_row.append(increment_label)

        increment_adjustment = Gtk.Adjustment(
            value=0,
            lower=0,
            upper=60,
            step_increment=1,
            page_increment=5,
            page_size=0,
        )
        self._custom_increment_spin = Gtk.SpinButton(
            adjustment=increment_adjustment,
            climb_rate=1,
            digits=0,
        )
        self._custom_increment_spin.add_css_class("config-input")
        self._custom_increment_spin.connect(
            "value-changed", self._on_custom_time_changed
        )
        increment_row.append(self._custom_increment_spin)

        custom_hint = Gtk.Label(
            label="Set your own clock values for a personalized timed game."
        )
        custom_hint.set_halign(Gtk.Align.START)
        custom_hint.set_xalign(0.0)
        custom_hint.set_wrap(True)
        custom_hint.add_css_class("config-note")
        custom_box.append(custom_hint)

        self._selected_preset = self._build_custom_preset()
        self._start_button.set_sensitive(True)
        self._time_summary.set_label(
            f"Selected: Custom {self._selected_preset['label']}"
        )

    def _on_preset_changed(
        self,
        button: Gtk.CheckButton,
        preset: dict,
    ) -> None:
        """Store the selected time control preset."""

        if not button.get_active():
            return

        self._selected_preset = preset
        self._start_button.set_sensitive(True)
        speed_label = TIME_CONTROL_GROUPS[self._selected_speed]["label"]
        self._time_summary.set_label(f"Selected: {speed_label} {preset['label']}")

    def _build_custom_preset(self) -> dict:
        """Return the current custom time selection."""

        minutes = int(self._custom_minutes_spin.get_value())
        increment = int(self._custom_increment_spin.get_value())
        label = f"{minutes} | {increment}" if increment > 0 else f"{minutes} min"
        return {
            "label": label,
            "base_seconds": minutes * 60,
            "increment_seconds": increment,
        }

    def _on_custom_time_changed(self, *_args) -> None:
        """Store the current custom time selection."""

        if self._selected_speed != "custom":
            return

        self._selected_preset = self._build_custom_preset()
        self._start_button.set_sensitive(True)
        self._time_summary.set_label(
            f"Selected: Custom {self._selected_preset['label']}"
        )

    def get_config(self) -> dict:
        """Return the selected configuration as a dictionary."""

        if self._selected_speed is None or self._selected_preset is None:
            raise ShatranjError("A time control must be selected.")

        speed_label = TIME_CONTROL_GROUPS[self._selected_speed]["label"]

        return {
            "mode": self._selected_mode,
            "ai_color": BLACK,
            "algorithm": self._selected_algorithm,
            "speed_label": speed_label,
            "time_control_label": self._selected_preset["label"],
            "base_seconds": self._selected_preset["base_seconds"],
            "increment_seconds": self._selected_preset["increment_seconds"],
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

    def __init__(
        self,
        *,
        blitz: bool = False,
        blitz_time_minutes: int = 30,
        **kwargs,
    ) -> None:

        self._startup_blitz = blitz
        self._startup_blitz_time_minutes = blitz_time_minutes

        # Initialize the parent Gtk.ApplicationWindow

        super().__init__(**kwargs)

        # Title displayed in the window title bar

        self.set_title("Shatranj")

        # Default window size in pixels (width x height)

        self.set_default_size(900, 650)
        self._css_provider: Gtk.CssProvider | None = None
        self._install_css()

        # Rules engine — validates moves, detects end of game

        self._engine = RulesEngine()

        # Current game state (None = no game started)

        self._state: GameState | None = None
        self._saved: bool = True  # True = nothing to save

        # AI players dict: color → AIPlayer (empty = human vs human)

        self._ai_players: dict[str, AIPlayer] = {}

        self._timer_source_id: int | None = None
        self._clock_mode = "idle"
        self._time_control_name = "No active game"
        self._increment_seconds = 0
        self._remaining_time: dict[str, float] = {}
        self._turn_started_at: float | None = None
        self._elapsed_started_at: float | None = None
        self._game_paused = False
        self._network_client: GameClient | None = None
        self._network_player_id: str | None = None
        self._network_player_name: str | None = None
        self._network_server_address: str | None = None
        self._network_my_color: str | None = None
        self._network_last_players: list[str] = []
        self._network_last_invite: str | None = None
        self._network_lobby_dialog = None
        self._network_invite_dialog = None

        # Build the interface in order

        self._build_ui()  # layout and widgets

        self._build_menu()  # menu bar

        self._build_shortcuts()  # keyboard shortcuts
        self._reset_clock()

        if self._startup_blitz:
            self._start_game(self._build_startup_game_config())

    def _build_startup_game_config(self) -> dict:
        """Build the default GUI config used for --blitz startup."""

        base_seconds = self._startup_blitz_time_minutes * 60
        config = {
            "mode": "hvh",
            "ai_color": BLACK,
            "algorithm": "alphabeta",
            "speed_label": "Custom",
            "time_control_label": f"{self._startup_blitz_time_minutes} min",
            "base_seconds": base_seconds,
            "increment_seconds": 0,
        }

        for speed_key in TIME_CONTROL_ORDER:
            group = TIME_CONTROL_GROUPS[speed_key]
            for preset in group["presets"]:
                if (
                    preset["base_seconds"] == base_seconds
                    and preset["increment_seconds"] == 0
                ):
                    config["speed_label"] = group["label"]
                    config["time_control_label"] = preset["label"]
                    config["base_seconds"] = preset["base_seconds"]
                    return config

        return config

    def _install_css(self) -> None:
        """Install local CSS used by the custom clock widgets."""

        display = Gdk.Display.get_default()
        if display is None:
            return

        provider = Gtk.CssProvider()
        provider.load_from_data(CLOCK_CSS.encode("utf-8"))
        Gtk.StyleContext.add_provider_for_display(
            display,
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )
        self._css_provider = provider

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
        """Builds the welcome screen shown at startup."""

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        root.add_css_class("welcome-root")
        root.set_hexpand(True)
        root.set_vexpand(True)

        layout = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=20,
        )
        layout.set_halign(Gtk.Align.CENTER)
        layout.set_valign(Gtk.Align.CENTER)
        layout.set_hexpand(True)
        layout.set_vexpand(True)
        root.append(layout)

        preview_state = GameState()
        self._welcome_board_widget = BoardWidget(self._engine)
        self._welcome_board_widget.set_size_request(460, 460)
        self._welcome_board_widget.set_hexpand(False)
        self._welcome_board_widget.set_vexpand(False)
        self._welcome_board_widget.set_board(
            preview_state.board, preview_state.current_color
        )
        self._welcome_board_widget.set_interaction_enabled(False)
        board_frame = self._build_royal_board_frame(self._welcome_board_widget)
        board_frame.set_valign(Gtk.Align.CENTER)
        layout.append(board_frame)

        sidebar = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=14,
        )
        sidebar.add_css_class("welcome-sidebar")
        sidebar.set_valign(Gtk.Align.CENTER)
        layout.append(sidebar)

        kicker = Gtk.Label(label="FROM THE COURTS OF INDIA")
        kicker.set_halign(Gtk.Align.START)
        kicker.set_xalign(0.0)
        kicker.add_css_class("welcome-kicker")
        sidebar.append(kicker)

        title = Gtk.Label(label="Shatranj")
        title.set_halign(Gtk.Align.START)
        title.set_xalign(0.0)
        title.add_css_class("welcome-title")
        sidebar.append(title)

        subtitle = Gtk.Label(
            label=(
                "Start directly from the board. Choose a mode, pick the "
                "clock, and play from a real opening position."
            )
        )
        subtitle.set_halign(Gtk.Align.START)
        subtitle.set_xalign(0.0)
        subtitle.set_wrap(True)
        subtitle.add_css_class("welcome-subtitle")
        sidebar.append(subtitle)

        tag_row = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=8,
        )
        for label in ("Human", "AI", "Timed"):
            pill = Gtk.Label(label=label)
            pill.add_css_class("time-control-pill")
            tag_row.append(pill)
        sidebar.append(tag_row)

        new_btn = Gtk.Button(label=_("New Game"))
        new_btn.add_css_class("suggested-action")
        new_btn.add_css_class("welcome-action")
        new_btn.connect("clicked", self._on_new_game)
        sidebar.append(new_btn)

        load_btn = Gtk.Button(label=_("Load Game"))
        load_btn.add_css_class("welcome-action")
        load_btn.connect("clicked", self._on_load_game)
        sidebar.append(load_btn)

        online_btn = Gtk.Button(label=_("Join Server"))
        online_btn.add_css_class("welcome-action")
        online_btn.connect("clicked", self._on_join_server)
        sidebar.append(online_btn)

        info_btn = Gtk.Button(label=_("Info"))
        info_btn.add_css_class("welcome-action")
        info_btn.connect("clicked", self._on_info)
        sidebar.append(info_btn)

        sidebar.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))

        quit_btn = Gtk.Button(label=_("Quit"))
        quit_btn.add_css_class("destructive-action")
        quit_btn.add_css_class("welcome-action")
        quit_btn.connect("clicked", self._on_quit)
        sidebar.append(quit_btn)

        version_label = Gtk.Label(label="v0.4.0")
        version_label.set_halign(Gtk.Align.START)
        version_label.set_xalign(0.0)
        version_label.add_css_class("dim-label")
        sidebar.append(version_label)

        return root

    def _build_royal_board_frame(
        self,
        board_widget: BoardWidget,
        *,
        show_captures: bool = False,
    ) -> Gtk.Box:
        """Wrap a board widget in the welcome screen's stylized frame."""

        board_frame = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=12,
        )
        board_frame.add_css_class("welcome-board-frame")

        board_kicker = Gtk.Label(label="ROYAL SHATRANJ")
        board_kicker.set_halign(Gtk.Align.START)
        board_kicker.set_xalign(0.0)
        board_kicker.add_css_class("welcome-kicker")
        board_frame.append(board_kicker)

        board_meta = Gtk.Label(label="Where every square holds a destiny.")
        board_meta.set_halign(Gtk.Align.START)
        board_meta.set_xalign(0.0)
        board_meta.add_css_class("welcome-meta")
        board_frame.append(board_meta)

        if show_captures:
            self._black_capture_strip = self._create_capture_strip()
            board_frame.append(self._black_capture_strip)

        board_frame.append(board_widget)

        if show_captures:
            self._white_capture_strip = self._create_capture_strip()
            board_frame.append(self._white_capture_strip)

        return board_frame

    def _create_capture_strip(self) -> Gtk.Box:
        """Create one horizontal strip for small captured-piece icons."""
        strip = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=4,
        )
        strip.add_css_class("captured-strip")
        strip.set_halign(Gtk.Align.START)
        strip.set_hexpand(True)
        strip.set_size_request(-1, 24)
        return strip

    @staticmethod
    def _clear_box_children(box: Gtk.Box) -> None:
        """Remove every child from a GTK box."""
        while True:
            child = box.get_first_child()
            if child is None:
                return
            box.remove(child)

    def _make_captured_piece_widget(self, piece: str, color: str):
        """Build one small piece icon for the capture strips."""
        path = get_piece_asset_path(piece, color)
        if path is not None:
            picture = Gtk.Picture.new_for_filename(path)
            picture.set_size_request(20, 20)
            if hasattr(picture, "set_can_shrink"):
                picture.set_can_shrink(True)
            if hasattr(picture, "set_keep_aspect_ratio"):
                picture.set_keep_aspect_ratio(True)
            picture.set_tooltip_text(PIECE_LABELS.get(piece, piece.title()))
            return picture

        label = Gtk.Label(label=piece[:1].upper())
        label.set_halign(Gtk.Align.CENTER)
        label.set_valign(Gtk.Align.CENTER)
        label.set_tooltip_text(PIECE_LABELS.get(piece, piece.title()))
        return label

    def _update_captured_pieces(self) -> None:
        """Refresh the captured-piece strips above and below the board."""
        if not hasattr(self, "_black_capture_strip"):
            return

        captured = _captured_pieces_for_display(self._state)
        top_color, bottom_color = _captured_piece_colors_for_display(
            self._network_my_color
        )
        for captured_color, strip in (
            (top_color, self._black_capture_strip),
            (bottom_color, self._white_capture_strip),
        ):
            self._clear_box_children(strip)
            for piece in captured[captured_color]:
                strip.append(self._make_captured_piece_widget(piece, captured_color))

    def _sync_clock_card_order(self) -> None:
        """Keep top and bottom clocks aligned with the board orientation."""

        clock_box = getattr(self, "_clock_cards_box", None)
        black_card = getattr(self, "_black_clock_card", None)
        white_card = getattr(self, "_white_clock_card", None)
        if clock_box is None or black_card is None or white_card is None:
            return

        cards = {
            BLACK: black_card,
            WHITE: white_card,
        }
        top_color, bottom_color = _display_side_order(self._network_my_color)

        for card in (black_card, white_card):
            try:
                clock_box.remove(card)
            except Exception:
                pass

        clock_box.append(cards[top_color])
        clock_box.append(cards[bottom_color])

    def _refresh_game_view(self) -> None:
        """Refresh board-adjacent widgets after any state change."""
        ShatranjWindow._sync_clock_card_order(self)
        if self._state is not None:
            self._board_widget.set_flipped(
                _should_flip_board(self._network_my_color)
            )
            self._board_widget.set_board(
                self._state.board,
                self._state.current_color,
            )
        self._sync_board_interaction()
        self._update_history()
        self._update_captured_pieces()

    def _build_game_screen(self) -> Gtk.Box:
        """

        Builds the game screen with the board and right panel.

        """

        root = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
        )
        root.add_css_class("game-root")
        root.set_hexpand(True)
        root.set_vexpand(True)

        hbox = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=18,
        )
        hbox.set_halign(Gtk.Align.CENTER)
        hbox.set_valign(Gtk.Align.CENTER)
        hbox.set_hexpand(True)
        hbox.set_vexpand(True)

        hbox.set_margin_top(10)

        hbox.set_margin_bottom(10)

        hbox.set_margin_start(10)

        hbox.set_margin_end(10)

        root.append(hbox)

        board_shell = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
        )
        board_shell.set_halign(Gtk.Align.CENTER)
        board_shell.set_valign(Gtk.Align.CENTER)

        # Our custom board widget

        self._board_widget = BoardWidget(self._engine)

        self._board_widget.set_size_request(480, 480)

        self._board_widget.set_hexpand(False)

        self._board_widget.set_vexpand(False)
        self._board_widget.set_halign(Gtk.Align.CENTER)
        self._board_widget.set_valign(Gtk.Align.CENTER)

        # When the user plays a move, BoardWidget calls this callback

        self._board_widget.on_move_played = self._on_move_played

        board_frame = self._build_royal_board_frame(
            self._board_widget,
            show_captures=True,
        )
        board_shell.append(board_frame)
        hbox.append(board_shell)

        # Build and add the right panel

        right_panel = self._build_right_panel()
        right_panel.set_hexpand(False)
        right_panel.set_vexpand(False)
        right_panel.set_valign(Gtk.Align.CENTER)

        hbox.append(right_panel)

        return root

    def _build_right_panel(self) -> Gtk.Box:
        """Right panel: timer + move history + buttons."""

        panel = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=8,
        )

        panel.set_size_request(240, -1)
        panel.set_hexpand(False)

        clock_panel = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=10,
        )
        clock_panel.add_css_class("clock-panel")
        panel.append(clock_panel)

        clock_label = Gtk.Label(label=_("Game Clock"))
        clock_label.set_halign(Gtk.Align.START)
        clock_label.set_xalign(0.0)
        clock_label.add_css_class("clock-title")
        clock_panel.append(clock_label)

        self._time_control_label = Gtk.Label(label=_("No active game"))
        self._time_control_label.set_halign(Gtk.Align.START)
        self._time_control_label.set_xalign(0.0)
        self._time_control_label.add_css_class("time-control-pill")
        clock_panel.append(self._time_control_label)

        self._clock_cards_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=10,
        )
        clock_panel.append(self._clock_cards_box)

        (
            self._black_clock_card,
            self._black_clock_side_label,
            self._black_timer_label,
            self._black_timer_status_label,
        ) = self._create_clock_card("Black", "clock-card-black")
        self._clock_cards_box.append(self._black_clock_card)

        (
            self._white_clock_card,
            self._white_clock_side_label,
            self._white_timer_label,
            self._white_timer_status_label,
        ) = self._create_clock_card("White", "clock-card-white")
        self._clock_cards_box.append(self._white_clock_card)
        self._sync_clock_card_order()

        # "Move History" label aligned to the left

        history_label = Gtk.Label(label=_("Move History"))

        history_label.set_halign(Gtk.Align.START)

        panel.append(history_label)

        # ScrolledWindow with move list

        self._history_scroll = Gtk.ScrolledWindow()

        self._history_scroll.set_vexpand(True)
        self._history_scroll.set_hexpand(False)

        self._history_list = Gtk.ListBox()

        self._history_list.set_selection_mode(Gtk.SelectionMode.NONE)

        self._history_scroll.set_child(self._history_list)

        panel.append(self._history_scroll)

        # Undo button

        undo_btn = Gtk.Button(label=_("Undo"))

        undo_btn.connect("clicked", self._on_undo)

        panel.append(undo_btn)

        # Hint button

        hint_btn = Gtk.Button(label=_("Hint"))

        hint_btn.connect("clicked", self._on_hint)

        panel.append(hint_btn)

        # Back to menu button

        menu_btn = Gtk.Button(label=_("Back to Menu"))

        menu_btn.connect("clicked", self._on_back_to_menu)

        panel.append(menu_btn)

        return panel

    def _create_clock_card(
        self, side_label: str, tone_class: str
    ) -> tuple[Gtk.Box, Gtk.Label, Gtk.Label, Gtk.Label]:
        """Build one styled clock card."""

        card = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=2,
        )
        card.add_css_class("clock-card")
        card.add_css_class(tone_class)

        side = Gtk.Label(label=side_label.upper())
        side.set_halign(Gtk.Align.START)
        side.set_xalign(0.0)
        side.add_css_class("clock-side")
        card.append(side)

        timer_label = Gtk.Label(label="--:--")
        timer_label.set_halign(Gtk.Align.START)
        timer_label.set_xalign(0.0)
        timer_label.add_css_class("clock-time")
        card.append(timer_label)

        status_label = Gtk.Label(label=_("Waiting for game"))
        status_label.set_halign(Gtk.Align.START)
        status_label.set_xalign(0.0)
        status_label.set_wrap(True)
        status_label.set_max_width_chars(24)
        status_label.add_css_class("clock-status")
        card.append(status_label)

        return card, side, timer_label, status_label

    # ------------------------------------------------------------------

    # Timer

    # ------------------------------------------------------------------

    def _start_timer(self) -> None:
        """Start the game clock."""

        self._stop_timer(reset=False)

        if self._state is None or self._clock_mode == "idle":
            return

        now = time.monotonic()
        if self._clock_mode == "timed":
            self._turn_started_at = now
        elif self._clock_mode == "elapsed":
            self._elapsed_started_at = now

        self._timer_source_id = GLib.timeout_add(200, self._on_timer_tick)
        self._on_timer_tick()

    def _stop_timer(self, reset: bool = False) -> None:
        """Stop the timer and optionally reset the label."""

        if self._timer_source_id is not None:
            GLib.source_remove(self._timer_source_id)
            self._timer_source_id = None

        self._turn_started_at = None
        self._elapsed_started_at = None

        if reset:
            self._reset_clock()
        else:
            self._update_clock_labels()

    def _on_timer_tick(self) -> bool:
        """Refresh the active clock while a game is running."""

        if self._state is None:
            self._timer_source_id = None
            return False

        if self._clock_mode == "timed" and self._is_active_player_flagged():
            self._timer_source_id = None
            return False

        self._update_clock_labels()
        return True

    def _reset_clock(self) -> None:
        """Reset the clock state shown in the right panel."""

        self._clock_mode = "idle"
        self._time_control_name = "No active game"
        self._increment_seconds = 0
        self._remaining_time = {}
        self._turn_started_at = None
        self._elapsed_started_at = None
        self._game_paused = False
        self._update_clock_labels()

    def _configure_new_game_clock(self, config: dict) -> None:
        """Prepare a timed clock for a fresh game."""

        self._clock_mode = "timed"
        self._time_control_name = (
            f"{config['speed_label']} {config['time_control_label']}"
        )
        self._increment_seconds = config["increment_seconds"]
        base_seconds = float(config["base_seconds"])
        self._remaining_time = {
            WHITE: base_seconds,
            BLACK: base_seconds,
        }
        self._turn_started_at = None
        self._elapsed_started_at = None
        self._game_paused = False
        self._update_clock_labels()

    def _configure_loaded_game_clock(self) -> None:
        """Prepare the fallback clock used for legacy saves."""

        self._configure_elapsed_clock("Loaded Game")

    def _configure_elapsed_clock(self, label: str) -> None:
        """Show an untimed elapsed clock with a custom label."""

        self._clock_mode = "elapsed"
        self._time_control_name = label
        self._increment_seconds = 0
        self._remaining_time = {}
        self._turn_started_at = None
        self._elapsed_started_at = None
        self._game_paused = False
        self._update_clock_labels()

    def _build_clock_state(self) -> ClockState:
        """Serialize the current timed clock for save files."""

        if self._clock_mode != "timed" or self._state is None:
            return ClockState()

        now = time.monotonic()
        return ClockState(
            mode="timed",
            label=self._time_control_name,
            base_seconds=max(self._remaining_time.values(), default=0.0),
            increment_seconds=self._increment_seconds,
            white_seconds=self._get_display_time(WHITE, now),
            black_seconds=self._get_display_time(BLACK, now),
            paused=self._game_paused,
        )

    def _apply_loaded_clock_state(self, clock_state: ClockState) -> None:
        """Restore persisted clock data after loading a game."""

        if clock_state.mode != "timed":
            self._configure_loaded_game_clock()
            return

        self._clock_mode = "timed"
        self._time_control_name = clock_state.label
        self._increment_seconds = clock_state.increment_seconds
        self._remaining_time = {
            WHITE: clock_state.white_seconds,
            BLACK: clock_state.black_seconds,
        }
        self._turn_started_at = None
        self._elapsed_started_at = None
        self._game_paused = clock_state.paused
        self._update_clock_labels()

    def _show_alert(self, title: str, detail: str) -> None:
        """Display a simple GTK alert dialog."""

        dialog = Gtk.AlertDialog()
        dialog.set_message(title)
        dialog.set_detail(detail)
        dialog.show(self)

    def _save_game_to_path(
        self,
        path: str,
        *,
        state: GameState | None = None,
        clock_state: ClockState | None = None,
    ) -> bool:
        """Persist a game state to disk."""

        if state is None:
            state = self._state
        if state is None:
            return False

        if clock_state is None:
            clock_state = self._build_clock_state()

        save_game_file(
            path,
            state=state,
            clock=clock_state,
            ai_players=self._ai_players,
        )
        return True

    def _set_clock_card_state(
        self,
        card: Gtk.Box,
        timer_label: Gtk.Label,
        *,
        active: bool = False,
        critical: bool = False,
    ) -> None:
        """Apply active and critical styling to one clock card."""

        if active:
            card.add_css_class("clock-card-active")
        else:
            card.remove_css_class("clock-card-active")

        if critical:
            card.add_css_class("clock-card-critical")
            timer_label.add_css_class("clock-time-critical")
        else:
            card.remove_css_class("clock-card-critical")
            timer_label.remove_css_class("clock-time-critical")

    def _get_clock_status_text(
        self,
        color: str,
        current_color: str | None,
    ) -> str:
        """Return the status line shown under one timed clock."""

        if self._game_paused:
            status = _("Paused")
        elif color == current_color:
            if color in self._ai_players:
                status = _("AI thinking")
            else:
                status = _("To move")
        else:
            if color in self._ai_players:
                status = _("AI ready")
            else:
                status = _("Waiting")

        if self._increment_seconds > 0:
            return _("{status} | +{n}s increment").format(
                status=status, n=self._increment_seconds
            )
        return status

    def _update_clock_labels(self) -> None:
        """Refresh the clock labels according to the active mode."""

        if self._clock_mode == "timed":
            now = time.monotonic()
            current_color = None
            if self._state is not None:
                current_color = self._state.current_color
            white_time = self._get_display_time(WHITE, now)
            black_time = self._get_display_time(BLACK, now)
            self._time_control_label.set_label(self._time_control_name)
            self._white_clock_side_label.set_label("WHITE")
            self._black_clock_side_label.set_label("BLACK")
            self._white_timer_label.set_label(
                _format_clock(white_time, show_tenths=True)
            )
            self._black_timer_label.set_label(
                _format_clock(black_time, show_tenths=True)
            )
            self._white_timer_status_label.set_label(
                self._get_clock_status_text(WHITE, current_color)
            )
            self._black_timer_status_label.set_label(
                self._get_clock_status_text(BLACK, current_color)
            )
            self._set_clock_card_state(
                self._white_clock_card,
                self._white_timer_label,
                active=(current_color == WHITE and not self._game_paused),
                critical=white_time <= 20,
            )
            self._set_clock_card_state(
                self._black_clock_card,
                self._black_timer_label,
                active=(current_color == BLACK and not self._game_paused),
                critical=black_time <= 20,
            )
            return

        if self._clock_mode == "elapsed":
            elapsed = 0.0
            if self._elapsed_started_at is not None:
                elapsed = time.monotonic() - self._elapsed_started_at
            current_color = None
            if self._state is not None:
                current_color = self._state.current_color
            self._time_control_label.set_label(self._time_control_name)
            self._white_clock_side_label.set_label(_("ELAPSED"))
            self._black_clock_side_label.set_label(_("TURN"))
            self._white_timer_label.set_label(_format_clock(elapsed))
            self._black_timer_label.set_label(_display_color(current_color))
            self._white_timer_status_label.set_label(
                _("Time since this game was loaded")
            )
            self._black_timer_status_label.set_label(_("Side to move"))
            self._set_clock_card_state(
                self._white_clock_card,
                self._white_timer_label,
            )
            self._set_clock_card_state(
                self._black_clock_card,
                self._black_timer_label,
                active=current_color is not None,
            )
            return

        self._time_control_label.set_label(_("No active game"))
        self._white_clock_side_label.set_label(_("WHITE"))
        self._black_clock_side_label.set_label(_("BLACK"))
        self._white_timer_label.set_label("--:--")
        self._black_timer_label.set_label("--:--")
        self._white_timer_status_label.set_label(_("Waiting for game"))
        self._black_timer_status_label.set_label(_("Waiting for game"))
        self._set_clock_card_state(
            self._white_clock_card,
            self._white_timer_label,
        )
        self._set_clock_card_state(
            self._black_clock_card,
            self._black_timer_label,
        )

    def _get_display_time(self, color: str, now: float | None = None) -> float:
        """Return the time currently shown for one player."""

        remaining = self._remaining_time.get(color, 0.0)
        if (
            self._clock_mode == "timed"
            and self._state is not None
            and not self._game_paused
            and self._state.current_color == color
            and self._turn_started_at is not None
        ):
            if now is None:
                now = time.monotonic()
            remaining -= now - self._turn_started_at
        return max(0.0, remaining)

    def _finish_active_turn(self, moving_color: str) -> bool:
        """Commit the elapsed time for the player who just moved."""

        if self._clock_mode != "timed" or self._turn_started_at is None:
            return True

        remaining = self._get_display_time(moving_color)
        self._turn_started_at = None

        if remaining <= 0:
            winner = BLACK if moving_color == WHITE else WHITE
            self._remaining_time[moving_color] = 0.0
            self._update_clock_labels()
            self._show_game_over_dialog(
                _("Time out! {color} wins!").format(color=_display_color(winner))
            )
            return False

        self._remaining_time[moving_color] = remaining + self._increment_seconds
        self._update_clock_labels()
        return True

    def _start_next_turn(self) -> None:
        """Start the clock for the player whose turn just began."""

        if self._clock_mode != "timed" or self._state is None:
            return

        if self._game_paused:
            return

        self._turn_started_at = time.monotonic()
        self._update_clock_labels()

    def _is_active_player_flagged(self) -> bool:
        """Handle a timeout detected from the running clock."""

        if (
            self._clock_mode != "timed"
            or self._state is None
            or self._game_paused
            or self._turn_started_at is None
        ):
            return False

        current_color = self._state.current_color
        if self._get_display_time(current_color) > 0:
            return False

        self._remaining_time[current_color] = 0.0
        winner = BLACK if current_color == WHITE else WHITE
        self._update_clock_labels()
        self._show_game_over_dialog(
            _("Time out! {color} wins!").format(color=_display_color(winner))
        )
        return True

    def _sync_board_interaction(self) -> None:
        """Allow moves only when the current turn belongs to a human."""

        if not hasattr(self, "_board_widget"):
            return

        can_interact = _can_interact_with_board(
            self._state,
            game_paused=self._game_paused,
            ai_players=self._ai_players,
            network_player_color=self._network_my_color,
        )
        self._board_widget.set_interaction_enabled(can_interact)

    def _toggle_pause(self) -> None:
        """Pause or resume a timed game."""

        if self._state is None or self._clock_mode != "timed":
            return

        if self._game_paused:
            self._game_paused = False
            self._turn_started_at = time.monotonic()
            self._sync_board_interaction()
            self._update_clock_labels()
            self._auto_play_ai_turns()
            return

        current_color = self._state.current_color
        self._remaining_time[current_color] = self._get_display_time(current_color)
        self._turn_started_at = None
        self._game_paused = True
        self._sync_board_interaction()
        self._update_clock_labels()

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

        file_menu.append("Quit", "win.quit")

        menu.append_submenu("File", file_menu)

        game_menu = Gio.Menu()

        game_menu.append("Undo", "win.undo")

        game_menu.append("Redo", "win.redo")

        game_menu.append("Pause", "win.pause")

        game_menu.append("Hint", "win.hint")

        menu.append_submenu("Game", game_menu)

        network_menu = Gio.Menu()

        network_menu.append("Join Server", "win.join-server")
        network_menu.append("Online Players", "win.online-players")
        network_menu.append("Invite Player", "win.invite-player")
        network_menu.append("Accept Invite", "win.accept-invite")
        network_menu.append("Decline Invite", "win.decline-invite")

        menu.append_submenu("Network", network_menu)

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
            "join-server": self._on_join_server,
            "online-players": self._on_online_players,
            "invite-player": self._on_invite_player,
            "accept-invite": self._on_accept_invite,
            "decline-invite": self._on_decline_invite,
            "help": self._on_help,
            "quit": self._on_quit,
        }

        for name, callback in actions.items():

            action = Gio.SimpleAction.new(name, None)

            action.connect("activate", callback)

            self.add_action(action)

        self.get_application().set_menubar(menu)

        self.set_show_menubar(False)

    # ------------------------------------------------------------------

    # Keyboard shortcuts (F28)

    # ------------------------------------------------------------------

    def _build_shortcuts(self) -> None:
        """Configures keyboard shortcuts."""

        app = self.get_application()

        for action, accels in WINDOW_SHORTCUTS.items():

            app.set_accels_for_action(action, accels)

    # ------------------------------------------------------------------

    # Game setup

    # ------------------------------------------------------------------

    def _start_game(self, config: dict) -> None:
        """Start a new game with the given configuration."""

        if self._is_network_connected():
            self._close_network_connection()

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

        self._refresh_game_view()

        self._configure_new_game_clock(config)
        self._start_timer()

        # Show menubar now that a game is in progress
        self.set_show_menubar(True)

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

        self._sync_board_interaction()

        def ai_thread():

            while (
                self._state is not None
                and self._state.current_color in self._ai_players
            ):
                if self._game_paused:
                    time.sleep(0.05)
                    continue

                ai = self._ai_players[self._state.current_color]

                move = ai.choose_move(self._state.board)

                if move is None:

                    break

                while self._game_paused and self._state is not None:
                    time.sleep(0.05)

                if (
                    self._state is None
                    or self._state.current_color not in self._ai_players
                ):
                    break

                # GLib.idle_add ensures GTK updates happen in the main thread

                done_event = threading.Event()
                GLib.idle_add(self._apply_ai_move, move, done_event)
                done_event.wait(timeout=5)

        thread = threading.Thread(target=ai_thread, daemon=True)

        thread.start()

    def _apply_ai_move(
        self,
        move,
        done_event: threading.Event | None = None,
    ) -> bool:
        """Apply an AI move in the GTK main thread.\

         Returns False to remove from idle."""
        completed = True
        try:
            if self._state is None:

                return False

            if self._game_paused:
                completed = False
                return True

            moving_color = self._state.current_color
            if moving_color not in self._ai_players:
                return False

            if move.color != moving_color:
                return False

            legal_moves = self._engine.generate_legal_moves(
                self._state.board, moving_color
            )
            if move not in legal_moves:
                return False

            if not self._finish_active_turn(moving_color):
                return False

            self._state.apply_move(move)
            self._saved = False

            self._refresh_game_view()

            if self._check_game_over():
                return False

            self._start_next_turn()
            self._sync_board_interaction()
            # GLib.idle_add requires returning False to stop repeating
            return False
        finally:
            if done_event is not None and completed:
                done_event.set()

    # ------------------------------------------------------------------

    # Callbacks

    # ------------------------------------------------------------------

    def _on_new_game(self, *_args) -> None:
        """Open the new game configuration dialog."""

        dialog = NewGameDialog(self)

        dialog.connect("response", self._on_new_game_response)

        dialog.present()

    def _on_new_game_response(self, dialog, response) -> None:
        """Called when the user closes the new game dialog."""

        if response == Gtk.ResponseType.OK:

            try:
                config = dialog.get_config()
            except ShatranjError:
                return

            dialog.destroy()

            self._start_game(config)

        else:

            dialog.destroy()

    def _on_back_to_menu(self, *_args) -> None:
        """Go back to the welcome screen."""

        def do_back():
            self._close_network_connection()
            self.set_show_menubar(False)  # hide menubar on welcome screen
            self._stop_timer(reset=True)

            self._state = None

            self._ai_players = {}
            self._sync_board_interaction()

            self._stack.set_visible_child_name("welcome")

        self._confirm_abandon(do_back)

    def _on_quit(self, *_args) -> None:
        """Quit the application from the welcome screen."""

        def do_quit():
            self._close_network_connection()
            self.get_application().quit()

        self._confirm_abandon(do_quit)

    def _on_load_game(self, *_args) -> None:

        dialog = Gtk.FileDialog()

        dialog.set_title(_("Load Game"))

        dialog.open(self, None, self._on_load_game_finish)

    def _on_load_game_finish(self, dialog, result) -> None:
        try:
            file = dialog.open_finish(result)
            if file is None:
                return
            path = file.get_path()
            if self._is_network_connected():
                self._close_network_connection()
            loaded = load_game_file(path)
            self._state = loaded.state
            self._saved = True
            self._ai_players = loaded.ai_players
            self._refresh_game_view()
            self._apply_loaded_clock_state(loaded.clock)
            self._start_timer()
            self.set_show_menubar(True)
            self._stack.set_visible_child_name("game")

        except LoadError as err:
            self._show_alert(_("Load Error"), str(err))
        except ShatranjError as err:
            self._show_alert(_("Error"), str(err))
        except Exception as err:
            self._show_alert(_("Load Error"), str(err))

    def _on_save_game(self, *_args) -> None:

        if self._state is None:

            return

        dialog = Gtk.FileDialog()

        dialog.set_title(_("Save Game"))

        dialog.save(self, None, self._on_save_game_finish)

    def _on_save_game_finish(self, dialog, result) -> None:
        try:
            file = dialog.save_finish(result)
            if file is None:
                return
            path = file.get_path()
            if self._save_game_to_path(path):
                self._saved = True
            else:
                self._show_alert(
                    _("Save Error"),
                    _("Could not write to '{path}'.").format(path=path),
                )

        except ShatranjError as err:
            self._show_alert(_("Save Error"), str(err))
        except Exception as err:
            self._show_alert(_("Save Error"), str(err))

    def _on_info(self, *_args) -> None:
        """Show a centered information dialog."""
        dialog = Gtk.Dialog(
            title=_("About Shatranj"),
            transient_for=self,
            modal=True,
        )
        dialog.set_default_size(420, 260)
        dialog.add_button(_("Close"), Gtk.ResponseType.CLOSE)

        content = dialog.get_content_area()
        content.set_spacing(0)
        content.set_margin_top(0)
        content.set_margin_bottom(0)
        content.set_margin_start(0)
        content.set_margin_end(0)

        box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=10,
        )
        box.set_margin_top(24)
        box.set_margin_bottom(24)
        box.set_margin_start(24)
        box.set_margin_end(24)
        content.append(box)

        title = Gtk.Label(label="Shatranj")
        title.set_halign(Gtk.Align.CENTER)
        title.set_xalign(0.5)
        title.add_css_class("config-title")
        box.append(title)

        version = Gtk.Label(label="Version 0.4.0")
        version.set_halign(Gtk.Align.CENTER)
        version.set_xalign(0.5)
        box.append(version)

        description = Gtk.Label(
            label=_(
                "Indian Chess - a faithful implementation of the ancient "
                "game of Shatranj."
            )
        )
        description.set_halign(Gtk.Align.CENTER)
        description.set_xalign(0.5)
        description.set_wrap(True)
        description.set_justify(Gtk.Justification.CENTER)
        box.append(description)

        school = Gtk.Label(label=_("Universite de Bordeaux"))
        school.set_halign(Gtk.Align.CENTER)
        school.set_xalign(0.5)
        box.append(school)

        website = Gtk.Label(label="https://www.u-bordeaux.fr")
        website.set_halign(Gtk.Align.CENTER)
        website.set_xalign(0.5)
        website.set_selectable(True)
        box.append(website)

        copyright_label = Gtk.Label(
            label="(c) 2025-2026 Master Informatique - Universite de Bordeaux"
        )
        copyright_label.set_halign(Gtk.Align.CENTER)
        copyright_label.set_xalign(0.5)
        copyright_label.set_wrap(True)
        copyright_label.set_justify(Gtk.Justification.CENTER)
        box.append(copyright_label)

        dialog.connect("response", lambda dlg, *_args: dlg.destroy())
        dialog.present()
        return
        """
                "Indian Chess — a faithful implementation of"
                "the ancient game of Shatranj."
            )
        )
        dialog.set_website_label(_("Université de Bordeaux"))
        dialog.set_copyright(
            "© 2025–2026 Master Informatique" " — Université de Bordeaux"
        )

        """

    def _on_configuration(self, *_args) -> None:
        """Show the active GUI configuration and keyboard shortcuts."""
        shortcut_lines = []
        for action, accels in WINDOW_SHORTCUTS.items():
            label = action.replace("win.", "").replace("-", " ")
            shortcut_lines.append(f"  {label:<14} {' / '.join(accels)}")

        detail = (
            _("Current mode: {mode}\n").format(mode=self._time_control_name)
            + _("Keyboard shortcuts:\n")
            + "\n".join(shortcut_lines)
        )
        self._show_alert(_("Configuration"), detail)

    def _on_undo(self, *_args) -> None:
        if self._is_network_game_active():
            self._show_alert(
                _("Network"),
                _("Undo is not available during an online game."),
            )
            return

        if self._state is None:

            return

        self._state.undo()

        self._refresh_game_view()
        if self._clock_mode == "timed":
            self._turn_started_at = time.monotonic()
        self._update_clock_labels()

    def _on_redo(self, *_args) -> None:
        """Replay the last undone move."""

        if self._is_network_game_active():
            self._show_alert(
                _("Network"),
                _("Redo is not available during an online game."),
            )
            return

        if self._state is None:
            return

        move = self._state.redo()
        if move is None:
            return

        self._refresh_game_view()
        if self._clock_mode == "timed":
            self._turn_started_at = time.monotonic()
        self._update_clock_labels()

    def _on_pause(self, *_args) -> None:
        if self._is_network_game_active():
            self._show_alert(
                _("Network"),
                _("Pause is not available during an online game."),
            )
            return
        self._toggle_pause()

    def _on_hint(self, *_args) -> None:

        if self._state is None:

            return

        move = choose_hint_move(
            self._state.board, self._state.current_color, self._ai_players
        )

        if move is None:

            return

        from shatranj.domain.core.board import Board as B

        frm = B.square_to_algebraic(move.from_square)

        to = B.square_to_algebraic(move.to_square)

        dialog = Gtk.AlertDialog()

        dialog.set_message(_("Hint"))

        dialog.set_detail(f"{frm}-{to}")

        dialog.show(self)

    def _on_help(self, *_args) -> None:
        """Show a help dialog explaining the basic controls."""
        help_text = (
            "HOW TO PLAY\n\n"
            "Click a piece to select it — valid squares are highlighted.\n"
            "Drop the piece onto a highlighted square to move.\n\n"
            "PIECE MOVES\n"
            "  Shah (K/k)   — one square in any direction\n"
            "  Ferz (F/f)   — one square diagonally\n"
            "  Rook (R/r)   — any distance horizontally or vertically\n"
            "  Knight (N/n) — L-shape jump (2+1 squares)\n"
            "  Alfil (A/a)  — exactly two squares diagonally (jumps)\n"
            "  Pawn (P/p)   — one square forward; captures diagonally\n\n"
            "WINNING CONDITIONS\n"
            "  Checkmate  — Shah in check with no escape\n"
            "  Stalemate  — opponent has no legal move (you win)\n"
            "  Bare King  — opponent has only their Shah left\n\n"
            "SHORTCUTS\n"
            "  Ctrl+N  New game    Ctrl+U  Undo\n"
            "  Ctrl+S  Save        Ctrl+R  Redo\n"
            "  Ctrl+L  Load        Ctrl+H  Hint\n"
            "  Ctrl+,  Config      Ctrl+I  Info\n"
            "  Ctrl+P  Pause       Ctrl+Q  Quit\n"
            "  F1      Help"
        )
        dialog = Gtk.AlertDialog()
        dialog.set_message(_("Shatranj — Help"))
        dialog.set_detail(help_text)
        dialog.show(self)

    def _default_network_player_name(self) -> str:
        """Return the default name proposed in the join-server dialog."""

        return os.environ.get("USERNAME") or os.environ.get("USER") or "Player"

    def _is_network_connected(self) -> bool:
        """Return True when the GUI holds an active TCP client."""

        client = self._network_client
        if client is None:
            return False
        if hasattr(client, "is_connected"):
            return bool(client.is_connected())
        return bool(getattr(client, "connected", False))

    def _is_network_game_active(self) -> bool:
        """Return True when the current visible game is an online match."""

        return self._state is not None and self._network_my_color is not None

    def _close_network_connection(self) -> None:
        """Disconnect from the online server and clear the GUI network state."""

        client = self._network_client
        self._close_network_dialogs()
        self._network_client = None
        self._network_player_id = None
        self._network_player_name = None
        self._network_server_address = None
        self._network_my_color = None
        self._network_last_players = []
        self._network_last_invite = None

        if client is not None:
            try:
                client.disconnect()
            except Exception:
                pass

    def _close_network_dialogs(self) -> None:
        """Destroy transient dialogs created by the online lobby flow."""

        for attr in ("_network_lobby_dialog", "_network_invite_dialog"):
            dialog = getattr(self, attr, None)
            if dialog is None:
                continue
            try:
                dialog.destroy()
            except Exception:
                pass
            setattr(self, attr, None)

    def _show_online_lobby_dialog(self) -> None:
        """Show one simple lobby dialog with the connected players."""

        if not self._is_network_connected():
            self._show_alert(
                _("Network"),
                _("Join a server before opening the online lobby."),
            )
            return

        if self._is_network_game_active():
            return

        if self._network_invite_dialog is not None:
            try:
                self._network_invite_dialog.destroy()
            except Exception:
                pass
            self._network_invite_dialog = None

        if self._network_lobby_dialog is not None:
            try:
                self._network_lobby_dialog.destroy()
            except Exception:
                pass
            self._network_lobby_dialog = None

        dialog = Gtk.Dialog(
            title=_("Online Lobby"),
            transient_for=self,
            modal=True,
        )
        self._network_lobby_dialog = dialog
        dialog.add_button(_("Close"), Gtk.ResponseType.CLOSE)
        dialog.add_button(_("Invite"), Gtk.ResponseType.OK)
        dialog.set_default_response(Gtk.ResponseType.OK)

        box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=10,
        )
        box.set_margin_top(18)
        box.set_margin_bottom(18)
        box.set_margin_start(18)
        box.set_margin_end(18)

        summary = Gtk.Label(
            label=_("Connected as {name} ({pid})").format(
                name=self._network_player_name or _("Player"),
                pid=self._network_player_id or "--",
            )
        )
        summary.set_halign(Gtk.Align.START)
        summary.set_xalign(0.0)
        summary.set_wrap(True)
        box.append(summary)

        players = Gtk.Label(label=_format_network_players(self._network_last_players))
        players.set_halign(Gtk.Align.START)
        players.set_xalign(0.0)
        players.set_wrap(True)
        players.set_selectable(True)
        box.append(players)

        player_label = Gtk.Label(label=_("Target Player ID"))
        player_label.set_halign(Gtk.Align.START)
        player_label.set_xalign(0.0)
        box.append(player_label)

        player_entry = Gtk.Entry()
        box.append(player_entry)

        blitz_label = Gtk.Label(label=_("Blitz Minutes (0 = untimed)"))
        blitz_label.set_halign(Gtk.Align.START)
        blitz_label.set_xalign(0.0)
        box.append(blitz_label)

        blitz_adjustment = Gtk.Adjustment(
            value=0,
            lower=0,
            upper=120,
            step_increment=1,
            page_increment=5,
            page_size=0,
        )
        blitz_spin = Gtk.SpinButton(
            adjustment=blitz_adjustment,
            climb_rate=1,
            digits=0,
        )
        box.append(blitz_spin)

        note = Gtk.Label(
            label=_("Copy an ID from the list above, paste it here, then click Invite.")
        )
        note.set_halign(Gtk.Align.START)
        note.set_xalign(0.0)
        note.set_wrap(True)
        note.add_css_class("config-note")
        box.append(note)

        dialog.get_content_area().append(box)

        def on_response(dlg, response):
            self._network_lobby_dialog = None
            if response == Gtk.ResponseType.OK:
                target_id = player_entry.get_text().strip()
                blitz_value = int(blitz_spin.get_value())
                dlg.destroy()
                self._send_network_invite(
                    target_id,
                    blitz_minutes=blitz_value if blitz_value > 0 else None,
                )
                return
            dlg.destroy()

        dialog.connect("response", on_response)
        dialog.present()

    def _show_network_invitation_dialog(self) -> None:
        """Show a direct accept/decline prompt for the latest invitation."""

        if self._network_lobby_dialog is not None:
            try:
                self._network_lobby_dialog.destroy()
            except Exception:
                pass
            self._network_lobby_dialog = None

        if self._network_invite_dialog is not None:
            try:
                self._network_invite_dialog.destroy()
            except Exception:
                pass
            self._network_invite_dialog = None

        dialog = Gtk.Dialog(
            transient_for=self,
            modal=True,
            title=_("Invitation Received"),
        )
        self._network_invite_dialog = dialog
        dialog.add_button(_("Decline"), Gtk.ResponseType.NO)
        dialog.add_button(_("Accept"), Gtk.ResponseType.YES)

        box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=10,
        )
        box.set_margin_top(18)
        box.set_margin_bottom(18)
        box.set_margin_start(18)
        box.set_margin_end(18)

        title = Gtk.Label(label=_("Invitation Received"))
        title.set_halign(Gtk.Align.START)
        title.set_xalign(0.0)
        title.add_css_class("config-title")
        box.append(title)

        details = Gtk.Label(label=self._network_last_invite or _("Unknown player"))
        details.set_halign(Gtk.Align.START)
        details.set_xalign(0.0)
        details.set_wrap(True)
        box.append(details)

        note = Gtk.Label(label=_("Do you want to start the online game?"))
        note.set_halign(Gtk.Align.START)
        note.set_xalign(0.0)
        note.set_wrap(True)
        box.append(note)

        dialog.get_content_area().append(box)

        def on_response(dlg, response):
            self._network_invite_dialog = None
            dlg.destroy()
            if response == Gtk.ResponseType.YES:
                self._on_accept_invite()
            elif response == Gtk.ResponseType.NO:
                self._on_decline_invite()

        dialog.connect("response", on_response)
        dialog.present()

    def _on_join_server(self, *_args) -> None:
        """Open the connection dialog used to join a TCP game server."""

        if self._is_network_connected():
            self._on_online_players()
            return

        if self._state is not None:
            self._show_alert(
                _("Network"),
                _(
                    "Finish the current game or return to the menu before joining a server."
                ),
            )
            return

        dialog = Gtk.Dialog(
            title=_("Join Server"),
            transient_for=self,
            modal=True,
        )
        dialog.add_button(_("Cancel"), Gtk.ResponseType.CANCEL)
        dialog.add_button(_("Connect"), Gtk.ResponseType.OK)
        dialog.set_default_response(Gtk.ResponseType.OK)

        box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=10,
        )
        box.set_margin_top(18)
        box.set_margin_bottom(18)
        box.set_margin_start(18)
        box.set_margin_end(18)

        address_label = Gtk.Label(label=_("Server Address"))
        address_label.set_halign(Gtk.Align.START)
        address_label.set_xalign(0.0)
        box.append(address_label)

        address_entry = Gtk.Entry()
        address_entry.set_text("localhost:12345")
        box.append(address_entry)

        name_label = Gtk.Label(label=_("Player Name"))
        name_label.set_halign(Gtk.Align.START)
        name_label.set_xalign(0.0)
        box.append(name_label)

        name_entry = Gtk.Entry()
        name_entry.set_text(self._default_network_player_name())
        box.append(name_entry)

        dialog.get_content_area().append(box)

        def on_response(dlg, response):
            if response == Gtk.ResponseType.OK:
                address = address_entry.get_text().strip() or "localhost:12345"
                name = (
                    name_entry.get_text().strip() or self._default_network_player_name()
                )
                dlg.destroy()
                self._connect_to_network_server(address, name)
                return
            dlg.destroy()

        dialog.connect("response", on_response)
        dialog.present()

    def _connect_to_network_server(self, address: str, player_name: str) -> None:
        """Create the TCP client used by the online GUI."""

        try:
            client = GameClient(address, callback=self._on_network_message)
            if not client.start_connection(player_name=player_name):
                self._show_alert(
                    _("Network"),
                    _("Could not connect to {address}.").format(address=address),
                )
                return

            self._network_client = client
            self._network_player_name = player_name
            self._network_server_address = address
            self._network_last_players = []
            client.get_players()
        except Exception as err:
            self._show_alert(_("Network Error"), str(err))

    def _on_online_players(self, *_args) -> None:
        """Request the current list of online players."""

        if not self._is_network_connected():
            self._show_alert(
                _("Network"),
                _("Join a server before requesting the online players."),
            )
            return

        if self._network_last_players:
            self._show_online_lobby_dialog()
            return

        if not self._network_client.get_players():
            self._show_alert(
                _("Network"),
                _("Could not request the online players."),
            )

    def _on_invite_player(self, *_args) -> None:
        """Open a small dialog used to invite another online player."""

        if not self._is_network_connected():
            self._show_alert(
                _("Network"),
                _("Join a server before inviting another player."),
            )
            return

        dialog = Gtk.Dialog(
            title=_("Invite Player"),
            transient_for=self,
            modal=True,
        )
        dialog.add_button(_("Cancel"), Gtk.ResponseType.CANCEL)
        dialog.add_button(_("Invite"), Gtk.ResponseType.OK)
        dialog.set_default_response(Gtk.ResponseType.OK)

        box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=10,
        )
        box.set_margin_top(18)
        box.set_margin_bottom(18)
        box.set_margin_start(18)
        box.set_margin_end(18)

        player_label = Gtk.Label(label=_("Target Player ID"))
        player_label.set_halign(Gtk.Align.START)
        player_label.set_xalign(0.0)
        box.append(player_label)

        player_entry = Gtk.Entry()
        box.append(player_entry)

        blitz_label = Gtk.Label(label=_("Blitz Minutes (0 = untimed)"))
        blitz_label.set_halign(Gtk.Align.START)
        blitz_label.set_xalign(0.0)
        box.append(blitz_label)

        blitz_adjustment = Gtk.Adjustment(
            value=0,
            lower=0,
            upper=120,
            step_increment=1,
            page_increment=5,
            page_size=0,
        )
        blitz_spin = Gtk.SpinButton(
            adjustment=blitz_adjustment,
            climb_rate=1,
            digits=0,
        )
        box.append(blitz_spin)

        if self._network_last_players:
            hint = Gtk.Label(
                label=_("Known players:\n{players}").format(
                    players=_format_network_players(self._network_last_players)
                )
            )
            hint.set_halign(Gtk.Align.START)
            hint.set_xalign(0.0)
            hint.set_wrap(True)
            hint.add_css_class("config-note")
            box.append(hint)

        dialog.get_content_area().append(box)

        def on_response(dlg, response):
            if response == Gtk.ResponseType.OK:
                target_id = player_entry.get_text().strip()
                blitz_value = int(blitz_spin.get_value())
                dlg.destroy()
                self._send_network_invite(
                    target_id,
                    blitz_minutes=blitz_value if blitz_value > 0 else None,
                )
                return
            dlg.destroy()

        dialog.connect("response", on_response)
        dialog.present()

    def _send_network_invite(
        self,
        target_id: str,
        *,
        blitz_minutes: int | None = None,
    ) -> None:
        """Send a network invitation to another connected player."""

        if not self._is_network_connected():
            self._show_alert(
                _("Network"),
                _("Join a server before inviting another player."),
            )
            return

        payload = _build_network_invite_target(target_id, blitz_minutes)
        if not payload:
            self._show_alert(
                _("Network"),
                _("A target player ID is required."),
            )
            return

        if not self._network_client.invite_player(payload):
            self._show_alert(
                _("Network"),
                _("Could not send the invitation."),
            )

    def _on_accept_invite(self, *_args) -> None:
        """Accept the latest invitation received from the online lobby."""

        if not self._is_network_connected():
            self._show_alert(
                _("Network"),
                _("Join a server before accepting invitations."),
            )
            return

        if not self._network_client.accept_invite():
            self._show_alert(
                _("Network"),
                _("Could not accept the invitation."),
            )

    def _on_decline_invite(self, *_args) -> None:
        """Decline the latest invitation received from the online lobby."""

        if not self._is_network_connected():
            self._show_alert(
                _("Network"),
                _("Join a server before declining invitations."),
            )
            return

        if not self._network_client.decline_invite():
            self._show_alert(
                _("Network"),
                _("Could not decline the invitation."),
            )

    def _on_network_message(self, msg) -> None:
        """Relay TCP messages onto the GTK main loop."""

        GLib.idle_add(self._process_network_message, msg)

    def _process_network_message(self, msg) -> bool:
        """Handle one online message from the server on the GTK thread."""

        cmd = str(getattr(msg, "command", "")).upper()
        args = list(getattr(msg, "args", []))

        if cmd == "CONN_OK":
            for arg in args:
                if arg.startswith("id="):
                    self._network_player_id = arg.split("=", 1)[1]
                    break
            return False

        if cmd == "CONN_FAIL":
            self._close_network_connection()
            self._show_alert(
                _("Network"),
                ("\n".join(args) if args else _("Connection refused by the server.")),
            )
            return False

        if cmd == "PLAYERS_LIST":
            self._network_last_players = args
            if self._state is None and self._network_my_color is None:
                self._show_online_lobby_dialog()
            else:
                self._show_alert(
                    _("Online Players"),
                    _format_network_players(args),
                )
            return False

        if cmd == "INVITE_RECV":
            self._network_last_invite = " | ".join(args)
            self._show_network_invitation_dialog()
            return False

        if cmd == "INVITE_SENT":
            self._show_alert(
                _("Invitation Sent"),
                "\n".join(args) if args else _("Waiting for the opponent."),
            )
            return False

        if cmd == "INVITE_DECLINED":
            self._show_alert(
                _("Invitation Declined"),
                "\n".join(args) if args else _("The opponent declined."),
            )
            return False

        if cmd == "PONG":
            self._show_alert(
                _("Ping"),
                "\n".join(args) if args else _("Server reached."),
            )
            return False

        if cmd == "GAME_START":
            try:
                start_info = _parse_network_game_start(args)
            except Exception as err:
                self._show_alert(_("Network Error"), str(err))
                return False

            self._close_network_dialogs()
            self._state = GameState()
            self._state.board = start_info["board"]
            self._saved = False
            self._ai_players = {}
            self._network_my_color = start_info["my_color"]
            self._refresh_game_view()

            clock_config = _build_network_clock_config(start_info["blitz_minutes"])
            if clock_config is not None:
                self._configure_new_game_clock(clock_config)
            else:
                self._configure_elapsed_clock("Online Match")
            self._start_timer()

            self.set_show_menubar(True)
            self._stack.set_visible_child_name("game")
            self._sync_board_interaction()
            return False

        if cmd in ("OPPONENT_MOVE", "MOVE"):
            if self._state is None or not args:
                return False

            move = _move_from_network_text(self._state.board, args[0])
            if move is None:
                self._show_alert(
                    _("Network Error"),
                    _("Could not parse the opponent move: {move}").format(move=args[0]),
                )
                return False

            moving_color = self._state.current_color
            if not self._finish_active_turn(moving_color):
                return False

            self._state.apply_move(move)
            self._saved = False
            self._refresh_game_view()

            if self._check_game_over():
                return False

            self._start_next_turn()
            self._sync_board_interaction()
            return False

        if cmd in ("ERROR", "INVALID"):
            message = "\n".join(args) if args else _("Network error.")
            if self._is_network_game_active():
                lowered = message.lower()
                if any(
                    token in lowered
                    for token in (
                        "quit",
                        "quitt",
                        "left",
                        "disconnect",
                        "fant",
                    )
                ):
                    self._close_network_connection()
                    self._show_game_over_dialog(message)
                    return False
            self._show_alert(_("Network"), message)
            return False

        return False

    def _on_move_played(self, move) -> None:
        """Called by BoardWidget when the user plays a move."""

        if self._state is None:

            return

        if self._game_paused:
            self._sync_board_interaction()
            return

        if self._state.current_color in self._ai_players:
            self._sync_board_interaction()
            return

        if (
            self._is_network_game_active()
            and self._state.current_color != self._network_my_color
        ):
            self._sync_board_interaction()
            return

        moving_color = self._state.current_color
        if not self._finish_active_turn(moving_color):
            return

        if self._is_network_game_active():
            client = self._network_client
            move_text = _move_to_network_text(move)
            if client is None or not client.play_move(move_text):
                self._close_network_connection()
                self._show_game_over_dialog(_("Connection to the server was lost."))
                return

        self._state.apply_move(move)
        self._saved = False

        self._refresh_game_view()

        if self._check_game_over():

            return

        self._start_next_turn()
        self._sync_board_interaction()

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
            self._scroll_history_to_position(0.0)

            return

        # Refill with all moves

        for i, move in enumerate(self._state.get_history()):

            color = "W" if move.color == WHITE else "B"
            piece = PIECE_LABELS.get(move.piece_type, move.piece_type.title())

            frm = B.square_to_algebraic(move.from_square)

            to = B.square_to_algebraic(move.to_square)

            sep = "x" if move.captured_piece else "-"

            label = Gtk.Label(label=f"{i + 1}. {color} {piece} {frm}{sep}{to}")

            label.set_halign(Gtk.Align.START)
            label.set_xalign(0.0)
            label.set_wrap(True)
            label.set_max_width_chars(24)

            self._history_list.append(label)

        self._scroll_history_to_latest()

    def _scroll_history_to_latest(self) -> None:
        """Keep the move history focused on the most recent move."""

        self._scroll_history_to_position(None)

    def _scroll_history_to_position(self, value: float | None) -> None:
        """Scroll the move history after GTK has updated the layout."""

        if not hasattr(self, "_history_scroll"):
            return

        def _apply_scroll() -> bool:
            adjustment = self._history_scroll.get_vadjustment()
            if adjustment is None:
                return False

            if value is None:
                target = max(
                    0.0,
                    adjustment.get_upper() - adjustment.get_page_size(),
                )
            else:
                target = max(0.0, value)

            adjustment.set_value(target)
            return False

        GLib.idle_add(_apply_scroll)

    def _check_game_over(self) -> bool:
        """Check if the game is over after a move."""

        if self._state is None:

            return False

        current = self._state.current_color

        opponent = BLACK if current == WHITE else WHITE

        if self._engine.is_checkmate(self._state.board, current):

            self._show_game_over_dialog(
                _("Checkmate! {color} wins!").format(color=opponent)
            )
            return True

        if self._engine.is_stalemate(self._state.board, current):

            self._show_game_over_dialog(
                _("Stalemate! {color} wins!").format(color=opponent)
            )
            return True

        if self._engine.is_bare_king(self._state.board, current):

            self._show_game_over_dialog(
                _("Bare King! {color} wins!").format(color=opponent)
            )
            return True

        return False

    def _show_game_over_dialog(self, message: str) -> None:
        """Show a dialog when the game is over, then return to menu."""

        dialog = Gtk.AlertDialog()

        dialog.set_message(_("Game Over"))

        dialog.set_detail(message)

        dialog.show(self)

        self._stop_timer()

        # Keep the board visible — don't clear it

        self._state = None

        self._ai_players = {}
        self._sync_board_interaction()

    def _confirm_abandon(self, on_confirmed) -> None:
        """Ask the user to save before abandoning an unsaved game."""
        if self._state is None or self._saved:
            on_confirmed()
            return

        dialog = Gtk.MessageDialog(
            transient_for=self,
            modal=True,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.NONE,
            text=_("Save the game before leaving?"),
        )
        dialog.add_button(_("Cancel"), Gtk.ResponseType.CANCEL)
        dialog.add_button(_("No"), Gtk.ResponseType.NO)
        dialog.add_button(_("Yes"), Gtk.ResponseType.YES)

        def on_response(dlg, response):
            dlg.destroy()
            if response == Gtk.ResponseType.YES:
                self._save_then_confirm(on_confirmed)
            elif response == Gtk.ResponseType.NO:
                on_confirmed()

        dialog.connect("response", on_response)
        dialog.present()

    def _save_then_confirm(self, on_confirmed) -> None:
        """Open the save dialog, then run on_confirmed only after save."""
        if self._state is None:
            on_confirmed()
            return

        self._state_to_save = self._state

        dialog = Gtk.FileDialog()
        dialog.set_title(_("Save Game"))

        def on_save_finish(dlg, result):
            try:
                file = dlg.save_finish(result)
                if file is None:
                    # User cancelled save — don't proceed
                    return
                path = file.get_path()
                success = self._save_game_to_path(
                    path,
                    state=self._state_to_save,
                    clock_state=self._build_clock_state(),
                )
                if success:
                    self._saved = True
                else:
                    self._show_alert(
                        _("Save Error"),
                        _("Could not write to '{path}'.").format(path=path),
                    )
                    return
            except Exception as err:
                self._show_alert(_("Save Error"), str(err))
                return
            finally:
                self._state_to_save = None

            # Save succeeded — now execute the original action
            on_confirmed()

        dialog.save(self, None, on_save_finish)
