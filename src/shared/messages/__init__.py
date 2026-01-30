# Message type classes and envelope functions for Poolio IoT system
# CircuitPython compatible (no dataclasses, no type annotations in signatures)

from .decoder import camel_to_snake, decode_message
from .encoder import encode_message, snake_to_camel
from .envelope import (
    PROTOCOL_VERSION,
    create_envelope,
    parse_envelope,
    validate_device_id,
)
from .types import (
    Battery,
    # Control types
    Command,
    CommandResponse,
    ConfigUpdate,
    DisplayStatus,
    Error,
    # Constants
    ErrorCode,
    # Event types
    FillStart,
    FillStop,
    Humidity,
    # Composite types
    PoolStatus,
    ScheduleInfo,
    Temperature,
    ValveState,
    ValveStatus,
    # Base types
    WaterLevel,
)
from .validator import (
    COMMAND_MAX_AGE_SECONDS,
    COMMAND_TYPES,
    MAX_FUTURE_SECONDS,
    MAX_MESSAGE_SIZE_BYTES,
    STATUS_MAX_AGE_SECONDS,
    validate_envelope,
    validate_message_size,
    validate_payload,
    validate_timestamp_freshness,
)

__all__ = [
    # Envelope functions
    "PROTOCOL_VERSION",
    "create_envelope",
    "parse_envelope",
    "validate_device_id",
    # Validation functions
    "validate_envelope",
    "validate_message_size",
    "validate_payload",
    "validate_timestamp_freshness",
    # Validation constants
    "MAX_MESSAGE_SIZE_BYTES",
    "COMMAND_MAX_AGE_SECONDS",
    "STATUS_MAX_AGE_SECONDS",
    "MAX_FUTURE_SECONDS",
    "COMMAND_TYPES",
    # Encoder/decoder functions
    "encode_message",
    "decode_message",
    "snake_to_camel",
    "camel_to_snake",
    # Base types
    "WaterLevel",
    "Temperature",
    "Battery",
    "Humidity",
    # Composite types
    "PoolStatus",
    "ValveState",
    "ScheduleInfo",
    "ValveStatus",
    "DisplayStatus",
    # Event types
    "FillStart",
    "FillStop",
    # Control types
    "Command",
    "CommandResponse",
    "Error",
    "ConfigUpdate",
    # Constants
    "ErrorCode",
]
