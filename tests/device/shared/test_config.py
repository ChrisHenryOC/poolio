"""
On-device tests for the shared.config module.

These tests verify configuration management functionality including
environment validation, feed name generation, and API key selection.
All tests are pure logic - no hardware required.
"""

from shared.config import (
    NODE_DEFAULTS,
    ConfigurationError,
    EnvironmentConfig,
    get_feed_name,
    select_api_key,
    validate_environment,
)
from tests.device.assertions import (
    assert_equal,
    assert_in,
    assert_raises,
    assert_true,
)

# =============================================================================
# Environment Validation Tests
# =============================================================================


def test_validate_environment_prod():
    """validate_environment accepts 'prod'."""
    # Should not raise
    validate_environment("prod")


def test_validate_environment_nonprod():
    """validate_environment accepts 'nonprod'."""
    # Should not raise
    validate_environment("nonprod")


def test_validate_environment_invalid():
    """validate_environment rejects invalid environment."""
    assert_raises(ConfigurationError, validate_environment, "invalid")


def test_validate_environment_dev():
    """validate_environment rejects 'dev' (not in VALID_ENVIRONMENTS)."""
    assert_raises(ConfigurationError, validate_environment, "dev")


# =============================================================================
# Feed Name Tests
# =============================================================================


def test_get_feed_name_prod():
    """get_feed_name returns correct format for prod."""
    result = get_feed_name("gateway", "prod")
    assert_equal(result, "poolio.gateway")


def test_get_feed_name_prod_pooltemp():
    """get_feed_name works for pooltemp feed in prod."""
    result = get_feed_name("pooltemp", "prod")
    assert_equal(result, "poolio.pooltemp")


def test_get_feed_name_nonprod():
    """get_feed_name returns correct format for nonprod."""
    result = get_feed_name("gateway", "nonprod")
    assert_equal(result, "poolio-nonprod.nonprod-gateway")


def test_get_feed_name_nonprod_pooltemp():
    """get_feed_name adds nonprod prefix for nonprod feeds."""
    result = get_feed_name("pooltemp", "nonprod")
    assert_equal(result, "poolio-nonprod.nonprod-pooltemp")


def test_get_feed_name_invalid_environment():
    """get_feed_name raises for invalid environment."""
    assert_raises(ConfigurationError, get_feed_name, "gateway", "invalid")


# =============================================================================
# API Key Selection Tests
# =============================================================================


def test_select_api_key_prod():
    """select_api_key returns AIO_KEY_PROD for prod."""
    secrets = {"AIO_KEY_PROD": "prod-key-123", "AIO_KEY_NONPROD": "nonprod-key-456"}
    result = select_api_key("prod", secrets)
    assert_equal(result, "prod-key-123")


def test_select_api_key_nonprod():
    """select_api_key returns AIO_KEY_NONPROD for nonprod."""
    secrets = {"AIO_KEY_PROD": "prod-key-123", "AIO_KEY_NONPROD": "nonprod-key-456"}
    result = select_api_key("nonprod", secrets)
    assert_equal(result, "nonprod-key-456")


def test_select_api_key_missing_prod():
    """select_api_key raises when prod key is missing."""
    secrets = {"AIO_KEY_NONPROD": "nonprod-key-456"}
    assert_raises(ConfigurationError, select_api_key, "prod", secrets)


def test_select_api_key_missing_nonprod():
    """select_api_key raises when nonprod key is missing."""
    secrets = {"AIO_KEY_PROD": "prod-key-123"}
    assert_raises(ConfigurationError, select_api_key, "nonprod", secrets)


def test_select_api_key_invalid_environment():
    """select_api_key raises for invalid environment."""
    secrets = {"AIO_KEY_PROD": "prod-key-123"}
    assert_raises(ConfigurationError, select_api_key, "invalid", secrets)


# =============================================================================
# EnvironmentConfig Tests
# =============================================================================


def test_environment_config_prod():
    """EnvironmentConfig for prod has correct attributes."""
    config = EnvironmentConfig("prod")

    assert_equal(config.environment, "prod")
    assert_equal(config.feed_group, "poolio")
    assert_true(config.hardware_enabled)


def test_environment_config_nonprod():
    """EnvironmentConfig for nonprod has correct attributes."""
    config = EnvironmentConfig("nonprod")

    assert_equal(config.environment, "nonprod")
    assert_equal(config.feed_group, "poolio-nonprod")
    assert_true(config.hardware_enabled)


def test_environment_config_invalid():
    """EnvironmentConfig raises for invalid environment."""
    assert_raises(ConfigurationError, EnvironmentConfig, "invalid")


# =============================================================================
# Node Defaults Tests
# =============================================================================


def test_node_defaults_has_pool_node():
    """NODE_DEFAULTS contains pool_node configuration."""
    assert_in("pool_node", NODE_DEFAULTS)


def test_node_defaults_has_valve_node():
    """NODE_DEFAULTS contains valve_node configuration."""
    assert_in("valve_node", NODE_DEFAULTS)


def test_node_defaults_has_display_node():
    """NODE_DEFAULTS contains display_node configuration."""
    assert_in("display_node", NODE_DEFAULTS)


def test_node_defaults_pool_node_structure():
    """pool_node defaults contain expected keys."""
    pool_node = NODE_DEFAULTS["pool_node"]
    assert_in("sleep_duration", pool_node)
    assert_in("float_switch_reads", pool_node)
    assert_in("watchdog_timeout", pool_node)


def test_node_defaults_valve_node_structure():
    """valve_node defaults contain expected keys."""
    valve_node = NODE_DEFAULTS["valve_node"]
    assert_in("valve_start_time", valve_node)
    assert_in("max_fill_minutes", valve_node)
    assert_in("fill_window_hours", valve_node)
