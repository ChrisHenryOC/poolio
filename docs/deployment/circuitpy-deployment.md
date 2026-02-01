# CircuitPython Deployment Guide

This guide covers deploying code to CircuitPython-based nodes (Valve Node, Display Node).

## Prerequisites

1. **CircuitPython device** - ESP32-S3 Feather or similar with CircuitPython installed
2. **Python environment** - Python 3.x with dependencies (managed by uv)
3. **Device mounted** - CIRCUITPY drive must be mounted
4. **Adafruit IO setup** - Feeds created via `scripts/adafruit_io_setup.py`

## Quick Start

```bash
# Deploy valve-node to nonprod environment
python circuitpython/deploy.py --target valve-node --env nonprod --source

# Deploy display-node to production
python circuitpython/deploy.py --target display-node --env prod --source
```

## Deployment Script

The `circuitpython/deploy.py` script handles the full deployment.

### Arguments

| Argument | Options | Description |
|----------|---------|-------------|
| `--target`, `-t` | `valve-node`, `display-node`, `pool-node`, `test` | Target device type |
| `--env`, `-e` | `prod`, `nonprod` | Environment (deploys matching config.json) |
| `--source`, `-s` | flag | Also deploy project source code |
| `--tests` | flag | Also deploy device tests |
| `--device`, `-d` | path | Device mount path (default: auto-detect) |

### What It Does

1. **Downloads bundle** - Fetches Adafruit CircuitPython library bundle if needed
2. **Detects device** - Finds CIRCUITPY mount point (macOS or Linux)
3. **Checks settings.toml** - Warns if secrets file is missing
4. **Deploys libraries** - Copies required libraries from bundle to `lib/`
5. **Deploys source** - Copies `src/shared/` to device (with `--source`)
6. **Deploys config** - Copies environment-specific `config.json` (with `--env`)

### Example Output

```text
Device: /Volumes/CIRCUITPY
Target: valve-node
Environment: nonprod
  Found: settings.toml (secrets preserved)

Deploying 12 libraries to /Volumes/CIRCUITPY/lib...
  Copied: adafruit_minimqtt/
  Copied: adafruit_io/
  ...

Deploying source code...
  Copied: shared/

Deploying configuration...
  Deployed: config.json (nonprod)

Deployment complete!
```

## Configuration Files

### settings.toml (Secrets - Manual Setup)

Create this file manually on the device. It contains secrets and is **never overwritten**
by deployments.

```toml
# WiFi credentials
CIRCUITPY_WIFI_SSID = "your_wifi_ssid"
CIRCUITPY_WIFI_PASSWORD = "your_wifi_password"

# Adafruit IO credentials
AIO_USERNAME = "your_adafruit_io_username"
AIO_KEY = "your_adafruit_io_key"

# Timezone (for scheduling)
TIMEZONE = "America/Los_Angeles"
```

### config.json (Environment Config - Auto-deployed)

Environment-specific configuration is stored in `circuitpython/configs/<node-type>/<environment>/config.json`
and copied to the device during deployment.

Example (`circuitpython/configs/valve-node/nonprod/config.json`):

```json
{
  "environment": "nonprod",
  "device_id": "valve-node-dev",
  "device_type": "valve-node",
  "feed_group": "poolio-nonprod",
  "debug": true,
  "publish_interval_seconds": 30,
  "watchdog_timeout_seconds": 120,
  "valve": {
    "max_fill_duration_minutes": 5,
    "cooldown_minutes": 1
  }
}
```

## Environment Differences

| Setting | Production | Non-Production |
|---------|------------|----------------|
| feed_group | `poolio` | `poolio-nonprod` |
| debug | `false` | `true` |
| publish_interval | 60s | 30s |
| valve max_fill | 30 min | 5 min |

## Device Mount Points

The script auto-detects the CIRCUITPY mount:

| Platform | Mount Point |
|----------|-------------|
| macOS | `/Volumes/CIRCUITPY` |
| Linux | `/media/$USER/CIRCUITPY` |
| Linux (alt) | `/run/media/$USER/CIRCUITPY` |

## Troubleshooting

### Device Not Found

```text
ERROR: CIRCUITPY device not found.
```

- Ensure device is connected via USB
- Check if device appears in file manager
- Try a different USB port or cable
- Specify path manually: `--device /path/to/CIRCUITPY`

### Settings.toml Missing

```text
WARNING: settings.toml not found on device
```

This is expected on first deployment. Create `settings.toml` with your secrets
before the device can connect to WiFi and Adafruit IO.

### Library Not Found in Bundle

```text
WARNING: Libraries not found in bundle: some_library
```

- Verify the library name in your requirements file
- Some libraries may need manual installation
- Check the Adafruit CircuitPython bundle contents

## Common Deployment Scenarios

```bash
# Development: Deploy with source and test framework
python circuitpython/deploy.py --target valve-node --env nonprod --source --tests

# Production: Deploy without tests
python circuitpython/deploy.py --target valve-node --env prod --source

# Libraries only (no source or config)
python circuitpython/deploy.py --target valve-node

# List available targets
python circuitpython/deploy.py --list-targets

# Download bundle only (no device needed)
python circuitpython/deploy.py --download-only
```

## Post-Deployment

After deployment:

1. **Verify settings.toml** - Ensure secrets are configured
2. **Reset device** - Press reset button or Ctrl+D in REPL
3. **Monitor output** - `python scripts/serial_monitor.py`

## See Also

- [Adafruit IO Setup](./adafruit-io-nonprod-setup.md) - Creating feeds
- [Architecture: Deployment](../architecture.md#deployment) - Deployment architecture
