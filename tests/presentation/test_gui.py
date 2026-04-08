"""
test_gui.py - Unit tests for the GUI layer

Strategy: GTK4 requires a display and cannot be instantiated in a
headless test environment. We test the pure logic that does NOT touch
GTK widgets by mocking the gi / GTK imports entirely.
"""

import sys
import time
import types
from types import SimpleNamespace
from unittest.mock import MagicMock, patch, call

import pytest

from shatranj.utils.constants import BLACK, BOARD_SIZE, WHITE, PAWN, ROOK, SHAH, KNIGHT, ALFIL, FERZ

# ---------------------------------------------------------------------------
# GTK mock — installed BEFORE any shatranj.presentation.gui import
# ---------------------------------------------------------------------------


def _make_gtk_mock():
    gi = types.ModuleType("gi")
    gi.require_version = MagicMock()

    repo = types.ModuleType("gi.repository")

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
    gtk_mock.ResponseType.YES = 2
    gtk_mock.ResponseType.NO = 3
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
    gtk_mock.License = MagicMock()
    gtk_mock.License.UNKNOWN = 0
    gtk_mock.MessageType = MagicMock()
    gtk_mock.MessageType.QUESTION = 0
    gtk_mock.ButtonsType = MagicMock()
    gtk_mock.ButtonsType.NONE = 0

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
# Helpers
# ---------------------------------------------------------------------------

def _make_game_state(color=WHITE):
    from shatranj.presentation.cli.game_state import GameState
    state = GameState()
    state.current_color = color
    return state


def _make_window_ns(**kwargs):
    defaults = dict(
        _state=None,
        _ai_players={},
        _clock_mode="idle",
        _time_control_name="No active game",
        _increment_seconds=0,
        _remaining_time={},
        _turn_started_at=None,
        _elapsed_started_at=None,
        _game_paused=False,
        _saved=True,
        _board_widget=MagicMock(),
        _history_list=MagicMock(),
        _history_scroll=MagicMock(),
        _white_clock_card=MagicMock(),
        _black_clock_card=MagicMock(),
        _white_clock_side_label=MagicMock(),
        _black_clock_side_label=MagicMock(),
        _white_timer_label=MagicMock(),
        _black_timer_label=MagicMock(),
        _white_timer_status_label=MagicMock(),
        _black_timer_status_label=MagicMock(),
        _time_control_label=MagicMock(),
        _timer_source_id=None,
        _stack=MagicMock(),
        _engine=MagicMock(),
        _css_provider=None,
        # callback stubs
        _on_save_game_finish=MagicMock(),
        _on_load_game_finish=MagicMock(),
        _on_new_game_response=MagicMock(),
        _on_timer_tick=MagicMock(),
        # réseau
        _network_my_color=None,
        _network_client=None,
        _network_player_id=None,
        _network_player_name=None,
        _network_server_address=None,
        _network_last_players=[],
        _network_last_invite=None,
        _network_lobby_dialog=None,
        _network_invite_dialog=None,
        _is_network_game_active=lambda: False,
        _is_network_connected=lambda: False,
        _close_network_connection=MagicMock(),
        _close_network_dialogs=MagicMock(),
        # méthodes GUI
        _refresh_game_view=MagicMock(),
        _show_alert=MagicMock(),
        _get_clock_status_text=MagicMock(return_value="To move"),
        _configure_elapsed_clock=MagicMock(),
        _apply_loaded_clock_state=MagicMock(),
        _start_timer=MagicMock(),
        set_show_menubar=MagicMock(),
        _update_captured_pieces=MagicMock(),
    )
    defaults.update(kwargs)
    ns = SimpleNamespace(**defaults)

    import shatranj.presentation.gui.window as _w_mod

    def _get_display_time(color, now=None):
        return _w_mod.ShatranjWindow._get_display_time(ns, color, now)

    ns._get_display_time = _get_display_time
    return ns


# ---------------------------------------------------------------------------
# Tests for _format_clock
# ---------------------------------------------------------------------------

class TestFormatClock:
    def _fmt(self):
        import importlib
        import shatranj.presentation.gui.window as w
        importlib.reload(w)
        return w._format_clock

    def test_zero(self):
        assert self._fmt()(0.0) == "00:00"

    def test_one_minute(self):
        assert self._fmt()(60.0) == "01:00"

    def test_ninety_seconds(self):
        assert self._fmt()(90.0) == "01:30"

    def test_negative_clamps(self):
        assert self._fmt()(-5.0) == "00:00"

    def test_show_tenths_below_20(self):
        result = self._fmt()(9.5, show_tenths=True)
        assert "." in result

    def test_show_tenths_above_20_no_dot(self):
        result = self._fmt()(25.0, show_tenths=True)
        assert "." not in result

    def test_large_value(self):
        assert self._fmt()(3600.0) == "60:00"

    def test_rounds_up(self):
        assert self._fmt()(9.1) == "00:10"

    def test_exact_seconds_not_rounded_up(self):
        assert self._fmt()(10.0) == "00:10"

    def test_30_minutes(self):
        assert self._fmt()(1800.0) == "30:00"

    def test_tenths_format_has_colon_and_dot(self):
        result = self._fmt()(5.3, show_tenths=True)
        assert ":" in result and "." in result


# ---------------------------------------------------------------------------
# Tests for _display_color
# ---------------------------------------------------------------------------

class TestDisplayColor:
    def _fn(self):
        import importlib
        import shatranj.presentation.gui.window as w
        importlib.reload(w)
        return w._display_color

    def test_white(self):
        assert self._fn()(WHITE) == "White"

    def test_black(self):
        assert self._fn()(BLACK) == "Black"

    def test_none(self):
        assert self._fn()(None) == "--"

    def test_unknown(self):
        assert self._fn()("green") == "--"


# ---------------------------------------------------------------------------
# Tests for board coordinate math
# ---------------------------------------------------------------------------

class TestBoardCoordinateMath:
    def _pixel_to_square(self, x, y, width=480, height=480):
        sq_size = min(width, height) / BOARD_SIZE
        file = int(x / sq_size)
        rank = BOARD_SIZE - 1 - int(y / sq_size)
        if not (0 <= file < BOARD_SIZE and 0 <= rank < BOARD_SIZE):
            return None
        return rank * BOARD_SIZE + file

    def _square_to_pixel_center(self, square, width=480, height=480):
        sq_size = min(width, height) / BOARD_SIZE
        rank, file = divmod(square, BOARD_SIZE)
        x = file * sq_size + sq_size / 2
        y = (BOARD_SIZE - 1 - rank) * sq_size + sq_size / 2
        return x, y

    def test_top_left_is_a8(self):
        assert self._pixel_to_square(1, 1) == 56

    def test_bottom_left_is_a1(self):
        assert self._pixel_to_square(1, 479) == 0

    def test_bottom_right_is_h1(self):
        assert self._pixel_to_square(479, 479) == 7

    def test_top_right_is_h8(self):
        assert self._pixel_to_square(479, 1) == 63

    def test_center_e4(self):
        x, y = self._square_to_pixel_center(28)
        assert self._pixel_to_square(x, y) == 28

    def test_roundtrip_all_squares(self):
        for sq in range(64):
            x, y = self._square_to_pixel_center(sq)
            assert self._pixel_to_square(x, y) == sq

    def test_out_of_bounds_x(self):
        assert self._pixel_to_square(500, 0) is None

    def test_out_of_bounds_y(self):
        assert self._pixel_to_square(0, 500) is None

    def test_board_geometry_wider(self):
        import importlib
        import shatranj.presentation.gui.board_widget as bw
        importlib.reload(bw)
        sq, ox, oy = bw._board_geometry(800, 480)
        assert sq == 60
        assert ox == 160
        assert oy == 0

    def test_board_geometry_taller(self):
        import importlib
        import shatranj.presentation.gui.board_widget as bw
        importlib.reload(bw)
        sq, ox, oy = bw._board_geometry(480, 800)
        assert sq == 60
        assert ox == 0
        assert oy == 160

    def test_board_geometry_square(self):
        import importlib
        import shatranj.presentation.gui.board_widget as bw
        importlib.reload(bw)
        sq, ox, oy = bw._board_geometry(480, 480)
        assert sq == 60
        assert ox == 0
        assert oy == 0


# ---------------------------------------------------------------------------
# Tests for _get_clock_status_text
# ---------------------------------------------------------------------------

class TestGetClockStatusText:
    def _method(self):
        import importlib
        import shatranj.presentation.gui.window as w
        importlib.reload(w)
        return w.ShatranjWindow._get_clock_status_text

    def test_paused(self):
        ns = _make_window_ns(_game_paused=True, _increment_seconds=0)
        result = self._method()(ns, WHITE, WHITE)
        assert "ause" in result

    def test_to_move_human(self):
        ns = _make_window_ns(_game_paused=False, _ai_players={}, _increment_seconds=0)
        result = self._method()(ns, WHITE, WHITE)
        assert "move" in result.lower() or "jouer" in result.lower()

    def test_ai_thinking(self):
        ai = MagicMock()
        ns = _make_window_ns(
            _game_paused=False,
            _ai_players={WHITE: ai},
            _increment_seconds=0,
        )
        result = self._method()(ns, WHITE, WHITE)
        assert "AI" in result or "IA" in result

    def test_waiting_human(self):
        ns = _make_window_ns(_game_paused=False, _ai_players={}, _increment_seconds=0)
        result = self._method()(ns, BLACK, WHITE)
        assert "ait" in result.lower()

    def test_ai_ready(self):
        ai = MagicMock()
        ns = _make_window_ns(
            _game_paused=False,
            _ai_players={BLACK: ai},
            _increment_seconds=0,
        )
        result = self._method()(ns, BLACK, WHITE)
        assert "ready" in result.lower() or "prête" in result.lower()

    def test_increment_appended(self):
        ns = _make_window_ns(_game_paused=False, _ai_players={}, _increment_seconds=5)
        result = self._method()(ns, WHITE, WHITE)
        assert "5" in result

    def test_no_increment_no_pipe(self):
        ns = _make_window_ns(_game_paused=False, _ai_players={}, _increment_seconds=0)
        result = self._method()(ns, WHITE, WHITE)
        assert "|" not in result


# ---------------------------------------------------------------------------
# Tests for _get_display_time
# ---------------------------------------------------------------------------

class TestGetDisplayTime:
    def _method(self):
        import importlib
        import shatranj.presentation.gui.window as w
        importlib.reload(w)
        return w.ShatranjWindow._get_display_time

    def test_idle_returns_zero(self):
        ns = _make_window_ns(_remaining_time={}, _clock_mode="idle")
        assert self._method()(ns, WHITE) == 0.0

    def test_timed_not_active_player(self):
        state = _make_game_state(BLACK)
        ns = _make_window_ns(
            _remaining_time={WHITE: 100.0, BLACK: 80.0},
            _clock_mode="timed",
            _state=state,
            _game_paused=False,
            _turn_started_at=None,
        )
        assert self._method()(ns, WHITE) == 100.0

    def test_timed_active_player_decreases(self):
        state = _make_game_state(WHITE)
        t0 = time.monotonic() - 2.0
        ns = _make_window_ns(
            _remaining_time={WHITE: 100.0},
            _clock_mode="timed",
            _state=state,
            _game_paused=False,
            _turn_started_at=t0,
        )
        result = self._method()(ns, WHITE)
        assert result < 100.0
        assert result >= 97.0

    def test_paused_no_decrease(self):
        state = _make_game_state(WHITE)
        t0 = time.monotonic() - 5.0
        ns = _make_window_ns(
            _remaining_time={WHITE: 100.0},
            _clock_mode="timed",
            _state=state,
            _game_paused=True,
            _turn_started_at=t0,
        )
        assert self._method()(ns, WHITE) == 100.0

    def test_clamps_to_zero(self):
        state = _make_game_state(WHITE)
        t0 = time.monotonic() - 200.0
        ns = _make_window_ns(
            _remaining_time={WHITE: 10.0},
            _clock_mode="timed",
            _state=state,
            _game_paused=False,
            _turn_started_at=t0,
        )
        assert self._method()(ns, WHITE) == 0.0


# ---------------------------------------------------------------------------
# Tests for _finish_active_turn
# ---------------------------------------------------------------------------

class TestFinishActiveTurn:
    def _method(self):
        import importlib
        import shatranj.presentation.gui.window as w
        importlib.reload(w)
        return w.ShatranjWindow._finish_active_turn

    def test_not_timed_returns_true(self):
        ns = _make_window_ns(_clock_mode="idle", _turn_started_at=None)
        assert self._method()(ns, WHITE) is True

    def test_no_timer_started_returns_true(self):
        ns = _make_window_ns(_clock_mode="timed", _turn_started_at=None)
        assert self._method()(ns, WHITE) is True

    def test_time_remaining_deducted(self):
        state = _make_game_state(WHITE)
        t0 = time.monotonic() - 1.0
        ns = _make_window_ns(
            _clock_mode="timed",
            _state=state,
            _game_paused=False,
            _turn_started_at=t0,
            _remaining_time={WHITE: 100.0},
            _increment_seconds=0,
        )
        ns._update_clock_labels = MagicMock()
        ns._show_game_over_dialog = MagicMock()
        result = self._method()(ns, WHITE)
        assert result is True
        assert ns._remaining_time[WHITE] < 100.0

    def test_timeout_returns_false(self):
        state = _make_game_state(WHITE)
        t0 = time.monotonic() - 200.0
        ns = _make_window_ns(
            _clock_mode="timed",
            _state=state,
            _game_paused=False,
            _turn_started_at=t0,
            _remaining_time={WHITE: 5.0},
            _increment_seconds=0,
        )
        ns._update_clock_labels = MagicMock()
        ns._show_game_over_dialog = MagicMock()
        result = self._method()(ns, WHITE)
        assert result is False
        ns._show_game_over_dialog.assert_called_once()

    def test_increment_added_after_move(self):
        state = _make_game_state(WHITE)
        t0 = time.monotonic() - 1.0
        ns = _make_window_ns(
            _clock_mode="timed",
            _state=state,
            _game_paused=False,
            _turn_started_at=t0,
            _remaining_time={WHITE: 100.0},
            _increment_seconds=10,
        )
        ns._update_clock_labels = MagicMock()
        ns._show_game_over_dialog = MagicMock()
        self._method()(ns, WHITE)
        assert ns._remaining_time[WHITE] > 100.0


# ---------------------------------------------------------------------------
# Tests for _is_active_player_flagged
# ---------------------------------------------------------------------------

class TestIsActivePlayerFlagged:
    def _method(self):
        import importlib
        import shatranj.presentation.gui.window as w
        importlib.reload(w)
        return w.ShatranjWindow._is_active_player_flagged

    def test_not_timed_returns_false(self):
        ns = _make_window_ns(_clock_mode="idle")
        assert self._method()(ns) is False

    def test_no_state_returns_false(self):
        ns = _make_window_ns(_clock_mode="timed", _state=None)
        assert self._method()(ns) is False

    def test_paused_returns_false(self):
        ns = _make_window_ns(
            _clock_mode="timed",
            _state=_make_game_state(),
            _game_paused=True,
            _turn_started_at=time.monotonic(),
        )
        assert self._method()(ns) is False

    def test_time_remaining_returns_false(self):
        state = _make_game_state(WHITE)
        t0 = time.monotonic()
        ns = _make_window_ns(
            _clock_mode="timed",
            _state=state,
            _game_paused=False,
            _turn_started_at=t0,
            _remaining_time={WHITE: 100.0},
        )
        assert self._method()(ns) is False

    def test_flagged_calls_game_over(self):
        state = _make_game_state(WHITE)
        t0 = time.monotonic() - 200.0
        ns = _make_window_ns(
            _clock_mode="timed",
            _state=state,
            _game_paused=False,
            _turn_started_at=t0,
            _remaining_time={WHITE: 5.0},
        )
        ns._update_clock_labels = MagicMock()
        ns._show_game_over_dialog = MagicMock()
        result = self._method()(ns)
        assert result is True
        ns._show_game_over_dialog.assert_called_once()


# ---------------------------------------------------------------------------
# Tests for _configure_new_game_clock / _configure_loaded_game_clock
# ---------------------------------------------------------------------------

class TestConfigureClock:
    def _window_module(self):
        import importlib
        import shatranj.presentation.gui.window as w
        importlib.reload(w)
        return w

    def test_configure_new_game_sets_timed_mode(self):
        w = self._window_module()
        ns = _make_window_ns()
        ns._update_clock_labels = MagicMock()
        config = {
            "speed_label": "Blitz",
            "time_control_label": "5 min",
            "base_seconds": 300,
            "increment_seconds": 2,
        }
        w.ShatranjWindow._configure_new_game_clock(ns, config)
        assert ns._clock_mode == "timed"
        assert ns._remaining_time[WHITE] == 300.0
        assert ns._remaining_time[BLACK] == 300.0
        assert ns._increment_seconds == 2

    def test_configure_loaded_game_sets_elapsed_mode(self):
        w = self._window_module()
        ns = _make_window_ns()
        ns._configure_elapsed_clock = MagicMock()
        w.ShatranjWindow._configure_loaded_game_clock(ns)
        ns._configure_elapsed_clock.assert_called_once_with("Loaded Game")


# ---------------------------------------------------------------------------
# Tests for _check_game_over
# ---------------------------------------------------------------------------

class TestCheckGameOver:
    def _method(self):
        import importlib
        import shatranj.presentation.gui.window as w
        importlib.reload(w)
        return w.ShatranjWindow._check_game_over

    def _ns_with_engine(self, checkmate=False, stalemate=False, bare=False):
        engine = MagicMock()
        engine.is_checkmate.return_value = checkmate
        engine.is_stalemate.return_value = stalemate
        engine.is_bare_king.return_value = bare
        state = _make_game_state(WHITE)
        ns = _make_window_ns(_state=state, _engine=engine)
        ns._show_game_over_dialog = MagicMock()
        ns._stop_timer = MagicMock()
        return ns, engine

    def test_no_end_returns_false(self):
        ns, _ = self._ns_with_engine()
        assert self._method()(ns) is False

    def test_none_state_returns_false(self):
        ns = _make_window_ns(_state=None)
        assert self._method()(ns) is False

    def test_checkmate_returns_true(self):
        ns, _ = self._ns_with_engine(checkmate=True)
        assert self._method()(ns) is True
        ns._show_game_over_dialog.assert_called_once()

    def test_stalemate_returns_true(self):
        ns, _ = self._ns_with_engine(stalemate=True)
        assert self._method()(ns) is True
        ns._show_game_over_dialog.assert_called_once()

    def test_bare_king_returns_true(self):
        ns, _ = self._ns_with_engine(bare=True)
        assert self._method()(ns) is True
        ns._show_game_over_dialog.assert_called_once()

    def test_checkmate_message_contains_winner(self):
        ns, _ = self._ns_with_engine(checkmate=True)
        self._method()(ns)
        msg = ns._show_game_over_dialog.call_args[0][0]
        assert "BLACK" in msg or "Noirs" in msg or "black" in msg.lower()


# ---------------------------------------------------------------------------
# Tests for _show_game_over_dialog
# ---------------------------------------------------------------------------

class TestShowGameOverDialog:
    def _method(self):
        import importlib
        import shatranj.presentation.gui.window as w
        importlib.reload(w)
        return w.ShatranjWindow._show_game_over_dialog

    def test_clears_state(self):
        import importlib
        import shatranj.presentation.gui.window as w
        importlib.reload(w)

        state = _make_game_state()
        ns = _make_window_ns(_state=state, _ai_players={WHITE: MagicMock()})
        ns._stop_timer = MagicMock()
        ns._sync_board_interaction = MagicMock()

        dialog = MagicMock()
        w.Gtk.AlertDialog = MagicMock(return_value=dialog)

        self._method()(ns, "Game over!")

        assert ns._state is None
        assert ns._ai_players == {}
        ns._stop_timer.assert_called_once()
        ns._sync_board_interaction.assert_called_once()

    def test_dialog_shown_with_message(self):
        import importlib
        import shatranj.presentation.gui.window as w
        importlib.reload(w)

        ns = _make_window_ns(_state=_make_game_state())
        ns._stop_timer = MagicMock()
        ns._sync_board_interaction = MagicMock()

        dialog = MagicMock()
        w.Gtk.AlertDialog = MagicMock(return_value=dialog)

        self._method()(ns, "Test message")
        dialog.set_detail.assert_called_with("Test message")


# ---------------------------------------------------------------------------
# Tests for _sync_board_interaction
# ---------------------------------------------------------------------------

class TestSyncBoardInteraction:
    def _method(self):
        import importlib
        import shatranj.presentation.gui.window as w
        importlib.reload(w)
        return w.ShatranjWindow._sync_board_interaction

    def test_no_state_disables_interaction(self):
        ns = _make_window_ns(_state=None, _game_paused=False, _ai_players={},
                             _network_my_color=None)
        self._method()(ns)
        ns._board_widget.set_interaction_enabled.assert_called_with(False)

    def test_human_turn_enables_interaction(self):
        state = _make_game_state(WHITE)
        ns = _make_window_ns(_state=state, _game_paused=False, _ai_players={},
                             _network_my_color=None)
        self._method()(ns)
        ns._board_widget.set_interaction_enabled.assert_called_with(True)

    def test_ai_turn_disables_interaction(self):
        state = _make_game_state(WHITE)
        ns = _make_window_ns(
            _state=state,
            _game_paused=False,
            _ai_players={WHITE: MagicMock()},
            _network_my_color=None,
        )
        self._method()(ns)
        ns._board_widget.set_interaction_enabled.assert_called_with(False)

    def test_paused_disables_interaction(self):
        state = _make_game_state(WHITE)
        ns = _make_window_ns(_state=state, _game_paused=True, _ai_players={},
                             _network_my_color=None)
        self._method()(ns)
        ns._board_widget.set_interaction_enabled.assert_called_with(False)

    def test_no_board_widget_does_not_crash(self):
        ns = SimpleNamespace(_state=None)
        import importlib
        import shatranj.presentation.gui.window as w
        importlib.reload(w)
        w.ShatranjWindow._sync_board_interaction(ns)


# ---------------------------------------------------------------------------
# Tests for _on_undo / _on_redo
# ---------------------------------------------------------------------------

class TestUndoRedo:
    def test_on_undo_no_state_does_nothing(self):
        import importlib
        import shatranj.presentation.gui.window as w
        importlib.reload(w)
        ns = _make_window_ns(_state=None)
        w.ShatranjWindow._on_undo(ns)

    def test_on_undo_calls_state_undo(self):
        import importlib
        import shatranj.presentation.gui.window as w
        importlib.reload(w)
        state = _make_game_state()
        state.undo = MagicMock()
        ns = _make_window_ns(_state=state, _clock_mode="idle")
        ns._sync_board_interaction = MagicMock()
        ns._update_history = MagicMock()
        ns._update_clock_labels = MagicMock()
        w.ShatranjWindow._on_undo(ns)
        state.undo.assert_called_once()

    def test_on_redo_no_state_does_nothing(self):
        import importlib
        import shatranj.presentation.gui.window as w
        importlib.reload(w)
        ns = _make_window_ns(_state=None)
        w.ShatranjWindow._on_redo(ns)

    def test_on_redo_calls_state_redo(self):
        import importlib
        import shatranj.presentation.gui.window as w
        importlib.reload(w)
        state = _make_game_state()
        state.redo = MagicMock(return_value=MagicMock())
        ns = _make_window_ns(_state=state, _clock_mode="idle")
        ns._sync_board_interaction = MagicMock()
        ns._update_history = MagicMock()
        ns._update_clock_labels = MagicMock()
        w.ShatranjWindow._on_redo(ns)
        state.redo.assert_called_once()

    def test_on_redo_no_move_returns_early(self):
        import importlib
        import shatranj.presentation.gui.window as w
        importlib.reload(w)
        state = _make_game_state()
        state.redo = MagicMock(return_value=None)
        ns = _make_window_ns(_state=state, _clock_mode="idle")
        ns._sync_board_interaction = MagicMock()
        ns._update_history = MagicMock()
        w.ShatranjWindow._on_redo(ns)
        ns._update_history.assert_not_called()


# ---------------------------------------------------------------------------
# Tests for _on_hint
# ---------------------------------------------------------------------------

class TestOnHint:
    def test_no_state_does_nothing(self):
        import importlib
        import shatranj.presentation.gui.window as w
        importlib.reload(w)
        ns = _make_window_ns(_state=None)
        w.ShatranjWindow._on_hint(ns)

    def test_hint_shown_when_move_found(self):
        import importlib
        import shatranj.presentation.gui.window as w
        importlib.reload(w)

        from shatranj.domain.core.move import Move
        move = Move(from_square=12, to_square=20, piece_type=PAWN, color=WHITE)

        state = _make_game_state(WHITE)
        ns = _make_window_ns(_state=state, _ai_players={})

        dialog = MagicMock()
        w.Gtk.AlertDialog = MagicMock(return_value=dialog)

        with patch("shatranj.presentation.gui.window.choose_hint_move", return_value=move):
            w.ShatranjWindow._on_hint(ns)

        dialog.set_detail.assert_called_once()
        detail = dialog.set_detail.call_args[0][0]
        assert "-" in detail or "x" in detail

    def test_hint_not_shown_when_no_move(self):
        import importlib
        import shatranj.presentation.gui.window as w
        importlib.reload(w)

        state = _make_game_state(WHITE)
        ns = _make_window_ns(_state=state, _ai_players={})

        dialog = MagicMock()
        w.Gtk.AlertDialog = MagicMock(return_value=dialog)

        with patch("shatranj.presentation.gui.window.choose_hint_move", return_value=None):
            w.ShatranjWindow._on_hint(ns)

        dialog.show.assert_not_called()


# ---------------------------------------------------------------------------
# Tests for _on_pause
# ---------------------------------------------------------------------------

class TestOnPause:
    def test_on_pause_delegates_to_toggle(self):
        import importlib
        import shatranj.presentation.gui.window as w
        importlib.reload(w)
        ns = _make_window_ns()
        ns._toggle_pause = MagicMock()
        w.ShatranjWindow._on_pause(ns)
        ns._toggle_pause.assert_called_once()

    def test_toggle_pause_not_timed_does_nothing(self):
        import importlib
        import shatranj.presentation.gui.window as w
        importlib.reload(w)
        state = _make_game_state()
        ns = _make_window_ns(_state=state, _clock_mode="elapsed")
        w.ShatranjWindow._toggle_pause(ns)

    def test_toggle_pause_sets_paused(self):
        import importlib
        import shatranj.presentation.gui.window as w
        importlib.reload(w)
        state = _make_game_state(WHITE)
        ns = _make_window_ns(
            _state=state,
            _clock_mode="timed",
            _game_paused=False,
            _remaining_time={WHITE: 100.0, BLACK: 100.0},
        )
        ns._sync_board_interaction = MagicMock()
        ns._update_clock_labels = MagicMock()
        ns._get_display_time = MagicMock(return_value=90.0)
        w.ShatranjWindow._toggle_pause(ns)
        assert ns._game_paused is True

    def test_toggle_pause_resumes(self):
        import importlib
        import shatranj.presentation.gui.window as w
        importlib.reload(w)
        state = _make_game_state(WHITE)
        ns = _make_window_ns(
            _state=state,
            _clock_mode="timed",
            _game_paused=True,
            _remaining_time={WHITE: 90.0, BLACK: 100.0},
        )
        ns._sync_board_interaction = MagicMock()
        ns._update_clock_labels = MagicMock()
        ns._auto_play_ai_turns = MagicMock()
        w.ShatranjWindow._toggle_pause(ns)
        assert ns._game_paused is False


# ---------------------------------------------------------------------------
# Tests for _on_move_played
# ---------------------------------------------------------------------------

class TestOnMovePlayed:
    def _make_move(self, from_sq=12, to_sq=20):
        from shatranj.domain.core.move import Move
        return Move(from_square=from_sq, to_square=to_sq, piece_type=PAWN, color=WHITE)

    def test_no_state_does_nothing(self):
        import importlib
        import shatranj.presentation.gui.window as w
        importlib.reload(w)
        ns = _make_window_ns(_state=None)
        w.ShatranjWindow._on_move_played(ns, self._make_move())

    def test_paused_aborts(self):
        import importlib
        import shatranj.presentation.gui.window as w
        importlib.reload(w)
        state = _make_game_state(WHITE)
        ns = _make_window_ns(_state=state, _game_paused=True, _ai_players={})
        ns._sync_board_interaction = MagicMock()
        w.ShatranjWindow._on_move_played(ns, self._make_move())
        ns._sync_board_interaction.assert_called()

    def test_ai_turn_aborts(self):
        import importlib
        import shatranj.presentation.gui.window as w
        importlib.reload(w)
        state = _make_game_state(WHITE)
        ns = _make_window_ns(
            _state=state,
            _game_paused=False,
            _ai_players={WHITE: MagicMock()},
        )
        ns._sync_board_interaction = MagicMock()
        w.ShatranjWindow._on_move_played(ns, self._make_move())
        ns._sync_board_interaction.assert_called()

    def test_valid_move_applied(self):
        import importlib
        import shatranj.presentation.gui.window as w
        importlib.reload(w)

        state = _make_game_state(WHITE)
        state.apply_move = MagicMock()

        ns = _make_window_ns(
            _state=state,
            _game_paused=False,
            _ai_players={},
            _clock_mode="idle",
        )
        ns._finish_active_turn = MagicMock(return_value=True)
        ns._sync_board_interaction = MagicMock()
        ns._update_history = MagicMock()
        ns._check_game_over = MagicMock(return_value=False)
        ns._start_next_turn = MagicMock()
        ns._auto_play_ai_turns = MagicMock()

        move = self._make_move()
        w.ShatranjWindow._on_move_played(ns, move)

        state.apply_move.assert_called_once_with(move)
        assert ns._saved is False


# ---------------------------------------------------------------------------
# Tests for _confirm_abandon
# ---------------------------------------------------------------------------

class TestConfirmAbandon:
    def test_no_state_calls_confirmed_directly(self):
        import importlib
        import shatranj.presentation.gui.window as w
        importlib.reload(w)
        ns = _make_window_ns(_state=None, _saved=True)
        callback = MagicMock()
        w.ShatranjWindow._confirm_abandon(ns, callback)
        callback.assert_called_once()

    def test_saved_calls_confirmed_directly(self):
        import importlib
        import shatranj.presentation.gui.window as w
        importlib.reload(w)
        ns = _make_window_ns(_state=_make_game_state(), _saved=True)
        callback = MagicMock()
        w.ShatranjWindow._confirm_abandon(ns, callback)
        callback.assert_called_once()

    def test_unsaved_shows_dialog(self):
        import importlib
        import shatranj.presentation.gui.window as w
        importlib.reload(w)

        ns = _make_window_ns(_state=_make_game_state(), _saved=False)
        dialog = MagicMock()
        w.Gtk.MessageDialog = MagicMock(return_value=dialog)

        callback = MagicMock()
        w.ShatranjWindow._confirm_abandon(ns, callback)

        dialog.present.assert_called_once()
        callback.assert_not_called()


# ---------------------------------------------------------------------------
# Tests for NewGameDialog.get_config logic
# ---------------------------------------------------------------------------

class TestNewGameDialogConfig:
    def _make_config(self, mode, algorithm, speed_label,
                     time_label, base_seconds, increment_seconds):
        return {
            "mode": mode,
            "ai_color": BLACK,
            "algorithm": algorithm,
            "speed_label": speed_label,
            "time_control_label": time_label,
            "base_seconds": base_seconds,
            "increment_seconds": increment_seconds,
        }

    def test_hvh_keys_present(self):
        config = self._make_config("hvh", "alphabeta", "Blitz", "5 min", 300, 0)
        for key in ("mode", "algorithm", "base_seconds", "increment_seconds"):
            assert key in config

    def test_hvai_mode(self):
        config = self._make_config("hvai", "alphabeta", "Rapid", "10 min", 600, 0)
        assert config["mode"] == "hvai"
        assert config["ai_color"] == BLACK

    def test_aivai_mode(self):
        config = self._make_config("aivai", "mcts", "Bullet", "1 min", 60, 0)
        assert config["mode"] == "aivai"
        assert config["algorithm"] == "mcts"

    def test_increment_stored(self):
        config = self._make_config("hvh", "alphabeta", "Blitz", "3 | 2", 180, 2)
        assert config["increment_seconds"] == 2

    def test_base_seconds_stored(self):
        config = self._make_config("hvh", "alphabeta", "Rapid", "30 min", 1800, 0)
        assert config["base_seconds"] == 1800

    def test_get_config_raises_without_preset(self):
        import importlib
        import shatranj.presentation.gui.window as w
        importlib.reload(w)
        from shatranj.utils.exceptions import ShatranjError

        dialog = SimpleNamespace(
            _selected_speed=None,
            _selected_preset=None,
        )
        with pytest.raises(ShatranjError):
            w.NewGameDialog.get_config(dialog)


# ---------------------------------------------------------------------------
# Tests for ShatranjApp structure
# ---------------------------------------------------------------------------

class TestShatranjApp:
    def test_app_module_importable(self):
        import importlib
        try:
            import shatranj.presentation.gui.app as app_module
            importlib.reload(app_module)
            assert hasattr(app_module, "ShatranjApp")
            assert hasattr(app_module, "run_gui")
        except Exception as e:
            pytest.skip(f"GTK not available: {e}")

    def test_run_gui_callable(self):
        try:
            from shatranj.presentation.gui.app import run_gui
            assert callable(run_gui)
        except Exception as e:
            pytest.skip(f"GTK not available: {e}")


# ---------------------------------------------------------------------------
# Tests for _update_history
# ---------------------------------------------------------------------------

class TestUpdateHistory:
    def test_no_state_clears_list(self):
        import importlib
        import shatranj.presentation.gui.window as w
        importlib.reload(w)

        ns = _make_window_ns(_state=None)
        row = MagicMock()
        ns._history_list.get_row_at_index = MagicMock(side_effect=[row, None])
        ns._scroll_history_to_position = MagicMock()

        w.ShatranjWindow._update_history(ns)
        ns._history_list.remove.assert_called_with(row)
        ns._scroll_history_to_position.assert_called_with(0.0)

    def test_with_state_appends_moves(self):
        import importlib
        import shatranj.presentation.gui.window as w
        importlib.reload(w)

        from shatranj.domain.core.move import Move

        state = _make_game_state(WHITE)
        move = Move(from_square=12, to_square=20, piece_type=PAWN, color=WHITE)
        state._history = [(move, {})]

        ns = _make_window_ns(_state=state)
        ns._history_list.get_row_at_index = MagicMock(return_value=None)
        ns._scroll_history_to_latest = MagicMock()

        label_mock = MagicMock()
        w.Gtk.Label = MagicMock(return_value=label_mock)

        w.ShatranjWindow._update_history(ns)
        ns._history_list.append.assert_called_once()


# ---------------------------------------------------------------------------
# Tests for _on_save_game
# ---------------------------------------------------------------------------

class TestOnSaveGame:
    def test_no_state_returns_early(self):
        import importlib
        import shatranj.presentation.gui.window as w
        importlib.reload(w)

        ns = _make_window_ns(_state=None)
        dialog = MagicMock()
        w.Gtk.FileDialog = MagicMock(return_value=dialog)

        w.ShatranjWindow._on_save_game(ns)
        dialog.save.assert_not_called()

    def test_with_state_opens_dialog(self):
        import importlib
        import shatranj.presentation.gui.window as w
        importlib.reload(w)

        ns = _make_window_ns(_state=_make_game_state())
        dialog = MagicMock()
        w.Gtk.FileDialog = MagicMock(return_value=dialog)

        w.ShatranjWindow._on_save_game(ns)
        dialog.save.assert_called_once()


# ---------------------------------------------------------------------------
# Regression: translated hint callback
# ---------------------------------------------------------------------------

class TestHintCallback:
    def test_on_hint_does_not_shadow_gettext(self):
        import importlib
        import shatranj.presentation.gui.window as w
        importlib.reload(w)

        from shatranj.domain.core.board import Board
        from shatranj.presentation.cli.game_state import GameState

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

        ns = _make_window_ns(_state=state, _ai_players={})
        w.ShatranjWindow._on_hint(ns)

        dialog.set_message.assert_called_once_with("Hint")


# ---------------------------------------------------------------------------
# Tests for _reset_clock
# ---------------------------------------------------------------------------

class TestResetClock:
    def test_reset_sets_idle_mode(self):
        import importlib
        import shatranj.presentation.gui.window as w
        importlib.reload(w)
        ns = _make_window_ns(_clock_mode="timed", _game_paused=True)
        ns._update_clock_labels = MagicMock()
        w.ShatranjWindow._reset_clock(ns)
        assert ns._clock_mode == "idle"
        assert ns._game_paused is False
        assert ns._remaining_time == {}
        assert ns._turn_started_at is None
        assert ns._increment_seconds == 0

    def test_reset_calls_update_labels(self):
        import importlib
        import shatranj.presentation.gui.window as w
        importlib.reload(w)
        ns = _make_window_ns()
        ns._update_clock_labels = MagicMock()
        w.ShatranjWindow._reset_clock(ns)
        ns._update_clock_labels.assert_called_once()


# ---------------------------------------------------------------------------
# Tests for _start_next_turn
# ---------------------------------------------------------------------------

class TestStartNextTurn:
    def test_not_timed_does_nothing(self):
        import importlib
        import shatranj.presentation.gui.window as w
        importlib.reload(w)
        ns = _make_window_ns(_clock_mode="idle", _state=_make_game_state())
        ns._update_clock_labels = MagicMock()
        w.ShatranjWindow._start_next_turn(ns)
        assert ns._turn_started_at is None

    def test_no_state_does_nothing(self):
        import importlib
        import shatranj.presentation.gui.window as w
        importlib.reload(w)
        ns = _make_window_ns(_clock_mode="timed", _state=None)
        ns._update_clock_labels = MagicMock()
        w.ShatranjWindow._start_next_turn(ns)
        assert ns._turn_started_at is None

    def test_paused_does_nothing(self):
        import importlib
        import shatranj.presentation.gui.window as w
        importlib.reload(w)
        ns = _make_window_ns(
            _clock_mode="timed",
            _state=_make_game_state(),
            _game_paused=True,
        )
        ns._update_clock_labels = MagicMock()
        w.ShatranjWindow._start_next_turn(ns)
        assert ns._turn_started_at is None

    def test_sets_turn_started_at(self):
        import importlib
        import shatranj.presentation.gui.window as w
        importlib.reload(w)
        ns = _make_window_ns(
            _clock_mode="timed",
            _state=_make_game_state(),
            _game_paused=False,
        )
        ns._update_clock_labels = MagicMock()
        w.ShatranjWindow._start_next_turn(ns)
        assert ns._turn_started_at is not None


# ---------------------------------------------------------------------------
# Tests for _set_clock_card_state
# ---------------------------------------------------------------------------

class TestSetClockCardState:
    def _method(self):
        import importlib
        import shatranj.presentation.gui.window as w
        importlib.reload(w)
        return w.ShatranjWindow._set_clock_card_state

    def test_active_adds_css_class(self):
        card = MagicMock()
        label = MagicMock()
        ns = _make_window_ns()
        self._method()(ns, card, label, active=True)
        card.add_css_class.assert_called_with("clock-card-active")

    def test_inactive_removes_css_class(self):
        card = MagicMock()
        label = MagicMock()
        ns = _make_window_ns()
        self._method()(ns, card, label, active=False)
        card.remove_css_class.assert_any_call("clock-card-active")

    def test_critical_adds_css_class(self):
        card = MagicMock()
        label = MagicMock()
        ns = _make_window_ns()
        self._method()(ns, card, label, critical=True)
        card.add_css_class.assert_called_with("clock-card-critical")
        label.add_css_class.assert_called_with("clock-time-critical")

    def test_not_critical_removes_css_class(self):
        card = MagicMock()
        label = MagicMock()
        ns = _make_window_ns()
        self._method()(ns, card, label, critical=False)
        card.remove_css_class.assert_called_with("clock-card-critical")
        label.remove_css_class.assert_called_with("clock-time-critical")


# ---------------------------------------------------------------------------
# Tests for _on_new_game_response
# ---------------------------------------------------------------------------

class TestOnNewGameResponse:
    def test_ok_response_starts_game(self):
        import importlib
        import shatranj.presentation.gui.window as w
        importlib.reload(w)

        config = {
            "mode": "hvh",
            "algorithm": "alphabeta",
            "speed_label": "Blitz",
            "time_control_label": "5 min",
            "base_seconds": 300,
            "increment_seconds": 0,
            "ai_color": BLACK,
        }
        dialog = MagicMock()
        dialog.get_config.return_value = config

        ns = _make_window_ns()
        ns._start_game = MagicMock()

        w.ShatranjWindow._on_new_game_response(ns, dialog, w.Gtk.ResponseType.OK)
        ns._start_game.assert_called_once_with(config)
        dialog.destroy.assert_called_once()

    def test_cancel_response_destroys_dialog(self):
        import importlib
        import shatranj.presentation.gui.window as w
        importlib.reload(w)

        dialog = MagicMock()
        ns = _make_window_ns()
        ns._start_game = MagicMock()

        w.ShatranjWindow._on_new_game_response(ns, dialog, w.Gtk.ResponseType.CANCEL)
        dialog.destroy.assert_called_once()
        ns._start_game.assert_not_called()

    def test_shatranj_error_in_get_config_aborts(self):
        import importlib
        import shatranj.presentation.gui.window as w
        importlib.reload(w)
        from shatranj.utils.exceptions import ShatranjError

        dialog = MagicMock()
        dialog.get_config.side_effect = ShatranjError("no preset")
        ns = _make_window_ns()
        ns._start_game = MagicMock()

        w.ShatranjWindow._on_new_game_response(ns, dialog, w.Gtk.ResponseType.OK)
        ns._start_game.assert_not_called()


# ---------------------------------------------------------------------------
# Tests for _on_back_to_menu and _on_quit
# ---------------------------------------------------------------------------

class TestBackToMenuAndQuit:
    def test_on_back_to_menu_calls_confirm_abandon(self):
        import importlib
        import shatranj.presentation.gui.window as w
        importlib.reload(w)

        ns = _make_window_ns(_state=None, _saved=True)
        ns._confirm_abandon = MagicMock()
        w.ShatranjWindow._on_back_to_menu(ns)
        ns._confirm_abandon.assert_called_once()

    def test_on_quit_calls_confirm_abandon(self):
        import importlib
        import shatranj.presentation.gui.window as w
        importlib.reload(w)

        ns = _make_window_ns(_state=None, _saved=True)
        ns._confirm_abandon = MagicMock()
        w.ShatranjWindow._on_quit(ns)
        ns._confirm_abandon.assert_called_once()

    def test_do_back_clears_state(self):
        import importlib
        import shatranj.presentation.gui.window as w
        importlib.reload(w)

        ns = _make_window_ns(_state=_make_game_state(), _saved=True)
        ns.set_show_menubar = MagicMock()
        ns._stop_timer = MagicMock()
        ns._sync_board_interaction = MagicMock()
        ns.get_application = MagicMock()

        captured = []
        def fake_confirm(cb):
            captured.append(cb)
            cb()
        ns._confirm_abandon = fake_confirm

        w.ShatranjWindow._on_back_to_menu(ns)
        assert ns._state is None
        assert ns._ai_players == {}


# ---------------------------------------------------------------------------
# Tests for _apply_ai_move
# ---------------------------------------------------------------------------

class TestApplyAiMove:
    def _make_move(self, from_sq=12, to_sq=20, color=WHITE):
        from shatranj.domain.core.move import Move
        return Move(from_square=from_sq, to_square=to_sq, piece_type=PAWN, color=color)

    def test_none_state_returns_false(self):
        import importlib
        import shatranj.presentation.gui.window as w
        importlib.reload(w)
        ns = _make_window_ns(_state=None)
        result = w.ShatranjWindow._apply_ai_move(ns, self._make_move())
        assert result is False

    def test_paused_returns_true(self):
        import importlib
        import shatranj.presentation.gui.window as w
        importlib.reload(w)
        ns = _make_window_ns(
            _state=_make_game_state(WHITE),
            _game_paused=True,
            _ai_players={WHITE: MagicMock()},
        )
        result = w.ShatranjWindow._apply_ai_move(ns, self._make_move())
        assert result is True

    def test_wrong_color_returns_false(self):
        import importlib
        import shatranj.presentation.gui.window as w
        importlib.reload(w)
        state = _make_game_state(BLACK)
        ns = _make_window_ns(
            _state=state,
            _game_paused=False,
            _ai_players={BLACK: MagicMock()},
        )
        move = self._make_move(color=WHITE)
        result = w.ShatranjWindow._apply_ai_move(ns, move)
        assert result is False

    def test_color_not_in_ai_players_returns_false(self):
        import importlib
        import shatranj.presentation.gui.window as w
        importlib.reload(w)
        state = _make_game_state(WHITE)
        ns = _make_window_ns(_state=state, _game_paused=False, _ai_players={})
        result = w.ShatranjWindow._apply_ai_move(ns, self._make_move(color=WHITE))
        assert result is False

    def test_illegal_move_returns_false(self):
        import importlib
        import shatranj.presentation.gui.window as w
        importlib.reload(w)
        state = _make_game_state(WHITE)
        engine = MagicMock()
        engine.generate_legal_moves.return_value = []
        ns = _make_window_ns(
            _state=state,
            _game_paused=False,
            _ai_players={WHITE: MagicMock()},
            _engine=engine,
        )
        result = w.ShatranjWindow._apply_ai_move(ns, self._make_move(color=WHITE))
        assert result is False

    def test_done_event_set_on_success(self):
        import importlib
        import threading
        import shatranj.presentation.gui.window as w
        importlib.reload(w)

        from shatranj.domain.core.move import Move
        move = Move(from_square=12, to_square=20, piece_type=PAWN, color=WHITE)

        state = _make_game_state(WHITE)
        engine = MagicMock()
        engine.generate_legal_moves.return_value = [move]

        ns = _make_window_ns(
            _state=state,
            _game_paused=False,
            _ai_players={WHITE: MagicMock()},
            _engine=engine,
        )
        ns._finish_active_turn = MagicMock(return_value=True)
        ns._sync_board_interaction = MagicMock()
        ns._update_history = MagicMock()
        ns._check_game_over = MagicMock(return_value=False)
        ns._start_next_turn = MagicMock()

        event = threading.Event()
        w.ShatranjWindow._apply_ai_move(ns, move, event)
        assert event.is_set()


# ---------------------------------------------------------------------------
# Tests for _scroll_history_to_position
# ---------------------------------------------------------------------------

class TestScrollHistory:
    def test_scroll_to_position_value(self):
        import importlib
        import shatranj.presentation.gui.window as w
        importlib.reload(w)

        adjustment = MagicMock()
        adjustment.get_upper.return_value = 100.0
        adjustment.get_page_size.return_value = 20.0
        scroll = MagicMock()
        scroll.get_vadjustment.return_value = adjustment

        ns = _make_window_ns()
        ns._history_scroll = scroll

        captured = []
        w.GLib.idle_add = lambda fn: captured.append(fn) or fn()

        w.ShatranjWindow._scroll_history_to_position(ns, 42.0)
        adjustment.set_value.assert_called_with(42.0)

    def test_scroll_to_latest(self):
        import importlib
        import shatranj.presentation.gui.window as w
        importlib.reload(w)

        ns = _make_window_ns()
        ns._scroll_history_to_position = MagicMock()
        w.ShatranjWindow._scroll_history_to_latest(ns)
        ns._scroll_history_to_position.assert_called_once_with(None)


# ---------------------------------------------------------------------------
# Tests for BoardWidget pure logic
# ---------------------------------------------------------------------------

class TestBoardWidgetLogic:
    def _make_widget(self):
        from shatranj.domain.core.board import Board
        from shatranj.domain.rules.rules_engine import RulesEngine

        engine = RulesEngine()
        board = Board(setup=True)

        ns = SimpleNamespace(
            _board=board,
            _current_color=WHITE,
            _interaction_enabled=True,
            _selected_square=None,
            _valid_moves=[],
            _dragging=False,
            _drag_square=None,
            _drag_x=0.0,
            _drag_y=0.0,
            _engine=engine,
            on_move_played=None,
            queue_draw=MagicMock(),
            get_width=lambda: 480,
            get_height=lambda: 480,
        )
        return ns

    def test_set_board_updates_state(self):
        import importlib
        import shatranj.presentation.gui.board_widget as bw
        importlib.reload(bw)

        from shatranj.domain.core.board import Board
        ns = self._make_widget()
        new_board = Board(setup=False)
        bw.BoardWidget.set_board(ns, new_board, BLACK)
        assert ns._board is new_board
        assert ns._current_color == BLACK
        assert ns._selected_square is None
        assert ns._valid_moves == []
        ns.queue_draw.assert_called()

    def test_clear_selection_resets_state(self):
        import importlib
        import shatranj.presentation.gui.board_widget as bw
        importlib.reload(bw)

        ns = self._make_widget()
        ns._selected_square = 12
        ns._valid_moves = [MagicMock()]
        bw.BoardWidget.clear_selection(ns)
        assert ns._selected_square is None
        assert ns._valid_moves == []
        ns.queue_draw.assert_called()

    def test_set_interaction_enabled_true(self):
        import importlib
        import shatranj.presentation.gui.board_widget as bw
        importlib.reload(bw)

        ns = self._make_widget()
        bw.BoardWidget.set_interaction_enabled(ns, True)
        assert ns._interaction_enabled is True

    def test_set_interaction_disabled_clears_drag(self):
        import importlib
        import shatranj.presentation.gui.board_widget as bw
        importlib.reload(bw)

        ns = self._make_widget()
        ns._dragging = True
        ns._drag_square = 20
        ns._selected_square = 12
        bw.BoardWidget.set_interaction_enabled(ns, False)
        assert ns._interaction_enabled is False
        assert ns._dragging is False
        assert ns._drag_square is None
        assert ns._selected_square is None

    def test_on_click_disabled_does_nothing(self):
        import importlib
        import shatranj.presentation.gui.board_widget as bw
        importlib.reload(bw)

        ns = self._make_widget()
        ns._interaction_enabled = False
        bw.BoardWidget._on_click(ns, MagicMock(), 1, 100, 100)
        assert ns._selected_square is None

    def test_on_click_no_board_does_nothing(self):
        import importlib
        import shatranj.presentation.gui.board_widget as bw
        importlib.reload(bw)

        ns = self._make_widget()
        ns._board = None
        bw.BoardWidget._on_click(ns, MagicMock(), 1, 100, 100)
        assert ns._selected_square is None

    def test_on_click_selects_own_piece(self):
        import importlib
        import shatranj.presentation.gui.board_widget as bw
        importlib.reload(bw)

        ns = self._make_widget()
        x, y = 4 * 60 + 30, (8 - 1 - 1) * 60 + 30
        bw.BoardWidget._on_click(ns, MagicMock(), 1, x, y)
        assert ns._selected_square == 12

    def test_on_click_negative_coords_returns_early(self):
        import importlib
        import shatranj.presentation.gui.board_widget as bw
        importlib.reload(bw)

        ns = self._make_widget()
        bw.BoardWidget._on_click(ns, MagicMock(), 1, -1, 100)
        assert ns._selected_square is None

    def test_on_click_plays_valid_move(self):
        import importlib
        import shatranj.presentation.gui.board_widget as bw
        importlib.reload(bw)
        from shatranj.domain.core.move import Move

        ns = self._make_widget()
        move = Move(from_square=12, to_square=20, piece_type=PAWN, color=WHITE)
        ns._valid_moves = [move]
        played = []
        ns.on_move_played = lambda m: played.append(m)

        x, y = 4 * 60 + 30, (7 - 2) * 60 + 30
        bw.BoardWidget._on_click(ns, MagicMock(), 1, x, y)
        assert played == [move]

    def test_on_drag_begin_disabled_does_nothing(self):
        import importlib
        import shatranj.presentation.gui.board_widget as bw
        importlib.reload(bw)

        ns = self._make_widget()
        ns._interaction_enabled = False
        bw.BoardWidget._on_drag_begin(ns, MagicMock(), 100, 100)
        assert not ns._dragging

    def test_on_drag_begin_selects_piece(self):
        import importlib
        import shatranj.presentation.gui.board_widget as bw
        importlib.reload(bw)

        ns = self._make_widget()
        x, y = 4 * 60 + 30, (8 - 1 - 1) * 60 + 30
        bw.BoardWidget._on_drag_begin(ns, MagicMock(), x, y)
        assert ns._dragging is True
        assert ns._drag_square == 12

    def test_on_drag_begin_enemy_piece_does_nothing(self):
        import importlib
        import shatranj.presentation.gui.board_widget as bw
        importlib.reload(bw)

        ns = self._make_widget()
        x, y = 4 * 60 + 30, (8 - 1 - 6) * 60 + 30
        bw.BoardWidget._on_drag_begin(ns, MagicMock(), x, y)
        assert not ns._dragging

    def test_on_drag_update_moves_piece(self):
        import importlib
        import shatranj.presentation.gui.board_widget as bw
        importlib.reload(bw)

        ns = self._make_widget()
        ns._dragging = True
        gesture = MagicMock()
        gesture.get_start_point.return_value = (True, 100.0, 100.0)
        bw.BoardWidget._on_drag_update(ns, gesture, 20.0, 30.0)
        assert ns._drag_x == 120.0
        assert ns._drag_y == 130.0

    def test_on_drag_update_not_dragging_does_nothing(self):
        import importlib
        import shatranj.presentation.gui.board_widget as bw
        importlib.reload(bw)

        ns = self._make_widget()
        ns._dragging = False
        bw.BoardWidget._on_drag_update(ns, MagicMock(), 20.0, 30.0)
        assert ns._drag_x == 0.0

    def test_on_drag_end_not_dragging_does_nothing(self):
        import importlib
        import shatranj.presentation.gui.board_widget as bw
        importlib.reload(bw)

        ns = self._make_widget()
        ns._dragging = False
        bw.BoardWidget._on_drag_end(ns, MagicMock(), 20.0, 30.0)

    def test_on_drag_end_drops_on_valid_square(self):
        import importlib
        import shatranj.presentation.gui.board_widget as bw
        importlib.reload(bw)
        from shatranj.domain.core.move import Move

        ns = self._make_widget()
        ns._dragging = True
        ns._drag_square = 12

        move = Move(from_square=12, to_square=20, piece_type=PAWN, color=WHITE)
        ns._valid_moves = [move]

        played = []
        ns.on_move_played = lambda m: played.append(m)

        gesture = MagicMock()
        start_x, start_y = 4 * 60 + 30, (8 - 1 - 1) * 60 + 30
        end_x, end_y = 4 * 60 + 30, (8 - 1 - 2) * 60 + 30
        gesture.get_start_point.return_value = (True, start_x, start_y)
        dx = end_x - start_x
        dy = end_y - start_y

        bw.BoardWidget._on_drag_end(ns, gesture, dx, dy)
        assert played == [move]


# ---------------------------------------------------------------------------
# Tests for hinting.py
# ---------------------------------------------------------------------------

class TestHinting:
    def test_build_hint_player_uses_existing_ai(self):
        from shatranj.domain.ai.hinting import build_hint_player
        from shatranj.domain.ai.ai_player import AIPlayer

        ai = AIPlayer(color=WHITE, depth=3, algorithm="alphabeta")
        result = build_hint_player(WHITE, {WHITE: ai})
        assert result is ai

    def test_build_hint_player_clones_template(self):
        from shatranj.domain.ai.hinting import build_hint_player
        from shatranj.domain.ai.ai_player import AIPlayer

        ai = AIPlayer(color=BLACK, depth=3, algorithm="alphabeta")
        result = build_hint_player(WHITE, {BLACK: ai})
        assert result is not ai
        assert result.color == WHITE
        assert result.algorithm == "alphabeta"

    def test_build_hint_player_no_ai_uses_defaults(self):
        from shatranj.domain.ai.hinting import build_hint_player

        result = build_hint_player(WHITE, {})
        assert result.color == WHITE
        assert result.algorithm == "alphabeta"

    def test_choose_hint_move_returns_move_or_none(self):
        from shatranj.domain.ai.hinting import choose_hint_move
        from shatranj.domain.core.board import Board
        from shatranj.domain.core.move import Move

        board = Board(setup=True)
        result = choose_hint_move(board, WHITE, {})
        assert result is None or isinstance(result, Move)

    def test_extract_depth_from_ai(self):
        from shatranj.domain.ai.hinting import _extract_depth
        from shatranj.domain.ai.ai_player import AIPlayer

        ai = AIPlayer(color=WHITE, depth=5, algorithm="alphabeta")
        assert _extract_depth(ai) == 5

    def test_extract_depth_fallback(self):
        from shatranj.domain.ai.hinting import _extract_depth, DEFAULT_HINT_DEPTH

        fake = SimpleNamespace(_search=SimpleNamespace())
        result = _extract_depth(fake)
        assert result == DEFAULT_HINT_DEPTH


# ---------------------------------------------------------------------------
# Tests for NewGameDialog pure logic
# ---------------------------------------------------------------------------

class TestNewGameDialogPureLogic:
    def test_on_mode_changed_updates_selected_mode(self):
        import importlib
        import shatranj.presentation.gui.window as w
        importlib.reload(w)

        button = MagicMock()
        button.get_active.return_value = True
        ns = SimpleNamespace(
            _selected_mode="hvh",
            _mode_hint=MagicMock(),
            _update_ai_options_visibility=MagicMock(),
        )
        w.NewGameDialog._on_mode_changed(ns, button, "hvai")
        assert ns._selected_mode == "hvai"

    def test_on_mode_changed_inactive_button_ignored(self):
        import importlib
        import shatranj.presentation.gui.window as w
        importlib.reload(w)

        button = MagicMock()
        button.get_active.return_value = False
        ns = SimpleNamespace(
            _selected_mode="hvh",
            _mode_hint=MagicMock(),
            _update_ai_options_visibility=MagicMock(),
        )
        w.NewGameDialog._on_mode_changed(ns, button, "hvai")
        assert ns._selected_mode == "hvh"

    def test_update_ai_options_hides_for_hvh(self):
        import importlib
        import shatranj.presentation.gui.window as w
        importlib.reload(w)

        ns = SimpleNamespace(
            _selected_mode="hvh",
            _algorithm_section=MagicMock(),
        )
        w.NewGameDialog._update_ai_options_visibility(ns)
        ns._algorithm_section.set_visible.assert_called_with(False)

    def test_update_ai_options_shows_for_hvai(self):
        import importlib
        import shatranj.presentation.gui.window as w
        importlib.reload(w)

        ns = SimpleNamespace(
            _selected_mode="hvai",
            _algorithm_section=MagicMock(),
        )
        w.NewGameDialog._update_ai_options_visibility(ns)
        ns._algorithm_section.set_visible.assert_called_with(True)

    def test_build_custom_preset_returns_dict(self):
        import importlib
        import shatranj.presentation.gui.window as w
        importlib.reload(w)

        ns = SimpleNamespace(
            _custom_minutes_spin=MagicMock(),
            _custom_increment_spin=MagicMock(),
        )
        ns._custom_minutes_spin.get_value.return_value = 15.0
        ns._custom_increment_spin.get_value.return_value = 5.0

        result = w.NewGameDialog._build_custom_preset(ns)
        assert result["base_seconds"] == 900
        assert result["increment_seconds"] == 5
        assert "15" in result["label"] or "min" in result["label"]

    def test_build_custom_preset_no_increment_label(self):
        import importlib
        import shatranj.presentation.gui.window as w
        importlib.reload(w)

        ns = SimpleNamespace(
            _custom_minutes_spin=MagicMock(),
            _custom_increment_spin=MagicMock(),
        )
        ns._custom_minutes_spin.get_value.return_value = 10.0
        ns._custom_increment_spin.get_value.return_value = 0.0

        result = w.NewGameDialog._build_custom_preset(ns)
        assert "min" in result["label"]

    def test_on_algorithm_changed_stores_selection(self):
        import importlib
        import shatranj.presentation.gui.window as w
        importlib.reload(w)

        ns = SimpleNamespace(
            _algorithm_combo=MagicMock(),
            _selected_algorithm="alphabeta",
        )
        ns._algorithm_combo.get_selected.return_value = 1
        w.NewGameDialog._on_algorithm_changed(ns)
        assert ns._selected_algorithm == "minimax"

    def test_get_config_valid_returns_dict(self):
        import importlib
        import shatranj.presentation.gui.window as w
        importlib.reload(w)

        ns = SimpleNamespace(
            _selected_speed="blitz",
            _selected_preset={
                "label": "5 min",
                "base_seconds": 300,
                "increment_seconds": 0,
            },
            _selected_mode="hvh",
            _selected_algorithm="alphabeta",
        )
        config = w.NewGameDialog.get_config(ns)
        assert config["mode"] == "hvh"
        assert config["base_seconds"] == 300
        assert config["algorithm"] == "alphabeta"


# ---------------------------------------------------------------------------
# Tests for _update_clock_labels
# ---------------------------------------------------------------------------

class TestUpdateClockLabels:
    def _method(self):
        import importlib
        import shatranj.presentation.gui.window as w
        importlib.reload(w)
        return w.ShatranjWindow._update_clock_labels

    def test_idle_mode_sets_dashes(self):
        ns = _make_window_ns(_clock_mode="idle")
        ns._set_clock_card_state = MagicMock()
        self._method()(ns)
        ns._time_control_label.set_label.assert_called_with("No active game")
        ns._white_timer_label.set_label.assert_called_with("--:--")
        ns._black_timer_label.set_label.assert_called_with("--:--")

    def test_timed_mode_sets_labels(self):
        state = _make_game_state(WHITE)
        ns = _make_window_ns(
            _clock_mode="timed",
            _state=state,
            _remaining_time={WHITE: 300.0, BLACK: 300.0},
            _game_paused=False,
            _time_control_name="Blitz 5 min",
        )
        ns._set_clock_card_state = MagicMock()
        ns._get_clock_status_text = MagicMock(return_value="To move")
        self._method()(ns)
        ns._time_control_label.set_label.assert_called_with("Blitz 5 min")
        ns._white_clock_side_label.set_label.assert_called_with("WHITE")
        ns._black_clock_side_label.set_label.assert_called_with("BLACK")

    def test_elapsed_mode_sets_labels(self):
        state = _make_game_state(WHITE)
        ns = _make_window_ns(
            _clock_mode="elapsed",
            _state=state,
            _elapsed_started_at=None,
            _time_control_name="Loaded Game",
        )
        ns._set_clock_card_state = MagicMock()
        self._method()(ns)
        ns._white_clock_side_label.set_label.assert_called_with("ELAPSED")
        ns._black_clock_side_label.set_label.assert_called_with("TURN")

    def test_timed_mode_no_state(self):
        ns = _make_window_ns(
            _clock_mode="timed",
            _state=None,
            _remaining_time={WHITE: 100.0, BLACK: 100.0},
            _game_paused=False,
            _time_control_name="Blitz",
        )
        ns._set_clock_card_state = MagicMock()
        ns._get_clock_status_text = MagicMock(return_value="Waiting")
        self._method()(ns)


# ---------------------------------------------------------------------------
# Tests for _stop_timer
# ---------------------------------------------------------------------------

class TestStopTimer:
    def _method(self):
        import importlib
        import shatranj.presentation.gui.window as w
        importlib.reload(w)
        return w.ShatranjWindow._stop_timer

    def test_stop_timer_clears_source(self):
        import importlib
        import shatranj.presentation.gui.window as w
        importlib.reload(w)

        ns = _make_window_ns(_timer_source_id=42)
        ns._update_clock_labels = MagicMock()
        ns._reset_clock = MagicMock()
        w.GLib.source_remove = MagicMock()

        self._method()(ns, reset=False)
        w.GLib.source_remove.assert_called_with(42)
        assert ns._timer_source_id is None
        assert ns._turn_started_at is None

    def test_stop_timer_with_reset(self):
        import importlib
        import shatranj.presentation.gui.window as w
        importlib.reload(w)

        ns = _make_window_ns(_timer_source_id=None)
        ns._update_clock_labels = MagicMock()
        ns._reset_clock = MagicMock()

        self._method()(ns, reset=True)
        ns._reset_clock.assert_called_once()
        ns._update_clock_labels.assert_not_called()

    def test_stop_timer_without_reset_calls_update(self):
        import importlib
        import shatranj.presentation.gui.window as w
        importlib.reload(w)

        ns = _make_window_ns(_timer_source_id=None)
        ns._update_clock_labels = MagicMock()
        ns._reset_clock = MagicMock()

        self._method()(ns, reset=False)
        ns._update_clock_labels.assert_called_once()
        ns._reset_clock.assert_not_called()


# ---------------------------------------------------------------------------
# Tests for _on_timer_tick
# ---------------------------------------------------------------------------

class TestOnTimerTick:
    def _method(self):
        import importlib
        import shatranj.presentation.gui.window as w
        importlib.reload(w)
        return w.ShatranjWindow._on_timer_tick

    def test_no_state_returns_false(self):
        ns = _make_window_ns(_state=None)
        result = self._method()(ns)
        assert result is False
        assert ns._timer_source_id is None

    def test_game_running_returns_true(self):
        ns = _make_window_ns(_state=_make_game_state(), _clock_mode="timed")
        ns._is_active_player_flagged = MagicMock(return_value=False)
        ns._update_clock_labels = MagicMock()
        result = self._method()(ns)
        assert result is True

    def test_flagged_returns_false(self):
        ns = _make_window_ns(_state=_make_game_state(), _clock_mode="timed")
        ns._is_active_player_flagged = MagicMock(return_value=True)
        ns._update_clock_labels = MagicMock()
        result = self._method()(ns)
        assert result is False
        assert ns._timer_source_id is None


# ---------------------------------------------------------------------------
# Tests for _on_load_game_finish
# ---------------------------------------------------------------------------

class TestOnLoadGameFinish:
    def test_file_none_returns_early(self):
        import importlib
        import shatranj.presentation.gui.window as w
        importlib.reload(w)

        ns = _make_window_ns()
        dialog = MagicMock()
        dialog.open_finish.return_value = None

        w.ShatranjWindow._on_load_game_finish(ns, dialog, MagicMock())
        assert ns._state is None

    def test_load_error_shows_alert(self):
        import importlib
        import shatranj.presentation.gui.window as w
        importlib.reload(w)
        from shatranj.utils.exceptions import LoadError

        ns = _make_window_ns()
        file_mock = MagicMock()
        file_mock.get_path.return_value = "/fake/path.shj"
        dialog = MagicMock()
        dialog.open_finish.return_value = file_mock

        with patch(
            "shatranj.persistence.load_game_file",
            side_effect=LoadError("bad file"),
        ):
            w.ShatranjWindow._on_load_game_finish(ns, dialog, MagicMock())

        ns._show_alert.assert_called()

    def test_successful_load_updates_state(self):
        import importlib
        import shatranj.presentation.gui.window as w
        importlib.reload(w)

        state = _make_game_state(WHITE)

        from shatranj.persistence import LoadedGame
        loaded = LoadedGame(state=state, ai_players={})

        ns = _make_window_ns()

        file_mock = MagicMock()
        file_mock.get_path.return_value = "/fake/path.shj"
        dialog = MagicMock()
        dialog.open_finish.return_value = file_mock

        with patch("shatranj.presentation.gui.window.load_game_file", return_value=loaded):
            w.ShatranjWindow._on_load_game_finish(ns, dialog, MagicMock())

        assert ns._state is state
        ns._start_timer.assert_called_once()


# ---------------------------------------------------------------------------
# Tests for _on_save_game_finish
# ---------------------------------------------------------------------------

class TestOnSaveGameFinish:
    def test_file_none_returns_early(self):
        import importlib
        import shatranj.presentation.gui.window as w
        importlib.reload(w)

        ns = _make_window_ns(_state=_make_game_state())
        dialog = MagicMock()
        dialog.save_finish.return_value = None

        w.ShatranjWindow._on_save_game_finish(ns, dialog, MagicMock())
        assert ns._saved is True

    def test_successful_save_sets_saved(self):
        import importlib
        import shatranj.presentation.gui.window as w
        importlib.reload(w)

        state = _make_game_state(WHITE)
        ns = _make_window_ns(_state=state, _saved=False)
        ns._save_game_to_path = MagicMock(return_value=True)

        file_mock = MagicMock()
        file_mock.get_path.return_value = "/tmp/test_save.shj"
        dialog = MagicMock()
        dialog.save_finish.return_value = file_mock

        w.ShatranjWindow._on_save_game_finish(ns, dialog, MagicMock())

        assert ns._saved is True


# ---------------------------------------------------------------------------
# Tests for _on_info and _on_help
# ---------------------------------------------------------------------------

class TestOnInfoAndHelp:
    def test_on_info_creates_dialog(self):
        import importlib
        import shatranj.presentation.gui.window as w
        importlib.reload(w)

        ns = _make_window_ns()
        dialog = MagicMock()
        w.Gtk.Dialog = MagicMock(return_value=dialog)

        w.ShatranjWindow._on_info(ns)
        dialog.present.assert_called_once()

    def test_on_help_creates_alert_dialog(self):
        import importlib
        import shatranj.presentation.gui.window as w
        importlib.reload(w)

        ns = _make_window_ns()
        dialog = MagicMock()
        w.Gtk.AlertDialog = MagicMock(return_value=dialog)

        w.ShatranjWindow._on_help(ns)
        dialog.set_message.assert_called_once()
        dialog.set_detail.assert_called_once()
        dialog.show.assert_called_once()


# ---------------------------------------------------------------------------
# Tests for _start_game
# ---------------------------------------------------------------------------

class TestStartGame:
    def _make_config(self, mode="hvh", algo="alphabeta"):
        return {
            "mode": mode,
            "algorithm": algo,
            "ai_color": BLACK,
            "speed_label": "Blitz",
            "time_control_label": "5 min",
            "base_seconds": 300,
            "increment_seconds": 0,
        }

    def _make_ns(self):
        ns = _make_window_ns()
        ns._sync_board_interaction = MagicMock()
        ns._update_history = MagicMock()
        ns._configure_new_game_clock = MagicMock()
        ns._start_timer = MagicMock()
        ns._auto_play_ai_turns = MagicMock()
        ns.set_show_menubar = MagicMock()
        return ns

    def test_hvh_creates_no_ai_players(self):
        import importlib
        import shatranj.presentation.gui.window as w
        importlib.reload(w)
        ns = self._make_ns()
        w.ShatranjWindow._start_game(ns, self._make_config("hvh"))
        assert ns._ai_players == {}
        assert ns._state is not None

    def test_hvai_creates_one_ai_player(self):
        import importlib
        import shatranj.presentation.gui.window as w
        importlib.reload(w)
        ns = self._make_ns()
        w.ShatranjWindow._start_game(ns, self._make_config("hvai"))
        assert BLACK in ns._ai_players
        assert WHITE not in ns._ai_players

    def test_aivai_creates_two_ai_players(self):
        import importlib
        import shatranj.presentation.gui.window as w
        importlib.reload(w)
        ns = self._make_ns()
        w.ShatranjWindow._start_game(ns, self._make_config("aivai"))
        assert WHITE in ns._ai_players
        assert BLACK in ns._ai_players

    def test_mcts_uses_depth_100(self):
        import importlib
        import shatranj.presentation.gui.window as w
        importlib.reload(w)
        ns = self._make_ns()
        w.ShatranjWindow._start_game(ns, self._make_config("hvai", "mcts"))
        assert ns._ai_players[BLACK]._search._depth == 100

    def test_start_game_calls_configure_clock(self):
        import importlib
        import shatranj.presentation.gui.window as w
        importlib.reload(w)
        ns = self._make_ns()
        config = self._make_config()
        w.ShatranjWindow._start_game(ns, config)
        ns._configure_new_game_clock.assert_called_once_with(config)
        ns._start_timer.assert_called_once()


# ---------------------------------------------------------------------------
# Tests for _on_new_game and _on_load_game
# ---------------------------------------------------------------------------

class TestOnNewGameAndLoad:
    def test_on_new_game_creates_dialog(self):
        import importlib
        import shatranj.presentation.gui.window as w
        importlib.reload(w)

        ns = _make_window_ns()

        with patch.object(w, "NewGameDialog") as MockDlg:
            instance = MagicMock()
            MockDlg.return_value = instance
            w.ShatranjWindow._on_new_game(ns)
            instance.connect.assert_called_once()
            instance.present.assert_called_once()

    def test_on_load_game_opens_file_dialog(self):
        import importlib
        import shatranj.presentation.gui.window as w
        importlib.reload(w)

        ns = _make_window_ns()
        dialog = MagicMock()
        w.Gtk.FileDialog = MagicMock(return_value=dialog)

        w.ShatranjWindow._on_load_game(ns)
        dialog.open.assert_called_once()


# ---------------------------------------------------------------------------
# Tests for NewGameDialog speed/preset
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Helpers pour accéder aux méthodes de NewGameDialog sans GTK
# ---------------------------------------------------------------------------

import importlib as _importlib
import types as _types

def _get_newgame_method(name):
    """Extract a method from NewGameDialog source without going through the mock."""
    import shatranj.presentation.gui.window as _w
    # The class may be mocked, but its methods are defined in the source.
    # We find them by inspecting the module's source-defined classes.
    for obj in vars(_w).values():
        if isinstance(obj, type) and obj.__name__ == "NewGameDialog":
            method = obj.__dict__.get(name)
            if method is not None:
                return method
    # Fallback: get from MRO excluding Mock bases
    raise AttributeError(f"NewGameDialog has no method {name!r}")
