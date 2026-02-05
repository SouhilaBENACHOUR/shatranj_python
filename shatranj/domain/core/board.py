"""
Rôle : Interface haut niveau au BitboardManager + logique jeu Fonctions :

    __init__() : Init BitboardManager
    get_piece(square) : Type pièce sur case
    make_move(move) : Applique coup (met à jour bitboards)
    unmake_move(move) : Annule coup (undo)
    get_legal_moves(square) : Coups possibles pour pièce (via MoveGenerator)
    is_square_attacked(square, by_color) : Case attaquée ?
    to_ascii() : Affichage 8×8 ASCII
    Attributs : bitboard_manager, current_turn
"""