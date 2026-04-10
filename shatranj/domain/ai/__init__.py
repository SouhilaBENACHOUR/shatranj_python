"""
AI search and evaluation modules for Shatranj.

Algorithms:
  - Minimax            : depth-limited Minimax with Transposition Table
  - AlphaBeta          : Minimax + Alpha-Beta pruning + Transposition Table
  - MCTS               : Monte Carlo Tree Search + Transposition Table
  - IterativeDeepening : Iterative Deepening over Alpha-Beta

Evaluation functions (Evaluator):
  - material    : piece values only (fast)
  - positional  : material + piece-square tables (medium)
  - advanced    : positional + mobility + center control + shah safety

Transposition Table:
  - ZobristHasher      : computes and updates Zobrist hash keys
  - TranspositionTable : caches previously evaluated positions
"""

__all__ = []