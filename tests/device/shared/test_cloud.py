"""
On-device tests for the shared.cloud module.

These tests verify MockBackend functionality which is used for testing
without network access. All tests are pure logic - no hardware required.
"""

from shared.cloud import MockBackend
from tests.device.assertions import (
    assert_equal,
    assert_false,
    assert_is_none,
    assert_is_not_none,
    assert_true,
    skip,
)

# =============================================================================
# MockBackend Connection Tests
# =============================================================================


def test_mock_backend_initial_state():
    """MockBackend starts disconnected."""
    backend = MockBackend(environment="test")
    assert_false(backend.is_connected)


def test_mock_backend_connect():
    """MockBackend connect sets connected state."""
    backend = MockBackend(environment="test")
    backend.connect()
    assert_true(backend.is_connected)


def test_mock_backend_disconnect():
    """MockBackend disconnect clears connected state."""
    backend = MockBackend(environment="test")
    backend.connect()
    backend.disconnect()
    assert_false(backend.is_connected)


# =============================================================================
# MockBackend Publish Tests
# =============================================================================


def test_mock_backend_publish_stores_value():
    """Published values can be fetched."""
    backend = MockBackend(environment="test")
    backend.connect()

    backend.publish("test-feed", "test-value")
    result = backend.fetch_latest("test-feed")

    assert_equal(result, "test-value")


def test_mock_backend_publish_returns_true():
    """Publish returns True on success."""
    backend = MockBackend(environment="test")
    backend.connect()

    result = backend.publish("test-feed", "test-value")

    assert_true(result)


def test_mock_backend_publish_multiple_values():
    """Multiple publishes to same feed stores all values."""
    backend = MockBackend(environment="test")
    backend.connect()

    backend.publish("test-feed", "value-1")
    backend.publish("test-feed", "value-2")
    backend.publish("test-feed", "value-3")

    # fetch_latest returns most recent
    result = backend.fetch_latest("test-feed")
    assert_equal(result, "value-3")


# =============================================================================
# MockBackend Subscribe Tests
# =============================================================================


def test_mock_backend_subscribe_callback():
    """Subscribe callback is invoked on publish."""
    backend = MockBackend(environment="test")
    backend.connect()

    received = []

    def callback(feed, value):
        received.append((feed, value))

    backend.subscribe("test-feed", callback)
    backend.publish("test-feed", "test-value")

    assert_equal(len(received), 1)
    assert_equal(received[0], ("test-feed", "test-value"))


def test_mock_backend_subscribe_multiple_callbacks():
    """Multiple subscribers all receive published values."""
    backend = MockBackend(environment="test")
    backend.connect()

    received_1 = []
    received_2 = []

    backend.subscribe("test-feed", lambda f, v: received_1.append(v))
    backend.subscribe("test-feed", lambda f, v: received_2.append(v))
    backend.publish("test-feed", "test-value")

    assert_equal(len(received_1), 1)
    assert_equal(len(received_2), 1)


def test_mock_backend_subscribe_wrong_feed():
    """Subscriber only receives from subscribed feed."""
    backend = MockBackend(environment="test")
    backend.connect()

    received = []
    backend.subscribe("feed-a", lambda f, v: received.append(v))
    backend.publish("feed-b", "wrong-feed")

    assert_equal(len(received), 0)


# =============================================================================
# MockBackend Fetch Tests
# =============================================================================


def test_mock_backend_fetch_latest_empty():
    """Fetch from empty feed returns None."""
    backend = MockBackend(environment="test")
    backend.connect()

    result = backend.fetch_latest("nonexistent-feed")

    assert_is_none(result)


def test_mock_backend_fetch_history_empty():
    """Fetch history from empty feed returns empty list."""
    backend = MockBackend(environment="test")
    backend.connect()

    result = backend.fetch_history("nonexistent-feed", hours=24)

    assert_equal(result, [])


def test_mock_backend_fetch_history_returns_values():
    """Fetch history returns recent values."""
    backend = MockBackend(environment="test")
    backend.connect()

    backend.publish("test-feed", "value-1")
    backend.publish("test-feed", "value-2")

    result = backend.fetch_history("test-feed", hours=1)

    assert_equal(len(result), 2)
    assert_equal(result[0], "value-1")
    assert_equal(result[1], "value-2")


# =============================================================================
# MockBackend Time Sync Tests
# =============================================================================


def test_mock_backend_sync_time():
    """Sync time returns a datetime object."""
    backend = MockBackend(environment="test")
    backend.connect()

    # sync_time may raise if datetime module is not available
    try:
        result = backend.sync_time()
        assert_is_not_none(result)
    except RuntimeError:
        skip("datetime module not available")


# =============================================================================
# MockBackend Environment Tests
# =============================================================================


def test_mock_backend_environment():
    """MockBackend stores environment."""
    backend = MockBackend(environment="nonprod")

    assert_equal(backend.environment, "nonprod")
