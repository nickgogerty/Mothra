"""
Retry utilities with exponential backoff.
"""

import asyncio
from functools import wraps
from typing import Any, Callable, TypeVar, cast

from tenacity import (
    AsyncRetrying,
    RetryError,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from mothra.config import settings
from mothra.utils.logging import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


def async_retry(
    max_attempts: int | None = None,
    min_wait: float = 1.0,
    max_wait: float = 60.0,
    retry_exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Decorator for retrying async functions with exponential backoff.

    Args:
        max_attempts: Maximum number of retry attempts
        min_wait: Minimum wait time between retries in seconds
        max_wait: Maximum wait time between retries in seconds
        retry_exceptions: Tuple of exception types to retry on

    Returns:
        Decorated function with retry logic
    """
    if max_attempts is None:
        max_attempts = settings.retry_attempts

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                async for attempt in AsyncRetrying(
                    stop=stop_after_attempt(max_attempts),
                    wait=wait_exponential(
                        multiplier=settings.retry_backoff_factor,
                        min=min_wait,
                        max=max_wait,
                    ),
                    retry=retry_if_exception_type(retry_exceptions),
                    reraise=True,
                ):
                    with attempt:
                        result = await func(*args, **kwargs)
                        if attempt.retry_state.attempt_number > 1:
                            logger.info(
                                "retry_succeeded",
                                function=func.__name__,
                                attempts=attempt.retry_state.attempt_number,
                            )
                        return result
            except RetryError as e:
                logger.error(
                    "retry_failed",
                    function=func.__name__,
                    max_attempts=max_attempts,
                    error=str(e),
                )
                raise e.last_attempt.exception()  # type: ignore

        return wrapper

    return decorator


async def retry_with_backoff(
    func: Callable[..., Any],
    *args: Any,
    max_attempts: int | None = None,
    **kwargs: Any,
) -> Any:
    """
    Retry a function with exponential backoff.

    Args:
        func: Async function to retry
        *args: Positional arguments for func
        max_attempts: Maximum number of attempts
        **kwargs: Keyword arguments for func

    Returns:
        Result of func

    Raises:
        Last exception if all retries fail
    """
    if max_attempts is None:
        max_attempts = settings.retry_attempts

    last_exception = None

    for attempt in range(max_attempts):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            if attempt < max_attempts - 1:
                wait_time = settings.retry_backoff_factor**attempt
                logger.warning(
                    "retry_attempt",
                    function=func.__name__,
                    attempt=attempt + 1,
                    max_attempts=max_attempts,
                    wait_time=wait_time,
                    error=str(e),
                )
                await asyncio.sleep(wait_time)
            else:
                logger.error(
                    "retry_exhausted",
                    function=func.__name__,
                    max_attempts=max_attempts,
                    error=str(e),
                )

    if last_exception:
        raise last_exception
