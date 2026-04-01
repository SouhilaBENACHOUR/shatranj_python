"""
i18n.py - Internationalisation (F3)

Role: initialises gettext, detects the language from LANG/LC_ALL,
      exposes the _() function for all translations.

Behaviour (F3 of the specification):
  - Default language: English (en)
  - French supported: fr
  - If LANG or LC_ALL is set → use that language
  - If the language is not supported → warning on stderr + English

Usage in other modules:
    from shatranj.i18n import _
    print(_("Welcome to Shatranj!"))
"""

import gettext
import locale
import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DOMAIN = "shatranj"
LOCALES_DIR = Path(__file__).parent / "i18n"
SUPPORTED_LANGUAGES = {"en", "fr"}
DEFAULT_LANGUAGE = "en"

# ---------------------------------------------------------------------------
# Language detection
# ---------------------------------------------------------------------------


def _detect_language() -> str:
    """
    Detect the language from environment variables.

    Priority: LC_ALL > LANG > default (en)
    Only the first two characters are used (e.g. 'fr_FR.UTF-8' → 'fr').
    """
    for var in ("LC_ALL", "LANG"):
        value = os.environ.get(var, "")
        if value:
            # Extract language code: 'fr_FR.UTF-8' → 'fr'
            lang = value.split("_")[0].split(".")[0].lower()
            if lang:
                return lang

    # Fallback: ask Python's locale module
    try:
        lang, _ = locale.getlocale()
        if lang:
            return lang[:2].lower()
    except Exception:
        pass

    return DEFAULT_LANGUAGE


# ---------------------------------------------------------------------------
# Initialisation
# ---------------------------------------------------------------------------


def setup(language: str | None = None) -> gettext.GNUTranslations:
    """
    Initialise gettext and install _() as a builtin.

    Parameters
    ----------
    language:
        Force a specific language code (e.g. 'fr').
        If None, auto-detect from environment.

    Returns
    -------
    The active GNUTranslations object.
    """
    if language is None:
        language = _detect_language()

    # Warn and fall back if language is not supported
    if language not in SUPPORTED_LANGUAGES:
        print(
            f"Warning: language '{language}' is not supported. "
            f"Falling back to English.",
            file=sys.stderr,
        )
        language = DEFAULT_LANGUAGE

    try:
        translation = gettext.translation(
            domain=DOMAIN,
            localedir=str(LOCALES_DIR),
            languages=[language],
        )
    except FileNotFoundError:
        # .mo file missing — use NullTranslations (returns strings unchanged)
        translation = gettext.NullTranslations()

    # Install _() as a builtin so all modules can use it without importing
    translation.install()
    return translation


# ---------------------------------------------------------------------------
# Convenience: module-level _() for direct imports
# ---------------------------------------------------------------------------

# This is initialised with a NullTranslations by default.
# Call setup() at startup to activate the real translations.
_ = gettext.gettext
