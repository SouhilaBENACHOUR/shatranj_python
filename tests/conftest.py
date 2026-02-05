"""
Configuration globale des tests pytest.

Ce fichier contient les fixtures partagées par tous les tests.
Les fixtures sont des fonctions qui préparent des objets réutilisables
pour les tests.

Fixtures disponibles :
    - empty_bitboard : Bitboard vide
    - starting_bitboard : Position de départ
    - sample_game : Partie en cours
    - temp_save_file : Fichier temporaire
    - mock_board : Mock de Board
    - sample_moves : Liste de Move valides
"""    