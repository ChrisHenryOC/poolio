# Message encoder for Poolio IoT system
# Converts Python message objects to JSON with camelCase keys
#
# CircuitPython compatible at runtime (no dataclasses, no abc module).
# Type annotations are included for mypy/static analysis but are ignored
# by CircuitPython's stripped-down Python interpreter.

from __future__ import annotations

import json
try:
    from typing import Any
except ImportError:
    Any = None  # CircuitPython doesn't have typing module

from .envelope import create_envelope

# Fields that contain user data and should preserve their keys
_PRESERVE_KEYS_FIELDS = {"parameters", "context"}


def snake_to_camel(name: str) -> str:
    """Convert snake_case string to camelCase.

    Args:
        name: String in snake_case format (e.g., "water_level")

    Returns:
        str: String in camelCase format (e.g., "waterLevel")
    """
    parts = name.split("_")
    if not parts:
        return name

    # First part stays lowercase, rest get capitalized
    result = parts[0]
    for part in parts[1:]:
        if part:  # Skip empty parts from trailing underscores
            # Manual capitalize for CircuitPython compatibility
            result += part[0].upper() + part[1:] if part else ""

    return result


def _encode_value(obj: Any, preserve_keys: bool = False) -> Any:
    """Recursively encode a value to JSON-ready format with camelCase keys.

    Args:
        obj: Python object to encode (can be message object, dict, list, or primitive)
        preserve_keys: If True, don't convert keys in this dict or nested dicts
                      (used for user data like parameters, context)

    Returns:
        JSON-ready value (dict, list, or primitive)
    """
    # Handle None
    if obj is None:
        return None

    # Handle primitives
    if isinstance(obj, (bool, int, float, str)):
        return obj

    # Handle lists
    if isinstance(obj, list):
        return [_encode_value(item, preserve_keys=preserve_keys) for item in obj]

    # Handle dicts - convert keys to camelCase unless preserve_keys is set
    if isinstance(obj, dict):
        if preserve_keys:
            # Preserve keys as-is for user data fields
            return {k: _encode_value(v, preserve_keys=True) for k, v in obj.items()}
        return {snake_to_camel(k): _encode_value(v) for k, v in obj.items()}

    # Handle objects with __dict__ (our message classes)
    if hasattr(obj, "__dict__"):
        result: dict[str, Any] = {}
        for key, value in obj.__dict__.items():
            # Skip private attributes
            if key.startswith("_"):
                continue
            camel_key = snake_to_camel(key)
            # Check if this field should preserve keys in nested values
            should_preserve = key in _PRESERVE_KEYS_FIELDS
            result[camel_key] = _encode_value(value, preserve_keys=should_preserve)
        return result

    # Fallback for unknown types - try to convert to string
    return str(obj)


def encode_message(
    message: Any, device_id: str, msg_type: str, timestamp: str | None = None
) -> str:
    """Encode a message object to JSON string with envelope.

    Args:
        message: Python message object (e.g., PoolStatus, Command)
        device_id: Device identifier string (e.g., "pool-node-001")
        msg_type: Message type string (e.g., "pool_status")
        timestamp: Optional ISO 8601 timestamp. If not provided, current time is used.

    Returns:
        str: JSON string with message envelope and payload

    Raises:
        ValueError: If device_id format is invalid or msg_type is empty
    """
    # Validate msg_type
    if not msg_type:
        raise ValueError("msg_type cannot be empty")

    # Convert message object to dict with camelCase keys
    payload = _encode_value(message)

    # Create envelope with payload
    envelope = create_envelope(msg_type, device_id, payload, timestamp)

    # Convert to JSON string
    return json.dumps(envelope, separators=(",", ":"))
