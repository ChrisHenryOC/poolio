"""
Hardware fixture helpers for on-device testing.

Provides utilities for detecting hardware availability and skipping
tests that require specific hardware when it's not present.

Usage:
    from tests.device.fixtures import requires_i2c, requires_wifi
    from tests.device.assertions import skip

    def test_i2c_sensor():
        if not requires_i2c():
            skip("I2C not available")
        # ... test code using I2C
"""


def requires_i2c():
    """
    Check if I2C hardware is available.

    Returns:
        True if I2C bus can be initialized, False otherwise
    """
    try:
        import board
        import busio

        # Try to initialize I2C
        i2c = busio.I2C(board.SCL, board.SDA)
        i2c.deinit()
        return True
    except (ImportError, RuntimeError, AttributeError):
        return False


def requires_onewire():
    """
    Check if OneWire hardware is available.

    Returns:
        True if OneWire bus can be initialized, False otherwise
    """
    try:
        import board
        import onewireio

        # Try to initialize OneWire on a common pin
        # Note: This assumes D10 is available for OneWire
        if not hasattr(board, "D10"):
            return False
        ow = onewireio.OneWire(board.D10)
        ow.deinit()
        return True
    except (ImportError, RuntimeError, AttributeError):
        return False


def requires_wifi():
    """
    Check if WiFi is available and connected.

    Returns:
        True if WiFi is available and connected, False otherwise
    """
    try:
        import wifi

        return wifi.radio.connected
    except (ImportError, AttributeError):
        return False


class MockCallTracker:
    """
    Track function calls for testing retry logic.

    Usage:
        tracker = MockCallTracker(fail_count=2, return_value="success")
        result = retry_with_backoff(tracker.call, max_retries=3)
        assert tracker.call_count == 3
        assert result == "success"
    """

    def __init__(self, fail_count=0, return_value=None, exception_type=Exception):
        """
        Initialize the call tracker.

        Args:
            fail_count: Number of times to raise exception before succeeding
            return_value: Value to return on successful call
            exception_type: Type of exception to raise on failure
        """
        self.fail_count = fail_count
        self.return_value = return_value
        self.exception_type = exception_type
        self.call_count = 0
        self.call_times = []

    def call(self):
        """
        Callable that tracks invocations.

        Raises exception for first fail_count calls, then returns return_value.
        """
        import time

        self.call_count += 1
        self.call_times.append(time.monotonic())

        if self.call_count <= self.fail_count:
            raise self.exception_type(f"Mock failure {self.call_count}")

        return self.return_value

    def reset(self):
        """Reset call tracking state."""
        self.call_count = 0
        self.call_times = []
