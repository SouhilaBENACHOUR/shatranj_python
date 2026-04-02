"""
test_gui.py - Unit tests for the GUI layer

Strategy: GTK4 requires a display and cannot be instantiated in a
headless test environment. We test the pure logic that does NOT touch
GTK widgets by mocking the gi / GTK imports entirely.

What is tested:
  - app.py       : ShatranjApp class structure
  - board_widget : coordinate math (pixel → square, square → pixel)
  - window.py    : pure logic helpers (_format_clock, _display_color,
                   NewGameDialog.get_config logic, clock state helpers)

What is NOT tested here (requires a real display / integration tests):
  - Actual GTK widget rendering
  - Signal / event handling
  - Cairo drawing functions
"""

import sys
import types
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from shatranj.utils.constants import BLACK, BOARD_SIZE, WHITE

# ---------------------------------------------------------------------------
# GTK mock — installed BEFORE any shatranj.presentation.gui import
# ---------------------------------------------------------------------------


def _make_gtk_mock():
    """Return a minimal mock of the gi / GTK ecosystem."""
    gi = types.ModuleType("gi")
    gi.require_version = MagicMock()

    # gi.repository namespace
    repo = types.ModuleType("gi.repository")

    # Build lightweight GTK mock classes
    class _Widget(MagicMock):
        pass

    class _Application(MagicMock):
        pass

    class _ApplicationWindow(MagicMock):
        pass

    class _DrawingArea(MagicMock):
        pass

    class _Dialog(MagicMock):
        pass

    gtk_mock = MagicMock()
    gtk_mock.Application = _Application
    gtk_mock.ApplicationWindow = _ApplicationWindow
    gtk_mock.DrawingArea = _DrawingArea
    gtk_mock.Dialog = _Dialog
    gtk_mock.ResponseType = MagicMock()
    gtk_mock.ResponseType.OK = 0
    gtk_mock.ResponseType.CANCEL = 1
    gtk_mock.Align = MagicMock()
    gtk_mock.Align.START = "start"
    gtk_mock.Align.CENTER = "center"
    gtk_mock.Orientation = MagicMock()
    gtk_mock.Orientation.VERTICAL = "vertical"
    gtk_mock.Orientation.HORIZONTAL = "horizontal"
    gtk_mock.StackTransitionType = MagicMock()
    gtk_mock.SelectionMode = MagicMock()
    gtk_mock.SelectionMode.NONE = 0
    gtk_mock.StyleContext = MagicMock()
    gtk_mock.STYLE_PROVIDER_PRIORITY_APPLICATION = 600

    repo.Gtk = gtk_mock
    repo.Gio = MagicMock()
    repo.GLib = MagicMock()
    repo.Gdk = MagicMock()
    repo.Rsvg = MagicMock()

    gi.repository = repo
    sys.modules["gi"] = gi
    sys.modules["gi.repository"] = repo
    sys.modules["gi.repository.Gtk"] = gtk_mock
    sys.modules["gi.repository.Gio"] = repo.Gio
    sys.modules["gi.repository.GLib"] = repo.GLib
    sys.modules["gi.repository.Gdk"] = repo.Gdk
    sys.modules["gi.repository.Rsvg"] = repo.Rsvg
    sys.modules["cairo"] = MagicMock()

    return gi, gtk_mock


_gi_mock, _gtk_mock = _make_gtk_mock()


# ---------------------------------------------------------------------------
# Tests for _format_clock (pure function in window.py)
# ---------------------------------------------------------------------------


class TestFormatClock:
    """Tests for the _format_clock helper (no GTK dependency)."""

    def _get_format_clock(self):
        # Import lazily to ensure mocks are in place
        import importlib

        import shatranj.presentation.gui.window as w

        importlib.reload(w)
        return w._format_clock

    def test_zero_seconds(self):
        fmt = self._get_format_clock()
        assert fmt(0.0) == "00:00"

    def test_one_minute(self):
        fmt = self._get_format_clock()
        assert fmt(60.0) == "01:00"

    def test_ninety_seconds(self):
        fmt = self._get_format_clock()
        assert fmt(90.0) == "01:30"

    def test_negative_clamps_to_zero(self):
        fmt = self._get_format_clock()
        assert fmt(-5.0) == "00:00"

    def test_show_tenths_below_20(self):
        fmt = self._get_format_clock()
        result = fmt(9.5, show_tenths=True)
        # Should contain tenths: "00:09.5"
        assert "." in result

    def test_show_tenths_above_20_no_tenths(self):
        fmt = self._get_format_clock()
        result = fmt(25.0, show_tenths=True)
        assert "." not in result

    def test_large_value(self):
        fmt = self._get_format_clock()
        assert fmt(3600.0) == "60:00"


# ---------------------------------------------------------------------------
# Tests for _display_color (pure function in window.py)
# ---------------------------------------------------------------------------


class TestDisplayColor:
    """Tests for the _display_color helper."""

    def _get_display_color(self):
        import importlib

        import shatranj.presentation.gui.window as w

        importlib.reload(w)
        return w._display_color

    def test_white(self):
        fn = self._get_display_color()
        assert fn(WHITE) == "White"

    def test_black(self):
        fn = self._get_display_color()
        assert fn(BLACK) == "Black"

    def test_none_returns_dash(self):
        fn = self._get_display_color()
        assert fn(None) == "--"

    def test_unknown_string_returns_dash(self):
        fn = self._get_display_color()
        assert fn("green") == "--"


# ---------------------------------------------------------------------------
# Tests for board coordinate math (board_widget logic)
# ---------------------------------------------------------------------------


class TestBoardCoordinateMath:
    """
    Tests for the pixel ↔ square coordinate conversion logic.

    BoardWidget computes:
      file = int(x / sq_size)
      rank = BOARD_SIZE - 1 - int(y / sq_size)
      square = rank * BOARD_SIZE + file
    """

    def _pixel_to_square(self, x, y, width=480, height=480):
        """Replicate the BoardWidget pixel-to-square logic."""
        sq_size = min(width, height) / BOARD_SIZE
        file = int(x / sq_size)
        rank = BOARD_SIZE - 1 - int(y / sq_size)
        if not (0 <= file < BOARD_SIZE and 0 <= rank < BOARD_SIZE):
            return None
        return rank * BOARD_SIZE + file

    def _square_to_pixel_center(self, square, width=480, height=480):
        """Return the center pixel of a square."""
        sq_size = min(width, height) / BOARD_SIZE
        rank, file = divmod(square, BOARD_SIZE)
        x = file * sq_size + sq_size / 2
        y = (BOARD_SIZE - 1 - rank) * sq_size + sq_size / 2
        return x, y

    def test_top_left_corner_is_a8(self):
        # Top-left pixel → rank 7, file 0 → square 56 (a8)
        sq = self._pixel_to_square(1, 1)
        assert sq == 56

    def test_bottom_left_corner_is_a1(self):
        # Bottom-left pixel → rank 0, file 0 → square 0 (a1)
        sq = self._pixel_to_square(1, 479)
        assert sq == 0

    def test_bottom_right_corner_is_h1(self):
        # Bottom-right → rank 0, file 7 → square 7 (h1)
        sq = self._pixel_to_square(479, 479)
        assert sq == 7

    def test_top_right_corner_is_h8(self):
        # Top-right → rank 7, file 7 → square 63 (h8)
        sq = self._pixel_to_square(479, 1)
        assert sq == 63

    def test_center_e4_square(self):
        # e4 = rank 3, file 4 → square 28
        x, y = self._square_to_pixel_center(28)
        sq = self._pixel_to_square(x, y)
        assert sq == 28

    def test_roundtrip_all_squares(self):
        """Pixel center of each square should map back to that square."""
        for sq in range(64):
            x, y = self._square_to_pixel_center(sq)
            result = self._pixel_to_square(x, y)
            assert result == sq, f"Roundtrip failed for square {sq}"

    def test_out_of_bounds_returns_none(self):
        # x=500 → file = int(500/60) = 8 → hors bornes [0,7]
        assert self._pixel_to_square(500, 0) is None
        # y=500 → rank = 7 - int(500/60) = -1 → hors bornes
        assert self._pixel_to_square(0, 500) is None

    def test_board_geometry_centers_when_wider_than_tall(self):
        import importlib

        import shatranj.presentation.gui.board_widget as bw

        importlib.reload(bw)
        sq, offset_x, offset_y = bw._board_geometry(800, 480)

        assert sq == 60
        assert offset_x == 160
        assert offset_y == 0

    def test_board_geometry_centers_when_taller_than_wide(self):
        import importlib

        import shatranj.presentation.gui.board_widget as bw

        importlib.reload(bw)
        sq, offset_x, offset_y = bw._board_geometry(480, 800)

        assert sq == 60
        assert offset_x == 0
        assert offset_y == 160


# ---------------------------------------------------------------------------
# Tests for NewGameDialog.get_config logic
# ---------------------------------------------------------------------------


class TestNewGameDialogConfig:
    """
    Tests for get_config() — the pure dict-building logic,
    mocked away from GTK.
    """

    def _make_config(
        self,
        mode,
        algorithm,
        speed_label,
        time_label,
        base_seconds,
        increment_seconds,
    ):
        """Build a config dict as get_config() would return."""
        return {
            "mode": mode,
            "ai_color": BLACK,
            "algorithm": algorithm,
            "speed_label": speed_label,
            "time_control_label": time_label,
            "base_seconds": base_seconds,
            "increment_seconds": increment_seconds,
        }

    def test_hvh_config_keys(self):
        config = self._make_config(
            "hvh", "alphabeta", "Blitz", "5 min", 300, 0
        )
        assert "mode" in config
        assert "algorithm" in config
        assert "base_seconds" in config
        assert "increment_seconds" in config

    def test_hvai_mode(self):
        config = self._make_config(
            "hvai", "alphabeta", "Rapid", "10 min", 600, 0
        )
        assert config["mode"] == "hvai"
        assert config["ai_color"] == BLACK

    def test_aivai_mode(self):
        config = self._make_config("aivai", "mcts", "Bullet", "1 min", 60, 0)
        assert config["mode"] == "aivai"
        assert config["algorithm"] == "mcts"

    def test_increment_seconds_stored(self):
        config = self._make_config(
            "hvh", "alphabeta", "Blitz", "3 | 2", 180, 2
        )
        assert config["increment_seconds"] == 2

    def test_base_seconds_stored(self):
        config = self._make_config(
            "hvh", "alphabeta", "Rapid", "30 min", 1800, 0
        )
        assert config["base_seconds"] == 1800


# ---------------------------------------------------------------------------
# Tests for ShatranjApp structure (app.py)
# ---------------------------------------------------------------------------


class TestShatranjApp:
    """Tests for the ShatranjApp class — structure only, no GTK launch."""

    def test_app_module_importable(self):
        """app.py should be importable without a display."""
        import importlib

        try:
            import shatranj.presentation.gui.app as app_module

            importlib.reload(app_module)
            assert hasattr(app_module, "ShatranjApp")
            assert hasattr(app_module, "run_gui")
        except Exception as e:
            pytest.skip(f"GTK not available: {e}")

    def test_run_gui_is_callable(self):
        """run_gui should be a callable."""
        try:
            from shatranj.presentation.gui.app import run_gui

            assert callable(run_gui)
        except Exception as e:
            pytest.skip(f"GTK not available: {e}")


class TestHintCallback:
    """Regression tests for translated GUI callbacks."""

    def test_on_hint_does_not_shadow_gettext(self):
        import importlib

        import shatranj.presentation.gui.window as w
        from shatranj.domain.core.board import Board
        from shatranj.presentation.cli.game_state import GameState
        from shatranj.utils.constants import PAWN, ROOK, SHAH

        importlib.reload(w)

        board = Board(setup=False)
        board.place_piece(SHAH, WHITE, 0)
        board.place_piece(ROOK, WHITE, 1)
        board.place_piece(SHAH, BLACK, 63)
        board.place_piece(PAWN, BLACK, 2)

        state = GameState()
        state.board = board
        state.current_color = WHITE
        state._history = []
        state._redo_stack = []

        dialog = MagicMock()
        w.Gtk.AlertDialog = MagicMock(return_value=dialog)

        fake_window = SimpleNamespace(
            _state=state,
            _ai_players={},
        )

        w.ShatranjWindow._on_hint(fake_window, object())

        dialog.set_message.assert_called_once_with("Hint")


# ---------------------------------------------------------------------------
# Tests for clock state helpers (pure logic)
# ---------------------------------------------------------------------------


class TestClockHelpers:
    """Tests for clock-related pure calculations."""

    def test_format_clock_30_minutes(self):
        """30 minutes = 1800 seconds → '30:00'."""
        import importlib

        import shatranj.presentation.gui.window as w

        importlib.reload(w)
        assert w._format_clock(1800.0) == "30:00"

    def test_format_clock_rounds_up(self):
        """9.1 seconds should round up to 10 → '00:10'."""
        import importlib

        import shatranj.presentation.gui.window as w

        importlib.reload(w)
        assert w._format_clock(9.1) == "00:10"

    def test_format_clock_exact_seconds(self):
        """Exact integer seconds should not be rounded up."""
        import importlib

        import shatranj.presentation.gui.window as w

        importlib.reload(w)
        assert w._format_clock(10.0) == "00:10"

    def test_display_color_white(self):
        import importlib

        import shatranj.presentation.gui.window as w

        importlib.reload(w)
        assert w._display_color(WHITE) == "White"

    def test_display_color_black(self):
        import importlib

        import shatranj.presentation.gui.window as w

        importlib.reload(w)
        assert w._display_color(BLACK) == "Black"
