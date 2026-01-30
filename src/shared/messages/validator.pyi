# Type stubs for message validation functions

from typing import Any

MAX_MESSAGE_SIZE_BYTES: int
COMMAND_MAX_AGE_SECONDS: int
STATUS_MAX_AGE_SECONDS: int
MAX_FUTURE_SECONDS: int
COMMAND_TYPES: set[str]
ENVELOPE_REQUIRED_FIELDS: list[str]
PAYLOAD_REQUIRED_FIELDS: dict[str, list[str]]

def validate_envelope(envelope: dict[str, Any]) -> tuple[bool, list[str]]: ...
def validate_message_size(json_str: str) -> tuple[bool, list[str]]: ...
def validate_payload(msg_type: str, payload: dict[str, Any]) -> tuple[bool, list[str]]: ...
def validate_timestamp_freshness(
    timestamp: str, msg_type: str, current_time: int | None = None
) -> tuple[bool, list[str]]: ...
