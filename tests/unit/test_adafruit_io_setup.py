"""Tests for the Adafruit IO setup script."""

import sys
from unittest.mock import MagicMock, patch

import pytest

# Mock Adafruit_IO before importing the module - must be done before import
# ruff: noqa: E402
_mock_client_class = MagicMock()
mock_request_error = type("RequestError", (Exception,), {})
sys.modules["Adafruit_IO"] = MagicMock(Client=_mock_client_class, RequestError=mock_request_error)

# Now import the module under test (after mocking)
sys.path.insert(0, "scripts")
from adafruit_io_setup import (
    FEEDS,
    create_feed,
    create_group,
    get_group_name,
    main,
)


class TestGetGroupName:
    """Tests for get_group_name function."""

    def test_prod_environment_returns_poolio(self):
        """Production environment returns 'poolio' without prefix."""
        assert get_group_name("prod") == "poolio"

    def test_nonprod_environment_returns_poolio_nonprod(self):
        """Nonprod environment returns 'poolio-nonprod'."""
        assert get_group_name("nonprod") == "poolio-nonprod"

    def test_dev_environment_returns_poolio_dev(self):
        """Dev environment returns 'poolio-dev'."""
        assert get_group_name("dev") == "poolio-dev"

    def test_test_environment_returns_poolio_test(self):
        """Test environment returns 'poolio-test'."""
        assert get_group_name("test") == "poolio-test"


class TestCreateGroup:
    """Tests for create_group function."""

    def test_group_exists_returns_true(self, capsys):
        """When group already exists, returns True and prints message."""
        mock_client = MagicMock()
        mock_client.groups.return_value = {"name": "poolio-nonprod"}

        result = create_group(mock_client, "poolio-nonprod", "Test description")

        assert result is True
        mock_client.groups.assert_called_once_with("poolio-nonprod")
        mock_client.create_group.assert_not_called()
        captured = capsys.readouterr()
        assert "already exists" in captured.out

    def test_group_not_exists_creates_group(self, capsys):
        """When group doesn't exist, creates it and returns True."""
        mock_client = MagicMock()
        # First call raises RequestError (group doesn't exist)
        mock_client.groups.side_effect = mock_request_error()
        mock_client.create_group.return_value = {"name": "poolio-nonprod"}

        result = create_group(mock_client, "poolio-nonprod", "Test description")

        assert result is True
        mock_client.create_group.assert_called_once()
        captured = capsys.readouterr()
        assert "Created group" in captured.out

    def test_group_creation_fails_returns_false(self, capsys):
        """When group creation fails, returns False and prints error."""
        mock_client = MagicMock()
        mock_client.groups.side_effect = mock_request_error()
        mock_client.create_group.side_effect = mock_request_error()

        result = create_group(mock_client, "poolio-nonprod", "Test description")

        assert result is False
        captured = capsys.readouterr()
        assert "ERROR creating group" in captured.out


class TestCreateFeed:
    """Tests for create_feed function."""

    def test_feed_exists_returns_true(self, capsys):
        """When feed already exists, returns True and prints message."""
        mock_client = MagicMock()
        mock_client.feeds.return_value = {"key": "poolio-nonprod.gateway"}

        result = create_feed(mock_client, "poolio-nonprod", "gateway", "Test description")

        assert result is True
        mock_client.feeds.assert_called_once_with("poolio-nonprod.gateway")
        mock_client.create_feed.assert_not_called()
        captured = capsys.readouterr()
        assert "already exists" in captured.out

    def test_feed_not_exists_creates_feed(self, capsys):
        """When feed doesn't exist, creates it and returns True."""
        mock_client = MagicMock()
        mock_client.feeds.side_effect = mock_request_error()
        mock_client.create_feed.return_value = {"key": "poolio-nonprod.gateway"}

        result = create_feed(mock_client, "poolio-nonprod", "gateway", "Test description")

        assert result is True
        mock_client.create_feed.assert_called_once()
        # Verify group_key was passed correctly
        call_args = mock_client.create_feed.call_args
        assert call_args[1]["group_key"] == "poolio-nonprod"
        captured = capsys.readouterr()
        assert "Created feed" in captured.out

    def test_feed_creation_fails_returns_false(self, capsys):
        """When feed creation fails, returns False and prints error."""
        mock_client = MagicMock()
        mock_client.feeds.side_effect = mock_request_error()
        mock_client.create_feed.side_effect = mock_request_error()

        result = create_feed(mock_client, "poolio-nonprod", "gateway", "Test description")

        assert result is False
        captured = capsys.readouterr()
        assert "ERROR creating feed" in captured.out


class TestFeedsConstant:
    """Tests for the FEEDS constant."""

    def test_feeds_contains_expected_count(self):
        """FEEDS list contains 12 feeds."""
        assert len(FEEDS) == 12

    def test_feeds_contains_gateway(self):
        """FEEDS list contains gateway feed."""
        feed_names = [name for name, _ in FEEDS]
        assert "gateway" in feed_names

    def test_feeds_contains_config_feeds(self):
        """FEEDS list contains all config feeds."""
        feed_names = [name for name, _ in FEEDS]
        assert "config" in feed_names
        assert "config-pool-node" in feed_names
        assert "config-valve-node" in feed_names
        assert "config-display-node" in feed_names

    def test_poolvalveruntime_description_uses_minutes(self):
        """poolvalveruntime description uses minutes, not seconds."""
        for name, desc in FEEDS:
            if name == "poolvalveruntime":
                assert "minutes" in desc.lower()
                assert "seconds" not in desc.lower()
                break
        else:
            pytest.fail("poolvalveruntime feed not found")


class TestMain:
    """Tests for main function argument parsing."""

    def test_missing_username_returns_error(self, capsys):
        """Missing username returns error code 1."""
        with patch.dict("os.environ", {}, clear=True):
            with patch("sys.argv", ["prog", "--environment", "nonprod"]):
                result = main()

        assert result == 1
        captured = capsys.readouterr()
        assert "Username required" in captured.out

    def test_missing_key_returns_error(self, capsys):
        """Missing API key returns error code 1."""
        with patch.dict("os.environ", {"AIO_USERNAME": "testuser"}, clear=True):
            with patch("sys.argv", ["prog", "--environment", "nonprod"]):
                result = main()

        assert result == 1
        captured = capsys.readouterr()
        assert "API key required" in captured.out

    def test_env_vars_used_when_args_not_provided(self):
        """Environment variables are used when CLI args not provided."""
        with patch.dict("os.environ", {"AIO_USERNAME": "envuser", "AIO_KEY": "envkey"}, clear=True):
            with patch("sys.argv", ["prog", "--environment", "nonprod"]):
                with patch("adafruit_io_setup.setup_feeds", return_value=0) as mock_setup:
                    result = main()

        assert result == 0
        mock_setup.assert_called_once_with("envuser", "envkey", "nonprod")

    def test_cli_args_override_env_vars(self):
        """CLI arguments override environment variables."""
        with patch.dict("os.environ", {"AIO_USERNAME": "envuser", "AIO_KEY": "envkey"}, clear=True):
            with patch(
                "sys.argv",
                [
                    "prog",
                    "--username",
                    "cliuser",
                    "--key",
                    "clikey",
                    "--environment",
                    "prod",
                ],
            ):
                with patch("adafruit_io_setup.setup_feeds", return_value=0) as mock_setup:
                    result = main()

        assert result == 0
        mock_setup.assert_called_once_with("cliuser", "clikey", "prod")

    def test_verify_flag_calls_verify_feeds(self):
        """--verify flag calls verify_feeds instead of setup_feeds."""
        with patch.dict(
            "os.environ", {"AIO_USERNAME": "testuser", "AIO_KEY": "testkey"}, clear=True
        ):
            with patch("sys.argv", ["prog", "--environment", "nonprod", "--verify"]):
                with patch("adafruit_io_setup.verify_feeds", return_value=0) as mock_verify:
                    with patch("adafruit_io_setup.setup_feeds") as mock_setup:
                        result = main()

        assert result == 0
        mock_verify.assert_called_once_with("testuser", "testkey", "nonprod")
        mock_setup.assert_not_called()
