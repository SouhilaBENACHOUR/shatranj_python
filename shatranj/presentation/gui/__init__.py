"""
Module de l'interface graphique (GUI).

Responsabilités :
    - Interface graphique complète avec PyGObject (GTK 4)
    - Affichage du plateau 8×8
    - Drag'n'drop des pièces
    - Menus et dialogues
    - Raccourcis clavier personnalisables

Composants :
    - MainWindow : Fenêtre principale avec menus 
    - BoardWidget : Widget personnalisé pour le plateau 
    - MenuBar : Barre de menus
    - DialogManager : Gestion des boîtes de dialogue
    - EventHandler : Gestion des événements souris/clavier
    - TimeDisplay : Affichage du temps (mode blitz)

Classe MainWindow :
    Responsabilité : Fenêtre principale de l'application
    
    Composants :
        - menu_bar : MenuBar (File, Game)
        - board_widget : BoardWidget (plateau de jeu)
        - status_bar : Gtk.Statusbar (messages)
        - timer_labels : Labels pour temps blitz
    
    Méthodes :
        - __init__(app, game) : Initialiser
        - build_ui() : Construire l'interface
        - update_display() : Rafraîchir l'affichage
        - show_error_dialog(message) : Boîte d'erreur
        - show_game_over_dialog(winner) : Dialogue de fin

Classe BoardWidget :
    Responsabilité : Widget personnalisé pour le plateau
    
    Fonctionnalités :
        - Dessine le plateau 8×8 avec Cairo
        - Détecte les clics/mouvements de souris
        - Gère le drag'n'drop des pièces
        - Surligne les cases accessibles
    
    Méthodes :
        - __init__(game) : Initialiser
        - on_draw(widget, cr) : Dessiner le plateau (Cairo)
        - draw_board(cr) : Dessiner les cases 8×8
        - draw_pieces(cr) : Dessiner les pièces
        - draw_highlights(cr) : Surligner coups possibles
        - on_button_press(widget, event) : Clic souris 
        - on_button_release(widget, event) : Fin drag'n'drop 
        - on_motion_notify(widget, event) : Déplacement souris 
        - square_from_coords(x, y) -> int : Pixels → case
        - coords_from_square(square) -> Tuple[int, int] : Case → pixels
    
    Drag'n'Drop :
        Fonctionnement :
            1. Clic sur une pièce → Pièce "attrapée"
            2. Déplacement souris → Pièce suit le curseur
            3. Relâchement → Pièce déposée sur case
        
        Affichage des coups possibles :
            - Quand pièce sélectionnée
            - Surligner les cases accessibles
            - Utilise MoveGenerator de la couche Domain

Classe MenuBar :
    Responsabilité : Barre de menus de l'application
    
    Menu "File" :
        - New Game (Ctrl+N)
        - Load Game... (Ctrl+L)
        - Save Game... (Ctrl+S)
        - Configuration (Ctrl+,)
        - Info (Ctrl+I)
        - Quit (Ctrl+Q)
    
    Menu "Game"  :
        - Undo (Ctrl+U)
        - Redo (Ctrl+R)
        - Pause (Ctrl+P)
        - Hint (Ctrl+H)
    
    Méthodes :
        - build_file_menu() : Construire menu File
        - build_game_menu() : Construire menu Game
        - on_new_game() : Handler nouvelle partie
        - on_load_game() : Handler charger
        - on_save_game() : Handler sauvegarder
        - on_undo() : Handler annuler 
        - on_redo() : Handler rejouer 
        - on_pause() : Handler pause 
        - on_hint() : Handler conseil
        - setup_shortcuts() : Configurer raccourcis 

Classe DialogManager :
    Responsabilité : Gestion des boîtes de dialogue
    
    Dialogues :
        - NewGameDialog : Configuration nouvelle partie
        - LoadGameDialog : Sélection fichier à charger
        - SaveGameDialog : Sélection fichier de sauvegarde
        - SettingsDialog : Configuration de l'application
        - HintDialog : Affichage du conseil IA
        - GameOverDialog : Fin de partie (mat/pat)
    
    Méthodes :
        - show_new_game_dialog() -> Optional[GameConfig]
        - show_load_dialog() -> Optional[str]
        - show_save_dialog() -> Optional[str]
        - show_settings_dialog()
        - show_hint_dialog(move, explanation)
        - show_game_over_dialog(result, winner)

Classe EventHandler :
    Responsabilité : Gestion des événements souris/clavier
    
    Méthodes :
        - handle_mouse_click(x, y) : Clic souris
        - handle_key_press(key) : Touche clavier
        - handle_drag_start(square) : Début drag
        - handle_drag_motion(x, y) : Mouvement drag
        - handle_drag_end(square) : Fin drag

Classe TimeDisplay (F13) :
    Responsabilité : Affichage du temps en mode blitz
    
    Affichage (F13.1) :
        White: 08:42 | Black: 09:15
    
    Méthodes :
        - update_time(white_time, black_time) : Mettre à jour
        - format_time(seconds) -> str : Convertir en MM:SS
        - highlight_current_player(color) : Surligner joueur actif

Raccourcis clavier :
    Raccourcis standards :
        - Ctrl+N : Nouvelle partie
        - Ctrl+L : Charger partie
        - Ctrl+S : Sauvegarder
        - Ctrl+, : Configuration
        - Ctrl+I : Info
        - Ctrl+Q : Quitter
        - Ctrl+U : Undo
        - Ctrl+R : Redo
        - Ctrl+P : Pause
        - Ctrl+H : Hint
    
    Personnalisation :
        - L'utilisateur peut personnaliser les raccourcis
        - Sauvegardés dans .shatranjrc
        - Interface graphique pour configuration
        - Bouton "Reset to defaults"
    
    Format dans .shatranjrc :
        [shortcuts]
        new-game = <Primary>n
        load-game = <Primary>l
        save-game = <Primary>s
        undo = <Primary>u
        redo = <Primary>r

Gestion des événements :
    Flux d'un coup à la souris :
        1. Utilisateur clique sur e2
           → BoardWidget détecte clic
           → Convertit pixels → case 12
           → Demande au Game : "Quels coups depuis case 12 ?"
           → Game retourne : [20, 28] (e3, e4)
           → BoardWidget surligne ces cases
        
        2. Utilisateur clique sur e4
           → BoardWidget détecte clic
           → Convertit pixels → case 28
           → Transmet au Game : "Jouer de 12 vers 28"
           → Game valide et applique
           → BoardWidget rafraîchit l'affichage
"""

# TODO: Importer les classes lors de l'implémentation
# from shatranj.presentation.gui.main_window import MainWindow, ShatranjApp
# from shatranj.presentation.gui.board_widget import BoardWidget
# from shatranj.presentation.gui.menu_bar import MenuBar
# from shatranj.presentation.gui.dialogManager import DialogManager
# from shatranj.presentation.gui.event_handler import EventHandler
# from shatranj.presentation.gui.time_display import TimeDisplay

__all__ = [
    # Classes principales (à décommenter)
    # "ShatranjApp",
    # "MainWindow",
    # "BoardWidget",
    # "MenuBar",
    # "DialogManager",
    # "EventHandler",
    # "TimeDisplay",
]