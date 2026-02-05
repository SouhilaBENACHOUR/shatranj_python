"""
Rôle : Représente un coup de jeu Fonctions :

    __init__(from_sq, to_sq, piece, is_capture, is_promo) : Constructeur
    to_algebraic() : Convertit → "e2-e4" ou "e4xe5"
    from_algebraic(notation) : Parse "e2-e4" → Move
    __eq__(other) : Comparaison égalité
    __str__() : Affichage lisible
    Attributs : from_square, to_square, piece_type, is_capture, is_promotion
"""