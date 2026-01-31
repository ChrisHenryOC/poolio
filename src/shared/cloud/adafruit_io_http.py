# Adafruit IO HTTP client for cloud backend
# CircuitPython compatible (no dataclasses, no type annotations in signatures)

from .base import CloudBackend

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

# HTTP timeout in seconds per NFR-REL-005
HTTP_TIMEOUT = 10


class AdafruitIOHTTP(CloudBackend):
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
        super().__init__(environment)
        self._username = username
        self._api_key = api_key
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

    def _get_headers(self):
        """
        Get headers for API requests.

        Returns:
            Dictionary of HTTP headers
        """
        return {"X-AIO-Key": self._api_key}

    def _require_requests(self):
        """
        Raise RuntimeError if requests module is not available.

        Used to validate module availability before HTTP operations.
        """
        if requests is None:
            raise RuntimeError("requests module not available")

    def publish(self, feed, value, qos=0):
        """
        Publish a value to a feed.

        Args:
            feed: Feed name (string)
            value: Value to publish (any type)
            qos: Quality of Service level (ignored by HTTP, included for interface)

        Returns:
            True on success

        Raises:
            RuntimeError: If requests module is not available or HTTP error
        """
        # Note: qos parameter is accepted for interface compatibility
        # but is not meaningful for HTTP (no QoS concept)
        self._require_requests()

        feed_name = self._get_feed_name(feed)
        url = f"{self._base_url}/{self._username}/feeds/{feed_name}/data"

        response = requests.post(
            url, headers=self._get_headers(), json={"value": value}, timeout=HTTP_TIMEOUT
        )
        try:
            if response.status_code >= 400:
                raise RuntimeError(f"HTTP {response.status_code} from Adafruit IO")
            return True
        finally:
            response.close()

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
            Most recent value or None if feed not found or missing value

        Raises:
            RuntimeError: If requests module is not available or HTTP error
        """
        self._require_requests()

        feed_name = self._get_feed_name(feed)
        url = f"{self._base_url}/{self._username}/feeds/{feed_name}/data/last"

        response = requests.get(url, headers=self._get_headers(), timeout=HTTP_TIMEOUT)
        try:
            if response.status_code == 404:
                return None
            if response.status_code >= 400:
                raise RuntimeError(f"HTTP {response.status_code} from Adafruit IO")

            data = response.json()
            if "value" not in data:
                return None
            return data["value"]
        finally:
            response.close()

    def fetch_history(self, feed, hours, resolution=6):
        """
        Fetch historical values from a feed.

        Uses Adafruit IO chart endpoint which aggregates data at the specified
        resolution. Values are averages over each interval, not raw data points.

        Args:
            feed: Feed name (string)
            hours: Number of hours to look back
            resolution: Data point interval in minutes (default: 6)

        Returns:
            List of averaged values at resolution-minute intervals, in
            chronological order. Empty list if feed not found.

        Raises:
            RuntimeError: If requests module is not available or HTTP error
        """
        self._require_requests()

        feed_name = self._get_feed_name(feed)
        url = f"{self._base_url}/{self._username}/feeds/{feed_name}/data/chart"

        params = {"hours": hours, "resolution": resolution}
        response = requests.get(
            url, headers=self._get_headers(), params=params, timeout=HTTP_TIMEOUT
        )
        try:
            if response.status_code == 404:
                return []
            if response.status_code >= 400:
                raise RuntimeError(f"HTTP {response.status_code} from Adafruit IO")

            data = response.json().get("data", [])
            try:
                return [item[1] for item in data]
            except (IndexError, TypeError):
                return []
        finally:
            response.close()

    def sync_time(self):
        """
        Get current time from the backend.

        Returns:
            datetime object representing current time

        Raises:
            RuntimeError: If requests or datetime module is not available,
                HTTP error, or response missing required time fields
        """
        self._require_requests()

        if datetime is None:
            raise RuntimeError("datetime module not available")

        url = f"{self._base_url}/{self._username}/integrations/time/struct"
        response = requests.get(url, headers=self._get_headers(), timeout=HTTP_TIMEOUT)
        try:
            if response.status_code >= 400:
                raise RuntimeError(f"HTTP {response.status_code} from Adafruit IO")

            data = response.json()

            required_fields = ["year", "mon", "mday", "hour", "min", "sec"]
            for field in required_fields:
                if field not in data:
                    raise RuntimeError(f"Missing time field '{field}' in response")

            return datetime(
                year=data["year"],
                month=data["mon"],
                day=data["mday"],
                hour=data["hour"],
                minute=data["min"],
                second=data["sec"],
            )
        finally:
            response.close()
