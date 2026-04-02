

from shatranj.domain.core.board import Board
from shatranj.domain.ai.alphabeta import AlphaBeta
from shatranj.domain.ai.evaluator import Evaluator
from shatranj.domain.rules.rules_engine import RulesEngine
from shatranj.utils.constants import WHITE, BLACK, SHAH, ROOK, PAWN

# ================================================================
# Positive tests
# ================================================================


def test_alphabeta_returns_a_move():
    """AlphaBeta returns a move when moves are available."""
    board = Board(setup=False)
    board.place_piece(SHAH, WHITE, 0)
    board.place_piece(ROOK, WHITE, 1)
    board.place_piece(SHAH, BLACK, 63)
    ab = AlphaBeta(engine=RulesEngine(), evaluator=Evaluator(), depth=2)
    move = ab.best_move(board, WHITE)
    assert move is not None


def test_alphabeta_returns_none_when_no_moves():
    """AlphaBeta returns None if no moves available."""
    board = Board(setup=False)
    board.place_piece(SHAH, WHITE, 0)
    board.place_piece(ROOK, BLACK, 8)
    board.place_piece(ROOK, BLACK, 1)
    board.place_piece(SHAH, BLACK, 9)
    ab = AlphaBeta(engine=RulesEngine(), evaluator=Evaluator(), depth=2)
    move = ab.best_move(board, WHITE)
    assert move is None


def test_alphabeta_captures_winning_piece():
    """AlphaBeta must capture an opponent piece if it is the best move."""
    board = Board(setup=False)
    board.place_piece(SHAH, WHITE, 0)
    board.place_piece(ROOK, WHITE, 16)
    board.place_piece(SHAH, BLACK, 63)
    board.place_piece(PAWN, BLACK, 24)
    ab = AlphaBeta(engine=RulesEngine(), evaluator=Evaluator(), depth=2)
    move = ab.best_move(board, WHITE)
    assert move is not None
    assert move.to_square == 24


def test_alphabeta_same_result_as_minimax():
    """AlphaBeta and Minimax must return the same best move."""
    from shatranj.domain.ai.minmax import Minimax

    board = Board(setup=False)
    board.place_piece(SHAH, WHITE, 0)
    board.place_piece(ROOK, WHITE, 16)
    board.place_piece(SHAH, BLACK, 63)
    board.place_piece(PAWN, BLACK, 24)

    engine = RulesEngine()
    evaluator = Evaluator()

    mm = Minimax(engine=engine, evaluator=evaluator, depth=2)
    ab = AlphaBeta(engine=engine, evaluator=evaluator, depth=2)
    move_mm = mm.best_move(board, WHITE)
    move_ab = ab.best_move(board, WHITE)

    assert move_mm.to_square == move_ab.to_square


# ================================================================
# Negative tests
# ================================================================


def test_alphabeta_returns_none_on_empty_board():
    """No pieces → no moves → None."""
    board = Board(setup=False)
    ab = AlphaBeta(engine=RulesEngine(), evaluator=Evaluator(), depth=2)
    move = ab.best_move(board, WHITE)
    assert move is None


def test_alphabeta_does_not_modify_board():
    """AlphaBeta must not leave the board in a modified state."""
    board = Board(setup=False)
    board.place_piece(SHAH, WHITE, 0)
    board.place_piece(ROOK, WHITE, 1)
    board.place_piece(SHAH, BLACK, 63)

    boards_before = dict(board._boards)
    ab = AlphaBeta(engine=RulesEngine(), evaluator=Evaluator(), depth=2)
    ab.best_move(board, WHITE)
    assert board._boards == boards_before


def test_alphabeta_returns_legal_move_only():
    """AlphaBeta must never return an illegal move."""
    board = Board(setup=False)
    board.place_piece(SHAH, WHITE, 0)
    board.place_piece(ROOK, WHITE, 1)
    board.place_piece(SHAH, BLACK, 63)
    engine = RulesEngine()
    ab = AlphaBeta(engine=engine, evaluator=Evaluator(), depth=2)
    move = ab.best_move(board, WHITE)
    assert move in engine.generate_legal_moves(board, WHITE)


def test_alphabeta_depth_1_returns_move():
    """Even at depth 1, AlphaBeta returns a valid move."""
    board = Board(setup=False)
    board.place_piece(SHAH, WHITE, 0)
    board.place_piece(ROOK, WHITE, 1)
    board.place_piece(SHAH, BLACK, 63)
    ab = AlphaBeta(engine=RulesEngine(), evaluator=Evaluator(), depth=1)
    move = ab.best_move(board, WHITE)
    assert move is not None
