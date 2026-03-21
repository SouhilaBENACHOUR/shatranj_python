"""
Module de gestion des règles du Shatranj.


Responsabilités :
    - Génération de tous les coups possibles
    - Validation de la légalité des coups
    - Détection échec, mat, pat

Composants :
    - MoveGenerator : Génère tous les coups possibles
    - MoveValidator : Valide la légalité d'un coup
    - RulesEngine : Détecte échec, mat, pat

Classe MoveGenerator  :
    Responsabilité : Générer tous les coups légaux/pseudo-légaux

    Méthodes principales :
        - generate_all_moves(board, color) -> List[Move]
            Génère tous les coups pseudo-légaux (respecte mouvements pièces)

        - generate_legal_moves(board, color) -> List[Move]
            Génère uniquement les coups légaux (filtre ceux qui exposent
            le Shah)

        - generate_pawn_moves(board, color) -> List[Move]
            Pions : 1 case avant + captures diagonales + promotions

        - generate_knight_moves(board, color) -> List[Move]
            Cavaliers : mouvement en "L"

        - generate_alfil_moves(board, color) -> List[Move]
            Alfils : 2 cases en diagonale (saute)

        - generate_ferz_moves(board, color) -> List[Move]
            Ferz : 1 case en diagonale

        - generate_shah_moves(board, color) -> List[Move]
            Shah : 1 case dans toutes directions

        - generate_rook_moves(board, color) -> List[Move]
            Tours : lignes droites (raycasting)

    Optimisations :
        - Utilise les masques pré-calculés (KNIGHT_ATTACKS, etc.)
        - Raycasting pour les pièces glissantes (Tour)
        - Algorithmes bitwise ultra-rapides
        - Performance : génération en quelques microsecondes

Classe MoveValidator:
    Responsabilité : Valider la légalité des coups

    Méthodes principales :
        - is_valid_move(board, move) -> bool
            Vérifie si le coup respecte les règles de mouvement de la pièce
            (mais ne teste PAS si le Shah est en échec après)

        - is_legal_move(board, move) -> bool
            Vérifie is_valid_move() ET que le coup ne laisse pas le Shah
            en échec

        - would_be_in_check(board, move, color) -> bool
            Simule le coup et teste si le Shah de 'color' serait en échec

        - is_square_attacked(board, square, by_color) -> bool
            Teste si une case est attaquée par une couleur

        - get_attackers(board, square, by_color) -> List[int]
            Retourne les positions de toutes les pièces qui attaquent square

    Validation en 2 étapes :
        1. Coup valide : respecte les règles de la pièce
        2. Coup légal : ne met pas son propre Shah en échec

    Calcul des attaques par type :
        - get_pawn_attacks(board, color) -> int : Bitboard des attaques
        - get_knight_attacks(board, color) -> int
        - get_alfil_attacks(board, color) -> int
        - get_ferz_attacks(board, color) -> int
        - get_shah_attacks(board, color) -> int
        - get_rook_attacks(board, color) -> int

    Relation avec cahier des charges :
        - F9.1 : "Vérifier leur validité"
        - F26 : "Vérifier si un coup est valide"

Classe RulesEngine :
    Responsabilité : Détecter les situations spéciales

    Méthodes principales :
        - is_in_check(board, color) -> bool
            Le Shah de 'color' est-il attaqué ?

        - is_checkmate(board, color) -> bool
            Le joueur 'color' est-il en échec ET mat ?
            (en échec + aucun coup légal)

        - is_stalemate(board, color) -> bool
            Le joueur 'color' est-il en pat ?
            (PAS en échec + aucun coup légal)

        - is_game_over(board, current_player) -> Tuple[bool, Optional[str]]
            Retourne (True, "CHECKMATE_WHITE") ou (True, "STALEMATE") etc.

        - find_king_square(board, color) -> int
            Localiser le Shah (chercher le bit actif dans bitboard shah)

        - has_legal_moves(board, color) -> bool
            Au moins un coup légal existe ?

    Conditions de fin :
        1. Échec et mat : Shah attaqué et aucun coup légal → Victoire
        2. Pat (Stalemate) : Aucun coup légal mais pas en échec → Nul
        3. Timeout : Temps écoulé (géré par TimeManager) → Défaite

Gestion des erreurs (F10) :
    Le module ne doit jamais crasher le programme.
    En cas de coup invalide, retourner False ou lever une exception appropriée.

    Exemples d'erreurs gérées :
        - Format de coup incorrect
        - Coup illégal (pièce ne peut pas bouger ainsi)
        - Pas le tour du joueur
        - Case vide
        - Se mettre en échec

Règles spécifiques du Shatranj :
    Pion (différences avec échecs modernes) :
        Pas de mouvement initial de 2 cases
        Pas de prise "en passant"
        Promotion : uniquement en Ferz (pas en Dame)

    Alfil (différent du Fou moderne) :
        - Saute exactement 2 cases en diagonale
        - Peut sauter par-dessus les pièces
        - N'atteint que 8 cases maximum sur tout le plateau

    Ferz (différent de la Dame moderne) :
        - Une case en diagonale uniquement
        - Pièce très faible (contrairement à la Dame)
"""

# TODO: Importer les classes lors de l'implémentation
# from shatranj.domain.rules.move_generator import MoveGenerator
# from shatranj.domain.rules.move_validator import MoveValidator
# from shatranj.domain.rules.rules_engine import RulesEngine

__all__ = [
    # Classes principales (à décommenter)
    # "MoveGenerator",
    # "MoveValidator",
    # "RulesEngine",
]
