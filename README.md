# Shatranj

> A Python implementation of Shatranj — the ancient Persian predecessor to modern chess — featuring a full game engine, GTK GUI, multiple AI algorithms, network multiplayer, and internationalization.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue) ![Version](https://img.shields.io/badge/version-0.4.0-green) ![License](https://img.shields.io/badge/license-MIT-lightgrey)

---

## Features

- **Game engine** — Full Shatranj rules with bitboard representation
- **CLI** — Interactive shell with algebraic notation, undo/redo, hints
- **GUI** — GTK 3 graphical interface with drag & drop, piece themes, blitz clock
- **AI** — Minimax, Alpha-Beta pruning, MCTS, iterative deepening, transposition table
- **Network** — Local multiplayer server with LAN discovery
- **i18n** — English and French support via gettext
- **Save/Load** — Persistent games in `.shatranj` format

---

## Shatranj vs Modern Chess

| Piece | Shatranj | Modern Chess |
|-------|----------|--------------|
| Ferz (Advisor) | 1 square diagonally | Queen (any direction) |
| Alfil (Elephant) | Jumps exactly 2 squares diagonally | Bishop (any diagonal) |
| Pawn | No double step, promotes to Ferz only | Double step + multiple promotions |

---

## Installation

**Requirements:** Python 3.10+, GTK 3 (for GUI)

```bash
git clone https://github.com/SouhilaBENACHOUR/shatranj_python.git
cd shatranj_python

python3 -m venv .venv
source .venv/bin/activate

pip install -e .
```

---

## Usage

```bash
# Launch CLI (default)
shatranj

# Launch GUI
shatranj --gui

# Play against AI
shatranj --ai B
shatranj --ai A --ai-mode mcts --ai-depth 200

# Blitz mode (30 minutes per player)
shatranj --blitz --time 30

# Load a saved game
shatranj game.shatranj

# Start multiplayer server
shatranj --server 12345
```

### CLI Commands
new [ARGS]          Start new game

load FILE           Load game

save FILE           Save game

hint                Show AI hint

undo [N]            Undo last move(s)

redo [N]            Redo move(s)

show board          Display board

show history        Move history

show time           Remaining time

server start [PORT] Start local server

join [HOST:PORT]    Connect to server

set PARAM=VALUE     Change configuration

quit                Exit

### Move Notation
e2-e4       Simple move

e4xe5       Capture

---

## Internationalization

```bash
LANG=fr_FR.UTF-8 shatranj    # French
LANG=en_US.UTF-8 shatranj    # English
```

---

## Development

```bash
pytest

flake8 shatranj/
black shatranj/
```

Coverage target: **≥ 85%**

---

## Troubleshooting

**Language not changing?** Remove the cached config:
```bash
sed -i '/language/d' ~/.shatranjrc
```

**GTK GUI — missing text / invisible labels?**
```bash
# Temporary fix
GTK_THEME=Adwaita shatranj -g

# Permanent fix
echo 'export GTK_THEME=Adwaita' >> ~/.bashrc
source ~/.bashrc
```

---

## Authors

- BENACHOUR Souhila
- DRIES Amina
- EL GHALI Ayman
- MARCHOUD Souhail
- MEKLAT Sarah
---

## License

MIT License — see [LICENSE](LICENSE) for details.