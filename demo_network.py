#!/usr/bin/env python3
"""
Quick demonstration of networked Shatranj with board display.
"""

import os
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(__file__))

from shatranj.domain.network import GameServer, GameClient  # noqa: E402
from shatranj.domain.core.board import Board  # noqa: E402
from shatranj.i18n import i18n_setup  # noqa: E402
from shatranj.presentation.cli.display import print_board  # noqa: E402

i18n_setup()

import builtins  # noqa: E402

_ = builtins.__dict__.get("_", lambda x: x)


def demo_server():
    """Start a local demonstration server."""
    print(_("Starting demonstration server..."))
    server = GameServer("DemoServer", 12345)
    server.start()
    time.sleep(1)
    return server


def demo_client(name, moves):
    """
    Demonstration client that plays moves automatically.
    """
    print(_("Connecting {name}...").format(name=name))
    board = Board()
    my_color = None
    game_started = False

    def on_message(msg):
        nonlocal my_color, game_started
        print(
            _("[{name}] Message: {cmd}: {args}").format(
                name=name, cmd=msg.command, args=msg.args
            )
        )
        if msg.command == "CONN_OK":
            for arg in msg.args:
                if arg.startswith("color="):
                    my_color = arg.split("=")[1]
                    print(
                        _("[{name}] Color: {color}").format(
                            name=name, color=my_color
                        )
                    )
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
                print(
                    _("[{name}] Board load error: {e}").format(name=name, e=e)
                )
        if msg.command == "GAME_START":
            game_started = True
            print(_("[{name}] Game started!").format(name=name))
            print(_("[{name}] Initial board:").format(name=name))
            print_board(board)

        elif msg.command == "OK":
            print(_("[{name}] Move accepted!").format(name=name))
            print(_("[{name}] Board after my move:").format(name=name))
            print_board(board)

        elif msg.command == "OPPONENT_MOVE":
            if msg.args:
                move_str = msg.args[0]
                print(
                    _("[{name}] Opponent plays: {move}").format(
                        name=name, move=move_str
                    )
                )
                print(
                    _("[{name}] Board after opponent move:").format(name=name)
                )
                print_board(board)

    client = GameClient("127.0.0.1", 12345, on_message)

    if not client.connect(name):
        print(_("[{name}] Connection failed.").format(name=name))
        return

    timeout = 10
    while not game_started and timeout > 0:
        time.sleep(0.5)
        timeout -= 0.5

    if not game_started:
        print(_("[{name}] Game did not start.").format(name=name))
        client.disconnect()
        return

    for move in moves:
        if my_color == "WHITE":
            time.sleep(1)
            print(_("[{name}] Playing: {move}").format(name=name, move=move))
            client.play_move(move)

            try:
                from_sq, to_sq = Board.algebraic_to_square(
                    move.split("-")[0]
                ), Board.algebraic_to_square(move.split("-")[1])
                board.move_piece(from_sq, to_sq)
                print(_("[{name}] Board after my move:").format(name=name))
                print_board(board)
            except Exception:
                pass

    time.sleep(2)
    client.disconnect()
    print(_("[{name}] Disconnected.").format(name=name))


def main():
    """Run the network demonstration."""
    print(_("Shatranj network demonstration with board display"))
    print("=" * 60)

    server = demo_server()

    try:
        alice_thread = threading.Thread(
            target=demo_client, args=("Alice", ["e2-e4", "d2-d4"])
        )
        alice_thread.start()

        time.sleep(1)

        bob_thread = threading.Thread(target=demo_client, args=("Bob", []))
        bob_thread.start()

        alice_thread.join(timeout=15)
        bob_thread.join(timeout=15)

    finally:
        server.stop()
        print(_("Demonstration complete."))


if __name__ == "__main__":
    main()
