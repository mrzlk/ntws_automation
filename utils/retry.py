"""
Retry utilities for handling transient failures.
"""

import time
import functools
from typing import Callable, Type, Tuple, Optional, TypeVar, Any
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


def retry_on_failure(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Callable[[Exception, int], None] = None
) -> Callable:
    """
    Decorator for retrying failed operations.

    Args:
        max_attempts: Maximum retry attempts.
        delay: Initial delay between retries in seconds.
        backoff: Multiplier for delay after each attempt.
        exceptions: Tuple of exceptions to catch and retry.
        on_retry: Optional callback called on each retry.

    Returns:
        Decorated function.

    Example:
        @retry_on_failure(max_attempts=3, delay=1.0)
        def flaky_operation():
            # May fail sometimes
            pass
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            current_delay = delay
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt < max_attempts - 1:
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_attempts} failed: {e}. "
                            f"Retrying in {current_delay:.1f}s..."
                        )

                        if on_retry:
                            on_retry(e, attempt + 1)

                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            f"All {max_attempts} attempts failed for {func.__name__}"
                        )

            raise last_exception

        return wrapper
    return decorator


def wait_until(
    condition: Callable[[], bool],
    timeout: float = 30.0,
    interval: float = 0.5,
    message: str = "Condition not met"
) -> bool:
    """
    Wait until condition is true.

    Args:
        condition: Callable that returns True when ready.
        timeout: Maximum wait time in seconds.
        interval: Check interval in seconds.
        message: Error message if timeout.

    Returns:
        True if condition met.

    Raises:
        TimeoutError: If condition not met within timeout.

    Example:
        # Wait for element to appear
        wait_until(lambda: element.is_visible(), timeout=10)
    """
    from ..core.exceptions import TimeoutError

    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            if condition():
                return True
        except Exception as e:
            logger.debug(f"Condition check failed: {e}")

        time.sleep(interval)

    raise TimeoutError(message, timeout)


def wait_for_change(
    get_value: Callable[[], Any],
    timeout: float = 30.0,
    interval: float = 0.5
) -> Any:
    """
    Wait for a value to change.

    Args:
        get_value: Callable that returns current value.
        timeout: Maximum wait time.
        interval: Check interval.

    Returns:
        New value after change.

    Raises:
        TimeoutError: If value doesn't change within timeout.
    """
    from ..core.exceptions import TimeoutError

    initial_value = get_value()
    start_time = time.time()

    while time.time() - start_time < timeout:
        current_value = get_value()
        if current_value != initial_value:
            return current_value
        time.sleep(interval)

    raise TimeoutError("Value did not change", timeout)


def with_timeout(timeout: float) -> Callable:
    """
    Decorator to add timeout to a function.

    Note: This is a simple implementation that checks
    timeout after function returns. For true preemptive
    timeout, use threading or asyncio.

    Args:
        timeout: Maximum execution time in seconds.

    Returns:
        Decorated function.
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            start_time = time.time()
            result = func(*args, **kwargs)
            elapsed = time.time() - start_time

            if elapsed > timeout:
                logger.warning(
                    f"{func.__name__} took {elapsed:.2f}s "
                    f"(timeout: {timeout:.2f}s)"
                )

            return result

        return wrapper
    return decorator
