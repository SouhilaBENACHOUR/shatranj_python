import pytest

from shatranj.domain.core.board import Board
from shatranj.domain.ai.ai_player import AIPlayer
from shatranj.domain.rules.rules_engine import RulesEngine
from shatranj.utils.constants import WHITE, BLACK, SHAH, ROOK, PAWN

# ================================================================
# AIPlayer — positive tests
# ================================================================


def test_ai_returns_a_move():
    """AI returns a move when moves are available."""
    board = Board(setup=False)
    board.place_piece(SHAH, WHITE, 0)
    board.place_piece(ROOK, WHITE, 1)
    board.place_piece(SHAH, BLACK, 63)
    ai = AIPlayer(color=WHITE, depth=2)
    move = ai.choose_move(board)
    assert move is not None


def test_ai_returns_none_when_no_moves():
    """AI returns None if no move available (checkmate)."""
    board = Board(setup=False)
    board.place_piece(SHAH, WHITE, 0)
    board.place_piece(ROOK, BLACK, 8)
    board.place_piece(ROOK, BLACK, 1)
    board.place_piece(SHAH, BLACK, 9)
    ai = AIPlayer(color=WHITE, depth=2)
    move = ai.choose_move(board)
    assert move is None


def test_ai_captures_winning_piece():
    """AI must capture an opponent piece if it is the best move."""
    board = Board(setup=False)
    board.place_piece(SHAH, WHITE, 0)
    board.place_piece(ROOK, WHITE, 16)
    board.place_piece(SHAH, BLACK, 63)
    board.place_piece(PAWN, BLACK, 24)
    ai = AIPlayer(color=WHITE, depth=2)
    move = ai.choose_move(board)
    assert move is not None
    assert move.to_square == 24


@pytest.mark.parametrize(
    ("algorithm", "depth"),
    [
        ("alphabeta", 2),
        ("minimax", 2),
        ("mcts", 10),
    ],
)
def test_ai_does_not_mutate_source_board(algorithm, depth):
    """choose_move() must not mutate the board."""
    board = Board(setup=False)
    board.place_piece(SHAH, WHITE, 0)
    board.place_piece(ROOK, WHITE, 1)
    board.place_piece(SHAH, BLACK, 63)

    snapshot = dict(board._boards)
    ai = AIPlayer(color=WHITE, depth=depth, algorithm=algorithm)
    move = ai.choose_move(board)

    assert move is not None
    assert board._boards == snapshot


# ================================================================
# AIPlayer — negative tests
# ================================================================


def test_ai_player_invalid_algorithm_uses_default():
    """Invalid algorithm falls back to minimax without raising."""
    board = Board(setup=False)
    board.place_piece(SHAH, WHITE, 0)
    board.place_piece(ROOK, WHITE, 1)
    board.place_piece(SHAH, BLACK, 63)
    ai = AIPlayer(color=WHITE, algorithm="invalid_algo", depth=2)
    move = ai.choose_move(board)
    assert move is not None  # falls back to minimax → still works


def test_ai_player_invalid_scoring_raises():
    """Invalid scoring raises an error."""
    with pytest.raises(Exception):
        AIPlayer(color=WHITE, scoring="invalid_scoring")


def test_ai_player_returns_none_on_checkmate_all_algos():
    """All algorithms return None on checkmate."""
    board = Board(setup=False)
    board.place_piece(SHAH, WHITE, 0)
    board.place_piece(ROOK, BLACK, 1)
    board.place_piece(ROOK, BLACK, 8)
    board.place_piece(SHAH, BLACK, 9)

    for algo in ("minimax", "alphabeta", "mcts", "iterative"):
        ai = AIPlayer(color=WHITE, algorithm=algo, depth=2)
        move = ai.choose_move(board)
        assert move is None, f"{algo} should return None on checkmate"


def test_ai_player_returns_legal_move_all_algos():
    """All algorithms return a legal move."""
    board = Board(setup=False)
    board.place_piece(SHAH, WHITE, 0)
    board.place_piece(ROOK, WHITE, 1)
    board.place_piece(SHAH, BLACK, 63)
    engine = RulesEngine()

    for algo in ("minimax", "alphabeta", "mcts", "iterative"):
        ai = AIPlayer(color=WHITE, algorithm=algo, depth=2)
        move = ai.choose_move(board)
        assert move is not None
        assert move in engine.generate_legal_moves(
            board, WHITE
        ), f"{algo} returned an illegal move"


def test_ai_player_does_not_modify_board_all_algos():
    """All algorithms must not modify the board."""
    board = Board(setup=False)
    board.place_piece(SHAH, WHITE, 0)
    board.place_piece(ROOK, WHITE, 1)
    board.place_piece(SHAH, BLACK, 63)

    boards_before = dict(board._boards)

    for algo in ("minimax", "alphabeta", "mcts", "iterative"):
        ai = AIPlayer(color=WHITE, algorithm=algo, depth=2)
        ai.choose_move(board)
        assert board._boards == boards_before, f"{algo} modified the board"
