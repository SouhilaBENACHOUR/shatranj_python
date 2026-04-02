

from shatranj.domain.core.board import Board
from shatranj.domain.ai.iterative_deepening import IterativeDeepening
from shatranj.domain.ai.evaluator import Evaluator
from shatranj.domain.rules.rules_engine import RulesEngine
from shatranj.utils.constants import WHITE, BLACK, SHAH, ROOK

# ================================================================
# Positive tests
# ================================================================


def test_id_returns_a_move():
    """Iterative Deepening returns a move when moves are available."""
    board = Board(setup=False)
    board.place_piece(SHAH, WHITE, 0)
    board.place_piece(ROOK, WHITE, 1)
    board.place_piece(SHAH, BLACK, 63)
    id_ = IterativeDeepening(
        engine=RulesEngine(),
        evaluator=Evaluator(mode="material"),
        depth=2,
    )
    assert id_.best_move(board, WHITE) is not None


def test_id_returns_none_when_no_moves():
    """Iterative Deepening returns None if no moves available."""
    board = Board(setup=False)
    board.place_piece(SHAH, WHITE, 0)
    board.place_piece(ROOK, BLACK, 8)
    board.place_piece(ROOK, BLACK, 1)
    board.place_piece(SHAH, BLACK, 9)
    id_ = IterativeDeepening(
        engine=RulesEngine(),
        evaluator=Evaluator(mode="material"),
        depth=2,
    )
    assert id_.best_move(board, WHITE) is None


def test_id_respects_time_limit():
    """Iterative Deepening stops when time limit is reached."""
    board = Board(setup=True)
    id_ = IterativeDeepening(
        engine=RulesEngine(),
        evaluator=Evaluator(mode="material"),
        depth=10,
        time_limit=0.5,
    )
    assert id_.best_move(board, WHITE) is not None


def test_id_returns_legal_move():
    """Iterative Deepening returns a legal move."""
    board = Board(setup=False)
    board.place_piece(SHAH, WHITE, 0)
    board.place_piece(ROOK, WHITE, 1)
    board.place_piece(SHAH, BLACK, 63)
    engine = RulesEngine()
    id_ = IterativeDeepening(
        engine=engine,
        evaluator=Evaluator(mode="material"),
        depth=2,
    )
    move = id_.best_move(board, WHITE)
    assert move in engine.generate_legal_moves(board, WHITE)


# ================================================================
# Negative tests
# ================================================================


def test_id_returns_none_on_empty_board():
    """No pieces → no moves → None."""
    board = Board(setup=False)
    id_ = IterativeDeepening(
        engine=RulesEngine(),
        evaluator=Evaluator(mode="material"),
        depth=2,
    )
    assert id_.best_move(board, WHITE) is None


def test_id_returns_none_on_checkmate():
    """Checkmate position → no moves → None."""
    board = Board(setup=False)
    board.place_piece(SHAH, WHITE, 0)
    board.place_piece(ROOK, BLACK, 1)
    board.place_piece(ROOK, BLACK, 8)
    board.place_piece(SHAH, BLACK, 9)
    id_ = IterativeDeepening(
        engine=RulesEngine(),
        evaluator=Evaluator(mode="material"),
        depth=2,
    )
    assert id_.best_move(board, WHITE) is None


def test_id_does_not_modify_board():
    """ID must not leave the board in a modified state."""
    board = Board(setup=False)
    board.place_piece(SHAH, WHITE, 0)
    board.place_piece(ROOK, WHITE, 1)
    board.place_piece(SHAH, BLACK, 63)

    boards_before = dict(board._boards)
    id_ = IterativeDeepening(
        engine=RulesEngine(),
        evaluator=Evaluator(mode="material"),
        depth=2,
    )
    id_.best_move(board, WHITE)
    assert board._boards == boards_before


def test_id_depth_1_returns_move():
    """Even at depth 1, ID returns a valid move."""
    board = Board(setup=False)
    board.place_piece(SHAH, WHITE, 0)
    board.place_piece(ROOK, WHITE, 1)
    board.place_piece(SHAH, BLACK, 63)
    id_ = IterativeDeepening(
        engine=RulesEngine(),
        evaluator=Evaluator(mode="material"),
        depth=1,
    )
    assert id_.best_move(board, WHITE) is not None


def test_id_very_short_time_limit_returns_move():
    """Even with a very short time limit, ID returns a move."""
    board = Board(setup=True)
    id_ = IterativeDeepening(
        engine=RulesEngine(),
        evaluator=Evaluator(mode="material"),
        depth=10,
        time_limit=0.001,  # extremely short
    )
    assert id_.best_move(board, WHITE) is not None
