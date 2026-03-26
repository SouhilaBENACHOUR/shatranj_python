from shatranj.domain.core.board import Board
from shatranj.domain.ai.iterative_deepening import IterativeDeepening
from shatranj.domain.ai.evaluator import Evaluator
from shatranj.domain.rules.rules_engine import RulesEngine
from shatranj.utils.constants import WHITE, BLACK, SHAH, ROOK, PAWN


def test_id_returns_a_move():
    """Iterative Deepening returns a move when moves are available."""
    board = Board(setup=False)
    board.place_piece(SHAH, WHITE, 0)
    board.place_piece(ROOK, WHITE, 1)
    board.place_piece(SHAH, BLACK, 63)
    engine = RulesEngine()
    id_    = IterativeDeepening(
        engine    = engine,
        evaluator = Evaluator(mode="material"),
        depth     = 2,
    )
    move = id_.best_move(board, WHITE)
    assert move is not None


def test_id_returns_none_when_no_moves():
    """Iterative Deepening returns None if no moves available."""
    board = Board(setup=False)
    board.place_piece(SHAH, WHITE, 0)
    board.place_piece(ROOK, BLACK, 8)
    board.place_piece(ROOK, BLACK, 1)
    board.place_piece(SHAH, BLACK, 9)
    engine = RulesEngine()
    id_    = IterativeDeepening(
        engine    = engine,
        evaluator = Evaluator(mode="material"),
        depth     = 2,
    )
    move = id_.best_move(board, WHITE)
    assert move is None


def test_id_respects_time_limit():
    """Iterative Deepening stops when time limit is reached."""
    board = Board(setup=True)
    engine = RulesEngine()
    id_    = IterativeDeepening(
        engine     = engine,
        evaluator  = Evaluator(mode="material"),
        depth      = 10,    # profondeur très grande
        time_limit = 0.5,   # mais seulement 0.5 secondes
    )
    move = id_.best_move(board, WHITE)
    assert move is not None  # toujours un coup valide malgré la limite


def test_id_returns_legal_move():
    """Iterative Deepening returns a legal move."""
    board = Board(setup=False)
    board.place_piece(SHAH, WHITE, 0)
    board.place_piece(ROOK, WHITE, 1)
    board.place_piece(SHAH, BLACK, 63)
    engine = RulesEngine()
    id_    = IterativeDeepening(
        engine    = engine,
        evaluator = Evaluator(mode="material"),
        depth     = 2,
    )
    move = id_.best_move(board, WHITE)
    assert move in engine.generate_legal_moves(board, WHITE)