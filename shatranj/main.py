"""
main.py - Point d'entrée du programme Shatranj

Rôle : gère les options de ligne de commande (F1, F4 du cahier des charges)
       puis lance l'interface appropriée (CLI par défaut).

Pourquoi argparse ?
  Le cahier des charges (section 1.12) impose argparse pour Python.
  argparse gère automatiquement -h/--help et les messages d'erreur.

Options gérées (F1) :
  -h / --help     : affiche l'aide
  -V / --version  : affiche la version
  -v / --verbose  : mode verbeux
  -d / --debug    : mode debug
  -b / --blitz    : mode blitz (F5)
  -t / --time     : temps en minutes pour le blitz (F5)
  -g / --gui      : interface graphique (F7) - pas encore implémentée
  -a / --ai       : joueur artificiel (F8) - pas encore implémenté
"""

import argparse
import sys

# Version du programme 
VERSION = "0.1.0"


def build_argument_parser() -> argparse.ArgumentParser:
    """
    Construit et retourne le parser d'arguments.

    On sépare la construction du parser de son utilisation
    pour faciliter les tests unitaires.
    """
    parser = argparse.ArgumentParser(
        prog="shatranj",
        description="Shatranj - Indian Chess game",
        # epilog affiché après la liste des options dans --help
        epilog="Examples:\n"
               "  shatranj              Start a new game (CLI)\n"
               "  shatranj -b -t 15    Start a blitz game (15 min per player)\n"
               "  shatranj save.shatranj  Resume a saved game\n",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # -V / --version : affiche la version et quitte (F1)
    parser.add_argument(
        "-V", "--version",
        action="version",
        version=f"%(prog)s {VERSION}",
    )

    # -v / --verbose : augmente la verbosité (F1)
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",         # True si présent, False sinon
        default=False,
        help="Increase verbosity",
    )

    # -d / --debug : affiche les messages de debug (F1)
    parser.add_argument(
        "-d", "--debug",
        action="store_true",
        default=False,
        help="Enable debug messages",
    )

    # -b / --blitz : mode blitz (F5)
    parser.add_argument(
        "-b", "--blitz",
        action="store_true",
        default=False,
        help="Start a blitz game (timed)",
    )

    # -t / --time : temps en minutes pour le blitz (F5)
    parser.add_argument(
        "-t", "--time",
        type=int,
        default=30,
        metavar="TIME",
        help="Time limit in minutes for blitz mode (default: 30)",
    )

    # -g / --gui : interface graphique (F7)
    parser.add_argument(
        "-g", "--gui",
        action="store_true",
        default=False,
        help="Launch the graphical interface (not yet implemented)",
    )

    # -a / --ai : joueur artificiel (F8)
    # nargs="?" signifie : optionnel, avec une valeur possible
    parser.add_argument(
        "-a", "--ai",
        nargs="?",           # 0 ou 1 argument
        const="black",       # valeur si -a sans argument
        default=None,        # valeur si -a absent
        metavar="COLOR",
        help="Replace player COLOR with AI (default: black). "
             "Colors: white, black, all",
    )

    # -c / --contest : mode contest (F6)
    parser.add_argument(
        "-c", "--contest",
        action="store_true",
        default=False,
        help="Contest mode: read a position from a file and output the best move",
    )

    # Argument positionnel optionnel : fichier de sauvegarde (F4)
    parser.add_argument(
        "savefile",
        nargs="?",           # 0 ou 1 argument positionnel
        default=None,
        metavar="SAVEFILE",
        help="Save file to load at startup",
    )

    return parser


def main() -> int:
    """
    Point d'entrée principal.

    Retourne 0 en cas de succès, 1 en cas d'erreur (F1).
    """
    parser = build_argument_parser()
    args = parser.parse_args()

    # --- Validation des options ---

    # F5 : -t sans -b affiche un avertissement
    # (on vérifie si --time a été explicitement donné)
    time_given_explicitly = "--time" in sys.argv or "-t" in sys.argv
    if time_given_explicitly and not args.blitz:
        print(
            "Warning: --time is ignored without --blitz (-b).",
            file=sys.stderr,
        )

    # --- Lancement de l'interface ---

    if args.gui:  # ← 4 espaces, CORRECT
        try:
            from shatranj.presentation.gui.app import run_gui
            return run_gui()
        except ModuleNotFoundError:
            print("Error: GUI requires GTK which is not available on Windows.", file=sys.stderr)
            print("Please use Linux or WSL to run the GUI.", file=sys.stderr)
            return 1

    # Par défaut : interface CLI
    # On importe ici pour éviter les imports circulaires
    from shatranj.presentation.cli.cli import CLI

    cli = CLI(verbose=args.verbose, debug=args.debug)

    # Si un fichier de sauvegarde est donné, on le charge automatiquement (F4)
    if args.savefile:
        # On simule la commande "load FILE"
        cli._do_load([args.savefile])

    # Lance la boucle interactive
    cli.run()

    return 0


if __name__ == "__main__":
    # sys.exit() convertit le code de retour int en exit code du processus
    sys.exit(main())