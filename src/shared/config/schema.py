# Configuration schema and validation
# CircuitPython compatible (no dataclasses, no type annotations in signatures)


# Valid environment values per architecture.md
VALID_ENVIRONMENTS = ["prod", "nonprod"]


class ConfigurationError(Exception):
    """
    Exception raised for configuration errors.

    Used for invalid configuration values, missing required fields,
    or unknown node types/environments.
    """
