"""
On-device tests for the shared.messages module.

These tests are adapted from tests/unit/ for CircuitPython compatibility.
They test message types, encoding, decoding, envelope, and validation.
"""

import json

from shared.messages.decoder import camel_to_snake, decode_message
from shared.messages.encoder import encode_message, snake_to_camel
from shared.messages.envelope import (
    PROTOCOL_VERSION,
    create_envelope,
    parse_envelope,
    validate_device_id,
)

# Import the modules under test
from shared.messages.types import (
    Battery,
    Humidity,
    PoolStatus,
    ScheduleInfo,
    Temperature,
    ValveState,
    ValveStatus,
    WaterLevel,
)
from tests.device.assertions import (
    assert_equal,
    assert_in,
    assert_raises,
)

# Test timestamp for CircuitPython (which lacks datetime auto-generation)
TEST_TIMESTAMP = "2026-01-20T14:30:00-08:00"


# =============================================================================
# Type Tests
# =============================================================================


def test_water_level_creation():
    """WaterLevel requires float_switch and confidence."""
    water_level = WaterLevel(float_switch=True, confidence=0.95)

    assert_equal(water_level.float_switch, True)
    assert_equal(water_level.confidence, 0.95)


def test_water_level_false_switch():
    """WaterLevel works with False float_switch."""
    water_level = WaterLevel(float_switch=False, confidence=0.8)

    assert_equal(water_level.float_switch, False)
    assert_equal(water_level.confidence, 0.8)


def test_temperature_creation():
    """Temperature requires value and optional unit."""
    temp = Temperature(value=78.5, unit="fahrenheit")

    assert_equal(temp.value, 78.5)
    assert_equal(temp.unit, "fahrenheit")


def test_temperature_default_unit():
    """Temperature defaults to fahrenheit unit."""
    temp = Temperature(value=72.0)

    assert_equal(temp.value, 72.0)
    assert_equal(temp.unit, "fahrenheit")


def test_temperature_celsius():
    """Temperature supports celsius unit."""
    temp = Temperature(value=25.0, unit="celsius")

    assert_equal(temp.value, 25.0)
    assert_equal(temp.unit, "celsius")


def test_battery_creation():
    """Battery requires voltage and percentage."""
    battery = Battery(voltage=3.85, percentage=72)

    assert_equal(battery.voltage, 3.85)
    assert_equal(battery.percentage, 72)


def test_humidity_creation():
    """Humidity requires value and optional unit."""
    humidity = Humidity(value=45.0, unit="percent")

    assert_equal(humidity.value, 45.0)
    assert_equal(humidity.unit, "percent")


def test_pool_status_creation():
    """PoolStatus composes WaterLevel, Temperature, Battery, and reporting_interval."""
    water = WaterLevel(float_switch=True, confidence=0.95)
    temp = Temperature(value=78.5)
    battery = Battery(voltage=3.85, percentage=72)

    status = PoolStatus(
        water_level=water,
        temperature=temp,
        battery=battery,
        reporting_interval=300,
    )

    assert_equal(status.water_level.float_switch, True)
    assert_equal(status.temperature.value, 78.5)
    assert_equal(status.battery.voltage, 3.85)
    assert_equal(status.reporting_interval, 300)


def test_valve_state_creation():
    """ValveState tracks valve state details."""
    state = ValveState(
        state="open",
        is_filling=True,
        current_fill_duration=120,
        max_fill_duration=600,
    )

    assert_equal(state.state, "open")
    assert_equal(state.is_filling, True)
    assert_equal(state.current_fill_duration, 120)
    assert_equal(state.max_fill_duration, 600)


def test_valve_status_creation():
    """ValveStatus composes ValveState, ScheduleInfo, and Temperature."""
    valve = ValveState(
        state="closed",
        is_filling=False,
        current_fill_duration=0,
        max_fill_duration=600,
    )
    schedule = ScheduleInfo(
        enabled=True,
        start_time="06:00",
        window_hours=4,
    )
    temp = Temperature(value=75.0)

    status = ValveStatus(valve=valve, schedule=schedule, temperature=temp)

    assert_equal(status.valve.state, "closed")
    assert_equal(status.schedule.enabled, True)
    assert_equal(status.temperature.value, 75.0)


# =============================================================================
# Encoder Tests
# =============================================================================


def test_snake_to_camel_single_word():
    """Single word remains unchanged."""
    assert_equal(snake_to_camel("value"), "value")


def test_snake_to_camel_two_words():
    """Two words convert to camelCase."""
    assert_equal(snake_to_camel("water_level"), "waterLevel")


def test_snake_to_camel_three_words():
    """Three words convert to camelCase."""
    assert_equal(snake_to_camel("current_fill_duration"), "currentFillDuration")


def test_encode_simple_message():
    """encode_message converts simple message to JSON with envelope."""
    temp = Temperature(value=78.5, unit="fahrenheit")

    json_str = encode_message(
        temp, "pool-node-001", msg_type="temperature", timestamp=TEST_TIMESTAMP
    )
    data = json.loads(json_str)

    assert_equal(data["version"], 2)
    assert_equal(data["type"], "temperature")
    assert_equal(data["deviceId"], "pool-node-001")
    assert_equal(data["timestamp"], TEST_TIMESTAMP)
    assert_equal(data["payload"]["value"], 78.5)
    assert_equal(data["payload"]["unit"], "fahrenheit")


def test_encode_converts_snake_to_camel():
    """encode_message converts snake_case attributes to camelCase keys."""
    water_level = WaterLevel(float_switch=True, confidence=0.95)

    json_str = encode_message(
        water_level, "pool-node-001", msg_type="water_level", timestamp=TEST_TIMESTAMP
    )
    data = json.loads(json_str)

    assert_in("floatSwitch", data["payload"])
    assert_equal(data["payload"]["floatSwitch"], True)
    assert_equal(data["payload"]["confidence"], 0.95)


# =============================================================================
# Decoder Tests
# =============================================================================


def test_camel_to_snake_single_word():
    """Single word remains unchanged."""
    assert_equal(camel_to_snake("value"), "value")


def test_camel_to_snake_two_words():
    """camelCase converts to snake_case."""
    assert_equal(camel_to_snake("waterLevel"), "water_level")


def test_camel_to_snake_three_words():
    """Multiple camelCase words convert correctly."""
    assert_equal(camel_to_snake("currentFillDuration"), "current_fill_duration")


def test_decode_pool_status():
    """decode_message parses pool_status message."""
    json_str = """{
        "version": 2,
        "type": "pool_status",
        "deviceId": "pool-node-001",
        "timestamp": "2026-01-20T14:30:00-08:00",
        "payload": {
            "waterLevel": {"floatSwitch": true, "confidence": 0.95},
            "temperature": {"value": 78.5, "unit": "fahrenheit"},
            "battery": {"voltage": 3.85, "percentage": 72},
            "reportingInterval": 300
        }
    }"""

    result = decode_message(json_str)

    # decode_message returns the payload object directly
    assert_equal(result.water_level.float_switch, True)
    assert_equal(result.temperature.value, 78.5)
    assert_equal(result.battery.percentage, 72)


# =============================================================================
# Envelope Tests
# =============================================================================


def test_validate_device_id_valid():
    """Valid device IDs are accepted."""
    # Should not raise
    validate_device_id("pool-node-001")
    validate_device_id("valve-node-001")
    validate_device_id("display-node-001")


def test_validate_device_id_invalid_uppercase():
    """Device ID with uppercase letters is rejected."""
    assert_raises(ValueError, validate_device_id, "Pool-Node-001")


def test_validate_device_id_invalid_underscore():
    """Device ID with underscores is rejected."""
    assert_raises(ValueError, validate_device_id, "pool_node_001")


def test_create_envelope_basic():
    """create_envelope returns dict with all required fields."""
    payload = {"waterLevel": {"floatSwitch": True, "confidence": 0.95}}

    envelope = create_envelope("pool_status", "pool-node-001", payload, timestamp=TEST_TIMESTAMP)

    assert_equal(envelope["version"], PROTOCOL_VERSION)
    assert_equal(envelope["type"], "pool_status")
    assert_equal(envelope["deviceId"], "pool-node-001")
    assert_equal(envelope["timestamp"], TEST_TIMESTAMP)
    assert_equal(envelope["payload"], payload)


def test_parse_envelope_valid():
    """parse_envelope extracts fields from valid JSON."""
    json_str = """{
        "version": 2,
        "type": "pool_status",
        "deviceId": "pool-node-001",
        "timestamp": "2026-01-20T14:30:00-08:00",
        "payload": {"temperature": 78.5}
    }"""

    envelope, payload = parse_envelope(json_str)

    assert_equal(envelope["version"], 2)
    assert_equal(envelope["type"], "pool_status")
    assert_equal(envelope["deviceId"], "pool-node-001")
    assert_equal(payload["temperature"], 78.5)


def test_parse_envelope_invalid_json():
    """parse_envelope raises error for invalid JSON.

    Note: CircuitPython may raise AttributeError instead of ValueError
    for invalid JSON, so we accept either exception.
    """
    assert_raises((ValueError, AttributeError), parse_envelope, "not valid json")


# =============================================================================
# Round-Trip Tests
# =============================================================================


def test_encode_decode_round_trip_temperature():
    """Encoding then decoding preserves Temperature data."""
    original = Temperature(value=78.5, unit="fahrenheit")

    # Create full pool_status message (decoder expects known types)
    status = PoolStatus(
        water_level=WaterLevel(float_switch=True, confidence=0.9),
        temperature=original,
        battery=Battery(voltage=3.8, percentage=80),
        reporting_interval=300,
    )

    json_str = encode_message(
        status, "test-device", msg_type="pool_status", timestamp=TEST_TIMESTAMP
    )
    decoded = decode_message(json_str)

    assert_equal(decoded.temperature.value, original.value)
    assert_equal(decoded.temperature.unit, original.unit)


def test_encode_decode_round_trip_pool_status():
    """Encoding then decoding preserves PoolStatus data."""
    original = PoolStatus(
        water_level=WaterLevel(float_switch=True, confidence=0.95),
        temperature=Temperature(value=78.5, unit="fahrenheit"),
        battery=Battery(voltage=3.85, percentage=72),
        reporting_interval=300,
    )

    json_str = encode_message(
        original, "pool-node-001", msg_type="pool_status", timestamp=TEST_TIMESTAMP
    )
    decoded = decode_message(json_str)

    assert_equal(decoded.water_level.float_switch, True)
    assert_equal(decoded.water_level.confidence, 0.95)
    assert_equal(decoded.temperature.value, 78.5)
    assert_equal(decoded.battery.voltage, 3.85)
    assert_equal(decoded.battery.percentage, 72)
    assert_equal(decoded.reporting_interval, 300)
