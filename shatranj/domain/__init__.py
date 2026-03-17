"""
Couche Domaine (Métier) du projet Shatranj.

Cette couche contient toute la logique du jeu, les règles et l'intelligence
artificielle. C'est le "cerveau" de l'application.

Responsabilités (selon architecture 3-tiers) :
    - Gestion de l'état du jeu (Game)
    - Représentation logique du plateau (Board final)
    - Validation des coups selon les règles du Shatranj
    - Génération de tous les coups possibles
    - Détection échec, mat, pat
    - Intelligence artificielle
    - Gestion du temps en mode blitz
    - Gestion de l'historique undo/redo
    - Orchestration du jeu en réseau

Sous-modules :
    - core : Classes fondamentales (Game, Board, Move, Player, TimeManager)
    - rules : Moteur de règles (MoveGenerator, MoveValidator, RulesEngine)
    - ai : Intelligence artificielle (Minimax, MCTS, évaluation)
    - network : Communication réseau et jeu multijoueur

Architecture :
    Board (couche domain) utilise Bitboard (couche data)
    Board fournit une interface "plateau" au lieu de "bits"
    Toute la logique de jeu est indépendante de l'interface

Règles spécifiques du Shatranj  :
    - Shah (Roi) : 1 case dans toutes directions
    - Ferz (Conseiller) : 1 case en diagonale uniquement
         Différence majeure : aux échecs modernes, la Dame est puissante
    - Rook (Tour) : ligne droite horizontal/vertical
    - Alfil (Éléphant) : 2 cases en diagonale (saute)
        Différence majeure : le Fou moderne va sur toute la diagonale
    - Knight (Cavalier) : en "L" (comme échecs modernes)
    - Pawn (Pion) : 1 case avant, capture diagonale
        Différences : pas de double pas initial, pas de prise en passant
        Promotion : uniquement en Ferz (pas en Dame)

Conditions de fin de partie :
    - Échec et mat : Shah attaqué et aucun coup légal → Victoire
    - Pat (Stalemate) : Aucun coup légal mais pas en échec → Nul
    - Timeout : Temps écoulé en mode blitz → Défaite

    
# TODO: Importer les classes principales lors de l'implémentation
# from shatranj.domain.core.game import Game
# from shatranj.domain.core.board import Board
# from shatranj.domain.core.move import Move
# from shatranj.domain.core.player import Player, HumanPlayer, AIPlayer

__all__ = [
    # Classes principales (à décommenter)
    # "Game",
    # "Board",
    # "Move",
    # "Player",
    # "HumanPlayer",
    # "AIPlayer",
]
"""
