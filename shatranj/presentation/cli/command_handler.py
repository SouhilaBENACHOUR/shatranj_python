"""
Rôle : Parse et exécute commandes shell 
Fonctions :
    handle(command_str) : Dispatcher commande
    cmd_new(**kwargs) : Nouvelle partie
    cmd_help(command=None) : Affiche aide
    cmd_quit() : Quitte (propose save si non sauvegardé)
    cmd_load(filepath) : Charge partie
    cmd_save(filepath) : Sauvegarde partie
    cmd_show(what) : board, history, time, configuration
    cmd_undo(n=1), cmd_redo(n=1) : Annulation/rejeu
    cmd_hint() : Conseil IA
    cmd_pause(), cmd_set(param, value) : Blitz/config
    _parse_move(move_str) : "e2-e4" → Move
"""