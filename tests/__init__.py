"""
Suite de tests pour le projet Shatranj.

Ce module contient tous les tests unitaires et d'intégration pour valider
le bon fonctionnement de l'application.

Objectif de couverture : 85% minimum (cahier des charges section 1.6)

Organisation des tests :
    - data/ : Tests de la couche données
        - test_bitboard.py : Tests des bitboards
        - test_masks.py : Tests des masques pré-calculés
        - test_operations.py : Tests opérations binaires
        - test_persistance.py : Tests sauvegarde/chargement
    
    - domain/ : Tests de la couche domaine
        - core/ : Tests des classes fondamentales
            - test_board.py : Tests Board
            - test_game.py : Tests Game
            - test_move.py : Tests Move
            - test_time_manager.py : Tests TimeManager
        
        - rules/ : Tests du moteur de règles
            - test_move_generator.py : Tests génération coups
            - test_move_validator.py : Tests validation
            - test_rules_engine.py : Tests détection mat/pat
        
        - ai/ : Tests de l'IA
            - test_evaluator.py : Tests fonctions d'évaluation
            - test_minimax.py : Tests Minimax + Alpha-Beta
            - test_mcts.py : Tests MCTS
        
        - network/ : Tests réseau
            - test_server.py : Tests serveur
            - test_client.py : Tests client
            - test_protocol.py : Tests protocole
    
    - presentation/ : Tests des interfaces
        - test_cli.py : Tests CLI
        - test_gui.py : Tests GUI (si possible)
    
    - integration/ : Tests d'intégration
        - test_full_game.py : Partie complète du début à la fin
        - test_network_game.py : Partie en réseau
        - test_save_load.py : Sauvegarde puis chargement

Marqueurs pytest :
    - @pytest.mark.unit : Tests unitaires
    - @pytest.mark.integration : Tests d'intégration
    - @pytest.mark.slow : Tests lents (à exclure pour CI rapide)

Commandes utiles :
    # Tous les tests
    pytest
    
    # Avec couverture
    pytest --cov=shatranj --cov-report=html
    
    # Vérifier objectif 85%
    pytest --cov=shatranj --cov-fail-under=85
    
    # Tests unitaires uniquement
    pytest -m unit
    
    # Tests rapides (exclure slow)
    pytest -m "not slow"
    
    # Un module spécifique
    pytest tests/data/test_bitboard.py
    
    # Une fonction spécifique
    pytest tests/data/test_bitboard.py::test_set_bit

Configuration pytest :
    Définie dans pyproject.toml (section [tool.pytest.ini_options])
    
    Options par défaut :
        - -v : Verbose
        - --cov=shatranj : Couverture du package
        - --cov-report=term-missing : Lignes non couvertes
        - --cov-report=html : Rapport HTML
        - --cov-fail-under=85 : Échec si couverture < 85%

Fixtures globales :
    Définies dans conftest.py à la racine de tests/
    
    Fixtures disponibles :
        - empty_bitboard : Bitboard vide
        - starting_bitboard : Position de départ
        - sample_game : Partie en cours (quelques coups joués)
        - temp_save_file : Fichier temporaire pour tests
        - mock_board : Mock de Board pour tests isolés
        - sample_moves : Liste de Move objects valides

Bonnes pratiques :
    - Tester les cas nominaux ET les cas limites
    - Tester les erreurs (exceptions attendues)
    - Utiliser des fixtures pour éviter la duplication
    - Nommer les tests explicitement (test_pawn_cannot_move_backwards)
    - Un test = une assertion principale
    - Utiliser pytest.parametrize pour tester plusieurs cas
"""

__all__ = []