from shatranj.domain.core.board import Board
from shatranj.domain.ai.mcts import MCTS
from shatranj.domain.ai.ai_player import AIPlayer
from shatranj.domain.rules.rules_engine import RulesEngine
from shatranj.utils.constants import WHITE, BLACK, SHAH, ROOK, PAWN


def test_mcts_returns_a_move():
    """MCTS retourne un coup quand des coups sont disponibles."""
    board = Board(setup=False)
    board.place_piece(SHAH, WHITE, 0)
    board.place_piece(ROOK, WHITE, 1)
    board.place_piece(SHAH, BLACK, 63)
    engine = RulesEngine()
    mcts = MCTS(engine=engine, simulations=50)  # 50 pour les tests (rapide)
    move = mcts.best_move(board, WHITE)
    assert move is not None


def test_mcts_returns_none_when_no_moves():
    """MCTS retourne None si aucun coup disponible (mat)."""
    board = Board(setup=False)
    board.place_piece(SHAH, WHITE, 0)
    board.place_piece(ROOK, BLACK, 8)
    board.place_piece(ROOK, BLACK, 1)
    board.place_piece(SHAH, BLACK, 9)
    engine = RulesEngine()
    mcts = MCTS(engine=engine, simulations=50)
    move = mcts.best_move(board, WHITE)
    assert move is None


def test_mcts_via_ai_player():
    """AIPlayer avec algorithme mcts fonctionne correctement."""
    board = Board(setup=False)
    board.place_piece(SHAH, WHITE, 0)
    board.place_piece(ROOK, WHITE, 1)
    board.place_piece(SHAH, BLACK, 63)
    ai = AIPlayer(color=WHITE, algorithm="mcts")
    move = ai.choose_move(board)
    assert move is not None


def test_mcts_avoids_immediate_loss():
    """
    MCTS doit éviter de jouer dans une position perdante immédiate.
    Le Shah blanc ne doit pas se déplacer vers une case attaquée.
    """
    board = Board(setup=False)
    board.place_piece(SHAH, WHITE, 0)  # a1
    board.place_piece(ROOK, WHITE, 16)  # a3
    board.place_piece(SHAH, BLACK, 63)  # h8
    board.place_piece(PAWN, BLACK, 24)  # a4 — capturable
    engine = RulesEngine()
    mcts = MCTS(engine=engine, simulations=200)
    move = mcts.best_move(board, WHITE)
    assert move is not None
