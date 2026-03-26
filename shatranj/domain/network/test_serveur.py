import time
from shatranj.domain.network.game_server import GameServer

# On allume le serveur
serveur = GameServer("ServeurDeTest", 12345)
serveur.start()

print("Le serveur est allumé !")
print("Appuie sur Ctrl+C pour l'éteindre.")

# On le garde allumé
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    serveur.stop()
    print("Serveur éteint.")