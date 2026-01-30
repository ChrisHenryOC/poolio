# Message validation functions for Poolio IoT system
# Issue #12: Simple required-field validation for CircuitPython
#
# CircuitPython compatible at runtime (no dataclasses, no abc module).
# Type annotations are included for mypy/static analysis but are ignored
# by CircuitPython's stripped-down Python interpreter.

from __future__ import annotations

import re
from typing import Any

# Constants for message size validation
MAX_MESSAGE_SIZE_BYTES = 4096  # 4KB per requirements

# Constants for timestamp freshness validation
COMMAND_MAX_AGE_SECONDS = 300  # 5 minutes for commands
STATUS_MAX_AGE_SECONDS = 900  # 15 minutes for status messages
MAX_FUTURE_SECONDS = 60  # 1 minute clock skew tolerance

# Message types that use command threshold (5 minutes)
COMMAND_TYPES = {"command", "command_response", "config_update"}

# Required envelope fields per FR-MSG-002
ENVELOPE_REQUIRED_FIELDS = ["version", "type", "deviceId", "timestamp", "payload"]

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
        # For error.context, allow None value but field must be present
        if field not in payload:
            errors.append(f"Payload missing required field '{field}' for {msg_type}")

    return (len(errors) == 0, errors)


def _parse_iso_timestamp(timestamp: str) -> int | None:
    """Parse ISO 8601 timestamp to Unix timestamp (seconds since epoch).

    Args:
        timestamp: ISO 8601 format timestamp string

    Returns:
        Unix timestamp in seconds, or None if parsing fails
    """
    match = ISO_TIMESTAMP_PATTERN.match(timestamp)
    if not match:
        return None

    year = int(match.group(1))
    month = int(match.group(2))
    day = int(match.group(3))
    hour = int(match.group(4))
    minute = int(match.group(5))
    second = int(match.group(6))
    tz_str = match.group(7)

    # Calculate days since epoch (1970-01-01)
    # Simplified calculation - doesn't account for leap seconds
    days_in_month = [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

    # Count leap years from 1970 to year-1
    def is_leap_year(y: int) -> bool:
        return y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)

    # Days from 1970 to start of year
    days = 0
    for y in range(1970, year):
        days += 366 if is_leap_year(y) else 365

    # Days in current year up to start of month
    if is_leap_year(year):
        days_in_month[2] = 29
    for m in range(1, month):
        days += days_in_month[m]

    # Days in current month
    days += day - 1

    # Convert to seconds
    unix_time = days * 86400 + hour * 3600 + minute * 60 + second

    # Apply timezone offset
    if tz_str == "Z":
        pass  # UTC, no offset
    else:
        # Parse offset like -08:00 or +05:30
        sign = 1 if tz_str[0] == "+" else -1
        tz_hour = int(tz_str[1:3])
        tz_min = int(tz_str[4:6])
        offset_seconds = sign * (tz_hour * 3600 + tz_min * 60)
        # Subtract offset to get UTC
        unix_time -= offset_seconds

    return unix_time


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
