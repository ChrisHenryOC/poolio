# Tests for configuration management module

import pytest


class TestConfigurationError:
    """Test ConfigurationError exception class."""

    def test_configuration_error_can_be_imported(self) -> None:
        """ConfigurationError can be imported from shared.config."""
        from shared.config import ConfigurationError

        assert ConfigurationError is not None

    def test_configuration_error_is_exception(self) -> None:
        """ConfigurationError is an Exception subclass."""
        from shared.config import ConfigurationError

        assert issubclass(ConfigurationError, Exception)

    def test_configuration_error_has_message(self) -> None:
        """ConfigurationError stores error message."""
        from shared.config import ConfigurationError

        error = ConfigurationError("Invalid config")
        assert str(error) == "Invalid config"

    def test_configuration_error_can_be_raised(self) -> None:
        """ConfigurationError can be raised and caught."""
        from shared.config import ConfigurationError

        with pytest.raises(ConfigurationError, match="test error"):
            raise ConfigurationError("test error")


class TestValidEnvironments:
    """Test VALID_ENVIRONMENTS constant."""

    def test_valid_environments_can_be_imported(self) -> None:
        """VALID_ENVIRONMENTS can be imported from shared.config."""
        from shared.config import VALID_ENVIRONMENTS

        assert VALID_ENVIRONMENTS is not None

    def test_valid_environments_contains_prod(self) -> None:
        """VALID_ENVIRONMENTS contains 'prod'."""
        from shared.config import VALID_ENVIRONMENTS

        assert "prod" in VALID_ENVIRONMENTS

    def test_valid_environments_contains_nonprod(self) -> None:
        """VALID_ENVIRONMENTS contains 'nonprod'."""
        from shared.config import VALID_ENVIRONMENTS

        assert "nonprod" in VALID_ENVIRONMENTS

    def test_valid_environments_has_only_two_entries(self) -> None:
        """VALID_ENVIRONMENTS has exactly two entries."""
        from shared.config import VALID_ENVIRONMENTS

        assert len(VALID_ENVIRONMENTS) == 2


class TestNodeDefaults:
    """Test NODE_DEFAULTS configuration."""

    def test_node_defaults_can_be_imported(self) -> None:
        """NODE_DEFAULTS can be imported from shared.config."""
        from shared.config import NODE_DEFAULTS

        assert NODE_DEFAULTS is not None

    def test_node_defaults_is_dict(self) -> None:
        """NODE_DEFAULTS is a dictionary."""
        from shared.config import NODE_DEFAULTS

        assert isinstance(NODE_DEFAULTS, dict)

    def test_node_defaults_has_pool_node(self) -> None:
        """NODE_DEFAULTS has pool_node entry."""
        from shared.config import NODE_DEFAULTS

        assert "pool_node" in NODE_DEFAULTS

    def test_node_defaults_has_valve_node(self) -> None:
        """NODE_DEFAULTS has valve_node entry."""
        from shared.config import NODE_DEFAULTS

        assert "valve_node" in NODE_DEFAULTS

    def test_node_defaults_has_display_node(self) -> None:
        """NODE_DEFAULTS has display_node entry."""
        from shared.config import NODE_DEFAULTS

        assert "display_node" in NODE_DEFAULTS

    def test_pool_node_has_sleep_duration(self) -> None:
        """pool_node defaults include sleep_duration."""
        from shared.config import NODE_DEFAULTS

        assert "sleep_duration" in NODE_DEFAULTS["pool_node"]
        assert NODE_DEFAULTS["pool_node"]["sleep_duration"] == 120

    def test_pool_node_has_watchdog_timeout(self) -> None:
        """pool_node defaults include watchdog_timeout."""
        from shared.config import NODE_DEFAULTS

        assert "watchdog_timeout" in NODE_DEFAULTS["pool_node"]
        assert NODE_DEFAULTS["pool_node"]["watchdog_timeout"] == 60

    def test_valve_node_has_valve_start_time(self) -> None:
        """valve_node defaults include valve_start_time."""
        from shared.config import NODE_DEFAULTS

        assert "valve_start_time" in NODE_DEFAULTS["valve_node"]
        assert NODE_DEFAULTS["valve_node"]["valve_start_time"] == "09:00"

    def test_valve_node_has_max_fill_minutes(self) -> None:
        """valve_node defaults include max_fill_minutes."""
        from shared.config import NODE_DEFAULTS

        assert "max_fill_minutes" in NODE_DEFAULTS["valve_node"]
        assert NODE_DEFAULTS["valve_node"]["max_fill_minutes"] == 9

    def test_display_node_has_chart_history_hours(self) -> None:
        """display_node defaults include chart_history_hours."""
        from shared.config import NODE_DEFAULTS

        assert "chart_history_hours" in NODE_DEFAULTS["display_node"]
        assert NODE_DEFAULTS["display_node"]["chart_history_hours"] == 24


class TestValidateEnvironment:
    """Test validate_environment function."""

    def test_validate_environment_can_be_imported(self) -> None:
        """validate_environment can be imported from shared.config."""
        from shared.config import validate_environment

        assert validate_environment is not None

    def test_validate_environment_accepts_prod(self) -> None:
        """validate_environment accepts 'prod'."""
        from shared.config import validate_environment

        # Should not raise
        validate_environment("prod")

    def test_validate_environment_accepts_nonprod(self) -> None:
        """validate_environment accepts 'nonprod'."""
        from shared.config import validate_environment

        # Should not raise
        validate_environment("nonprod")

    def test_validate_environment_rejects_invalid(self) -> None:
        """validate_environment raises ConfigurationError for invalid environment."""
        from shared.config import ConfigurationError, validate_environment

        with pytest.raises(ConfigurationError, match="Unknown environment"):
            validate_environment("invalid")

    def test_validate_environment_rejects_dev(self) -> None:
        """validate_environment rejects 'dev' (not in two-environment model)."""
        from shared.config import ConfigurationError, validate_environment

        with pytest.raises(ConfigurationError):
            validate_environment("dev")

    def test_validate_environment_rejects_empty_string(self) -> None:
        """validate_environment raises ConfigurationError for empty string."""
        from shared.config import ConfigurationError, validate_environment

        with pytest.raises(ConfigurationError):
            validate_environment("")

    def test_validate_environment_is_case_sensitive(self) -> None:
        """validate_environment rejects uppercase 'PROD'."""
        from shared.config import ConfigurationError, validate_environment

        with pytest.raises(ConfigurationError):
            validate_environment("PROD")


class TestGetFeedName:
    """Test get_feed_name function."""

    def test_get_feed_name_can_be_imported(self) -> None:
        """get_feed_name can be imported from shared.config."""
        from shared.config import get_feed_name

        assert get_feed_name is not None

    def test_get_feed_name_prod_format(self) -> None:
        """get_feed_name returns 'poolio.feedname' for prod."""
        from shared.config import get_feed_name

        result = get_feed_name("gateway", "prod")
        assert result == "poolio.gateway"

    def test_get_feed_name_nonprod_format(self) -> None:
        """get_feed_name returns 'poolio-nonprod.nonprod-feedname' for nonprod."""
        from shared.config import get_feed_name

        result = get_feed_name("gateway", "nonprod")
        assert result == "poolio-nonprod.nonprod-gateway"

    def test_get_feed_name_raises_for_invalid_environment(self) -> None:
        """get_feed_name raises ConfigurationError for invalid environment."""
        from shared.config import ConfigurationError, get_feed_name

        with pytest.raises(ConfigurationError):
            get_feed_name("gateway", "invalid")


class TestSelectApiKey:
    """Test select_api_key function."""

    def test_select_api_key_can_be_imported(self) -> None:
        """select_api_key can be imported from shared.config."""
        from shared.config import select_api_key

        assert select_api_key is not None

    def test_select_api_key_prod(self) -> None:
        """select_api_key returns AIO_KEY_PROD for prod environment."""
        from shared.config import select_api_key

        secrets = {"AIO_KEY_PROD": "prod_key", "AIO_KEY_NONPROD": "nonprod_key"}
        result = select_api_key("prod", secrets)
        assert result == "prod_key"

    def test_select_api_key_nonprod(self) -> None:
        """select_api_key returns AIO_KEY_NONPROD for nonprod environment."""
        from shared.config import select_api_key

        secrets = {"AIO_KEY_PROD": "prod_key", "AIO_KEY_NONPROD": "nonprod_key"}
        result = select_api_key("nonprod", secrets)
        assert result == "nonprod_key"

    def test_select_api_key_raises_for_missing_key(self) -> None:
        """select_api_key raises ConfigurationError if key is missing."""
        from shared.config import ConfigurationError, select_api_key

        secrets = {}
        with pytest.raises(ConfigurationError, match="API key"):
            select_api_key("prod", secrets)

    def test_select_api_key_raises_for_invalid_environment(self) -> None:
        """select_api_key raises ConfigurationError for invalid environment."""
        from shared.config import ConfigurationError, select_api_key

        secrets = {"AIO_KEY_PROD": "key"}
        with pytest.raises(ConfigurationError):
            select_api_key("invalid", secrets)


class TestEnvironmentConfig:
    """Test EnvironmentConfig class."""

    def test_environment_config_can_be_imported(self) -> None:
        """EnvironmentConfig can be imported from shared.config."""
        from shared.config import EnvironmentConfig

        assert EnvironmentConfig is not None

    def test_environment_config_has_environment(self) -> None:
        """EnvironmentConfig has environment attribute."""
        from shared.config import EnvironmentConfig

        config = EnvironmentConfig("prod")
        assert config.environment == "prod"

    def test_environment_config_has_feed_group(self) -> None:
        """EnvironmentConfig has feed_group attribute."""
        from shared.config import EnvironmentConfig

        config = EnvironmentConfig("prod")
        assert config.feed_group == "poolio"

    def test_environment_config_nonprod_feed_group(self) -> None:
        """EnvironmentConfig has correct feed_group for nonprod."""
        from shared.config import EnvironmentConfig

        config = EnvironmentConfig("nonprod")
        assert config.feed_group == "poolio-nonprod"

    def test_environment_config_has_hardware_enabled(self) -> None:
        """EnvironmentConfig has hardware_enabled attribute."""
        from shared.config import EnvironmentConfig

        config = EnvironmentConfig("prod")
        assert config.hardware_enabled is True

    def test_environment_config_nonprod_hardware_enabled(self) -> None:
        """EnvironmentConfig hardware_enabled is True for nonprod (per arch)."""
        from shared.config import EnvironmentConfig

        config = EnvironmentConfig("nonprod")
        # Per architecture.md, nonprod has hardware configurable, defaulting to enabled
        assert config.hardware_enabled is True


class TestConfig:
    """Test Config class."""

    def test_config_can_be_imported(self) -> None:
        """Config can be imported from shared.config."""
        from shared.config import Config

        assert Config is not None

    def test_config_has_node_type(self) -> None:
        """Config has node_type attribute."""
        from shared.config import Config

        config = Config("pool_node", "prod", {})
        assert config.node_type == "pool_node"

    def test_config_has_environment(self) -> None:
        """Config has environment attribute."""
        from shared.config import Config

        config = Config("pool_node", "prod", {})
        assert config.environment == "prod"

    def test_config_has_settings(self) -> None:
        """Config has settings attribute."""
        from shared.config import Config

        settings = {"sleep_duration": 120}
        config = Config("pool_node", "prod", settings)
        assert config.settings == settings

    def test_config_get_returns_setting(self) -> None:
        """Config.get() returns setting value."""
        from shared.config import Config

        config = Config("pool_node", "prod", {"sleep_duration": 120})
        assert config.get("sleep_duration") == 120

    def test_config_get_returns_default(self) -> None:
        """Config.get() returns default when key missing."""
        from shared.config import Config

        config = Config("pool_node", "prod", {})
        assert config.get("missing", "default") == "default"

    def test_config_get_returns_none_when_no_default(self) -> None:
        """Config.get() returns None when key missing and no default provided."""
        from shared.config import Config

        config = Config("pool_node", "prod", {})
        assert config.get("missing") is None


class TestLoadConfig:
    """Test load_config function."""

    def test_load_config_can_be_imported(self) -> None:
        """load_config can be imported from shared.config."""
        from shared.config import load_config

        assert load_config is not None

    def test_load_config_returns_config(self) -> None:
        """load_config returns Config instance."""
        from shared.config import Config, load_config

        result = load_config("pool_node")
        assert isinstance(result, Config)

    def test_load_config_uses_defaults(self) -> None:
        """load_config applies NODE_DEFAULTS for node type."""
        from shared.config import load_config

        result = load_config("pool_node")
        # Should have pool_node defaults
        assert result.get("sleep_duration") == 120
        assert result.get("watchdog_timeout") == 60

    def test_load_config_with_env_override(self) -> None:
        """load_config uses env_override when provided."""
        from shared.config import load_config

        result = load_config("pool_node", env_override="nonprod")
        assert result.environment == "nonprod"

    def test_load_config_default_environment_is_prod(self) -> None:
        """load_config defaults to prod environment."""
        from shared.config import load_config

        result = load_config("pool_node")
        assert result.environment == "prod"

    def test_load_config_raises_for_invalid_node_type(self) -> None:
        """load_config raises ConfigurationError for unknown node type."""
        from shared.config import ConfigurationError, load_config

        with pytest.raises(ConfigurationError, match="Unknown node type"):
            load_config("invalid_node")

    def test_load_config_raises_for_invalid_environment(self) -> None:
        """load_config raises ConfigurationError for invalid environment."""
        from shared.config import ConfigurationError, load_config

        with pytest.raises(ConfigurationError):
            load_config("pool_node", env_override="invalid")

    def test_load_config_valve_node(self) -> None:
        """load_config works for valve_node."""
        from shared.config import load_config

        result = load_config("valve_node")
        assert result.node_type == "valve_node"
        assert result.get("valve_start_time") == "09:00"

    def test_load_config_display_node(self) -> None:
        """load_config works for display_node."""
        from shared.config import load_config

        result = load_config("display_node")
        assert result.node_type == "display_node"
        assert result.get("chart_history_hours") == 24
