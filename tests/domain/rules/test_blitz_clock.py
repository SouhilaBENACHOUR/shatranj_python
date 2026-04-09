from unittest.mock import patch

from shatranj.domain.rules.BlitzClock import BlitzClock


def test_start_turn_normalizes_color_and_sets_timestamp():
    clock = BlitzClock(60)

    with patch("shatranj.domain.rules.BlitzClock.time.time", return_value=10.0):
        clock.start_turn(" WHITE ")

    assert clock.active_color == "white"
    assert clock.last_update == 10.0


def test_end_turn_subtracts_elapsed_time_and_adds_increment():
    clock = BlitzClock(60, increment=2)
    clock.active_color = "white"
    clock.last_update = 10.0

    with patch("shatranj.domain.rules.BlitzClock.time.time", return_value=15.5):
        clock.end_turn()

    assert clock.times["white"] == 56.5
    assert clock.last_update is None


def test_get_remaining_time_uses_live_clock_for_active_player():
    clock = BlitzClock(60)
    clock.active_color = "black"
    clock.last_update = 20.0

    with patch("shatranj.domain.rules.BlitzClock.time.time", return_value=24.0):
        remaining = clock.get_remaining_time("BLACK")

    assert remaining == 56.0


def test_is_flagged_returns_true_when_time_is_over():
    clock = BlitzClock(1)
    clock.times["black"] = -0.1

    assert clock.is_flagged("black") is True
