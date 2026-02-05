"""
Rôle : Génère tous les coups possibles pour chaque type de pièce

Fonctions :
    generate_moves(board, square) : Dispatch selon type pièce
    generate_shah_moves(board, square) : 8 directions, 1 case
    generate_ferz_moves(board, square) : 4 diagonales, 1 case
    generate_knight_moves(board, square) : L-shape (8 max)
    generate_alfil_moves(board, square) : 2 diag, saute obstacles
    generate_rook_moves(board, square) : Raycast 4 directions
    generate_pawn_moves(board, square) : Avance + captures + promotion
"""