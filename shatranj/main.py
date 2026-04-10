"""
main.py - Program entry point.

Role: handle command-line options, merge them with configuration values,
then launch the requested interface.
"""

import argparse
import sys
import time

from shatranj.config import ShatranjConfig

VERSION = "0.4.0"
VALID_AI_ALGOS = ("minimax", "alphabeta", "mcts", "iterative")
VALID_AI_SCORING = ("material", "positional", "advanced")
VALID_AI_SELECTIONS = ("uct", "ucb1")


def build_argument_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser."""

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
        "  shatranj -a A --ai-mode mcts --ai-depth 200"
        "  shatranj -a W --ai-mode iterative --ai-time 5"
        "  shatranj -a W --ai-scoring material"
        "  shatranj -a W --ai-scoring positional"
        "  shatranj -a W --ai-scoring advanced"
        "  shatranj -b -t 15",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"%(prog)s {VERSION}",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        default=False,
        help="Increase verbosity",
    )
    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        default=False,
        help="Enable debug messages",
    )
    parser.add_argument(
        "-b",
        "--blitz",
        action="store_true",
        default=False,
        help="Start a blitz game (timed)",
    )
    parser.add_argument(
        "-t",
        "--time",
        type=int,
        default=30,
        metavar="TIME",
        help="Time limit in minutes for blitz mode (default: 30)",
    )
    parser.add_argument(
        "-g",
        "--gui",
        action="store_true",
        default=False,
        help="Launch the graphical interface",
    )
    parser.add_argument(
        "-s",
        "--server",
        nargs="?",
        const=12345,
        default=None,
        type=int,
        metavar="PORT",
        help="Start the multiplayer server on PORT (default: 12345)",
    )
    parser.add_argument(
        "--daemon",
        action="store_true",
        default=False,
        help="Run the multiplayer server without launching CLI or GUI",
    )
    parser.add_argument(
        "-a",
        "--ai",
        nargs="?",
        const="B",
        default=None,
        metavar="COLOR",
        help=(
            "Replace player COLOR with AI. "
            "Colors: W (white), B (black), A (all)"
        ),
    )
    parser.add_argument(
        "--ai-mode",
        default=None,
        metavar="MODE",
        help="AI algorithm: minimax, alphabeta, mcts, iterative",
    )
    parser.add_argument(
        "--ai-depth",
        type=int,
        default=None,
        metavar="DEPTH",
        help="Search depth for minimax/alphabeta/iterative"
        " (default: 3 for minimax, 4 for alphabeta/iterative)",
    )
    parser.add_argument(
        "--ai-scoring",
        default=None,
        metavar="SCORING",
        help="Evaluation function: material, positional, advanced (default)",
    )
    parser.add_argument(
        "--ai-minimax-depth",
        dest="ai_minimax_depth",
        type=int,
        default=None,
        metavar="DEPTH",
        help="Alias of --ai-depth for minimax-style searches",
    )
    parser.add_argument(
        "--ai-minimax-scoring",
        dest="ai_minimax_scoring",
        default=None,
        metavar="SCORING",
        help="Alias of --ai-scoring for minimax-style searches",
    )
    parser.add_argument(
        "--ai-time",
        type=float,
        default=None,
        metavar="SECONDS",
        help="Per-move time limit used by iterative AI",
    )
    parser.add_argument(
        "--ai-mcts-selection",
        default=None,
        metavar="POLICY",
        help="MCTS selection policy (uct by default)",
    )
    parser.add_argument(
        "-c",
        "--contest",
        action="store_true",
        default=False,
        help=(
            "Contest mode: read a position from a file "
            "and output the best move"
        ),
    )
    parser.add_argument(
        "savefile",
        nargs="?",
        default=None,
        metavar="SAVEFILE",
        help="Save file to load at startup",
    )
    return parser


def _resolve_ai_depth(args, cfg: ShatranjConfig) -> int:
    depth = args.ai_minimax_depth
    if depth is None:
        depth = args.ai_depth
    if depth is not None:
        return depth
    return cfg.get_int("ai-depth")


def _resolve_ai_scoring(args, cfg: ShatranjConfig) -> str:
    scoring = args.ai_minimax_scoring
    if scoring is None:
        scoring = args.ai_scoring
    if scoring is not None:
        return scoring
    return cfg.get_str("ai-scoring")


def main() -> int:
    """Run the configured interface and return an exit status."""

    from shatranj.i18n import setup as i18n_setup

    cfg = ShatranjConfig()
    parser = build_argument_parser()
    args = parser.parse_args()
    cfg.apply_args(args)
    lang = cfg.get_str("language") or None
    i18n_setup(language=lang)
    if args.server is not None:
        from shatranj.domain.network import DiscoveryServer, GameServer

        port = args.server
        server_name = "ShatranjServer"
        discovery = DiscoveryServer(server_name, port, VERSION)
        server = GameServer(server_name, port)

        discovery.start()
        server.start()

        if not args.daemon:
            print(f"Starting Shatranj server on TCP {port} / UDP 12346...")
            print("Press Ctrl+C to stop the server.")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            server.stop()
            discovery.stop()
        return 0

    verbose = cfg.get_bool("verbose")
    debug = cfg.get_bool("debug")
    blitz = cfg.get_bool("blitz")
    timeout_minutes = cfg.get_int("timeout")
    ai_mode = (
        args.ai_mode if args.ai_mode is not None else cfg.get_str("ai-mode")
    )
    ai_depth = _resolve_ai_depth(args, cfg)
    ai_scoring = _resolve_ai_scoring(args, cfg)
    ai_time = args.ai_time
    ai_selection = (
        args.ai_mcts_selection.lower()
        if args.ai_mcts_selection is not None
        else "uct"
    )

    if ("--time" in sys.argv or "-t" in sys.argv) and not args.blitz:
        print(
            "Warning: --time is ignored without --blitz (-b).",
            file=sys.stderr,
        )

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

    if args.gui:
        try:
            from shatranj.presentation.gui.app import run_gui

            return run_gui(
                blitz=blitz,
                blitz_time_minutes=timeout_minutes,
            )
        except ModuleNotFoundError:
            print(
                "Error: GUI requires GTK which is not available on Windows.",
                file=sys.stderr,
            )
            print("Please use Linux or WSL to run the GUI.", file=sys.stderr)
            return 1

    from shatranj.presentation.cli.cli import CLI

    cli = CLI(
        verbose=verbose,
        debug=debug,
        blitz=blitz,
        blitz_time_minutes=timeout_minutes,
    )

    if args.ai:
        ai_color = args.ai.upper()
        if ai_color not in ("W", "B", "A"):
            print(
                f"Error: invalid color '{args.ai}'. Use W, B or A.",
                file=sys.stderr,
            )
            return 1

        algo = ai_mode.lower()
        if algo not in VALID_AI_ALGOS:
            print(
                f"Error: unknown algorithm '{algo}'. Use minimax, "
                "alphabeta, mcts or iterative.",
                file=sys.stderr,
            )
            return 1

        scoring = ai_scoring.lower()
        if scoring not in VALID_AI_SCORING:
            print(f"Error: unknown scoring '{scoring}'.", file=sys.stderr)
            return 1

        if ai_depth < 1:
            print(
                "Error: AI depth must be a positive integer.", file=sys.stderr
            )
            return 1

        if ai_time is not None and ai_time <= 0:
            print("Error: AI time must be greater than 0.", file=sys.stderr)
            return 1

        if ai_selection not in VALID_AI_SELECTIONS:
            print(
                f"Error: unknown MCTS selection '{ai_selection}'.",
                file=sys.stderr,
            )
            return 1

        extra_args = []
        if ai_time is not None:
            extra_args.append(f"time={ai_time}")
        if args.ai_mcts_selection is not None:
            extra_args.append(f"selection={ai_selection}")

        if ai_color == "A":
            cli._pending_new = [
                "ai-vs-ai",
                algo,
                str(ai_depth),
                scoring,
                *extra_args,
            ]
        else:
            color_str = "white" if ai_color == "W" else "black"
            cli._pending_new = [
                "ai",
                color_str,
                algo,
                str(ai_depth),
                scoring,
                *extra_args,
            ]
    elif blitz:
        cli._pending_new = []

    if args.savefile:
        cli._do_load([args.savefile])

    cli.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
