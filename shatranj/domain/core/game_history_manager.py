"""
Rôle : Gestion undo/redo avec règles IA 

Fonctions :
    add_move(move, player) : Ajoute coup à historique
    undo(current_player) : Annule jusqu'à coup humain précédent
    redo() : Rejoue coups annulés
    clear_future() : Efface branche alternative après undo
    get_history() : Liste tous coups joués
    Attributs : past_moves[], future_moves[]
"""