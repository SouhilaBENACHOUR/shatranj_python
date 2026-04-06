"""
main.py - Point d'entrée du programme Shatranj

Role: handles command-line options (F1, F4 of the specification)
      then launches the appropriate interface (CLI by default).

Why argparse?
  The specification (section 1.12) requires argparse for Python.
  argparse automatically handles -h/--help and error messages.

Options handled (F1):
  -h / --help        : show help
  -V / --version     : show version
  -v / --verbose     : verbose mode
  -d / --debug       : debug mode
  -b / --blitz       : blitz mode (F5)
  -t / --time        : time in minutes for blitz (F5)
  -g / --gui         : graphical interface (F7)
  -a / --ai          : AI player color: W or B (F8)
  --ai-mode          : AI algorithm: minimax, alphabeta, mcts, iterative
  --ai-depth         : search depth for minimax/alphabeta/iterative
  --ai-scoring       : evaluation function: material, positional, advanced
"""

import argparse
import sys

from shatranj.config import ShatranjConfig

VERSION = "0.4.0"


def build_argument_parser() -> argparse.ArgumentParser:
    """
    Build and return the argument parser.

    We separate the parser construction from its use
    to make unit testing easier.
    """
    parser = argparse.ArgumentParser(
        prog="shatranj",
        description="Shatranj - Indian Chess game",
        epilog="Examples:\n"
        "  shatranj "
        "  shatranj -a B"
        "  shatranj -a W --ai-mode minimax "
        "  shatranj -a B --ai-mode mcts "
        "  shatranj -a W --ai-mode iterative"
        "  shatranj -a W --ai-mode minimax --ai-depth 6"
        "  shatranj -a W --ai-mode iterative --ai-depth 6"
        "  shatranj -a W --ai-scoring material"
        "  shatranj -a W --ai-scoring positional"
        "  shatranj -a W --ai-scoring advanced"
        "  shatranj -b -t 15",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # -V / --version
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"%(prog)s {VERSION}",
    )

    # -v / --verbose
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        default=False,
        help="Increase verbosity",
    )

    # -d / --debug
    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        default=False,
        help="Enable debug messages",
    )

    # -b / --blitz
    parser.add_argument(
        "-b",
        "--blitz",
        action="store_true",
        default=False,
        help="Start a blitz game (timed)",
    )

    # -t / --time
    parser.add_argument(
        "-t",
        "--time",
        type=int,
        default=30,
        metavar="TIME",
        help="Time limit in minutes for blitz mode (default: 30)",
    )

    # -g / --gui
    parser.add_argument(
        "-g",
        "--gui",
        action="store_true",
        default=False,
        help="Launch the graphical interface",
    )

    # -a / --ai : color of the AI player (W or B)
    parser.add_argument(
        "-a",
        "--ai",
        nargs="?",
        const="B",
        default=None,
        metavar="COLOR",
        help="Replace player COLOR with AI. Colors: W (white), B (black)",
    )

    # --ai-mode : AI algorithm
    parser.add_argument(
        "--ai-mode",
        default=None,
        metavar="MODE",
        help="AI algorithm: minimax, alphabeta, mcts, iterative",
    )

    # --ai-depth : search depth
    parser.add_argument(
        "--ai-depth",
        type=int,
        default=None,
        metavar="DEPTH",
        help="Search depth for minimax/alphabeta/iterative"
        " (default: 3 for minimax, 4 for alphabeta/iterative)",
    )

    # --ai-scoring : evaluation function
    parser.add_argument(
        "--ai-scoring",
        default=None,
        metavar="SCORING",
        help="Evaluation function: material, positional, advanced (default)",
    )

    # -c / --contest
    parser.add_argument(
        "-c",
        "--contest",
        action="store_true",
        default=False,
        help="Contest mode: read a position from a"
        "file and output the best " "move",
    )

    # positional: save file
    parser.add_argument(
        "savefile",
        nargs="?",
        default=None,
        metavar="SAVEFILE",
        help="Save file to load at startup",
    )

    return parser


def main() -> int:
    """
    Main entry point.

    Returns 0 on success, 1 on error (F1).
    """
    # F3 — Internationalisation (doit être fait EN PREMIER)
    from shatranj.i18n import setup as i18n_setup
    cfg = ShatranjConfig()
    parser = build_argument_parser()
    args = parser.parse_args()
    cfg.apply_args(args)
    language = cfg.get_str("language")
    i18n_setup(language=language)

    # ------------------------------------------------------------------
    # F2 — Load (or create) the configuration file
    # ------------------------------------------------------------------
    cfg = ShatranjConfig()
    parser = build_argument_parser()
    args = parser.parse_args()

    # Apply CLI overrides on top of the config values
    cfg.apply_args(args)

    # ------------------------------------------------------------------
    # Resolve final values (config merged with CLI)
    # ------------------------------------------------------------------
    verbose = cfg.get_bool("verbose")
    debug = cfg.get_bool("debug")
    blitz = cfg.get_bool("blitz")
    timeout_minutes = cfg.get_int("timeout")
    ai_mode = (
        args.ai_mode
        if args.ai_mode is not None
        else cfg.get_str("ai-mode")
    )
    ai_depth = (
        args.ai_depth
        if args.ai_depth is not None
        else cfg.get_int("ai-depth")
    )
    ai_scoring = (
        args.ai_scoring
        if args.ai_scoring is not None
        else cfg.get_str("ai-scoring")
    )

    # -t without -b: warning
    time_given_explicitly = "--time" in sys.argv or "-t" in sys.argv
    if time_given_explicitly and not args.blitz:
        print(
            "Warning: --time is ignored without --blitz (-b).",
            file=sys.stderr,
        )

    # --- Contest mode (F6) ---
    if args.contest:
        if not args.savefile:
            print(
                "Error: contest mode requires a position file.",
                file=sys.stderr,
            )
            return 1
        from shatranj.presentation.cli.cli import CLI

        cli = CLI(verbose=False, debug=False)
        return cli._do_contest(
            path=args.savefile,
            algo=ai_mode.lower(),
            depth=ai_depth,
            scoring=ai_scoring.lower(),
        )

    # --- Launch interface ---

    if args.gui:
        try:
            from shatranj.presentation.gui.app import run_gui

            return run_gui(blitz=args.blitz, blitz_time_minutes=args.time)
        except ModuleNotFoundError:
            print(
                "Error: GUI requires GTK which is not available on Windows.",
                file=sys.stderr,
            )
            print("Please use Linux or WSL to run the GUI.", file=sys.stderr)
            return 1

    from shatranj.presentation.cli.cli import CLI

    cli = CLI(
        verbose=args.verbose,
        debug=args.debug,
        blitz=args.blitz,
        blitz_time_minutes=args.time
    )
    cli = CLI(verbose=verbose, debug=debug)
    if blitz:
        cli.enable_blitz(timeout_minutes)

    # configure AI if -a is given
    if args.ai:
        ai_color = args.ai.upper()
        if ai_color not in ("W", "B"):
            print(
                f"Error: invalid color '{args.ai}'. Use W or B.",
                file=sys.stderr,
            )
            return 1

        algo = ai_mode.lower()
        if algo not in ("minimax", "alphabeta", "mcts", "iterative"):
            print(
                f"Error: unknown algorithm '{algo}'. Use minimax, "
                "alphabeta, mcts or iterative.",
                file=sys.stderr,
            )
            return 1

        scoring = ai_scoring.lower()
        if scoring not in ("material", "positional", "advanced"):
            print(f"Error: unknown scoring '{scoring}'.", file=sys.stderr)
            return 1

        # default depth depending on algorithm
        if ai_depth is not None:
            depth = ai_depth
        elif algo in ("alphabeta", "iterative"):
            depth = 4
        elif algo == "mcts":
            depth = 500
        else:
            depth = 3

        color_str = "white" if ai_color == "W" else "black"

        # store AI config to launch inside run() — avoids double board display
        cli._pending_new = ["ai", color_str, algo, str(depth), scoring]

    elif args.blitz:
        cli._pending_new = []

    if args.savefile:
        cli._do_load([args.savefile])

    cli.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
