"""
Rôle : Affichage chronomètres Blitz 
Fonctions :
    __init__(time_manager) : Init Gtk.Labels
    update() : Rafraîchit affichage (appelé chaque seconde)
    _format_time(seconds) : "05:30"
    _set_color(label, low_time) : Rouge si < 1 min
"""