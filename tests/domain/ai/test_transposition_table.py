

from shatranj.domain.ai.transposition_table import (
    TranspositionTable,
    ZobristHasher,
    EXACT,
    LOWER_BOUND,
    UPPER_BOUND,
)
from shatranj.domain.core.board import Board
from shatranj.utils.constants import WHITE, BLACK, SHAH, ROOK

# ================================================================
# Positive tests
# ================================================================


def test_tt_store_and_retrieve_exact():
    """Store an EXACT entry and retrieve it."""
    tt = TranspositionTable()
    tt.store(key=1, score=5.0, depth=3, flag=EXACT)
    score, should_use = tt.get(key=1, depth=3, alpha=-100, beta=100)
    assert should_use is True
    assert score == 5.0


def test_tt_lower_bound_usable_when_score_ge_beta():
    """LOWER_BOUND usable when score >= beta."""
    tt = TranspositionTable()
    tt.store(key=1, score=10.0, depth=3, flag=LOWER_BOUND)
    score, should_use = tt.get(key=1, depth=3, alpha=-100, beta=5)
    assert should_use is True


def test_tt_upper_bound_usable_when_score_le_alpha():
    """UPPER_BOUND usable when score <= alpha."""
    tt = TranspositionTable()
    tt.store(key=1, score=-10.0, depth=3, flag=UPPER_BOUND)
    score, should_use = tt.get(key=1, depth=3, alpha=-5, beta=100)
    assert should_use is True


def test_tt_size_increases_after_store():
    """Size increases after storing entries."""
    tt = TranspositionTable()
    tt.store(key=1, score=1.0, depth=1, flag=EXACT)
    tt.store(key=2, score=2.0, depth=1, flag=EXACT)
    assert tt.size() == 2


def test_tt_clear_empties_table():
    """Clear removes all entries."""
    tt = TranspositionTable()
    tt.store(key=1, score=5.0, depth=3, flag=EXACT)
    tt.store(key=2, score=3.0, depth=2, flag=EXACT)
    tt.clear()
    assert tt.size() == 0


def test_zobrist_same_position_same_key():
    """Same position always produces same key."""
    hasher = ZobristHasher()
    board = Board(setup=False)
    board.place_piece(SHAH, WHITE, 0)
    board.place_piece(SHAH, BLACK, 63)
    assert hasher.compute_key(board, WHITE) == hasher.compute_key(board, WHITE)


def test_zobrist_color_to_move_changes_key():
    """Same position but different color to move → different key."""
    hasher = ZobristHasher()
    board = Board(setup=False)
    board.place_piece(SHAH, WHITE, 0)
    board.place_piece(SHAH, BLACK, 63)
    assert hasher.compute_key(board, WHITE) != hasher.compute_key(board, BLACK)


# ================================================================
# Negative tests
# ================================================================


def test_tt_get_unknown_key_returns_false():
    """Getting an unknown key returns (None, False)."""
    tt = TranspositionTable()
    score, should_use = tt.get(99999, depth=3, alpha=-100, beta=100)
    assert score is None
    assert should_use is False


def test_tt_get_insufficient_depth_returns_false():
    """Entry found but depth too shallow → not usable."""
    tt = TranspositionTable()
    tt.store(key=1, score=5.0, depth=2, flag=EXACT)
    score, should_use = tt.get(key=1, depth=4, alpha=-100, beta=100)
    assert should_use is False


def test_tt_lower_bound_not_usable_when_score_less_than_beta():
    """LOWER_BOUND not usable when score < beta."""
    tt = TranspositionTable()
    tt.store(key=1, score=3.0, depth=3, flag=LOWER_BOUND)
    score, should_use = tt.get(key=1, depth=3, alpha=-100, beta=10)
    assert should_use is False


def test_tt_upper_bound_not_usable_when_score_greater_than_alpha():
    """UPPER_BOUND not usable when score > alpha."""
    tt = TranspositionTable()
    tt.store(key=1, score=7.0, depth=3, flag=UPPER_BOUND)
    score, should_use = tt.get(key=1, depth=3, alpha=-100, beta=100)
    assert should_use is False


def test_tt_evicts_oldest_when_full():
    """When table is full, oldest entry is evicted."""
    tt = TranspositionTable(max_size=3)
    tt.store(key=1, score=1.0, depth=1, flag=EXACT)
    tt.store(key=2, score=2.0, depth=1, flag=EXACT)
    tt.store(key=3, score=3.0, depth=1, flag=EXACT)
    tt.store(key=4, score=4.0, depth=1, flag=EXACT)
    assert tt.size() == 3
    score, should_use = tt.get(key=1, depth=1, alpha=-100, beta=100)
    assert should_use is False


def test_zobrist_different_positions_have_different_keys():
    """Two different positions must have different Zobrist keys."""
    hasher = ZobristHasher()

    board1 = Board(setup=False)
    board1.place_piece(SHAH, WHITE, 0)
    board1.place_piece(SHAH, BLACK, 63)

    board2 = Board(setup=False)
    board2.place_piece(SHAH, WHITE, 0)
    board2.place_piece(SHAH, BLACK, 63)
    board2.place_piece(ROOK, WHITE, 1)

    assert hasher.compute_key
    (board1, WHITE) != hasher.compute_key(board2, WHITE)
