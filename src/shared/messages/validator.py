# Message validation functions for Poolio IoT system
# Issue #12: Simple required-field validation for CircuitPython
#
# CircuitPython compatible at runtime (no dataclasses, no abc module).
# Type annotations are included for mypy/static analysis but are ignored
# by CircuitPython's stripped-down Python interpreter.

from __future__ import annotations

import re
from typing import Any

from .envelope import ENVELOPE_REQUIRED_FIELDS

# Try to import datetime (CPython/Blinka), fall back to adafruit_datetime
try:
    from datetime import datetime
except ImportError:
    from adafruit_datetime import datetime  # type: ignore[import-not-found,no-redef]

# Constants for message size validation
MAX_MESSAGE_SIZE_BYTES = 4096  # 4KB per requirements

# Constants for timestamp freshness validation
COMMAND_MAX_AGE_SECONDS = 300  # 5 minutes for commands
STATUS_MAX_AGE_SECONDS = 900  # 15 minutes for status messages
MAX_FUTURE_SECONDS = 60  # 1 minute clock skew tolerance

# Message types that use command threshold (5 minutes)
COMMAND_TYPES = {"command", "command_response", "config_update"}

# Required payload fields per message type (camelCase for JSON)
PAYLOAD_REQUIRED_FIELDS: dict[str, list[str]] = {
    "pool_status": ["waterLevel", "temperature", "battery", "reportingInterval"],
    "valve_status": ["valve", "schedule", "temperature"],
    "display_status": ["localTemperature", "localHumidity"],
    "fill_start": ["fillStartTime", "scheduledEndTime", "maxDuration", "trigger"],
    "fill_stop": ["fillStopTime", "actualDuration", "reason"],
    "command": ["command", "parameters", "source"],
    "command_response": ["commandTimestamp", "command", "status"],
    "error": ["errorCode", "errorMessage", "severity", "context"],
    "config_update": ["configKey", "configValue", "source"],
}

# ISO 8601 timestamp pattern with timezone offset
# Matches: 2026-01-20T14:30:00-08:00 or 2026-01-20T14:30:00+00:00 or 2026-01-20T14:30:00Z
ISO_TIMESTAMP_PATTERN = re.compile(
    r"^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(Z|[+-]\d{2}:\d{2})$"
)


def validate_envelope(envelope: dict[str, Any]) -> tuple[bool, list[str]]:
    """Validate required envelope fields per FR-MSG-002.

    Args:
        envelope: dict with version, type, deviceId, timestamp, payload

    Returns:
        tuple: (valid: bool, errors: list of str)
    """
    errors = []

    for field in ENVELOPE_REQUIRED_FIELDS:
        if field not in envelope:
            errors.append(f"Envelope missing required field: {field}")

    return (len(errors) == 0, errors)


def validate_message_size(json_str: str) -> tuple[bool, list[str]]:
    """Validate message size does not exceed 4KB.

    Args:
        json_str: JSON string to validate

    Returns:
        tuple: (valid: bool, errors: list of str)
    """
    size_bytes = len(json_str.encode("utf-8"))

    if size_bytes > MAX_MESSAGE_SIZE_BYTES:
        return (
            False,
            [
                f"Message size {size_bytes} bytes exceeds maximum {MAX_MESSAGE_SIZE_BYTES} bytes (4KB)"
            ],
        )

    return (True, [])


def validate_payload(msg_type: str, payload: dict[str, Any]) -> tuple[bool, list[str]]:
    """Validate required payload fields for a message type.

    Args:
        msg_type: str message type (e.g., "pool_status")
        payload: dict payload to validate

    Returns:
        tuple: (valid: bool, errors: list of str)
    """
    if msg_type not in PAYLOAD_REQUIRED_FIELDS:
        return (False, [f"Unknown message type: {msg_type}"])

    required_fields = PAYLOAD_REQUIRED_FIELDS[msg_type]
    errors = []

    for field in required_fields:
        if field not in payload:
            errors.append(f"Payload missing required field '{field}' for {msg_type}")

    return (len(errors) == 0, errors)


def _parse_iso_timestamp(timestamp: str) -> int | None:
    """Parse ISO 8601 timestamp to Unix timestamp (seconds since epoch).

    Uses datetime.fromisoformat() for parsing with additional security
    validations for pre-epoch timestamps and extreme timezone offsets.

    Args:
        timestamp: ISO 8601 format timestamp string

    Returns:
        Unix timestamp in seconds, or None if parsing fails
    """
    try:
        # Validate format with regex first (ensures consistent format)
        match = ISO_TIMESTAMP_PATTERN.match(timestamp)
        if not match:
            return None

        tz_str = match.group(7)

        # Validate timezone offset bounds before parsing
        if tz_str != "Z":
            tz_hour = int(tz_str[1:3])
            tz_min = int(tz_str[4:6])
            # Reject invalid minutes (must be 0-59)
            if tz_min >= 60:
                return None
            # Reject extreme offsets (UTC-12 to UTC+14)
            sign = 1 if tz_str[0] == "+" else -1
            if sign == 1 and tz_hour > 14:
                return None
            if sign == -1 and tz_hour > 12:
                return None

        # Handle Z suffix (Python < 3.11 doesn't support Z in fromisoformat)
        ts = timestamp
        if ts.endswith("Z"):
            ts = ts[:-1] + "+00:00"

        dt = datetime.fromisoformat(ts)

        # Security validation: reject pre-epoch timestamps
        if dt.year < 1970:
            return None

        return int(dt.timestamp())
    except (ValueError, OSError, OverflowError):
        return None


def validate_timestamp_freshness(
    timestamp: str, msg_type: str, current_time: int | None = None
) -> tuple[bool, list[str]]:
    """Validate timestamp is not too old or in the future.

    Args:
        timestamp: ISO 8601 timestamp string
        msg_type: str message type to determine age limit
        current_time: Unix timestamp (seconds since epoch). If None, uses time.time().

    Returns:
        tuple: (valid: bool, errors: list of str)
    """
    # Parse the message timestamp
    msg_time = _parse_iso_timestamp(timestamp)
    if msg_time is None:
        return (False, [f"Invalid timestamp format: {timestamp}"])

    # Get current time if not provided
    if current_time is None:
        import time

        current_time = int(time.time())

    # Calculate age (positive = message is in past, negative = message is in future)
    age_seconds = current_time - msg_time

    # Check if message is too far in the future
    if age_seconds < -MAX_FUTURE_SECONDS:
        return (
            False,
            [
                f"Message timestamp is {-age_seconds} seconds in the future (max allowed: {MAX_FUTURE_SECONDS})"
            ],
        )

    # Determine max age based on message type
    if msg_type in COMMAND_TYPES:
        max_age = COMMAND_MAX_AGE_SECONDS
        threshold_desc = "5 minutes"
    else:
        max_age = STATUS_MAX_AGE_SECONDS
        threshold_desc = "15 minutes"

    # Check if message is too old
    if age_seconds > max_age:
        return (
            False,
            [
                f"Message timestamp is {age_seconds} seconds old (max allowed: {max_age} seconds / {threshold_desc})"
            ],
        )

    return (True, [])
