"""Tests for the logging module."""

from __future__ import annotations

import logging
from io import StringIO

import pytest


class TestGetLogger:
    """Tests for get_logger function."""

    def test_get_logger_can_be_imported(self) -> None:
        """get_logger can be imported from shared.logging."""
        from shared.logging import get_logger

        assert get_logger is not None

    def test_get_logger_returns_logger(self) -> None:
        """get_logger returns a logger instance."""
        from shared.logging import get_logger

        logger = get_logger("test-device")
        assert logger is not None
        # Should have a name attribute (logging.Logger interface)
        assert hasattr(logger, "name")

    def test_get_logger_sets_debug_level_when_debug_logging_true(self) -> None:
        """get_logger sets DEBUG level when debug_logging=True."""
        from shared.logging import get_logger

        logger = get_logger("test-device", debug_logging=True)
        assert logger.level == logging.DEBUG

    def test_get_logger_sets_info_level_when_debug_logging_false(self) -> None:
        """get_logger sets INFO level when debug_logging=False."""
        from shared.logging import get_logger

        logger = get_logger("test-device", debug_logging=False)
        assert logger.level == logging.INFO

    def test_get_logger_default_level_is_info(self) -> None:
        """get_logger defaults to INFO level."""
        from shared.logging import get_logger

        logger = get_logger("test-device")
        assert logger.level == logging.INFO

    def test_get_logger_has_stream_handler(self) -> None:
        """get_logger adds a StreamHandler."""
        from shared.logging import get_logger

        logger = get_logger("test-device-handler")
        # Check at least one handler is a StreamHandler
        has_stream = any(isinstance(h, logging.StreamHandler) for h in logger.handlers)
        assert has_stream, f"Expected StreamHandler but got: {logger.handlers}"

    def test_get_logger_includes_device_id_in_messages(self) -> None:
        """Logger includes device_id in formatted messages."""
        from shared.logging import get_logger

        # Create a logger and capture its output
        logger = get_logger("my-pool-node")

        # Create a string buffer to capture log output
        buffer = StringIO()
        # Find and replace the stream handler's stream
        for handler in logger.handlers:
            if isinstance(handler, logging.StreamHandler):
                handler.stream = buffer
                break

        logger.info("Test message")
        output = buffer.getvalue()

        assert "my-pool-node" in output
        assert "Test message" in output


class TestIsWritable:
    """Tests for is_writable function."""

    def test_is_writable_can_be_imported(self) -> None:
        """is_writable can be imported from shared.logging."""
        from shared.logging import is_writable

        assert is_writable is not None

    def test_is_writable_returns_true_for_writable_directory(
        self, tmp_path: pytest.TempPathFactory
    ) -> None:
        """is_writable returns True for writable directory."""
        from shared.logging import is_writable

        result = is_writable(str(tmp_path))
        assert result is True

    def test_is_writable_returns_false_for_nonexistent_directory(self) -> None:
        """is_writable returns False for non-existent directory."""
        from shared.logging import is_writable

        result = is_writable("/nonexistent/path/that/does/not/exist")
        assert result is False

    def test_is_writable_returns_false_for_readonly_directory(
        self, tmp_path: pytest.TempPathFactory
    ) -> None:
        """is_writable returns False for read-only directory."""
        import os
        import stat

        from shared.logging import is_writable

        # Create a read-only directory
        readonly_dir = tmp_path / "readonly"
        readonly_dir.mkdir()
        # Remove write permission
        os.chmod(readonly_dir, stat.S_IRUSR | stat.S_IXUSR)

        try:
            result = is_writable(str(readonly_dir))
            assert result is False
        finally:
            # Restore write permission for cleanup
            os.chmod(readonly_dir, stat.S_IRWXU)

    def test_is_writable_handles_exceptions_gracefully(self) -> None:
        """is_writable returns False on exceptions without raising."""
        from shared.logging import is_writable

        # None should not raise, just return False
        result = is_writable(None)  # type: ignore[arg-type]
        assert result is False


class TestRotatingFileHandler:
    """Tests for RotatingFileHandler class."""

    def test_rotating_file_handler_can_be_imported(self) -> None:
        """RotatingFileHandler can be imported from shared.logging."""
        from shared.logging import RotatingFileHandler

        assert RotatingFileHandler is not None

    def test_rotating_file_handler_creates_file(self, tmp_path: pytest.TempPathFactory) -> None:
        """RotatingFileHandler creates the log file."""
        from shared.logging import RotatingFileHandler

        log_file = tmp_path / "test.log"
        handler = RotatingFileHandler(str(log_file))
        handler.close()

        assert log_file.exists()

    def test_rotating_file_handler_writes_to_file(self, tmp_path: pytest.TempPathFactory) -> None:
        """RotatingFileHandler writes log records to file."""
        from shared.logging import RotatingFileHandler

        log_file = tmp_path / "test.log"
        handler = RotatingFileHandler(str(log_file))
        handler.setFormatter(logging.Formatter("%(message)s"))

        # Create a log record
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        handler.emit(record)
        handler.close()

        content = log_file.read_text()
        assert "Test message" in content

    def test_rotating_file_handler_rotates_at_max_bytes(
        self, tmp_path: pytest.TempPathFactory
    ) -> None:
        """RotatingFileHandler rotates when file exceeds maxBytes."""
        from shared.logging import RotatingFileHandler

        log_file = tmp_path / "test.log"
        # Use small maxBytes for testing (100 bytes)
        handler = RotatingFileHandler(str(log_file), maxBytes=100, backupCount=2)
        handler.setFormatter(logging.Formatter("%(message)s"))

        # Write enough data to trigger rotation
        for i in range(10):
            record = logging.LogRecord(
                name="test",
                level=logging.INFO,
                pathname="",
                lineno=0,
                msg=f"Message number {i:04d} with some padding",
                args=(),
                exc_info=None,
            )
            handler.emit(record)

        handler.close()

        # Check that backup files were created
        backup1 = tmp_path / "test.log.1"
        assert backup1.exists(), "First backup file should exist"

    def test_rotating_file_handler_keeps_max_backup_files(
        self, tmp_path: pytest.TempPathFactory
    ) -> None:
        """RotatingFileHandler keeps only backupCount backup files."""
        from shared.logging import RotatingFileHandler

        log_file = tmp_path / "test.log"
        # Use small maxBytes and 2 backups
        handler = RotatingFileHandler(str(log_file), maxBytes=50, backupCount=2)
        handler.setFormatter(logging.Formatter("%(message)s"))

        # Write enough data to trigger multiple rotations
        for i in range(20):
            record = logging.LogRecord(
                name="test",
                level=logging.INFO,
                pathname="",
                lineno=0,
                msg=f"Message {i:04d} with padding text here",
                args=(),
                exc_info=None,
            )
            handler.emit(record)

        handler.close()

        # Should have test.log, test.log.1, test.log.2 (3 total files)
        assert log_file.exists()
        assert (tmp_path / "test.log.1").exists()
        assert (tmp_path / "test.log.2").exists()
        # Should NOT have test.log.3
        assert not (tmp_path / "test.log.3").exists()

    def test_rotating_file_handler_default_values(self, tmp_path: pytest.TempPathFactory) -> None:
        """RotatingFileHandler has correct default values."""
        from shared.logging import RotatingFileHandler

        log_file = tmp_path / "test.log"
        handler = RotatingFileHandler(str(log_file))

        assert handler.maxBytes == 128000  # 125KB
        assert handler.backupCount == 2  # 3 total files
        handler.close()


class TestAddFileLogging:
    """Tests for add_file_logging function."""

    def test_add_file_logging_can_be_imported(self) -> None:
        """add_file_logging can be imported from shared.logging."""
        from shared.logging import add_file_logging

        assert add_file_logging is not None

    def test_add_file_logging_adds_handler_to_logger(
        self, tmp_path: pytest.TempPathFactory
    ) -> None:
        """add_file_logging adds a RotatingFileHandler to the logger."""
        from shared.logging import RotatingFileHandler, add_file_logging, get_logger

        log_file = tmp_path / "test.log"
        logger = get_logger("test-file-logging")

        initial_count = len(logger.handlers)
        result = add_file_logging(logger, str(log_file))

        assert result is True
        assert len(logger.handlers) == initial_count + 1

        # Check the added handler is a RotatingFileHandler
        new_handler = logger.handlers[-1]
        assert isinstance(new_handler, RotatingFileHandler)

        # Cleanup
        new_handler.close()

    def test_add_file_logging_returns_false_for_readonly(
        self, tmp_path: pytest.TempPathFactory
    ) -> None:
        """add_file_logging returns False for read-only directory."""
        import os
        import stat

        from shared.logging import add_file_logging, get_logger

        # Create a read-only directory
        readonly_dir = tmp_path / "readonly"
        readonly_dir.mkdir()
        os.chmod(readonly_dir, stat.S_IRUSR | stat.S_IXUSR)

        logger = get_logger("test-readonly")
        log_file = readonly_dir / "test.log"

        try:
            result = add_file_logging(logger, str(log_file))
            assert result is False
        finally:
            os.chmod(readonly_dir, stat.S_IRWXU)

    def test_add_file_logging_writes_to_file(self, tmp_path: pytest.TempPathFactory) -> None:
        """add_file_logging creates a working file handler."""
        from shared.logging import add_file_logging, get_logger

        log_file = tmp_path / "test.log"
        logger = get_logger("test-file-write")
        add_file_logging(logger, str(log_file))

        logger.info("Test message to file")

        # Find and close the file handler
        for handler in logger.handlers:
            if hasattr(handler, "filename") and handler.filename == str(log_file):
                handler.close()
                break

        content = log_file.read_text()
        assert "Test message to file" in content
