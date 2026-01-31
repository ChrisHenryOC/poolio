# Mock cloud backend for testing
# CircuitPython compatible (no dataclasses, no type annotations in signatures)

import time

from .base import CloudBackend

# Import datetime with fallback to adafruit_datetime for CircuitPython
try:
    from datetime import datetime
except ImportError:
    try:
        from adafruit_datetime import datetime
    except ImportError:
        datetime = None


class MockBackend(CloudBackend):
    """
    Mock cloud backend for testing.

    Provides in-memory storage for feeds and subscriber callbacks.
    All operations are synchronous and do not require network access.

    Attributes:
        _feeds: Dictionary mapping feed names to list of (timestamp, value) tuples
        _subscribers: Dictionary mapping feed names to list of callback functions
        _connected: Boolean indicating connection state
    """

    def __init__(self, environment="prod"):
        """
        Initialize MockBackend with empty storage.

        Args:
            environment: Environment name (default: prod)
        """
        super().__init__(environment)
        self._feeds = {}
        self._subscribers = {}
        self._connected = False

    def connect(self):
        """
        Connect to the backend (no-op for mock).

        Can be called multiple times without error.
        """
        self._connected = True

    def disconnect(self):
        """
        Disconnect from the backend (no-op for mock).

        Can be called multiple times without error.
        """
        self._connected = False

    @property
    def is_connected(self):
        """Return True if connected to the backend."""
        return self._connected

    def publish(self, feed, value, qos=0):
        """
        Publish a value to a feed.

        Stores the value with current timestamp and notifies all subscribers.

        Args:
            feed: Feed name (string)
            value: Value to publish (any type)
            qos: Quality of Service level (ignored by mock)

        Returns:
            True (mock always succeeds)
        """
        # Note: qos parameter is accepted for interface compatibility
        # but is not used by MockBackend
        timestamp = time.time()

        if feed not in self._feeds:
            self._feeds[feed] = []

        self._feeds[feed].append((timestamp, value))

        if feed in self._subscribers:
            for callback in self._subscribers[feed]:
                callback(feed, value)

        return True

    def subscribe(self, feed, callback):
        """
        Subscribe to a feed with a callback.

        The callback will be called with (feed, value) for each publish.

        Args:
            feed: Feed name to subscribe to (string)
            callback: Function to call with (feed, value) on publish
        """
        if feed not in self._subscribers:
            self._subscribers[feed] = []

        self._subscribers[feed].append(callback)

    def fetch_latest(self, feed):
        """
        Fetch the most recent value from a feed.

        Args:
            feed: Feed name (string)

        Returns:
            Most recent value or None if feed has no values
        """
        if feed not in self._feeds:
            return None

        if not self._feeds[feed]:
            return None

        return self._feeds[feed][-1][1]

    def fetch_history(self, feed, hours, resolution=6):
        """
        Fetch historical values from a feed within time window.

        Args:
            feed: Feed name (string)
            hours: Number of hours to look back (integer or float)
            resolution: Data point interval in minutes (default: 6, ignored by mock)

        Returns:
            List of values in chronological order (oldest first)
        """
        # Note: resolution parameter is accepted for interface compatibility
        # with AdafruitIOHTTP but ignored by MockBackend
        if feed not in self._feeds:
            return []

        cutoff_time = time.time() - (hours * 3600)
        result = []

        for timestamp, value in self._feeds[feed]:
            if timestamp >= cutoff_time:
                result.append(value)

        return result

    def sync_time(self):
        """
        Get current time from the backend.

        Returns:
            datetime object representing current time

        Raises:
            RuntimeError: If datetime module is not available
        """
        if datetime is None:
            raise RuntimeError("datetime module not available")

        return datetime.now()
