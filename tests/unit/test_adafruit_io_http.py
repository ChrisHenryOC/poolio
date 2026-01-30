# Tests for AdafruitIOHTTP cloud client

from unittest.mock import MagicMock, patch

import pytest

from shared.cloud import AdafruitIOHTTP


class TestAdafruitIOHTTPInitialization:
    """Test AdafruitIOHTTP initialization."""

    def test_stores_username(self) -> None:
        """Constructor stores username."""
        client = AdafruitIOHTTP("testuser", "test_api_key")
        assert client._username == "testuser"

    def test_stores_api_key(self) -> None:
        """Constructor stores API key."""
        client = AdafruitIOHTTP("testuser", "test_api_key")
        assert client._api_key == "test_api_key"

    def test_default_environment_is_prod(self) -> None:
        """Default environment is prod."""
        client = AdafruitIOHTTP("testuser", "test_api_key")
        assert client._environment == "prod"

    def test_custom_environment(self) -> None:
        """Can set custom environment."""
        client = AdafruitIOHTTP("testuser", "test_api_key", environment="nonprod")
        assert client._environment == "nonprod"

    def test_starts_disconnected(self) -> None:
        """Client starts in disconnected state."""
        client = AdafruitIOHTTP("testuser", "test_api_key")
        assert client.is_connected is False


class TestAdafruitIOHTTPFeedNamePrefix:
    """Test environment-based feed name prefixing (NFR-ENV-002)."""

    def test_prod_environment_no_prefix(self) -> None:
        """Prod environment uses no prefix."""
        client = AdafruitIOHTTP("testuser", "test_api_key", environment="prod")
        assert client._get_feed_name("pooltemp") == "pooltemp"

    def test_nonprod_environment_adds_prefix(self) -> None:
        """Nonprod environment adds prefix."""
        client = AdafruitIOHTTP("testuser", "test_api_key", environment="nonprod")
        assert client._get_feed_name("pooltemp") == "nonprod-pooltemp"

    def test_dev_environment_adds_prefix(self) -> None:
        """Dev environment adds prefix."""
        client = AdafruitIOHTTP("testuser", "test_api_key", environment="dev")
        assert client._get_feed_name("pooltemp") == "dev-pooltemp"

    def test_test_environment_adds_prefix(self) -> None:
        """Test environment adds prefix."""
        client = AdafruitIOHTTP("testuser", "test_api_key", environment="test")
        assert client._get_feed_name("waterlevel") == "test-waterlevel"


class TestAdafruitIOHTTPConnectDisconnect:
    """Test connect/disconnect behavior."""

    def test_connect_sets_connected_state(self) -> None:
        """connect() sets connected state to True."""
        client = AdafruitIOHTTP("testuser", "test_api_key")
        client.connect()
        assert client.is_connected is True

    def test_disconnect_clears_connected_state(self) -> None:
        """disconnect() sets connected state to False."""
        client = AdafruitIOHTTP("testuser", "test_api_key")
        client.connect()
        client.disconnect()
        assert client.is_connected is False

    def test_multiple_connects_allowed(self) -> None:
        """Can call connect() multiple times."""
        client = AdafruitIOHTTP("testuser", "test_api_key")
        client.connect()
        client.connect()
        assert client.is_connected is True

    def test_multiple_disconnects_allowed(self) -> None:
        """Can call disconnect() multiple times."""
        client = AdafruitIOHTTP("testuser", "test_api_key")
        client.disconnect()
        client.disconnect()
        assert client.is_connected is False


class TestAdafruitIOHTTPSubscribe:
    """Test subscribe() raises NotImplementedError."""

    def test_subscribe_raises_not_implemented(self) -> None:
        """subscribe() raises NotImplementedError for HTTP client."""
        client = AdafruitIOHTTP("testuser", "test_api_key")
        with pytest.raises(NotImplementedError, match="HTTP client does not support"):
            client.subscribe("pooltemp", lambda f, v: None)


class TestAdafruitIOHTTPPublish:
    """Test publish() functionality."""

    @patch("shared.cloud.adafruit_io_http.requests")
    def test_publish_makes_post_request(self, mock_requests: MagicMock) -> None:
        """publish() makes POST request to correct URL."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_requests.post.return_value = mock_response

        client = AdafruitIOHTTP("testuser", "test_api_key")
        client.publish("pooltemp", 72.5)

        mock_requests.post.assert_called_once()
        call_args = mock_requests.post.call_args
        assert "testuser/feeds/pooltemp/data" in call_args[0][0]

    @patch("shared.cloud.adafruit_io_http.requests")
    def test_publish_includes_api_key_header(self, mock_requests: MagicMock) -> None:
        """publish() includes X-AIO-Key header."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_requests.post.return_value = mock_response

        client = AdafruitIOHTTP("testuser", "test_api_key")
        client.publish("pooltemp", 72.5)

        call_args = mock_requests.post.call_args
        headers = call_args[1]["headers"]
        assert headers["X-AIO-Key"] == "test_api_key"

    @patch("shared.cloud.adafruit_io_http.requests")
    def test_publish_sends_value_in_body(self, mock_requests: MagicMock) -> None:
        """publish() sends value in JSON body."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_requests.post.return_value = mock_response

        client = AdafruitIOHTTP("testuser", "test_api_key")
        client.publish("pooltemp", 72.5)

        call_args = mock_requests.post.call_args
        json_data = call_args[1]["json"]
        assert json_data["value"] == 72.5

    @patch("shared.cloud.adafruit_io_http.requests")
    def test_publish_applies_environment_prefix(self, mock_requests: MagicMock) -> None:
        """publish() applies environment prefix to feed name."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_requests.post.return_value = mock_response

        client = AdafruitIOHTTP("testuser", "test_api_key", environment="nonprod")
        client.publish("pooltemp", 72.5)

        call_args = mock_requests.post.call_args
        assert "nonprod-pooltemp" in call_args[0][0]


class TestAdafruitIOHTTPFetchLatest:
    """Test fetch_latest() functionality."""

    @patch("shared.cloud.adafruit_io_http.requests")
    def test_fetch_latest_makes_get_request(self, mock_requests: MagicMock) -> None:
        """fetch_latest() makes GET request to correct URL."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"value": "72.5"}
        mock_requests.get.return_value = mock_response

        client = AdafruitIOHTTP("testuser", "test_api_key")
        client.fetch_latest("pooltemp")

        mock_requests.get.assert_called_once()
        call_args = mock_requests.get.call_args
        assert "testuser/feeds/pooltemp/data/last" in call_args[0][0]

    @patch("shared.cloud.adafruit_io_http.requests")
    def test_fetch_latest_includes_api_key_header(self, mock_requests: MagicMock) -> None:
        """fetch_latest() includes X-AIO-Key header."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"value": "72.5"}
        mock_requests.get.return_value = mock_response

        client = AdafruitIOHTTP("testuser", "test_api_key")
        client.fetch_latest("pooltemp")

        call_args = mock_requests.get.call_args
        headers = call_args[1]["headers"]
        assert headers["X-AIO-Key"] == "test_api_key"

    @patch("shared.cloud.adafruit_io_http.requests")
    def test_fetch_latest_returns_value(self, mock_requests: MagicMock) -> None:
        """fetch_latest() returns the value from response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"value": "72.5"}
        mock_requests.get.return_value = mock_response

        client = AdafruitIOHTTP("testuser", "test_api_key")
        result = client.fetch_latest("pooltemp")

        assert result == "72.5"

    @patch("shared.cloud.adafruit_io_http.requests")
    def test_fetch_latest_returns_none_on_404(self, mock_requests: MagicMock) -> None:
        """fetch_latest() returns None when feed not found."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_requests.get.return_value = mock_response

        client = AdafruitIOHTTP("testuser", "test_api_key")
        result = client.fetch_latest("unknown")

        assert result is None

    @patch("shared.cloud.adafruit_io_http.requests")
    def test_fetch_latest_applies_environment_prefix(self, mock_requests: MagicMock) -> None:
        """fetch_latest() applies environment prefix to feed name."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"value": "72.5"}
        mock_requests.get.return_value = mock_response

        client = AdafruitIOHTTP("testuser", "test_api_key", environment="nonprod")
        client.fetch_latest("pooltemp")

        call_args = mock_requests.get.call_args
        assert "nonprod-pooltemp" in call_args[0][0]


class TestAdafruitIOHTTPFetchHistory:
    """Test fetch_history() functionality."""

    @patch("shared.cloud.adafruit_io_http.requests")
    def test_fetch_history_makes_get_request(self, mock_requests: MagicMock) -> None:
        """fetch_history() makes GET request to chart endpoint."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": []}
        mock_requests.get.return_value = mock_response

        client = AdafruitIOHTTP("testuser", "test_api_key")
        client.fetch_history("pooltemp", hours=24)

        mock_requests.get.assert_called_once()
        call_args = mock_requests.get.call_args
        assert "testuser/feeds/pooltemp/data/chart" in call_args[0][0]

    @patch("shared.cloud.adafruit_io_http.requests")
    def test_fetch_history_includes_hours_param(self, mock_requests: MagicMock) -> None:
        """fetch_history() includes hours parameter."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": []}
        mock_requests.get.return_value = mock_response

        client = AdafruitIOHTTP("testuser", "test_api_key")
        client.fetch_history("pooltemp", hours=24)

        call_args = mock_requests.get.call_args
        params = call_args[1]["params"]
        assert params["hours"] == 24

    @patch("shared.cloud.adafruit_io_http.requests")
    def test_fetch_history_default_resolution(self, mock_requests: MagicMock) -> None:
        """fetch_history() uses default resolution of 6 minutes."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": []}
        mock_requests.get.return_value = mock_response

        client = AdafruitIOHTTP("testuser", "test_api_key")
        client.fetch_history("pooltemp", hours=24)

        call_args = mock_requests.get.call_args
        params = call_args[1]["params"]
        assert params["resolution"] == 6

    @patch("shared.cloud.adafruit_io_http.requests")
    def test_fetch_history_custom_resolution(self, mock_requests: MagicMock) -> None:
        """fetch_history() accepts custom resolution."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": []}
        mock_requests.get.return_value = mock_response

        client = AdafruitIOHTTP("testuser", "test_api_key")
        client.fetch_history("pooltemp", hours=24, resolution=30)

        call_args = mock_requests.get.call_args
        params = call_args[1]["params"]
        assert params["resolution"] == 30

    @patch("shared.cloud.adafruit_io_http.requests")
    def test_fetch_history_returns_values_list(self, mock_requests: MagicMock) -> None:
        """fetch_history() returns list of values from response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [["2024-01-01T00:00:00Z", "72.5"], ["2024-01-01T00:06:00Z", "73.0"]]
        }
        mock_requests.get.return_value = mock_response

        client = AdafruitIOHTTP("testuser", "test_api_key")
        result = client.fetch_history("pooltemp", hours=1)

        assert result == ["72.5", "73.0"]

    @patch("shared.cloud.adafruit_io_http.requests")
    def test_fetch_history_returns_empty_on_404(self, mock_requests: MagicMock) -> None:
        """fetch_history() returns empty list when feed not found."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_requests.get.return_value = mock_response

        client = AdafruitIOHTTP("testuser", "test_api_key")
        result = client.fetch_history("unknown", hours=1)

        assert result == []

    @patch("shared.cloud.adafruit_io_http.requests")
    def test_fetch_history_applies_environment_prefix(self, mock_requests: MagicMock) -> None:
        """fetch_history() applies environment prefix to feed name."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": []}
        mock_requests.get.return_value = mock_response

        client = AdafruitIOHTTP("testuser", "test_api_key", environment="nonprod")
        client.fetch_history("pooltemp", hours=24)

        call_args = mock_requests.get.call_args
        assert "nonprod-pooltemp" in call_args[0][0]


class TestAdafruitIOHTTPSyncTime:
    """Test sync_time() functionality."""

    @patch("shared.cloud.adafruit_io_http.requests")
    def test_sync_time_makes_get_request(self, mock_requests: MagicMock) -> None:
        """sync_time() makes GET request to time struct endpoint."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "year": 2024,
            "mon": 1,
            "mday": 15,
            "hour": 10,
            "min": 30,
            "sec": 45,
            "wday": 0,
            "yday": 15,
            "isdst": 0,
        }
        mock_requests.get.return_value = mock_response

        client = AdafruitIOHTTP("testuser", "test_api_key")
        client.sync_time()

        mock_requests.get.assert_called_once()
        call_args = mock_requests.get.call_args
        assert "testuser/integrations/time/struct" in call_args[0][0]

    @patch("shared.cloud.adafruit_io_http.requests")
    def test_sync_time_includes_api_key_header(self, mock_requests: MagicMock) -> None:
        """sync_time() includes X-AIO-Key header."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "year": 2024,
            "mon": 1,
            "mday": 15,
            "hour": 10,
            "min": 30,
            "sec": 45,
            "wday": 0,
            "yday": 15,
            "isdst": 0,
        }
        mock_requests.get.return_value = mock_response

        client = AdafruitIOHTTP("testuser", "test_api_key")
        client.sync_time()

        call_args = mock_requests.get.call_args
        headers = call_args[1]["headers"]
        assert headers["X-AIO-Key"] == "test_api_key"

    @patch("shared.cloud.adafruit_io_http.requests")
    def test_sync_time_returns_datetime(self, mock_requests: MagicMock) -> None:
        """sync_time() returns a datetime object."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "year": 2024,
            "mon": 1,
            "mday": 15,
            "hour": 10,
            "min": 30,
            "sec": 45,
            "wday": 0,
            "yday": 15,
            "isdst": 0,
        }
        mock_requests.get.return_value = mock_response

        client = AdafruitIOHTTP("testuser", "test_api_key")
        result = client.sync_time()

        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15
        assert result.hour == 10
        assert result.minute == 30
        assert result.second == 45
