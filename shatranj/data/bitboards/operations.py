"""
Rôle : Opérations binaires optimisées sur bitboards Fonctions :

    shift_north(bb) : Décalage << 8 (haut)
    shift_south(bb) : Décalage >> 8 (bas)
    shift_east(bb) : Décalage << 1 avec masque (droite)
    shift_west(bb) : Décalage >> 1 avec masque (gauche)
    shift_ne(bb), shift_nw(bb), shift_se(bb), shift_sw(bb) : Diagonales
    intersection(bb1, bb2) : AND (cases communes)
    union(bb1, bb2) : OR (union cases)
    difference(bb1, bb2) : bb1 & ~bb2 (retirer)
"""