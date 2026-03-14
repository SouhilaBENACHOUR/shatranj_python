from shatranj.domain.core.move import Move


def test_move_fields():
    m = Move(from_square=12, to_square=28, piece_type="PAWN", color="WHITE")
    assert m.from_square == 12
    assert m.to_square == 28
    assert m.piece_type == "PAWN"
    assert m.color == "WHITE"
    assert m.captured_piece is None
