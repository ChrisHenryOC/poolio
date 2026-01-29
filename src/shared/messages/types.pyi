# Type stubs for message type classes
# FR-MSG-004 through FR-MSG-013 payload types

from typing import Any

class WaterLevel:
    float_switch: bool
    confidence: float
    def __init__(self, float_switch: bool, confidence: float) -> None: ...
    def __eq__(self, other: object) -> bool: ...

class Temperature:
    value: float
    unit: str
    def __init__(self, value: float, unit: str = "fahrenheit") -> None: ...
    def __eq__(self, other: object) -> bool: ...

class Battery:
    voltage: float
    percentage: int
    def __init__(self, voltage: float, percentage: int) -> None: ...
    def __eq__(self, other: object) -> bool: ...

class Humidity:
    value: float
    unit: str
    def __init__(self, value: float, unit: str = "percent") -> None: ...
    def __eq__(self, other: object) -> bool: ...

class PoolStatus:
    water_level: WaterLevel
    temperature: Temperature
    battery: Battery
    reporting_interval: int
    def __init__(
        self,
        water_level: WaterLevel,
        temperature: Temperature,
        battery: Battery,
        reporting_interval: int,
    ) -> None: ...

class ValveState:
    state: str
    is_filling: bool
    current_fill_duration: int
    max_fill_duration: int
    def __init__(
        self,
        state: str,
        is_filling: bool,
        current_fill_duration: int,
        max_fill_duration: int,
    ) -> None: ...

class ScheduleInfo:
    enabled: bool
    start_time: str
    window_hours: int
    next_scheduled_fill: str | None
    def __init__(
        self,
        enabled: bool,
        start_time: str,
        window_hours: int,
        next_scheduled_fill: str | None = None,
    ) -> None: ...

class ValveStatus:
    valve: ValveState
    schedule: ScheduleInfo
    temperature: Temperature
    def __init__(
        self,
        valve: ValveState,
        schedule: ScheduleInfo,
        temperature: Temperature,
    ) -> None: ...

class DisplayStatus:
    local_temperature: Temperature
    local_humidity: Humidity
    def __init__(
        self,
        local_temperature: Temperature,
        local_humidity: Humidity,
    ) -> None: ...

class FillStart:
    fill_start_time: str
    scheduled_end_time: str
    max_duration: int
    trigger: str
    def __init__(
        self,
        fill_start_time: str,
        scheduled_end_time: str,
        max_duration: int,
        trigger: str,
    ) -> None: ...

class FillStop:
    fill_stop_time: str
    actual_duration: int
    reason: str
    def __init__(
        self,
        fill_stop_time: str,
        actual_duration: int,
        reason: str,
    ) -> None: ...

class Command:
    command: str
    parameters: dict[str, Any]
    source: str
    def __init__(
        self,
        command: str,
        parameters: dict[str, Any],
        source: str,
    ) -> None: ...

class CommandResponse:
    command_timestamp: str
    command: str
    status: str
    error_code: str | None
    error_message: str | None
    def __init__(
        self,
        command_timestamp: str,
        command: str,
        status: str,
        error_code: str | None = None,
        error_message: str | None = None,
    ) -> None: ...

class Error:
    error_code: str
    error_message: str
    severity: str
    context: dict[str, Any] | None
    def __init__(
        self,
        error_code: str,
        error_message: str,
        severity: str,
        context: dict[str, Any] | None,
    ) -> None: ...

class ConfigUpdate:
    config_key: str
    config_value: Any
    source: str
    def __init__(
        self,
        config_key: str,
        config_value: Any,
        source: str,
    ) -> None: ...

class ErrorCode:
    SENSOR_READ_FAILURE: str
    SENSOR_INIT_FAILURE: str
    SENSOR_OUT_OF_RANGE: str
    NETWORK_CONNECTION_FAILED: str
    NETWORK_TIMEOUT: str
    NETWORK_AUTH_FAILURE: str
    BUS_I2C_FAILURE: str
    BUS_ONEWIRE_FAILURE: str
    BUS_SPI_FAILURE: str
    CONFIG_INVALID_VALUE: str
    CONFIG_MISSING_REQUIRED: str
    CONFIG_SCHEMA_VIOLATION: str
    SYSTEM_MEMORY_LOW: str
    SYSTEM_WATCHDOG_RESET: str
    SYSTEM_UNEXPECTED_RESET: str
    VALVE_SAFETY_INTERLOCK: str
    VALVE_MAX_DURATION: str
    VALVE_ALREADY_ACTIVE: str
    VALVE_DATA_STALE: str
    VALVE_HARDWARE_FAILURE: str
