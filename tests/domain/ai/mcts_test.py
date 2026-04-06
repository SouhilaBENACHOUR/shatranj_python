

from shatranj.domain.core.board import Board
from shatranj.domain.ai.mcts import MCTS
from shatranj.domain.ai.ai_player import AIPlayer
from shatranj.domain.rules.rules_engine import RulesEngine
from shatranj.utils.constants import WHITE, BLACK, SHAH, ROOK, PAWN

# ================================================================
# Positive tests
# ================================================================


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


def test_mcts_via_ai_player():
    """AIPlayer with mcts algorithm works correctly."""
    board = Board(setup=False)
    board.place_piece(SHAH, WHITE, 0)
    board.place_piece(ROOK, WHITE, 1)
    board.place_piece(SHAH, BLACK, 63)
    ai = AIPlayer(color=WHITE, algorithm="mcts", depth=2)
    assert ai.choose_move(board) is not None


def test_mcts_handles_branching_position():
    """MCTS returns a legal move on a position with many choices."""
    board = Board(setup=False)
    board.place_piece(SHAH, WHITE, 0)
    board.place_piece(ROOK, WHITE, 16)
    board.place_piece(SHAH, BLACK, 63)
    board.place_piece(PAWN, BLACK, 24)
    engine = RulesEngine()
    mcts = MCTS(engine=engine, simulations=1)
    move = mcts.best_move(board, WHITE)
    assert move is not None
    assert move in engine.generate_legal_moves(board, WHITE)


# ================================================================
# Negative tests
# ================================================================


def test_mcts_returns_none_on_empty_board():
    """No pieces → no moves → None."""
    board = Board(setup=False)
    mcts = MCTS(engine=RulesEngine(), simulations=2)
    assert mcts.best_move(board, WHITE) is None


def test_mcts_returns_legal_move_only():
    """MCTS must never return an illegal move."""
    board = Board(setup=False)
    board.place_piece(SHAH, WHITE, 0)
    board.place_piece(ROOK, WHITE, 1)
    board.place_piece(SHAH, BLACK, 63)
    engine = RulesEngine()
    mcts = MCTS(engine=engine, simulations=5)
    move = mcts.best_move(board, WHITE)
    assert move in engine.generate_legal_moves(board, WHITE)


def test_mcts_minimum_simulations_returns_move():
    """Even with 1 simulation, MCTS returns a move."""
    board = Board(setup=False)
    board.place_piece(SHAH, WHITE, 0)
    board.place_piece(ROOK, WHITE, 1)
    board.place_piece(SHAH, BLACK, 63)
    mcts = MCTS(engine=RulesEngine(), simulations=1)
    assert mcts.best_move(board, WHITE) is not None


def test_mcts_does_not_modify_board():
    """MCTS must not leave the board in a modified state."""
    board = Board(setup=False)
    board.place_piece(SHAH, WHITE, 0)
    board.place_piece(ROOK, WHITE, 1)
    board.place_piece(SHAH, BLACK, 63)

    boards_before = dict(board._boards)
    mcts = MCTS(engine=RulesEngine(), simulations=5)
    mcts.best_move(board, WHITE)
    assert board._boards == boards_before
