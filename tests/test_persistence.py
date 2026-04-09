"""Tests for shared save/load helpers."""

from pathlib import Path

import pytest

from shatranj.domain.core.move import Move
from shatranj.persistence import (ClockState, _parse_ai_players,
                                  _parse_clock_state, load_game_file,
                                  save_game_file, strip_save_comments)
from shatranj.presentation.cli.game_state import GameState
from shatranj.utils.constants import BLACK, PAWN, SHAH, WHITE
from shatranj.utils.exceptions import LoadError, SaveError


def _build_capturing_state() -> GameState:
    """Return a small game state with one recorded capture."""
    state = GameState()
    state.board.clear()
    state.board.place_piece(SHAH, WHITE, 4)
    state.board.place_piece(SHAH, BLACK, 60)
    state.board.place_piece(PAWN, WHITE, 12)
    state.board.place_piece(PAWN, BLACK, 21)
    state.apply_move(Move(12, 21, PAWN, WHITE, captured_piece=PAWN))
    return state


def _workspace_temp_file(name: str) -> Path:
    """
    Return a writable temporary file path inside the repository workspace.
    """
    base = Path(".tmp_persistence_tests")
    base.mkdir(exist_ok=True)
    return base / name


def test_save_and_load_preserve_captured_piece_type(tmp_path):
    state = _build_capturing_state()
    save_file = tmp_path / "capture.shj"

    save_game_file(str(save_file), state=state)
    raw = save_file.read_text(encoding="ascii")
    loaded = load_game_file(str(save_file))

    assert "W e2xf3:P" in raw
    assert loaded.state.current_color == BLACK
    assert loaded.state.get_history()[0].captured_piece == PAWN


def test_load_keeps_legacy_capture_history_compatible(tmp_path):
    state = _build_capturing_state()
    save_file = tmp_path / "legacy_capture.shj"

    save_game_file(str(save_file), state=state)
    raw = save_file.read_text(encoding="ascii").replace(":P", "")
    save_file.write_text(raw, encoding="ascii")

    loaded = load_game_file(str(save_file))

    assert loaded.state.get_history()[0].captured_piece == "unknown"


def test_save_without_state_raises_save_error():
    with pytest.raises(SaveError):
        save_game_file("unused.shj", state=None)


def test_strip_save_comments_removes_inline_and_block_comments():
    content = """
    [settings]
    verbose=true # inline
    { block
      comment }
    [game]
    W
    """

    result = strip_save_comments(content)

    assert result == ["[settings]", "verbose=true", "[game]", "W"]


def test_parse_clock_state_reads_timed_settings():
    clock = _parse_clock_state(
        {
            "clock_mode": "timed",
            "time_control_name": "Blitz 3+2",
            "base_seconds": "180",
            "increment_seconds": "2",
            "white_remaining_seconds": "170.5",
            "black_remaining_seconds": "160.0",
            "timer_paused": "true",
        }
    )

    assert clock.mode == "timed"
    assert clock.label == "Blitz 3+2"
    assert clock.base_seconds == 180.0
    assert clock.increment_seconds == 2
    assert clock.white_seconds == 170.5
    assert clock.black_seconds == 160.0
    assert clock.paused is True


def test_parse_ai_players_rebuilds_saved_ai_configuration():
    players = _parse_ai_players(
        {
            "ai-color": "white",
            "ai-mode": "minimax",
            "ai-depth": "4",
            "ai-scoring": "advanced",
        }
    )

    assert list(players) == [WHITE]
    ai = players[WHITE]
    assert getattr(ai, "algorithm", None) == "minimax"
    assert getattr(getattr(ai, "_search", None), "_depth", None) == 4
    assert getattr(ai, "scoring", None) == "advanced"


def test_parse_ai_players_without_color_returns_empty_mapping():
    assert _parse_ai_players({}) == {}


def test_load_missing_sections_raises_load_error():
    save_file = _workspace_temp_file("broken_sections.shj")
    try:
        save_file.write_text("[settings]\nverbose=true\n", encoding="ascii")

        with pytest.raises(LoadError):
            load_game_file(str(save_file))
    finally:
        save_file.unlink(missing_ok=True)


def test_load_invalid_captured_piece_suffix_raises_load_error():
    state = _build_capturing_state()

    save_file = _workspace_temp_file("invalid_capture.shj")
    try:
        save_game_file(str(save_file), state=state)
        raw = save_file.read_text(encoding="ascii").replace(":P", ":Z")
        save_file.write_text(raw, encoding="ascii")

        with pytest.raises(LoadError):
            load_game_file(str(save_file))
    finally:
        save_file.unlink(missing_ok=True)


def test_load_invalid_capture_error_reports_source_line():
    state = _build_capturing_state()
    save_file = _workspace_temp_file("invalid_capture_line.shj")
    try:
        save_game_file(str(save_file), state=state)
        raw = save_file.read_text(encoding="ascii").replace(
            "W e2xf3:P", "W e2xf3:Z"
        )
        save_file.write_text(raw, encoding="ascii")

        with pytest.raises(LoadError) as exc_info:
            load_game_file(str(save_file))

        assert exc_info.value.line == 17
    finally:
        save_file.unlink(missing_ok=True)


def test_load_invalid_square_in_history_raises_load_error():
    state = _build_capturing_state()

    save_file = _workspace_temp_file("invalid_square.shj")
    try:
        save_game_file(str(save_file), state=state)
        raw = save_file.read_text(encoding="ascii").replace(
            "e2xf3:P", "z9xf3:P"
        )
        save_file.write_text(raw, encoding="ascii")

        with pytest.raises(LoadError):
            load_game_file(str(save_file))
    finally:
        save_file.unlink(missing_ok=True)


def test_load_invalid_square_error_reports_source_line():
    state = _build_capturing_state()
    save_file = _workspace_temp_file("invalid_square_line.shj")
    try:
        save_game_file(str(save_file), state=state)
        raw = save_file.read_text(encoding="ascii").replace(
            "e2xf3:P", "z9xf3:P"
        )
        save_file.write_text(raw, encoding="ascii")

        with pytest.raises(LoadError) as exc_info:
            load_game_file(str(save_file))

        assert exc_info.value.line == 17
    finally:
        save_file.unlink(missing_ok=True)


def test_save_and_load_roundtrip_preserves_clock_and_ai_settings():
    from shatranj.domain.ai.ai_player import AIPlayer

    state = _build_capturing_state()
    save_file = _workspace_temp_file("timed_ai_roundtrip.shj")
    ai_players = {WHITE: AIPlayer(color=WHITE, depth=2, algorithm="alphabeta")}
    clock = ClockState(
        mode="timed",
        label="Blitz 3+2",
        base_seconds=180.0,
        increment_seconds=2,
        white_seconds=170.0,
        black_seconds=165.0,
        paused=True,
    )

    try:
        save_game_file(
            str(save_file), state=state, clock=clock, ai_players=ai_players
        )
        loaded = load_game_file(str(save_file))

        assert loaded.clock.mode == "timed"
        assert loaded.clock.label == "Blitz 3+2"
        assert loaded.clock.white_seconds == 170.0
        assert loaded.clock.black_seconds == 165.0
        assert loaded.clock.paused is True
        assert WHITE in loaded.ai_players
        assert (
            getattr(loaded.ai_players[WHITE], "algorithm", None) == "alphabeta"
        )
    finally:
        save_file.unlink(missing_ok=True)


def test_load_invalid_board_row_raises_load_error():
    state = _build_capturing_state()
    save_file = _workspace_temp_file("invalid_row.shj")

    try:
        save_game_file(str(save_file), state=state)
        raw = save_file.read_text(encoding="ascii").replace(
            "_ _ _ _ _ _ _ _", "_ _ _"
        )
        save_file.write_text(raw, encoding="ascii")

        with pytest.raises(LoadError):
            load_game_file(str(save_file))
    finally:
        save_file.unlink(missing_ok=True)


def test_load_unknown_piece_symbol_raises_load_error():
    state = _build_capturing_state()
    save_file = _workspace_temp_file("invalid_symbol.shj")

    try:
        save_game_file(str(save_file), state=state)
        raw = save_file.read_text(encoding="ascii").replace("k", "z", 1)
        save_file.write_text(raw, encoding="ascii")

        with pytest.raises(LoadError):
            load_game_file(str(save_file))
    finally:
        save_file.unlink(missing_ok=True)
