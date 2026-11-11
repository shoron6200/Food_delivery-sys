"""A small in-memory rate limiter: at most N calls per time window, per key."""

import threading
import time
from collections import defaultdict, deque


class RateLimiter:
    """Remembers when each key (for example a user id) made its recent calls.

    It lives in this server's memory, so it resets on restart and is not shared
    between several servers. That is enough here; a big deployment would keep
    these counts in Redis.
    """

    def __init__(self, max_calls: int, per_seconds: float):
        self.max_calls = max_calls
        self.per_seconds = per_seconds
        self._calls: dict[object, deque[float]] = defaultdict(deque)
        # Requests run in several threads; the lock lets one at a time count.
        self._lock = threading.Lock()

    def allow(self, key: object) -> bool:
        """Record a call for `key`. False if the key has used up its calls."""
        now = time.monotonic()
        with self._lock:
            calls = self._calls[key]
            while calls and now - calls[0] >= self.per_seconds:
                calls.popleft()
            if len(calls) >= self.max_calls:
                return False
            calls.append(now)
            return True

    def reset(self) -> None:
        with self._lock:
            self._calls.clear()
