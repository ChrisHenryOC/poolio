"""Tests for the CircuitPython deploy script."""

import json
import sys
from pathlib import Path

import pytest

# Import the module under test
sys.path.insert(0, "circuitpython")
from deploy import check_settings_toml, deploy_config


class TestCheckSettingsToml:
    """Tests for check_settings_toml function."""

    def test_settings_exists_returns_true(self, tmp_path: Path, capsys):
        """When settings.toml exists, returns True."""
        settings_file = tmp_path / "settings.toml"
        settings_file.write_text('WIFI_SSID = "test"')

        result = check_settings_toml(tmp_path)

        assert result is True
        captured = capsys.readouterr()
        assert "settings.toml (secrets preserved)" in captured.out

    def test_settings_missing_returns_false(self, tmp_path: Path, capsys):
        """When settings.toml is missing, returns False and prints warning."""
        result = check_settings_toml(tmp_path)

        assert result is False
        captured = capsys.readouterr()
        assert "WARNING: settings.toml not found" in captured.out
        assert "CIRCUITPY_WIFI_SSID" in captured.out


class TestDeployConfig:
    """Tests for deploy_config function."""

    @pytest.fixture
    def config_dir(self, tmp_path: Path, monkeypatch):
        """Create a temporary config directory structure."""
        configs_dir = tmp_path / "configs"
        configs_dir.mkdir()

        # Create valve-node/nonprod config
        valve_nonprod = configs_dir / "valve-node" / "nonprod"
        valve_nonprod.mkdir(parents=True)
        config_data = {
            "environment": "nonprod",
            "device_id": "valve-node-dev",
            "device_type": "valve-node",
        }
        (valve_nonprod / "config.json").write_text(json.dumps(config_data))

        # Create valve-node/prod config
        valve_prod = configs_dir / "valve-node" / "prod"
        valve_prod.mkdir(parents=True)
        prod_config = {
            "environment": "prod",
            "device_id": "valve-node-01",
            "device_type": "valve-node",
        }
        (valve_prod / "config.json").write_text(json.dumps(prod_config))

        # Patch CONFIGS_DIR to use our temp directory
        monkeypatch.setattr("deploy.CONFIGS_DIR", configs_dir)

        return configs_dir

    def test_successful_deployment(self, tmp_path: Path, config_dir: Path, capsys):
        """Config file is copied to device on success."""
        device_path = tmp_path / "device"
        device_path.mkdir()

        result = deploy_config(device_path, "valve-node", "nonprod")

        assert result is True
        config_dest = device_path / "config.json"
        assert config_dest.exists()
        data = json.loads(config_dest.read_text())
        assert data["environment"] == "nonprod"
        captured = capsys.readouterr()
        assert "Deployed: config.json (nonprod)" in captured.out

    def test_unknown_target_returns_false(self, tmp_path: Path, config_dir: Path, capsys):
        """Unknown target returns False with error message."""
        device_path = tmp_path / "device"
        device_path.mkdir()

        result = deploy_config(device_path, "unknown-node", "nonprod")

        assert result is False
        captured = capsys.readouterr()
        assert "Unknown target 'unknown-node'" in captured.out
        assert "valve-node" in captured.out  # Shows available targets

    def test_missing_config_returns_false(self, tmp_path: Path, config_dir: Path, capsys):
        """Missing config file for valid target returns False."""
        device_path = tmp_path / "device"
        device_path.mkdir()

        # valve-node exists but no "staging" environment
        result = deploy_config(device_path, "valve-node", "staging")

        # Note: staging isn't in VALID_ENVIRONMENTS, but if somehow passed,
        # the config won't exist
        assert result is False

    def test_invalid_json_returns_false(self, tmp_path: Path, config_dir: Path, capsys):
        """Invalid JSON in config file returns False."""
        device_path = tmp_path / "device"
        device_path.mkdir()

        # Corrupt the config file
        bad_config = config_dir / "valve-node" / "nonprod" / "config.json"
        bad_config.write_text("{ invalid json }")

        result = deploy_config(device_path, "valve-node", "nonprod")

        assert result is False
        captured = capsys.readouterr()
        assert "Invalid JSON" in captured.out

    def test_environment_mismatch_warns_but_continues(
        self, tmp_path: Path, config_dir: Path, capsys
    ):
        """Environment mismatch in config prints warning but still deploys."""
        device_path = tmp_path / "device"
        device_path.mkdir()

        # Create config with wrong environment field
        mismatched_config = config_dir / "valve-node" / "nonprod" / "config.json"
        mismatched_config.write_text(json.dumps({"environment": "prod"}))

        result = deploy_config(device_path, "valve-node", "nonprod")

        assert result is True  # Still deploys
        captured = capsys.readouterr()
        assert "Config environment mismatch" in captured.out
        assert "Expected: nonprod" in captured.out
        assert "Found: prod" in captured.out

    def test_path_traversal_prevented(self, tmp_path: Path, config_dir: Path, capsys):
        """Path traversal in target parameter is rejected."""
        device_path = tmp_path / "device"
        device_path.mkdir()

        result = deploy_config(device_path, "../../../etc", "nonprod")

        assert result is False
        captured = capsys.readouterr()
        assert "Unknown target" in captured.out
