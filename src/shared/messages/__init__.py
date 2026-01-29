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

__all__ = [
    # Envelope functions
    "PROTOCOL_VERSION",
    "create_envelope",
    "parse_envelope",
    "validate_device_id",
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
