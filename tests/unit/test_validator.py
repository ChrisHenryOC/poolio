# Unit tests for message validation functions
# Tests for Issue #12: Message Validation (Simple)


from shared.messages.validator import (
    COMMAND_MAX_AGE_SECONDS,
    COMMAND_TYPES,
    MAX_FUTURE_SECONDS,
    MAX_MESSAGE_SIZE_BYTES,
    STATUS_MAX_AGE_SECONDS,
    validate_envelope,
    validate_message_size,
    validate_payload,
    validate_timestamp_freshness,
)


class TestValidateEnvelope:
    """Tests for validate_envelope function."""

    def test_valid_envelope_returns_true(self) -> None:
        """Valid envelope with all required fields returns (True, [])."""
        envelope = {
            "version": 2,
            "type": "pool_status",
            "deviceId": "pool-node-001",
            "timestamp": "2026-01-20T14:30:00-08:00",
            "payload": {"waterLevel": {"floatSwitch": True}},
        }

        valid, errors = validate_envelope(envelope)

        assert valid is True
        assert errors == []

    def test_missing_version_returns_error(self) -> None:
        """Envelope missing version field returns (False, [error])."""
        envelope = {
            "type": "pool_status",
            "deviceId": "pool-node-001",
            "timestamp": "2026-01-20T14:30:00-08:00",
            "payload": {},
        }

        valid, errors = validate_envelope(envelope)

        assert valid is False
        assert len(errors) == 1
        assert "version" in errors[0]

    def test_missing_type_returns_error(self) -> None:
        """Envelope missing type field returns (False, [error])."""
        envelope = {
            "version": 2,
            "deviceId": "pool-node-001",
            "timestamp": "2026-01-20T14:30:00-08:00",
            "payload": {},
        }

        valid, errors = validate_envelope(envelope)

        assert valid is False
        assert len(errors) == 1
        assert "type" in errors[0]

    def test_missing_device_id_returns_error(self) -> None:
        """Envelope missing deviceId field returns (False, [error])."""
        envelope = {
            "version": 2,
            "type": "pool_status",
            "timestamp": "2026-01-20T14:30:00-08:00",
            "payload": {},
        }

        valid, errors = validate_envelope(envelope)

        assert valid is False
        assert len(errors) == 1
        assert "deviceId" in errors[0]

    def test_missing_timestamp_returns_error(self) -> None:
        """Envelope missing timestamp field returns (False, [error])."""
        envelope = {
            "version": 2,
            "type": "pool_status",
            "deviceId": "pool-node-001",
            "payload": {},
        }

        valid, errors = validate_envelope(envelope)

        assert valid is False
        assert len(errors) == 1
        assert "timestamp" in errors[0]

    def test_missing_payload_returns_error(self) -> None:
        """Envelope missing payload field returns (False, [error])."""
        envelope = {
            "version": 2,
            "type": "pool_status",
            "deviceId": "pool-node-001",
            "timestamp": "2026-01-20T14:30:00-08:00",
        }

        valid, errors = validate_envelope(envelope)

        assert valid is False
        assert len(errors) == 1
        assert "payload" in errors[0]

    def test_multiple_missing_fields_returns_all_errors(self) -> None:
        """Envelope missing multiple fields returns all errors."""
        envelope = {
            "version": 2,
        }

        valid, errors = validate_envelope(envelope)

        assert valid is False
        assert len(errors) == 4
        error_text = " ".join(errors)
        assert "type" in error_text
        assert "deviceId" in error_text
        assert "timestamp" in error_text
        assert "payload" in error_text

    def test_empty_envelope_returns_all_errors(self) -> None:
        """Empty envelope returns errors for all required fields."""
        envelope: dict[str, object] = {}

        valid, errors = validate_envelope(envelope)

        assert valid is False
        assert len(errors) == 5


class TestValidateMessageSize:
    """Tests for validate_message_size function."""

    def test_small_message_is_valid(self) -> None:
        """Message under 4KB is valid."""
        json_str = '{"version": 2, "type": "test"}'

        valid, errors = validate_message_size(json_str)

        assert valid is True
        assert errors == []

    def test_exactly_4kb_is_valid(self) -> None:
        """Message exactly 4096 bytes is valid."""
        # Create a message that is exactly 4096 bytes
        padding = "x" * (4096 - len('{"data": ""}'))
        json_str = '{"data": "' + padding + '"}'
        assert len(json_str.encode("utf-8")) == 4096

        valid, errors = validate_message_size(json_str)

        assert valid is True
        assert errors == []

    def test_message_over_4kb_is_invalid(self) -> None:
        """Message over 4096 bytes is invalid."""
        padding = "x" * 4097
        json_str = '{"data": "' + padding + '"}'

        valid, errors = validate_message_size(json_str)

        assert valid is False
        assert len(errors) == 1
        assert "4096" in errors[0] or "4KB" in errors[0]

    def test_error_includes_actual_size(self) -> None:
        """Error message includes actual message size."""
        padding = "x" * 5000
        json_str = '{"data": "' + padding + '"}'
        actual_size = len(json_str.encode("utf-8"))

        valid, errors = validate_message_size(json_str)

        assert valid is False
        assert str(actual_size) in errors[0]

    def test_multibyte_characters_counted_correctly(self) -> None:
        """Size is calculated in bytes, not characters."""
        # Unicode characters take multiple bytes
        # \u00e9 is 2 bytes in UTF-8, \u4e2d is 3 bytes
        json_str = '{"text": "' + "\u4e2d" * 1400 + '"}'  # ~4200 bytes
        assert len(json_str.encode("utf-8")) > 4096

        valid, errors = validate_message_size(json_str)

        assert valid is False

    def test_empty_message_is_valid(self) -> None:
        """Empty string is valid (under size limit)."""
        valid, errors = validate_message_size("")

        assert valid is True
        assert errors == []


class TestValidatePayload:
    """Tests for validate_payload function."""

    def test_valid_pool_status_payload(self) -> None:
        """Valid pool_status payload with all required fields."""
        payload = {
            "waterLevel": {"floatSwitch": True, "confidence": 0.95},
            "temperature": {"value": 78.5, "unit": "fahrenheit"},
            "battery": {"voltage": 3.7, "percentage": 85},
            "reportingInterval": 300,
        }

        valid, errors = validate_payload("pool_status", payload)

        assert valid is True
        assert errors == []

    def test_missing_pool_status_field(self) -> None:
        """pool_status missing required field returns error."""
        payload = {
            "waterLevel": {"floatSwitch": True, "confidence": 0.95},
            "temperature": {"value": 78.5, "unit": "fahrenheit"},
            # Missing battery and reportingInterval
        }

        valid, errors = validate_payload("pool_status", payload)

        assert valid is False
        assert len(errors) >= 1
        error_text = " ".join(errors)
        assert "battery" in error_text or "reportingInterval" in error_text

    def test_valid_valve_status_payload(self) -> None:
        """Valid valve_status payload with all required fields."""
        payload = {
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
            },
            "temperature": {"value": 72.0, "unit": "fahrenheit"},
        }

        valid, errors = validate_payload("valve_status", payload)

        assert valid is True
        assert errors == []

    def test_valid_display_status_payload(self) -> None:
        """Valid display_status payload with all required fields."""
        payload = {
            "localTemperature": {"value": 68.5, "unit": "fahrenheit"},
            "localHumidity": {"value": 45.0, "unit": "percent"},
        }

        valid, errors = validate_payload("display_status", payload)

        assert valid is True
        assert errors == []

    def test_valid_fill_start_payload(self) -> None:
        """Valid fill_start payload with all required fields."""
        payload = {
            "fillStartTime": "2026-01-20T09:00:00-08:00",
            "scheduledEndTime": "2026-01-20T09:09:00-08:00",
            "maxDuration": 540,
            "trigger": "scheduled",
        }

        valid, errors = validate_payload("fill_start", payload)

        assert valid is True
        assert errors == []

    def test_valid_fill_stop_payload(self) -> None:
        """Valid fill_stop payload with all required fields."""
        payload = {
            "fillStopTime": "2026-01-20T09:08:30-08:00",
            "actualDuration": 510,
            "reason": "water_full",
        }

        valid, errors = validate_payload("fill_stop", payload)

        assert valid is True
        assert errors == []

    def test_valid_command_payload(self) -> None:
        """Valid command payload with all required fields."""
        payload = {
            "command": "valve_start",
            "parameters": {"duration": 300},
            "source": "display-node-001",
        }

        valid, errors = validate_payload("command", payload)

        assert valid is True
        assert errors == []

    def test_valid_command_response_payload(self) -> None:
        """Valid command_response payload with required fields."""
        payload = {
            "commandTimestamp": "2026-01-20T14:30:00-08:00",
            "command": "valve_start",
            "status": "success",
        }

        valid, errors = validate_payload("command_response", payload)

        assert valid is True
        assert errors == []

    def test_valid_command_response_with_optional_fields(self) -> None:
        """Valid command_response with optional error fields."""
        payload = {
            "commandTimestamp": "2026-01-20T14:30:00-08:00",
            "command": "valve_start",
            "status": "failed",
            "errorCode": "VALVE_ALREADY_ACTIVE",
            "errorMessage": "Fill operation already in progress",
        }

        valid, errors = validate_payload("command_response", payload)

        assert valid is True
        assert errors == []

    def test_valid_error_payload(self) -> None:
        """Valid error payload with all required fields."""
        payload = {
            "errorCode": "SENSOR_READ_FAILURE",
            "errorMessage": "Temperature sensor not responding",
            "severity": "error",
            "context": {"sensor": "DS18B20", "attempts": 3},
        }

        valid, errors = validate_payload("error", payload)

        assert valid is True
        assert errors == []

    def test_error_payload_with_null_context(self) -> None:
        """Error payload with null context is valid."""
        payload = {
            "errorCode": "NETWORK_TIMEOUT",
            "errorMessage": "MQTT connection timeout",
            "severity": "warning",
            "context": None,
        }

        valid, errors = validate_payload("error", payload)

        assert valid is True
        assert errors == []

    def test_valid_config_update_payload(self) -> None:
        """Valid config_update payload with all required fields."""
        payload = {
            "configKey": "reporting_interval",
            "configValue": 600,
            "source": "cloud",
        }

        valid, errors = validate_payload("config_update", payload)

        assert valid is True
        assert errors == []

    def test_unknown_message_type_returns_error(self) -> None:
        """Unknown message type returns error."""
        payload = {"data": "value"}

        valid, errors = validate_payload("unknown_type", payload)

        assert valid is False
        assert len(errors) == 1
        assert "unknown_type" in errors[0].lower() or "unknown" in errors[0].lower()

    def test_empty_payload_for_known_type(self) -> None:
        """Empty payload for known type returns errors for all required fields."""
        valid, errors = validate_payload("command", {})

        assert valid is False
        assert len(errors) >= 3  # command, parameters, source


class TestValidateTimestampFreshness:
    """Tests for validate_timestamp_freshness function."""

    # Reference time: 2026-01-20T14:35:00-08:00 = 2026-01-20T22:35:00Z = 1768948500
    REFERENCE_TIME = 1768948500

    def test_fresh_command_is_valid(self) -> None:
        """Command timestamp within 5 minutes is valid."""
        # Message timestamp: 2026-01-20T14:32:00-08:00 (3 minutes before reference)
        timestamp = "2026-01-20T14:32:00-08:00"

        valid, errors = validate_timestamp_freshness(timestamp, "command", self.REFERENCE_TIME)

        assert valid is True
        assert errors == []

    def test_stale_command_is_invalid(self) -> None:
        """Command timestamp older than 5 minutes is invalid."""
        # Message timestamp: 2026-01-20T14:29:00-08:00 (6 minutes before reference)
        timestamp = "2026-01-20T14:29:00-08:00"

        valid, errors = validate_timestamp_freshness(timestamp, "command", self.REFERENCE_TIME)

        assert valid is False
        assert len(errors) == 1
        assert "5 minute" in errors[0] or "300" in errors[0] or "old" in errors[0].lower()

    def test_fresh_status_is_valid(self) -> None:
        """Status timestamp within 15 minutes is valid."""
        # Message timestamp: 2026-01-20T14:25:00-08:00 (10 minutes before reference)
        timestamp = "2026-01-20T14:25:00-08:00"

        valid, errors = validate_timestamp_freshness(timestamp, "pool_status", self.REFERENCE_TIME)

        assert valid is True
        assert errors == []

    def test_stale_status_is_invalid(self) -> None:
        """Status timestamp older than 15 minutes is invalid."""
        # Message timestamp: 2026-01-20T14:15:00-08:00 (20 minutes before reference)
        timestamp = "2026-01-20T14:15:00-08:00"

        valid, errors = validate_timestamp_freshness(timestamp, "pool_status", self.REFERENCE_TIME)

        assert valid is False
        assert len(errors) == 1
        assert "15 minute" in errors[0] or "900" in errors[0] or "old" in errors[0].lower()

    def test_future_timestamp_is_invalid(self) -> None:
        """Timestamp more than 1 minute in future is invalid."""
        # Message timestamp: 2026-01-20T14:37:00-08:00 (2 minutes after reference)
        timestamp = "2026-01-20T14:37:00-08:00"

        valid, errors = validate_timestamp_freshness(timestamp, "command", self.REFERENCE_TIME)

        assert valid is False
        assert len(errors) == 1
        assert "future" in errors[0].lower()

    def test_slightly_future_timestamp_is_valid(self) -> None:
        """Timestamp less than 1 minute in future is valid (clock skew tolerance)."""
        # Message timestamp: 2026-01-20T14:35:30-08:00 (30 seconds after reference)
        timestamp = "2026-01-20T14:35:30-08:00"

        valid, errors = validate_timestamp_freshness(timestamp, "command", self.REFERENCE_TIME)

        assert valid is True
        assert errors == []

    def test_command_response_uses_command_threshold(self) -> None:
        """command_response uses 5 minute threshold like command."""
        # Message timestamp: 2026-01-20T14:29:00-08:00 (6 minutes before reference)
        timestamp = "2026-01-20T14:29:00-08:00"

        valid, errors = validate_timestamp_freshness(
            timestamp, "command_response", self.REFERENCE_TIME
        )

        assert valid is False

    def test_config_update_uses_command_threshold(self) -> None:
        """config_update uses 5 minute threshold like command."""
        # Message timestamp: 2026-01-20T14:29:00-08:00 (6 minutes before reference)
        timestamp = "2026-01-20T14:29:00-08:00"

        valid, errors = validate_timestamp_freshness(
            timestamp, "config_update", self.REFERENCE_TIME
        )

        assert valid is False

    def test_fill_start_uses_status_threshold(self) -> None:
        """fill_start uses 15 minute threshold like status."""
        # Message timestamp: 2026-01-20T14:25:00-08:00 (10 minutes before reference)
        timestamp = "2026-01-20T14:25:00-08:00"

        valid, errors = validate_timestamp_freshness(timestamp, "fill_start", self.REFERENCE_TIME)

        assert valid is True

    def test_error_type_uses_status_threshold(self) -> None:
        """error message type uses 15 minute threshold."""
        # Message timestamp: 2026-01-20T14:25:00-08:00 (10 minutes before reference)
        timestamp = "2026-01-20T14:25:00-08:00"

        valid, errors = validate_timestamp_freshness(timestamp, "error", self.REFERENCE_TIME)

        assert valid is True

    def test_invalid_timestamp_format(self) -> None:
        """Invalid timestamp format returns error."""
        current_time = 1737412500

        valid, errors = validate_timestamp_freshness("not-a-timestamp", "command", current_time)

        assert valid is False
        assert len(errors) == 1
        assert "format" in errors[0].lower() or "parse" in errors[0].lower()


class TestConstants:
    """Tests for validation constants."""

    def test_max_message_size_is_4kb(self) -> None:
        """MAX_MESSAGE_SIZE_BYTES is 4096."""
        assert MAX_MESSAGE_SIZE_BYTES == 4096

    def test_command_max_age_is_5_minutes(self) -> None:
        """COMMAND_MAX_AGE_SECONDS is 300."""
        assert COMMAND_MAX_AGE_SECONDS == 300

    def test_status_max_age_is_15_minutes(self) -> None:
        """STATUS_MAX_AGE_SECONDS is 900."""
        assert STATUS_MAX_AGE_SECONDS == 900

    def test_max_future_is_1_minute(self) -> None:
        """MAX_FUTURE_SECONDS is 60."""
        assert MAX_FUTURE_SECONDS == 60

    def test_command_types_includes_command(self) -> None:
        """COMMAND_TYPES includes 'command'."""
        assert "command" in COMMAND_TYPES

    def test_command_types_includes_command_response(self) -> None:
        """COMMAND_TYPES includes 'command_response'."""
        assert "command_response" in COMMAND_TYPES

    def test_command_types_includes_config_update(self) -> None:
        """COMMAND_TYPES includes 'config_update'."""
        assert "config_update" in COMMAND_TYPES
