"""
Module d'utilitaires transverses.

Ce module contient les constantes, exceptions et utilitaires utilisés
par toutes les couches de l'application.

Composants :
    - constants : Constantes globales du jeu
    - exceptions : Exceptions personnalisées

Fichier constants.py :
    Responsabilité : Définir toutes les constantes du jeu

    Types de pièces  :
        - SHAH = "SHAH" (Roi)
        - FERZ = "FERZ" (Conseiller)
        - ROOK = "ROOK" (Tour)
        - ALFIL = "ALFIL" (Éléphant)
        - KNIGHT = "KNIGHT" (Cavalier)
        - PAWN = "PAWN" (Pion)

    Couleurs :
        - WHITE = "WHITE"
        - BLACK = "BLACK"

    Dimensions :
        - BOARD_SIZE = 8
        - NUM_SQUARES = 64

    Valeurs matérielles (pour évaluation IA) :
        PIECE_VALUES = {
            SHAH: float('inf'),  # Perte du Shah = défaite
            ROOK: 5,
            KNIGHT: 3,
            ALFIL: 1.5,
            FERZ: 1.5,
            PAWN: 1
        }

    Notations  :
        FILES = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
        RANKS = [1, 2, 3, 4, 5, 6, 7, 8]

    Symboles ASCII  :
        PIECE_SYMBOLS = {
            ('SHAH', 'WHITE'): 'K',
            ('SHAH', 'BLACK'): 'k',
            ('FERZ', 'WHITE'): 'F',
            ('FERZ', 'BLACK'): 'f',
            # ... etc
        }

    Symboles Unicode (affichage GUI/CLI) :
        PIECE_UNICODE = {
            ('SHAH', 'WHITE'): '♔',
            ('SHAH', 'BLACK'): '♚',
            ('FERZ', 'WHITE'): '♕',
            ('FERZ', 'BLACK'): '♛',
            # ... etc
        }

    Statuts de jeu :
        - GAME_NOT_STARTED = "NOT_STARTED"
        - GAME_IN_PROGRESS = "IN_PROGRESS"
        - GAME_CHECK = "CHECK"
        - GAME_CHECKMATE_WHITE = "CHECKMATE_WHITE"
        - GAME_CHECKMATE_BLACK = "CHECKMATE_BLACK"
        - GAME_STALEMATE = "STALEMATE"
        - GAME_TIMEOUT = "TIMEOUT"

Fichier exceptions.py :
    Responsabilité : Exceptions personnalisées

    Hiérarchie :
        ShatranjException (base)
        ├── InvalidMoveException : Format de coup invalide
        ├── IllegalMoveException : Coup illégal selon les règles
        ├── CheckException : Joueur en échec
        ├── CheckmateException : Partie terminée par mat
        ├── StalemateException : Partie terminée par pat
        ├── TimeoutException : Temps écoulé (mode blitz)
        ├── FileFormatException : Fichier de sauvegarde invalide
        └── NetworkException : Erreur réseau

    Classe ShatranjException :
        Exception de base pour toutes les exceptions du jeu

        Attributs :
            - message : str (message d'erreur)
            - details : Optional[dict] (détails supplémentaires)

    Classe InvalidMoveException :
        Levée quand format de coup incorrect

        Exemples :
            - "e9-e10" (case invalide)
            - "move e2 to e4" (format incorrect)

    Classe IllegalMoveException :
        Levée quand coup illégal selon les règles

        Exemples :
            - Pion qui avance de 2 cases
            - Cavalier qui bouge en ligne droite
            - Se mettre soi-même en échec

    Classe CheckException :
        Levée quand joueur en échec

    Classe CheckmateException :
        Levée quand partie terminée par mat

        Attributs supplémentaires :
            - winner : Color

    Classe StalemateException :
        Levée quand partie terminée par pat

    Classe TimeoutException :
        Levée quand temps écoulé en mode blitz

        Attributs supplémentaires :
            - loser : Color

    Classe FileFormatException :
        Levée lors du parsing de fichiers invalides

        Attributs supplémentaires :
            - filepath : str
            - line_number : Optional[int]
            - expected : str (ce qui était attendu)
            - found : str (ce qui a été trouvé)

    Classe NetworkException :
        Levée lors d'erreurs réseau

        Attributs supplémentaires :
            - error_type : str (connection, timeout, protocol, etc.)

Gestion des erreurs :
    Principes :
        - Ne jamais crasher le programme
        - Messages d'erreur clairs et explicites
        - Utiliser les exceptions appropriées
        - Logger les erreurs pour debug
"""

# TODO: Importer les constantes et exceptions lors de l'implémentation
# from shatranj.utils.constants import (
#     # Types de pièces
#     SHAH, FERZ, ROOK, ALFIL, KNIGHT, PAWN,
#     # Couleurs
#     WHITE, BLACK,
#     # Dimensions
#     BOARD_SIZE, NUM_SQUARES,
#     # Valeurs
#     PIECE_VALUES,
#     # Notations
#     FILES, RANKS,
#     # Symboles
#     PIECE_SYMBOLS,
#     PIECE_UNICODE,
#     # Statuts
#     GAME_NOT_STARTED,
#     GAME_IN_PROGRESS,
#     GAME_CHECK,
#     GAME_CHECKMATE_WHITE,
#     GAME_CHECKMATE_BLACK,
#     GAME_STALEMATE,
#     GAME_TIMEOUT
# )
#
# from shatranj.utils.exceptions import (
#     ShatranjException,
#     InvalidMoveException,
#     IllegalMoveException,
#     CheckException,
#     CheckmateException,
#     StalemateException,
#     TimeoutException,
#     FileFormatException,
#     NetworkException
# )

__all__ = [
    # Constantes (à décommenter)
    # "SHAH", "FERZ", "ROOK", "ALFIL", "KNIGHT", "PAWN",
    # "WHITE", "BLACK",
    # "BOARD_SIZE", "NUM_SQUARES",
    # "PIECE_VALUES",
    # "FILES", "RANKS",
    # "PIECE_SYMBOLS",
    # "PIECE_UNICODE",
    # "GAME_NOT_STARTED",
    # "GAME_IN_PROGRESS",
    # "GAME_CHECK",
    # "GAME_CHECKMATE_WHITE",
    # "GAME_CHECKMATE_BLACK",
    # "GAME_STALEMATE",
    # "GAME_TIMEOUT",
    # Exceptions (à décommenter)
    # "ShatranjException",
    # "InvalidMoveException",
    # "IllegalMoveException",
    # "CheckException",
    # "CheckmateException",
    # "StalemateException",
    # "TimeoutException",
    # "FileFormatException",
    # "NetworkException",
]
