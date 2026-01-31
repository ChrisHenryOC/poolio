# Environment configuration handling
# CircuitPython compatible (no dataclasses, no type annotations in signatures)

from .schema import VALID_ENVIRONMENTS, ConfigurationError

# Feed group names per environment
FEED_GROUPS = {
    "prod": "poolio",
    "nonprod": "poolio-nonprod",
}

# API key names in secrets per environment
API_KEY_NAMES = {
    "prod": "AIO_KEY_PROD",
    "nonprod": "AIO_KEY_NONPROD",
}


def validate_environment(environment):
    """
    Validate environment string.

    Args:
        environment: Environment name to validate

    Raises:
        ConfigurationError: If environment is not in VALID_ENVIRONMENTS
    """
    if environment not in VALID_ENVIRONMENTS:
        raise ConfigurationError(f"Unknown environment: {environment}. Valid: {VALID_ENVIRONMENTS}")


def get_feed_name(logical_name, environment):
    """
    Get full feed name with group prefix.

    Args:
        logical_name: Logical feed name (e.g., "gateway")
        environment: Environment name ("prod" or "nonprod")

    Returns:
        Full feed name in format: "{group}.{prefixed_feed}"
        - prod: "poolio.gateway"
        - nonprod: "poolio-nonprod.nonprod-gateway"

    Raises:
        ConfigurationError: If environment is invalid
    """
    validate_environment(environment)

    group = FEED_GROUPS[environment]

    if environment == "prod":
        return f"{group}.{logical_name}"
    else:
        # Nonprod feeds have environment prefix
        return f"{group}.{environment}-{logical_name}"


def select_api_key(environment, secrets):
    """
    Select appropriate API key for environment.

    Args:
        environment: Environment name ("prod" or "nonprod")
        secrets: Dictionary containing API keys (from settings.toml)

    Returns:
        API key string for the environment

    Raises:
        ConfigurationError: If environment is invalid or key is missing
    """
    validate_environment(environment)

    key_name = API_KEY_NAMES[environment]
    if key_name not in secrets:
        raise ConfigurationError(f"API key '{key_name}' not found in secrets")

    return secrets[key_name]


class EnvironmentConfig:
    """
    Configuration for a specific environment.

    Provides environment-specific settings like feed group names
    and hardware enable flags.

    Attributes:
        environment: Environment name (prod, nonprod)
        feed_group: Adafruit IO feed group name
        hardware_enabled: Whether hardware operations are enabled
    """

    def __init__(self, environment):
        """
        Initialize EnvironmentConfig.

        Args:
            environment: Environment name (prod or nonprod)
        """
        validate_environment(environment)

        self.environment = environment
        self.feed_group = FEED_GROUPS[environment]
        # Hardware is enabled for both prod and nonprod by default
        # Per architecture.md, nonprod hardware is "configurable"
        self.hardware_enabled = True
