"""
Rôle : Cache positions avec hash Zobrist 

Fonctions :
    __init__() : Init table hash
    init_zobrist_keys() : Génère clés aléatoires 64 bits
    compute_hash(board) : Hash position actuelle
    store(position_hash, depth, score, move) : Stocke évaluation
    lookup(position_hash, depth) : Récupère si présent
    Attribut : table = {} (dict position_hash → entry)
"""