# Default configuration values per node type
# CircuitPython compatible (no dataclasses, no type annotations in signatures)

from typing import Any

# Node type defaults per architecture.md Section 3.5
# These are overridden by config.json and then by cloud-provided config
NODE_DEFAULTS: dict[str, dict[str, Any]] = {
    "pool_node": {
        "sleep_duration": 120,  # seconds between readings
        "float_switch_reads": 30,  # number of reads for debouncing
        "watchdog_timeout": 60,  # seconds
    },
    "valve_node": {
        "valve_start_time": "09:00",  # HH:MM format
        "max_fill_minutes": 9,  # maximum fill duration
        "fill_window_hours": 2,  # hours after start time for fill window
        "fill_check_interval": 10,  # minutes between eligibility checks
        "status_update_interval": 60,  # seconds between status updates
        "staleness_multiplier": 2,  # pool_interval * this = freshness threshold
        "watchdog_timeout": 30,  # seconds
    },
    "display_node": {
        "chart_history_hours": 24,  # hours of history to display
        "chart_refresh_interval": 300,  # seconds between chart refreshes
        "stale_data_threshold": 1800,  # seconds before data is stale
        "watchdog_timeout": 120,  # seconds
    },
}

# Document which config items are hot-reloadable vs restart-required
# per architecture.md Section 3.5
HOT_RELOADABLE = [
    "reportInterval",
    "staleDataThreshold",
    "chartRefreshInterval",
    "screensaverTimeout",
    "valveStartTime",
    "fillWindowHours",
    "maxFillDuration",
    "logLevel",
    "debugLogging",
]

RESTART_REQUIRED = [
    "deviceId",
    "environment",
    "hardwareEnabled",
    # GPIO pins
    # I2C/SPI addresses
    # API keys
    # WiFi credentials
    # Supported message versions
]
