"""
Rôle : Serveur TCP multi-thread Fonctions :

    __init__(port) : Init socket TCP
    start() : Boucle accept() clients
    _handle_client(client_socket, addr) : Thread par client
    _broadcast_udp() : Thread annonces UDP découverte
    _validate_move(game_id, player_id, move) : Anti-triche
    _route_message(game_id, message) : Dispatch aux bons joueurs
    Attributs : clients[], games{}, locks{} (mutex par partie)
"""