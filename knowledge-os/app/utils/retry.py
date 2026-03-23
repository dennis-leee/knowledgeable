"""Retry utilities for self-healing."""

import asyncio
import functools
from typing import Any, Callable, Optional, TypeVar

T = TypeVar("T")


class RetryError(Exception):
    """Retry exhausted error."""

    def __init__(self, message: str, attempts: int, last_error: Optional[Exception] = None):
        super().__init__(message)
        self.attempts = attempts
        self.last_error = last_error


def async_retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff_multiplier: float = 2.0,
    exceptions: tuple = (Exception,),
):
    """Decorator for async retry with exponential backoff."""

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            last_error: Optional[Exception] = None
            current_delay = delay

            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_error = e
                    if attempt == max_attempts:
                        raise RetryError(
                            f"Retry exhausted after {max_attempts} attempts: {str(e)}",
                            attempts=max_attempts,
                            last_error=e,
                        ) from e

                    await asyncio.sleep(current_delay)
                    current_delay *= backoff_multiplier

            raise RetryError(
                f"Retry exhausted after {max_attempts} attempts",
                attempts=max_attempts,
                last_error=last_error,
            )

        return wrapper

    return decorator


def sync_retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff_multiplier: float = 2.0,
    exceptions: tuple = (Exception,),
):
    """Decorator for sync retry with exponential backoff."""

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            import time

            last_error: Optional[Exception] = None
            current_delay = delay

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_error = e
                    if attempt == max_attempts:
                        raise RetryError(
                            f"Retry exhausted after {max_attempts} attempts: {str(e)}",
                            attempts=max_attempts,
                            last_error=e,
                        ) from e

                    time.sleep(current_delay)
                    current_delay *= backoff_multiplier

            raise RetryError(
                f"Retry exhausted after {max_attempts} attempts",
                attempts=max_attempts,
                last_error=last_error,
            )

        return wrapper

    return decorator
