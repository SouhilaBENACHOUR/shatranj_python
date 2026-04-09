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

Composants implémentés :
    - DiscoveryServer: Serveur UDP diffusant présence (annonces toutes les 10s)
    - DiscoveryClient: Client UDP découvrant serveurs disponibles (timeout 30s)
    - GameServer : Serveur TCP gérant parties multijoueur
    - GameClient : Client TCP se connectant à un serveur
    - PlayerConnection : Gestion communication avec un joueur
    - Protocol : Définition du protocole de messages

Protocole UDP (Découverte) :
    - Port : 12346
    - Fréquence : Tous les 10 secondes
    - Format : SERVER_ANNOUNCE|nom_serveur|port|version
    - Exemple : SERVER_ANNOUNCE|Alice|12345|1.0

Protocole TCP (Jeu) :
    - Port : 12345 (par défaut)
    - Commandes client -> serveur :
        - AUTH|nom_joueur
        - MOVE|e2-e4
        - QUIT
    - Réponses serveur -> client :
        - AUTH_OK|player_id=1|color=white
        - OK (coup accepté)
        - INVALID|reason=illegal_move (coup refusé)
        - OPPONENT_MOVE|e7-e5
        - CHECKMATE|winner=white
"""

from shatranj.domain.network.discovery_client import (DiscoveryClient,
                                                      ServerInfo)
from shatranj.domain.network.discovery_server import DiscoveryServer
from shatranj.domain.network.game_client import GameClient
from shatranj.domain.network.game_server import GameServer, GameSession
from shatranj.domain.network.player_connection import PlayerConnection
# Importer les classes du réseau
from shatranj.domain.network.protocol import (BROADCAST_ADDRESS,
                                              BROADCAST_INTERVAL,
                                              DISCOVERY_PORT,
                                              GAME_PORT_DEFAULT,
                                              SERVER_TIMEOUT, Command,
                                              InvalidReason, Message, Response)

__all__ = [
    # Protocol
    "Command",
    "Response",
    "InvalidReason",
    "Message",
    "DISCOVERY_PORT",
    "BROADCAST_ADDRESS",
    "BROADCAST_INTERVAL",
    "SERVER_TIMEOUT",
    "GAME_PORT_DEFAULT",
    # Discovery
    "DiscoveryServer",
    "DiscoveryClient",
    "ServerInfo",
    # Game
    "GameServer",
    "GameSession",
    "GameClient",
    "PlayerConnection",
]
