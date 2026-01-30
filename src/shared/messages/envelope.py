# Message envelope functions for Poolio IoT system
# FR-MSG-001 and FR-MSG-002: Message structure and envelope fields
#
# CircuitPython compatible at runtime (no dataclasses, no abc module).
# Type annotations are included for mypy/static analysis but are ignored
# by CircuitPython's stripped-down Python interpreter.

from __future__ import annotations

import json
import re
try:
    from typing import Any
except ImportError:
    Any = None  # CircuitPython doesn't have typing module

# Try to import datetime (CPython/Blinka), fall back to time module
try:
    from datetime import datetime, timezone
except ImportError:
    datetime = None  # type: ignore[misc,assignment]
    timezone = None  # type: ignore[misc,assignment]

# Protocol version per FR-MSG-001
PROTOCOL_VERSION = 2

# Required envelope fields per FR-MSG-002
ENVELOPE_REQUIRED_FIELDS = ["version", "type", "deviceId", "timestamp", "payload"]

# Device ID validation pattern per FR-MSG-002
# Lowercase letters, numbers, hyphens only, 1-64 characters
DEVICE_ID_PATTERN = re.compile(r"^[a-z0-9-]+$")


def validate_device_id(device_id: str) -> None:
    """Validate device ID format per FR-MSG-002.

    Args:
        device_id: Device identifier string to validate

    Raises:
        ValueError: If device_id does not match required format

    Device ID requirements:
    - Lowercase letters, numbers, and hyphens only
    - 1-64 characters in length
    """
    if not device_id or len(device_id) > 64:
        raise ValueError("Device ID must be 1-64 characters")

    if not DEVICE_ID_PATTERN.match(device_id):
        raise ValueError("Device ID must contain only lowercase letters, numbers, and hyphens")


def _get_current_timestamp() -> str:
    """Get current timestamp in ISO 8601 format with timezone offset.

    Returns:
        str: ISO 8601 formatted timestamp (e.g., "2026-01-20T14:30:00-08:00")
    """
    if datetime is not None:
        # CPython/Blinka: use datetime with timezone
        now = datetime.now(timezone.utc).astimezone()
        # Format as ISO 8601 with timezone offset
        return now.isoformat(timespec="seconds")
    else:
        # CircuitPython fallback: would need adafruit_datetime
        # For now, raise an error - caller should provide timestamp
        raise NotImplementedError(
            "Timestamp generation requires datetime module. "
            "On CircuitPython, provide the timestamp parameter explicitly."
        )


def create_envelope(
    msg_type: str, device_id: str, payload: dict[str, Any], timestamp: str | None = None
) -> dict[str, Any]:
    """Create a message envelope dict per FR-MSG-001/002.

    Args:
        msg_type: Message type identifier (str, e.g., "pool_status")
        device_id: Unique device identifier (str, e.g., "pool-node-001")
        payload: Message payload dict
        timestamp: Optional ISO 8601 timestamp string. If not provided,
                   current time is used.

    Returns:
        dict: Message envelope with version, type, deviceId, timestamp, payload

    Raises:
        ValueError: If device_id format is invalid
    """
    validate_device_id(device_id)

    if timestamp is None:
        timestamp = _get_current_timestamp()

    return {
        "version": PROTOCOL_VERSION,
        "type": msg_type,
        "deviceId": device_id,
        "timestamp": timestamp,
        "payload": payload,
    }


def parse_envelope(json_str: str) -> tuple[dict[str, Any], dict[str, Any]]:
    """Parse a JSON message string into envelope and payload.

    Args:
        json_str: JSON string containing a message envelope

    Returns:
        tuple: (envelope_dict, payload_dict) where envelope_dict contains
               version, type, deviceId, timestamp (but not payload)

    Raises:
        ValueError: If JSON is invalid or required fields are missing
    """
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}") from e

    # Check required fields per FR-MSG-002
    for field in ENVELOPE_REQUIRED_FIELDS:
        if field not in data:
            raise ValueError(f"Envelope missing required field: {field}")

    # Extract payload and create envelope dict without payload
    payload = data["payload"]
    envelope = {
        "version": data["version"],
        "type": data["type"],
        "deviceId": data["deviceId"],
        "timestamp": data["timestamp"],
    }

    return envelope, payload
