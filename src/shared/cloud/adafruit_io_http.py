# Adafruit IO HTTP client for cloud backend
# CircuitPython compatible (no dataclasses, no type annotations in signatures)

# Import requests with fallback for CircuitPython
try:
    import requests
except ImportError:
    requests = None

# Import datetime with fallback to adafruit_datetime for CircuitPython
try:
    from datetime import datetime
except ImportError:
    try:
        from adafruit_datetime import datetime
    except ImportError:
        datetime = None


class AdafruitIOHTTP:
    """
    HTTP client for Adafruit IO cloud backend.

    Implements the CloudBackend pattern using REST API calls.
    Suitable for nodes that only need to publish data (no subscriptions).

    Attributes:
        _username: Adafruit IO username
        _api_key: Adafruit IO API key
        _environment: Environment name (prod, nonprod, dev, test)
        _connected: Boolean indicating connection state
        _base_url: Base URL for Adafruit IO API v2
    """

    def __init__(self, username, api_key, environment="prod"):
        """
        Initialize AdafruitIOHTTP client.

        Args:
            username: Adafruit IO username
            api_key: Adafruit IO API key
            environment: Environment name (default: prod)
        """
        self._username = username
        self._api_key = api_key
        self._environment = environment
        self._connected = False
        self._base_url = "https://io.adafruit.com/api/v2"

    def connect(self):
        """
        Connect to the backend.

        For HTTP client, this just sets the connected state.
        Can be called multiple times without error.
        """
        self._connected = True

    def disconnect(self):
        """
        Disconnect from the backend.

        For HTTP client, this just clears the connected state.
        Can be called multiple times without error.
        """
        self._connected = False

    @property
    def is_connected(self):
        """Return True if connected to the backend."""
        return self._connected

    def _get_feed_name(self, logical_name):
        """
        Apply environment prefix to feed name per NFR-ENV-002.

        Args:
            logical_name: Logical feed name without prefix

        Returns:
            Feed name with environment prefix (or no prefix for prod)
        """
        if self._environment == "prod":
            return logical_name
        return f"{self._environment}-{logical_name}"

    def _get_headers(self):
        """
        Get headers for API requests.

        Returns:
            Dictionary of HTTP headers
        """
        return {"X-AIO-Key": self._api_key}

    def publish(self, feed, value):
        """
        Publish a value to a feed.

        Args:
            feed: Feed name (string)
            value: Value to publish (any type)

        Raises:
            RuntimeError: If requests module is not available
        """
        if requests is None:
            raise RuntimeError("requests module not available")

        feed_name = self._get_feed_name(feed)
        url = f"{self._base_url}/{self._username}/feeds/{feed_name}/data"

        requests.post(url, headers=self._get_headers(), json={"value": value})

    def subscribe(self, feed, callback):
        """
        Subscribe to a feed with a callback.

        HTTP client does not support subscriptions.

        Args:
            feed: Feed name (string)
            callback: Callback function

        Raises:
            NotImplementedError: Always, HTTP client cannot subscribe
        """
        raise NotImplementedError(
            "HTTP client does not support subscriptions. Use MQTT client instead."
        )

    def fetch_latest(self, feed):
        """
        Fetch the most recent value from a feed.

        Args:
            feed: Feed name (string)

        Returns:
            Most recent value or None if feed not found

        Raises:
            RuntimeError: If requests module is not available
        """
        if requests is None:
            raise RuntimeError("requests module not available")

        feed_name = self._get_feed_name(feed)
        url = f"{self._base_url}/{self._username}/feeds/{feed_name}/data/last"

        response = requests.get(url, headers=self._get_headers())

        if response.status_code == 404:
            return None

        return response.json()["value"]

    def fetch_history(self, feed, hours, resolution=6):
        """
        Fetch historical values from a feed.

        Args:
            feed: Feed name (string)
            hours: Number of hours to look back
            resolution: Data point interval in minutes (default: 6)

        Returns:
            List of values in chronological order

        Raises:
            RuntimeError: If requests module is not available
        """
        if requests is None:
            raise RuntimeError("requests module not available")

        feed_name = self._get_feed_name(feed)
        url = f"{self._base_url}/{self._username}/feeds/{feed_name}/data/chart"

        params = {"hours": hours, "resolution": resolution}
        response = requests.get(url, headers=self._get_headers(), params=params)

        if response.status_code == 404:
            return []

        data = response.json().get("data", [])
        # Chart endpoint returns [timestamp, value] pairs
        return [item[1] for item in data]

    def sync_time(self):
        """
        Get current time from the backend.

        Returns:
            datetime object representing current time

        Raises:
            RuntimeError: If requests or datetime module is not available
        """
        if requests is None:
            raise RuntimeError("requests module not available")

        if datetime is None:
            raise RuntimeError("datetime module not available")

        url = f"{self._base_url}/{self._username}/integrations/time/struct"
        response = requests.get(url, headers=self._get_headers())

        data = response.json()

        return datetime(
            year=data["year"],
            month=data["mon"],
            day=data["mday"],
            hour=data["hour"],
            minute=data["min"],
            second=data["sec"],
        )
