# Retry utilities for sensor operations
# CircuitPython compatible (no type annotations in signatures)

import time


def retry_with_backoff(
    func,
    max_retries=3,
    base_delay=0.1,
    max_delay=2.0,
    exceptions=(Exception,),
    logger=None,
):
    """
    Retry a function with exponential backoff.

    Calls the function and retries on failure with increasing delays.
    Delays follow pattern: base_delay, base_delay*2, base_delay*4, ...
    capped at max_delay.

    Example with defaults (base_delay=0.1, max_delay=2.0):
    - Attempt 1: immediate
    - Attempt 2: after 100ms delay
    - Attempt 3: after 200ms delay
    - Attempt 4: after 400ms delay

    With max_retries=6: 100ms, 200ms, 400ms, 800ms, 1600ms, 2000ms (capped)

    Note: Total attempts = max_retries + 1 (initial attempt plus retries)

    Args:
        func: Callable to execute (no arguments)
        max_retries: Maximum number of retry attempts after initial failure (int)
        base_delay: Initial delay in seconds (float)
        max_delay: Maximum delay cap in seconds (float)
        exceptions: Tuple of exception types to catch and retry
        logger: Optional logger for diagnostics

    Returns:
        Return value of func() on success

    Raises:
        The last exception if all retries are exhausted
    """
    delay = min(base_delay, max_delay)  # Cap initial delay too
    last_exception = None

    # Total attempts = initial + max_retries
    total_attempts = max_retries + 1

    for attempt in range(total_attempts):
        try:
            return func()
        except exceptions as e:
            last_exception = e
            attempt_num = attempt + 1

            if attempt < max_retries:
                # More retries available
                if logger:
                    logger.debug(
                        "Attempt %d/%d failed: %s, retrying in %.3fs",
                        attempt_num,
                        total_attempts,
                        e,
                        delay,
                    )
                time.sleep(delay)
                # Exponential backoff with cap
                delay = min(delay * 2, max_delay)
            else:
                # All retries exhausted
                if logger:
                    logger.warning(
                        "All %d attempts failed, last error: %s",
                        total_attempts,
                        e,
                    )

    # If we get here, all retries were exhausted
    raise last_exception
