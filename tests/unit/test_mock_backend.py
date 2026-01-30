# Tests for MockBackend cloud implementation

import time
from unittest.mock import patch

from shared.cloud import MockBackend


class TestMockBackendInitialization:
    """Test MockBackend initialization state."""

    def test_starts_with_empty_feeds(self):
        """MockBackend starts with no stored feeds."""
        backend = MockBackend()
        assert backend._feeds == {}

    def test_starts_with_no_subscribers(self):
        """MockBackend starts with no subscribers."""
        backend = MockBackend()
        assert backend._subscribers == {}

    def test_starts_disconnected(self):
        """MockBackend starts in disconnected state."""
        backend = MockBackend()
        assert backend._connected is False


class TestMockBackendConnectDisconnect:
    """Test connect/disconnect no-op behavior."""

    def test_connect_does_not_raise(self):
        """connect() is a no-op and does not raise."""
        backend = MockBackend()
        backend.connect()

    def test_disconnect_does_not_raise(self):
        """disconnect() is a no-op and does not raise."""
        backend = MockBackend()
        backend.disconnect()

    def test_multiple_connects_allowed(self):
        """Can call connect() multiple times without error."""
        backend = MockBackend()
        backend.connect()
        backend.connect()
        backend.connect()

    def test_multiple_disconnects_allowed(self):
        """Can call disconnect() multiple times without error."""
        backend = MockBackend()
        backend.disconnect()
        backend.disconnect()
        backend.disconnect()

    def test_connect_sets_connected_state(self):
        """connect() sets connected state to True."""
        backend = MockBackend()
        backend.connect()
        assert backend._connected is True

    def test_disconnect_clears_connected_state(self):
        """disconnect() sets connected state to False."""
        backend = MockBackend()
        backend.connect()
        backend.disconnect()
        assert backend._connected is False


class TestMockBackendPublish:
    """Test publish() functionality."""

    def test_publish_stores_value_by_feed_name(self):
        """publish() stores value indexed by feed name."""
        backend = MockBackend()
        backend.publish("pooltemp", 72.5)
        assert "pooltemp" in backend._feeds
        assert len(backend._feeds["pooltemp"]) == 1

    def test_publish_stores_value_with_timestamp(self):
        """publish() stores value with timestamp tuple."""
        backend = MockBackend()
        before = time.time()
        backend.publish("pooltemp", 72.5)
        after = time.time()

        stored = backend._feeds["pooltemp"][0]
        timestamp, value = stored
        assert value == 72.5
        assert before <= timestamp <= after

    def test_publish_multiple_values_same_feed(self):
        """publish() accumulates multiple values for same feed."""
        backend = MockBackend()
        backend.publish("pooltemp", 72.5)
        backend.publish("pooltemp", 73.0)
        backend.publish("pooltemp", 73.5)

        assert len(backend._feeds["pooltemp"]) == 3

    def test_publish_different_feeds_separate(self):
        """publish() keeps different feeds separate."""
        backend = MockBackend()
        backend.publish("pooltemp", 72.5)
        backend.publish("waterlevel", "ok")

        assert len(backend._feeds) == 2
        assert len(backend._feeds["pooltemp"]) == 1
        assert len(backend._feeds["waterlevel"]) == 1


class TestMockBackendSubscribe:
    """Test subscribe() functionality."""

    def test_subscribe_registers_callback(self):
        """subscribe() registers callback for feed."""
        backend = MockBackend()

        def callback(feed, value):
            pass

        backend.subscribe("pooltemp", callback)

        assert "pooltemp" in backend._subscribers
        assert callback in backend._subscribers["pooltemp"]

    def test_subscribe_multiple_callbacks_same_feed(self):
        """subscribe() allows multiple callbacks for same feed."""
        backend = MockBackend()

        def callback1(feed, value):
            pass

        def callback2(feed, value):
            pass

        backend.subscribe("pooltemp", callback1)
        backend.subscribe("pooltemp", callback2)

        assert len(backend._subscribers["pooltemp"]) == 2

    def test_publish_triggers_subscriber_callback(self):
        """publish() calls registered subscriber callbacks."""
        backend = MockBackend()
        received = []

        def callback(feed, value):
            received.append((feed, value))

        backend.subscribe("pooltemp", callback)
        backend.publish("pooltemp", 72.5)

        assert len(received) == 1
        assert received[0] == ("pooltemp", 72.5)

    def test_publish_triggers_all_subscribers(self):
        """publish() calls all registered callbacks for feed."""
        backend = MockBackend()
        received1 = []
        received2 = []

        def callback1(feed, value):
            received1.append((feed, value))

        def callback2(feed, value):
            received2.append((feed, value))

        backend.subscribe("pooltemp", callback1)
        backend.subscribe("pooltemp", callback2)
        backend.publish("pooltemp", 72.5)

        assert len(received1) == 1
        assert len(received2) == 1

    def test_subscriber_only_receives_matching_feed(self):
        """Subscriber only receives messages for subscribed feed."""
        backend = MockBackend()
        received = []

        def callback(feed, value):
            received.append((feed, value))

        backend.subscribe("pooltemp", callback)
        backend.publish("waterlevel", "ok")

        assert len(received) == 0


class TestMockBackendFetchLatest:
    """Test fetch_latest() functionality."""

    def test_fetch_latest_returns_none_for_unknown_feed(self):
        """fetch_latest() returns None for unknown feed."""
        backend = MockBackend()
        result = backend.fetch_latest("unknown")
        assert result is None

    def test_fetch_latest_returns_value_after_publish(self):
        """fetch_latest() returns value after publish."""
        backend = MockBackend()
        backend.publish("pooltemp", 72.5)
        result = backend.fetch_latest("pooltemp")
        assert result == 72.5

    def test_fetch_latest_returns_most_recent(self):
        """fetch_latest() returns most recent when multiple published."""
        backend = MockBackend()
        backend.publish("pooltemp", 72.5)
        backend.publish("pooltemp", 73.0)
        backend.publish("pooltemp", 73.5)
        result = backend.fetch_latest("pooltemp")
        assert result == 73.5


class TestMockBackendFetchHistory:
    """Test fetch_history() functionality."""

    def test_fetch_history_returns_empty_for_unknown_feed(self):
        """fetch_history() returns empty list for unknown feed."""
        backend = MockBackend()
        result = backend.fetch_history("unknown", hours=1)
        assert result == []

    def test_fetch_history_returns_all_within_window(self):
        """fetch_history() returns all values within time window."""
        backend = MockBackend()
        backend.publish("pooltemp", 72.5)
        backend.publish("pooltemp", 73.0)
        backend.publish("pooltemp", 73.5)

        result = backend.fetch_history("pooltemp", hours=1)
        assert len(result) == 3
        assert 72.5 in result
        assert 73.0 in result
        assert 73.5 in result

    def test_fetch_history_filters_old_values(self):
        """fetch_history() filters values outside time window."""
        backend = MockBackend()
        # Manually insert an old value (2 hours ago)
        old_timestamp = time.time() - (2 * 3600)
        backend._feeds["pooltemp"] = [(old_timestamp, 70.0)]
        # Publish a recent value
        backend.publish("pooltemp", 72.5)

        result = backend.fetch_history("pooltemp", hours=1)
        assert len(result) == 1
        assert result[0] == 72.5

    def test_fetch_history_returns_chronological_order(self):
        """fetch_history() returns values in chronological order."""
        backend = MockBackend()
        backend.publish("pooltemp", 72.5)
        backend.publish("pooltemp", 73.0)
        backend.publish("pooltemp", 73.5)

        result = backend.fetch_history("pooltemp", hours=1)
        assert result == [72.5, 73.0, 73.5]


class TestMockBackendSyncTime:
    """Test sync_time() functionality."""

    def test_sync_time_returns_datetime_object(self):
        """sync_time() returns a datetime object."""
        backend = MockBackend()
        result = backend.sync_time()
        assert hasattr(result, "year")
        assert hasattr(result, "month")
        assert hasattr(result, "day")
        assert hasattr(result, "hour")
        assert hasattr(result, "minute")
        assert hasattr(result, "second")

    def test_sync_time_returns_current_time(self):
        """sync_time() returns approximately current time."""
        backend = MockBackend()
        before = time.time()
        result = backend.sync_time()
        after = time.time()

        result_timestamp = result.timestamp()
        assert before <= result_timestamp <= after

    def test_sync_time_raises_when_datetime_unavailable(self):
        """sync_time() raises RuntimeError when datetime is None."""
        import pytest

        backend = MockBackend()
        with patch("shared.cloud.mock.datetime", None):
            with pytest.raises(RuntimeError, match="datetime module not available"):
                backend.sync_time()
