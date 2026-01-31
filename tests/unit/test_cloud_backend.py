# Tests for CloudBackend base class and interface compliance

import pytest

from shared.cloud import CloudBackend, MockBackend, AdafruitIOHTTP


class TestCloudBackendBaseClass:
    """Test CloudBackend base class interface."""

    def test_cloudbackend_exists(self) -> None:
        """CloudBackend class can be imported."""
        assert CloudBackend is not None

    def test_cloudbackend_connect_raises_not_implemented(self) -> None:
        """connect() raises NotImplementedError."""
        backend = CloudBackend()
        with pytest.raises(NotImplementedError):
            backend.connect()

    def test_cloudbackend_disconnect_raises_not_implemented(self) -> None:
        """disconnect() raises NotImplementedError."""
        backend = CloudBackend()
        with pytest.raises(NotImplementedError):
            backend.disconnect()

    def test_cloudbackend_is_connected_raises_not_implemented(self) -> None:
        """is_connected raises NotImplementedError."""
        backend = CloudBackend()
        with pytest.raises(NotImplementedError):
            _ = backend.is_connected

    def test_cloudbackend_publish_raises_not_implemented(self) -> None:
        """publish() raises NotImplementedError."""
        backend = CloudBackend()
        with pytest.raises(NotImplementedError):
            backend.publish("feed", "value")

    def test_cloudbackend_publish_accepts_qos_parameter(self) -> None:
        """publish() accepts qos parameter."""
        backend = CloudBackend()
        with pytest.raises(NotImplementedError):
            backend.publish("feed", "value", qos=1)

    def test_cloudbackend_subscribe_raises_not_implemented(self) -> None:
        """subscribe() raises NotImplementedError."""
        backend = CloudBackend()
        with pytest.raises(NotImplementedError):
            backend.subscribe("feed", lambda f, v: None)

    def test_cloudbackend_fetch_latest_raises_not_implemented(self) -> None:
        """fetch_latest() raises NotImplementedError."""
        backend = CloudBackend()
        with pytest.raises(NotImplementedError):
            backend.fetch_latest("feed")

    def test_cloudbackend_fetch_history_raises_not_implemented(self) -> None:
        """fetch_history() raises NotImplementedError."""
        backend = CloudBackend()
        with pytest.raises(NotImplementedError):
            backend.fetch_history("feed", hours=24)

    def test_cloudbackend_fetch_history_accepts_resolution_parameter(self) -> None:
        """fetch_history() accepts resolution parameter."""
        backend = CloudBackend()
        with pytest.raises(NotImplementedError):
            backend.fetch_history("feed", hours=24, resolution=10)

    def test_cloudbackend_sync_time_raises_not_implemented(self) -> None:
        """sync_time() raises NotImplementedError."""
        backend = CloudBackend()
        with pytest.raises(NotImplementedError):
            backend.sync_time()


class TestMockBackendInheritance:
    """Test MockBackend extends CloudBackend."""

    def test_mockbackend_is_subclass_of_cloudbackend(self) -> None:
        """MockBackend is a subclass of CloudBackend."""
        assert issubclass(MockBackend, CloudBackend)

    def test_mockbackend_instance_is_cloudbackend(self) -> None:
        """MockBackend instance is also a CloudBackend instance."""
        backend = MockBackend()
        assert isinstance(backend, CloudBackend)

    def test_mockbackend_publish_accepts_qos_parameter(self) -> None:
        """MockBackend.publish() accepts qos parameter."""
        backend = MockBackend()
        # Should not raise - qos is accepted but ignored
        backend.publish("feed", "value", qos=1)


class TestAdafruitIOHTTPInheritance:
    """Test AdafruitIOHTTP extends CloudBackend."""

    def test_adafruitiohttp_is_subclass_of_cloudbackend(self) -> None:
        """AdafruitIOHTTP is a subclass of CloudBackend."""
        assert issubclass(AdafruitIOHTTP, CloudBackend)

    def test_adafruitiohttp_instance_is_cloudbackend(self) -> None:
        """AdafruitIOHTTP instance is also a CloudBackend instance."""
        backend = AdafruitIOHTTP("user", "key")
        assert isinstance(backend, CloudBackend)

    @pytest.fixture
    def mock_requests(self) -> "pytest.fixture":
        """Mock requests module for HTTP tests."""
        from unittest.mock import MagicMock, patch

        with patch("shared.cloud.adafruit_io_http.requests") as mock:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock.post.return_value = mock_response
            yield mock

    def test_adafruitiohttp_publish_accepts_qos_parameter(
        self, mock_requests: "MagicMock"
    ) -> None:
        """AdafruitIOHTTP.publish() accepts qos parameter."""
        backend = AdafruitIOHTTP("user", "key")
        # Should not raise - qos is accepted but ignored
        result = backend.publish("feed", "value", qos=1)
        assert result is True
