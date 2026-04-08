#!/usr/bin/env python3
"""
Script simple pour jouer à Shatranj en réseau avec affichage du plateau
Usage: python3 play_network.py [nom_joueur]
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from shatranj.domain.network import GameClient
from shatranj.domain.core.board import Board
from shatranj.presentation.cli.display import print_board
from shatranj.domain.network.protocol import Response


class NetworkGame:
    def __init__(self, player_name="Joueur"):
        self.player_name = player_name
        self.board = Board(
            setup=False
        )  # Start with empty board, will be updated by server
        self.my_color = None
        self.current_turn = "WHITE"  # Les blancs commencent
        self.client = None
        self.game_started = False

    def on_message(self, msg):
        print(f"📨 {msg.command}: {msg.args}")

        # Extract board state from any message that contains it
        board_fen = None
        turn_hint = None
        for arg in msg.args:
            if arg.startswith("board="):
                board_fen = arg.split("=", 1)[1]
            elif arg.startswith("turn="):
                turn_hint = arg.split("=", 1)[1]

        if board_fen:
            try:
                self.board = Board.from_fen(board_fen)
            except Exception as e:
                print(f"Erreur lors du chargement du plateau: {e}")

        if turn_hint:
            self.current_turn = turn_hint

        if msg.command == Response.CONN_OK:
            # Extraire la couleur du joueur
            for arg in msg.args:
                if arg.startswith("color="):
                    self.my_color = arg.split("=")[1]
                    print(f"🎯 Vous jouez les {self.my_color}")
                    break

        elif msg.command == Response.GAME_START:
            self.game_started = True
            print("🎮 Partie démarrée!")
            print(f"🔁 Tour: {self.current_turn} (envoyé par le serveur)")
            self.display_board()

        elif msg.command == Response.OK:
            print("✅ Coup joué avec succès!")
            self.display_board()

        elif msg.command == Response.OPPONENT_MOVE:
            if msg.args and len(msg.args) > 0:
                move_str = msg.args[0]
                print(f"🤖 Adversaire joue: {move_str}")
                self.display_board()

        elif msg.command == Response.INVALID:
            reason = None
            for arg in msg.args:
                if arg.startswith("reason="):
                    reason = arg.split("=", 1)[1]
                    break
            if reason:
                print(f"❌ Coup invalide: {reason}")
            else:
                print("❌ Coup invalide!")

        elif msg.command == Response.CHECK:
            print("♔ Échec!")

        elif msg.command == Response.CHECKMATE:
            winner = None
            for arg in msg.args:
                if arg.startswith("winner="):
                    winner = arg.split("=")[1]
                    break
            print(f"🏆 Échec et mat! Le gagnant est {winner}")

        elif msg.command == Response.STALEMATE:
            print("🤝 Pat! Match nul.")

    def display_board(self):
        """Affiche le plateau avec des informations de jeu"""
        print("\n" + "=" * 50)
        print(f"Plateau actuel - Tour des {self.current_turn}")
        if self.my_color:
            print(f"Vous jouez les {self.my_color}")
        print_board(self.board)
        print("=" * 50 + "\n")

    def connect_and_play(self):
        """Se connecter et jouer"""
        print(f"🎯 Connexion au serveur Shatranj en tant que '{self.player_name}'...")
        print("💡 Entrez vos coups au format 'e2-e4' ou 'QUIT' pour quitter")

        self.client = GameClient("127.0.0.1", 12345, self.on_message)

        if not self.client.connect(self.player_name):
            print("❌ Échec de connexion au serveur")
            return

        try:
            while True:
                if self.game_started and self.my_color:
                    print(f"🔁 Tour actuel (serveur) : {self.current_turn}")
                    if self.current_turn == self.my_color:
                        move = input("Votre coup: ").strip().upper()
                        if move == "QUIT":
                            break
                        if move:
                            if self.client.play_move(move):
                                print(f"📤 Coup envoyé: {move}")
                            else:
                                print("❌ Erreur d'envoi du coup")
                    else:
                        # Attendre passivement les messages jusqu'à ce que le serveur indique que c'est notre tour
                        import time

                        time.sleep(0.1)
                        continue
                else:
                    import time

                    time.sleep(0.1)
                    continue
        except KeyboardInterrupt:
            print("\n👋 Déconnexion...")
        finally:
            if self.client:
                self.client.disconnect()


def main():
    player_name = sys.argv[1] if len(sys.argv) > 1 else "Joueur"

    game = NetworkGame(player_name)
    game.connect_and_play()


if __name__ == "__main__":
    main()
