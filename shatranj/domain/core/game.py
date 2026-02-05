"""
Rôle : Orchestre une partie complète 

Fonctions :
    __init__(white_player, black_player, config) : Init partie
    make_move(move) : Joue coup + switch tour + vérifie fin
    is_over() : Partie terminée ?
    get_winner() : Retourne Player gagnant ou None (nul)
    get_status() : "in_progress", "checkmate", "stalemate", "timeout"
    Attributs : board, white_player, black_player, current_turn, history_manager
"""