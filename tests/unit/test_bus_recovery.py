# Tests for bus recovery utilities
# Tests I2C and OneWire bus recovery functions

from unittest.mock import MagicMock, Mock, patch

import pytest


@pytest.fixture(autouse=True)
def reset_module_logger():
    """Reset the module-level logger cache before each test."""
    import src.shared.sensors.bus_recovery as bus_recovery_module

    bus_recovery_module._logger = None
    yield
    bus_recovery_module._logger = None


class TestRecoverI2CBus:
    """Tests for recover_i2c_bus function."""

    def test_successful_recovery(self):
        """I2C bus recovery succeeds with proper sequence."""
        from src.shared.sensors.bus_recovery import recover_i2c_bus

        scl_pin = Mock()
        sda_pin = Mock()

        with patch("src.shared.sensors.bus_recovery.digitalio") as mock_digitalio:
            with patch("src.shared.sensors.bus_recovery.busio"):
                with patch("src.shared.sensors.bus_recovery.time"):
                    # Setup mock for DigitalInOut
                    mock_scl_gpio = MagicMock()
                    mock_digitalio.DigitalInOut.return_value = mock_scl_gpio

                    result = recover_i2c_bus(scl_pin, sda_pin)

        assert result is True

    def test_toggles_scl_nine_times(self):
        """SCL is toggled 9 times during recovery."""
        from src.shared.sensors.bus_recovery import recover_i2c_bus

        scl_pin = Mock()
        sda_pin = Mock()

        # Track value assignments
        value_assignments = []

        with patch("src.shared.sensors.bus_recovery.digitalio") as mock_digitalio:
            with patch("src.shared.sensors.bus_recovery.busio"):
                with patch("src.shared.sensors.bus_recovery.time"):
                    mock_scl_gpio = MagicMock()
                    # Track each value assignment
                    type(mock_scl_gpio).value = property(
                        fget=lambda self: None,
                        fset=lambda self, v: value_assignments.append(v),
                    )
                    mock_digitalio.DigitalInOut.return_value = mock_scl_gpio

                    recover_i2c_bus(scl_pin, sda_pin)

        # 9 toggles (high/low each) = 18 assignments + 1 final high = 19 total
        assert len(value_assignments) == 19
        # Verify pattern: alternating True/False for 18, then final True
        for i in range(18):
            expected = i % 2 == 0  # True for even indices (high), False for odd (low)
            assert value_assignments[i] == expected
        assert value_assignments[18] is True  # Final release high

    def test_reinitializes_i2c_bus(self):
        """I2C bus is reinitialized after recovery."""
        from src.shared.sensors.bus_recovery import recover_i2c_bus

        scl_pin = Mock()
        sda_pin = Mock()

        with patch("src.shared.sensors.bus_recovery.digitalio") as mock_digitalio:
            with patch("src.shared.sensors.bus_recovery.busio") as mock_busio:
                with patch("src.shared.sensors.bus_recovery.time"):
                    mock_scl_gpio = MagicMock()
                    mock_digitalio.DigitalInOut.return_value = mock_scl_gpio
                    mock_i2c = MagicMock()
                    mock_busio.I2C.return_value = mock_i2c

                    recover_i2c_bus(scl_pin, sda_pin)

                    # Verify I2C was created with correct pins
                    mock_busio.I2C.assert_called_once_with(scl_pin, sda_pin)
                    # Verify I2C was immediately deinitialized
                    mock_i2c.deinit.assert_called_once()

    def test_returns_false_on_exception(self):
        """Returns False when recovery fails."""
        from src.shared.sensors.bus_recovery import recover_i2c_bus

        scl_pin = Mock()
        sda_pin = Mock()

        with patch("src.shared.sensors.bus_recovery.digitalio") as mock_digitalio:
            # Simulate hardware failure
            mock_digitalio.DigitalInOut.side_effect = RuntimeError("Pin in use")

            result = recover_i2c_bus(scl_pin, sda_pin)

        assert result is False

    def test_cleans_up_gpio_on_success(self):
        """GPIO is cleaned up after successful recovery."""
        from src.shared.sensors.bus_recovery import recover_i2c_bus

        scl_pin = Mock()
        sda_pin = Mock()

        with patch("src.shared.sensors.bus_recovery.digitalio") as mock_digitalio:
            with patch("src.shared.sensors.bus_recovery.busio"):
                with patch("src.shared.sensors.bus_recovery.time"):
                    mock_scl_gpio = MagicMock()
                    mock_digitalio.DigitalInOut.return_value = mock_scl_gpio

                    recover_i2c_bus(scl_pin, sda_pin)

                    # GPIO should be deinitialized
                    mock_scl_gpio.deinit.assert_called_once()

    def test_logs_recovery_attempt(self):
        """Recovery attempt is logged."""
        from src.shared.sensors.bus_recovery import recover_i2c_bus

        scl_pin = Mock()
        sda_pin = Mock()

        with patch("src.shared.sensors.bus_recovery.digitalio") as mock_digitalio:
            with patch("src.shared.sensors.bus_recovery.busio"):
                with patch("src.shared.sensors.bus_recovery.time"):
                    with patch("src.shared.sensors.bus_recovery.get_logger") as mock_get_logger:
                        mock_logger = Mock()
                        mock_get_logger.return_value = mock_logger
                        mock_scl_gpio = MagicMock()
                        mock_digitalio.DigitalInOut.return_value = mock_scl_gpio

                        recover_i2c_bus(scl_pin, sda_pin)

                        # Should log recovery info
                        assert mock_logger.info.call_count >= 1

    def test_logs_failure(self):
        """Failure is logged when recovery fails."""
        from src.shared.sensors.bus_recovery import recover_i2c_bus

        scl_pin = Mock()
        sda_pin = Mock()

        with patch("src.shared.sensors.bus_recovery.digitalio") as mock_digitalio:
            with patch("src.shared.sensors.bus_recovery.get_logger") as mock_get_logger:
                mock_logger = Mock()
                mock_get_logger.return_value = mock_logger
                mock_digitalio.DigitalInOut.side_effect = RuntimeError("failure")

                recover_i2c_bus(scl_pin, sda_pin)

                # Should log error
                assert mock_logger.error.call_count >= 1


class TestRecoverOneWireBus:
    """Tests for recover_onewire_bus function."""

    def test_successful_recovery(self):
        """OneWire bus recovery succeeds with proper sequence."""
        from src.shared.sensors.bus_recovery import recover_onewire_bus

        data_pin = Mock()

        with patch("src.shared.sensors.bus_recovery.digitalio") as mock_digitalio:
            with patch("src.shared.sensors.bus_recovery.onewireio"):
                with patch("src.shared.sensors.bus_recovery.time"):
                    mock_data_gpio = MagicMock()
                    mock_digitalio.DigitalInOut.return_value = mock_data_gpio

                    result = recover_onewire_bus(data_pin)

        assert result is True

    def test_pulls_data_low_for_500_microseconds(self):
        """Data line is pulled low for 500 microseconds."""
        from src.shared.sensors.bus_recovery import recover_onewire_bus

        data_pin = Mock()

        with patch("src.shared.sensors.bus_recovery.digitalio") as mock_digitalio:
            with patch("src.shared.sensors.bus_recovery.onewireio"):
                with patch("src.shared.sensors.bus_recovery.time") as mock_time:
                    mock_data_gpio = MagicMock()
                    mock_digitalio.DigitalInOut.return_value = mock_data_gpio

                    recover_onewire_bus(data_pin)

                    # Should sleep for 500 microseconds (0.0005 seconds)
                    # Check if any sleep call is approximately 500us
                    sleep_calls = mock_time.sleep.call_args_list
                    found_500us = any(abs(c[0][0] - 0.0005) < 0.0001 for c in sleep_calls if c[0])
                    assert found_500us, f"No 500us sleep found: {sleep_calls}"

    def test_reinitializes_onewire_bus(self):
        """OneWire bus is reinitialized after recovery."""
        from src.shared.sensors.bus_recovery import recover_onewire_bus

        data_pin = Mock()

        with patch("src.shared.sensors.bus_recovery.digitalio") as mock_digitalio:
            with patch("src.shared.sensors.bus_recovery.onewireio") as mock_onewire:
                with patch("src.shared.sensors.bus_recovery.time"):
                    mock_data_gpio = MagicMock()
                    mock_digitalio.DigitalInOut.return_value = mock_data_gpio
                    mock_ow = MagicMock()
                    mock_onewire.OneWire.return_value = mock_ow

                    recover_onewire_bus(data_pin)

                    # Verify OneWire was created with correct pin
                    mock_onewire.OneWire.assert_called_once_with(data_pin)
                    # Verify OneWire was immediately deinitialized
                    mock_ow.deinit.assert_called_once()

    def test_returns_false_on_exception(self):
        """Returns False when recovery fails."""
        from src.shared.sensors.bus_recovery import recover_onewire_bus

        data_pin = Mock()

        with patch("src.shared.sensors.bus_recovery.digitalio") as mock_digitalio:
            # Simulate hardware failure
            mock_digitalio.DigitalInOut.side_effect = RuntimeError("Pin in use")

            result = recover_onewire_bus(data_pin)

        assert result is False

    def test_cleans_up_gpio_on_success(self):
        """GPIO is cleaned up after successful recovery."""
        from src.shared.sensors.bus_recovery import recover_onewire_bus

        data_pin = Mock()

        with patch("src.shared.sensors.bus_recovery.digitalio") as mock_digitalio:
            with patch("src.shared.sensors.bus_recovery.onewireio"):
                with patch("src.shared.sensors.bus_recovery.time"):
                    mock_data_gpio = MagicMock()
                    mock_digitalio.DigitalInOut.return_value = mock_data_gpio

                    recover_onewire_bus(data_pin)

                    # GPIO should be deinitialized
                    mock_data_gpio.deinit.assert_called_once()

    def test_logs_recovery_attempt(self):
        """Recovery attempt is logged."""
        from src.shared.sensors.bus_recovery import recover_onewire_bus

        data_pin = Mock()

        with patch("src.shared.sensors.bus_recovery.digitalio") as mock_digitalio:
            with patch("src.shared.sensors.bus_recovery.onewireio"):
                with patch("src.shared.sensors.bus_recovery.time"):
                    with patch("src.shared.sensors.bus_recovery.get_logger") as mock_get_logger:
                        mock_logger = Mock()
                        mock_get_logger.return_value = mock_logger
                        mock_data_gpio = MagicMock()
                        mock_digitalio.DigitalInOut.return_value = mock_data_gpio

                        recover_onewire_bus(data_pin)

                        # Should log recovery info
                        assert mock_logger.info.call_count >= 1

    def test_logs_failure(self):
        """Failure is logged when recovery fails."""
        from src.shared.sensors.bus_recovery import recover_onewire_bus

        data_pin = Mock()

        with patch("src.shared.sensors.bus_recovery.digitalio") as mock_digitalio:
            with patch("src.shared.sensors.bus_recovery.get_logger") as mock_get_logger:
                mock_logger = Mock()
                mock_get_logger.return_value = mock_logger
                mock_digitalio.DigitalInOut.side_effect = RuntimeError("failure")

                recover_onewire_bus(data_pin)

                # Should log error
                assert mock_logger.error.call_count >= 1


class TestBusRecoveryEdgeCases:
    """Edge case tests for bus recovery functions."""

    def test_i2c_recovery_cleans_up_on_reinit_failure(self):
        """I2C GPIO is cleaned up even if reinit fails."""
        from src.shared.sensors.bus_recovery import recover_i2c_bus

        scl_pin = Mock()
        sda_pin = Mock()

        with patch("src.shared.sensors.bus_recovery.digitalio") as mock_digitalio:
            with patch("src.shared.sensors.bus_recovery.busio") as mock_busio:
                with patch("src.shared.sensors.bus_recovery.time"):
                    mock_scl_gpio = MagicMock()
                    mock_digitalio.DigitalInOut.return_value = mock_scl_gpio
                    # I2C reinit fails
                    mock_busio.I2C.side_effect = RuntimeError("I2C init fail")

                    result = recover_i2c_bus(scl_pin, sda_pin)

        assert result is False
        # GPIO should still be cleaned up
        mock_scl_gpio.deinit.assert_called_once()

    def test_onewire_recovery_cleans_up_on_reinit_failure(self):
        """OneWire GPIO is cleaned up even if reinit fails."""
        from src.shared.sensors.bus_recovery import recover_onewire_bus

        data_pin = Mock()

        with patch("src.shared.sensors.bus_recovery.digitalio") as mock_digitalio:
            with patch("src.shared.sensors.bus_recovery.onewireio") as mock_onewire:
                with patch("src.shared.sensors.bus_recovery.time"):
                    mock_data_gpio = MagicMock()
                    mock_digitalio.DigitalInOut.return_value = mock_data_gpio
                    # OneWire reinit fails
                    mock_onewire.OneWire.side_effect = RuntimeError("OneWire init fail")

                    result = recover_onewire_bus(data_pin)

        assert result is False
        # GPIO should still be cleaned up
        mock_data_gpio.deinit.assert_called_once()
