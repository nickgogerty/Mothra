"""
Rate limiting utilities for MOTHRA crawlers.
"""

import asyncio
import time
from collections import deque
from typing import Optional


class RateLimiter:
    """
    Token bucket rate limiter for API calls.

    Args:
        calls: Number of calls allowed per period
        period: Time period in seconds
    """

    def __init__(self, calls: int, period: int = 60) -> None:
        self.calls = calls
        self.period = period
        self.timestamps: deque[float] = deque()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """
        Acquire permission to make a call, waiting if necessary.
        """
        async with self._lock:
            now = time.time()

            # Remove timestamps outside the window
            while self.timestamps and self.timestamps[0] < now - self.period:
                self.timestamps.popleft()

            # If we've hit the limit, wait
            if len(self.timestamps) >= self.calls:
                sleep_time = self.period - (now - self.timestamps[0])
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
                    # Recursively try again
                    return await self.acquire()

            # Record this call
            self.timestamps.append(now)

    async def __aenter__(self) -> "RateLimiter":
        """Context manager entry."""
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore
        """Context manager exit."""
        pass


class AdaptiveRateLimiter(RateLimiter):
    """
    Rate limiter that adapts based on error responses (e.g., 429).

    Args:
        calls: Initial number of calls allowed per period
        period: Time period in seconds
        min_calls: Minimum calls per period
        max_calls: Maximum calls per period
    """

    def __init__(
        self,
        calls: int,
        period: int = 60,
        min_calls: int = 1,
        max_calls: Optional[int] = None,
    ) -> None:
        super().__init__(calls, period)
        self.min_calls = min_calls
        self.max_calls = max_calls or calls * 2
        self.original_calls = calls

    def decrease_rate(self, factor: float = 0.5) -> None:
        """
        Decrease the rate limit (e.g., after receiving 429).

        Args:
            factor: Multiplication factor (0 < factor < 1)
        """
        new_calls = max(self.min_calls, int(self.calls * factor))
        self.calls = new_calls

    def increase_rate(self, factor: float = 1.1) -> None:
        """
        Increase the rate limit (e.g., after successful calls).

        Args:
            factor: Multiplication factor (factor > 1)
        """
        new_calls = min(self.max_calls, int(self.calls * factor))
        self.calls = new_calls

    def reset(self) -> None:
        """Reset to original rate limit."""
        self.calls = self.original_calls
