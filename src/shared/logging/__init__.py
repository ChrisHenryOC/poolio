# Logging module for Poolio IoT system
# CircuitPython compatible wrapper around adafruit_logging

from .filesystem import add_file_logging, is_writable
from .logger import get_logger
from .rotating_handler import RotatingFileHandler

__all__ = [
    "get_logger",
    "add_file_logging",
    "is_writable",
    "RotatingFileHandler",
]
