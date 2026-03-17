from shatranj.domain.core.board import Board
from shatranj.domain.rules.rules_engine import RulesEngine
from shatranj.utils.constants import WHITE, BLACK, PAWN, ROOK, KNIGHT, ALFIL, FERZ, SHAH

# Valeur de chaque pièce en Shatranj
# Ces valeurs sont classiques pour le Shatranj
PIECE_VALUES = {
    PAWN: 1,
    ALFIL: 2,  # fou sauteur — limité, donc peu de valeur
    KNIGHT: 6,  # cavalier — très mobile
    ROOK: 9,  # tour — très puissante
    FERZ: 2,  # vizir — limité à 1 case diagonale
    SHAH: 0,  # le roi ne compte pas dans le score
}
MOBILITY_WEIGHT = 0.15  # bonus léger pour encourager l'activité des pièces


class Evaluator:
    """
    Donne un score à une position du board.

    Score positif → avantage pour WHITE
    Score négatif → avantage pour BLACK
    Score 0       → position équilibrée

    Heuristique utilisée :
      - matériel
      - mobilité (nombre de coups légaux)
    """

    def __init__(self) -> None:
        self._engine = RulesEngine()

    def evaluate(self, board: Board, color: str) -> float:
        """
        Calcule le score de la position pour 'color'.
        On additionne les valeurs des pièces blanches
        et on soustrait les valeurs des pièces noires.
        """
        score = 0

        for piece, value in PIECE_VALUES.items():
            # compte les pièces blanches et ajoute leur valeur
            white_count = bin(board._boards[(piece, WHITE)]).count("1")
            # compte les pièces noires et soustrait leur valeur
            black_count = bin(board._boards[(piece, BLACK)]).count("1")
            score += value * white_count
            score -= value * black_count

        # Bonus de mobilité : incite l'IA à jouer des coups actifs
        # Pseudo-légal pour rester léger en temps
        # (l'évaluation est appelée très souvent).
        white_mobility = len(self._engine.generate_pseudo_legal_moves(board, WHITE))
        black_mobility = len(self._engine.generate_pseudo_legal_moves(board, BLACK))
        score += MOBILITY_WEIGHT * (white_mobility - black_mobility)

        # si color est BLACK on inverse le score
        # car BLACK veut maximiser son propre avantage
        return score if color == WHITE else -score
