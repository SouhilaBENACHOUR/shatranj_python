#!/usr/bin/env python3
"""
Simple script to play Shatranj over the network with board display.
Usage: python3 play_network.py [player_name]
"""
import builtins
import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))

from shatranj.domain.network import GameClient  # noqa: E402
from shatranj.domain.core.board import Board  # noqa: E402
from shatranj.presentation.cli.display import print_board  # noqa: E402
from shatranj.domain.network.protocol import Response  # noqa: E402
from shatranj.i18n import i18n_setup  # noqa: E402

i18n_setup()
_ = builtins.__dict__.get("_", lambda x: x)


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
        print(
            _("Message: {cmd}: {args}").format(
                cmd=msg.command, args=msg.args
            )
        )
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
                print(_("Board load error: {e}").format(e=e))

        if turn_hint:
            self.current_turn = turn_hint

        if msg.command == Response.CONN_OK:
            # Extraire la couleur du joueur
            for arg in msg.args:
                if arg.startswith("color="):
                    self.my_color = arg.split("=")[1]
                    print(
                        _("You are playing: {color}").format(
                            color=self.my_color
                        )
                    )
                    break

        elif msg.command == Response.GAME_START:
            self.game_started = True
            print(_("Game started!"))
            print(
                _("Current turn: {turn}").format(turn=self.current_turn)
            )
            self.display_board()

        elif msg.command == Response.OK:
            print(_("Move played successfully!"))
            self.display_board()

        elif msg.command == Response.OPPONENT_MOVE:
            if msg.args and len(msg.args) > 0:
                move_str = msg.args[0]
                print(
                    _("Opponent plays: {move}").format(move=move_str)
                )
                self.display_board()

        elif msg.command == Response.INVALID:
            reason = None
            for arg in msg.args:
                if arg.startswith("reason="):
                    reason = arg.split("=", 1)[1]
                    break
            if reason:
                print(_("Invalid move: {reason}").format(reason=reason))
            else:
                print(_("Invalid move!"))

        elif msg.command == Response.CHECK:
            print(_("Check!"))

        elif msg.command == Response.CHECKMATE:
            winner = None
            for arg in msg.args:
                if arg.startswith("winner="):
                    winner = arg.split("=")[1]
                    break
            print(_("Checkmate! Winner: {winner}").format(winner=winner))

        elif msg.command == Response.STALEMATE:
            print("🤝 Pat! Match nul.")

    def display_board(self):
        """Display the board with game information."""
        print("\n" + "=" * 50)
        print(_("Current board — {turn} to move").format(
            turn=self.current_turn
        ))
        if self.my_color:
            print(_("You are playing: {color}").format(color=self.my_color))
        print_board(self.board)
        print("=" * 50 + "\n")

    def connect_and_play(self):
        """Connect to the server and start playing."""
        print(
            _("Connecting to Shatranj server as '{name}'...").format(
                name=self.player_name
            )
        )
        print(_("Enter moves as 'e2-e4' or type QUIT to exit."))

        self.client = GameClient("127.0.0.1", 12345, self.on_message)

        if not self.client.connect(self.player_name):
            print(_("Connection to server failed."))
            return

        try:
            while True:
                if self.game_started and self.my_color:
                    print(
                        _("Current turn: {turn}").format(
                            turn=self.current_turn
                        )
                    )
                    if self.current_turn == self.my_color:
                        move = input(_("Your move: ")).strip().upper()
                        if move == "QUIT":
                            break
                        if move:
                            if self.client.play_move(move):
                                print(
                                    _("Move sent: {move}").format(move=move)
                                )
                            else:
                                print(_("Failed to send move."))
                    else:
                        time.sleep(0.1)
                        continue
                else:
                    time.sleep(0.1)
                    continue
        except KeyboardInterrupt:
            print(_("\nDisconnecting..."))
        finally:
            if self.client:
                self.client.disconnect()


def main():
    player_name = sys.argv[1] if len(sys.argv) > 1 else "Player"

    game = NetworkGame(player_name)
    game.connect_and_play()


if __name__ == "__main__":
    main()
