from shatranj.domain.core.board import Board
from shatranj.domain.ai.alphabeta import AlphaBeta
from shatranj.domain.ai.evaluator import Evaluator
from shatranj.domain.rules.rules_engine import RulesEngine
from shatranj.utils.constants import WHITE, BLACK, SHAH, ROOK, PAWN


def test_alphabeta_returns_a_move():
    """AlphaBeta retourne un coup quand des coups sont disponibles."""
    board = Board(setup=False)
    board.place_piece(SHAH, WHITE, 0)
    board.place_piece(ROOK, WHITE, 1)
    board.place_piece(SHAH, BLACK, 63)
    engine   = RulesEngine()
    alphabeta = AlphaBeta(engine=engine, evaluator=Evaluator(), depth=2)
    move = alphabeta.best_move(board, WHITE)
    assert move is not None

def test_alphabeta_returns_none_when_no_moves():
    """AlphaBeta retourne None si aucun coup disponible."""
    board = Board(setup=False)
    board.place_piece(SHAH, WHITE, 0)
    board.place_piece(ROOK, BLACK, 8)
    board.place_piece(ROOK, BLACK, 1)
    board.place_piece(SHAH, BLACK, 9)
    engine   = RulesEngine()
    alphabeta = AlphaBeta(engine=engine, evaluator=Evaluator(), depth=2)
    move = alphabeta.best_move(board, WHITE)
    assert move is None

def test_alphabeta_captures_winning_piece():
    """AlphaBeta doit capturer une pièce adverse si c'est le meilleur coup."""
    board = Board(setup=False)
    board.place_piece(SHAH, WHITE, 0)    # a1
    board.place_piece(ROOK, WHITE, 16)   # a3
    board.place_piece(SHAH, BLACK, 63)   # h8
    board.place_piece(PAWN, BLACK, 24)   # a4 — capturable par la tour
    engine   = RulesEngine()
    alphabeta = AlphaBeta(engine=engine, evaluator=Evaluator(), depth=2)
    move = alphabeta.best_move(board, WHITE)
    assert move is not None
    assert move.to_square == 24

def test_alphabeta_same_result_as_minimax():
    """
    Alpha-Beta et Minimax doivent choisir le même coup
    (Alpha-Beta est juste plus rapide, pas différent).
    """
    from shatranj.domain.ai.minimax import Minimax

    board = Board(setup=False)
    board.place_piece(SHAH, WHITE, 0)
    board.place_piece(ROOK, WHITE, 16)
    board.place_piece(SHAH, BLACK, 63)
    board.place_piece(PAWN, BLACK, 24)

    engine    = RulesEngine()
    evaluator = Evaluator()

    minimax   = Minimax(engine=engine, evaluator=evaluator, depth=2)
    alphabeta = AlphaBeta(engine=engine, evaluator=evaluator, depth=2)

    move_mm = minimax.best_move(board, WHITE)
    move_ab = alphabeta.best_move(board, WHITE)

    # les deux algorithmes doivent choisir le même coup
    assert move_mm.to_square == move_ab.to_square