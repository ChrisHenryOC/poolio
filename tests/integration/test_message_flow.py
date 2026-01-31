# Integration tests for message flow
# Tests end-to-end: create → encode → publish → subscribe → decode → verify


import pytest
from src.shared.cloud import MockBackend
from src.shared.messages import (
    Battery,
    Command,
    PoolStatus,
    ScheduleInfo,
    Temperature,
    ValveState,
    ValveStatus,
    WaterLevel,
    decode_message,
    encode_message,
)


@pytest.fixture
def backend():
    """Provide a connected MockBackend instance with automatic cleanup."""
    b = MockBackend(environment="test")
    b.connect()
    yield b
    b.disconnect()


class TestMessageFlow:
    """End-to-end integration tests for message encoding/decoding through MockBackend."""

    def test_pool_status_round_trip(self, backend: MockBackend) -> None:
        """PoolStatus message survives encode → publish → subscribe → decode."""
        # Setup subscription
        received_messages: list[str] = []
        backend.subscribe("test-poolstatus", lambda f, v: received_messages.append(v))

        # Create original message with nested objects
        original = PoolStatus(
            water_level=WaterLevel(float_switch=True, confidence=0.95),
            temperature=Temperature(value=78.5, unit="fahrenheit"),
            battery=Battery(voltage=3.85, percentage=72),
            reporting_interval=120,
        )

        # Encode and publish
        device_id = "pool-node-001"
        json_str = encode_message(original, device_id, "pool_status")
        backend.publish("test-poolstatus", json_str)

        # Verify subscription received message
        assert len(received_messages) == 1

        # Decode and verify all fields match
        decoded = decode_message(received_messages[0])
        assert isinstance(decoded, PoolStatus)

        # Verify nested objects using __eq__
        assert decoded.water_level == original.water_level
        assert decoded.temperature == original.temperature
        assert decoded.battery == original.battery

        # Verify top-level field
        assert decoded.reporting_interval == original.reporting_interval

    def test_valve_status_round_trip(self, backend: MockBackend) -> None:
        """ValveStatus message survives encode → publish → subscribe → decode."""
        # Setup subscription
        received_messages: list[str] = []
        backend.subscribe("test-valvestatus", lambda f, v: received_messages.append(v))

        # Create original message with nested objects
        original = ValveStatus(
            valve=ValveState(
                state="open",
                is_filling=True,
                current_fill_duration=45,
                max_fill_duration=300,
            ),
            schedule=ScheduleInfo(
                enabled=True,
                start_time="06:00",
                window_hours=2,
                next_scheduled_fill="2026-01-30T06:00:00-08:00",
            ),
            temperature=Temperature(value=65.2, unit="fahrenheit"),
        )

        # Encode and publish
        device_id = "valve-node-001"
        json_str = encode_message(original, device_id, "valve_status")
        backend.publish("test-valvestatus", json_str)

        # Verify subscription received message
        assert len(received_messages) == 1

        # Decode and verify all fields match
        decoded = decode_message(received_messages[0])
        assert isinstance(decoded, ValveStatus)

        # Verify nested ValveState
        assert decoded.valve.state == original.valve.state
        assert decoded.valve.is_filling == original.valve.is_filling
        assert decoded.valve.current_fill_duration == original.valve.current_fill_duration
        assert decoded.valve.max_fill_duration == original.valve.max_fill_duration

        # Verify nested ScheduleInfo
        assert decoded.schedule.enabled == original.schedule.enabled
        assert decoded.schedule.start_time == original.schedule.start_time
        assert decoded.schedule.window_hours == original.schedule.window_hours
        assert decoded.schedule.next_scheduled_fill == original.schedule.next_scheduled_fill

        # Verify nested Temperature using __eq__
        assert decoded.temperature == original.temperature

    def test_command_round_trip(self, backend: MockBackend) -> None:
        """Command message survives encode → publish → subscribe → decode."""
        # Setup subscription
        received_messages: list[str] = []
        backend.subscribe("test-command", lambda f, v: received_messages.append(v))

        # Create original message with parameters dict
        original = Command(
            command="start_fill",
            parameters={"duration": 300, "force": True},
            source="homekit",
        )

        # Encode and publish
        device_id = "display-node-001"
        json_str = encode_message(original, device_id, "command")
        backend.publish("test-command", json_str)

        # Verify subscription received message
        assert len(received_messages) == 1

        # Decode and verify all fields match
        decoded = decode_message(received_messages[0])
        assert isinstance(decoded, Command)

        # Verify command fields
        assert decoded.command == original.command
        assert decoded.source == original.source

        # Verify parameters dict preserved
        assert decoded.parameters == original.parameters
        assert decoded.parameters["duration"] == 300
        assert decoded.parameters["force"] is True
