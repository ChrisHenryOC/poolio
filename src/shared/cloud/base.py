# CloudBackend base class for cloud backend implementations
# CircuitPython compatible (no ABC, no type annotations in signatures)


class CloudBackend:
    """
    Base class for cloud backend implementations.

    Defines the interface that all cloud backends must implement.
    Uses duck typing with NotImplementedError for abstract methods
    since CircuitPython doesn't support ABC.

    Subclasses must implement all methods. Some backends may raise
    NotImplementedError for methods they don't support (e.g., HTTP
    cannot subscribe).
    """

    def connect(self):
        """
        Connect to the cloud backend.

        Establishes connection. Can be called multiple times without error.
        """
        raise NotImplementedError("Subclasses must implement connect()")

    def disconnect(self):
        """
        Disconnect from the cloud backend.

        Cleanly closes connection. Can be called multiple times without error.
        """
        raise NotImplementedError("Subclasses must implement disconnect()")

    @property
    def is_connected(self):
        """
        Return True if connected to the backend.

        Returns:
            Boolean indicating connection state
        """
        raise NotImplementedError("Subclasses must implement is_connected")

    def publish(self, feed, value, qos=0):
        """
        Publish a value to a feed.

        Args:
            feed: Feed name (string)
            value: Value to publish (any type)
            qos: Quality of Service level (0 or 1, default: 0)
                 - 0: At most once (fire and forget)
                 - 1: At least once (acknowledged delivery)

        Returns:
            True if published successfully, False if throttled (MQTT only)

        Raises:
            RuntimeError: If unable to publish
        """
        raise NotImplementedError("Subclasses must implement publish()")

    def subscribe(self, feed, callback):
        """
        Subscribe to a feed with a callback.

        Args:
            feed: Feed name to subscribe to (string)
            callback: Function called with (feed, value) on message

        Raises:
            NotImplementedError: If backend doesn't support subscriptions
        """
        raise NotImplementedError("Subclasses must implement subscribe()")

    def fetch_latest(self, feed):
        """
        Fetch the most recent value from a feed.

        Args:
            feed: Feed name (string)

        Returns:
            Most recent value or None if feed not found
        """
        raise NotImplementedError("Subclasses must implement fetch_latest()")

    def fetch_history(self, feed, hours, resolution=6):
        """
        Fetch historical values from a feed.

        Args:
            feed: Feed name (string)
            hours: Number of hours to look back
            resolution: Data point interval in minutes (default: 6)

        Returns:
            List of values in chronological order
        """
        raise NotImplementedError("Subclasses must implement fetch_history()")

    def sync_time(self):
        """
        Get current time from the backend.

        Returns:
            datetime object representing current time

        Raises:
            RuntimeError: If time sync fails
        """
        raise NotImplementedError("Subclasses must implement sync_time()")
