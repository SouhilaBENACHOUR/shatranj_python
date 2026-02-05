"""
Package principal du projet Shatranj.

Ce package implémente un jeu de Shatranj (échecs indiens) complet avec :
- Représentation optimisée du plateau via bitboards
- Intelligence artificielle (Minimax, MCTS + Random Forest)
- Interfaces CLI et GUI
- Jeu en réseau
- Sauvegarde/chargement de parties

Architecture 3-tiers :
    - Couche Data : Bitboards et persistence
    - Couche Domain : Logique du jeu, règles, IA, réseau
    - Couche Presentation : CLI et GUI

Modules principaux :
    - shatranj.data : Couche données (bitboards, persistence)
    - shatranj.domain : Couche métier (logique, règles, IA, réseau)
    - shatranj.presentation : Couche présentation (CLI, GUI)
    - shatranj.utils : Utilitaires transverses

Exécution du programme (cahier des charges F1) :
    Ligne de commande : shatranj [OPTIONS] [ARGUMENTS]
    
    Options obligatoires :
        -h, --help      : Affiche l'aide
        -V, --version   : Affiche la version
        -v, --verbose   : Mode verbeux
        -d, --debug     : Mode debug
        -g, --gui       : Interface graphique
        -b, --blitz     : Mode blitz
        -t TIME         : Temps blitz en minutes
        -a COLOR        : Joueur artificiel (W/B/A)

Auteurs :
    BENACHOUR Souhila
    DRIES Amina
    EL GHALI Ayman
    MARCHOUD Souhail
    MEKLAT Sarah

Licence :


Version :
    1.0.0
"""

__version__ = "1.0.0"
__author__ = "Équipe Shatranj"
#__license__ = " "

# Imports principaux (à décommenter progressivement lors de l'implémentation)
# from shatranj.domain.core.game import Game
# from shatranj.domain.core.board import Board
# from shatranj.data.bitboards.bitboard import Bitboard

__all__ = [
    "__version__",
    "__author__",
    "__license__",
    # Classes principales 
    # "Game",
    # "Board",
    # "Bitboard",
]