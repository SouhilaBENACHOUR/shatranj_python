"""
Module core de la couche domaine.

Ce module contient les classes fondamentales représentant les concepts
de base du jeu de Shatranj.

Classes principales :
    - Game : Orchestrateur principal, gère l'état complet d'une partie
    - Board : Représentation logique du plateau (superposition des bitboards)
    - Move : Représentation d'un coup dans le jeu
    - Player : Représentation d'un joueur (humain ou IA)
    - TimeManager : Gestion du temps en mode blitz
    - GameHistoryManager : Gestion de l'historique undo/redo

Classe Game :
    Responsabilité : Orchestrateur principal

    Attributs :
        - board : Board (état actuel du plateau)
        - current_player : Color (WHITE ou BLACK)
        - white_player : Player
        - black_player : Player
        - time_manager : TimeManager (si mode blitz)
        - history_manager : GameHistoryManager
        - game_status : str (IN_PROGRESS, CHECK, CHECKMATE, STALEMATE)

    Méthodes principales :
        - make_move(move) -> bool : Jouer un coup
        - make_move_algebraic(notation) -> bool : Jouer via notation "e2-e4"
        - undo_move() -> bool : Annuler le dernier coup
        - redo_move() -> bool : Rejouer un coup annulé
        - get_legal_moves() -> List[Move] : Coups légaux
        - is_game_over() -> bool : Partie terminée ?
        - get_winner() -> Optional[Color] : Gagnant si partie terminée

Classe Board :
    Responsabilité : Représentation logique du plateau (board final)

    Attributs :
        - bitboards : Bitboard (instance de la couche data)

    Propriétés calculées :
        - occupancy : int (bitboard de toutes cases occupées)
        - white_occupancy : int
        - black_occupancy : int

    Méthodes principales :
        - get_piece_at(square) -> Optional[Tuple[str, str]]
        - get_piece_at_algebraic(notation) -> Optional[Tuple[str, str]]
        - place_piece(piece_type, color, square)
        - remove_piece(square)
        - move_piece(from_square, to_square)
        - capture_piece(from_square, to_square)

    Conversion :
        - square_to_algebraic(square) -> str : 28 -> "e4"
        - algebraic_to_square(notation) -> int : "e4" -> 28

    Note architecturale :
        Board est une abstraction logique au-dessus des bitboards.
        Il fournit une interface "plateau" au lieu de "bits".
        Board délègue toutes les opérations bas niveau à Bitboard.

Classe Move :
    Responsabilité : Représentation d'un coup

    Attributs :
        - from_square : int (case de départ 0-63)
        - to_square : int (case d'arrivée 0-63)
        - piece_type : PieceType
        - color : Color
        - captured_piece : Optional[PieceType]
        - is_promotion : bool
        - is_check : bool
        - is_checkmate : bool

    Méthodes :
        - to_algebraic() -> str : Convertir en "e2-e4" ou "e4xe5"
        - from_algebraic(notation, board) -> Move : Parser notation
        - is_capture() -> bool

    Notation algébrique (F19) :
        - Format : origine-destination
        - Déplacement simple : "e2-e4"
        - Capture : "e4xe5" (avec 'x')

Classe Player :
    Responsabilité : Représentation d'un joueur

    Attributs :
        - name : str
        - color : Color (WHITE ou BLACK)
        - is_human : bool
        - time_remaining : float (secondes, mode blitz)

    Méthodes :
        - get_move(game) -> Move : Demander le coup (abstrait)
        - update_time(elapsed) : Décrémenter le temps

Classe TimeManager  :
    Responsabilité : Gestion du chronomètre en mode blitz

    Attributs :
        - white_time : float (secondes)
        - black_time : float (secondes)
        - is_paused : bool
        - current_color : Color

    Méthodes :
        - start() : Démarrer le chrono
        - pause() : Mettre en pause
        - resume() : Reprendre
        - update(elapsed) : Décrémenter temps du joueur courant
        - is_timeout(color) -> bool : Temps écoulé ?
        - get_remaining_time(color) -> float

Classe GameHistoryManager :
    Responsabilité : Gestion de l'historique undo/redo

    Attributs :
        - moves : List[Move] (coups joués)
        - redo_stack : List[Move] (coups annulés)

    Méthodes :
        - add_move(move) : Ajouter un coup
        - undo() -> Optional[Move] : Annuler dernier coup
        - redo() -> Optional[Move] : Rejouer coup annulé
        - undo_n(n) -> List[Move] : Annuler N coups
        - clear_redo_stack() : Effacer l'historique futur
        - get_history() -> List[Move]

    Règles spéciales  :
        - Seuls les joueurs humains peuvent undo
        - Si undo : annule coup humain + tous coups IA jusqu'au coup humain
        précédent
        - Si coup différent après undo : efface l'historique futur

Relations entre classes :
    Game contient :
        - 1 Board (état actuel)
        - 2 Players (blanc et noir)
        - 1 TimeManager (si mode blitz)
        - 1 GameHistoryManager (historique)

    Board utilise :
        - 1 Bitboard (de la couche data)
"""

# TODO: Importer les classes lors de l'implémentation
# from shatranj.domain.core.game import Game
# from shatranj.domain.core.board import Board
# from shatranj.domain.core.move import Move
# from shatranj.domain.core.player import Player, HumanPlayer, AIPlayer
# from shatranj.domain.core.time_manager import TimeManager
# from shatranj.domain.core.game_history_manager import GameHistoryManager

__all__ = [
    # Classes principales (à décommenter)
    # "Game",
    # "Board",
    # "Move",
    # "Player",
    # "HumanPlayer",
    # "AIPlayer",
    # "TimeManager",
    # "GameHistoryManager",
]
