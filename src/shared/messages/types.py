# Message type classes for Poolio IoT system
# FR-MSG-004 through FR-MSG-013 payload types
#
# CircuitPython compatible: no dataclasses, no type annotations in signatures


class WaterLevel:
    """Water level measurement from float switch.

    Attributes:
        float_switch: Whether float switch indicates water is at level (bool)
        confidence: Confidence level of reading 0.0-1.0 (float)
    """

    def __init__(self, float_switch, confidence):
        self.float_switch = float_switch
        self.confidence = confidence

    def __eq__(self, other):
        if not isinstance(other, WaterLevel):
            return NotImplemented
        return self.float_switch == other.float_switch and self.confidence == other.confidence


class Temperature:
    """Temperature measurement.

    Attributes:
        value: Temperature value (float)
        unit: Temperature unit (str) - "fahrenheit" or "celsius"
    """

    def __init__(self, value, unit="fahrenheit"):
        self.value = value
        self.unit = unit

    def __eq__(self, other):
        if not isinstance(other, Temperature):
            return NotImplemented
        return self.value == other.value and self.unit == other.unit


class Battery:
    """Battery status.

    Attributes:
        voltage: Battery voltage (float)
        percentage: Battery charge percentage 0-100 (int)
    """

    def __init__(self, voltage, percentage):
        self.voltage = voltage
        self.percentage = percentage

    def __eq__(self, other):
        if not isinstance(other, Battery):
            return NotImplemented
        return self.voltage == other.voltage and self.percentage == other.percentage


class Humidity:
    """Humidity measurement.

    Attributes:
        value: Humidity value (float)
        unit: Humidity unit (str) - typically "percent"
    """

    def __init__(self, value, unit="percent"):
        self.value = value
        self.unit = unit

    def __eq__(self, other):
        if not isinstance(other, Humidity):
            return NotImplemented
        return self.value == other.value and self.unit == other.unit


# Composite types


class PoolStatus:
    """Pool node status message payload (FR-MSG-004).

    Attributes:
        water_level: Water level reading (WaterLevel)
        temperature: Temperature reading (Temperature)
        battery: Battery status (Battery)
        reporting_interval: Seconds between reports (int)
    """

    def __init__(self, water_level, temperature, battery, reporting_interval):
        self.water_level = water_level
        self.temperature = temperature
        self.battery = battery
        self.reporting_interval = reporting_interval


class ValveState:
    """Valve state information (FR-MSG-005).

    Attributes:
        state: Valve state (str) - "open" or "closed"
        is_filling: Whether a fill operation is in progress (bool)
        current_fill_duration: Seconds since fill started, 0 when not filling (int)
        max_fill_duration: Maximum fill duration in seconds (int)
    """

    def __init__(self, state, is_filling, current_fill_duration, max_fill_duration):
        self.state = state
        self.is_filling = is_filling
        self.current_fill_duration = current_fill_duration
        self.max_fill_duration = max_fill_duration


class ScheduleInfo:
    """Valve fill schedule information (FR-MSG-005).

    Attributes:
        enabled: Whether scheduling is enabled (bool)
        start_time: Schedule start time (str) - "HH:MM" format
        window_hours: Fill window duration in hours (int)
        next_scheduled_fill: Next scheduled fill time (str) - ISO 8601 format, or None
    """

    def __init__(self, enabled, start_time, window_hours, next_scheduled_fill=None):
        self.enabled = enabled
        self.start_time = start_time
        self.window_hours = window_hours
        self.next_scheduled_fill = next_scheduled_fill


class ValveStatus:
    """Valve node status message payload (FR-MSG-005).

    Attributes:
        valve: Valve state (ValveState)
        schedule: Schedule information (ScheduleInfo)
        temperature: Local temperature reading (Temperature)
    """

    def __init__(self, valve, schedule, temperature):
        self.valve = valve
        self.schedule = schedule
        self.temperature = temperature


class DisplayStatus:
    """Display node status message payload (FR-MSG-006).

    Attributes:
        local_temperature: Local temperature reading (Temperature)
        local_humidity: Local humidity reading (Humidity)
    """

    def __init__(self, local_temperature, local_humidity):
        self.local_temperature = local_temperature
        self.local_humidity = local_humidity


# Event types


class FillStart:
    """Fill operation started event (FR-MSG-007).

    Attributes:
        fill_start_time: Fill start time (str) - ISO 8601 format
        scheduled_end_time: Scheduled end time (str) - ISO 8601 format
        max_duration: Maximum fill duration in seconds (int)
        trigger: What triggered the fill (str) - "scheduled", "manual", or "low_water"
    """

    def __init__(self, fill_start_time, scheduled_end_time, max_duration, trigger):
        self.fill_start_time = fill_start_time
        self.scheduled_end_time = scheduled_end_time
        self.max_duration = max_duration
        self.trigger = trigger


class FillStop:
    """Fill operation stopped event (FR-MSG-008).

    Attributes:
        fill_stop_time: Fill stop time (str) - ISO 8601 format
        actual_duration: Actual fill duration in seconds (int)
        reason: Why fill stopped (str) - "water_full", "max_duration", "manual",
                "error", or "window_closed"
    """

    def __init__(self, fill_stop_time, actual_duration, reason):
        self.fill_stop_time = fill_stop_time
        self.actual_duration = actual_duration
        self.reason = reason


# Control types


class Command:
    """Remote command message payload (FR-MSG-009).

    Attributes:
        command: Command name (str) - "valve_start", "valve_stop",
                 "device_reset", or "set_config"
        parameters: Command parameters (dict)
        source: Origin of command (str) - device ID or "cloud"
    """

    def __init__(self, command, parameters, source):
        self.command = command
        self.parameters = parameters
        self.source = source


class CommandResponse:
    """Command response message payload (FR-MSG-013).

    Attributes:
        command_timestamp: Original command timestamp (str) - ISO 8601 format
        command: Command that was executed (str)
        status: Execution result (str) - "success", "failed", or "rejected"
        error_code: Error code if failed/rejected (str or None)
        error_message: Error description if failed/rejected (str or None)
    """

    def __init__(self, command_timestamp, command, status, error_code=None, error_message=None):
        self.command_timestamp = command_timestamp
        self.command = command
        self.status = status
        self.error_code = error_code
        self.error_message = error_message


class Error:
    """Error report message payload (FR-MSG-011).

    Attributes:
        error_code: Standard error code (str) - see ErrorCode class
        error_message: Human-readable error description (str)
        severity: Error severity (str) - "debug", "info", "warning",
                  "error", or "critical"
        context: Additional diagnostic information (dict or None)
    """

    def __init__(self, error_code, error_message, severity, context):
        self.error_code = error_code
        self.error_message = error_message
        self.severity = severity
        self.context = context


class ConfigUpdate:
    """Configuration update message payload (FR-MSG-012).

    Attributes:
        config_key: Configuration parameter being updated (str)
        config_value: New value for the parameter (any)
        source: Origin of update (str) - "cloud", "local", or "default"
    """

    def __init__(self, config_key, config_value, source):
        self.config_key = config_key
        self.config_value = config_value
        self.source = source


# Error code constants


class ErrorCode:
    """Standard error codes for FR-MSG-011.

    Error codes are organized by category:
    - SENSOR_*: Sensor-related errors
    - NETWORK_*: Network connectivity errors
    - BUS_*: Hardware bus errors
    - CONFIG_*: Configuration errors
    - SYSTEM_*: System-level errors
    - VALVE_*: Valve operation errors
    """

    # Sensor errors
    SENSOR_READ_FAILURE = "SENSOR_READ_FAILURE"
    SENSOR_INIT_FAILURE = "SENSOR_INIT_FAILURE"
    SENSOR_OUT_OF_RANGE = "SENSOR_OUT_OF_RANGE"

    # Network errors
    NETWORK_CONNECTION_FAILED = "NETWORK_CONNECTION_FAILED"
    NETWORK_TIMEOUT = "NETWORK_TIMEOUT"
    NETWORK_AUTH_FAILURE = "NETWORK_AUTH_FAILURE"

    # Bus errors
    BUS_I2C_FAILURE = "BUS_I2C_FAILURE"
    BUS_ONEWIRE_FAILURE = "BUS_ONEWIRE_FAILURE"
    BUS_SPI_FAILURE = "BUS_SPI_FAILURE"

    # Config errors
    CONFIG_INVALID_VALUE = "CONFIG_INVALID_VALUE"
    CONFIG_MISSING_REQUIRED = "CONFIG_MISSING_REQUIRED"
    CONFIG_SCHEMA_VIOLATION = "CONFIG_SCHEMA_VIOLATION"

    # System errors
    SYSTEM_MEMORY_LOW = "SYSTEM_MEMORY_LOW"
    SYSTEM_WATCHDOG_RESET = "SYSTEM_WATCHDOG_RESET"
    SYSTEM_UNEXPECTED_RESET = "SYSTEM_UNEXPECTED_RESET"

    # Valve errors
    VALVE_SAFETY_INTERLOCK = "VALVE_SAFETY_INTERLOCK"
    VALVE_MAX_DURATION = "VALVE_MAX_DURATION"
    VALVE_ALREADY_ACTIVE = "VALVE_ALREADY_ACTIVE"
    VALVE_DATA_STALE = "VALVE_DATA_STALE"
    VALVE_HARDWARE_FAILURE = "VALVE_HARDWARE_FAILURE"
