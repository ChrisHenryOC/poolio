# Filesystem utilities for logging
# CircuitPython compatible (no dataclasses, no type annotations in signatures)

import os

from .rotating_handler import RotatingFileHandler


def is_writable(path):
    """
    Check if a path is writable.

    Attempts to create a temporary file in the directory to verify
    write access. Handles read-only filesystems gracefully.

    Args:
        path: Directory path to check

    Returns:
        True if writable, False otherwise
    """
    try:
        if path is None:
            return False

        # Check if directory exists
        if not os.path.isdir(path):
            return False

        # Try to create a temporary file
        test_file = os.path.join(path, ".write_test")
        try:
            with open(test_file, "w") as f:
                f.write("test")
            os.remove(test_file)
            return True
        except OSError:
            return False
    except Exception:
        # Catch any unexpected exceptions
        return False


def add_file_logging(logger, log_path):
    """
    Add file logging to a logger.

    Creates a RotatingFileHandler and adds it to the logger if the
    log directory is writable. Silently fails if not writable.

    Args:
        logger: Logger instance to add file handler to
        log_path: Path for the log file

    Returns:
        True if file logging was added, False otherwise
    """
    try:
        # Get directory from log path
        log_dir = os.path.dirname(log_path)
        if not log_dir:
            log_dir = "."

        # Check if directory is writable
        if not is_writable(log_dir):
            return False

        # Create rotating file handler
        handler = RotatingFileHandler(log_path)

        # Use same formatter as other handlers if available
        if logger.handlers and logger.handlers[0].formatter:
            handler.setFormatter(logger.handlers[0].formatter)

        logger.addHandler(handler)
        return True
    except Exception:
        return False
