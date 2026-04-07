"""Interactive network server demo."""

import time

from shatranj.domain.network.game_server import GameServer


def main() -> None:
    """Run the interactive server."""
    serveur = GameServer("ServeurDeTest", 12345)
    serveur.start()

    print("Le serveur est allume !")
    print("Appuie sur Ctrl+C pour l'eteindre.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        serveur.stop()
        print("Serveur eteint.")


if __name__ == "__main__":
    main()
