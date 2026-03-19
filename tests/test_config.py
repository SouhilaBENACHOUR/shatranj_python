"""
test_config.py - Tests for config.py (F2)

Tests cover:
  - Default file creation
  - Reading valid values
  - Invalid values replaced by defaults
  - CLI overrides (apply_args)
  - Missing section
  - Unparseable file
"""

import sys
import argparse
from pathlib import Path

import pytest

from shatranj.config import ShatranjConfig, DEFAULTS, MINIMAL_CONFIG


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_config(tmp_path: Path, content: str) -> ShatranjConfig:
    """Create a ShatranjConfig from a string content written to a temp file."""
    p = tmp_path / ".shatranjrc"
    p.write_text(content, encoding="utf-8")
    return ShatranjConfig(config_path=p)


def make_args(**kwargs):
    """Build a minimal argparse Namespace for apply_args()."""
    defaults = {
        "verbose": False,
        "debug": False,
        "blitz": False,
        "time": 30,
        "ai_mode": None,
        "ai_depth": None,
        "ai_scoring": None,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


# ---------------------------------------------------------------------------
# File creation
# ---------------------------------------------------------------------------

class TestFileCreation:
    def test_creates_file_if_missing(self, tmp_path):
        p = tmp_path / ".shatranjrc"
        assert not p.exists()
        ShatranjConfig(config_path=p)
        assert p.exists()

    def test_created_file_contains_defaults_section(self, tmp_path):
        p = tmp_path / ".shatranjrc"
        ShatranjConfig(config_path=p)
        content = p.read_text(encoding="utf-8")
        assert "[defaults]" in content

    def test_created_file_matches_minimal_config(self, tmp_path):
        p = tmp_path / ".shatranjrc"
        ShatranjConfig(config_path=p)
        content = p.read_text(encoding="utf-8")
        assert "ai-mode" in content
        assert "language" in content

    def test_does_not_overwrite_existing_file(self, tmp_path):
        p = tmp_path / ".shatranjrc"
        p.write_text("[defaults]\nverbose = true\n", encoding="utf-8")
        ShatranjConfig(config_path=p)
        content = p.read_text(encoding="utf-8")
        assert "verbose = true" in content


# ---------------------------------------------------------------------------
# Reading valid values
# ---------------------------------------------------------------------------

class TestReadValidValues:
    def test_reads_verbose_true(self, tmp_path):
        cfg = make_config(tmp_path, "[defaults]\nverbose = true\n")
        assert cfg.get_bool("verbose") is True

    def test_reads_verbose_false(self, tmp_path):
        cfg = make_config(tmp_path, "[defaults]\nverbose = false\n")
        assert cfg.get_bool("verbose") is False

    def test_reads_ai_mode(self, tmp_path):
        cfg = make_config(tmp_path, "[defaults]\nai-mode = minimax\n")
        assert cfg.get_str("ai-mode") == "minimax"

    def test_reads_ai_depth_as_int(self, tmp_path):
        cfg = make_config(tmp_path, "[defaults]\nai-depth = 5\n")
        assert cfg.get_int("ai-depth") == 5

    def test_reads_timeout(self, tmp_path):
        cfg = make_config(tmp_path, "[defaults]\ntimeout = 15\n")
        assert cfg.get_int("timeout") == 15

    def test_reads_language(self, tmp_path):
        cfg = make_config(tmp_path, "[defaults]\nlanguage = fr\n")
        assert cfg.get_str("language") == "fr"

    def test_accepts_yes_as_bool(self, tmp_path):
        cfg = make_config(tmp_path, "[defaults]\nverbose = yes\n")
        assert cfg.get_bool("verbose") is True

    def test_accepts_1_as_bool(self, tmp_path):
        cfg = make_config(tmp_path, "[defaults]\ndebug = 1\n")
        assert cfg.get_bool("debug") is True

    def test_missing_key_uses_default(self, tmp_path):
        cfg = make_config(tmp_path, "[defaults]\n")
        assert cfg.get_str("ai-mode") == DEFAULTS["ai-mode"]
        assert cfg.get_int("ai-depth") == int(DEFAULTS["ai-depth"])


# ---------------------------------------------------------------------------
# Invalid values replaced by defaults
# ---------------------------------------------------------------------------

class TestInvalidValues:
    def test_invalid_ai_mode_uses_default(self, tmp_path, capsys):
        cfg = make_config(tmp_path, "[defaults]\nai-mode = blabla\n")
        assert cfg.get_str("ai-mode") == DEFAULTS["ai-mode"]
        captured = capsys.readouterr()
        assert "Warning" in captured.err

    def test_invalid_ai_scoring_uses_default(self, tmp_path, capsys):
        cfg = make_config(tmp_path, "[defaults]\nai-scoring = unknown\n")
        assert cfg.get_str("ai-scoring") == DEFAULTS["ai-scoring"]
        captured = capsys.readouterr()
        assert "Warning" in captured.err

    def test_invalid_language_uses_default(self, tmp_path, capsys):
        cfg = make_config(tmp_path, "[defaults]\nlanguage = de\n")
        assert cfg.get_str("language") == DEFAULTS["language"]

    def test_invalid_boolean_uses_default(self, tmp_path, capsys):
        cfg = make_config(tmp_path, "[defaults]\nverbose = maybe\n")
        assert cfg.get_bool("verbose") is False
        captured = capsys.readouterr()
        assert "Warning" in captured.err

    def test_invalid_integer_uses_default(self, tmp_path, capsys):
        cfg = make_config(tmp_path, "[defaults]\nai-depth = abc\n")
        assert cfg.get_int("ai-depth") == int(DEFAULTS["ai-depth"])
        captured = capsys.readouterr()
        assert "Warning" in captured.err

    def test_invalid_timeout_uses_default(self, tmp_path, capsys):
        cfg = make_config(tmp_path, "[defaults]\ntimeout = notanumber\n")
        assert cfg.get_int("timeout") == int(DEFAULTS["timeout"])

    def test_does_not_overwrite_invalid_file(self, tmp_path):
        p = tmp_path / ".shatranjrc"
        original = "[defaults]\nai-mode = blabla\n"
        p.write_text(original, encoding="utf-8")
        ShatranjConfig(config_path=p)
        assert p.read_text(encoding="utf-8") == original


# ---------------------------------------------------------------------------
# Missing section
# ---------------------------------------------------------------------------

class TestMissingSection:
    def test_no_defaults_section_warns(self, tmp_path, capsys):
        cfg = make_config(tmp_path, "[other]\nfoo = bar\n")
        captured = capsys.readouterr()
        assert "Warning" in captured.err

    def test_no_defaults_section_uses_defaults(self, tmp_path):
        cfg = make_config(tmp_path, "[other]\nfoo = bar\n")
        assert cfg.get_str("ai-mode") == DEFAULTS["ai-mode"]


# ---------------------------------------------------------------------------
# Unparseable file
# ---------------------------------------------------------------------------

class TestUnparseableFile:
    def test_invalid_file_warns(self, tmp_path, capsys):
        cfg = make_config(tmp_path, "this is not ini !!!")
        captured = capsys.readouterr()
        assert "Warning" in captured.err

    def test_invalid_file_uses_defaults(self, tmp_path):
        cfg = make_config(tmp_path, "this is not ini !!!")
        assert cfg.get_str("ai-mode") == DEFAULTS["ai-mode"]
        assert cfg.get_bool("verbose") is False


# ---------------------------------------------------------------------------
# apply_args: CLI overrides
# ---------------------------------------------------------------------------

class TestApplyArgs:
    def test_verbose_flag_overrides_config(self, tmp_path):
        cfg = make_config(tmp_path, "[defaults]\nverbose = false\n")
        args = make_args(verbose=True)
        cfg.apply_args(args)
        assert cfg.get_bool("verbose") is True

    def test_debug_flag_overrides_config(self, tmp_path):
        cfg = make_config(tmp_path, "[defaults]\ndebug = false\n")
        args = make_args(debug=True)
        cfg.apply_args(args)
        assert cfg.get_bool("debug") is True

    def test_ai_mode_overrides_config(self, tmp_path, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["shatranj", "--ai-mode", "mcts"])
        cfg = make_config(tmp_path, "[defaults]\nai-mode = minimax\n")
        args = make_args(ai_mode="mcts")
        cfg.apply_args(args)
        assert cfg.get_str("ai-mode") == "mcts"

    def test_ai_depth_overrides_config(self, tmp_path):
        cfg = make_config(tmp_path, "[defaults]\nai-depth = 3\n")
        args = make_args(ai_depth=6)
        cfg.apply_args(args)
        assert cfg.get_int("ai-depth") == 6

    def test_ai_scoring_overrides_config(self, tmp_path, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["shatranj", "--ai-scoring", "material"])
        cfg = make_config(tmp_path, "[defaults]\nai-scoring = advanced\n")
        args = make_args(ai_scoring="material")
        cfg.apply_args(args)
        assert cfg.get_str("ai-scoring") == "material"

    def test_none_ai_mode_does_not_override(self, tmp_path):
        cfg = make_config(tmp_path, "[defaults]\nai-mode = minimax\n")
        args = make_args(ai_mode=None)
        cfg.apply_args(args)
        assert cfg.get_str("ai-mode") == "minimax"

    def test_false_verbose_does_not_override_true(self, tmp_path):
        cfg = make_config(tmp_path, "[defaults]\nverbose = true\n")
        args = make_args(verbose=False)
        cfg.apply_args(args)
        # False flag should not override a true in config
        assert cfg.get_bool("verbose") is True

    def test_time_override_requires_argv(self, tmp_path, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["shatranj", "-t", "10"])
        cfg = make_config(tmp_path, "[defaults]\ntimeout = 30\n")
        args = make_args(time=10)
        cfg.apply_args(args)
        assert cfg.get_int("timeout") == 10

    def test_time_not_overridden_without_argv(self, tmp_path, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["shatranj"])
        cfg = make_config(tmp_path, "[defaults]\ntimeout = 30\n")
        args = make_args(time=30)
        cfg.apply_args(args)
        assert cfg.get_int("timeout") == 30


# ---------------------------------------------------------------------------
# get_* methods
# ---------------------------------------------------------------------------

class TestGetMethods:
    def test_get_str_unknown_key_returns_empty(self, tmp_path):
        cfg = make_config(tmp_path, "[defaults]\n")
        assert cfg.get_str("nonexistent") == ""

    def test_get_bool_unknown_key_returns_false(self, tmp_path):
        cfg = make_config(tmp_path, "[defaults]\n")
        assert cfg.get_bool("nonexistent") is False

    def test_get_int_unknown_key_returns_zero(self, tmp_path):
        cfg = make_config(tmp_path, "[defaults]\n")
        assert cfg.get_int("nonexistent") == 0

    def test_get_int_invalid_stored_value_returns_zero(self, tmp_path):
        cfg = make_config(tmp_path, "[defaults]\n")
        cfg._values["ai-depth"] = "notanint"
        assert cfg.get_int("ai-depth") == 0