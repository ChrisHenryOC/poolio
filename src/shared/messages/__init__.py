# Message type classes for Poolio IoT system
# CircuitPython compatible (no dataclasses, no type annotations in signatures)

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
