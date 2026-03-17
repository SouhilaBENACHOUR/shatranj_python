from shatranj.domain.core.board import Board
from shatranj.domain.core.move import Move
from shatranj.domain.rules.rules_engine import RulesEngine
from shatranj.domain.ai.evaluator import Evaluator
from shatranj.utils.constants import WHITE, BLACK


class Minimax:
    """
    Algorithme Minimax avec profondeur configurable.

    Principe :
      - MAX : l'IA cherche à maximiser son score
      - MIN : l'adversaire cherche à minimiser le score de l'IA

    À chaque niveau on alterne MAX et MIN.
    On explore jusqu'à la profondeur demandée,
    puis on évalue la position avec Evaluator.
    """

    def __init__(
        self,
        engine: RulesEngine,
        evaluator: Evaluator,
        depth: int = 3,
    ) -> None:
        self._engine = engine  # pour générer les coups légaux
        self._evaluator = evaluator  # pour évaluer les positions
        self._depth = depth  # profondeur de recherche

    def best_move(self, board: Board, color: str) -> Move | None:
        """
        Retourne le meilleur coup pour 'color' dans la position actuelle.
        Retourne None si aucun coup n'est disponible (mat ou pat).
        """
        # on commence à -infini car on cherche le maximum
        best_score = float("-inf")
        best_moves: list[Move] = []

        legal_moves = self._engine.generate_legal_moves(board, color)

        if not legal_moves:
            return None  # pas de coup disponible

        eps = 1e-9
        for move in legal_moves:
            # joue le coup
            captured = board.apply_move(move)

            # appelle minimax pour l'adversaire (MIN)
            opponent = BLACK if color == WHITE else WHITE
            score = self._minimax(
                board=board,
                depth=self._depth - 1,
                is_maximizing=False,  # c'est au tour de l'adversaire
                ai_color=color,
                current_color=opponent,
            )

            # annule le coup
            board.undo_move(move, captured)

            # garde le meilleur coup
            if score > best_score + eps:
                best_score = score
                best_moves = [move]
            elif abs(score - best_score) <= eps:
                best_moves.append(move)

        if not best_moves:
            return None
        return self._select_most_active_move(board, color, best_moves)

    def _select_most_active_move(
        self,
        board: Board,
        color: str,
        moves: list[Move],
    ) -> Move:
        """
        Départage les coups ex-aequo pour éviter les allers-retours passifs.
        Priorités:
          1) capture
          2) mobilité du camp IA après le coup
          3) amplitude du déplacement
        """
        best_move = moves[0]
        best_activity = self._activity_score(board, color, best_move)

        for move in moves[1:]:
            activity = self._activity_score(board, color, move)
            if activity > best_activity:
                best_activity = activity
                best_move = move

        return best_move

    def _activity_score(
        self, board: Board, color: str, move: Move
    ) -> tuple[int, int, int, int, int]:
        captured = board.apply_move(move)
        mobility_after = len(self._engine.generate_legal_moves(board, color))
        board.undo_move(move, captured)

        from_rank, from_file = divmod(move.from_square, 8)
        to_rank, to_file = divmod(move.to_square, 8)
        distance = abs(to_rank - from_rank) + abs(to_file - from_file)
        is_capture = 1 if move.captured_piece is not None else 0

        # Les deux derniers critères rendent la sélection déterministe.
        return (is_capture, mobility_after, distance, move.to_square, -move.from_square)

    def _minimax(
        self,
        board: Board,
        depth: int,
        is_maximizing: bool,
        ai_color: str,
        current_color: str,
    ) -> float:
        """
        Fonction récursive du Minimax.

        depth          → profondeur restante (s'arrête à 0)
        is_maximizing  → True si c'est le tour de l'IA (MAX), False sinon (MIN)
        ai_color       → la couleur de l'IA (ne change jamais)
        current_color  → la couleur qui joue à ce niveau
        """
        # cas de base : profondeur atteinte → on évalue la position
        if depth == 0:
            return self._evaluator.evaluate(board, ai_color)

        legal_moves = self._engine.generate_legal_moves(board, current_color)

        # cas de base : plus de coups → mat ou pat
        if not legal_moves:
            if self._engine._is_in_check(board, current_color):
                # mat → très bon pour l'IA si c'est l'adversaire qui est mat
                return 9999.0 if not is_maximizing else -9999.0
            else:
                # pat → score nul
                return 0.0

        opponent = BLACK if current_color == WHITE else WHITE

        if is_maximizing:
            # l'IA cherche le score maximum
            best = float("-inf")
            for move in legal_moves:
                captured = board.apply_move(move)
                score = self._minimax(
                    board=board,
                    depth=depth - 1,
                    is_maximizing=False,  # prochain niveau → adversaire (MIN)
                    ai_color=ai_color,
                    current_color=opponent,
                )
                board.undo_move(move, captured)
                best = max(best, score)  # garde le meilleur score
            return best

        else:
            # l'adversaire cherche le score minimum
            best = float("+inf")
            for move in legal_moves:
                captured = board.apply_move(move)
                score = self._minimax(
                    board=board,
                    depth=depth - 1,
                    is_maximizing=True,  # prochain niveau → IA (MAX)
                    ai_color=ai_color,
                    current_color=opponent,
                )
                board.undo_move(move, captured)
                best = min(best, score)  # garde le pire score pour l'IA
            return best
