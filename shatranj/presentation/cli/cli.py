"""
cli.py - Shell interactif du jeu Shatranj

Rôle : c'est le point d'entrée de l'interface CLI.
       Il lit les commandes de l'utilisateur et appelle les bonnes méthodes.

Pourquoi un shell interactif ?
  Le cahier des charges (F14) demande un shell avec un prompt ">>".
  readline (F16, F17, F18) gère l'édition de ligne, l'historique,
  et la complétion Tab automatiquement.

Structure générale :
  - run()          : boucle principale (lire -> parser -> exécuter)
  - _do_XXX()      : une méthode par commande
  - _parse_move()  : convertit "e2-e4" en objet Move
"""

import readline  # Active l'édition de ligne, l'historique, et le Tab
import re        # Pour parser la notation algébrique avec une regex
import sys       # Pour sys.exit() et sys.stderr

from shatranj.domain.core.move import Move
from shatranj.domain.rules.rules_engine import RulesEngine
from shatranj.utils.constants import WHITE, BLACK
from shatranj.domain.core.board import Board
from shatranj.utils.constants import WHITE, BLACK, SHAH, FERZ, ROOK, ALFIL, KNIGHT, PAWN

# Import de nos propres modules
# On utilise des imports relatifs car on est dans le même package
from .display import print_board, board_to_string
from .game_state import GameState


# ---------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------

PROMPT = ">> "  # Le prompt affiché à l'utilisateur (F14)

# Liste de toutes les commandes reconnues (pour la complétion Tab, F18)
COMMANDS = [
    "new", "help", "quit", "load", "save",
    "pause", "hint", "undo", "redo",
    "show board", "show history", "show time", "show configuration",
    "set",
]


# ---------------------------------------------------------------------
# Classe principale du CLI
# ---------------------------------------------------------------------

class CLI:
    """
    Shell interactif pour jouer au Shatranj en ligne de commande.

    Attributs :
      _state   : l'état de la partie en cours (GameState)
      _engine  : le moteur de règles (RulesEngine)
      _running : True tant que la boucle tourne
      _saved   : True si la partie a été sauvegardée depuis le dernier coup
      _verbose : True si le mode verbeux est activé
    """

    def __init__(self, verbose: bool = False, debug: bool = False) -> None:
        self._state: GameState | None = None   # Pas de partie au démarrage
        self._engine = RulesEngine()
        self._running = False
        self._saved = True          # Rien à sauvegarder au démarrage
        self._verbose = verbose
        self._debug = debug

        # Configuration de readline pour la complétion Tab (F18)
        readline.set_completer(self._completer)
        readline.parse_and_bind("tab: complete")

        # Configuration de readline pour l'historique (F17)
        # Ctrl+R est géré automatiquement par readline

    # ------------------------------------------------------------------
    # Boucle principale
    # ------------------------------------------------------------------

    def run(self) -> None:
        """
        Lance la boucle principale du shell.

        On affiche un message de bienvenue, puis on lit les commandes
        une par une jusqu'à ce que l'utilisateur tape "quit".
        """
        self._running = True
        print("Welcome to Shatranj! Type 'help' to see available commands.")
        print("Start a new game with 'new'.")
        print()

        while self._running:
            try:
                # input() avec readline actif gère l'édition et l'historique
                raw = input(PROMPT).strip()
            except EOFError:
                # Ctrl+D : on quitte proprement
                print()
                self._do_quit([])
                break
            except KeyboardInterrupt:
                # Ctrl+C : on passe à la ligne suivante sans quitter
                print()
                continue

            # On ignore les lignes vides
            if not raw:
                continue

            # Ajout à l'historique readline (pour les flèches haut/bas)
            readline.add_history(raw)

            # Parsing et exécution de la commande
            self._dispatch(raw)

    # ------------------------------------------------------------------
    # Dispatcher : analyse la commande et appelle la bonne méthode
    # ------------------------------------------------------------------

    def _dispatch(self, raw: str) -> None:
        """
        Analyse la ligne de commande et appelle la méthode correspondante.

        On sépare d'abord les mots, puis on regarde le premier mot
        pour identifier la commande.

        Cas spéciaux :
          - "show board" et "show history" sont des commandes en deux mots
          - Un coup comme "e2-e4" n'est pas un mot-clé
        """
        parts = raw.split()
        if not parts:
            return

        cmd = parts[0].lower()
        args = parts[1:]  # Arguments après la commande

        # Commandes en deux mots : "show board", "show history", ...
        if cmd == "show":
            sub = args[0].lower() if args else ""
            if sub == "board":
                self._do_show_board()
            elif sub == "history":
                self._do_show_history()
            elif sub == "time":
                self._do_show_time()
            elif sub == "configuration":
                self._do_show_configuration()
            else:
                self._error(f"Unknown subcommand: show {sub}")
            return

        # Commandes en un mot
        handlers = {
            "new":    self._do_new,
            "help":   self._do_help,
            "quit":   self._do_quit,
            "q":      self._do_quit,     
            "load":   self._do_load,
            "save":   self._do_save,
            "pause":  self._do_pause,
            "hint":   self._do_hint,
            "undo":   self._do_undo,
            "redo":   self._do_redo,
            "set":    self._do_set,
        }

        if cmd in handlers:
            handlers[cmd](args)
            return

        # Si ce n'est pas une commande connue, on essaie de parser un coup
        # Format attendu : "e2-e4" ou "e2xe4"
        if self._looks_like_move(raw):
            self._do_play_move(raw)
            return

        # Commande inconnue
        self._error(f"Unknown command: '{raw}'. Type 'help' for the list of commands.")

    # ------------------------------------------------------------------
    # Vérifier si une chaîne ressemble à un coup (notation algébrique)
    # ------------------------------------------------------------------

    def _looks_like_move(self, text: str) -> bool:
        """
        Retourne True si le texte ressemble à un coup en notation algébrique.

        Formats acceptés (F19 du cahier des charges) :
          - "e2-e4"  : déplacement simple
          - "e2xe4"  : capture (x minuscule)
          - "Ng8-f6" : avec préfixe de pièce (optionnel)
        """
        # Regex : optionnellement une lettre de pièce, puis case-séparateur-case
        pattern = r"^[A-Za-z]?[a-h][1-8][-x][a-h][1-8]$"
        return bool(re.match(pattern, text.strip()))

    # ------------------------------------------------------------------
    # Parser un coup en notation algébrique -> objet Move
    # ------------------------------------------------------------------

    def _parse_move(self, text: str) -> Move | None:
        """
        Convertit une chaîne comme "e2-e4" en objet Move.

        Retourne None si le format est invalide.

        Exemple :
          "e2-e4"  -> from_square=12, to_square=28
          "e2xe4"  -> idem (la capture est détectée automatiquement par le board)

        Pourquoi Board.algebraic_to_square ?
          Cette méthode convertit "e2" -> 12 (rank=1, file=4 -> 1*8+4=12).
          Elle est déjà implémentée dans board.py, on la réutilise.
        """
        from shatranj.domain.core.board import Board

        # On retire le préfixe de pièce si présent (ex: "N" dans "Ng8-f6")
        text = text.strip()
        if len(text) == 6 and text[0].isupper():
            text = text[1:]  # On enlève le "N" : "Ng8-f6" -> "g8-f6"

        # On accepte "-" ou "x" comme séparateur
        if len(text) != 5 or text[2] not in ("-", "x"):
            self._error(f"Invalid move format: '{text}'. Expected format: e2-e4")
            return None

        from_str = text[0:2]  # "e2"
        to_str   = text[3:5]  # "e4"

        try:
            from_sq = Board.algebraic_to_square(from_str)
            to_sq   = Board.algebraic_to_square(to_str)
        except ValueError as err:
            self._error(str(err))
            return None

        # On récupère la pièce sur la case de départ pour construire le Move
        piece_info = self._state.board.get_piece_at(from_sq)
        if piece_info is None:
            self._error(f"No piece on {from_str}.")
            return None

        piece_type, color = piece_info

        # On récupère la pièce capturée (s'il y en a une)
        target = self._state.board.get_piece_at(to_sq)
        captured = target[0] if target is not None else None

        return Move(
            from_square=from_sq,
            to_square=to_sq,
            piece_type=piece_type,
            color=color,
            captured_piece=captured,
        )

    # ------------------------------------------------------------------
    # Commandes
    # ------------------------------------------------------------------

    def _do_play_move(self, text: str) -> None:
        """
        Joue un coup saisi par l'utilisateur.

        Étapes :
          1. Vérifier qu'une partie est en cours
          2. Parser le coup (notation algébrique -> Move)
          3. Vérifier que le coup est légal (RulesEngine)
          4. Appliquer le coup (GameState)
          5. Afficher le plateau mis à jour
        """
        if self._state is None:
            self._error("No game in progress. Type 'new' to start a game.")
            return

        move = self._parse_move(text)
        if move is None:
            return  # L'erreur a déjà été affichée par _parse_move

        # Vérification que c'est le bon joueur qui joue
        if move.color != self._state.current_color:
            self._error(
                f"It's {self._state.current_color}'s turn, not {move.color}'s."
            )
            return

        # Vérification de la légalité du coup
        if not self._engine.is_valid_move(self._state.board, move):
            self._error(f"Illegal move: {text}")
            return

        # Application du coup
        self._state.apply_move(move)
        self._saved = False  # La partie a été modifiée, pas encore sauvegardée

        # Affichage du plateau après le coup
        print_board(self._state.board)
        print(f"\nIt's now {self._state.current_color}'s turn.")

    def _do_new(self, args: list[str]) -> None:
        """
        Lance une nouvelle partie.

        Si une partie non sauvegardée est en cours, on demande confirmation.
        """
        if self._state is not None and not self._saved:
            answer = input("Current game is not saved. Start a new game anyway? [y/N] ")
            if answer.strip().lower() not in ("y", "yes"):
                print("New game cancelled.")
                return

        self._state = GameState()
        self._saved = True
        print("New game started! White plays first.")
        print()
        print_board(self._state.board)
        print()

    def _do_quit(self, args: list[str]) -> None:
        """
        Quitte le programme.

        Si la partie n'est pas sauvegardée, on propose de sauvegarder (F15).
        Si l'utilisateur ne répond pas clairement, on quitte sans sauvegarder
        (le défaut est N, comme indiqué dans le cahier des charges F15).
        """
        if self._state is not None and not self._saved:
            print("Save the game before quitting? [y/N]", end=" ")
            answer = input().strip().lower()

            if answer in ("y", "yes"):
                # On demande le chemin du fichier
                path = input("Enter file path to save: ").strip()
                if path:
                    success = self._save_to_file(path)
                    if not success:
                        # Erreur d'enregistrement : on redemande (F15)
                        answer2 = input("Save failed. Try to save again? [y/N] ").strip().lower()
                        if answer2 in ("y", "yes"):
                            path2 = input("Enter file path to save: ").strip()
                            self._save_to_file(path2)
                else:
                    print("No path given, quitting without saving.")

        print("Goodbye!")
        self._running = False

    def _do_help(self, args: list[str]) -> None:
        """
        Affiche l'aide générale ou l'aide d'une commande spécifique.

        Usage : help [CMD]
        """
        if args:
            cmd = args[0].lower()
            self._print_command_help(cmd)
        else:
            self._print_general_help()

    def _print_general_help(self) -> None:
        """Affiche la liste de toutes les commandes."""
        print("""
Available commands:
  new [ARGS]          Start a new game
  help [CMD]          Show this help or help for CMD
  quit                Quit the program
  load FILE           Load a game from a file
  save FILE           Save the current game to a file
  pause               Pause the blitz timer
  hint                Show a move suggestion
  undo [N]            Undo the last N moves (default: 1)
  redo [N]            Redo the last N undone moves (default: 1)
  show board          Display the current board
  show history        Display the move history
  show time           Display remaining time (blitz mode)
  show configuration  Display current configuration
  set PARAM=VALUE     Change a configuration parameter

To play a move, type it in algebraic notation: e.g. e2-e4 or e2xe4
""")

    def _print_command_help(self, cmd: str) -> None:
        """Affiche l'aide détaillée d'une commande."""
        help_texts = {
            "new":    "new [ARGS]  -  Start a new game. Args: 'ai white', 'ai black'...",
            "quit":   "quit  -  Quit the program. You'll be asked to save if needed.",
            "help":   "help [CMD]  -  Show help. With CMD: show help for that command.",
            "load":   "load FILE  -  Load a saved game from FILE (.shatranj format).",
            "save":   "save FILE  -  Save the current game to FILE.",
            "hint":   "hint  -  Get a move suggestion from the engine.",
            "undo":   "undo [N]  -  Undo the last N moves (default 1).",
            "redo":   "redo [N]  -  Redo the last N undone moves (default 1).",
            "pause":  "pause  -  Pause/resume the blitz timer.",
            "set":    "set PARAM=VALUE  -  Change a setting. E.g.: set debug=true",
        }
        if cmd in help_texts:
            print(help_texts[cmd])
        else:
            self._error(f"Unknown command: '{cmd}'")

    def _do_show_board(self) -> None:
        """Affiche l'état actuel du plateau."""
        if self._state is None:
            self._error("No game in progress. Type 'new' to start a game.")
            return
        print()
        print_board(self._state.board)
        print()

    def _do_show_history(self) -> None:
        """
        Affiche l'historique des coups joués.

        Format (F24 du cahier des charges) :
          W e2-e4 B Ng8-f6
          W d2-d4 B Nf6xe4
          ...
        """
        if self._state is None:
            self._error("No game in progress.")
            return

        history = self._state.get_history()
        if not history:
            print("No moves played yet.")
            return

        from shatranj.domain.core.board import Board

        print("\nMove history:")
        # On regroupe les coups par paires (blanc, noir)
        i = 0
        turn = 1
        while i < len(history):
            line = f"  {turn:3}."

            # Coup blanc
            move = history[i]
            from_alg = Board.square_to_algebraic(move.from_square)
            to_alg   = Board.square_to_algebraic(move.to_square)
            sep = "x" if move.captured_piece else "-"
            line += f"  W {from_alg}{sep}{to_alg}"
            i += 1

            # Coup noir (s'il existe)
            if i < len(history):
                move = history[i]
                from_alg = Board.square_to_algebraic(move.from_square)
                to_alg   = Board.square_to_algebraic(move.to_square)
                sep = "x" if move.captured_piece else "-"
                line += f"  B {from_alg}{sep}{to_alg}"
                i += 1

            print(line)
            turn += 1
        print()

    def _do_show_time(self) -> None:
        """Affiche le temps restant (uniquement en mode blitz)."""
        # Pas encore de mode blitz implémenté : message informatif
        print("Time display is only available in blitz mode (use -b at startup).")

    def _do_show_configuration(self) -> None:
        """Affiche la configuration courante."""
        print(f"\nCurrent configuration:")
        print(f"  verbose = {self._verbose}")
        print(f"  debug   = {self._debug}")
        print()

    def _do_undo(self, args: list[str]) -> None:
        """
        Annule le(s) dernier(s) coup(s).

        Usage : undo [N]
        N est optionnel, vaut 1 par défaut.
        """
        if self._state is None:
            self._error("No game in progress.")
            return

        # Nombre de coups à annuler (1 par défaut)
        n = 1
        if args:
            try:
                n = int(args[0])
                if n < 1:
                    self._error("N must be a positive integer.")
                    return
            except ValueError:
                self._error(f"Invalid number: '{args[0]}'")
                return

        undone = 0
        for _ in range(n):
            move = self._state.undo()
            if move is None:
                print(f"Nothing more to undo (undid {undone} move(s)).")
                break
            undone += 1

        if undone > 0:
            print(f"Undid {undone} move(s).")
            print_board(self._state.board)
            self._saved = False

    def _do_redo(self, args: list[str]) -> None:
        """
        Rejoue le(s) dernier(s) coup(s) annulé(s).

        Usage : redo [N]
        """
        if self._state is None:
            self._error("No game in progress.")
            return

        n = 1
        if args:
            try:
                n = int(args[0])
                if n < 1:
                    self._error("N must be a positive integer.")
                    return
            except ValueError:
                self._error(f"Invalid number: '{args[0]}'")
                return

        redone = 0
        for _ in range(n):
            move = self._state.redo()
            if move is None:
                print(f"Nothing more to redo (redid {redone} move(s)).")
                break
            redone += 1

        if redone > 0:
            print(f"Redid {redone} move(s).")
            print_board(self._state.board)
            self._saved = False

    def _do_hint(self, args: list[str]) -> None:
        """
        Affiche un conseil de coup à jouer.

        Pour l'instant : on retourne le premier coup légal trouvé.
        Dans une vraie IA, on utiliserait Minimax ou MCTS (F31-F35).
        """
        if self._state is None:
            self._error("No game in progress.")
            return

        from shatranj.domain.core.board import Board

        legal_moves = self._engine.generate_legal_moves(
            self._state.board, self._state.current_color
        )
        if not legal_moves:
            print("No legal moves available.")
            return

        # On prend le premier coup légal (simple, pas d'IA pour l'instant)
        suggested = legal_moves[0]
        from_alg = Board.square_to_algebraic(suggested.from_square)
        to_alg   = Board.square_to_algebraic(suggested.to_square)
        sep = "x" if suggested.captured_piece else "-"
        print(f"Hint: {from_alg}{sep}{to_alg}")

    def _do_load(self, args: list[str]) -> None:
        """
        Load a game from a file.
        Usage : load FILE
        """
        if not args:
            self._error("Usage: load FILE")
            return

        path = args[0]

        try:
            with open(path, "r", encoding="ascii") as f:
                lines = [line.strip() for line in f.readlines()]
        except OSError as err:
            self._error(f"Could not open '{path}': {err}")
            return

        # Remove comments and empty lines
        lines = [l for l in lines if l and not l.startswith("#")]

        try:
            # --- Find sections ---
            idx_settings = lines.index("[settings]")
            idx_game     = lines.index("[game]")
            idx_history  = lines.index("[history]")

            # --- Read [settings] ---
            for line in lines[idx_settings + 1 : idx_game]:
                if "=" in line:
                    key, _, val = line.partition("=")
                    key = key.strip().lower()
                    val = val.strip().lower()
                    if key == "verbose":
                        self._verbose = val in ("true", "1", "yes")
                    elif key == "debug":
                        self._debug = val in ("true", "1", "yes")

            # --- Read [game] ---
            game_lines = lines[idx_game + 1 : idx_history]

            # First line = current player color
            color_letter = game_lines[0].strip().upper()
            if color_letter not in ("W", "B"):
                self._error(f"Invalid player color: '{color_letter}'")
                return
            current_color = WHITE if color_letter == "W" else BLACK

            # Next 8 lines = the board (rank 8 at top, rank 1 at bottom)
            board_lines = game_lines[1:9]
            if len(board_lines) != 8:
                self._error("Invalid board format: expected 8 rows")
                return

            # Map piece symbols to (piece_type, color)
            SYMBOL_MAP = {
                "K": (SHAH,   WHITE), "F": (FERZ,   WHITE),
                "R": (ROOK,   WHITE), "A": (ALFIL,  WHITE),
                "N": (KNIGHT, WHITE), "P": (PAWN,   WHITE),
                "k": (SHAH,   BLACK), "f": (FERZ,   BLACK),
                "r": (ROOK,   BLACK), "a": (ALFIL,  BLACK),
                "n": (KNIGHT, BLACK), "p": (PAWN,   BLACK),
            }

            new_board = Board(setup=False)

            for rank_idx, board_line in enumerate(board_lines):
                # rank 8 is at top (rank_idx=0) -> rank=7
                # rank 1 is at bottom (rank_idx=7) -> rank=0
                rank = 7 - rank_idx
                symbols = board_line.split()
                if len(symbols) != 8:
                    self._error(f"Invalid board row {rank_idx + 1}: '{board_line}'")
                    return
                for file_idx, symbol in enumerate(symbols):
                    if symbol == "_":
                        continue  # empty square
                    if symbol not in SYMBOL_MAP:
                        self._error(f"Unknown piece symbol: '{symbol}' at row {rank_idx + 1}")
                        return
                    piece, color = SYMBOL_MAP[symbol]
                    square = rank * 8 + file_idx
                    new_board.place_piece(piece, color, square)

            # --- Read [history] ---
            from shatranj.domain.core.move import Move

            history_moves = []
            for line in lines[idx_history + 1:]:
                # Format: "W e2-e3 B e7-e6"
                tokens = line.split()
                i = 0
                while i + 1 < len(tokens):
                    color_tok = tokens[i].upper()
                    move_tok  = tokens[i + 1]
                    i += 2

                    color = WHITE if color_tok == "W" else BLACK

                    # Parse "e2-e3" or "e2xe3"
                    if len(move_tok) != 5 or move_tok[2] not in ("-", "x"):
                        self._error(f"Invalid move in history: '{move_tok}'")
                        return

                    try:
                        from_sq = Board.algebraic_to_square(move_tok[0:2])
                        to_sq   = Board.algebraic_to_square(move_tok[3:5])
                    except ValueError as err:
                        self._error(f"Invalid square in history: {err}")
                        return

                    # Determine if it's a capture
                    captured = None
                    if move_tok[2] == "x":
                        captured = "unknown"

                    # Get piece type from the reconstructed board
                    piece_info = new_board.get_piece_at(from_sq)
                    if piece_info is not None:
                        piece_type = piece_info[0]
                    else:
                        piece_type = PAWN  # fallback

                    history_moves.append(Move(from_sq, to_sq, piece_type, color, captured))

            # --- Build GameState from loaded data ---
            from shatranj.presentation.cli.game_state import GameState

            new_state = GameState.__new__(GameState)
            new_state.board = new_board
            new_state.current_color = current_color
            new_state._history = [(move, {}) for move in history_moves]
            new_state._redo_stack = []

            self._state = new_state
            self._saved = True

            print(f"Game loaded from '{path}'.")
            print_board(self._state.board)
            print(f"\nIt's {self._state.current_color}'s turn.")

        except ValueError as err:
            self._error(f"Error parsing file '{path}': {err}")
        except Exception as err:
            self._error(f"Unexpected error loading '{path}': {err}")

    def _do_save(self, args: list[str]) -> None:
        """
        Sauvegarde la partie en cours dans un fichier.

        Usage : save FILE
        """
        if self._state is None:
            self._error("No game in progress.")
            return
        if not args:
            self._error("Usage: save FILE")
            return

        path = args[0]
        success = self._save_to_file(path)
        if success:
            self._saved = True

    def _save_to_file(self, path: str) -> bool:
        """
        Sauvegarde la partie dans un fichier texte ASCII (F20-F24).

        Retourne True si la sauvegarde a réussi, False sinon.

        Format du fichier :
          [settings]
          ...
          [game]
          W
          R N A F K A N R
          ...
          [history]
          W e2-e4 B e7-e5
          ...
        """
        from shatranj.domain.core.board import Board
        from shatranj.utils.constants import (
            SHAH, FERZ, ROOK, ALFIL, KNIGHT, PAWN, WHITE, BLACK
        )

        # Symboles des pièces pour la sauvegarde (F23)
        SYMBOLS = {
            (SHAH,   WHITE): "K", (FERZ,   WHITE): "F",
            (ROOK,   WHITE): "R", (ALFIL,  WHITE): "A",
            (KNIGHT, WHITE): "N", (PAWN,   WHITE): "P",
            (SHAH,   BLACK): "k", (FERZ,   BLACK): "f",
            (ROOK,   BLACK): "r", (ALFIL,  BLACK): "a",
            (KNIGHT, BLACK): "n", (PAWN,   BLACK): "p",
        }

        try:
            with open(path, "w", encoding="ascii") as f:
                # --- Section [settings] ---
                f.write("[settings]\n")
                f.write(f"verbose={str(self._verbose).lower()}\n")
                f.write(f"debug={str(self._debug).lower()}\n")
                f.write("\n")

                # --- Section [game] ---
                f.write("[game]\n")
                # Couleur du joueur courant
                f.write(f"{self._state.current_color[0].upper()}\n")

                # Le plateau rang par rang (du rang 8 au rang 1, F23)
                for rank in range(7, -1, -1):
                    row = []
                    for file in range(8):
                        sq = rank * 8 + file
                        piece = self._state.board.get_piece_at(sq)
                        if piece is None:
                            row.append("_")
                        else:
                            row.append(SYMBOLS[piece])
                    f.write(" ".join(row) + "\n")
                f.write("\n")

                # --- Section [history] ---
                f.write("[history]\n")
                history = self._state.get_history()
                # On regroupe par paires (blanc, noir) sur la même ligne (F24)
                i = 0
                while i < len(history):
                    line_parts = []
                    move = history[i]
                    color_letter = "W" if move.color == WHITE else "B"
                    from_alg = Board.square_to_algebraic(move.from_square)
                    to_alg   = Board.square_to_algebraic(move.to_square)
                    sep = "x" if move.captured_piece else "-"
                    line_parts.append(f"{color_letter} {from_alg}{sep}{to_alg}")
                    i += 1

                    if i < len(history):
                        move = history[i]
                        color_letter = "W" if move.color == WHITE else "B"
                        from_alg = Board.square_to_algebraic(move.from_square)
                        to_alg   = Board.square_to_algebraic(move.to_square)
                        sep = "x" if move.captured_piece else "-"
                        line_parts.append(f"{color_letter} {from_alg}{sep}{to_alg}")
                        i += 1

                    f.write(" ".join(line_parts) + "\n")

            print(f"Game saved to '{path}'.")
            return True

        except OSError as err:
            # OSError couvre les erreurs d'écriture (disque plein, permissions...)
            self._error(f"Could not save to '{path}': {err}")
            return False

    def _do_pause(self, args: list[str]) -> None:
        """Met en pause le chronomètre (mode blitz uniquement)."""
        print("Pause is only available in blitz mode.")

    def _do_set(self, args: list[str]) -> None:
        """
        Change un paramètre de configuration.

        Usage : set PARAM=VALUE
        Exemple : set debug=true
        """
        if not args:
            self._error("Usage: set PARAM=VALUE")
            return

        setting = args[0]
        if "=" not in setting:
            self._error(f"Invalid format: '{setting}'. Expected: PARAM=VALUE")
            return

        param, _, value = setting.partition("=")
        param = param.strip().lower()
        value = value.strip().lower()

        if param == "verbose":
            self._verbose = value in ("true", "1", "yes")
            print(f"verbose = {self._verbose}")
        elif param == "debug":
            self._debug = value in ("true", "1", "yes")
            print(f"debug = {self._debug}")
        else:
            self._error(f"Unknown parameter: '{param}'")

    # ------------------------------------------------------------------
    # Complétion Tab (F18)
    # ------------------------------------------------------------------

    def _completer(self, text: str, state: int) -> str | None:
        """
        Fonction de complétion pour readline.

        readline l'appelle avec state=0, 1, 2, ... jusqu'à ce qu'on retourne None.
        On retourne les commandes qui commencent par `text`.

        Exemple :
          L'utilisateur tape "sh" puis Tab.
          readline appelle _completer("sh", 0) -> "show board"
          readline appelle _completer("sh", 1) -> "show history"
          readline appelle _completer("sh", 2) -> "show time"
          readline appelle _completer("sh", 3) -> None  (fin)
        """
        options = [c for c in COMMANDS if c.startswith(text)]
        if state < len(options):
            return options[state]
        return None

    # ------------------------------------------------------------------
    # Affichage des erreurs (F10 du cahier des charges)
    # ------------------------------------------------------------------

    def _error(self, message: str) -> None:
        """
        Affiche un message d'erreur sur stderr (F1 du cahier des charges).

        Le cahier des charges impose que les messages d'erreur aillent
        sur stderr, pas stdout.
        """
        print(f"Error: {message}", file=sys.stderr)

    def _debug_print(self, message: str) -> None:
        """Affiche un message de debug uniquement si --debug est actif."""
        if self._debug:
            print(f"[DEBUG] {message}", file=sys.stderr)