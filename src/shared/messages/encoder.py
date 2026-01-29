# Message encoder for Poolio IoT system
# Converts Python message objects to JSON with camelCase keys
#
# CircuitPython compatible: no dataclasses, no type annotations in signatures
# Note: Type annotations are added for mypy/static analysis but the code
# itself does not depend on them for runtime behavior.

from __future__ import annotations

import json
from typing import Any

from .envelope import create_envelope


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
            result += part.capitalize()

    return result


def _encode_value(obj: Any) -> Any:
    """Recursively encode a value to JSON-ready format with camelCase keys.

    Args:
        obj: Python object to encode (can be message object, dict, list, or primitive)

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
        return [_encode_value(item) for item in obj]

    # Handle dicts - convert keys to camelCase and recurse into values
    if isinstance(obj, dict):
        return {snake_to_camel(k): _encode_value(v) for k, v in obj.items()}

    # Handle objects with __dict__ (our message classes)
    if hasattr(obj, "__dict__"):
        result: dict[str, Any] = {}
        for key, value in obj.__dict__.items():
            # Skip private attributes
            if key.startswith("_"):
                continue
            camel_key = snake_to_camel(key)
            result[camel_key] = _encode_value(value)
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
        ValueError: If device_id format is invalid
    """
    # Convert message object to dict with camelCase keys
    payload = _encode_value(message)

    # Create envelope with payload
    envelope = create_envelope(msg_type, device_id, payload, timestamp)

    # Convert to JSON string
    return json.dumps(envelope, separators=(",", ":"))
