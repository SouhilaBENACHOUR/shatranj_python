"""
display.py - Affichage ASCII du plateau de Shatranj

Rôle : transformer l'objet Board en texte lisible pour le terminal.

Pourquoi un fichier séparé ?
  - Séparation des responsabilités : le Board ne sait pas s'afficher,
    le CLI ne sait pas dessiner. C'est la couche Présentation.
  - Facile à tester : on peut afficher n'importe quel état du Board.
"""

from shatranj.domain.core.board import Board
from shatranj.utils.constants import (
    WHITE, BLACK,
    SHAH, FERZ, ROOK, ALFIL, KNIGHT, PAWN,
)

# Dictionnaire : (type_pièce, couleur) -> lettre ASCII
# Blanc = MAJUSCULE, Noir = minuscule
PIECE_SYMBOLS = {
    (SHAH,   WHITE): "K",
    (FERZ,   WHITE): "F",
    (ROOK,   WHITE): "R",
    (ALFIL,  WHITE): "A",
    (KNIGHT, WHITE): "N",
    (PAWN,   WHITE): "P",
    (SHAH,   BLACK): "k",
    (FERZ,   BLACK): "f",
    (ROOK,   BLACK): "r",
    (ALFIL,  BLACK): "a",
    (KNIGHT, BLACK): "n",
    (PAWN,   BLACK): "p",
}


def board_to_string(board: Board) -> str:
    """
    Retourne une représentation ASCII du plateau.

    L'échiquier est affiché du rang 8 (haut) au rang 1 (bas),
    de la colonne a (gauche) à h (droite).

    Exemple de sortie :
        8  r n a f k a n r
        7  p p p p p p p p
        6  . . . . . . . .
        ...
        1  R N A F K A N R
           a b c d e f g h
    """
    lines = []

    # On parcourt les rangs de 7 (rang 8) à 0 (rang 1), du haut vers le bas
    for rank in range(7, -1, -1):
        # Le numéro affiché à gauche (1 à 8)
        row_label = str(rank + 1)
        row_squares = []

        # On parcourt les colonnes de 0 (a) à 7 (h)
        for file in range(8):
            # Calcul de l'index de la case : rank * 8 + file
            # Exemple : rang=1, file=4 -> case 12 (e2)
            square = rank * 8 + file

            piece = board.get_piece_at(square)
            if piece is None:
                row_squares.append(".")  # case vide
            else:
                row_squares.append(PIECE_SYMBOLS[piece])

        # Format : "8  r n a f k a n r"
        lines.append(f"  {row_label}  " + " ".join(row_squares))

    # Ligne des colonnes en bas
    lines.append("     a b c d e f g h")
    return "\n".join(lines)


def print_board(board: Board) -> None:
    """Affiche le plateau directement dans le terminal."""
    print(board_to_string(board))