"""
Retry handler with exponential backoff for model adapters.

This module provides retry logic for handling transient failures
when calling LLM APIs.
"""

import asyncio
import logging
import time
from typing import Callable, Optional, Type, Tuple, Any
from functools import wraps

logger = logging.getLogger(__name__)


class RetryConfig:
    """Configuration for retry behavior."""

    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retry_on_exceptions: Optional[Tuple[Type[Exception], ...]] = None
    ):
        """
        Initialize retry configuration.

        Args:
            max_retries: Maximum number of retry attempts
            initial_delay: Initial delay in seconds before first retry
            max_delay: Maximum delay in seconds between retries
            exponential_base: Base for exponential backoff calculation
            jitter: Whether to add random jitter to delays
            retry_on_exceptions: Tuple of exception types to retry on.
                If None, retries on all exceptions.
        """
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retry_on_exceptions = retry_on_exceptions or (Exception,)

    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay for a given retry attempt.

        Args:
            attempt: The retry attempt number (0-indexed)

        Returns:
            Delay in seconds
        """
        delay = min(
            self.initial_delay * (self.exponential_base ** attempt),
            self.max_delay
        )

        if self.jitter:
            import random
            # Add jitter: random value between 0 and delay
            delay = delay * (0.5 + random.random() * 0.5)

        return delay

    def should_retry(self, exception: Exception, attempt: int) -> bool:
        """
        Determine if we should retry after an exception.

        Args:
            exception: The exception that was raised
            attempt: Current retry attempt number

        Returns:
            True if we should retry, False otherwise
        """
        if attempt >= self.max_retries:
            return False

        return isinstance(exception, self.retry_on_exceptions)


def retry_with_backoff(
    config: Optional[RetryConfig] = None,
    on_retry: Optional[Callable[[Exception, int, float], None]] = None
):
    """
    Decorator for adding retry logic with exponential backoff.

    Args:
        config: RetryConfig object. If None, uses default configuration.
        on_retry: Optional callback function called before each retry.
            Receives (exception, attempt, delay) as arguments.

    Returns:
        Decorated function with retry logic

    Example:
        @retry_with_backoff(config=RetryConfig(max_retries=5))
        async def call_api():
            # API call that might fail
            pass
    """
    if config is None:
        config = RetryConfig()

    def decorator(func: Callable) -> Callable:
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                last_exception = None

                for attempt in range(config.max_retries + 1):
                    try:
                        return await func(*args, **kwargs)
                    except Exception as e:
                        last_exception = e

                        if not config.should_retry(e, attempt):
                            logger.error(
                                f"Max retries ({config.max_retries}) exceeded "
                                f"for {func.__name__}: {e}"
                            )
                            raise

                        delay = config.calculate_delay(attempt)

                        logger.warning(
                            f"Retry {attempt + 1}/{config.max_retries} "
                            f"for {func.__name__} after {delay:.2f}s "
                            f"due to: {type(e).__name__}: {e}"
                        )

                        if on_retry:
                            on_retry(e, attempt, delay)

                        await asyncio.sleep(delay)

                # This should never be reached, but just in case
                if last_exception:
                    raise last_exception

            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                last_exception = None

                for attempt in range(config.max_retries + 1):
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        last_exception = e

                        if not config.should_retry(e, attempt):
                            logger.error(
                                f"Max retries ({config.max_retries}) exceeded "
                                f"for {func.__name__}: {e}"
                            )
                            raise

                        delay = config.calculate_delay(attempt)

                        logger.warning(
                            f"Retry {attempt + 1}/{config.max_retries} "
                            f"for {func.__name__} after {delay:.2f}s "
                            f"due to: {type(e).__name__}: {e}"
                        )

                        if on_retry:
                            on_retry(e, attempt, delay)

                        time.sleep(delay)

                # This should never be reached, but just in case
                if last_exception:
                    raise last_exception

            return sync_wrapper

    return decorator


class RetryableError(Exception):
    """Base class for errors that should trigger a retry."""
    pass


class RateLimitError(RetryableError):
    """Error raised when hitting API rate limits."""
    pass


class TimeoutError(RetryableError):
    """Error raised when a request times out."""
    pass


class ServiceUnavailableError(RetryableError):
    """Error raised when the service is temporarily unavailable."""
    pass


# Common retry configurations
DEFAULT_RETRY_CONFIG = RetryConfig(
    max_retries=3,
    initial_delay=1.0,
    max_delay=60.0,
    exponential_base=2.0,
    jitter=True
)

AGGRESSIVE_RETRY_CONFIG = RetryConfig(
    max_retries=5,
    initial_delay=0.5,
    max_delay=30.0,
    exponential_base=2.0,
    jitter=True
)

CONSERVATIVE_RETRY_CONFIG = RetryConfig(
    max_retries=2,
    initial_delay=2.0,
    max_delay=120.0,
    exponential_base=2.0,
    jitter=True
)

API_RATE_LIMIT_RETRY_CONFIG = RetryConfig(
    max_retries=5,
    initial_delay=5.0,
    max_delay=300.0,
    exponential_base=2.0,
    jitter=True,
    retry_on_exceptions=(RateLimitError, TimeoutError, ServiceUnavailableError)
)
