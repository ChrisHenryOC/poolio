# Configuration loader
# CircuitPython compatible (no dataclasses, no type annotations in signatures)

from typing import Any

from .defaults import NODE_DEFAULTS
from .environment import validate_environment
from .schema import ConfigurationError

# Valid node types
VALID_NODE_TYPES: list[str] = ["pool_node", "valve_node", "display_node"]


class Config:
    """
    Configuration container for a node.

    Holds merged configuration from defaults, config.json, and settings.toml.
    Provides get() method for accessing settings with defaults.

    Attributes:
        node_type: Type of node (pool_node, valve_node, display_node)
        environment: Environment name (prod, nonprod)
        settings: Dictionary of configuration settings
    """

    node_type: str
    environment: str
    settings: dict[str, Any]

    def __init__(self, node_type: str, environment: str, settings: dict[str, Any]) -> None:
        """
        Initialize Config.

        Args:
            node_type: Type of node
            environment: Environment name
            settings: Dictionary of configuration settings
        """
        self.node_type = node_type
        self.environment = environment
        self.settings = settings

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        return self.settings.get(key, default)


def load_config(node_type: str, env_override: str | None = None) -> Config:
    """
    Load configuration for a node type.

    Merges configuration from multiple sources:
    1. NODE_DEFAULTS for the node type
    2. config.json (if present) - TODO: implement file loading
    3. settings.toml secrets (if present) - TODO: implement file loading

    Args:
        node_type: Type of node (pool_node, valve_node, display_node)
        env_override: Optional environment override (defaults to "prod")

    Returns:
        Config instance with merged configuration

    Raises:
        ConfigurationError: If node_type or environment is invalid
    """
    # Validate node type
    if node_type not in VALID_NODE_TYPES:
        raise ConfigurationError(f"Unknown node type: {node_type}. Valid: {VALID_NODE_TYPES}")

    # Determine environment
    environment = env_override if env_override else "prod"
    validate_environment(environment)

    # Start with defaults for this node type
    defaults = NODE_DEFAULTS.get(node_type, {})
    settings: dict[str, Any] = dict(defaults)

    # TODO: Load from config.json and merge
    # TODO: Load from settings.toml and merge secrets

    return Config(node_type, environment, settings)
