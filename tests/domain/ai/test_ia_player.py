from shatranj.domain.core.board import Board
from shatranj.domain.ai.ai_player import AIPlayer
from shatranj.domain.ai.evaluator import Evaluator
from shatranj.utils.constants import WHITE, BLACK, SHAH, ROOK, PAWN


# ================================================================
# Evaluator
# ================================================================

def test_evaluator_equal_position():
    """Position symétrique → score nul."""
    board = Board(setup=False)
    board.place_piece(SHAH, WHITE, 0)
    board.place_piece(SHAH, BLACK, 63)
    evaluator = Evaluator()
    assert evaluator.evaluate(board, WHITE) == 0

def test_evaluator_white_advantage():
    """White a une tour de plus → score positif pour WHITE."""
    board = Board(setup=False)
    board.place_piece(SHAH, WHITE, 0)
    board.place_piece(ROOK, WHITE, 1)   # tour en plus pour WHITE
    board.place_piece(SHAH, BLACK, 63)
    evaluator = Evaluator()
    assert evaluator.evaluate(board, WHITE) > 0

def test_evaluator_black_advantage():
    """Black a une tour de plus → score positif pour BLACK."""
    board = Board(setup=False)
    board.place_piece(SHAH, WHITE, 0)
    board.place_piece(SHAH, BLACK, 63)
    board.place_piece(ROOK, BLACK, 62)  # tour en plus pour BLACK
    evaluator = Evaluator()
    assert evaluator.evaluate(board, BLACK) > 0


def test_evaluator_rewards_mobility():
    """À matériel égal, une position plus active doit être mieux évaluée."""
    evaluator = Evaluator()

    board_center = Board(setup=False)
    board_center.place_piece(SHAH, WHITE, 0)    # a1
    board_center.place_piece(ROOK, WHITE, 27)   # d4 (très mobile)
    board_center.place_piece(SHAH, BLACK, 63)   # h8

    board_edge = Board(setup=False)
    board_edge.place_piece(SHAH, WHITE, 0)      # a1
    board_edge.place_piece(ROOK, WHITE, 8)      # a2 (moins mobile)
    board_edge.place_piece(SHAH, BLACK, 63)     # h8

    assert evaluator.evaluate(board_center, WHITE) > evaluator.evaluate(board_edge, WHITE)


# ================================================================
# AIPlayer
# ================================================================

def test_ai_returns_a_move():
    """L'IA retourne un coup quand des coups sont disponibles."""
    board = Board(setup=False)
    board.place_piece(SHAH, WHITE, 0)
    board.place_piece(ROOK, WHITE, 1)
    board.place_piece(SHAH, BLACK, 63)
    ai = AIPlayer(color=WHITE, depth=2)
    move = ai.choose_move(board)
    assert move is not None

def test_ai_returns_none_when_no_moves():
    """L'IA retourne None si aucun coup disponible (mat)."""
    board = Board(setup=False)
    board.place_piece(SHAH, WHITE, 0)
    board.place_piece(ROOK, BLACK, 8)
    board.place_piece(ROOK, BLACK, 1)
    board.place_piece(SHAH, BLACK, 9)
    ai = AIPlayer(color=WHITE, depth=2)
    move = ai.choose_move(board)
    assert move is None

def test_ai_captures_winning_piece():
    """L'IA doit capturer une pièce adverse si c'est le meilleur coup."""
    board = Board(setup=False)
    board.place_piece(SHAH, WHITE, 0)    # a1
    board.place_piece(ROOK, WHITE, 16)   # a3
    board.place_piece(SHAH, BLACK, 63)   # h8
    board.place_piece(PAWN, BLACK, 24)   # a4 — capturable par la tour
    ai = AIPlayer(color=WHITE, depth=2)
    move = ai.choose_move(board)
    # l'IA doit capturer le pion en a4
    assert move is not None
    assert move.to_square == 24
