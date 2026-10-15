import time
from collections.abc import Callable


class TokenBucket:
    """Blocking token bucket; clock/sleep are injectable so tests run in 0 s."""

    def __init__(self, rate_per_s: float, burst: int = 1, clock: Callable[[], float] = time.monotonic,
                 sleep: Callable[[float], None] = time.sleep):
        self.rate, self.burst, self.clock, self.sleep = rate_per_s, burst, clock, sleep
        self.tokens, self.last = float(burst), clock()

    def take(self) -> None:
        now = self.clock()
        self.tokens = min(self.burst, self.tokens + (now - self.last) * self.rate)
        self.last = now
        if self.tokens < 1:
            self.sleep((1 - self.tokens) / self.rate)
            self.last = self.clock()
            self.tokens = 1.0
        self.tokens -= 1
