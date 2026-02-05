"""
Rôle : Chronomètres mode Blitz 

Fonctions :
    __init__(time_per_player_sec) : Init temps
    start_timer(player) : Démarre décompte joueur
    pause() : Pause chrono
    resume() : Reprend chrono
    get_remaining_time(player) : Temps restant joueur
    is_timeout(player) : Temps écoulé ?
    Thread interne : décompte chaque seconde
"""