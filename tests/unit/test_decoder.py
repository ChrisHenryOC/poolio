# Unit tests for message decoder functions
# Tests for camelCase to snake_case conversion and message decoding

import json

import pytest

from shared.messages.decoder import camel_to_snake, decode_message
from shared.messages.types import (
    Battery,
    Command,
    CommandResponse,
    ConfigUpdate,
    DisplayStatus,
    Error,
    FillStart,
    FillStop,
    Humidity,
    PoolStatus,
    ScheduleInfo,
    Temperature,
    ValveState,
    ValveStatus,
    WaterLevel,
)


class TestCamelToSnake:
    """Tests for camel_to_snake function."""

    def test_single_word(self) -> None:
        """Single word remains unchanged."""
        assert camel_to_snake("value") == "value"

    def test_two_words(self) -> None:
        """Two words convert to snake_case."""
        assert camel_to_snake("waterLevel") == "water_level"

    def test_three_words(self) -> None:
        """Three words convert to snake_case."""
        assert camel_to_snake("currentFillDuration") == "current_fill_duration"

    def test_already_snake_case(self) -> None:
        """Already snake_case string stays unchanged."""
        assert camel_to_snake("water_level") == "water_level"

    def test_all_lowercase(self) -> None:
        """All lowercase stays unchanged."""
        assert camel_to_snake("temperature") == "temperature"

    def test_with_numbers(self) -> None:
        """Numbers in camelCase convert correctly."""
        assert camel_to_snake("value1") == "value1"
        assert camel_to_snake("node001") == "node001"

    def test_consecutive_capitals(self) -> None:
        """Consecutive capitals are handled."""
        # Common convention: treat as single word
        assert camel_to_snake("deviceID") == "device_id"
        assert camel_to_snake("httpURL") == "http_url"


class TestDecodeMessage:
    """Tests for decode_message function."""

    def test_decode_pool_status(self) -> None:
        """decode_message returns PoolStatus with nested objects."""
        json_str = json.dumps(
            {
                "version": 2,
                "type": "pool_status",
                "deviceId": "pool-node-001",
                "timestamp": "2026-01-20T14:30:00-08:00",
                "payload": {
                    "waterLevel": {"floatSwitch": True, "confidence": 0.95},
                    "temperature": {"value": 78.5, "unit": "fahrenheit"},
                    "battery": {"voltage": 3.85, "percentage": 72},
                    "reportingInterval": 120,
                },
            }
        )

        result = decode_message(json_str)

        assert isinstance(result, PoolStatus)
        assert isinstance(result.water_level, WaterLevel)
        assert result.water_level.float_switch is True
        assert result.water_level.confidence == 0.95
        assert isinstance(result.temperature, Temperature)
        assert result.temperature.value == 78.5
        assert isinstance(result.battery, Battery)
        assert result.battery.voltage == 3.85
        assert result.battery.percentage == 72
        assert result.reporting_interval == 120

    def test_decode_valve_status(self) -> None:
        """decode_message returns ValveStatus with nested objects."""
        json_str = json.dumps(
            {
                "version": 2,
                "type": "valve_status",
                "deviceId": "valve-node-001",
                "timestamp": "2026-01-20T14:30:00-08:00",
                "payload": {
                    "valve": {
                        "state": "closed",
                        "isFilling": False,
                        "currentFillDuration": 0,
                        "maxFillDuration": 540,
                    },
                    "schedule": {
                        "enabled": True,
                        "startTime": "09:00",
                        "windowHours": 2,
                        "nextScheduledFill": "2026-01-20T09:00:00-08:00",
                    },
                    "temperature": {"value": 72.0, "unit": "fahrenheit"},
                },
            }
        )

        result = decode_message(json_str)

        assert isinstance(result, ValveStatus)
        assert isinstance(result.valve, ValveState)
        assert result.valve.state == "closed"
        assert result.valve.is_filling is False
        assert result.valve.current_fill_duration == 0
        assert result.valve.max_fill_duration == 540
        assert isinstance(result.schedule, ScheduleInfo)
        assert result.schedule.enabled is True
        assert result.schedule.start_time == "09:00"
        assert result.schedule.window_hours == 2
        assert result.schedule.next_scheduled_fill == "2026-01-20T09:00:00-08:00"
        assert isinstance(result.temperature, Temperature)

    def test_decode_display_status(self) -> None:
        """decode_message returns DisplayStatus."""
        json_str = json.dumps(
            {
                "version": 2,
                "type": "display_status",
                "deviceId": "display-node-001",
                "timestamp": "2026-01-20T14:30:00-08:00",
                "payload": {
                    "localTemperature": {"value": 72.5, "unit": "fahrenheit"},
                    "localHumidity": {"value": 45.0, "unit": "percent"},
                },
            }
        )

        result = decode_message(json_str)

        assert isinstance(result, DisplayStatus)
        assert isinstance(result.local_temperature, Temperature)
        assert result.local_temperature.value == 72.5
        assert isinstance(result.local_humidity, Humidity)
        assert result.local_humidity.value == 45.0

    def test_decode_fill_start(self) -> None:
        """decode_message returns FillStart."""
        json_str = json.dumps(
            {
                "version": 2,
                "type": "fill_start",
                "deviceId": "valve-node-001",
                "timestamp": "2026-01-20T09:00:00-08:00",
                "payload": {
                    "fillStartTime": "2026-01-20T09:00:00-08:00",
                    "scheduledEndTime": "2026-01-20T09:09:00-08:00",
                    "maxDuration": 540,
                    "trigger": "scheduled",
                },
            }
        )

        result = decode_message(json_str)

        assert isinstance(result, FillStart)
        assert result.fill_start_time == "2026-01-20T09:00:00-08:00"
        assert result.scheduled_end_time == "2026-01-20T09:09:00-08:00"
        assert result.max_duration == 540
        assert result.trigger == "scheduled"

    def test_decode_fill_stop(self) -> None:
        """decode_message returns FillStop."""
        json_str = json.dumps(
            {
                "version": 2,
                "type": "fill_stop",
                "deviceId": "valve-node-001",
                "timestamp": "2026-01-20T09:05:30-08:00",
                "payload": {
                    "fillStopTime": "2026-01-20T09:05:30-08:00",
                    "actualDuration": 330,
                    "reason": "water_full",
                },
            }
        )

        result = decode_message(json_str)

        assert isinstance(result, FillStop)
        assert result.fill_stop_time == "2026-01-20T09:05:30-08:00"
        assert result.actual_duration == 330
        assert result.reason == "water_full"

    def test_decode_command(self) -> None:
        """decode_message returns Command."""
        json_str = json.dumps(
            {
                "version": 2,
                "type": "command",
                "deviceId": "display-node-001",
                "timestamp": "2026-01-20T14:30:00-08:00",
                "payload": {
                    "command": "valve_start",
                    "parameters": {"maxDuration": 540},
                    "source": "display-node-001",
                },
            }
        )

        result = decode_message(json_str)

        assert isinstance(result, Command)
        assert result.command == "valve_start"
        assert result.parameters == {"maxDuration": 540}
        assert result.source == "display-node-001"

    def test_decode_command_response(self) -> None:
        """decode_message returns CommandResponse."""
        json_str = json.dumps(
            {
                "version": 2,
                "type": "command_response",
                "deviceId": "valve-node-001",
                "timestamp": "2026-01-20T14:30:01-08:00",
                "payload": {
                    "commandTimestamp": "2026-01-20T14:30:00-08:00",
                    "command": "valve_start",
                    "status": "success",
                    "errorCode": None,
                    "errorMessage": None,
                },
            }
        )

        result = decode_message(json_str)

        assert isinstance(result, CommandResponse)
        assert result.command_timestamp == "2026-01-20T14:30:00-08:00"
        assert result.command == "valve_start"
        assert result.status == "success"
        assert result.error_code is None
        assert result.error_message is None

    def test_decode_command_response_with_error(self) -> None:
        """decode_message returns CommandResponse with error."""
        json_str = json.dumps(
            {
                "version": 2,
                "type": "command_response",
                "deviceId": "valve-node-001",
                "timestamp": "2026-01-20T14:30:01-08:00",
                "payload": {
                    "commandTimestamp": "2026-01-20T14:30:00-08:00",
                    "command": "valve_start",
                    "status": "failed",
                    "errorCode": "VALVE_ALREADY_ACTIVE",
                    "errorMessage": "Fill already in progress",
                },
            }
        )

        result = decode_message(json_str)

        assert isinstance(result, CommandResponse)
        assert result.status == "failed"
        assert result.error_code == "VALVE_ALREADY_ACTIVE"
        assert result.error_message == "Fill already in progress"

    def test_decode_error(self) -> None:
        """decode_message returns Error."""
        json_str = json.dumps(
            {
                "version": 2,
                "type": "error",
                "deviceId": "pool-node-001",
                "timestamp": "2026-01-20T14:30:00-08:00",
                "payload": {
                    "errorCode": "SENSOR_READ_FAILURE",
                    "errorMessage": "Failed to read temperature sensor",
                    "severity": "warning",
                    "context": {"sensor": "DS18X20", "retryCount": 3},
                },
            }
        )

        result = decode_message(json_str)

        assert isinstance(result, Error)
        assert result.error_code == "SENSOR_READ_FAILURE"
        assert result.error_message == "Failed to read temperature sensor"
        assert result.severity == "warning"
        assert result.context == {"sensor": "DS18X20", "retryCount": 3}

    def test_decode_error_with_none_context(self) -> None:
        """decode_message handles Error with null context."""
        json_str = json.dumps(
            {
                "version": 2,
                "type": "error",
                "deviceId": "pool-node-001",
                "timestamp": "2026-01-20T14:30:00-08:00",
                "payload": {
                    "errorCode": "SYSTEM_WATCHDOG_RESET",
                    "errorMessage": "Device reset by watchdog",
                    "severity": "critical",
                    "context": None,
                },
            }
        )

        result = decode_message(json_str)

        assert isinstance(result, Error)
        assert result.context is None

    def test_decode_config_update(self) -> None:
        """decode_message returns ConfigUpdate."""
        json_str = json.dumps(
            {
                "version": 2,
                "type": "config_update",
                "deviceId": "valve-node-001",
                "timestamp": "2026-01-20T14:30:00-08:00",
                "payload": {
                    "configKey": "valveStartTime",
                    "configValue": "10:00",
                    "source": "cloud",
                },
            }
        )

        result = decode_message(json_str)

        assert isinstance(result, ConfigUpdate)
        assert result.config_key == "valveStartTime"
        assert result.config_value == "10:00"
        assert result.source == "cloud"

    def test_decode_unknown_message_type(self) -> None:
        """decode_message raises error for unknown type."""
        json_str = json.dumps(
            {
                "version": 2,
                "type": "unknown_type",
                "deviceId": "pool-node-001",
                "timestamp": "2026-01-20T14:30:00-08:00",
                "payload": {},
            }
        )

        with pytest.raises(ValueError, match="Unknown message type"):
            decode_message(json_str)

    def test_decode_invalid_json(self) -> None:
        """decode_message raises error for invalid JSON."""
        with pytest.raises(ValueError, match="Invalid JSON"):
            decode_message("not valid json")

    def test_decode_missing_envelope_field(self) -> None:
        """decode_message raises error for missing envelope fields."""
        json_str = json.dumps(
            {
                "version": 2,
                # missing type
                "deviceId": "pool-node-001",
                "timestamp": "2026-01-20T14:30:00-08:00",
                "payload": {},
            }
        )

        with pytest.raises(ValueError, match="missing required field"):
            decode_message(json_str)

    def test_decode_schedule_with_null_next_fill(self) -> None:
        """decode_message handles null nextScheduledFill in ValveStatus."""
        json_str = json.dumps(
            {
                "version": 2,
                "type": "valve_status",
                "deviceId": "valve-node-001",
                "timestamp": "2026-01-20T14:30:00-08:00",
                "payload": {
                    "valve": {
                        "state": "closed",
                        "isFilling": False,
                        "currentFillDuration": 0,
                        "maxFillDuration": 540,
                    },
                    "schedule": {
                        "enabled": False,
                        "startTime": "09:00",
                        "windowHours": 2,
                        "nextScheduledFill": None,
                    },
                    "temperature": {"value": 72.0, "unit": "fahrenheit"},
                },
            }
        )

        result = decode_message(json_str)

        assert isinstance(result, ValveStatus)
        assert result.schedule.next_scheduled_fill is None


class TestRoundTrip:
    """Tests for round-trip encoding and decoding."""

    def test_round_trip_pool_status(self) -> None:
        """Encoding then decoding PoolStatus preserves all data."""
        from shared.messages.encoder import encode_message

        water_level = WaterLevel(float_switch=True, confidence=0.95)
        temp = Temperature(value=78.5, unit="fahrenheit")
        battery = Battery(voltage=3.85, percentage=72)
        original = PoolStatus(
            water_level=water_level,
            temperature=temp,
            battery=battery,
            reporting_interval=120,
        )

        # Encode to JSON
        json_str = encode_message(
            original,
            "pool-node-001",
            msg_type="pool_status",
            timestamp="2026-01-20T14:30:00-08:00",
        )

        # Decode back to object
        decoded = decode_message(json_str)

        # Verify all fields match
        assert decoded.water_level.float_switch == original.water_level.float_switch
        assert decoded.water_level.confidence == original.water_level.confidence
        assert decoded.temperature.value == original.temperature.value
        assert decoded.temperature.unit == original.temperature.unit
        assert decoded.battery.voltage == original.battery.voltage
        assert decoded.battery.percentage == original.battery.percentage
        assert decoded.reporting_interval == original.reporting_interval

    def test_round_trip_valve_status(self) -> None:
        """Encoding then decoding ValveStatus preserves all data."""
        from shared.messages.encoder import encode_message

        valve = ValveState(
            state="open",
            is_filling=True,
            current_fill_duration=120,
            max_fill_duration=540,
        )
        schedule = ScheduleInfo(
            enabled=True,
            start_time="09:00",
            window_hours=2,
            next_scheduled_fill="2026-01-20T09:00:00-08:00",
        )
        temp = Temperature(value=72.0, unit="fahrenheit")
        original = ValveStatus(valve=valve, schedule=schedule, temperature=temp)

        # Encode to JSON
        json_str = encode_message(
            original,
            "valve-node-001",
            msg_type="valve_status",
            timestamp="2026-01-20T14:30:00-08:00",
        )

        # Decode back to object
        decoded = decode_message(json_str)

        # Verify all fields match
        assert decoded.valve.state == original.valve.state
        assert decoded.valve.is_filling == original.valve.is_filling
        assert decoded.valve.current_fill_duration == original.valve.current_fill_duration
        assert decoded.valve.max_fill_duration == original.valve.max_fill_duration
        assert decoded.schedule.enabled == original.schedule.enabled
        assert decoded.schedule.start_time == original.schedule.start_time
        assert decoded.schedule.window_hours == original.schedule.window_hours
        assert decoded.schedule.next_scheduled_fill == original.schedule.next_scheduled_fill
        assert decoded.temperature.value == original.temperature.value

    def test_round_trip_command(self) -> None:
        """Encoding then decoding Command preserves all data."""
        from shared.messages.encoder import encode_message

        original = Command(
            command="valve_start",
            parameters={"maxDuration": 540},
            source="display-node-001",
        )

        # Encode to JSON
        json_str = encode_message(
            original,
            "display-node-001",
            msg_type="command",
            timestamp="2026-01-20T14:30:00-08:00",
        )

        # Decode back to object
        decoded = decode_message(json_str)

        # Verify all fields match
        assert decoded.command == original.command
        assert decoded.parameters == original.parameters
        assert decoded.source == original.source

    def test_round_trip_fill_start(self) -> None:
        """Encoding then decoding FillStart preserves all data."""
        from shared.messages.encoder import encode_message

        original = FillStart(
            fill_start_time="2026-01-20T09:00:00-08:00",
            scheduled_end_time="2026-01-20T09:09:00-08:00",
            max_duration=540,
            trigger="scheduled",
        )

        # Encode to JSON
        json_str = encode_message(
            original,
            "valve-node-001",
            msg_type="fill_start",
            timestamp="2026-01-20T09:00:00-08:00",
        )

        # Decode back to object
        decoded = decode_message(json_str)

        # Verify all fields match
        assert decoded.fill_start_time == original.fill_start_time
        assert decoded.scheduled_end_time == original.scheduled_end_time
        assert decoded.max_duration == original.max_duration
        assert decoded.trigger == original.trigger

    def test_round_trip_error(self) -> None:
        """Encoding then decoding Error preserves all data."""
        from shared.messages.encoder import encode_message

        original = Error(
            error_code="SENSOR_READ_FAILURE",
            error_message="Failed to read temperature sensor",
            severity="warning",
            context={"sensor": "DS18X20", "retryCount": 3},
        )

        # Encode to JSON
        json_str = encode_message(
            original,
            "pool-node-001",
            msg_type="error",
            timestamp="2026-01-20T14:30:00-08:00",
        )

        # Decode back to object
        decoded = decode_message(json_str)

        # Verify all fields match
        assert decoded.error_code == original.error_code
        assert decoded.error_message == original.error_message
        assert decoded.severity == original.severity
        assert decoded.context == original.context
