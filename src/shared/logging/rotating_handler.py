# Rotating file handler for logging
# CircuitPython compatible (no dataclasses, no type annotations in signatures)

import os

# Use adafruit_logging on CircuitPython, standard logging for tests
try:
    import adafruit_logging as logging
except ImportError:
    import logging


class RotatingFileHandler(logging.Handler):
    """
    A file handler that rotates log files based on size.

    Rotates when file exceeds maxBytes, keeping up to backupCount backup files.
    Total files = 1 (current) + backupCount (backups).

    Example with backupCount=2:
        - test.log (current)
        - test.log.1 (first backup)
        - test.log.2 (oldest backup)
    """

    def __init__(self, filename, maxBytes=128000, backupCount=2):
        """
        Initialize RotatingFileHandler.

        Args:
            filename: Path to the log file
            maxBytes: Maximum file size before rotation (default 125KB)
            backupCount: Number of backup files to keep (default 2)
        """
        super().__init__()
        self.filename = filename
        self.maxBytes = maxBytes
        self.backupCount = backupCount
        self._file = None
        self._open_file()

    def _open_file(self):
        """Open the log file for appending."""
        # Ensure directory exists
        dirname = os.path.dirname(self.filename)
        if dirname and not os.path.exists(dirname):
            os.makedirs(dirname)
        self._file = open(self.filename, "a")

    def emit(self, record):
        """
        Write a log record to the file.

        Args:
            record: LogRecord to write
        """
        try:
            # Check if rotation is needed before writing
            if self._should_rotate():
                self._do_rotation()

            # Format and write the record
            msg = self.format(record)
            self._file.write(msg + "\n")
            self._file.flush()
        except Exception:
            self.handleError(record)

    def _should_rotate(self):
        """Check if the file should be rotated."""
        if self.maxBytes <= 0:
            return False
        try:
            # Get current file size
            self._file.flush()
            size = os.path.getsize(self.filename)
            return size >= self.maxBytes
        except OSError:
            return False

    def _do_rotation(self):
        """Rotate the log files."""
        # Close current file
        if self._file:
            self._file.close()
            self._file = None

        # Rotate backup files
        # Delete oldest backup if it exists
        oldest = f"{self.filename}.{self.backupCount}"
        if os.path.exists(oldest):
            os.remove(oldest)

        # Shift existing backups
        for i in range(self.backupCount - 1, 0, -1):
            src = f"{self.filename}.{i}"
            dst = f"{self.filename}.{i + 1}"
            if os.path.exists(src):
                os.rename(src, dst)

        # Rename current log to .1
        if os.path.exists(self.filename):
            os.rename(self.filename, f"{self.filename}.1")

        # Reopen fresh log file
        self._open_file()

    def close(self):
        """Close the handler and release resources."""
        if self._file:
            self._file.close()
            self._file = None
        super().close()
