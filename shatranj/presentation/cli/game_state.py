"""
game_state.py - État complet d'une partie de Shatranj

Rôle : contient TOUT ce qui définit une partie en cours :
  - le plateau (Board)
  - qui joue (WHITE ou BLACK)
  - l'historique des coups pour undo/redo

Pourquoi une classe séparée de Board ?
  Board = juste les pièces sur les cases.
  GameState = Board + contexte de la partie (tour, historique, ...).
  C'est la couche Métier (Business Logic) du rapport préliminaire.
"""

from shatranj.domain.core.board import Board
from shatranj.domain.core.move import Move
from shatranj.utils.constants import WHITE, BLACK


class GameState:
    """
    Représente l'état complet d'une partie.

    Attributs :
      board         : le plateau actuel
      current_color : couleur du joueur dont c'est le tour (WHITE ou BLACK)
      history       : liste des coups joués (pour l'affichage et le undo)
      redo_stack    : pile des coups annulés (pour le redo)
    """

    def __init__(self) -> None:
        # On crée un nouveau plateau avec la position de départ
        self.board = Board(setup=True)

        # Les blancs commencent toujours (règle du Shatranj)
        self.current_color: str = WHITE

        # Historique des coups joués : liste de (move, board_snapshot)
        # On sauvegarde un snapshot du plateau AVANT chaque coup
        # pour pouvoir revenir en arrière (undo)
        self._history: list[tuple[Move, dict]] = []

        # Pile redo : coups annulés qu'on peut rejouer
        self._redo_stack: list[tuple[Move, dict]] = []

    # ------------------------------------------------------------------
    # Appliquer un coup
    # ------------------------------------------------------------------

    def apply_move(self, move: Move) -> None:
        """
        Applique un coup sur le plateau et passe au joueur suivant.

        On sauvegarde l'état du plateau AVANT le coup dans l'historique.
        Quand on joue un nouveau coup, on vide le redo_stack
        (on ne peut pas refaire des coups après avoir joué autre chose).
        """
        # Sauvegarde de l'état actuel (snapshot des bitboards)
        snapshot = self._take_snapshot()

        # Application du coup sur le plateau
        self.board.move_piece(move.from_square, move.to_square)

        # Ajout à l'historique
        self._history.append((move, snapshot))

        # Un nouveau coup efface les coups annulés
        self._redo_stack.clear()

        # Changement de tour
        self._switch_turn()

    # ------------------------------------------------------------------
    # Undo / Redo
    # ------------------------------------------------------------------

    def undo(self) -> Move | None:
        """
        Annule le dernier coup joué.
        Retourne le coup annulé, ou None si l'historique est vide.

        Principe : on restaure le snapshot sauvegardé AVANT ce coup.
        """
        if not self._history:
            return None  # Rien à annuler

        move, snapshot = self._history.pop()

        # On pousse le coup annulé dans le redo_stack
        self._redo_stack.append((move, self._take_snapshot()))

        # Restauration du plateau à l'état avant le coup
        self._restore_snapshot(snapshot)

        # On repasse au joueur précédent
        self._switch_turn()

        return move

    def redo(self) -> Move | None:
        """
        Rejoue le dernier coup annulé.
        Retourne le coup rejoué, ou None si pas de redo disponible.
        """
        if not self._redo_stack:
            return None  # Rien à rejouer

        move, _ = self._redo_stack.pop()

        # On réapplique le coup (comme apply_move mais sans vider redo_stack)
        snapshot = self._take_snapshot()
        self.board.move_piece(move.from_square, move.to_square)
        self._history.append((move, snapshot))
        self._switch_turn()

        return move

    def can_undo(self) -> bool:
        return len(self._history) > 0

    def can_redo(self) -> bool:
        return len(self._redo_stack) > 0

    # ------------------------------------------------------------------
    # Historique
    # ------------------------------------------------------------------

    def get_history(self) -> list[Move]:
        """Retourne la liste des coups joués (sans les snapshots)."""
        return [move for move, _ in self._history]

    # ------------------------------------------------------------------
    # Méthodes privées
    # ------------------------------------------------------------------

    def _switch_turn(self) -> None:
        """Passe le tour de WHITE à BLACK ou de BLACK à WHITE."""
        self.current_color = BLACK if self.current_color == WHITE else WHITE

    def _take_snapshot(self) -> dict:
        """
        Sauvegarde l'état des bitboards du plateau.

        On copie le dictionnaire _boards du Board.
        C'est une copie peu profonde mais ça suffit car les valeurs
        sont des entiers (immuables en Python).
        """
        return dict(self.board._boards)

    def _restore_snapshot(self, snapshot: dict) -> None:
        """Restaure les bitboards du plateau à partir d'un snapshot."""
        self.board._boards = dict(snapshot)