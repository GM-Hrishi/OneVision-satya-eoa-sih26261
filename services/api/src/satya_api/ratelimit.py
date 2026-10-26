"""Fixed-window rate limiting per IP and per signing client (kid), backed by Valkey.

Falls back to an in-process window when Valkey is unreachable so a broker outage never removes
the limit; the fallback is logged.
"""

import logging
import time
from collections import defaultdict

from redis.asyncio import Redis
from redis.exceptions import RedisError

log = logging.getLogger("satya.ratelimit")


class RateLimiter:
    def __init__(self, redis: Redis | None, limit: int, window_s: int, prefix: str) -> None:
        self.redis = redis
        self.limit = limit
        self.window_s = window_s
        self.prefix = prefix
        self._memory: dict[str, int] = defaultdict(int)
        self._memory_window = 0

    async def hit(self, key: str) -> int | None:
        """Count one request; return Retry-After seconds when over the limit, else None."""
        now = int(time.time())
        window = now // self.window_s
        retry_after = (window + 1) * self.window_s - now
        bucket = f"rl:{self.prefix}:{key}:{window}"
        count: int
        if self.redis is not None:
            try:
                async with self.redis.pipeline(transaction=True) as pipe:
                    pipe.incr(bucket)
                    pipe.expire(bucket, self.window_s + 1)
                    count = int((await pipe.execute())[0])
            except (RedisError, OSError):
                log.warning("rate limiter falling back to memory", extra={"limiter": self.prefix})
                count = self._memory_hit(bucket, window)
        else:
            count = self._memory_hit(bucket, window)
        return retry_after if count > self.limit else None

    def _memory_hit(self, bucket: str, window: int) -> int:
        if window != self._memory_window:
            self._memory.clear()
            self._memory_window = window
        self._memory[bucket] += 1
        return self._memory[bucket]
