# Unit tests for message type classes
# Tests for FR-MSG-004 through FR-MSG-013 payload types


class TestWaterLevel:
    """Tests for WaterLevel class."""

    def test_create_with_all_fields(self) -> None:
        """WaterLevel requires floatSwitch and confidence."""
        from shared.messages.types import WaterLevel

        water_level = WaterLevel(float_switch=True, confidence=0.95)

        assert water_level.float_switch is True
        assert water_level.confidence == 0.95

    def test_create_with_false_float_switch(self) -> None:
        """WaterLevel works with False floatSwitch."""
        from shared.messages.types import WaterLevel

        water_level = WaterLevel(float_switch=False, confidence=0.8)

        assert water_level.float_switch is False
        assert water_level.confidence == 0.8


class TestTemperature:
    """Tests for Temperature class."""

    def test_create_with_value_and_unit(self) -> None:
        """Temperature requires value and optional unit."""
        from shared.messages.types import Temperature

        temp = Temperature(value=78.5, unit="fahrenheit")

        assert temp.value == 78.5
        assert temp.unit == "fahrenheit"

    def test_default_unit_is_fahrenheit(self) -> None:
        """Temperature defaults to fahrenheit unit."""
        from shared.messages.types import Temperature

        temp = Temperature(value=72.0)

        assert temp.value == 72.0
        assert temp.unit == "fahrenheit"

    def test_celsius_unit(self) -> None:
        """Temperature supports celsius unit."""
        from shared.messages.types import Temperature

        temp = Temperature(value=25.0, unit="celsius")

        assert temp.value == 25.0
        assert temp.unit == "celsius"


class TestBattery:
    """Tests for Battery class."""

    def test_create_with_all_fields(self) -> None:
        """Battery requires voltage and percentage."""
        from shared.messages.types import Battery

        battery = Battery(voltage=3.85, percentage=72)

        assert battery.voltage == 3.85
        assert battery.percentage == 72

    def test_full_battery(self) -> None:
        """Battery works at 100%."""
        from shared.messages.types import Battery

        battery = Battery(voltage=4.2, percentage=100)

        assert battery.voltage == 4.2
        assert battery.percentage == 100

    def test_low_battery(self) -> None:
        """Battery works at low levels."""
        from shared.messages.types import Battery

        battery = Battery(voltage=3.3, percentage=5)

        assert battery.voltage == 3.3
        assert battery.percentage == 5


class TestHumidity:
    """Tests for Humidity class."""

    def test_create_with_value_and_unit(self) -> None:
        """Humidity requires value and optional unit."""
        from shared.messages.types import Humidity

        humidity = Humidity(value=45.0, unit="percent")

        assert humidity.value == 45.0
        assert humidity.unit == "percent"

    def test_default_unit_is_percent(self) -> None:
        """Humidity defaults to percent unit."""
        from shared.messages.types import Humidity

        humidity = Humidity(value=60.0)

        assert humidity.value == 60.0
        assert humidity.unit == "percent"


class TestPoolStatus:
    """Tests for PoolStatus class (FR-MSG-004)."""

    def test_create_with_all_fields(self) -> None:
        """PoolStatus requires waterLevel, temperature, battery, reportingInterval."""
        from shared.messages.types import (
            Battery,
            PoolStatus,
            Temperature,
            WaterLevel,
        )

        water_level = WaterLevel(float_switch=True, confidence=0.95)
        temp = Temperature(value=78.5)
        battery = Battery(voltage=3.85, percentage=72)

        status = PoolStatus(
            water_level=water_level,
            temperature=temp,
            battery=battery,
            reporting_interval=120,
        )

        assert status.water_level is water_level
        assert status.temperature is temp
        assert status.battery is battery
        assert status.reporting_interval == 120


class TestValveState:
    """Tests for ValveState class (FR-MSG-005)."""

    def test_create_closed_valve(self) -> None:
        """ValveState for a closed, idle valve."""
        from shared.messages.types import ValveState

        valve = ValveState(
            state="closed",
            is_filling=False,
            current_fill_duration=None,
            max_fill_duration=540,
        )

        assert valve.state == "closed"
        assert valve.is_filling is False
        assert valve.current_fill_duration is None
        assert valve.max_fill_duration == 540

    def test_create_open_filling_valve(self) -> None:
        """ValveState for an open, filling valve."""
        from shared.messages.types import ValveState

        valve = ValveState(
            state="open",
            is_filling=True,
            current_fill_duration=120,
            max_fill_duration=540,
        )

        assert valve.state == "open"
        assert valve.is_filling is True
        assert valve.current_fill_duration == 120
        assert valve.max_fill_duration == 540


class TestScheduleInfo:
    """Tests for ScheduleInfo class (FR-MSG-005)."""

    def test_create_with_all_fields(self) -> None:
        """ScheduleInfo requires startTime, windowHours, nextFillTime, nextCheckTime."""
        from shared.messages.types import ScheduleInfo

        schedule = ScheduleInfo(
            start_time="09:00",
            window_hours=2,
            next_fill_time="2026-01-20T09:00:00-08:00",
            next_check_time="2026-01-20T08:55:00-08:00",
        )

        assert schedule.start_time == "09:00"
        assert schedule.window_hours == 2
        assert schedule.next_fill_time == "2026-01-20T09:00:00-08:00"
        assert schedule.next_check_time == "2026-01-20T08:55:00-08:00"


class TestValveStatus:
    """Tests for ValveStatus class (FR-MSG-005)."""

    def test_create_with_all_fields(self) -> None:
        """ValveStatus requires valve, schedule, temperature."""
        from shared.messages.types import (
            ScheduleInfo,
            Temperature,
            ValveState,
            ValveStatus,
        )

        valve = ValveState(
            state="closed",
            is_filling=False,
            current_fill_duration=None,
            max_fill_duration=540,
        )
        schedule = ScheduleInfo(
            start_time="09:00",
            window_hours=2,
            next_fill_time="2026-01-20T09:00:00-08:00",
            next_check_time="2026-01-20T08:55:00-08:00",
        )
        temp = Temperature(value=72.0)

        status = ValveStatus(valve=valve, schedule=schedule, temperature=temp)

        assert status.valve is valve
        assert status.schedule is schedule
        assert status.temperature is temp


class TestDisplayStatus:
    """Tests for DisplayStatus class (FR-MSG-006)."""

    def test_create_with_all_fields(self) -> None:
        """DisplayStatus requires localTemperature and localHumidity."""
        from shared.messages.types import DisplayStatus, Humidity, Temperature

        temp = Temperature(value=72.5)
        humidity = Humidity(value=45.0)

        status = DisplayStatus(local_temperature=temp, local_humidity=humidity)

        assert status.local_temperature is temp
        assert status.local_humidity is humidity


class TestFillStart:
    """Tests for FillStart class (FR-MSG-007)."""

    def test_create_scheduled_fill(self) -> None:
        """FillStart for a scheduled fill operation."""
        from shared.messages.types import FillStart

        fill = FillStart(
            fill_start_time="2026-01-20T09:00:00-08:00",
            scheduled_end_time="2026-01-20T09:09:00-08:00",
            max_duration=540,
            trigger="scheduled",
        )

        assert fill.fill_start_time == "2026-01-20T09:00:00-08:00"
        assert fill.scheduled_end_time == "2026-01-20T09:09:00-08:00"
        assert fill.max_duration == 540
        assert fill.trigger == "scheduled"

    def test_create_manual_fill(self) -> None:
        """FillStart for a manual fill operation."""
        from shared.messages.types import FillStart

        fill = FillStart(
            fill_start_time="2026-01-20T14:30:00-08:00",
            scheduled_end_time="2026-01-20T14:39:00-08:00",
            max_duration=540,
            trigger="manual",
        )

        assert fill.trigger == "manual"

    def test_create_low_water_fill(self) -> None:
        """FillStart for a low water triggered fill operation."""
        from shared.messages.types import FillStart

        fill = FillStart(
            fill_start_time="2026-01-20T10:15:00-08:00",
            scheduled_end_time="2026-01-20T10:24:00-08:00",
            max_duration=540,
            trigger="low_water",
        )

        assert fill.trigger == "low_water"


class TestFillStop:
    """Tests for FillStop class (FR-MSG-008)."""

    def test_create_water_full_stop(self) -> None:
        """FillStop when water level is full."""
        from shared.messages.types import FillStop

        fill = FillStop(
            fill_stop_time="2026-01-20T09:05:30-08:00",
            actual_duration=330,
            reason="water_full",
        )

        assert fill.fill_stop_time == "2026-01-20T09:05:30-08:00"
        assert fill.actual_duration == 330
        assert fill.reason == "water_full"

    def test_create_max_duration_stop(self) -> None:
        """FillStop when max duration reached."""
        from shared.messages.types import FillStop

        fill = FillStop(
            fill_stop_time="2026-01-20T09:09:00-08:00",
            actual_duration=540,
            reason="max_duration",
        )

        assert fill.reason == "max_duration"

    def test_create_manual_stop(self) -> None:
        """FillStop when manually stopped."""
        from shared.messages.types import FillStop

        fill = FillStop(
            fill_stop_time="2026-01-20T09:03:00-08:00",
            actual_duration=180,
            reason="manual",
        )

        assert fill.reason == "manual"

    def test_create_error_stop(self) -> None:
        """FillStop due to error."""
        from shared.messages.types import FillStop

        fill = FillStop(
            fill_stop_time="2026-01-20T09:01:00-08:00",
            actual_duration=60,
            reason="error",
        )

        assert fill.reason == "error"

    def test_create_window_closed_stop(self) -> None:
        """FillStop when fill window closed."""
        from shared.messages.types import FillStop

        fill = FillStop(
            fill_stop_time="2026-01-20T11:00:00-08:00",
            actual_duration=120,
            reason="window_closed",
        )

        assert fill.reason == "window_closed"


class TestCommand:
    """Tests for Command class (FR-MSG-009)."""

    def test_create_valve_start_command(self) -> None:
        """Command for starting valve."""
        from shared.messages.types import Command

        cmd = Command(
            command="valve_start",
            parameters={"maxDuration": 540},
            source="display-node-001",
        )

        assert cmd.command == "valve_start"
        assert cmd.parameters == {"maxDuration": 540}
        assert cmd.source == "display-node-001"

    def test_create_valve_stop_command(self) -> None:
        """Command for stopping valve."""
        from shared.messages.types import Command

        cmd = Command(
            command="valve_stop",
            parameters={},
            source="cloud",
        )

        assert cmd.command == "valve_stop"
        assert cmd.parameters == {}

    def test_create_device_reset_command(self) -> None:
        """Command for device reset."""
        from shared.messages.types import Command

        cmd = Command(
            command="device_reset",
            parameters={},
            source="cloud",
        )

        assert cmd.command == "device_reset"

    def test_create_set_config_command(self) -> None:
        """Command for setting configuration."""
        from shared.messages.types import Command

        cmd = Command(
            command="set_config",
            parameters={"key": "valveStartTime", "value": "10:00"},
            source="cloud",
        )

        assert cmd.command == "set_config"
        assert cmd.parameters["key"] == "valveStartTime"


class TestCommandResponse:
    """Tests for CommandResponse class (FR-MSG-013)."""

    def test_create_success_response(self) -> None:
        """CommandResponse for successful command."""
        from shared.messages.types import CommandResponse

        resp = CommandResponse(
            command_timestamp="2026-01-20T09:00:00-08:00",
            command="valve_start",
            status="success",
            error_code=None,
            error_message=None,
        )

        assert resp.command_timestamp == "2026-01-20T09:00:00-08:00"
        assert resp.command == "valve_start"
        assert resp.status == "success"
        assert resp.error_code is None
        assert resp.error_message is None

    def test_create_failed_response(self) -> None:
        """CommandResponse for failed command."""
        from shared.messages.types import CommandResponse

        resp = CommandResponse(
            command_timestamp="2026-01-20T09:00:00-08:00",
            command="valve_start",
            status="failed",
            error_code="VALVE_ALREADY_ACTIVE",
            error_message="Fill already in progress",
        )

        assert resp.status == "failed"
        assert resp.error_code == "VALVE_ALREADY_ACTIVE"
        assert resp.error_message == "Fill already in progress"

    def test_create_rejected_response(self) -> None:
        """CommandResponse for rejected command."""
        from shared.messages.types import CommandResponse

        resp = CommandResponse(
            command_timestamp="2026-01-20T09:00:00-08:00",
            command="valve_start",
            status="rejected",
            error_code="VALVE_SAFETY_INTERLOCK",
            error_message="Safety interlock active",
        )

        assert resp.status == "rejected"


class TestError:
    """Tests for Error class (FR-MSG-011)."""

    def test_create_warning_error(self) -> None:
        """Error with warning severity."""
        from shared.messages.types import Error

        error = Error(
            error_code="SENSOR_READ_FAILURE",
            error_message="Failed to read temperature sensor after 3 retries",
            severity="warning",
            context={"sensor": "DS18X20", "retryCount": 3},
        )

        assert error.error_code == "SENSOR_READ_FAILURE"
        assert error.error_message == "Failed to read temperature sensor after 3 retries"
        assert error.severity == "warning"
        assert error.context == {"sensor": "DS18X20", "retryCount": 3}

    def test_create_error_severity(self) -> None:
        """Error with error severity."""
        from shared.messages.types import Error

        error = Error(
            error_code="NETWORK_CONNECTION_FAILED",
            error_message="Failed to connect to WiFi",
            severity="error",
            context={"ssid": "PoolNetwork"},
        )

        assert error.severity == "error"

    def test_create_critical_error(self) -> None:
        """Error with critical severity."""
        from shared.messages.types import Error

        error = Error(
            error_code="SYSTEM_WATCHDOG_RESET",
            error_message="Device reset by watchdog",
            severity="critical",
            context=None,
        )

        assert error.severity == "critical"
        assert error.context is None

    def test_create_info_error(self) -> None:
        """Error with info severity."""
        from shared.messages.types import Error

        error = Error(
            error_code="SENSOR_OUT_OF_RANGE",
            error_message="Temperature reading unusually high",
            severity="info",
            context={"value": 150.0},
        )

        assert error.severity == "info"

    def test_create_debug_error(self) -> None:
        """Error with debug severity."""
        from shared.messages.types import Error

        error = Error(
            error_code="BUS_I2C_FAILURE",
            error_message="I2C NAK received",
            severity="debug",
            context={"address": "0x68"},
        )

        assert error.severity == "debug"


class TestConfigUpdate:
    """Tests for ConfigUpdate class (FR-MSG-012)."""

    def test_create_cloud_config_update(self) -> None:
        """ConfigUpdate from cloud source."""
        from shared.messages.types import ConfigUpdate

        config = ConfigUpdate(
            config_key="valveStartTime",
            config_value="10:00",
            source="cloud",
        )

        assert config.config_key == "valveStartTime"
        assert config.config_value == "10:00"
        assert config.source == "cloud"

    def test_create_local_config_update(self) -> None:
        """ConfigUpdate from local source."""
        from shared.messages.types import ConfigUpdate

        config = ConfigUpdate(
            config_key="reportingInterval",
            config_value=120,
            source="local",
        )

        assert config.config_key == "reportingInterval"
        assert config.config_value == 120
        assert config.source == "local"

    def test_create_default_config_update(self) -> None:
        """ConfigUpdate from default source."""
        from shared.messages.types import ConfigUpdate

        config = ConfigUpdate(
            config_key="maxFillDuration",
            config_value=540,
            source="default",
        )

        assert config.source == "default"


class TestErrorCode:
    """Tests for ErrorCode constants (FR-MSG-011)."""

    def test_sensor_error_codes(self) -> None:
        """ErrorCode has all SENSOR_* codes."""
        from shared.messages.types import ErrorCode

        assert ErrorCode.SENSOR_READ_FAILURE == "SENSOR_READ_FAILURE"
        assert ErrorCode.SENSOR_INIT_FAILURE == "SENSOR_INIT_FAILURE"
        assert ErrorCode.SENSOR_OUT_OF_RANGE == "SENSOR_OUT_OF_RANGE"

    def test_network_error_codes(self) -> None:
        """ErrorCode has all NETWORK_* codes."""
        from shared.messages.types import ErrorCode

        assert ErrorCode.NETWORK_CONNECTION_FAILED == "NETWORK_CONNECTION_FAILED"
        assert ErrorCode.NETWORK_TIMEOUT == "NETWORK_TIMEOUT"
        assert ErrorCode.NETWORK_AUTH_FAILURE == "NETWORK_AUTH_FAILURE"

    def test_bus_error_codes(self) -> None:
        """ErrorCode has all BUS_* codes."""
        from shared.messages.types import ErrorCode

        assert ErrorCode.BUS_I2C_FAILURE == "BUS_I2C_FAILURE"
        assert ErrorCode.BUS_ONEWIRE_FAILURE == "BUS_ONEWIRE_FAILURE"
        assert ErrorCode.BUS_SPI_FAILURE == "BUS_SPI_FAILURE"

    def test_config_error_codes(self) -> None:
        """ErrorCode has all CONFIG_* codes."""
        from shared.messages.types import ErrorCode

        assert ErrorCode.CONFIG_INVALID_VALUE == "CONFIG_INVALID_VALUE"
        assert ErrorCode.CONFIG_MISSING_REQUIRED == "CONFIG_MISSING_REQUIRED"
        assert ErrorCode.CONFIG_SCHEMA_VIOLATION == "CONFIG_SCHEMA_VIOLATION"

    def test_system_error_codes(self) -> None:
        """ErrorCode has all SYSTEM_* codes."""
        from shared.messages.types import ErrorCode

        assert ErrorCode.SYSTEM_MEMORY_LOW == "SYSTEM_MEMORY_LOW"
        assert ErrorCode.SYSTEM_WATCHDOG_RESET == "SYSTEM_WATCHDOG_RESET"
        assert ErrorCode.SYSTEM_UNEXPECTED_RESET == "SYSTEM_UNEXPECTED_RESET"

    def test_valve_error_codes(self) -> None:
        """ErrorCode has all VALVE_* codes."""
        from shared.messages.types import ErrorCode

        assert ErrorCode.VALVE_SAFETY_INTERLOCK == "VALVE_SAFETY_INTERLOCK"
        assert ErrorCode.VALVE_MAX_DURATION == "VALVE_MAX_DURATION"
        assert ErrorCode.VALVE_ALREADY_ACTIVE == "VALVE_ALREADY_ACTIVE"
        assert ErrorCode.VALVE_DATA_STALE == "VALVE_DATA_STALE"
        assert ErrorCode.VALVE_HARDWARE_FAILURE == "VALVE_HARDWARE_FAILURE"

    def test_error_code_count(self) -> None:
        """ErrorCode has expected number of codes."""
        from shared.messages.types import ErrorCode

        # Count all public attributes (error codes)
        codes = [attr for attr in dir(ErrorCode) if not attr.startswith("_") and attr.isupper()]
        # 20 error codes defined in FR-MSG-011
        assert len(codes) == 20
