# Architecture Réseau - Shatranj Multi-Joueurs

## Vue d'ensemble

L'architecture réseau de Shatranj implémente l'intégralité du cahier des charges (Section 6) pour un jeu multi-joueurs fluide, sécurisé et sans configuration manuelle.

## Composants

### 1. Découverte Automatique (UDP Broadcast)

**Port:** 12346 (UDP)  
**Protocole:** UDP broadcast  
**Fréquence:** Toutes les 10 secondes  

#### DiscoveryServer
```python
from shatranj.domain.network import DiscoveryServer

# Crée et lance le serveur de découverte
discovery = DiscoveryServer(
    server_name="Mon Serveur",
    game_port=12345,
    version="1.0"
)
discovery.start()

# Le serveur envoie chaque 10s:
# SERVER_ANNOUNCE|Mon Serveur|12345|1.0
```

#### DiscoveryClient
```python
from shatranj.domain.network import DiscoveryClient

client = DiscoveryClient()
client.start()

# Écoute les annonces UDP et maintient une liste de serveurs
servers = client.get_servers()
for server in servers:
    print(f"{server.name} at {server.ip}:{server.port}")

client.stop()
```

**Caractéristiques:**
- Serveurs considérés hors-ligne après 30 secondes sans annonce
- Découverte automatique sans configuration manuelle
- Adaptation rapide aux changements réseau

### 2. Communication de Jeu (TCP)

**Port:** 12345 (TCP, par défaut)  
**Protocole:** Messages texte ASCII terminés par `\n`  
**Fiabilité:** Garanti (TCP)

#### GameServer
```python
from shatranj.domain.network import GameServer

server = GameServer(
    name="Serveur Shatranj",
    port=12345,
    max_sessions=10
)
server.start()

# Gère automatiquement:
# - Acceptation des connexions TCP
# - Authentification des joueurs
# - Appariement des scripts (matchmaking)
# - Validation anti-triche de tous les coups
# - Multi-threadé: un thread par client
```

#### GameClient
```python
from shatranj.domain.network import GameClient

def handle_message(msg):
    print(f"Reçu: {msg.command} {msg.args}")

client = GameClient("192.168.1.100", 12345, handle_message)
client.connect("AliceNom")

# Jouer un coup
client.play_move("e2-e4")

client.disconnect()
```

### 3. Protocole de Communication

#### Format des Messages

Tous les messages sont terminés par `\n` (LF):

```
COMMANDE|arg1|arg2|...\n
```

#### Commandes Client → Serveur

| Commande | Format | Description |
|----------|--------|-------------|
| AUTH | `AUTH\|nom_joueur` | Authentification |
| MOVE | `MOVE\|e2-e4` | Jouer un coup |
| UNDO | `UNDO` | Annuler le dernier coup |
| HINT | `HINT` | Demander un conseil IA |
| RESIGN | `RESIGN` | S'abandonner |
| DRAW_OFFER | `DRAW_OFFER` | Proposer une nulle |
| DRAW_ACCEPT | `DRAW_ACCEPT` | Accepter une nulle |
| CHAT | `CHAT\|message` | Envoyer message texte |
| QUIT | `QUIT` | Déconnecter |

#### Réponses Serveur → Client

| Réponse | Format | Description |
|---------|--------|-------------|
| AUTH_OK | `AUTH_OK\|player_id=1\|color=white` | Authentification réussie |
| AUTH_FAIL | `AUTH_FAIL\|reason=server_full` | Authentification échouée |
| GAME_START | `GAME_START\|white=Alice\|black=Bob` | Partie commencée |
| OK | `OK` | Coup accepté |
| INVALID | `INVALID\|reason=illegal_move` | Coup refusé |
| OPPONENT_MOVE | `OPPONENT_MOVE\|e7-e5` | Coup adverse reçu |
| CHECK | `CHECK` | Vous êtes en échec |
| CHECKMATE | `CHECKMATE\|winner=white` | Partie terminée (mat) |
| STALEMATE | `STALEMATE` | Match nul (pat) |
| TIMEOUT | `TIMEOUT\|loser=white` | Temps dépassé (blitz) |
| RESIGNATION | `RESIGNATION\|loser=black` | Abandon du joueur |
| ERROR | `ERROR\|message` | Erreur serveur |

### 4. Validation Anti-Triche

Le serveur valide **tous** les coups côté serveur:

```python
# Dans GameServer._handle_move():
if not session.engine.is_valid_move(session.board, move):
    connection.send(Message.build(Response.INVALID, "reason=illegal_move"))
    return

# Validation complète:
# 1. Pièce existe à la case source
# 2. Couleur correcte (c'est votre tour)
# 3. Coup respecte les règles de Shatranj
# 4. Le coup ne met pas votre Shah en échec
```

### 5. Appariement (Matchmaking)

```python
# Flux automatique:
1. Client1 se connecte (AUTH) → Ajouté à waiting_players
2. Client2 se connecte (AUTH) → Ajouté à waiting_players
3. Serveur détecte 2 joueurs en attente
4. Crée une GameSession
5. Chaque client reçoit GAME_START
6. Partie commence (White joue en premier)
```

## Architecture Multi-Threadée

```
Serveur
├── Thread Principal
│   └── Boucle d'acceptation (accepte connexions TCP)
│
├── Thread par Client
│   ├── Reçoit les messages
│   ├── Valide les coups
│   └── Broadcast à l'adversaire
│
└── Thread UDP (DiscoveryServer)
    └── Broadcast présence (toutes les 10s)
```

## Utilisation Complète

### Exemple 1: Lancer un Serveur

```python
from shatranj.domain.network import DiscoveryServer, GameServer

# Serveur de découverte
discovery = DiscoveryServer("MonServeur", 12345, "1.0")
discovery.start()

# Serveur de jeu
server = GameServer("MonServeur", 12345)
server.start()

# Les clients peuvent découvrir le serveur automatiquement!

server.stop()
discovery.stop()
```

### Exemple 2: Découvrir et Rejoindre

```python
from shatranj.domain.network import DiscoveryClient, GameClient

# Découvrir les serveurs
discovery = DiscoveryClient()
discovery.start()

import time
time.sleep(2)

servers = discovery.get_servers()
if servers:
    server = servers[0]
    
    # Se connecter au serveur découvert
    def handle_msg(msg):
        print(f"Reçu: {msg.command}")
    
    client = GameClient(server.ip, server.port, handle_msg)
    client.connect("Alice")
    
    # Jouer
    client.play_move("e2-e4")
    
    client.disconnect()

discovery.stop()
```

### Exemple 3: Exécuter la Démo Complète

```bash
python shatranj/domain/network/example_network.py
```

Cela lance:
- 1 serveur (avec découverte UDP)
- 1 client de découverte
- 2 clients jouant une partie

## Sécurité et Robustesse

### Anti-Triche
- Validation serveur-side de tous les coups
- Vérification du tour du joueur
- Protections contre coups illégaux

### Gestion des Erreurs
- Timeouts sur les sockets (évite les blocages)
- Try/except dans tous les threads
- Logging détaillé de tous les événements

### Performance
- Multi-threadé (un thread par client)
- Non-bloquant (sockets avec timeouts)
- Support jusqu'à 10 sessions simultanées

## Intégration avec le Mode CLI/GUI

```python
# CLI avec mode réseau
from shatranj.presentation.cli.cli import CLI
from shatranj.domain.network import GameClient

# Option: jouer localement
cli = CLI()
cli.run()

# Option: jouer en réseau
client = GameClient("192.168.1.100", 12345, handle_network_message)
client.connect("Alice")
# Intégrer la boucle de jeu pour afficher les coups adverses
```

## Protocole Détaillé

### Séquence d'Authentification

```
Client                          Serveur
  |                               |
  |------- AUTH|Alice ----------->|
  |                         Check auth ok
  |                      Check server not full
  |<------- AUTH_OK|player=1|color=white
  |
  |------- (en attente) -------->|
  |       (attendre 2e joueur)
  |
```

### Séquence d'une Partie

```
Client1 (White)                Server              Client2 (Black)
  |                             |                      |
  |------- AUTH|Alice -------->  |                      |
  |                         Ajout: waiting[Alice]      |
  |                             |                      |
  |                             |<---- AUTH|Bob -------
  |                         Ajout: waiting[Bob]       |
  |                         2+ joueurs -> GAME_START   |
  |<----- GAME_START|white=Alice|black=Bob ----|
  |                             |--- GAME_START|white=Alice|black=Bob -->|
  |                             |                      |
  |------- MOVE|e2-e4 -------->  |                      |
  |                         Validation OK              |
  |<----- OK ----                |                      |
  |                             |--- OPPONENT_MOVE|e2-e4 -->|
  |                             |                      |
  |                             |<---- MOVE|e7-e5 -----
  |                         Validation OK              |
  |<---- OPPONENT_MOVE|e7-e5 --  |                      |
  |                             |<----- OK -----
  |                             |                      |
  | ... (continuation du jeu)  |                      |
  |                             |                      |
```

## Performance et Limitations

- **Clients simultanés:** Limité par OS (généralement > 100)
- **Latence réseau:** Dépend du réseau local
- **Bande passante:** Négligeable (quelques octets par coup)
- **CPU:** Un thread léger par client
- **RAM:** ~1 MB par client (plateau + historique)

## Améliorations Futures

- [ ] Support TCP/IP sur Internet (pas juste LAN)
- [ ] Chiffrement SSL/TLS
- [ ] Protocole binaire compressé
- [ ] Support spectateurs
- [ ] Historique des parties
- [ ] Classement Elo
- [ ] Parties simultanées
- [ ] Timeouts configurables
