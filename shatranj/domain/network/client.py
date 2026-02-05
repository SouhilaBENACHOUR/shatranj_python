"""
Rôle : Client réseau 
Fonctions :
    __init__() : Init socket
    discover_servers() : Écoute UDP broadcast → liste serveurs
    connect(server_ip, port) : Connexion TCP
    send_move(move) : Envoie MOVE au serveur
    _receive_loop() : Thread réception messages serveur
    Attributs : socket, available_servers[]
"""