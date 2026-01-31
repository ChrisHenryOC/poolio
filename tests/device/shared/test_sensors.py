"""
On-device tests for the shared.sensors module.

These tests verify retry logic functionality. Bus recovery tests are
skipped when hardware is not available.
"""

from shared.sensors import retry_with_backoff
from tests.device.assertions import (
    assert_equal,
    assert_greater,
    assert_raises,
)
from tests.device.fixtures import MockCallTracker

# =============================================================================
# Retry Success Tests
# =============================================================================


def test_retry_with_backoff_success_first_try():
    """Function that succeeds on first try returns immediately."""
    tracker = MockCallTracker(fail_count=0, return_value="success")

    result = retry_with_backoff(tracker.call, max_retries=3)

    assert_equal(result, "success")
    assert_equal(tracker.call_count, 1)


def test_retry_with_backoff_returns_value():
    """Return value from function is passed through."""
    tracker = MockCallTracker(fail_count=0, return_value=42)

    result = retry_with_backoff(tracker.call)

    assert_equal(result, 42)


# =============================================================================
# Retry Failure and Recovery Tests
# =============================================================================


def test_retry_with_backoff_fails_then_succeeds():
    """Function that fails twice then succeeds is retried."""
    tracker = MockCallTracker(fail_count=2, return_value="success")

    result = retry_with_backoff(tracker.call, max_retries=3)

    assert_equal(result, "success")
    assert_equal(tracker.call_count, 3)  # 2 failures + 1 success


def test_retry_with_backoff_exhausted():
    """All retries exhausted raises the last exception."""
    tracker = MockCallTracker(fail_count=10, return_value="never")

    # Should raise after max_retries + 1 attempts
    assert_raises(Exception, retry_with_backoff, tracker.call, max_retries=2)
    assert_equal(tracker.call_count, 3)  # initial + 2 retries


def test_retry_with_backoff_specific_exception():
    """Only specified exception types are caught and retried."""

    class SpecificError(Exception):
        pass

    class OtherError(Exception):
        pass

    # Create tracker that raises SpecificError
    tracker = MockCallTracker(fail_count=1, return_value="success", exception_type=SpecificError)

    result = retry_with_backoff(tracker.call, max_retries=3, exceptions=(SpecificError,))

    assert_equal(result, "success")
    assert_equal(tracker.call_count, 2)


def test_retry_with_backoff_unhandled_exception():
    """Unhandled exception types are not caught."""

    class UnhandledError(Exception):
        pass

    tracker = MockCallTracker(fail_count=1, return_value="success", exception_type=UnhandledError)

    # Should raise immediately, not retry
    assert_raises(
        UnhandledError, retry_with_backoff, tracker.call, max_retries=3, exceptions=(ValueError,)
    )
    assert_equal(tracker.call_count, 1)


# =============================================================================
# Retry Timing Tests
# =============================================================================


def test_retry_with_backoff_has_delay():
    """Retries have delay between attempts."""
    tracker = MockCallTracker(fail_count=2, return_value="success")

    retry_with_backoff(tracker.call, max_retries=3, base_delay=0.01)

    # Verify there was some time between calls
    # (first call is immediate, subsequent calls have delay)
    assert_equal(len(tracker.call_times), 3)

    if len(tracker.call_times) >= 2:
        delay_1 = tracker.call_times[1] - tracker.call_times[0]
        assert_greater(delay_1, 0.005, "Expected delay between retries")


def test_retry_with_backoff_exponential():
    """Delay increases exponentially."""
    tracker = MockCallTracker(fail_count=3, return_value="success")

    retry_with_backoff(tracker.call, max_retries=4, base_delay=0.01, max_delay=1.0)

    # Check that delays are increasing
    if len(tracker.call_times) >= 4:
        delay_1 = tracker.call_times[1] - tracker.call_times[0]
        delay_2 = tracker.call_times[2] - tracker.call_times[1]
        delay_3 = tracker.call_times[3] - tracker.call_times[2]

        # Second delay should be roughly double the first
        assert_greater(delay_2, delay_1 * 1.5, "Expected exponential backoff")
        assert_greater(delay_3, delay_2 * 1.5, "Expected exponential backoff")
