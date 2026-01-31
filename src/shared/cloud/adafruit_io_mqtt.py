# Adafruit IO MQTT client for cloud backend
# CircuitPython compatible (no dataclasses, no type annotations in signatures)

import time

from .adafruit_io_http import AdafruitIOHTTP
from .base import CloudBackend

# Import MQTT with fallback for testing without CircuitPython
try:
    from adafruit_minimqtt.adafruit_minimqtt import MQTT
except ImportError:
    MQTT = None

# Throttle backoff schedule in seconds
# First throttle: 60s, then 120s, 240s, max 300s
THROTTLE_BACKOFF = [60, 120, 240, 300]

# Adafruit IO MQTT broker settings
ADAFRUIT_IO_BROKER = "io.adafruit.com"
ADAFRUIT_IO_PORT = 8883  # TLS


class AdafruitIOMQTT(CloudBackend):
    """
    MQTT client for Adafruit IO cloud backend.

    Implements the CloudBackend pattern using MQTT for publish/subscribe
    and HTTP fallback for fetch operations (fetch_latest, fetch_history, sync_time).

    Supports throttle handling with exponential backoff.

    Attributes:
        _username: Adafruit IO username
        _api_key: Adafruit IO API key
        _environment: Environment name (prod, nonprod, dev, test)
        _connected: Boolean indicating connection state
        _mqtt: MQTT client instance (None until connect())
        _http: HTTP client for fallback operations
        _subscribers: Dictionary mapping feeds to callbacks
        _throttle_until: Timestamp when throttle ends
        _throttle_count: Number of consecutive throttles (for backoff)
    """

    def __init__(self, username, api_key, environment="prod", socket_pool=None, ssl_context=None):
        """
        Initialize AdafruitIOMQTT client.

        Args:
            username: Adafruit IO username
            api_key: Adafruit IO API key
            environment: Environment name (default: prod)
            socket_pool: Socket pool for CircuitPython (optional)
            ssl_context: SSL context for TLS (optional)
        """
        self._username = username
        self._api_key = api_key
        self._environment = environment
        self._socket_pool = socket_pool
        self._ssl_context = ssl_context
        self._connected = False
        self._mqtt = None
        self._http = AdafruitIOHTTP(username, api_key, environment)
        self._subscribers = {}
        self._throttle_until = 0
        self._throttle_count = 0

    def connect(self):
        """
        Connect to Adafruit IO MQTT broker.

        Establishes TLS connection to io.adafruit.com:8883.
        Can be called multiple times without error.
        """
        if self._connected:
            return

        if MQTT is None:
            raise RuntimeError("adafruit_minimqtt module not available")

        # Create MQTT client
        self._mqtt = MQTT(
            broker=ADAFRUIT_IO_BROKER,
            port=ADAFRUIT_IO_PORT,
            username=self._username,
            password=self._api_key,
            socket_pool=self._socket_pool,
            ssl_context=self._ssl_context,
            is_ssl=True,
        )

        # Set up message callback
        self._mqtt.on_message = self._on_message

        # Connect to broker
        self._mqtt.connect()
        self._connected = True

    def disconnect(self):
        """
        Disconnect from Adafruit IO MQTT broker.

        Cleanly closes connection. Can be called multiple times without error.
        """
        if not self._connected or self._mqtt is None:
            self._connected = False
            return

        try:
            self._mqtt.disconnect()
        except Exception:
            pass  # Ignore disconnect errors
        finally:
            self._connected = False
            self._mqtt = None

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

    def _get_topic(self, feed):
        """
        Get MQTT topic for a feed.

        Args:
            feed: Logical feed name

        Returns:
            MQTT topic in format: username/feeds/feed_name
        """
        feed_name = self._get_feed_name(feed)
        return f"{self._username}/feeds/{feed_name}"

    def publish(self, feed, value, qos=0):
        """
        Publish a value to a feed.

        Args:
            feed: Feed name (string)
            value: Value to publish (any type)
            qos: Quality of Service level (0 or 1, default: 0)

        Returns:
            True if published successfully, False if throttled

        Raises:
            RuntimeError: If not connected
        """
        if not self._connected or self._mqtt is None:
            raise RuntimeError("Not connected to MQTT broker")

        # Check if throttled
        if time.time() < self._throttle_until:
            return False

        topic = self._get_topic(feed)
        self._mqtt.publish(topic, str(value), qos=qos)
        return True

    def subscribe(self, feed, callback):
        """
        Subscribe to a feed with a callback.

        Args:
            feed: Feed name to subscribe to (string)
            callback: Function called with (feed, value) on message

        Raises:
            RuntimeError: If not connected
        """
        if not self._connected or self._mqtt is None:
            raise RuntimeError("Not connected to MQTT broker")

        topic = self._get_topic(feed)

        # Store callback for this feed
        if feed not in self._subscribers:
            self._subscribers[feed] = []
        self._subscribers[feed].append(callback)

        # Subscribe to MQTT topic
        self._mqtt.subscribe(topic)

    def subscribe_throttle(self, callback=None):
        """
        Subscribe to the throttle topic.

        Adafruit IO sends throttle messages when rate limit is exceeded.
        This method automatically handles throttle messages with exponential backoff.

        Args:
            callback: Optional callback for throttle notifications (feed, message)
        """
        if not self._connected or self._mqtt is None:
            raise RuntimeError("Not connected to MQTT broker")

        throttle_topic = f"{self._username}/throttle"

        # Store throttle callback if provided
        if callback:
            if "throttle" not in self._subscribers:
                self._subscribers["throttle"] = []
            self._subscribers["throttle"].append(callback)

        # Subscribe to throttle topic
        self._mqtt.subscribe(throttle_topic)

    def _handle_throttle(self, topic, message):
        """
        Handle throttle message from Adafruit IO.

        Implements exponential backoff: 60s, 120s, 240s, max 300s.

        Args:
            topic: MQTT topic (ignored)
            message: Throttle message (ignored)
        """
        # Calculate backoff based on consecutive throttle count
        backoff_index = min(self._throttle_count, len(THROTTLE_BACKOFF) - 1)
        backoff_seconds = THROTTLE_BACKOFF[backoff_index]

        self._throttle_until = time.time() + backoff_seconds
        self._throttle_count += 1

        # Notify throttle callbacks
        if "throttle" in self._subscribers:
            for callback in self._subscribers["throttle"]:
                try:
                    callback("throttle", message)
                except Exception:
                    pass  # Don't let callback errors affect throttle handling

    def _on_message(self, client, topic, message):
        """
        Handle incoming MQTT message.

        Routes message to appropriate callback based on topic.

        Args:
            client: MQTT client (unused)
            topic: MQTT topic string
            message: Message payload
        """
        # Check if this is a throttle message
        if topic.endswith("/throttle"):
            self._handle_throttle(topic, message)
            return

        # Extract feed name from topic (format: username/feeds/feed_name)
        parts = topic.split("/")
        if len(parts) >= 3 and parts[1] == "feeds":
            feed_name = "/".join(parts[2:])  # Handle nested feed names

            # Find the logical feed name (remove environment prefix if present)
            logical_feed = feed_name
            if self._environment != "prod" and feed_name.startswith(f"{self._environment}-"):
                logical_feed = feed_name[len(self._environment) + 1 :]

            # Call registered callbacks
            if logical_feed in self._subscribers:
                for callback in self._subscribers[logical_feed]:
                    try:
                        callback(logical_feed, message)
                    except Exception:
                        pass  # Don't let callback errors crash the client

    def fetch_latest(self, feed):
        """
        Fetch the most recent value from a feed.

        Delegates to HTTP client (MQTT doesn't support request/response).

        Args:
            feed: Feed name (string)

        Returns:
            Most recent value or None if feed not found
        """
        return self._http.fetch_latest(feed)

    def fetch_history(self, feed, hours, resolution=6):
        """
        Fetch historical values from a feed.

        Delegates to HTTP client (MQTT doesn't support request/response).

        Args:
            feed: Feed name (string)
            hours: Number of hours to look back
            resolution: Data point interval in minutes (default: 6)

        Returns:
            List of values in chronological order
        """
        return self._http.fetch_history(feed, hours, resolution)

    def sync_time(self):
        """
        Get current time from the backend.

        Delegates to HTTP client (MQTT doesn't support request/response).

        Returns:
            datetime object representing current time

        Raises:
            RuntimeError: If time sync fails
        """
        return self._http.sync_time()
