from shatranj.domain.core.board import Board
from shatranj.domain.ai.mcts import MCTS
from shatranj.domain.ai.ai_player import AIPlayer
from shatranj.domain.rules.rules_engine import RulesEngine
from shatranj.utils.constants import WHITE, BLACK, SHAH, ROOK, PAWN


def test_mcts_returns_a_move():
    """MCTS returns a move when moves are available."""
    board = Board(setup=False)
    board.place_piece(SHAH, WHITE, 0)
    board.place_piece(ROOK, WHITE, 1)
    board.place_piece(SHAH, BLACK, 63)
    mcts = MCTS(engine=RulesEngine(), simulations=2)
    assert mcts.best_move(board, WHITE) is not None


def test_mcts_returns_none_when_no_moves():
    """MCTS returns None if no moves available (checkmate)."""
    board = Board(setup=False)
    board.place_piece(SHAH, WHITE, 0)
    board.place_piece(ROOK, BLACK, 8)
    board.place_piece(ROOK, BLACK, 1)
    board.place_piece(SHAH, BLACK, 9)
    mcts = MCTS(engine=RulesEngine(), simulations=1)
    assert mcts.best_move(board, WHITE) is None


def test_mcts_returns_legal_move():
    """MCTS returns a legal move."""
    board = Board(setup=False)
    board.place_piece(SHAH, WHITE, 0)
    board.place_piece(ROOK, WHITE, 1)
    board.place_piece(SHAH, BLACK, 63)
    engine = RulesEngine()
    mcts   = MCTS(engine=engine, simulations=2)
    move   = mcts.best_move(board, WHITE)
    assert move in engine.generate_legal_moves(board, WHITE)


def test_mcts_via_ai_player():
    """AIPlayer with mcts algorithm works correctly."""
    board = Board(setup=False)
    board.place_piece(SHAH, WHITE, 0)
    board.place_piece(ROOK, WHITE, 1)
    board.place_piece(SHAH, BLACK, 63)
    ai = AIPlayer(color=WHITE, algorithm="mcts", depth=2)
    assert ai.choose_move(board) is not None