#!/usr/bin/env python3
"""
Démonstration rapide du jeu en réseau avec affichage du plateau
"""

import os
import sys
import time
import threading

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(__file__))

from shatranj.domain.network import GameServer, GameClient
from shatranj.domain.core.board import Board
from shatranj.presentation.cli.display import print_board

def demo_server():
    """Lance un serveur de démonstration"""
    print("🚀 Démarrage du serveur de démonstration...")
    server = GameServer("DemoServer", 12345)
    server.start()
    time.sleep(1)  # Laisser le temps au serveur de démarrer
    return server

def demo_client(name, moves):
    """Client de démonstration qui joue automatiquement"""
    print(f"🎮 Connexion de {name}...")

    board = Board()
    my_color = None
    game_started = False

    def on_message(msg):
        nonlocal my_color, game_started
        print(f"[{name}] 📨 {msg.command}: {msg.args}")

        if msg.command == "AUTH_OK":
            for arg in msg.args:
                if arg.startswith("color="):
                    my_color = arg.split("=")[1]
                    print(f"[{name}] 🎯 Couleur: {my_color}")
                    break

        # Update local board from server if provided
        board_fen = None
        for arg in msg.args:
            if arg.startswith("board="):
                board_fen = arg.split("=", 1)[1]
                break

        if board_fen:
            try:
                board = Board.from_fen(board_fen)
            except Exception as e:
                print(f"[{name}] Erreur lors du chargement du plateau: {e}")

        if msg.command == "GAME_START":
            game_started = True
            print(f"[{name}] 🎮 Partie démarrée!")
            print(f"[{name}] Plateau initial:")
            print_board(board)

        elif msg.command == "OK":
            print(f"[{name}] ✅ Coup accepté!")
            print(f"[{name}] Plateau après mon coup:")
            print_board(board)

        elif msg.command == "OPPONENT_MOVE":
            if msg.args:
                move_str = msg.args[0]
                print(f"[{name}] 🤖 Adversaire: {move_str}")
                print(f"[{name}] Plateau après coup adverse:")
                print_board(board)

    client = GameClient('127.0.0.1', 12345, on_message)

    if not client.connect(name):
        print(f"[{name}] ❌ Échec de connexion")
        return

    # Attendre que la partie commence
    timeout = 10
    while not game_started and timeout > 0:
        time.sleep(0.5)
        timeout -= 0.5

    if not game_started:
        print(f"[{name}] ❌ Partie pas démarrée")
        client.disconnect()
        return

    # Jouer les coups automatiquement
    for move in moves:
        if my_color == "WHITE":  # Seulement les blancs jouent pour la démo
            time.sleep(1)
            print(f"[{name}] 🎯 Joue: {move}")
            client.play_move(move)

            # Mettre à jour le plateau local
            try:
                from_sq, to_sq = Board.algebraic_to_square(move.split("-")[0]), Board.algebraic_to_square(move.split("-")[1])
                board.move_piece(from_sq, to_sq)
                print(f"[{name}] Plateau après mon coup:")
                print_board(board)
            except:
                pass

    time.sleep(2)  # Attendre un peu avant de quitter
    client.disconnect()
    print(f"[{name}] 👋 Déconnexion")

def main():
    print("🎯 Démonstration du jeu Shatranj en réseau avec plateau visible")
    print("=" * 60)

    # Lancer le serveur
    server = demo_server()

    try:
        # Lancer Alice (Blancs)
        alice_thread = threading.Thread(target=demo_client, args=("Alice", ["e2-e4", "d2-d4"]))
        alice_thread.start()

        time.sleep(1)  # Laisser Alice se connecter

        # Lancer Bob (Noirs)
        bob_thread = threading.Thread(target=demo_client, args=("Bob", []))  # Bob ne joue pas, juste observe
        bob_thread.start()

        # Attendre la fin
        alice_thread.join(timeout=15)
        bob_thread.join(timeout=15)

    finally:
        server.stop()
        print("\n✅ Démonstration terminée!")

if __name__ == "__main__":
    main()