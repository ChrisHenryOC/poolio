# Logger configuration for Poolio IoT system
# CircuitPython compatible (no dataclasses, no type annotations in signatures)

# Use adafruit_logging on CircuitPython, standard logging for tests
try:
    import adafruit_logging as logging
except ImportError:
    import logging


def get_logger(device_id, debug_logging=False):
    """
    Get a configured logger for a device.

    Creates a logger with the device_id included in all log messages.
    A StreamHandler for console output is always added.

    Args:
        device_id: Device identifier to include in log messages
        debug_logging: If True, set level to DEBUG; otherwise INFO

    Returns:
        Configured logger instance
    """
    # Create logger with unique name based on device_id
    logger = logging.getLogger(device_id)

    # Set log level
    if debug_logging:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    # Only add handler if this logger doesn't have direct handlers
    # (avoid duplicates on repeated calls)
    # Note: Use len(logger.handlers) instead of logger.hasHandlers()
    # because hasHandlers() includes parent loggers
    if len(logger.handlers) == 0:
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)

        # Create formatter with device_id
        # Format: "LEVEL device_id: message"
        formatter = logging.Formatter(fmt=f"%(levelname)s {device_id}: %(message)s")
        console_handler.setFormatter(formatter)

        logger.addHandler(console_handler)

    return logger
