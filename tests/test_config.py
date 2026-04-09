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

import argparse
import configparser
import sys
from pathlib import Path
from unittest.mock import patch


from shatranj.config import ShatranjConfig, DEFAULTS

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
        "ai_minimax_depth": None,
        "ai_scoring": None,
        "ai_minimax_scoring": None,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def workspace_config_path(name: str) -> Path:
    """Return a config path stored inside the repository workspace."""
    base = Path(".tmp_config_tests")
    base.mkdir(exist_ok=True)
    return base / name


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

    def test_reads_iterative_ai_mode(self, tmp_path):
        cfg = make_config(tmp_path, "[defaults]\nai-mode = iterative\n")
        assert cfg.get_str("ai-mode") == "iterative"

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
        make_config(tmp_path, "[other]\nfoo = bar\n")
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
        make_config(tmp_path, "this is not ini !!!")
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

    def test_ai_minimax_depth_overrides_config(self, tmp_path):
        cfg = make_config(tmp_path, "[defaults]\nai-depth = 3\n")
        args = make_args(ai_minimax_depth=5)
        cfg.apply_args(args)
        assert cfg.get_int("ai-depth") == 5

    def test_ai_scoring_overrides_config(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            sys, "argv", ["shatranj", "--ai-scoring", "material"]
        )
        cfg = make_config(tmp_path, "[defaults]\nai-scoring = advanced\n")
        args = make_args(ai_scoring="material")
        cfg.apply_args(args)
        assert cfg.get_str("ai-scoring") == "material"

    def test_ai_minimax_scoring_overrides_config(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            sys, "argv", ["shatranj", "--ai-minimax-scoring", "positional"]
        )
        cfg = make_config(tmp_path, "[defaults]\nai-scoring = advanced\n")
        args = make_args(ai_minimax_scoring="positional")
        cfg.apply_args(args)
        assert cfg.get_str("ai-scoring") == "positional"

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
        args = make_args(time=10, blitz=True)
        cfg.apply_args(args)
        assert cfg.get_int("timeout") == 10

    def test_time_not_overridden_without_argv(self, tmp_path, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["shatranj"])
        cfg = make_config(tmp_path, "[defaults]\ntimeout = 30\n")
        args = make_args(time=30)
        cfg.apply_args(args)
        assert cfg.get_int("timeout") == 30

    def test_time_without_blitz_does_not_override(self, tmp_path, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["shatranj", "-t", "10"])
        cfg = make_config(tmp_path, "[defaults]\ntimeout = 30\n")
        args = make_args(time=10, blitz=False)
        cfg.apply_args(args)
        assert cfg.get_int("timeout") == 30


class TestConfigWithoutTmpPath:
    """Extra config tests that avoid pytest tmp directories."""

    def test_default_home_path_is_used_when_not_provided(self, monkeypatch):
        fake_home = workspace_config_path("fake_home")
        fake_home.mkdir(exist_ok=True)
        config_path = fake_home / ".shatranjrc"
        config_path.unlink(missing_ok=True)
        monkeypatch.setattr(Path, "home", lambda: fake_home)

        cfg = ShatranjConfig()

        assert cfg._path == config_path
        assert config_path.exists()
        config_path.unlink(missing_ok=True)

    def test_create_minimal_reports_oserror(self, capsys):
        config_path = workspace_config_path("cannot_create.shatranjrc")
        config_path.unlink(missing_ok=True)

        with patch.object(Path, "write_text", side_effect=OSError("blocked")):
            ShatranjConfig(config_path=config_path)

        assert "could not create" in capsys.readouterr().err

    def test_parser_read_exception_uses_defaults(self, capsys):
        config_path = workspace_config_path("parser_error.shatranjrc")
        config_path.write_text("[defaults]\nverbose=true\n", encoding="utf-8")

        with patch.object(
            configparser.ConfigParser,
            "read",
            side_effect=configparser.Error("boom"),
        ):
            cfg = ShatranjConfig(config_path=config_path)

        assert cfg.get_bool("verbose") is False
        assert "could not parse" in capsys.readouterr().err
        config_path.unlink(missing_ok=True)

    def test_blitz_flag_overrides_config(self):
        config_path = workspace_config_path("blitz_override.shatranjrc")
        config_path.write_text("[defaults]\nblitz = false\n", encoding="utf-8")

        cfg = ShatranjConfig(config_path=config_path)
        cfg.apply_args(make_args(blitz=True))

        assert cfg.get_bool("blitz") is True
        config_path.unlink(missing_ok=True)

    def test_ai_mode_without_flag_does_not_override(self, monkeypatch):
        config_path = workspace_config_path("ai_mode_keep.shatranjrc")
        config_path.write_text(
            "[defaults]\nai-mode = alphabeta\n", encoding="utf-8"
        )
        monkeypatch.setattr(sys, "argv", ["shatranj"])

        cfg = ShatranjConfig(config_path=config_path)
        cfg.apply_args(make_args(ai_mode="mcts"))

        assert cfg.get_str("ai-mode") == "alphabeta"
        config_path.unlink(missing_ok=True)

    def test_ai_scoring_without_flag_does_not_override(self, monkeypatch):
        config_path = workspace_config_path("ai_scoring_keep.shatranjrc")
        config_path.write_text(
            "[defaults]\nai-scoring = advanced\n", encoding="utf-8"
        )
        monkeypatch.setattr(sys, "argv", ["shatranj"])

        cfg = ShatranjConfig(config_path=config_path)
        cfg.apply_args(make_args(ai_scoring="material"))

        assert cfg.get_str("ai-scoring") == "advanced"
        config_path.unlink(missing_ok=True)

    def test_time_long_option_with_blitz_overrides_timeout(self, monkeypatch):
        config_path = workspace_config_path("timeout_override.shatranjrc")
        config_path.write_text("[defaults]\ntimeout = 30\n", encoding="utf-8")
        monkeypatch.setattr(sys, "argv", ["shatranj", "--time", "12", "--blitz"])

        cfg = ShatranjConfig(config_path=config_path)
        cfg.apply_args(make_args(time=12, blitz=True))

        assert cfg.get_int("timeout") == 12
        config_path.unlink(missing_ok=True)


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
