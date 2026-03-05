from types import SimpleNamespace

from shatranj.domain.core.board import Board
from shatranj.domain.core.move import Move
from shatranj.domain.rules.rules_engine import RulesEngine
from shatranj.utils.constants import WHITE, BLACK, SHAH, ROOK, PAWN, FERZ, KNIGHT


def make_validator(allowed_moves: set[tuple[int, int]]):
    def is_valid_move(board: Board, move: Move) -> bool:
        return (move.from_square, move.to_square) in allowed_moves
    return SimpleNamespace(is_valid_move=is_valid_move)


def make_generator(moves: list[Move]):
    called_methods: list[str] = []

    def record(method_name: str) -> list[Move]:
        called_methods.append(method_name)
        return moves

    def generate_pawn_moves(board: Board, color: str) -> list[Move]:
        return record("pawn")

    def generate_rook_moves(board: Board, color: str) -> list[Move]:
        return record("rook")

    def generate_knight_moves(board: Board, color: str) -> list[Move]:
        return record("knight")

    def generate_alfil_moves(board: Board, color: str) -> list[Move]:
        return record("alfil")

    def generate_ferz_moves(board: Board, color: str) -> list[Move]:
        return record("ferz")

    def generate_shah_moves(board: Board, color: str) -> list[Move]:
        return record("shah")

    generator = SimpleNamespace(
        generate_pawn_moves=generate_pawn_moves,
        generate_rook_moves=generate_rook_moves,
        generate_knight_moves=generate_knight_moves,
        generate_alfil_moves=generate_alfil_moves,
        generate_ferz_moves=generate_ferz_moves,
        generate_shah_moves=generate_shah_moves,
    )
    return generator, called_methods




def test_is_valid_move_delegates_to_validator():
    board = Board(setup=False)
    move = Move(8, 16, PAWN, WHITE)
    validator = make_validator({(8, 16)})
    engine = RulesEngine(validator=validator)
    assert engine.is_valid_move(board, move)




def test_generate_pseudo_legal_moves_aggregates_all_generators():
    board = Board(setup=False)
    move = Move(8, 16, PAWN, WHITE)
    generator, called_methods = make_generator([move])
    engine = RulesEngine(generator=generator)
    moves = engine.generate_pseudo_legal_moves(board, WHITE)
    assert len(moves) == 6
    assert all(m == move for m in moves)
    assert called_methods == ["pawn", "rook", "knight", "alfil", "ferz", "shah"]




def test_generate_legal_moves_filters_with_validator():
    """
    Le générateur mock retourne [legal, illegal] pour chaque pièce.
    Le validateur mock n'accepte que (8, 17).
    Les deux Shah sont obligatoires pour que _is_in_check fonctionne.
    """
    board = Board(setup=False)
    board.place_piece(PAWN, WHITE, 8)
    board.place_piece(PAWN, BLACK, 17)
    board.place_piece(SHAH, WHITE, 63)  # h8 — Shah blanc hors danger
    board.place_piece(SHAH, BLACK, 0)   # a1 — Shah noir obligatoire

    legal = Move(8, 17, PAWN, WHITE)
    illegal = Move(8, 24, PAWN, WHITE)
    generator, _ = make_generator([legal, illegal])
    validator = make_validator({(8, 17)})
    engine = RulesEngine(validator=validator, generator=generator)
    assert engine.generate_legal_moves(board, WHITE) == [legal] * 6




def test_has_legal_moves_with_real_generator_and_validator():
    """
    Tour blanche en a1 avec des cases libres → des coups légaux existent.
    Les deux Shah sont obligatoires pour que _is_in_check fonctionne.
    """
    board = Board(setup=False)
    board.place_piece(ROOK, WHITE, 0)
    board.place_piece(KNIGHT, BLACK, 10)
    board.place_piece(SHAH, WHITE, 63)  # h8 — Shah blanc obligatoire
    board.place_piece(SHAH, BLACK, 7)   # h1 — Shah noir obligatoire
    engine = RulesEngine()
    assert engine.has_legal_moves(board, WHITE)




def test_is_in_check_by_rook():
    """Shah blanc attaqué par une tour noire sur la même colonne."""
    board = Board(setup=False)
    board.place_piece(SHAH, WHITE, 4)   # e1
    board.place_piece(ROOK, BLACK, 60)  # e8 — même colonne
    engine = RulesEngine()
    assert engine._is_in_check(board, WHITE)

def test_is_not_in_check():
    """Shah blanc non attaqué."""
    board = Board(setup=False)
    board.place_piece(SHAH, WHITE, 4)   # e1
    board.place_piece(ROOK, BLACK, 61)  # f8 — colonne différente
    engine = RulesEngine()
    assert not engine._is_in_check(board, WHITE)

def test_is_in_check_by_ferz():
    """Shah blanc attaqué par un ferz noir en diagonale."""
    board = Board(setup=False)
    board.place_piece(SHAH, WHITE, 0)   # a1
    board.place_piece(FERZ, BLACK, 9)   # b2 — diagonale
    engine = RulesEngine()
    assert engine._is_in_check(board, WHITE)

def test_blocker_prevents_check():
    """Une pièce entre la tour et le Shah bloque l'échec."""
    board = Board(setup=False)
    board.place_piece(SHAH, WHITE, 4)   # e1
    board.place_piece(PAWN, WHITE, 36)  # e5 — bloque la colonne
    board.place_piece(ROOK, BLACK, 60)  # e8
    engine = RulesEngine()
    assert not engine._is_in_check(board, WHITE)




def test_is_checkmate():
    """
    Shah blanc en a1 coincé.
    Tour noire en a2 — attaque le Shah, mais protégée par le Shah noir.
    Tour noire en b1 — bloque la fuite, mais protégée par le Shah noir.
    Shah noir en b2 — protège les deux tours, Shah blanc ne peut pas capturer.
    """
    board = Board(setup=False)
    board.place_piece(SHAH, WHITE, 0)   # a1
    board.place_piece(ROOK, BLACK, 8)   # a2 — attaque le Shah
    board.place_piece(ROOK, BLACK, 1)   # b1 — bloque la fuite
    board.place_piece(SHAH, BLACK, 9)   # b2 — protège les deux tours
    engine = RulesEngine()
    assert engine.is_checkmate(board, WHITE)

def test_is_not_checkmate_can_escape():
    """Shah en échec mais b1 est libre → peut fuir."""
    board = Board(setup=False)
    board.place_piece(SHAH, WHITE, 0)   # a1
    board.place_piece(ROOK, BLACK, 8)   # a2 — échec mais b1 libre
    board.place_piece(SHAH, BLACK, 63)  # h8 — obligatoire
    engine = RulesEngine()
    assert not engine.is_checkmate(board, WHITE)

def test_is_not_checkmate_not_in_check():
    """Pas de mat si le Shah n'est pas en échec."""
    board = Board(setup=False)
    board.place_piece(SHAH, WHITE, 27)  # d4 — centre, aucune menace
    board.place_piece(SHAH, BLACK, 63)  # h8 — obligatoire
    engine = RulesEngine()
    assert not engine.is_checkmate(board, WHITE)




def test_is_stalemate():
    """
    Shah blanc en a1, pas en échec mais aucun coup légal.
    Tour noire en b3 contrôle b1 et b2.
    Tour noire en c2 contrôle a2.
    Shah noir en c3 — loin du Shah blanc.
    """
    board = Board(setup=False)
    board.place_piece(SHAH, WHITE, 0)   # a1
    board.place_piece(ROOK, BLACK, 17)  # b3 — contrôle b1 et b2
    board.place_piece(ROOK, BLACK, 10)  # c2 — contrôle a2
    board.place_piece(SHAH, BLACK, 63)  # h8 — loin
    engine = RulesEngine()
    assert engine.is_stalemate(board, WHITE)

def test_is_not_stalemate_has_moves():
    """Shah avec des coups disponibles → pas de pat."""
    board = Board(setup=False)
    board.place_piece(SHAH, WHITE, 27)  # d4 — centre, 8 cases libres
    board.place_piece(SHAH, BLACK, 63)  # h8 — obligatoire
    engine = RulesEngine()
    assert not engine.is_stalemate(board, WHITE)

def test_is_not_stalemate_in_check():
    """Shah en échec → c'est un mat, pas un pat."""
    board = Board(setup=False)
    board.place_piece(SHAH, WHITE, 0)   # a1
    board.place_piece(ROOK, BLACK, 8)   # a2
    board.place_piece(ROOK, BLACK, 1)   # b1
    board.place_piece(SHAH, BLACK, 63)  # h8 — obligatoire
    engine = RulesEngine()
    assert not engine.is_stalemate(board, WHITE)

def test_debug_checkmate():
    board = Board(setup=False)
    board.place_piece(SHAH, WHITE, 0)   # a1
    board.place_piece(ROOK, BLACK, 8)   # a2
    board.place_piece(ROOK, BLACK, 1)   # b1
    board.place_piece(SHAH, BLACK, 63)  # h8
    engine = RulesEngine()
    
    print("\n--- is_in_check ---")
    print(engine._is_in_check(board, WHITE))  # doit être True
    
    print("--- legal moves ---")
    moves = engine.generate_legal_moves(board, WHITE)
    print(moves)  # doit être []
    
    print("--- has_legal_moves ---")
    print(engine.has_legal_moves(board, WHITE))