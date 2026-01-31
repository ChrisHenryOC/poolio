# Tests for AdafruitIOMQTT cloud client

from unittest.mock import MagicMock, patch

import pytest

from shared.cloud import CloudBackend


class TestAdafruitIOMQTTImport:
    """Test AdafruitIOMQTT can be imported."""

    def test_adafruitiomqtt_can_be_imported(self) -> None:
        """AdafruitIOMQTT can be imported from shared.cloud."""
        from shared.cloud import AdafruitIOMQTT

        assert AdafruitIOMQTT is not None


class TestAdafruitIOMQTTInheritance:
    """Test AdafruitIOMQTT extends CloudBackend."""

    def test_adafruitiomqtt_is_subclass_of_cloudbackend(self) -> None:
        """AdafruitIOMQTT is a subclass of CloudBackend."""
        from shared.cloud import AdafruitIOMQTT

        assert issubclass(AdafruitIOMQTT, CloudBackend)

    def test_adafruitiomqtt_instance_is_cloudbackend(self) -> None:
        """AdafruitIOMQTT instance is also a CloudBackend instance."""
        from shared.cloud import AdafruitIOMQTT

        client = AdafruitIOMQTT("testuser", "test_api_key")
        assert isinstance(client, CloudBackend)


class TestAdafruitIOMQTTInitialization:
    """Test AdafruitIOMQTT initialization."""

    def test_stores_username(self) -> None:
        """Constructor stores username."""
        from shared.cloud import AdafruitIOMQTT

        client = AdafruitIOMQTT("testuser", "test_api_key")
        assert client._username == "testuser"

    def test_stores_api_key(self) -> None:
        """Constructor stores API key."""
        from shared.cloud import AdafruitIOMQTT

        client = AdafruitIOMQTT("testuser", "test_api_key")
        assert client._api_key == "test_api_key"

    def test_default_environment_is_prod(self) -> None:
        """Default environment is prod."""
        from shared.cloud import AdafruitIOMQTT

        client = AdafruitIOMQTT("testuser", "test_api_key")
        assert client._environment == "prod"

    def test_custom_environment(self) -> None:
        """Can set custom environment."""
        from shared.cloud import AdafruitIOMQTT

        client = AdafruitIOMQTT("testuser", "test_api_key", environment="nonprod")
        assert client._environment == "nonprod"

    def test_starts_disconnected(self) -> None:
        """Client starts in disconnected state."""
        from shared.cloud import AdafruitIOMQTT

        client = AdafruitIOMQTT("testuser", "test_api_key")
        assert client.is_connected is False

    def test_has_internal_http_client(self) -> None:
        """Client has internal HTTP client for fallback operations."""
        from shared.cloud import AdafruitIOMQTT

        client = AdafruitIOMQTT("testuser", "test_api_key")
        assert client._http is not None


class TestAdafruitIOMQTTFeedNamePrefix:
    """Test environment-based feed name prefixing."""

    def test_prod_environment_no_prefix(self) -> None:
        """Prod environment uses no prefix."""
        from shared.cloud import AdafruitIOMQTT

        client = AdafruitIOMQTT("testuser", "test_api_key", environment="prod")
        assert client._get_feed_name("pooltemp") == "pooltemp"

    def test_nonprod_environment_adds_prefix(self) -> None:
        """Nonprod environment adds prefix."""
        from shared.cloud import AdafruitIOMQTT

        client = AdafruitIOMQTT("testuser", "test_api_key", environment="nonprod")
        assert client._get_feed_name("pooltemp") == "nonprod-pooltemp"


class TestAdafruitIOMQTTConnectDisconnect:
    """Test connect/disconnect behavior."""

    @patch("shared.cloud.adafruit_io_mqtt.MQTT")
    def test_connect_creates_mqtt_client(self, mock_mqtt_class: MagicMock) -> None:
        """connect() creates MQTT client and connects."""
        from shared.cloud import AdafruitIOMQTT

        mock_mqtt = MagicMock()
        mock_mqtt_class.return_value = mock_mqtt

        client = AdafruitIOMQTT("testuser", "test_api_key")
        client.connect()

        mock_mqtt.connect.assert_called_once()
        assert client.is_connected is True

    @patch("shared.cloud.adafruit_io_mqtt.MQTT")
    def test_disconnect_closes_mqtt_connection(self, mock_mqtt_class: MagicMock) -> None:
        """disconnect() closes MQTT connection."""
        from shared.cloud import AdafruitIOMQTT

        mock_mqtt = MagicMock()
        mock_mqtt_class.return_value = mock_mqtt

        client = AdafruitIOMQTT("testuser", "test_api_key")
        client.connect()
        client.disconnect()

        mock_mqtt.disconnect.assert_called_once()
        assert client.is_connected is False

    @patch("shared.cloud.adafruit_io_mqtt.MQTT")
    def test_multiple_connects_allowed(self, mock_mqtt_class: MagicMock) -> None:
        """Can call connect() multiple times without error."""
        from shared.cloud import AdafruitIOMQTT

        mock_mqtt = MagicMock()
        mock_mqtt_class.return_value = mock_mqtt

        client = AdafruitIOMQTT("testuser", "test_api_key")
        client.connect()
        client.connect()  # Should not raise
        assert client.is_connected is True

    @patch("shared.cloud.adafruit_io_mqtt.MQTT")
    def test_disconnect_when_not_connected_is_safe(self, mock_mqtt_class: MagicMock) -> None:
        """disconnect() is safe when not connected."""
        from shared.cloud import AdafruitIOMQTT

        client = AdafruitIOMQTT("testuser", "test_api_key")
        client.disconnect()  # Should not raise
        assert client.is_connected is False


class TestAdafruitIOMQTTPublish:
    """Test publish() functionality."""

    @patch("shared.cloud.adafruit_io_mqtt.MQTT")
    def test_publish_sends_mqtt_message(self, mock_mqtt_class: MagicMock) -> None:
        """publish() sends message via MQTT."""
        from shared.cloud import AdafruitIOMQTT

        mock_mqtt = MagicMock()
        mock_mqtt_class.return_value = mock_mqtt

        client = AdafruitIOMQTT("testuser", "test_api_key")
        client.connect()
        result = client.publish("pooltemp", "72.5")

        mock_mqtt.publish.assert_called_once()
        assert result is True

    @patch("shared.cloud.adafruit_io_mqtt.MQTT")
    def test_publish_uses_correct_topic(self, mock_mqtt_class: MagicMock) -> None:
        """publish() uses correct MQTT topic format."""
        from shared.cloud import AdafruitIOMQTT

        mock_mqtt = MagicMock()
        mock_mqtt_class.return_value = mock_mqtt

        client = AdafruitIOMQTT("testuser", "test_api_key")
        client.connect()
        client.publish("pooltemp", "72.5")

        call_args = mock_mqtt.publish.call_args
        topic = call_args[0][0]
        assert topic == "testuser/feeds/pooltemp"

    @patch("shared.cloud.adafruit_io_mqtt.MQTT")
    def test_publish_applies_environment_prefix(self, mock_mqtt_class: MagicMock) -> None:
        """publish() applies environment prefix to feed name."""
        from shared.cloud import AdafruitIOMQTT

        mock_mqtt = MagicMock()
        mock_mqtt_class.return_value = mock_mqtt

        client = AdafruitIOMQTT("testuser", "test_api_key", environment="nonprod")
        client.connect()
        client.publish("pooltemp", "72.5")

        call_args = mock_mqtt.publish.call_args
        topic = call_args[0][0]
        assert topic == "testuser/feeds/nonprod-pooltemp"

    @patch("shared.cloud.adafruit_io_mqtt.MQTT")
    def test_publish_accepts_qos_parameter(self, mock_mqtt_class: MagicMock) -> None:
        """publish() accepts qos parameter."""
        from shared.cloud import AdafruitIOMQTT

        mock_mqtt = MagicMock()
        mock_mqtt_class.return_value = mock_mqtt

        client = AdafruitIOMQTT("testuser", "test_api_key")
        client.connect()
        client.publish("pooltemp", "72.5", qos=1)

        call_args = mock_mqtt.publish.call_args
        assert call_args[1]["qos"] == 1

    @patch("shared.cloud.adafruit_io_mqtt.MQTT")
    def test_publish_raises_when_not_connected(self, mock_mqtt_class: MagicMock) -> None:
        """publish() raises RuntimeError when not connected."""
        from shared.cloud import AdafruitIOMQTT

        client = AdafruitIOMQTT("testuser", "test_api_key")
        with pytest.raises(RuntimeError, match="Not connected"):
            client.publish("pooltemp", "72.5")


class TestAdafruitIOMQTTSubscribe:
    """Test subscribe() functionality."""

    @patch("shared.cloud.adafruit_io_mqtt.MQTT")
    def test_subscribe_registers_callback(self, mock_mqtt_class: MagicMock) -> None:
        """subscribe() registers callback for feed."""
        from shared.cloud import AdafruitIOMQTT

        mock_mqtt = MagicMock()
        mock_mqtt_class.return_value = mock_mqtt

        client = AdafruitIOMQTT("testuser", "test_api_key")
        client.connect()

        callback = MagicMock()
        client.subscribe("pooltemp", callback)

        mock_mqtt.subscribe.assert_called()

    @patch("shared.cloud.adafruit_io_mqtt.MQTT")
    def test_subscribe_uses_correct_topic(self, mock_mqtt_class: MagicMock) -> None:
        """subscribe() uses correct MQTT topic format."""
        from shared.cloud import AdafruitIOMQTT

        mock_mqtt = MagicMock()
        mock_mqtt_class.return_value = mock_mqtt

        client = AdafruitIOMQTT("testuser", "test_api_key")
        client.connect()

        callback = MagicMock()
        client.subscribe("pooltemp", callback)

        call_args = mock_mqtt.subscribe.call_args
        topic = call_args[0][0]
        assert topic == "testuser/feeds/pooltemp"

    def test_subscribe_raises_when_not_connected(self) -> None:
        """subscribe() raises RuntimeError when not connected."""
        from shared.cloud import AdafruitIOMQTT

        client = AdafruitIOMQTT("testuser", "test_api_key")
        with pytest.raises(RuntimeError, match="Not connected"):
            client.subscribe("pooltemp", lambda f, v: None)


class TestAdafruitIOMQTTThrottle:
    """Test throttle handling."""

    def test_subscribe_throttle_raises_when_not_connected(self) -> None:
        """subscribe_throttle() raises RuntimeError when not connected."""
        from shared.cloud import AdafruitIOMQTT

        client = AdafruitIOMQTT("testuser", "test_api_key")
        with pytest.raises(RuntimeError, match="Not connected"):
            client.subscribe_throttle()

    @patch("shared.cloud.adafruit_io_mqtt.MQTT")
    def test_subscribe_throttle_subscribes_to_throttle_topic(
        self, mock_mqtt_class: MagicMock
    ) -> None:
        """subscribe_throttle() subscribes to throttle topic."""
        from shared.cloud import AdafruitIOMQTT

        mock_mqtt = MagicMock()
        mock_mqtt_class.return_value = mock_mqtt

        client = AdafruitIOMQTT("testuser", "test_api_key")
        client.connect()
        client.subscribe_throttle()

        # Check that subscribe was called with throttle topic
        mock_mqtt.subscribe.assert_called()
        call_args = mock_mqtt.subscribe.call_args_list
        throttle_call = [c for c in call_args if "throttle" in str(c)]
        assert len(throttle_call) >= 1

    @patch("shared.cloud.adafruit_io_mqtt.time")
    @patch("shared.cloud.adafruit_io_mqtt.MQTT")
    def test_publish_returns_false_when_throttled(
        self, mock_mqtt_class: MagicMock, mock_time: MagicMock
    ) -> None:
        """publish() returns False when throttled."""
        from shared.cloud import AdafruitIOMQTT

        mock_mqtt = MagicMock()
        mock_mqtt_class.return_value = mock_mqtt
        mock_time.time.return_value = 1000

        client = AdafruitIOMQTT("testuser", "test_api_key")
        client.connect()

        # Simulate throttle (set throttle_until in the future)
        client._throttle_until = 1060  # 60 seconds from now

        result = client.publish("pooltemp", "72.5")
        assert result is False

    @patch("shared.cloud.adafruit_io_mqtt.time")
    @patch("shared.cloud.adafruit_io_mqtt.MQTT")
    def test_throttle_backoff_increases_exponentially(
        self, mock_mqtt_class: MagicMock, mock_time: MagicMock
    ) -> None:
        """Throttle backoff increases exponentially."""
        from shared.cloud import AdafruitIOMQTT

        mock_mqtt = MagicMock()
        mock_mqtt_class.return_value = mock_mqtt
        mock_time.time.return_value = 1000

        client = AdafruitIOMQTT("testuser", "test_api_key")
        client.connect()

        # First throttle: 60 seconds
        client._handle_throttle("testuser/throttle", "throttle")
        assert client._throttle_until == 1060

        # Second throttle: 120 seconds
        mock_time.time.return_value = 1100
        client._handle_throttle("testuser/throttle", "throttle")
        assert client._throttle_until == 1220  # 1100 + 120

        # Third throttle: 240 seconds
        mock_time.time.return_value = 1300
        client._handle_throttle("testuser/throttle", "throttle")
        assert client._throttle_until == 1540  # 1300 + 240

        # Fourth throttle: max 300 seconds
        mock_time.time.return_value = 1600
        client._handle_throttle("testuser/throttle", "throttle")
        assert client._throttle_until == 1900  # 1600 + 300

        # Fifth throttle: still max 300 seconds
        mock_time.time.return_value = 2000
        client._handle_throttle("testuser/throttle", "throttle")
        assert client._throttle_until == 2300  # 2000 + 300


class TestAdafruitIOMQTTOnMessage:
    """Test _on_message callback routing."""

    @patch("shared.cloud.adafruit_io_mqtt.MQTT")
    def test_on_message_routes_to_subscriber_callback(self, mock_mqtt_class: MagicMock) -> None:
        """_on_message routes incoming messages to registered callbacks."""
        from shared.cloud import AdafruitIOMQTT

        mock_mqtt = MagicMock()
        mock_mqtt_class.return_value = mock_mqtt

        client = AdafruitIOMQTT("testuser", "test_api_key")
        client.connect()

        received = []
        client.subscribe("pooltemp", lambda f, v: received.append((f, v)))

        # Simulate message receipt
        client._on_message(None, "testuser/feeds/pooltemp", "72.5")

        assert received == [("pooltemp", "72.5")]

    @patch("shared.cloud.adafruit_io_mqtt.MQTT")
    def test_on_message_strips_environment_prefix(self, mock_mqtt_class: MagicMock) -> None:
        """_on_message strips environment prefix from incoming messages."""
        from shared.cloud import AdafruitIOMQTT

        mock_mqtt = MagicMock()
        mock_mqtt_class.return_value = mock_mqtt

        client = AdafruitIOMQTT("testuser", "test_api_key", environment="nonprod")
        client.connect()

        received = []
        client.subscribe("pooltemp", lambda f, v: received.append((f, v)))

        # Simulate message with environment prefix in topic
        client._on_message(None, "testuser/feeds/nonprod-pooltemp", "72.5")

        # Callback should receive logical feed name without prefix
        assert received == [("pooltemp", "72.5")]

    @patch("shared.cloud.adafruit_io_mqtt.MQTT")
    def test_on_message_callback_error_does_not_crash(self, mock_mqtt_class: MagicMock) -> None:
        """_on_message catches callback errors without crashing."""
        from shared.cloud import AdafruitIOMQTT

        mock_mqtt = MagicMock()
        mock_mqtt_class.return_value = mock_mqtt

        client = AdafruitIOMQTT("testuser", "test_api_key")
        client.connect()

        def bad_callback(f, v):
            raise ValueError("Callback error")

        client.subscribe("pooltemp", bad_callback)

        # Should not raise
        client._on_message(None, "testuser/feeds/pooltemp", "72.5")

    @patch("shared.cloud.adafruit_io_mqtt.MQTT")
    def test_on_message_ignores_malformed_topics(self, mock_mqtt_class: MagicMock) -> None:
        """_on_message ignores topics that don't match expected format."""
        from shared.cloud import AdafruitIOMQTT

        mock_mqtt = MagicMock()
        mock_mqtt_class.return_value = mock_mqtt

        client = AdafruitIOMQTT("testuser", "test_api_key")
        client.connect()

        received = []
        client.subscribe("pooltemp", lambda f, v: received.append((f, v)))

        # Topic without /feeds/ segment should be ignored
        client._on_message(None, "testuser/other/pooltemp", "72.5")

        assert received == []

    @patch("shared.cloud.adafruit_io_mqtt.time")
    @patch("shared.cloud.adafruit_io_mqtt.MQTT")
    def test_on_message_routes_throttle_to_handler(
        self, mock_mqtt_class: MagicMock, mock_time: MagicMock
    ) -> None:
        """_on_message routes throttle messages to _handle_throttle."""
        from shared.cloud import AdafruitIOMQTT

        mock_mqtt = MagicMock()
        mock_mqtt_class.return_value = mock_mqtt
        mock_time.time.return_value = 1000

        client = AdafruitIOMQTT("testuser", "test_api_key")
        client.connect()

        # Simulate throttle message
        client._on_message(None, "testuser/throttle", "rate limited")

        # Throttle should have been applied
        assert client._throttle_until == 1060  # 1000 + 60


class TestAdafruitIOMQTTHTTPFallback:
    """Test HTTP fallback for fetch operations."""

    @patch("shared.cloud.adafruit_io_http.requests")
    def test_fetch_latest_uses_http(self, mock_requests: MagicMock) -> None:
        """fetch_latest() delegates to HTTP client."""
        from shared.cloud import AdafruitIOMQTT

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"value": "72.5"}
        mock_requests.get.return_value = mock_response

        client = AdafruitIOMQTT("testuser", "test_api_key")
        result = client.fetch_latest("pooltemp")

        assert result == "72.5"
        mock_requests.get.assert_called_once()

    @patch("shared.cloud.adafruit_io_http.requests")
    def test_fetch_history_uses_http(self, mock_requests: MagicMock) -> None:
        """fetch_history() delegates to HTTP client."""
        from shared.cloud import AdafruitIOMQTT

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [["2024-01-01T00:00:00Z", "72.5"], ["2024-01-01T00:06:00Z", "73.0"]]
        }
        mock_requests.get.return_value = mock_response

        client = AdafruitIOMQTT("testuser", "test_api_key")
        result = client.fetch_history("pooltemp", hours=24)

        assert result == ["72.5", "73.0"]
        mock_requests.get.assert_called_once()

    @patch("shared.cloud.adafruit_io_http.requests")
    def test_sync_time_uses_http(self, mock_requests: MagicMock) -> None:
        """sync_time() delegates to HTTP client."""
        from shared.cloud import AdafruitIOMQTT

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "year": 2024,
            "mon": 1,
            "mday": 15,
            "hour": 10,
            "min": 30,
            "sec": 45,
        }
        mock_requests.get.return_value = mock_response

        client = AdafruitIOMQTT("testuser", "test_api_key")
        result = client.sync_time()

        assert result.year == 2024
        mock_requests.get.assert_called_once()
