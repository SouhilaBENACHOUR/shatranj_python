"""
Rôle : Parser robuste format INI avec gestion erreurs Fonctions :

    parse_save_file(filepath) : Parse complet → dict sections
    parse_settings(lines) : Parse section [settings] → dict config
    parse_game(lines) : Parse section [game] → état plateau
    parse_history(lines) : Parse section [history] → liste Move
    _remove_comments(line) : Strip # et { } commentaires
    _validate_board(board_lines) : Vérifie 8 lignes × 8 colonnes
"""