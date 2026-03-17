"""
Module de communication réseau pour le jeu multijoueur.

Responsabilités :
    - Communication client-serveur pour jeu multijoueur
    - Découverte automatique des serveurs (UDP broadcast)
    - Validation anti-triche côté serveur
    - Gestion des invitations et matchmaking
    - Support multi-clients avec threads

Architecture réseau :
    - Découverte : UDP broadcast sur port 12346
    - Communication : TCP sur port 12345 (par défaut)
    - Serveur multi-threads : un thread par client
    - Validation serveur-side : anti-triche

Composants :
    - Server : Serveur de jeu multi-clients
    - Client : Client réseau pour connexion
    - Protocol : Définition des messages
    - MessageHandler : Traitement des messages

Classe Server :
    Responsabilité : Serveur de jeu multi-clients

    Attributs :
        - port : int (port TCP, défaut 12345)
        - clients : Dict[id, ClientInfo]
        - games : Dict[id, Game]
        - lock : threading.Lock (protection données partagées)

    Méthodes principales :
        - start() : Lancer le serveur
            - Thread principal : accepter connexions TCP
            - Thread UDP : broadcast présence toutes les 10s

        - accept_clients() : Thread d'acceptation
        - handle_client(client_socket) : Thread par client
        - broadcast_presence() : Annoncer présence UDP

    Méthodes gestion parties :
        - create_game(player1_id, player2_id) -> Game
        - validate_move(game_id, move) : Validation anti-triche
        - broadcast_move(game_id, move) : Envoyer à l'adversaire
        - handle_disconnect(client_id) : Gérer déconnexion

    Méthodes invitations :
        - send_invitation(from_id, to_id)
        - accept_invitation(player_id)
        - decline_invitation(player_id)
        - cancel_invitation(player_id)

    Découverte automatique :
        - Message UDP broadcast toutes les 10 secondes
        - Format : SERVER_ANNOUNCE|nom_serveur|port|version
        - Port UDP : 12346
        - Timeout : 30 secondes (3 annonces manquées)

    Validation anti-triche :
        Le serveur DOIT valider tous les coups pour empêcher la triche.
        Flux de validation :
            1. Client envoie MOVE e2-e4
            2. Serveur utilise RulesEngine pour valider
            3. Si invalide : INVALID|reason=illegal_move
            4. Si valide : OK + OPPONENT_MOVE à l'adversaire

    Options de lancement :
        shatranj -s              # Port 12345 par défaut
        shatranj -s 9999         # Port 9999
        shatranj --server 8000   # Port 8000
        shatranj -s -d           # Mode daemon (headless)

Classe Client :
    Responsabilité : Client réseau pour connexion

    Méthodes principales :
        - connect(ip, port) : Connexion TCP au serveur
        - send_move(move) : Envoyer un coup
        - receive_message() : Écoute des messages (thread)
        - handle_opponent_move(move) : Callback coup adverse
        - disconnect() : Fermer la connexion
        - ping_server() : Test de latence

    Découverte de serveurs :
        - listen_for_servers() : Écoute UDP port 12346
        - get_available_servers() -> List[ServerInfo]

    Commandes disponibles :
        - server list : Affiche serveurs disponibles
        - join [IP[:PORT]] : Se connecter
        - quit : Quitter le serveur
        - ping : Tester la connexion

Classe Protocol :
    Responsabilité : Définition des messages du protocole

    Format : Messages texte ASCII terminés par '\n'

    Messages de base :
        - SERVER_ANNOUNCE|nom|port|version : Annonce UDP
        - AUTH|nom_joueur : Authentification
        - AUTH_OK|player_id|color : Succès auth
        - AUTH_FAIL|reason : Échec auth
        - PING : Test connexion
        - PONG TIME=42ms : Réponse ping
        - QUIT : Déconnexion
        - BYE : Confirmation déconnexion

    Messages de jeu :
        - MOVE|e2-e4 : Jouer un coup
        - OK : Coup accepté
        - INVALID|reason : Coup refusé
        - OPPONENT_MOVE|e7-e5 : Coup adverse
        - CHECK : Vous êtes en échec
        - CHECKMATE|winner : Partie terminée
        - STALEMATE : Match nul

    Messages invitations:
        - INVITATION_SENT|player=Bob|timeout=300s
        - INVITATION_RECEIVED|from=Alice|expires=300s
        - ACCEPT : Accepter invitation
        - DECLINE : Refuser invitation
        - CANCEL : Annuler invitation
        - INVITATION_ACCEPTED|starting_game
        - GAME_START|opponent=Alice

    Méthodes :
        - encode_message(type, data) -> bytes
        - decode_message(bytes) -> dict
        - validate_message(msg) -> bool

Classe MessageHandler :
    Responsabilité : Traitement des messages réseau

    Méthodes :
        - handle_auth(client_id, message)
        - handle_move(client_id, message)
        - handle_invitation(client_id, message)
        - handle_disconnect(client_id)

Gestion multi-clients :
    Le serveur doit gérer plusieurs clients simultanément.

    Architecture :
        - Thread principal : accepte les connexions
        - Un thread par client : gère les messages
        - Locks : protège les données partagées

    Données partagées protégées :
        - Liste des clients connectés
        - États des parties en cours
        - File d'attente de matchmaking

Statuts des joueurs :
    - idle : Disponible
    - away : Absent (pas d'invitations)
    - waitgame : En attente de réponse invitation
    - ingame : En partie

    Commandes :
        - players [ID] : Afficher info joueur
        - away : Changer statut en away
        - back : Revenir en idle

Système d'invitations :
    Flux d'invitation :
        1. Player1 : new 2
        2. Server → Player2 : INVITATION_RECEIVED from=Player1 expires=300s
        3. Player2 : accept
        4. Server → Player1 : INVITATION_ACCEPTED starting_game
        5. Server → Both : GAME_START opponent=...

    Timeout : 5 minutes (300 secondes)
    Si pas de réponse : invitation expire automatiquement

Sécurité anti-triche :
    - Validation serveur-side de TOUS les coups
    - Timeout de 1 minute pour déconnexions inopinées
    - Vérification du tour du joueur
    - Protection contre coups illégaux


"""

# TODO: Importer les classes lors de l'implémentation
# from shatranj.domain.network.server import Server
# from shatranj.domain.network.client import Client
# from shatranj.domain.network.protocol import Protocol
# from shatranj.domain.network.message_handler import MessageHandler

__all__ = [
    # Classes principales (à décommenter)
    # "Server",
    # "Client",
    # "Protocol",
    # "MessageHandler",
]
