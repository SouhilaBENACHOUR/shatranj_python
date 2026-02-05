"""
Rôle : Gère les 12 bitboards du jeu (6 pièces × 2 couleurs) Fonctions :

    __init__() : Initialise 12 bitboards position départ
    get_piece_at(square) : Retourne type pièce + couleur sur case
    move_piece(from_sq, to_sq) : Déplace pièce (modifie bitboards)
    get_all_white() : Union tous bitboards blancs
    get_all_black() : Union tous bitboards noirs
    get_occupied() : Union blanc + noir (tout le plateau)
    copy() : Copie profonde (pour simulation coups)
    Attributs : white_pawns, white_knights, ..., black_shah
"""