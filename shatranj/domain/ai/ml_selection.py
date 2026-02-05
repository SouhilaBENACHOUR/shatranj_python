"""
Rôle : Random Forest pour sélection nœuds MCTS Fonctions :

    collect_training_data(num_games) : Auto-jeu → dataset CSV
    extract_features(node, board) : Matériel, mobilité, centre, etc.
    train_random_forest(dataset_path) : Entraîne sklearn model
    predict_promising_node(nodes, board, model) : Prédit meilleur nœud
    save_model(model, path), load_model(path) : Pickle
"""