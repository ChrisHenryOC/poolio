# Unit tests for message encoder functions
# Tests for snake_case to camelCase conversion and message encoding

import json

import pytest

from shared.messages.encoder import encode_message, snake_to_camel
from shared.messages.types import (
    Battery,
    Command,
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


class TestSnakeToCamel:
    """Tests for snake_to_camel function."""

    def test_single_word(self) -> None:
        """Single word remains unchanged."""
        assert snake_to_camel("value") == "value"

    def test_two_words(self) -> None:
        """Two words convert to camelCase."""
        assert snake_to_camel("water_level") == "waterLevel"

    def test_three_words(self) -> None:
        """Three words convert to camelCase."""
        assert snake_to_camel("current_fill_duration") == "currentFillDuration"

    def test_already_camel_case(self) -> None:
        """Already camelCase string stays unchanged."""
        assert snake_to_camel("waterLevel") == "waterLevel"

    def test_all_lowercase(self) -> None:
        """All lowercase without underscores stays unchanged."""
        assert snake_to_camel("temperature") == "temperature"

    def test_with_numbers(self) -> None:
        """Numbers in snake_case convert correctly."""
        assert snake_to_camel("value_1") == "value1"
        assert snake_to_camel("node_001") == "node001"

    def test_leading_underscore_removed(self) -> None:
        """Leading underscores produce capitalized result in isolated function.

        Note: This tests the snake_to_camel function in isolation. In the encoder,
        attributes starting with '_' are skipped entirely (see _encode_value),
        so this conversion never occurs during actual message encoding.
        """
        # Leading underscore followed by letter capitalizes the letter
        assert snake_to_camel("_private") == "Private"

    def test_trailing_underscore(self) -> None:
        """Trailing underscores are removed."""
        assert snake_to_camel("value_") == "value"


class TestEncodeMessage:
    """Tests for encode_message function."""

    def test_encode_simple_message(self) -> None:
        """encode_message converts simple message to JSON with envelope."""
        temp = Temperature(value=78.5, unit="fahrenheit")

        json_str = encode_message(temp, "pool-node-001", msg_type="temperature")
        data = json.loads(json_str)

        assert data["version"] == 2
        assert data["type"] == "temperature"
        assert data["deviceId"] == "pool-node-001"
        assert "timestamp" in data
        assert data["payload"]["value"] == 78.5
        assert data["payload"]["unit"] == "fahrenheit"

    def test_encode_converts_snake_to_camel(self) -> None:
        """encode_message converts snake_case attributes to camelCase keys."""
        water_level = WaterLevel(float_switch=True, confidence=0.95)

        json_str = encode_message(water_level, "pool-node-001", msg_type="water_level")
        data = json.loads(json_str)

        # Python attribute is float_switch, JSON key should be floatSwitch
        assert "floatSwitch" in data["payload"]
        assert data["payload"]["floatSwitch"] is True
        assert data["payload"]["confidence"] == 0.95

    def test_encode_nested_objects(self) -> None:
        """encode_message handles nested message objects."""
        water_level = WaterLevel(float_switch=True, confidence=0.95)
        temp = Temperature(value=78.5)
        battery = Battery(voltage=3.85, percentage=72)

        status = PoolStatus(
            water_level=water_level,
            temperature=temp,
            battery=battery,
            reporting_interval=120,
        )

        json_str = encode_message(status, "pool-node-001", msg_type="pool_status")
        data = json.loads(json_str)

        # Check nested objects have camelCase keys
        assert "waterLevel" in data["payload"]
        assert data["payload"]["waterLevel"]["floatSwitch"] is True
        assert data["payload"]["temperature"]["value"] == 78.5
        assert data["payload"]["battery"]["percentage"] == 72
        assert data["payload"]["reportingInterval"] == 120

    def test_encode_valve_status(self) -> None:
        """encode_message handles ValveStatus with multiple nested objects."""
        valve = ValveState(
            state="closed",
            is_filling=False,
            current_fill_duration=0,
            max_fill_duration=540,
        )
        schedule = ScheduleInfo(
            enabled=True,
            start_time="09:00",
            window_hours=2,
            next_scheduled_fill="2026-01-20T09:00:00-08:00",
        )
        temp = Temperature(value=72.0)

        status = ValveStatus(valve=valve, schedule=schedule, temperature=temp)

        json_str = encode_message(status, "valve-node-001", msg_type="valve_status")
        data = json.loads(json_str)

        # Check camelCase conversion in nested objects
        assert data["payload"]["valve"]["isFilling"] is False
        assert data["payload"]["valve"]["currentFillDuration"] == 0
        assert data["payload"]["valve"]["maxFillDuration"] == 540
        assert data["payload"]["schedule"]["startTime"] == "09:00"
        assert data["payload"]["schedule"]["windowHours"] == 2
        assert data["payload"]["schedule"]["nextScheduledFill"] == "2026-01-20T09:00:00-08:00"

    def test_encode_display_status(self) -> None:
        """encode_message handles DisplayStatus."""
        temp = Temperature(value=72.5)
        humidity = Humidity(value=45.0)

        status = DisplayStatus(local_temperature=temp, local_humidity=humidity)

        json_str = encode_message(status, "display-node-001", msg_type="display_status")
        data = json.loads(json_str)

        assert "localTemperature" in data["payload"]
        assert "localHumidity" in data["payload"]
        assert data["payload"]["localTemperature"]["value"] == 72.5
        assert data["payload"]["localHumidity"]["value"] == 45.0

    def test_encode_fill_start(self) -> None:
        """encode_message handles FillStart event."""
        fill = FillStart(
            fill_start_time="2026-01-20T09:00:00-08:00",
            scheduled_end_time="2026-01-20T09:09:00-08:00",
            max_duration=540,
            trigger="scheduled",
        )

        json_str = encode_message(fill, "valve-node-001", msg_type="fill_start")
        data = json.loads(json_str)

        assert data["payload"]["fillStartTime"] == "2026-01-20T09:00:00-08:00"
        assert data["payload"]["scheduledEndTime"] == "2026-01-20T09:09:00-08:00"
        assert data["payload"]["maxDuration"] == 540
        assert data["payload"]["trigger"] == "scheduled"

    def test_encode_fill_stop(self) -> None:
        """encode_message handles FillStop event."""
        fill = FillStop(
            fill_stop_time="2026-01-20T09:05:30-08:00",
            actual_duration=330,
            reason="water_full",
        )

        json_str = encode_message(fill, "valve-node-001", msg_type="fill_stop")
        data = json.loads(json_str)

        assert data["payload"]["fillStopTime"] == "2026-01-20T09:05:30-08:00"
        assert data["payload"]["actualDuration"] == 330
        assert data["payload"]["reason"] == "water_full"

    def test_encode_command(self) -> None:
        """encode_message handles Command."""
        cmd = Command(
            command="valve_start",
            parameters={"maxDuration": 540},
            source="display-node-001",
        )

        json_str = encode_message(cmd, "display-node-001", msg_type="command")
        data = json.loads(json_str)

        assert data["payload"]["command"] == "valve_start"
        assert data["payload"]["parameters"] == {"maxDuration": 540}
        assert data["payload"]["source"] == "display-node-001"

    def test_encode_error(self) -> None:
        """encode_message handles Error."""
        error = Error(
            error_code="SENSOR_READ_FAILURE",
            error_message="Failed to read temperature sensor",
            severity="warning",
            context={"sensor": "DS18X20", "retryCount": 3},
        )

        json_str = encode_message(error, "pool-node-001", msg_type="error")
        data = json.loads(json_str)

        assert data["payload"]["errorCode"] == "SENSOR_READ_FAILURE"
        assert data["payload"]["errorMessage"] == "Failed to read temperature sensor"
        assert data["payload"]["severity"] == "warning"
        assert data["payload"]["context"]["sensor"] == "DS18X20"
        assert data["payload"]["context"]["retryCount"] == 3

    def test_encode_config_update(self) -> None:
        """encode_message handles ConfigUpdate."""
        config = ConfigUpdate(
            config_key="valveStartTime",
            config_value="10:00",
            source="cloud",
        )

        json_str = encode_message(config, "valve-node-001", msg_type="config_update")
        data = json.loads(json_str)

        assert data["payload"]["configKey"] == "valveStartTime"
        assert data["payload"]["configValue"] == "10:00"
        assert data["payload"]["source"] == "cloud"

    def test_encode_with_none_values(self) -> None:
        """encode_message handles None values in objects."""
        schedule = ScheduleInfo(
            enabled=True,
            start_time="09:00",
            window_hours=2,
            next_scheduled_fill=None,
        )

        json_str = encode_message(schedule, "valve-node-001", msg_type="schedule_info")
        data = json.loads(json_str)

        assert data["payload"]["nextScheduledFill"] is None

    def test_encode_with_custom_timestamp(self) -> None:
        """encode_message accepts custom timestamp."""
        temp = Temperature(value=78.5)
        custom_timestamp = "2026-01-20T14:30:00-08:00"

        json_str = encode_message(
            temp, "pool-node-001", msg_type="temperature", timestamp=custom_timestamp
        )
        data = json.loads(json_str)

        assert data["timestamp"] == custom_timestamp

    def test_encode_validates_device_id(self) -> None:
        """encode_message validates device ID format."""
        temp = Temperature(value=78.5)

        with pytest.raises(ValueError, match="lowercase"):
            encode_message(temp, "Pool-Node-001", msg_type="temperature")

    def test_encode_validates_msg_type_not_empty(self) -> None:
        """encode_message validates msg_type is not empty."""
        temp = Temperature(value=78.5)

        with pytest.raises(ValueError, match="msg_type cannot be empty"):
            encode_message(temp, "pool-node-001", msg_type="")

    def test_encode_preserves_dict_values(self) -> None:
        """encode_message preserves dict values without recursion into them."""
        # The parameters dict should be preserved as-is (it's already JSON-ready)
        cmd = Command(
            command="set_config",
            parameters={"key": "valveStartTime", "value": "10:00"},
            source="cloud",
        )

        json_str = encode_message(cmd, "display-node-001", msg_type="command")
        data = json.loads(json_str)

        # parameters dict should be preserved exactly
        assert data["payload"]["parameters"]["key"] == "valveStartTime"
        assert data["payload"]["parameters"]["value"] == "10:00"

    def test_encode_error_with_none_context(self) -> None:
        """encode_message handles Error with None context."""
        error = Error(
            error_code="SYSTEM_WATCHDOG_RESET",
            error_message="Device reset by watchdog",
            severity="critical",
            context=None,
        )

        json_str = encode_message(error, "pool-node-001", msg_type="error")
        data = json.loads(json_str)

        assert data["payload"]["context"] is None

    def test_encode_preserves_snake_case_keys_in_parameters(self) -> None:
        """encode_message preserves snake_case keys in parameters dict."""
        # User data in parameters should NOT have keys converted to camelCase
        cmd = Command(
            command="set_config",
            parameters={"retry_count": 3, "max_timeout": 120},
            source="cloud",
        )

        json_str = encode_message(cmd, "display-node-001", msg_type="command")
        data = json.loads(json_str)

        # parameters keys should be preserved exactly as provided
        assert "retry_count" in data["payload"]["parameters"]
        assert "max_timeout" in data["payload"]["parameters"]
        assert data["payload"]["parameters"]["retry_count"] == 3

    def test_encode_preserves_snake_case_keys_in_context(self) -> None:
        """encode_message preserves snake_case keys in context dict."""
        # User data in context should NOT have keys converted to camelCase
        error = Error(
            error_code="SENSOR_READ_FAILURE",
            error_message="Failed to read sensor",
            severity="warning",
            context={"sensor_type": "DS18X20", "retry_count": 3},
        )

        json_str = encode_message(error, "pool-node-001", msg_type="error")
        data = json.loads(json_str)

        # context keys should be preserved exactly as provided
        assert "sensor_type" in data["payload"]["context"]
        assert "retry_count" in data["payload"]["context"]
        assert data["payload"]["context"]["sensor_type"] == "DS18X20"
