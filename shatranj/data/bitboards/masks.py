"""
Rôle : Pré-calcul des masques de déplacement pour chaque pièce Fonctions :

    generate_shah_masks() : 64 masques Shah (8 directions, 1 case)
    generate_ferz_masks() : 64 masques Ferz (4 diagonales, 1 case)
    generate_knight_masks() : 64 masques Cavalier (8 positions en L)
    generate_alfil_masks() : 64 masques Alfil (4 diag, 2 cases, saute)
    generate_rook_masks() : 64 masques Tour (rayons horizontaux/verticaux)
    generate_pawn_masks(color) : 64 masques Pion (avance + captures)
    Dictionnaires globaux : SHAH_MASKS[square], FERZ_MASKS[square], etc.
    
"""