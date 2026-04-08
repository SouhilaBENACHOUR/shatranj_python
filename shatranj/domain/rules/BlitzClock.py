import time


class BlitzClock:
    def __init__(self, initial_time_seconds: int, increment: int = 0):
        self.times = {
            "white": float(initial_time_seconds),
            "black": float(initial_time_seconds),
        }
        self.increment = increment
        self.last_update = None
        self.active_color = "white"

    def _normalize(self, color: str) -> str:
        """Normalize a color name to the format used internally."""
        return color.strip().lower()

    def start_turn(self, color: str):
        self.active_color = self._normalize(color)
        self.last_update = time.time()

    def end_turn(self):
        if self.last_update is None:
            return

        elapsed = time.time() - self.last_update
        self.times[self.active_color] -= elapsed
        self.times[self.active_color] += self.increment
        self.last_update = None

    def get_remaining_time(self, color: str) -> float:
        color = self._normalize(color)
        if self.active_color == color and self.last_update:
            return self.times[color] - (time.time() - self.last_update)
        return self.times[color]

    def is_flagged(self, color: str) -> bool:
        return self.get_remaining_time(color) <= 0
