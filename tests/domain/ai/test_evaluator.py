import pytest

from shatranj.domain.ai.evaluator import Evaluator
from shatranj.domain.core.board import Board
from shatranj.utils.constants import BLACK, ROOK, SHAH, WHITE
from shatranj.utils.exceptions import EvaluatorError

# ================================================================
# Evaluator — positive tests
# ================================================================


def test_evaluator_equal_position():
    """Symmetric position → score zero."""
    board = Board(setup=False)
    board.place_piece(SHAH, WHITE, 0)
    board.place_piece(SHAH, BLACK, 63)
    evaluator = Evaluator()
    assert evaluator.evaluate(board, WHITE) == 0


def test_evaluator_white_advantage():
    """White has one extra rook → positive score for WHITE."""
    board = Board(setup=False)
    board.place_piece(SHAH, WHITE, 0)
    board.place_piece(ROOK, WHITE, 1)
    board.place_piece(SHAH, BLACK, 63)
    evaluator = Evaluator()
    assert evaluator.evaluate(board, WHITE) > 0


def test_evaluator_black_advantage():
    """Black has one extra rook → positive score for BLACK."""
    board = Board(setup=False)
    board.place_piece(SHAH, WHITE, 0)
    board.place_piece(SHAH, BLACK, 63)
    board.place_piece(ROOK, BLACK, 62)
    evaluator = Evaluator()
    assert evaluator.evaluate(board, BLACK) > 0


def test_evaluator_rewards_mobility():
    """Equal material but more active position → better score."""
    evaluator = Evaluator()

    board_center = Board(setup=False)
    board_center.place_piece(SHAH, WHITE, 0)
    board_center.place_piece(ROOK, WHITE, 27)  # d4 (very mobile)
    board_center.place_piece(SHAH, BLACK, 63)

    board_edge = Board(setup=False)
    board_edge.place_piece(SHAH, WHITE, 0)
    board_edge.place_piece(ROOK, WHITE, 8)  # a2 (less mobile)
    board_edge.place_piece(SHAH, BLACK, 63)

    assert evaluator.evaluate(board_center, WHITE) > evaluator.evaluate(
        board_edge, WHITE
    )


# ================================================================
# Evaluator — negative tests
# ================================================================


def test_evaluator_invalid_mode_raises():
    with pytest.raises(EvaluatorError):
        Evaluator(mode="invalid")


def test_evaluator_invalid_mode_message():
    with pytest.raises(EvaluatorError, match="invalid"):
        Evaluator(mode="invalid")


def test_evaluator_empty_board_score_zero():
    """Empty board returns score 0 for material evaluation."""
    board = Board(setup=False)
    ev = Evaluator(mode="material")
    score = ev.evaluate(board, WHITE)
    assert score == 0


def test_evaluator_losing_position_negative_score():
    """Position where opponent has more pieces → negative score."""
    board = Board(setup=False)
    board.place_piece(SHAH, WHITE, 0)
    board.place_piece(SHAH, BLACK, 63)
    board.place_piece(ROOK, BLACK, 10)
    board.place_piece(ROOK, BLACK, 11)
    board.place_piece(ROOK, BLACK, 12)
    ev = Evaluator(mode="material")
    score = ev.evaluate(board, WHITE)
    assert score < 0


def test_evaluator_symmetric_position_score_zero():
    """Perfectly symmetric position → score 0."""
    board = Board(setup=False)
    board.place_piece(SHAH, WHITE, 0)
    board.place_piece(ROOK, WHITE, 1)
    board.place_piece(SHAH, BLACK, 63)
    board.place_piece(ROOK, BLACK, 62)
    ev = Evaluator(mode="material")
    score = ev.evaluate(board, WHITE)
    assert score == 0
