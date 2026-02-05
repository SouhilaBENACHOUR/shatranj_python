"""
Couche Présentation du projet Shatranj.

Cette couche gère l'affichage et la détection des événements utilisateur.
C'est la "peau" de l'application.

Responsabilités (selon architecture 3-tiers) :
    1. Affichage : Dessiner le plateau et les pièces
    2. Détection : Intercepter les événements (clics, touches)
    3. Capture de l'intention : Transformer événement en intention de jeu

Interdictions strictes (architecture) :
     AUCUNE règle de jeu dans cette couche
     Pas de validation de coups
     Pas de calcul de cases accessibles
     Pas de logique métier

Sous-modules :
    - cli : Interface en ligne de commande (F4, F14-F19)
    - gui : Interface graphique (F7, F27-F29)

Interface CLI  :
    - Shell interactif avec prompt >>
    - Commandes : new, move, undo, save, load, hint, quit
    - Édition de ligne (readline) 
    - Historique des commandes 
    - Auto-complétion (Tab) 
    - Affichage ASCII du plateau

Interface GUI :
    - Fenêtre GTK avec menus (File, Game)
    - Plateau graphique 8x8
    - Drag'n'drop des pièces 
    - Affichage des coups possibles
    - Dialogues (nouvelle partie, sauvegarde, etc.)
    - Raccourcis clavier 


"""

# TODO: Importer les classes principales lors de l'implémentation
# from shatranj.presentation.cli.shell import ShatranjShell
# from shatranj.presentation.gui.main_window import ShatranjApp

__all__ = [
    # Classes principales (à décommenter)
    # "ShatranjShell",
    # "ShatranjApp",
]