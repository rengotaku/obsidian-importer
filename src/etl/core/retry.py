"""Retry utilities using tenacity.

Provides:
- with_retry decorator for resilient function calls
- Exponential backoff with jitter
- Logging callbacks for retry events
- Exception-specific retry conditions
"""

import logging
from functools import wraps
from typing import Callable, TypeVar, ParamSpec

from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
    wait_exponential,
    retry_if_exception_type,
    before_log,
    after_log,
    Retrying,
)

from .models import RetryConfig


# Type variables for decorator typing
P = ParamSpec("P")
R = TypeVar("R")


# Default retry configuration
DEFAULT_RETRY_CONFIG = RetryConfig()


def build_tenacity_kwargs(
    config: RetryConfig,
    logger: logging.Logger | None = None,
) -> dict:
    """Convert RetryConfig to tenacity retry() kwargs.

    Args:
        config: RetryConfig instance with retry settings.
        logger: Optional logger for retry callbacks.

    Returns:
        Dictionary of kwargs for tenacity.retry decorator.
    """
    kwargs = {}

    # Stop condition: max attempts
    kwargs["stop"] = stop_after_attempt(config.max_attempts)

    # Wait strategy: exponential backoff with optional jitter
    if config.jitter:
        kwargs["wait"] = wait_random_exponential(
            min=config.min_wait_seconds,
            max=config.max_wait_seconds,
        )
    else:
        kwargs["wait"] = wait_exponential(
            min=config.min_wait_seconds,
            max=config.max_wait_seconds,
            multiplier=config.exponential_base,
        )

    # Retry condition: exception types
    if config.retry_exceptions:
        kwargs["retry"] = retry_if_exception_type(config.retry_exceptions)
    else:
        # Empty tuple means never retry
        kwargs["retry"] = retry_if_exception_type(tuple())

    # Logging callbacks (if logger provided)
    if logger is not None:
        kwargs["before"] = before_log(logger, logging.WARNING)
        kwargs["after"] = after_log(logger, logging.WARNING)

    return kwargs


def create_retry_decorator(
    config: RetryConfig | None = None,
    logger: logging.Logger | None = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Create a retry decorator with the given configuration.

    Args:
        config: RetryConfig instance. Uses DEFAULT_RETRY_CONFIG if None.
        logger: Optional logger for retry event logging.

    Returns:
        A decorator function that adds retry behavior.
    """
    if config is None:
        config = DEFAULT_RETRY_CONFIG

    kwargs = build_tenacity_kwargs(config, logger)

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        # Apply tenacity retry decorator
        retrying_func = retry(**kwargs)(func)

        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            return retrying_func(*args, **kwargs)

        return wrapper

    return decorator


def with_retry(
    config: RetryConfig | None = None,
    logger: logging.Logger | None = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorator factory for adding retry behavior to functions.

    Usage:
        @with_retry()
        def call_api():
            ...

        @with_retry(config=RetryConfig(max_attempts=5))
        def call_api():
            ...

        @with_retry(config=config, logger=my_logger)
        def call_api():
            ...

    Args:
        config: RetryConfig instance. Uses DEFAULT_RETRY_CONFIG if None.
        logger: Optional logger for retry event logging.

    Returns:
        A decorator that wraps the function with retry behavior.
    """
    return create_retry_decorator(config, logger)


# Convenience function for one-off retry calls
def retry_call(
    func: Callable[P, R],
    config: RetryConfig | None = None,
    logger: logging.Logger | None = None,
    *args: P.args,
    **kwargs: P.kwargs,
) -> R:
    """Execute a function with retry behavior.

    Convenience function for one-off retryable calls without using decorator.

    Args:
        func: The function to call.
        config: RetryConfig instance. Uses DEFAULT_RETRY_CONFIG if None.
        logger: Optional logger for retry event logging.
        *args: Positional arguments for func.
        **kwargs: Keyword arguments for func.

    Returns:
        The return value of func.

    Raises:
        RetryError: If all retry attempts fail.
    """
    if config is None:
        config = DEFAULT_RETRY_CONFIG

    tenacity_kwargs = build_tenacity_kwargs(config, logger)

    for attempt in Retrying(**tenacity_kwargs):
        with attempt:
            return func(*args, **kwargs)
