from shatranj.domain.core.board import Board
from shatranj.domain.core.move import Move
from shatranj.domain.rules.rules_engine import RulesEngine
from shatranj.domain.ai.evaluator import Evaluator
from shatranj.utils.constants import WHITE, BLACK


class AlphaBeta:
    """
    Algorithme Minimax avec élagage Alpha-Beta.

    Amélioration de Minimax :
      - Alpha = meilleur score garanti pour MAX (commence à -inf)
      - Beta  = meilleur score garanti pour MIN (commence à +inf)
      - Si beta <= alpha → on coupe la branche (inutile de continuer)

    Avantage : explore ~50% des nœuds en moins que Minimax pur.
    On peut donc augmenter la profondeur de 3 à 4 pour le même temps.
    """

    def __init__(
        self,
        engine: RulesEngine,
        evaluator: Evaluator,
        depth: int = 4,  
    ) -> None:
        self._engine   = engine
        self._evaluator = evaluator
        self._depth    = depth

    def best_move(self, board: Board, color: str) -> Move | None:
        """
        Retourne le meilleur coup pour 'color' avec Alpha-Beta.
        Retourne None si aucun coup n'est disponible.
        """
        best      = None
        alpha     = float("-inf")  # meilleur score garanti pour MAX
        beta      = float("+inf")  # meilleur score garanti pour MIN

        legal_moves = self._engine.generate_legal_moves(board, color)
        if not legal_moves:
            return None

        for move in legal_moves:
            captured = board.apply_move(move)

            opponent = BLACK if color == WHITE else WHITE
            score = self._alphabeta(
                board         = board,
                depth         = self._depth - 1,
                alpha         = alpha,
                beta          = beta,
                is_maximizing = False,  # adversaire joue en premier (MIN)
                ai_color      = color,
                current_color = opponent,
            )

            board.undo_move(move, captured)

            # on garde le meilleur coup pour MAX
            if score > alpha:
                alpha = score
                best  = move

        return best

    def _alphabeta(
        self,
        board         : Board,
        depth         : int,
        alpha         : float,
        beta          : float,
        is_maximizing : bool,
        ai_color      : str,
        current_color : str,
    ) -> float:
        """
        Fonction récursive Alpha-Beta.

        alpha         → meilleur score que MAX peut garantir
        beta          → meilleur score que MIN peut garantir
        is_maximizing → True si c'est le tour de l'IA (MAX)
        ai_color      → couleur de l'IA (ne change jamais)
        current_color → couleur qui joue à ce niveau
        """
        # cas de base : profondeur atteinte → on évalue
        if depth == 0:
            return self._evaluator.evaluate(board, ai_color)

        legal_moves = self._engine.generate_legal_moves(board, current_color)

        # cas de base : plus de coups → mat ou pat
        if not legal_moves:
            if self._engine._is_in_check(board, current_color):
                # mat → très bon pour l'IA si c'est l'adversaire qui est mat
                return 9999 if not is_maximizing else -9999
            else:
                return 0  # pat

        opponent = BLACK if current_color == WHITE else WHITE

        if is_maximizing:
            # MAX cherche le score le plus élevé
            best = float("-inf")
            for move in legal_moves:
                captured = board.apply_move(move)
                score = self._alphabeta(
                    board         = board,
                    depth         = depth - 1,
                    alpha         = alpha,
                    beta          = beta,
                    is_maximizing = False,
                    ai_color      = ai_color,
                    current_color = opponent,
                )
                board.undo_move(move, captured)

                best  = max(best, score)
                alpha = max(alpha, best)  # met à jour alpha

                # COUPE BETA : MIN ne choisira jamais cette branche
                # car MAX peut déjà garantir mieux ailleurs
                if beta <= alpha:
                    break  # ← c'est la coupe Alpha-Beta !

            return best

        else:
            # MIN cherche le score le plus bas
            best = float("+inf")
            for move in legal_moves:
                captured = board.apply_move(move)
                score = self._alphabeta(
                    board         = board,
                    depth         = depth - 1,
                    alpha         = alpha,
                    beta          = beta,
                    is_maximizing = True,
                    ai_color      = ai_color,
                    current_color = opponent,
                )
                board.undo_move(move, captured)

                best = min(best, score)
                beta = min(beta, best)  # met à jour beta

                # COUPE ALPHA : MAX ne choisira jamais cette branche
                # car MIN peut déjà garantir moins ailleurs
                if beta <= alpha:
                    break  # ← c'est la coupe Alpha-Beta !

            return best