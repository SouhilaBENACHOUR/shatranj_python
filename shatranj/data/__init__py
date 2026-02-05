"""
Couche Données du projet Shatranj.

Cette couche gère la représentation bas niveau des données et leur persistence.

Responsabilités (selon architecture 3-tiers) :
    - Représentation optimisée du plateau via bitboards (12 bitboards individuels)
    - Opérations binaires sur les bitboards (AND, OR, XOR, SHIFT)
    - Masques pré-calculés pour génération de coups rapide
    - Sauvegarde et chargement de parties (format INI - cahier des charges F20-F24)
    - Gestion du fichier de configuration .shatranjrc (cahier des charges F2)
    - Parsing des fichiers de sauvegarde (cahier des charges F21)

Sous-modules :
    - bitboards : Représentation bas niveau via bitboards (cahier des charges F25-F26)
    - persistence : Sauvegarde/chargement et configuration (cahier des charges F20-F24)

Note architecturale importante :
    Cette couche ne contient AUCUNE logique de jeu.
    Elle fournit uniquement :
        - Les structures de données optimisées (bitboards)
        - La persistence (fichiers)
    
    Les règles du jeu sont dans la couche Domain (domain/rules/).
    L'orchestration réseau est dans la couche Domain (domain/network/).

Relation avec cahier des charges :
    - F25 : Module bitboard → data/bitboards/
    - F26 : Algorithmes de manipulation → data/bitboards/operations.py
    - F20 : Sauvegarde/restauration → data/persistence/game_repository.py
    - F21 : Commentaires → data/persistence/save_parser.py
    - F23 : Format plateau → data/bitboards/bitboard.py

Exemples d'utilisation :
    >>> from shatranj.data.bitboards import Bitboard
    >>> bb = Bitboard()  # Position de départ
    >>> bb.get_piece_at(12)  # ('PAWN', 'WHITE')
    >>> bb.white_pieces  # Bitboard de toutes pièces blanches
    
    >>> from shatranj.data.persistence import GameRepository
    >>> repo = GameRepository()
    >>> repo.save_game(game, "partie.shatranj")
    >>> loaded_game = repo.load_game("partie.shatranj")
"""

# TODO: Importer les classes principales lors de l'implémentation
# from shatranj.data.bitboards.bitboard import Bitboard
# from shatranj.data.bitboards.manager import BitboardManager
# from shatranj.data.persistence.game_repository import GameRepository
# from shatranj.data.persistence.config_repository import ConfigRepository
# from shatranj.data.persistence.scoreboard_repository import ScoreboardRepository

__all__ = [
    # Bitboards 
    # "Bitboard",
    # "BitboardManager",
    # Persistence 
    # "GameRepository",
    # "ConfigRepository",
    # "ScoreboardRepository",
]