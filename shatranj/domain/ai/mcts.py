"""
Rôle : Monte Carlo Tree Search 

Fonctions :
    mcts_search(board, time_limit, selection_mode) : Point d'entrée
    _select(node) : Phase 1 - UCT ou RF selection
    _expand(node, board) : Phase 2 - Créer enfants
    _simulate(board) : Phase 3 - Rollout aléatoire
    _backpropagate(node, result) : Phase 4 - Remonter score
    Classe MCTSNode : wins, visits, children[], move
"""