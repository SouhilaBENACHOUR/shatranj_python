"""
Rôle : Fonctions d'évaluation heuristiques 

Fonctions :
    evaluate_material(board) : Score matériel (somme valeurs pièces)
    evaluate_positional(board) : Centre + mobilité + sécurité Shah
    evaluate_advanced(board) : + structure pions + menaces
    evaluate(board, scoring_function) : Dispatcher
    Constantes : PIECE_VALUES = {PAWN: 1, KNIGHT: 3, ...}
"""