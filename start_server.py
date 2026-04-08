#!/usr/bin/env python3
"""
Script pour lancer un serveur Shatranj
Usage: python3 start_server.py
"""

from shatranj.domain.network import GameServer, DiscoveryServer
import time


def main():
    print("🚀 Démarrage du serveur Shatranj...")
    print("📡 Port TCP: 12345, Port UDP: 12346")

    # Serveur de découverte (UDP)
    discovery = DiscoveryServer("ShatranjServer", 12345, "1.0")
    discovery.start()

    # Serveur de jeu (TCP)
    server = GameServer("ShatranjServer", 12345)
    server.start()

    print("✅ Serveur prêt! En attente de joueurs...")
    print("💡 Appuyez Ctrl+C pour arrêter")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Arrêt du serveur...")
    finally:
        server.stop()
        discovery.stop()
        print("✅ Serveur arrêté")


if __name__ == "__main__":
    main()
