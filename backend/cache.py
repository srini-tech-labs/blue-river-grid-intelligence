"""Tiny in-process TTL cache for deterministic, frozen-data queries.

Reduces warehouse wake-ups during a demo. Errors are never cached.
"""

import threading
import time
from functools import wraps

DEFAULT_TTL_S = 300.0


def ttl_cache(ttl_s: float = DEFAULT_TTL_S):
    def decorator(fn):
        store: dict = {}
        lock = threading.Lock()

        @wraps(fn)
        def wrapper(*args):
            now = time.monotonic()
            with lock:
                hit = store.get(args)
                if hit and hit[0] > now:
                    return hit[1]
            value = fn(*args)
            with lock:
                store[args] = (now + ttl_s, value)
            return value

        wrapper.cache_clear = store.clear  # type: ignore[attr-defined]
        return wrapper

    return decorator
