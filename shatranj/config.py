"""
config.py - Gestion du fichier de configuration .shatranjrc

Role: lit, crée et valide le fichier de configuration INI
      situé dans le répertoire HOME de l'utilisateur.

Comportement (F2 du cahier des charges) :
  - Lu au démarrage s'il est présent.
  - Créé automatiquement (minimal) s'il est absent.
  - Si présent mais invalide → avertissement sur stderr, pas d'écrasement.
  - Les options CLI supplantent toujours les valeurs du fichier.

Format du fichier :
  [defaults]
  verbose = false
  debug = false
  blitz = false
  timeout = 30
  ai-mode = alphabeta
  ai-depth = 3
  ai-scoring = advanced
  language = en
"""

import configparser
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

CONFIG_FILENAME = ".shatranjrc"

# Valeurs par défaut utilisées si la clé est absente du fichier
DEFAULTS: dict[str, str] = {
    "verbose": "false",
    "debug": "false",
    "blitz": "false",
    "timeout": "30",
    "ai-mode": "alphabeta",
    "ai-depth": "3",
    "ai-scoring": "advanced",
    "language": "en",
}

# Valeurs autorisées pour les clés à choix restreint
VALID_VALUES: dict[str, set[str]] = {
    "ai-mode": {"minimax", "alphabeta", "mcts"},
    "ai-scoring": {"material", "positional", "advanced"},
    "language": {"en", "fr"},
}

# Contenu du fichier de configuration minimal créé automatiquement
MINIMAL_CONFIG = """\
# Shatranj configuration file
# Lines starting with '#' are comments.

[defaults]
verbose = false
debug = false
blitz = false
timeout = 30
ai-mode = alphabeta
ai-depth = 3
ai-scoring = advanced
language = en
"""


# ---------------------------------------------------------------------------
# Classe principale
# ---------------------------------------------------------------------------


class ShatranjConfig:
    """
    Reads, validates, and exposes the .shatranjrc configuration file.

    Usage::

        cfg = ShatranjConfig()          # load (or create) the config file
        verbose = cfg.get_bool("verbose")
        ai_mode = cfg.get_str("ai-mode")

    CLI overrides are applied *after* loading via apply_args().
    """

    def __init__(self, config_path: Path | None = None) -> None:
        """
        Load (or create) the configuration file.

        Parameters
        ----------
        config_path:
            Override the default ~/.shatranjrc path (useful for tests).
        """
        if config_path is None:
            config_path = Path.home() / CONFIG_FILENAME

        self._path = config_path
        self._values: dict[str, str] = dict(DEFAULTS)  # start with defaults
        self._load()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_str(self, key: str) -> str:
        """Return a config value as a string."""
        return self._values.get(key, DEFAULTS.get(key, ""))

    def get_bool(self, key: str) -> bool:
        """Return a config value as a boolean."""
        return self._values.get(key, "false").lower() in ("true", "1", "yes")

    def get_int(self, key: str) -> int:
        """Return a config value as an integer (falls back to 0 on error)."""
        try:
            return int(self._values.get(key, DEFAULTS.get(key, "0")))
        except ValueError:
            return 0

    def apply_args(self, args) -> None:
        """
        Override config values with CLI arguments.

        Only overrides a key if the CLI flag was explicitly provided
        (i.e. the value differs from argparse's own default).

        Parameters
        ----------
        args:
            The namespace returned by argparse.parse_args().
        """
        # Boolean flags: only override if explicitly set on CLI
        mapping_bool = {
            "verbose": "verbose",
            "debug": "debug",
            "blitz": "blitz",
        }
        for arg_attr, cfg_key in mapping_bool.items():
            val = getattr(args, arg_attr, None)
            if val:  # True means the flag was passed
                self._values[cfg_key] = "true"

        # Integer flags
        if getattr(args, "time", None) is not None:
            # Only override if -t was explicitly given
            if "--time" in sys.argv or "-t" in sys.argv:
                self._values["timeout"] = str(args.time)

        # String flags
        if getattr(args, "ai_mode", None) is not None:
            if "--ai-mode" in sys.argv:
                self._values["ai-mode"] = args.ai_mode.lower()

        if getattr(args, "ai_depth", None) is not None:
            self._values["ai-depth"] = str(args.ai_depth)

        if getattr(args, "ai_scoring", None) is not None:
            if "--ai-scoring" in sys.argv:
                self._values["ai-scoring"] = args.ai_scoring.lower()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _load(self) -> None:
        """Read the config file, create it if missing, warn if invalid."""
        if not self._path.exists():
            self._create_minimal()
            return

        parser = configparser.ConfigParser()

        try:
            parser.read(self._path, encoding="utf-8")
        except configparser.Error as exc:
            print(
                f"Warning: could not parse '{self._path}': {exc}. "
                "Using default configuration.",
                file=sys.stderr,
            )
            return

        if "defaults" not in parser:
            print(
                f"Warning: '{self._path}' has no [defaults] section. "
                "Using default configuration.",
                file=sys.stderr,
            )
            return

        section = parser["defaults"]
        errors: list[str] = []

        for key, default in DEFAULTS.items():
            raw = section.get(key, default).strip()

            # Validate restricted-choice keys
            if key in VALID_VALUES and raw.lower() not in VALID_VALUES[key]:
                errors.append(
                    f"  '{key}' has invalid value '{raw}'. "
                    f"Allowed: {', '.join(sorted(VALID_VALUES[key]))}. "
                    f"Using default '{default}'."
                )
                raw = default

            # Validate boolean keys
            if key in ("verbose", "debug", "blitz"):
                if raw.lower() not in ("true", "false", "1", "0", "yes", "no"):
                    errors.append(
                        f"  '{key}' has invalid boolean value '{raw}'. "
                        f"Using default '{default}'."
                    )
                    raw = default

            # Validate integer keys
            if key in ("timeout", "ai-depth"):
                try:
                    int(raw)
                except ValueError:
                    errors.append(
                        f"  '{key}' has invalid integer value '{raw}'. "
                        f"Using default '{default}'."
                    )
                    raw = default

            self._values[key] = raw

        if errors:
            print(
                f"Warning: '{self._path}' contains invalid values:",
                file=sys.stderr,
            )
            for err in errors:
                print(err, file=sys.stderr)
            print("Invalid keys replaced by their defaults.", file=sys.stderr)

    def _create_minimal(self) -> None:
        """Create a minimal config file in HOME."""
        try:
            self._path.write_text(MINIMAL_CONFIG, encoding="utf-8")
        except OSError as exc:
            print(
                f"Warning: could not create '{self._path}': {exc}.",
                file=sys.stderr,
            )
