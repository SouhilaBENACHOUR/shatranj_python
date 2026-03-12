import math
import random

from shatranj.domain.core.board import Board
from shatranj.domain.core.move import Move
from shatranj.domain.rules.rules_engine import RulesEngine
from shatranj.utils.constants import WHITE, BLACK


class MCTSNode:
    """
    Un nœud dans l'arbre MCTS.

    Chaque nœud représente une position du jeu après un coup.

    Attributs :
      move      → le coup qui a mené à cette position (None pour la racine)
      parent    → le nœud parent (None pour la racine)
      children  → les nœuds enfants (coups explorés)
      wins      → nombre de victoires simulées depuis ce nœud
      visits    → nombre de fois que ce nœud a été visité
      untried   → coups pas encore explorés depuis cette position
      color     → couleur du joueur qui vient de jouer ce coup
    """

    def __init__(
        self,
        move  : Move | None,
        parent: "MCTSNode | None",
        color : str,
    ) -> None:
        self.move     = move
        self.parent   = parent
        self.color    = color
        self.children : list["MCTSNode"] = []
        self.wins     : float = 0.0
        self.visits   : int   = 0
        self.untried  : list[Move] = []  # sera rempli lors de l'expansion

    def is_fully_expanded(self) -> bool:
        """Retourne True si tous les coups ont été explorés."""
        return len(self.untried) == 0

    def best_child(self, exploration: float = 1.41) -> "MCTSNode":
        """
        Choisit le meilleur enfant selon la formule UCB1.

        UCB1 = wins/visits + exploration * sqrt(ln(parent.visits) / visits)

        Le premier terme exploite les bons coups connus.
        Le second terme explore les coups peu visités.
        exploration = 1.41 ≈ sqrt(2) est la valeur standard.
        """
        return max(
            self.children,
            key=lambda c: (c.wins / c.visits) +
                          exploration * math.sqrt(math.log(self.visits) / c.visits)
        )

    def best_move_child(self) -> "MCTSNode":
        """
        Retourne l'enfant le plus visité.
        Utilisé à la fin pour choisir le coup final.
        On prend le plus visité (pas le meilleur UCB1) car c'est plus robuste.
        """
        return max(self.children, key=lambda c: c.visits)


class MCTS:
    """
    Monte Carlo Tree Search.

    Principe :
      On répète N fois (simulations) :
        1. SELECTION  → descend dans l'arbre avec UCB1
        2. EXPANSION  → explore un coup non essayé
        3. SIMULATION → joue aléatoirement jusqu'à la fin (rollout)
        4. BACKPROP   → remonte le résultat dans l'arbre

      À la fin on choisit le coup le plus visité.
    """

    def __init__(
        self,
        engine     : RulesEngine,
        simulations: int = 500,
    ) -> None:
        self._engine      = engine
        self._simulations = simulations  # nombre de simulations par coup
        self._depth       = simulations  # pour compatibilité avec _do_ai_move

    def best_move(self, board: Board, color: str) -> Move | None:
        """
        Retourne le meilleur coup pour 'color' avec MCTS.
        Retourne None si aucun coup n'est disponible.
        """
        legal_moves = self._engine.generate_legal_moves(board, color)
        if not legal_moves:
            return None

        # crée la racine de l'arbre
        root = MCTSNode(move=None, parent=None, color=color)
        root.untried = list(legal_moves)
        root.visits  = 1

        # répète les simulations
        for _ in range(self._simulations):
            node        = root
            board_copy  = self._copy_board(board)
            sim_color   = color

            # ----------------------------------------------------------
            # 1. SELECTION
            # descend dans l'arbre tant que le nœud est fully expanded
            # ----------------------------------------------------------
            while node.is_fully_expanded() and node.children:
                node       = node.best_child()
                board_copy.apply_move(node.move)
                sim_color  = BLACK if sim_color == WHITE else WHITE

            # ----------------------------------------------------------
            # 2. EXPANSION
            # explore un coup non essayé depuis ce nœud
            # ----------------------------------------------------------
            if node.untried:
                move      = random.choice(node.untried)
                node.untried.remove(move)
                board_copy.apply_move(move)
                sim_color = BLACK if sim_color == WHITE else WHITE

                # crée un nouveau nœud enfant
                child           = MCTSNode(move=move, parent=node, color=sim_color)
                legal_child     = self._engine.generate_legal_moves(board_copy, sim_color)
                child.untried   = list(legal_child)
                node.children.append(child)
                node = child

            # ----------------------------------------------------------
            # 3. SIMULATION (rollout)
            # joue aléatoirement jusqu'à la fin de la partie
            # ----------------------------------------------------------
            result = self._rollout(board_copy, sim_color, color)

            # ----------------------------------------------------------
            # 4. BACKPROPAGATION
            # remonte le résultat dans tous les nœuds ancêtres
            # ----------------------------------------------------------
            self._backpropagate(node, result)

        # retourne le coup du nœud le plus visité
        if not root.children:
            return random.choice(legal_moves)
        return root.best_move_child().move

    def _rollout(
        self,
        board       : Board,
        current_color: str,
        ai_color    : str,
        max_moves   : int = 50,
    ) -> float:
        """
        Simule une partie aléatoire jusqu'à la fin.

        Retourne :
          1.0  → victoire pour l'IA
          0.0  → défaite pour l'IA
          0.5  → match nul
        """
        color = current_color

        for _ in range(max_moves):
            legal_moves = self._engine.generate_legal_moves(board, color)

            # plus de coups → mat ou pat
            if not legal_moves:
                if self._engine._is_in_check(board, color):
                    # mat → l'adversaire a gagné
                    opponent = BLACK if color == WHITE else WHITE
                    return 1.0 if opponent == ai_color else 0.0
                else:
                    # pat → nul
                    return 0.5

            # bare king → victoire pour l'adversaire
            if self._engine.is_bare_king(board, color):
                opponent = BLACK if color == WHITE else WHITE
                return 1.0 if opponent == ai_color else 0.0

            # joue un coup aléatoire
            move = random.choice(legal_moves)
            board.apply_move(move)
            color = BLACK if color == WHITE else WHITE

        # limite atteinte → nul
        return 0.5

    def _backpropagate(self, node: "MCTSNode", result: float) -> None:
        """
        Remonte le résultat depuis le nœud feuille jusqu'à la racine.

        Chaque nœud ancêtre reçoit :
          - +1 visite
          - +result en wins (ou +1-result si c'est l'adversaire)
        """
        while node is not None:
            node.visits += 1
            node.wins   += result
            result       = 1.0 - result  # inverse le résultat pour le parent
            node         = node.parent

    def _copy_board(self, board: Board) -> Board:
        """
        Crée une copie profonde du board pour les simulations.
        On copie uniquement les bitboards — c'est suffisant.
        """
        new_board         = Board(setup=False)
        new_board._boards = dict(board._boards)
        return new_board