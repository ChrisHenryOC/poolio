# Message decoder for Poolio IoT system
# Converts JSON messages to Python objects with snake_case attributes
#
# CircuitPython compatible at runtime (no dataclasses, no abc module).
# Type annotations are included for mypy/static analysis but are ignored
# by CircuitPython's stripped-down Python interpreter.

from __future__ import annotations

import re
try:
    from typing import Any
except ImportError:
    Any = None  # CircuitPython doesn't have typing module

from .envelope import parse_envelope
from .types import (
    Battery,
    Command,
    CommandResponse,
    ConfigUpdate,
    DisplayStatus,
    Error,
    FillStart,
    FillStop,
    Humidity,
    PoolStatus,
    ScheduleInfo,
    Temperature,
    ValveState,
    ValveStatus,
    WaterLevel,
)

# Pattern to find camelCase word boundaries
_CAMEL_PATTERN = re.compile(r"([a-z0-9])([A-Z])")


def camel_to_snake(name: str) -> str:
    """Convert camelCase string to snake_case.

    Args:
        name: String in camelCase format (e.g., "waterLevel")

    Returns:
        str: String in snake_case format (e.g., "water_level")
    """
    # Insert underscore before capital letters that follow lowercase
    result = _CAMEL_PATTERN.sub(r"\1_\2", name)
    return result.lower()


# Schema definitions for nested types
# Maps field name to the class that should be instantiated for that field
_NESTED_SCHEMAS: dict[str, dict[str, type[Any]]] = {
    "pool_status": {
        "water_level": WaterLevel,
        "temperature": Temperature,
        "battery": Battery,
    },
    "valve_status": {
        "valve": ValveState,
        "schedule": ScheduleInfo,
        "temperature": Temperature,
    },
    "display_status": {
        "local_temperature": Temperature,
        "local_humidity": Humidity,
    },
}

# Message type to class mapping
_MESSAGE_TYPES: dict[str, type[Any]] = {
    "pool_status": PoolStatus,
    "valve_status": ValveStatus,
    "display_status": DisplayStatus,
    "fill_start": FillStart,
    "fill_stop": FillStop,
    "command": Command,
    "command_response": CommandResponse,
    "error": Error,
    "config_update": ConfigUpdate,
}


# Fields that contain user data and should preserve their keys
_PRESERVE_KEYS_FIELDS = {"parameters", "context"}


def _convert_keys_to_snake(data: Any, preserve_keys: bool = False) -> Any:
    """Recursively convert dict keys from camelCase to snake_case.

    Args:
        data: Dict with camelCase keys, or list, or primitive
        preserve_keys: If True, don't convert keys in this dict or nested dicts
                      (used for user data like parameters, context)

    Returns:
        Same structure with snake_case keys (unless preserve_keys)
    """
    if isinstance(data, dict):
        if preserve_keys:
            # Preserve keys as-is but still recurse with preserve_keys
            return {k: _convert_keys_to_snake(v, preserve_keys=True) for k, v in data.items()}
        result: dict[str, Any] = {}
        for k, v in data.items():
            snake_key = camel_to_snake(k)
            # Check if this field should preserve keys in nested values
            should_preserve = snake_key in _PRESERVE_KEYS_FIELDS
            result[snake_key] = _convert_keys_to_snake(v, preserve_keys=should_preserve)
        return result
    elif isinstance(data, list):
        return [_convert_keys_to_snake(item, preserve_keys=preserve_keys) for item in data]
    else:
        return data


def _instantiate_nested(data: dict[str, Any], schema: dict[str, type[Any]]) -> dict[str, Any]:
    """Instantiate nested objects based on schema.

    Args:
        data: Dict with snake_case keys
        schema: Dict mapping field names to classes

    Returns:
        Dict with nested dicts replaced by class instances
    """
    result: dict[str, Any] = {}
    for key, value in data.items():
        if key in schema and isinstance(value, dict):
            # Instantiate the nested class
            cls = schema[key]
            result[key] = cls(**value)
        else:
            result[key] = value
    return result


def decode_message(json_str: str) -> Any:
    """Decode a JSON message string to appropriate Python object.

    Args:
        json_str: JSON string containing a message envelope

    Returns:
        Instance of appropriate message class (PoolStatus, Command, etc.)

    Raises:
        ValueError: If JSON is invalid, envelope fields missing, or unknown type
    """
    # Parse envelope and extract payload
    envelope, payload = parse_envelope(json_str)
    msg_type = envelope["type"]

    # Look up the message class
    if msg_type not in _MESSAGE_TYPES:
        raise ValueError(f"Unknown message type: {msg_type}")

    cls = _MESSAGE_TYPES[msg_type]

    # Convert payload keys to snake_case
    snake_payload = _convert_keys_to_snake(payload)

    # If this message type has nested schemas, instantiate nested objects
    if msg_type in _NESTED_SCHEMAS:
        snake_payload = _instantiate_nested(snake_payload, _NESTED_SCHEMAS[msg_type])

    # Instantiate and return the message object
    return cls(**snake_payload)
