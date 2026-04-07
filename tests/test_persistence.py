"""Tests for shared save/load helpers."""

from shatranj.domain.core.move import Move
from shatranj.persistence import load_game_file, save_game_file
from shatranj.presentation.cli.game_state import GameState
from shatranj.utils.constants import BLACK, PAWN, SHAH, WHITE


def _build_capturing_state() -> GameState:
    """Return a small game state with one recorded capture."""
    state = GameState()
    state.board.clear()
    state.board.place_piece(SHAH, WHITE, 4)
    state.board.place_piece(SHAH, BLACK, 60)
    state.board.place_piece(PAWN, WHITE, 12)
    state.board.place_piece(PAWN, BLACK, 21)
    state.apply_move(
        Move(12, 21, PAWN, WHITE, captured_piece=PAWN)
    )
    return state


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
