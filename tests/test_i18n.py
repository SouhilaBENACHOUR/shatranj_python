"""
test_i18n.py - Tests for i18n.py (F3)

Tests cover:
  - Language detection from environment variables
  - Fallback to English for unsupported languages
  - Warning displayed for unsupported languages
  - setup() installs _() as builtin
  - Missing .mo file does not crash
  - Forced language via setup(language=...)
"""

import builtins
import gettext
from pathlib import Path
from unittest.mock import patch

import pytest

from shatranj.i18n import _detect_language, setup, SUPPORTED_LANGUAGES, DEFAULT_LANGUAGE


# ---------------------------------------------------------------------------
# _detect_language()
# ---------------------------------------------------------------------------

class TestDetectLanguage:
    def test_detects_lang_from_LC_ALL(self, monkeypatch):
        monkeypatch.setenv("LC_ALL", "fr_FR.UTF-8")
        monkeypatch.delenv("LANG", raising=False)
        assert _detect_language() == "fr"

    def test_detects_lang_from_LANG(self, monkeypatch):
        monkeypatch.delenv("LC_ALL", raising=False)
        monkeypatch.setenv("LANG", "fr_FR.UTF-8")
        assert _detect_language() == "fr"

    def test_LC_ALL_takes_priority_over_LANG(self, monkeypatch):
        monkeypatch.setenv("LC_ALL", "fr_FR.UTF-8")
        monkeypatch.setenv("LANG", "en_US.UTF-8")
        assert _detect_language() == "fr"

    def test_detects_english(self, monkeypatch):
        monkeypatch.setenv("LANG", "en_US.UTF-8")
        monkeypatch.delenv("LC_ALL", raising=False)
        assert _detect_language() == "en"

    def test_returns_default_if_no_env(self, monkeypatch):
        monkeypatch.delenv("LC_ALL", raising=False)
        monkeypatch.delenv("LANG", raising=False)
        with patch("locale.getlocale", return_value=(None, None)):
            result = _detect_language()
        assert result == DEFAULT_LANGUAGE

    def test_handles_lang_without_region(self, monkeypatch):
        monkeypatch.setenv("LANG", "fr.UTF-8")
        monkeypatch.delenv("LC_ALL", raising=False)
        assert _detect_language() == "fr"

    def test_handles_lang_code_only(self, monkeypatch):
        monkeypatch.setenv("LANG", "fr")
        monkeypatch.delenv("LC_ALL", raising=False)
        assert _detect_language() == "fr"

    def test_returns_lowercase(self, monkeypatch):
        monkeypatch.setenv("LANG", "FR_FR.UTF-8")
        monkeypatch.delenv("LC_ALL", raising=False)
        assert _detect_language() == "fr"

    def test_locale_getlocale_fallback(self, monkeypatch):
        monkeypatch.delenv("LC_ALL", raising=False)
        monkeypatch.delenv("LANG", raising=False)
        with patch("locale.getlocale", return_value=("fr_FR", "UTF-8")):
            result = _detect_language()
        assert result == "fr"

    def test_locale_getlocale_exception_returns_default(self, monkeypatch):
        monkeypatch.delenv("LC_ALL", raising=False)
        monkeypatch.delenv("LANG", raising=False)
        with patch("locale.getlocale", side_effect=Exception("error")):
            result = _detect_language()
        assert result == DEFAULT_LANGUAGE


# ---------------------------------------------------------------------------
# setup()
# ---------------------------------------------------------------------------

class TestSetup:
    def test_setup_returns_translations_object(self):
        result = setup("en")
        assert isinstance(result, (gettext.GNUTranslations, gettext.NullTranslations))

    def test_setup_installs_builtin(self):
        setup("en")
        assert hasattr(builtins, "_")

    def test_setup_english_does_not_translate(self):
        setup("en")
        _ = builtins.__dict__["_"]
        assert _("Goodbye!") == "Goodbye!"

    def test_setup_french_translates(self):
        setup("fr")
        _ = builtins.__dict__["_"]
        assert _("Goodbye!") == "Au revoir !"

    def test_setup_french_translates_welcome(self):
        setup("fr")
        _ = builtins.__dict__["_"]
        result = _("Welcome to Shatranj! Type 'help' to see available commands.")
        assert "Bienvenue" in result

    def test_setup_unsupported_language_warns(self, capsys):
        setup("de")
        captured = capsys.readouterr()
        assert "Warning" in captured.err
        assert "de" in captured.err

    def test_setup_unsupported_language_falls_back_to_english(self, capsys):
        setup("de")
        _ = builtins.__dict__["_"]
        assert _("Goodbye!") == "Goodbye!"

    def test_setup_forced_language(self):
        result = setup(language="fr")
        assert isinstance(result, (gettext.GNUTranslations, gettext.NullTranslations))

    def test_setup_none_autodetects(self, monkeypatch):
        monkeypatch.setenv("LANG", "fr_FR.UTF-8")
        monkeypatch.delenv("LC_ALL", raising=False)
        setup(None)
        _ = builtins.__dict__["_"]
        assert _("Goodbye!") == "Au revoir !"

    def test_setup_missing_mo_does_not_crash(self, tmp_path, monkeypatch):
        """If .mo file is missing, NullTranslations is used — no crash."""
        import shatranj.i18n as i18n_module
        monkeypatch.setattr(i18n_module, "LOCALES_DIR", tmp_path)
        result = setup("fr")
        assert isinstance(result, gettext.NullTranslations)

    def test_null_translations_returns_string_unchanged(self, tmp_path, monkeypatch):
        import shatranj.i18n as i18n_module
        monkeypatch.setattr(i18n_module, "LOCALES_DIR", tmp_path)
        setup("fr")
        _ = builtins.__dict__["_"]
        assert _("Hello") == "Hello"


# ---------------------------------------------------------------------------
# Module-level _()
# ---------------------------------------------------------------------------

class TestModuleLevelUnderscore:
    def test_module_underscore_is_callable(self):
        from shatranj.i18n import _ as module_underscore
        assert callable(module_underscore)

    def test_module_underscore_returns_string(self):
        from shatranj.i18n import _ as module_underscore
        result = module_underscore("Hello")
        assert isinstance(result, str)


# ---------------------------------------------------------------------------
# Supported languages
# ---------------------------------------------------------------------------

class TestSupportedLanguages:
    def test_english_is_supported(self):
        assert "en" in SUPPORTED_LANGUAGES

    def test_french_is_supported(self):
        assert "fr" in SUPPORTED_LANGUAGES

    def test_german_is_not_supported(self):
        assert "de" not in SUPPORTED_LANGUAGES

    def test_default_language_is_english(self):
        assert DEFAULT_LANGUAGE == "en"

    def test_default_language_is_supported(self):
        assert DEFAULT_LANGUAGE in SUPPORTED_LANGUAGES