# Unit tests for message envelope functions
# Tests for FR-MSG-001 and FR-MSG-002 envelope creation and parsing

import json

import pytest

from shared.messages.envelope import (
    PROTOCOL_VERSION,
    create_envelope,
    parse_envelope,
    validate_device_id,
)


class TestValidateDeviceId:
    """Tests for validate_device_id function."""

    def test_valid_device_id(self) -> None:
        """Valid device IDs are accepted."""
        # Should not raise
        validate_device_id("pool-node-001")
        validate_device_id("valve-node-001")
        validate_device_id("display-node-001")

    def test_valid_device_id_with_numbers(self) -> None:
        """Device IDs with numbers are valid."""
        validate_device_id("pool-node-123")
        validate_device_id("node123")
        validate_device_id("123")

    def test_valid_device_id_minimum_length(self) -> None:
        """Device ID can be 1 character."""
        validate_device_id("a")
        validate_device_id("1")
        validate_device_id("-")

    def test_valid_device_id_maximum_length(self) -> None:
        """Device ID can be 64 characters."""
        device_id = "a" * 64
        validate_device_id(device_id)

    def test_invalid_device_id_too_long(self) -> None:
        """Device ID over 64 characters is rejected."""
        device_id = "a" * 65
        with pytest.raises(ValueError, match="1-64 characters"):
            validate_device_id(device_id)

    def test_invalid_device_id_empty(self) -> None:
        """Empty device ID is rejected."""
        with pytest.raises(ValueError, match="1-64 characters"):
            validate_device_id("")

    def test_invalid_device_id_uppercase(self) -> None:
        """Device ID with uppercase letters is rejected."""
        with pytest.raises(ValueError, match="lowercase letters, numbers, and hyphens"):
            validate_device_id("Pool-Node-001")

    def test_invalid_device_id_underscore(self) -> None:
        """Device ID with underscores is rejected."""
        with pytest.raises(ValueError, match="lowercase letters, numbers, and hyphens"):
            validate_device_id("pool_node_001")

    def test_invalid_device_id_special_chars(self) -> None:
        """Device ID with special characters is rejected."""
        with pytest.raises(ValueError, match="lowercase letters, numbers, and hyphens"):
            validate_device_id("pool.node.001")
        with pytest.raises(ValueError, match="lowercase letters, numbers, and hyphens"):
            validate_device_id("pool@node")

    def test_invalid_device_id_spaces(self) -> None:
        """Device ID with spaces is rejected."""
        with pytest.raises(ValueError, match="lowercase letters, numbers, and hyphens"):
            validate_device_id("pool node")


class TestCreateEnvelope:
    """Tests for create_envelope function."""

    def test_create_envelope_basic(self) -> None:
        """create_envelope returns dict with all required fields."""
        payload = {"waterLevel": {"floatSwitch": True, "confidence": 0.95}}

        envelope = create_envelope("pool_status", "pool-node-001", payload)

        assert envelope["version"] == PROTOCOL_VERSION
        assert envelope["type"] == "pool_status"
        assert envelope["deviceId"] == "pool-node-001"
        assert "timestamp" in envelope
        assert envelope["payload"] == payload

    def test_create_envelope_validates_device_id(self) -> None:
        """create_envelope validates device ID format."""
        with pytest.raises(ValueError, match="lowercase letters"):
            create_envelope("pool_status", "Pool-Node-001", {})

    def test_create_envelope_with_custom_timestamp(self) -> None:
        """create_envelope accepts custom timestamp."""
        custom_timestamp = "2026-01-20T14:30:00-08:00"
        payload = {"command": "valve_start"}

        envelope = create_envelope(
            "command", "display-node-001", payload, timestamp=custom_timestamp
        )

        assert envelope["timestamp"] == custom_timestamp

    def test_create_envelope_timestamp_format(self) -> None:
        """create_envelope generates ISO 8601 timestamp with timezone."""
        envelope = create_envelope("pool_status", "pool-node-001", {})

        timestamp = envelope["timestamp"]
        # Should have timezone offset like -08:00 or +00:00
        assert len(timestamp) >= 19  # Minimum: 2026-01-20T14:30:00
        # Timestamp should contain T separator and offset
        assert "T" in timestamp

    def test_create_envelope_empty_payload(self) -> None:
        """create_envelope works with empty payload."""
        envelope = create_envelope("heartbeat", "pool-node-001", {})

        assert envelope["payload"] == {}

    def test_create_envelope_complex_payload(self) -> None:
        """create_envelope preserves complex nested payload."""
        payload = {
            "valve": {
                "state": "open",
                "isFilling": True,
                "currentFillDuration": 120,
                "maxFillDuration": 540,
            },
            "schedule": {
                "enabled": True,
                "startTime": "09:00",
                "windowHours": 2,
            },
            "temperature": {"value": 72.0, "unit": "fahrenheit"},
        }

        envelope = create_envelope("valve_status", "valve-node-001", payload)

        assert envelope["payload"] == payload


class TestParseEnvelope:
    """Tests for parse_envelope function."""

    def test_parse_envelope_basic(self) -> None:
        """parse_envelope returns envelope and payload dicts."""
        json_str = json.dumps(
            {
                "version": 2,
                "type": "pool_status",
                "deviceId": "pool-node-001",
                "timestamp": "2026-01-20T14:30:00-08:00",
                "payload": {"waterLevel": {"floatSwitch": True}},
            }
        )

        envelope, payload = parse_envelope(json_str)

        assert envelope["version"] == 2
        assert envelope["type"] == "pool_status"
        assert envelope["deviceId"] == "pool-node-001"
        assert envelope["timestamp"] == "2026-01-20T14:30:00-08:00"
        assert payload == {"waterLevel": {"floatSwitch": True}}

    def test_parse_envelope_excludes_payload_from_envelope_dict(self) -> None:
        """parse_envelope returns envelope dict without payload field."""
        json_str = json.dumps(
            {
                "version": 2,
                "type": "pool_status",
                "deviceId": "pool-node-001",
                "timestamp": "2026-01-20T14:30:00-08:00",
                "payload": {"data": "value"},
            }
        )

        envelope, _ = parse_envelope(json_str)

        assert "payload" not in envelope

    def test_parse_envelope_empty_payload(self) -> None:
        """parse_envelope handles empty payload."""
        json_str = json.dumps(
            {
                "version": 2,
                "type": "heartbeat",
                "deviceId": "pool-node-001",
                "timestamp": "2026-01-20T14:30:00-08:00",
                "payload": {},
            }
        )

        envelope, payload = parse_envelope(json_str)

        assert payload == {}

    def test_parse_envelope_invalid_json(self) -> None:
        """parse_envelope raises on invalid JSON."""
        with pytest.raises(ValueError, match="Invalid JSON"):
            parse_envelope("not valid json")

    def test_parse_envelope_missing_version(self) -> None:
        """parse_envelope raises on missing version field."""
        json_str = json.dumps(
            {
                "type": "pool_status",
                "deviceId": "pool-node-001",
                "timestamp": "2026-01-20T14:30:00-08:00",
                "payload": {},
            }
        )

        with pytest.raises(ValueError, match="missing required field.*version"):
            parse_envelope(json_str)

    def test_parse_envelope_missing_type(self) -> None:
        """parse_envelope raises on missing type field."""
        json_str = json.dumps(
            {
                "version": 2,
                "deviceId": "pool-node-001",
                "timestamp": "2026-01-20T14:30:00-08:00",
                "payload": {},
            }
        )

        with pytest.raises(ValueError, match="missing required field.*type"):
            parse_envelope(json_str)

    def test_parse_envelope_missing_device_id(self) -> None:
        """parse_envelope raises on missing deviceId field."""
        json_str = json.dumps(
            {
                "version": 2,
                "type": "pool_status",
                "timestamp": "2026-01-20T14:30:00-08:00",
                "payload": {},
            }
        )

        with pytest.raises(ValueError, match="missing required field.*deviceId"):
            parse_envelope(json_str)

    def test_parse_envelope_missing_timestamp(self) -> None:
        """parse_envelope raises on missing timestamp field."""
        json_str = json.dumps(
            {
                "version": 2,
                "type": "pool_status",
                "deviceId": "pool-node-001",
                "payload": {},
            }
        )

        with pytest.raises(ValueError, match="missing required field.*timestamp"):
            parse_envelope(json_str)

    def test_parse_envelope_missing_payload(self) -> None:
        """parse_envelope raises on missing payload field."""
        json_str = json.dumps(
            {
                "version": 2,
                "type": "pool_status",
                "deviceId": "pool-node-001",
                "timestamp": "2026-01-20T14:30:00-08:00",
            }
        )

        with pytest.raises(ValueError, match="missing required field.*payload"):
            parse_envelope(json_str)


class TestProtocolVersion:
    """Tests for PROTOCOL_VERSION constant."""

    def test_protocol_version_is_two(self) -> None:
        """Protocol version is 2 per FR-MSG-001."""
        assert PROTOCOL_VERSION == 2
