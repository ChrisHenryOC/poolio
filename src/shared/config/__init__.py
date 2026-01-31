# Configuration management module
# CircuitPython compatible

from .defaults import NODE_DEFAULTS
from .environment import (
    EnvironmentConfig,
    get_environment_config,
    get_feed_name,
    select_api_key,
    validate_environment,
)
from .loader import Config, load_config
from .schema import VALID_ENVIRONMENTS, ConfigurationError

__all__ = [
    "ConfigurationError",
    "VALID_ENVIRONMENTS",
    "NODE_DEFAULTS",
    "validate_environment",
    "get_feed_name",
    "select_api_key",
    "get_environment_config",
    "EnvironmentConfig",
    "Config",
    "load_config",
]
