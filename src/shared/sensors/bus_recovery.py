# Bus recovery utilities for I2C and OneWire sensors
# CircuitPython compatible (no type annotations in signatures)

import time

# Hardware imports - will fail in test environment, mocked in tests
try:
    import busio
    import digitalio
    import onewireio
except ImportError:
    # Running in test environment - modules will be mocked
    busio = None
    digitalio = None
    onewireio = None

# Import logger from our logging module
try:
    from ..logging import get_logger
except ImportError:
    # Fallback for standalone use
    def get_logger(name):
        import logging

        return logging.getLogger(name)


# Module-level logger
_logger = None


def _get_module_logger():
    """Get or create the module logger."""
    global _logger
    if _logger is None:
        _logger = get_logger("sensors")
    return _logger


def recover_i2c_bus(scl_pin, sda_pin):
    """
    Attempt I2C bus recovery by toggling SCL to clear stuck slaves.

    The I2C protocol can get stuck when a slave holds SDA low waiting
    for clocks. Toggling SCL 9 times (one full byte + ACK) allows the
    slave to complete its transaction and release the bus.

    Recovery sequence:
    1. Configure SCL as GPIO output
    2. Toggle SCL high/low 9 times
    3. Release SCL (deinit GPIO)
    4. Reinitialize I2C bus

    Args:
        scl_pin: Board pin object for SCL (e.g., board.SCL)
        sda_pin: Board pin object for SDA (e.g., board.SDA)

    Returns:
        True if recovery succeeded, False if an error occurred
    """
    logger = _get_module_logger()
    logger.info("Attempting I2C bus recovery")

    scl_gpio = None
    try:
        # Step 1: Configure SCL as GPIO output
        scl_gpio = digitalio.DigitalInOut(scl_pin)
        scl_gpio.direction = digitalio.Direction.OUTPUT

        # Step 2: Toggle SCL 9 times to clock out stuck slave
        logger.debug("Toggling SCL 9 times")
        for _ in range(9):
            scl_gpio.value = True
            time.sleep(0.00001)  # 10 microseconds high
            scl_gpio.value = False
            time.sleep(0.00001)  # 10 microseconds low

        # Release SCL high (idle state)
        scl_gpio.value = True
        time.sleep(0.00001)

        # Step 3: Cleanup GPIO before reinit
        scl_gpio.deinit()
        scl_gpio = None

        # Step 4: Reinitialize I2C bus
        logger.debug("Reinitializing I2C bus")
        i2c = busio.I2C(scl_pin, sda_pin)
        # Immediately deinit - caller will create their own I2C instance
        i2c.deinit()

        logger.info("I2C bus recovery successful")
        return True

    except (RuntimeError, OSError, ValueError) as e:
        logger.error("I2C bus recovery failed: %s", e)
        return False

    finally:
        # Ensure GPIO is cleaned up
        if scl_gpio is not None:
            try:
                scl_gpio.deinit()
            except Exception:
                pass  # Ignore cleanup errors


def recover_onewire_bus(data_pin):
    """
    Attempt OneWire bus recovery by sending a reset pulse.

    The OneWire protocol uses a reset pulse (holding data low for
    480-960 microseconds) to reset all devices on the bus.

    Recovery sequence:
    1. Configure data pin as GPIO output
    2. Pull data low for 500 microseconds (reset pulse)
    3. Release data pin (deinit GPIO)
    4. Reinitialize OneWire bus

    Args:
        data_pin: Board pin object for data (e.g., board.D10)

    Returns:
        True if recovery succeeded, False if an error occurred
    """
    logger = _get_module_logger()
    logger.info("Attempting OneWire bus recovery")

    data_gpio = None
    try:
        # Step 1: Configure data pin as GPIO output
        data_gpio = digitalio.DigitalInOut(data_pin)
        data_gpio.direction = digitalio.Direction.OUTPUT

        # Step 2: Pull data low for 500 microseconds (reset pulse)
        logger.debug("Sending reset pulse (500us low)")
        data_gpio.value = False
        time.sleep(0.0005)  # 500 microseconds

        # Release data line (high-impedance via input mode)
        data_gpio.direction = digitalio.Direction.INPUT

        # Wait for presence pulse window
        time.sleep(0.0001)  # 100 microseconds

        # Step 3: Cleanup GPIO before reinit
        data_gpio.deinit()
        data_gpio = None

        # Step 4: Reinitialize OneWire bus
        logger.debug("Reinitializing OneWire bus")
        ow = onewireio.OneWire(data_pin)
        # Immediately deinit - caller will create their own OneWire instance
        ow.deinit()

        logger.info("OneWire bus recovery successful")
        return True

    except (RuntimeError, OSError, ValueError) as e:
        logger.error("OneWire bus recovery failed: %s", e)
        return False

    finally:
        # Ensure GPIO is cleaned up
        if data_gpio is not None:
            try:
                data_gpio.deinit()
            except Exception:
                pass  # Ignore cleanup errors
