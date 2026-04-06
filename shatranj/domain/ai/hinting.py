"""Helpers for generating move hints with the AI engine."""

from collections.abc import Mapping

from shatranj.domain.ai.ai_player import AIPlayer
from shatranj.domain.core.board import Board
from shatranj.domain.core.move import Move

DEFAULT_HINT_ALGORITHM = "alphabeta"
DEFAULT_HINT_DEPTH = 2
DEFAULT_HINT_SCORING = "advanced"


def _extract_depth(ai_player: AIPlayer) -> int:
    """Return a usable search depth from an existing AI player."""
    search = getattr(ai_player, "_search", None)
    depth = getattr(search, "_depth", None)
    if isinstance(depth, int) and depth > 0:
        return depth
    return DEFAULT_HINT_DEPTH


def build_hint_player(
    color: str,
    ai_players: Mapping[str, AIPlayer],
) -> AIPlayer:
    """
    Return the AI player used to compute a hint for `color`.

    Reuse the configured AI for the current side when available.
    In human-vs-AI mode, clone the configured AI settings for the human side
    so the hint uses the same algorithm/scoring profile.
    """
    current_ai = ai_players.get(color)
    if current_ai is not None:
        return current_ai

    template = next(iter(ai_players.values()), None)
    if template is None:
        return AIPlayer(
            color=color,
            depth=DEFAULT_HINT_DEPTH,
            algorithm=DEFAULT_HINT_ALGORITHM,
            scoring=DEFAULT_HINT_SCORING,
        )

    return AIPlayer(
        color=color,
        depth=_extract_depth(template),
        algorithm=getattr(template, "algorithm", DEFAULT_HINT_ALGORITHM),
        scoring=getattr(template, "scoring", DEFAULT_HINT_SCORING),
    )


def choose_hint_move(
    board: Board,
    color: str,
    ai_players: Mapping[str, AIPlayer],
) -> Move | None:
    """Return an AI-generated hint move for the given position."""
    return build_hint_player(color, ai_players).choose_move(board)
