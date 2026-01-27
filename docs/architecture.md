# Architecture: Poolio Pool Automation System

> Generated from: docs/requirements.md
> Synthesized from: docs/architecture1.md, docs/architecture2.md
> Date: 2026-01-21

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Principles](#architecture-principles)
3. [Architecture Decisions](#architecture-decisions)
4. [Components](#components)
5. [Directory Structure](#directory-structure)
6. [Data Flow](#data-flow)
7. [Tech Stack](#tech-stack)
8. [CircuitPython Compatibility](#circuitpython-compatibility)
9. [Message Protocol](#message-protocol)
10. [Reliability Patterns](#reliability-patterns)
11. [Environment Configuration](#environment-configuration)
12. [Credential Provisioning](#credential-provisioning)
13. [Deployment](#deployment)
14. [Testing & CI/CD](#testing--cicd)
15. [Build Sequence](#build-sequence)
16. [Critical Details](#critical-details)
17. [Resolved Questions](#resolved-questions)

---

## System Overview

Poolio is a distributed IoT pool automation and monitoring platform consisting of multiple microcontroller-based nodes that communicate via a cloud message broker (Adafruit IO). The system automates pool water management by:

- Monitoring pool temperature and water level
- Automatically filling the pool on schedule when water is low
- Displaying status on a touchscreen dashboard
- Supporting manual control via touch interface
- Integrating with Apple HomeKit (Phase 4)

### System Architecture Diagram

```text
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Pool Node     │     │   Valve Node     │     │  Display Node   │
│  (Sensor Unit)  │     │ (Fill Controller)│     │   (Dashboard)   │
│    [C++]        │     │  [CircuitPython] │     │  [CircuitPython]│
└────────┬────────┘     └────────┬─────────┘     └────────┬────────┘
         │                       │                        │
         │ HTTPS POST            │ MQTT PUB/SUB           │ MQTT SUB
         │                       │                        │
         └───────────────────────┴────────────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │      Adafruit IO        │
                    │   (Cloud Message Broker)│
                    └────────────┬────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │   Homebridge Plugin     │
                    │      (Phase 4)          │
                    └────────────┬────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │     Apple HomeKit       │
                    └─────────────────────────┘
```

### Node Summary

| Node | Purpose | Power | Communication | Language |
|------|---------|-------|---------------|----------|
| Pool Node | Monitor temp, water level, battery | Battery (deep sleep) | HTTPS REST | C++ |
| Valve Node | Control fill valve with scheduling | AC/DC powered | MQTT bidirectional | CircuitPython |
| Display Node | Status dashboard with touch control | AC/DC powered | MQTT + HTTP REST | CircuitPython |

---

## Architecture Principles

### Core Principle: Message Protocol as Integration Contract

Rather than traditional plugin inheritance, this architecture uses the **JSON message protocol** as the integration boundary. Each node is an independent implementation that speaks a common message language.

**Why not a traditional Device base class?**

The requirements mention a "device plugin architecture" (FR-EXT-001), but the Pool Node's deep sleep lifecycle fundamentally doesn't fit this pattern:

- Pool Node has no `process_command()` - it's asleep 99% of the time
- Pool Node lifecycle: Wake → Measure → Transmit → Sleep
- Valve/Display lifecycle: Initialize → Run Forever (with events)

**The solution:** The "plugin" value comes from the message protocol, not code inheritance. New device types just need to speak the protocol. This enables:

1. **Mixed-language implementations** - C++ and CircuitPython nodes communicate seamlessly
2. **Independent lifecycles** - Each node manages its own lifecycle appropriately
3. **Loose coupling** - Nodes only depend on message schemas, not shared code
4. **Future extensibility** - New device types register message schemas, not code plugins

### Design Rationale Evolution

This architecture evolved through several iterations:

1. **Initial hypothesis**: The system needs a sophisticated device plugin architecture with a common base class and runtime device discovery.

2. **First revision**: Recognized that Pool Node's deep sleep lifecycle doesn't fit a standard device interface (no `process_command()` when sleeping).

3. **Second revision**: The "plugin" value is really about configuration-driven hardware mapping and message routing, not code extensibility.

4. **Final rationale**: Language choice is node-specific based on reliability requirements. The JSON message protocol serves as the integration contract. Shared libraries provide common functionality with functional parity between Python and C++.

---

## Architecture Decisions

| Decision | Rationale | Alternatives Rejected |
|----------|-----------|----------------------|
| **C++ for Pool Node** | Battery-powered node requires hard timeouts on WiFi, proper bus recovery, and FreeRTOS for reliability | CircuitPython - no timeout control on blocking operations |
| **CircuitPython for Display Node** | UI-focused development benefits from rapid iteration; watchdog recovery acceptable | C++ - slower development cycle for UI changes |
| **CircuitPython for Valve Node** | AC-powered, can recover from hangs via watchdog; simpler development | May migrate to C++ if reliability issues arise |
| **JSON message protocol** | Human-readable for debugging, extensible for new message types, standard tooling | Pipe-delimited legacy - harder to extend |
| **Adafruit IO as cloud backend** | Simple setup, combined MQTT + REST, adequate rate limits | AWS IoT - overkill for this scale |
| **Thin cloud abstraction** | Enables mocking for tests, clean separation | No abstraction - harder to test |
| **Homebridge for HomeKit** | Mature ecosystem, well-documented, runs on separate device | Direct HAP - too resource-intensive for ESP32 |
| **Environment prefixes for feeds** | Simple isolation of prod/nonprod without separate accounts | Separate accounts - complex credential management |
| **Composition over inheritance** | Nodes have very different lifecycles; forced hierarchy adds complexity | Device base class - awkward fit for deep sleep |

---

## Components

### Shared Libraries (Python)

**Location:** `src/shared/`

**Purpose:** Provide reusable modules for CircuitPython nodes and simulators.

#### Module Overview

| Module | Responsibility |
|--------|----------------|
| `messages` | JSON message encoding, decoding, envelope handling, and schema validation |
| `cloud` | Adafruit IO client abstraction (MQTT + HTTP REST) |
| `config` | Configuration loading, validation, defaults, and environment handling |
| `logging` | Structured logging with levels and device context |
| `sensors` | Common sensor patterns: retry logic, bus recovery, timeout handling |

#### Messages Module

**JSON Schema Version:** Draft 2020-12 (as specified in Requirements Appendix A)

*Note: Full jsonschema validation is **DEFERRED** to Phase 4+ per Kent Beck's "fewest elements" principle. Start with simplified required-field validation on-device. JSON Schema files and strict mode (`validate_message(json_str, strict=True)`) will be added only if simple validation proves insufficient for debugging message format issues.*

```text
src/shared/messages/
├── __init__.py          # Public API exports
├── types.py             # Message type classes (plain classes, not dataclasses)
├── envelope.py          # Envelope creation/parsing
├── encoder.py           # Message → JSON
├── decoder.py           # JSON → Message
└── validator.py         # Schema validation (simplified on-device, full jsonschema in tests)
```

**Field Naming Convention:**

Python classes use `snake_case` for attributes (Pythonic convention). JSON messages use `camelCase` for keys (web API convention). The encoder and decoder handle conversion automatically:

| Direction | Conversion | Example |
|-----------|------------|---------|
| Python → JSON | `snake_case` → `camelCase` | `is_filling` → `isFilling` |
| JSON → Python | `camelCase` → `snake_case` | `currentFillDuration` → `current_fill_duration` |

**Key Interfaces:**

```python
# types.py - Message type classes (CircuitPython compatible, no dataclasses)
class PoolStatus:
    def __init__(self, water_level, temperature, battery, reporting_interval):
        self.water_level = water_level
        self.temperature = temperature
        self.battery = battery
        self.reporting_interval = reporting_interval

class WaterLevel:
    def __init__(self, float_switch, confidence):
        self.float_switch = float_switch  # bool
        self.confidence = confidence      # float

class Temperature:
    def __init__(self, value, unit="fahrenheit"):
        self.value = value  # float
        self.unit = unit    # str

# envelope.py - Envelope handling
def create_envelope(msg_type, device_id, payload):
    """Returns dict with envelope structure."""
    ...

def parse_envelope(json_str):
    """Returns (envelope_dict, payload_dict) tuple."""
    ...

# encoder.py - Encoding
def encode_message(message):
    """Returns JSON string."""
    ...

# decoder.py - Decoding
def decode_message(json_str):
    """Returns Message object."""
    ...

# validator.py - Validation (simplified for CircuitPython)
def validate_message(json_str, strict=False):
    """Returns bool. Full schema validation only in strict mode (tests)."""
    ...

def validate_envelope(envelope):
    """Returns (valid, errors) tuple where errors is a list of strings."""
    ...
```

#### Cloud Module

```text
src/shared/cloud/
├── __init__.py
├── base.py              # CloudBackend base class (duck typing, no abc module)
├── adafruit_io_http.py  # HTTP-only client (Pool Node)
├── adafruit_io_mqtt.py  # MQTT client (Valve/Display)
└── mock.py              # Mock backend for testing
```

**Key Interfaces:**

```python
# base.py - Base class using duck typing (CircuitPython has no abc module)
class CloudBackend:
    """
    Base class for cloud backends.
    Subclasses must implement all methods.
    Uses duck typing - no abstract enforcement in CircuitPython.
    """

    def connect(self):
        """Connect to the cloud backend."""
        raise NotImplementedError("Subclasses must implement connect()")

    def disconnect(self):
        """Disconnect from the cloud backend."""
        raise NotImplementedError("Subclasses must implement disconnect()")

    def publish(self, feed, value):
        """Publish value to feed."""
        raise NotImplementedError("Subclasses must implement publish()")

    def subscribe(self, feed, callback):
        """Subscribe to feed with callback function."""
        raise NotImplementedError("Subclasses must implement subscribe()")

    def fetch_latest(self, feed):
        """Fetch latest value from feed. Returns the value."""
        raise NotImplementedError("Subclasses must implement fetch_latest()")

    def fetch_history(self, feed, hours):
        """Fetch historical values from feed. Returns list."""
        raise NotImplementedError("Subclasses must implement fetch_history()")

    def sync_time(self):
        """Sync time from cloud. Returns adafruit_datetime.datetime object."""
        raise NotImplementedError("Subclasses must implement sync_time()")

# adafruit_io_http.py - HTTP-only client for Pool Node
class AdafruitIOHTTP(CloudBackend):
    def __init__(self, username, api_key, environment):
        ...

    # Implements publish, fetch_latest, fetch_history, sync_time
    # subscribe() raises NotImplementedError (HTTP doesn't support subscriptions)

# adafruit_io_mqtt.py - MQTT client for Valve/Display Nodes
class AdafruitIOMQTT(CloudBackend):
    def __init__(self, username, api_key, environment):
        ...

    # Implements all methods
    # Also: subscribe_throttle(callback) for rate limit notifications
```

**MQTT QoS Selection (FR-MSG-012):**

| Message Type | QoS Level | Rationale |
|--------------|-----------|-----------|
| Status messages (pool-status, valve-status, display-status) | QoS 0 | Fire-and-forget; next status update will arrive soon |
| Command messages (fill-start, fill-stop, manual controls) | QoS 1 | At-least-once delivery; critical for valve operations |
| Config updates | QoS 1 | Ensure configuration changes are received |

*See Requirements Section 5.1 for detailed MQTT usage specifications.*

**Time Synchronization (FR-SH-001):**

| Node Type | Sync Timing | Rationale |
|-----------|-------------|-----------|
| Pool Node | On each wake cycle | Stateless; no persistent clock during deep sleep |
| Valve Node | At startup + every 12 hours | Correct for RTC drift; ensure scheduling accuracy |
| Display Node | At startup + every 12 hours | Correct for RTC drift; ensure timestamp display accuracy |

*Note: ESP32 internal RTC can drift several seconds per day. Regular re-synchronization ensures scheduling accuracy for time-sensitive operations like fill windows.*

**Historical Data Strategy (Display Node):**

The Display Node fetches historical temperature data for sparkline and whisker chart displays. Adafruit IO's chart endpoint returns data at specified resolution intervals.

| View | Time Range | Resolution | Data Points | Memory |
|------|------------|------------|-------------|--------|
| 24h sparkline | 24 hours | 5 min | 288 | ~3 KB |
| 7d whisker | 7 days | 60 min | 168 | ~2 KB |
| 30d whisker | 30 days | 60 min | 720 | ~8 KB |

**Endpoint:**

```text
GET /api/v2/{username}/feeds/{feed}/data/chart?hours={hours}&resolution={minutes}
```

**Chart Endpoint Behavior:**

- Resolution parameter aggregates data using average
- Available resolutions: 1, 5, 10, 30, 60, 120, 240, 480, 960 minutes
- Does NOT provide min/max per window - only average values

**Whisker Chart Implementation:**

Since pool temperature changes slowly, 60-minute resolution captures daily trends accurately:

1. Fetch chart data at 60-minute resolution
2. Group data points by day (24 points per day)
3. Calculate min, max, avg for each day client-side
4. Render whisker chart with daily aggregates

*Note: IO+ tier (60 days retention) provides sufficient historical data for 30-day charts.*

#### Config Module

```text
src/shared/config/
├── __init__.py
├── loader.py            # Load config from sources
├── schema.py            # Validation schemas
├── defaults.py          # Default values by node type
└── environment.py       # Environment handling
```

**Key Interfaces:**

```python
# loader.py
def load_config(node_type, env_override=None):
    """Load config for node_type. Returns Config object."""
    ...

# environment.py
def get_feed_name(logical_name, environment):
    """Returns full feed name string (e.g., 'poolio-nonprod.gateway')."""
    ...

def select_api_key(environment, secrets):
    """Returns appropriate API key string for environment."""
    ...

def get_environment_config(environment):
    """Returns EnvironmentConfig object for environment."""
    ...

# defaults.py
NODE_DEFAULTS = {
    "pool_node": {
        "sleep_duration": 120,
        "float_switch_reads": 30,
        "watchdog_timeout": 60,
    },
    "valve_node": {
        "valve_start_time": "09:00",  # HH:MM format
        "max_fill_minutes": 9,
        "fill_window_hours": 2,
        "fill_check_interval": 10,  # minutes between eligibility checks
        "status_update_interval": 60,
        "staleness_multiplier": 2,  # pool_interval * this = freshness threshold
        "watchdog_timeout": 30,
    },
    "display_node": {
        "chart_history_hours": 24,
        "chart_refresh_interval": 300,
        "stale_data_threshold": 1800,
        "watchdog_timeout": 120,
    },
}
```

**Device Configuration Schema (FR-EXT-003):**

```json
{
  "devices": [
    {
      "id": "pool-node-001",
      "type": "pool_sensor",
      "enabled": true,
      "hardware": {
        "temperaturePin": "D10",
        "floatSwitchPin": "D11",
        "floatSwitchPowerPin": "D12",
        "batteryI2CAddress": "0x0B"
      },
      "settings": {
        "reportInterval": 120,
        "floatSwitchReads": 30
      }
    },
    {
      "id": "valve-node-001",
      "type": "valve_controller",
      "enabled": true,
      "hardware": {
        "valvePin": "D11",
        "temperaturePin": "D10"
      },
      "settings": {
        "maxFillMinutes": 9,
        "fillWindowHours": 2
      }
    }
  ]
}
```

**Configuration Reloadability (NFR-ARCH-003):**

| Category | Parameters | Reload Behavior |
|----------|------------|-----------------|
| **Hot-reloadable** | `reportInterval`, `staleDataThreshold`, `chartRefreshInterval`, `screensaverTimeout`, `valveStartTime`, `fillWindowHours`, `maxFillDuration`, `logLevel`, `debugLogging` | Applied immediately or on next cycle |
| **Restart-required** | `deviceId`, `environment`, `hardwareEnabled`, GPIO pins, I2C/SPI addresses, API keys, WiFi credentials, supported message versions | Require device restart |

*Note: Hot-reload is supported for Valve Node and Display Node (continuously running). Pool Node applies configuration changes on next wake cycle.*

**Configuration Distribution (Per-Device Config Feeds):**

Each device has its own configuration feed that stores the complete configuration JSON:

| Device | Config Feed |
|--------|-------------|
| Pool Node | `config-pool-node` |
| Valve Node | `config-valve-node` |
| Display Node | `config-display-node` |

*Note: Config feeds should be configured in Adafruit IO to retain only the latest value (1 data point history). This ensures devices always fetch the current configuration.*

**Boot Sequence:**

1. Load defaults from local `config.json` (includes calibration, hardware mappings)
2. Connect to WiFi
3. Fetch latest config via HTTP GET: `/api/v2/{username}/feeds/{config-feed}/data/last`
4. Merge fetched config over defaults (fetched values override local defaults)
5. Connect to MQTT and subscribe to config feed for runtime updates
6. Start normal operation

*Note: Adafruit IO does not support MQTT retained messages. Use HTTP GET to fetch initial config, then MQTT subscribe for runtime updates. Alternatively, publish to `{feed}/get` topic after subscribing to trigger immediate delivery of last value.*

**Configuration Updates:**

1. Administrator publishes complete config JSON to device's config feed
2. Device receives the message via MQTT subscription
3. Hot-reloadable changes are applied immediately
4. Restart-required changes are logged; device continues with current values until restarted

**Fallback Behavior:**

- If network is unavailable on boot, device uses local `config.json` only
- Local `config.json` contains baseline/default configuration
- For Display Node: if network unavailable, touch calibration defaults are acceptable since display has no data to show anyway

#### Logging Module

```text
src/shared/logging/
├── __init__.py
├── logger.py              # Wrapper around adafruit_logging
└── rotating_handler.py    # RotatingFileHandler (extends FileHandler)
```

**Base Library:** Uses [adafruit_logging](https://docs.circuitpython.org/projects/logging/en/latest/) which provides `Logger`, `FileHandler`, and `StreamHandler`. We extend it with rotation and graceful filesystem handling.

**Key Interfaces:**

```python
# logger.py - Thin wrapper adding device context
import adafruit_logging as logging

def get_logger(device_id, debug_logging=False):
    """
    Configure and return a logger with device context.
    Console (StreamHandler) is always added.

    Args:
        device_id: Device identifier for log context (str)
        debug_logging: If True, set level to DEBUG; otherwise INFO (bool)

    Returns:
        logging.Logger instance
    """
    logger = logging.getLogger(device_id)
    logger.setLevel(logging.DEBUG if debug_logging else logging.INFO)

    # Add console handler (always available)
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter(f"{{levelname}} {device_id}: {{message}}"))
    logger.addHandler(console)

    return logger

def add_file_logging(logger, log_path):
    """
    Add rotating file handler if filesystem is writable.

    Args:
        logger: logging.Logger instance
        log_path: Path to log file (str)

    Returns:
        True if file logging enabled, False if filesystem is read-only.
    """
    handler = RotatingFileHandler(log_path)
    if handler.is_writable():
        logger.addHandler(handler)
        return True
    return False


# rotating_handler.py - File rotation (adafruit_logging lacks this)
from adafruit_logging import FileHandler

class RotatingFileHandler(FileHandler):
    """
    FileHandler with size-based rotation.

    Rotation parameters (from NFR-MAINT-001):
    - Maximum file size: 125KB
    - Maximum file count: 3
    - Oldest file deleted when limit exceeded
    """
    MAX_FILE_SIZE = 125 * 1024  # 125KB
    MAX_FILE_COUNT = 3

    def __init__(self, filename):
        ...

    def is_writable(self):
        """Check if filesystem allows writing. Returns False for read-only."""
        try:
            with open(self.filename, "a") as f:
                pass
            return True
        except OSError:
            return False

    def emit(self, record):
        """Write log record, rotating if file exceeds MAX_FILE_SIZE."""
        self._rotate_if_needed()
        super().emit(record)

    def _rotate_if_needed(self):
        """Rotate log files if current file exceeds MAX_FILE_SIZE."""
        ...

    def _cleanup_old_files(self):
        """Delete oldest files if count exceeds MAX_FILE_COUNT."""
        ...
```

**Filesystem Graceful Degradation:**

CircuitPython devices typically cannot write to local storage while running (the CIRCUITPY drive is mounted as USB mass storage). The logger handles this gracefully by checking `is_writable()` before adding the file handler.

**Cloud Event Publishing:** Significant errors should be published to the cloud `events` feed using `cloud.publish()` at the application layer. This keeps the logger simple and gives application code control over what gets sent to the cloud.

Sources: [Adafruit Logger Library Documentation](https://docs.circuitpython.org/projects/logging/en/latest/), [Log to File Guide](https://learn.adafruit.com/a-logger-for-circuitpython/file-handler)

#### Sensors Module

```text
src/shared/sensors/
├── __init__.py
├── retry.py             # Retry with exponential backoff
└── bus_recovery.py      # I2C/OneWire recovery
```

**Key Interfaces:**

```python
# retry.py
def retry_with_backoff(func, max_retries=3, base_delay=0.1, max_delay=2.0, exceptions=(Exception,)):
    """
    Retry function with exponential backoff.

    Args:
        func: Callable to retry
        max_retries: Maximum number of retry attempts (int)
        base_delay: Initial delay in seconds (float)
        max_delay: Maximum delay cap in seconds (float)
        exceptions: Tuple of exception types to catch

    Returns:
        Result of func() on success

    Raises:
        Last exception if all retries fail
    """
    ...

# bus_recovery.py
def recover_i2c_bus(scl_pin, sda_pin):
    """Attempt I2C bus recovery. Returns True if successful."""
    ...

def recover_onewire_bus(data_pin):
    """Attempt OneWire bus recovery. Returns True if successful."""
    ...
```

---

### Pool Node (C++)

**Location:** `pool_node_cpp/`

**Purpose:** Battery-powered sensor node with deep sleep. C++ required for reliability (timeouts, bus recovery).

**Hardware:**

- MCU: Adafruit Feather ESP32 V2
- Temperature: DS18X20 (OneWire, GPIO D10)
- Water Level: Float switch (GPIO D11 input, D12 power)
- Battery: LC709203F fuel gauge (I2C)

**Interfaces:**

- Publishes: `pool_status` messages to gateway feed (HTTPS POST)
- Publishes: Individual feeds (pooltemp, poolnodebattery)
- No subscriptions (deep sleep prevents MQTT)

**Lifecycle:**

```text
Wake → Init Watchdog → WiFi Connect → Sync Time → Read Sensors → Transmit → Cleanup → Sleep
              ↓              ↓            ↓            ↓           ↓
         [feed watchdog at each stage, max 15s intervals]
```

**Structure:**

```text
pool_node_cpp/
├── platformio.ini
├── src/
│   ├── main.cpp               # Entry point
│   ├── pool_node.cpp/h        # Main controller
│   ├── sensors/
│   │   ├── temperature.cpp/h  # DS18X20 with retry
│   │   ├── water_level.cpp/h  # Float switch consensus
│   │   └── battery.cpp/h      # LC709203F with I2C recovery
│   ├── network/
│   │   ├── wifi_manager.cpp/h # WiFi with 15s timeout
│   │   ├── time_sync.cpp/h    # Time synchronization
│   │   └── http_client.cpp/h  # HTTPS POST with 10s timeout
│   ├── power/
│   │   └── sleep_manager.cpp/h # Deep sleep with cleanup
│   └── watchdog/
│       └── watchdog.cpp/h     # Hardware watchdog (60s)
├── lib/                       # C++ shared libraries
│   ├── messages/
│   ├── config/
│   └── logging/
├── include/
│   └── secrets.h.example
└── test/
```

---

### Valve Node (CircuitPython)

**Location:** `src/valve_node/`

**Purpose:** AC-powered fill controller with scheduling and safety interlocks.

**Hardware:**

- MCU: Adafruit Feather ESP32-S3
- Temperature: DS18X20 (OneWire, GPIO D10)
- Valve: Solenoid relay (GPIO D11)

**Interfaces:**

- Subscribes: `gateway` (for pool_status, commands), `valvestarttime`, `config` feeds
- Publishes: `valve_status`, `fill_start`, `fill_stop`, `error` messages
- Publishes: `outsidetemp`, `poolvalveruntime` feeds

**Safety Interlocks:**
1. Pool data freshness check (pool_status within staleness threshold)
2. Maximum fill duration (default: 9 minutes)
3. Float switch full detection (stop immediately when pool full)
4. Fill window time constraints
5. Continue active fill to max duration if data becomes stale mid-fill

**Structure:**

```text
src/valve_node/
├── code.py                    # Entry point
├── config.json                # Node configuration
├── valve_controller.py        # Main controller
├── scheduler.py               # Fill window scheduling
├── safety.py                  # Safety interlock checks
└── lib/                       # Symlink to ../shared
```

**Key Classes:**

```python
# valve_controller.py
class ValveController:
    def __init__(self, config, cloud, logger):
        """
        Args:
            config: Config object
            cloud: CloudBackend instance
            logger: Logger instance
        """
        ...

    def start(self):
        """Start the valve controller main loop."""
        ...

    def handle_pool_status(self, message):
        """Handle incoming PoolStatus message."""
        ...

    def handle_command(self, message):
        """Handle incoming Command message."""
        ...

    def check_fill_eligibility(self):
        """Check if fill is allowed. Returns (eligible, reason) tuple."""
        ...

    def start_fill(self, trigger):
        """Start fill operation. trigger is reason string."""
        ...

    def stop_fill(self, reason):
        """Stop fill operation with reason string."""
        ...

# scheduler.py
class FillScheduler:
    def __init__(self, start_time, window_hours, check_interval):
        """
        Args:
            start_time: Fill window start time as "HH:MM" string
            window_hours: Duration of fill window in hours (int)
            check_interval: Minutes between eligibility checks (int)
        """
        ...

    def is_within_window(self, current_time):
        """Check if current_time (adafruit_datetime) is within fill window. Returns bool."""
        ...

    def next_check_time(self):
        """Returns next check time as adafruit_datetime.datetime."""
        ...

    def next_fill_time(self):
        """Returns next fill window start as adafruit_datetime.datetime."""
        ...

# safety.py
class SafetyInterlocks:
    def __init__(self, config):
        """Args: config is Config object."""
        ...

    def check_data_freshness(self, pool_msg, now):
        """Check if pool data is fresh. Returns (ok, reason) tuple."""
        ...

    def check_water_level(self, pool_msg):
        """Check water level status. Returns (ok, reason) tuple."""
        ...

    def check_fill_window(self, scheduler, now):
        """Check if within fill window. Returns (ok, reason) tuple."""
        ...

    def check_all(self, pool_msg, scheduler):
        """Run all safety checks. Returns (ok, reason) tuple."""
        ...
```

**Command Rate Limiting (DEFERRED to Phase 4+):**

*Implementation Note: Rate limiting is deferred per Kent Beck's "no just-in-case code" principle. The system uses authenticated MQTT (Adafruit IO API key required). Implement only if abuse is detected in production.*

| Command | Minimum Interval |
|---------|------------------|
| `valve_start` | 60 seconds |
| `valve_stop` | 10 seconds |
| `set_config` | 30 seconds |
| `device_reset` | 300 seconds |

**Legacy Message Support (FR-VN-006) (DEFERRED to Phase 4+):**

*Implementation Note: Legacy support is deferred per Kent Beck's "no just-in-case code" principle. The rearchitecture is a clean break - legacy nodes can continue using the existing system until migrated. Implement only if parallel operation with legacy nodes proves necessary.*

During migration (if needed), the Valve Node accepts both JSON and legacy pipe-delimited commands:

| Legacy Type | JSON Equivalent | Description |
|-------------|-----------------|-------------|
| `6` | `{"command": "valve_start"}` | Manual fill start |
| `99` | `{"command": "device_reset"}` | Device reset |

**Detection:** First character determines format:
- `{` → JSON message
- Digit → Legacy pipe-delimited

**Sunset Timeline:**
- Phase 1-2: Full legacy support
- Phase 3: Deprecation warning logged for legacy messages
- Phase 4+: Legacy support may be removed

---

### Display Node (CircuitPython)

**Location:** `src/display_node/`

**Purpose:** Touchscreen dashboard with real-time status and command controls.

**Hardware:**

- MCU: Adafruit Feather ESP32-S2
- Display: ILI9341 2.4" TFT (320x240, SPI)
- Touchscreen: STMPE610 (SPI)
- Temp/Humidity: AHTx0 (I2C)

**Interfaces:**

- Subscribes: `gateway` feed (for all status messages)
- HTTP GET: Gateway feed latest on startup, historical data for charts
- Publishes: `display_status`, `command` messages
- Publishes: `insidetemp` feed

**Features:**

- Real-time status display (temperatures, fill state, battery, date/time)
- Data freshness indicators (alert on stale data)
- Touch buttons for manual control
- Burn-in prevention cycle
- Multiple screens/views (main dashboard, device details, settings)

**Burn-In Prevention (FR-DN-007):**

| Parameter | Default | Configurable |
|-----------|---------|--------------|
| Idle trigger time | 5 minutes | Yes |
| Rotation duration | 7 seconds | Yes |
| Background colors | 4 (black, white, red, blue) | Yes |
| Skip on touch | Yes | No |

**Fonts:**

| Attribute | Value |
|-----------|-------|
| Source | [adafruit/circuitpython-fonts](https://github.com/adafruit/circuitpython-fonts) |
| Format | PCF (Portable Compiled Format) |
| License | GNU FreeFont - GPL with Font Exception (allows embedding) |
| Font family | FreeSans (Regular, Bold, Oblique, BoldOblique) |
| Sizes | 8, 10, 12, 14, 18, 24 point (as needed) |
| Dependency | `adafruit_bitmap_font` library |

**Installation:**

```bash
# Via circup (recommended)
circup bundle-add adafruit/circuitpython-fonts
circup install font_free_sans_18 font_free_sans_bold_24

# Manual: Download from releases, copy PCF files to fonts/ directory
```

*UI Design: See [display-node-ui-design.md](display-node-ui-design.md) for screen layouts, navigation, and control specifications.*

**Structure:**

```text
src/display_node/
├── code.py                    # Entry point
├── config.json                # Node configuration
├── dashboard.py               # Main controller
├── ui/
│   ├── __init__.py
│   ├── screens.py             # Screen definitions
│   ├── widgets.py             # UI components
│   ├── touch.py               # Touch input handling
│   └── theme.py               # Colors, fonts, layouts
└── lib/                       # Symlink to ../shared
```

**Key Classes:**

```python
# dashboard.py
class Dashboard:
    def __init__(self, config, cloud, display, touch):
        """
        Args:
            config: Config object
            cloud: CloudBackend instance
            display: Display driver instance
            touch: Touch controller instance
        """
        ...

    def start(self):
        """Start the dashboard main loop."""
        ...

    def handle_message(self, message):
        """Handle incoming Message object."""
        ...

    def send_command(self, command, params=None):
        """Send command. params is optional dict."""
        ...

    def refresh_display(self):
        """Redraw the display."""
        ...

# ui/touch.py
class TouchHandler:
    DEBOUNCE_MS = 250  # Minimum interval between touch events

    def __init__(self, touch_controller, screen_width, screen_height):
        """
        Args:
            touch_controller: Hardware touch controller instance
            screen_width: Screen width in pixels (int)
            screen_height: Screen height in pixels (int)
        """
        ...

    def get_touch(self):
        """Get current touch position. Returns (x, y) tuple or None."""
        ...

    def register_button(self, name, bounds):
        """Register touchable button. bounds is (x, y, width, height) tuple."""
        ...

    def check_buttons(self):
        """Check if any registered button is touched. Returns button name or None."""
        ...

# ui/theme.py
COLORS = {
    "background": 0x000000,
    "text": 0xFFFFFF,
    "accent": 0x00AAFF,
    "alert": 0xFF0000,
    "success": 0x00FF00,
    "stale": 0xFFAA00,
}

FONTS = {
    "small": terminalio.FONT,
    "large": None,  # Load from file if available
}
```

---

### Node Simulators

**Location:** `src/simulators/`

**Purpose:** Enable development and testing without physical hardware.

**Simulators:**

- Pool Node Simulator - generates pool_status at configurable intervals
- Valve Node Simulator - responds to commands, generates status/events
- Display Node Simulator - subscribes to all messages, logs for debugging

**Usage:**

```bash
python -m poolio.simulators.pool_node --interval 120 --environment nonprod
python -m poolio.simulators.valve_node --environment nonprod
python -m poolio.simulators.display_node --environment nonprod
```

**Structure:**

```text
src/simulators/
├── __init__.py
├── pool_node.py               # Pool node simulator
├── valve_node.py              # Valve node simulator
├── display_node.py            # Display node simulator
└── common.py                  # Shared utilities
```

**Simulator Device IDs:**

- Simulators use `-sim` suffix: `pool-node-001-sim`, `valve-node-001-sim`
- This clearly identifies simulated messages in logs and cloud data

---

### Homebridge Plugin (Phase 4)

**Location:** `homebridge/`

**Purpose:** Expose Poolio devices to Apple HomeKit.

**Accessory Mapping:**

| Poolio Component | HomeKit Service | Characteristics |
|------------------|-----------------|-----------------|
| Pool Temperature | Temperature Sensor | CurrentTemperature |
| Outside Temperature | Temperature Sensor | CurrentTemperature |
| Inside Temp/Humidity | Temperature + Humidity Sensor | CurrentTemperature, CurrentRelativeHumidity |
| Water Level | Contact Sensor | ContactSensorState (DETECTED=full) |
| Fill Valve | Valve | Active, InUse, ValveType=IRRIGATION |
| Pool Node Battery | Battery Service | BatteryLevel, StatusLowBattery |
| Pump (future) | Fan | Active, RotationSpeed |

**Structure:**

```text
homebridge/
├── src/
│   ├── platform.ts            # Homebridge platform plugin
│   ├── accessories/
│   │   ├── temperature.ts     # Temperature sensor
│   │   ├── water-level.ts     # Contact sensor
│   │   ├── valve.ts           # Valve accessory
│   │   └── battery.ts         # Battery service
│   ├── cloud-client.ts        # Adafruit IO MQTT client
│   └── config-schema.ts       # Config type definitions
├── config.schema.json         # Homebridge Config UI schema
├── package.json
└── tsconfig.json
```

### Alternative: Home Assistant Integration (FR-HK-007)

As an alternative to Homebridge, Poolio can integrate with [Home Assistant](https://www.home-assistant.io/) using its native MQTT integration.

**Approach:**
- Home Assistant subscribes directly to Adafruit IO MQTT feeds
- MQTT sensor entities created for each Poolio data point
- Home Assistant's HomeKit Bridge exposes entities to Apple Home

**Configuration Example (Home Assistant YAML):**

```yaml
mqtt:
  sensor:
    - name: "Pool Temperature"
      state_topic: "chrishenry/feeds/poolio.pooltemp"
      unit_of_measurement: "°F"
      device_class: temperature

    - name: "Outside Temperature"
      state_topic: "chrishenry/feeds/poolio.outsidetemp"
      unit_of_measurement: "°F"
      device_class: temperature

  binary_sensor:
    - name: "Pool Water Level"
      state_topic: "chrishenry/feeds/poolio.gateway"
      value_template: "{{ value_json.payload.waterLevel.floatSwitch }}"
      payload_on: true
      payload_off: false
```

**Trade-offs vs Homebridge:**

| Aspect | Homebridge | Home Assistant |
|--------|------------|----------------|
| Complexity | Plugin development required | Configuration only |
| Hosting | Dedicated server/Pi | Requires HA installation |
| Customization | Limited to HAP | Full HA automation |
| Maintenance | npm package updates | HA core updates |

*Note: Home Assistant integration is documented as an alternative but not the primary implementation path. Homebridge is the recommended approach for dedicated HomeKit integration.*

---

## Directory Structure

```text
poolio_rearchitect/
├── src/
│   ├── shared/                    # Shared libraries (Python)
│   │   ├── __init__.py
│   │   ├── messages/              # JSON message protocol
│   │   │   ├── __init__.py
│   │   │   ├── types.py           # Message type definitions
│   │   │   ├── envelope.py        # Envelope handling
│   │   │   ├── encoder.py         # Message encoding
│   │   │   ├── decoder.py         # Message decoding
│   │   │   └── validator.py       # Schema validation
│   │   ├── cloud/                 # Cloud backend abstraction
│   │   │   ├── __init__.py
│   │   │   ├── base.py            # Abstract interface
│   │   │   ├── adafruit_io_http.py
│   │   │   ├── adafruit_io_mqtt.py
│   │   │   └── mock.py
│   │   ├── config/                # Configuration management
│   │   │   ├── __init__.py
│   │   │   ├── loader.py
│   │   │   ├── schema.py
│   │   │   ├── defaults.py
│   │   │   └── environment.py
│   │   ├── logging/               # Structured logging
│   │   │   ├── __init__.py
│   │   │   └── logger.py
│   │   └── sensors/               # Common sensor patterns
│   │       ├── __init__.py
│   │       ├── retry.py
│   │       └── bus_recovery.py
│   │
│   ├── valve_node/                # Valve controller (CircuitPython)
│   │   ├── code.py
│   │   ├── config.json
│   │   ├── valve_controller.py
│   │   ├── scheduler.py
│   │   ├── safety.py
│   │   └── lib/                   # Symlink to ../shared
│   │
│   ├── display_node/              # Dashboard (CircuitPython)
│   │   ├── code.py
│   │   ├── config.json
│   │   ├── dashboard.py
│   │   ├── ui/
│   │   │   ├── __init__.py
│   │   │   ├── screens.py
│   │   │   ├── widgets.py
│   │   │   ├── touch.py
│   │   │   └── theme.py
│   │   └── lib/                   # Symlink to ../shared
│   │
│   └── simulators/                # Development simulators
│       ├── __init__.py
│       ├── pool_node.py
│       ├── valve_node.py
│       ├── display_node.py
│       └── common.py
│
├── pool_node_cpp/                 # Pool Node C++ implementation
│   ├── platformio.ini
│   ├── src/
│   │   ├── main.cpp
│   │   ├── pool_node.cpp/h
│   │   ├── sensors/
│   │   ├── network/
│   │   ├── power/
│   │   └── watchdog/
│   ├── lib/                       # C++ shared libraries
│   │   ├── messages/
│   │   ├── config/
│   │   └── logging/
│   ├── include/
│   │   └── secrets.h.example
│   └── test/
│
├── homebridge/                    # HomeKit integration (Phase 4)
│   ├── src/
│   │   ├── platform.ts
│   │   ├── accessories/
│   │   └── cloud-client.ts
│   ├── config.schema.json
│   ├── package.json
│   └── tsconfig.json
│
├── schemas/                       # JSON schemas for validation
│   ├── message-envelope.json
│   ├── pool-status.json
│   ├── valve-status.json
│   ├── command.json
│   └── ...
│
├── tests/
│   ├── unit/
│   │   ├── test_messages.py
│   │   ├── test_config.py
│   │   └── ...
│   └── integration/
│       └── test_message_flow.py
│
├── docs/
│   ├── requirements.md
│   └── architecture.md            # This document
│
├── .claude/
├── CLAUDE.md
└── README.md
```

---

## Data Flow

### Sensor Data Collection Flow

```text
Pool Node                    Cloud (Adafruit IO)              Valve Node / Display Node
    │                              │                                    │
    │── pool_status (HTTPS) ──────>│                                    │
    │                              │── gateway (MQTT) ─────────────────>│
    │                              │                                    │
    │── pooltemp (HTTPS) ─────────>│                                    │
    │── poolnodebattery (HTTPS) ──>│                                    │
```

### Fill Operation Flow

```text
Valve Node                   Cloud (Adafruit IO)              Display Node
    │                              │                                    │
    │<── pool_status (MQTT) ───────│<── pool_status (HTTPS) ── Pool Node
    │                              │                                    │
    │ [Check interlocks]           │                                    │
    │ [Start fill if eligible]     │                                    │
    │                              │                                    │
    │── fill_start (MQTT) ────────>│── gateway (MQTT) ─────────────────>│
    │                              │                                    │
    │── valve_status (MQTT) ──────>│── gateway (MQTT) ─────────────────>│
    │                              │                                    │
    ├─────────────────────────────────────────────────────────────────────
    │ [ALT A: Float switch detects full]                                │
    │                              │                                    │
    │── fill_stop (MQTT) ─────────>│── gateway (MQTT) ─────────────────>│
    │   reason: "full"             │                                    │
    │                              │                                    │
    ├─────────────────────────────────────────────────────────────────────
    │ [ALT B: Max fill duration reached]                                │
    │                              │                                    │
    │── fill_stop (MQTT) ─────────>│── gateway (MQTT) ─────────────────>│
    │   reason: "timeout"          │                                    │
    └─────────────────────────────────────────────────────────────────────
```

### Command Flow

```text
Display Node                 Cloud (Adafruit IO)              Valve Node
    │                              │                                    │
    │── command (MQTT) ───────────>│── gateway (MQTT) ─────────────────>│
    │   {valve_start}              │                                    │
    │                              │                                    │
    │                              │<── command_response (MQTT) ────────│
    │<── command_response (MQTT) ──│                                    │
```

### HomeKit Integration Flow

```text
Poolio Nodes                 Cloud (Adafruit IO)              Homebridge              Apple Home
    │                              │                              │                        │
    │── status messages ──────────>│── MQTT ─────────────────────>│                        │
    │                              │                              │── HAP ────────────────>│
    │                              │                              │                        │
    │                              │                              │<── HAP command ────────│
    │                              │<── command (MQTT) ───────────│                        │
    │<── command (MQTT) ───────────│                              │                        │
```

### HTTP to MQTT Bridge

Adafruit IO automatically bridges HTTP REST API and MQTT:

- Data posted via HTTP POST appears to MQTT subscribers immediately
- Data published via MQTT is accessible via HTTP GET
- This enables Pool Node (HTTP-only due to deep sleep) to communicate with Valve/Display Nodes (MQTT)

**Example:**

```text
Pool Node posts to:       POST /api/v2/{username}/feeds/gateway/data
Valve/Display subscribe:  {username}/feeds/gateway
```

When Pool Node publishes sensor data via HTTPS, Valve Node and Display Node receive it on their MQTT subscriptions automatically. No bridging code is required.

*Reference: [Adafruit IO API Cookbook](https://io.adafruit.com/api/docs/cookbook.html)*

---

## Tech Stack

| Layer | Technology | Rationale |
|-------|------------|-----------|
| Pool Node MCU | ESP32 (Feather V2) | Deep sleep support, battery monitoring, WiFi |
| Pool Node Language | C++ (Arduino/ESP-IDF) | Timeout control, bus recovery, reliability-critical |
| Valve Node MCU | ESP32-S3 (Feather) | PSRAM for MQTT, robust WiFi |
| Valve Node Language | CircuitPython | Rapid iteration, simpler maintenance |
| Display Node MCU | ESP32-S2 (Feather) | Display support, adequate memory for UI |
| Display Node Language | CircuitPython | Complex UI easier in Python |
| Cloud Backend | Adafruit IO | MQTT + REST, simple setup, adequate for IoT |
| HomeKit Bridge | Homebridge (Node.js) | Mature ecosystem, HAP support |
| Simulators | Python 3.11+ | Cross-platform, shared library reuse |
| Message Protocol | JSON | Human-readable, extensible, debugging-friendly |
| Transport | MQTT (QoS 0/1) + HTTPS | Real-time + reliable delivery options |

---

## CircuitPython Compatibility

The shared libraries are designed to run on CircuitPython microcontrollers. This section documents key differences from standard Python (CPython) and the patterns used for compatibility.

### Module Availability

| Module | CPython | CircuitPython | Poolio Solution |
|--------|---------|---------------|-----------------|
| `dataclasses` | ✅ | ❌ | Use plain classes with `__init__` |
| `abc` (ABC, abstractmethod) | ✅ | ❌ | Use duck typing with `NotImplementedError` |
| `jsonschema` | ✅ | ❌ | Simplified validation on-device; full validation in tests |
| `typing` | ✅ | Limited | Type hints in docstrings only |
| `datetime` | ✅ | ❌ | Use `adafruit_datetime` library |
| `asyncio` | ✅ | Limited | Avoid; use polling patterns |
| `logging` | ✅ | ❌ | Use `adafruit_logging` library |
| `json` | ✅ | ✅ | Available (no custom encoders) |

### Pattern: Plain Classes Instead of Dataclasses

CircuitPython does not have the `dataclasses` module. Use plain classes with explicit `__init__` methods:

```python
# CPython (NOT CircuitPython compatible)
@dataclass
class Temperature:
    value: float
    unit: str = "fahrenheit"

# CircuitPython compatible
class Temperature:
    def __init__(self, value, unit="fahrenheit"):
        self.value = value
        self.unit = unit
```

### Pattern: Duck Typing Instead of ABC

CircuitPython does not have the `abc` module. Use `NotImplementedError` for interface enforcement:

```python
# CPython (NOT CircuitPython compatible)
from abc import ABC, abstractmethod
class CloudBackend(ABC):
    @abstractmethod
    def publish(self, feed, value): ...

# CircuitPython compatible
class CloudBackend:
    def publish(self, feed, value):
        raise NotImplementedError("Subclasses must implement publish()")
```

### Pattern: Simplified Schema Validation

The `jsonschema` library is too large for CircuitPython. Use simplified validation on-device.

*Implementation Note: Start with simplified validation only. Full jsonschema validation and JSON Schema files are DEFERRED to Phase 4+ per Kent Beck's "fewest elements" principle - implement only if simple validation proves insufficient.*

```python
# MVP: Simplified validation only (CircuitPython and initial tests)
def validate_message(json_str):
    """Check required fields only."""
    try:
        data = json.loads(json_str)
        required = ["version", "type", "deviceId", "timestamp"]
        return all(k in data for k in required)
    except (ValueError, KeyError):
        return False

# DEFERRED (Phase 4+): Full validation with JSON Schema files
# Add only if simple validation proves insufficient for debugging
# import jsonschema
# def validate_message_strict(json_str, schema):
#     jsonschema.validate(json.loads(json_str), schema)
```

### Pattern: adafruit_datetime for Time Handling

CircuitPython does not have the standard `datetime` module. Use `adafruit_datetime`:

```python
# Install: included in Adafruit CircuitPython Bundle
from adafruit_datetime import datetime, timedelta

now = datetime.now()
future = now + timedelta(hours=2)
```

### Dual Implementation Strategy

Some modules have two implementations for different environments:

| Environment | Runtime | Validation | Features |
|-------------|---------|------------|----------|
| **On-device** (CircuitPython) | Microcontroller | Simplified (required fields) | Core functionality |
| **Simulators/Tests** (CPython) | Desktop Python | Simplified initially; full jsonschema if needed (Phase 4+) | Core functionality, mocking |

This allows comprehensive testing on desktop while keeping device code lean. Full JSON Schema validation is DEFERRED to Phase 4+ - implement only if simple validation proves insufficient.

### Type Hints

Type hints are used in documentation and docstrings but NOT in actual function signatures for CircuitPython code. This ensures compatibility while maintaining documentation value:

```python
def get_feed_name(logical_name, environment):
    """Get full feed name for environment.

    Args:
        logical_name: Feed logical name (str), e.g., "gateway"
        environment: Environment name (str), e.g., "prod" or "nonprod"

    Returns:
        Full feed name (str), e.g., "poolio.gateway"
    """
    ...
```

---

## Message Protocol

### Envelope Structure

All messages use a standard envelope:

```json
{
  "version": 2,
  "type": "pool_status",
  "deviceId": "pool-node-001",
  "timestamp": "2026-01-21T10:30:00-08:00",
  "payload": { ... }
}
```

### Message Types

| Type | Direction | Purpose |
|------|-----------|---------|
| `pool_status` | Pool → Cloud | Sensor readings (temp, level, battery) |
| `valve_status` | Valve → Cloud | Controller state (valve, schedule, temp) |
| `display_status` | Display → Cloud | Inside sensor readings |
| `fill_start` | Valve → Cloud | Fill operation started |
| `fill_stop` | Valve → Cloud | Fill operation stopped |
| `command` | Cloud → Device | Remote command |
| `command_response` | Device → Cloud | Command execution result |
| `error` | Device → Cloud | Error report |
| `config_update` | Cloud → Device | Configuration change |

### Example Messages

**pool_status:**

```json
{
  "version": 2,
  "type": "pool_status",
  "deviceId": "pool-node-001",
  "timestamp": "2026-01-21T10:30:00-08:00",
  "payload": {
    "waterLevel": {
      "floatSwitch": false,
      "confidence": 0.95
    },
    "temperature": {
      "value": 78.5,
      "unit": "fahrenheit"
    },
    "battery": {
      "voltage": 3.85,
      "percentage": 72
    },
    "reportingInterval": 120
  }
}
```

**command:**

```json
{
  "version": 2,
  "type": "command",
  "deviceId": "display-node-001",
  "timestamp": "2026-01-21T10:30:00-08:00",
  "payload": {
    "command": "valve_start",
    "source": "display-node-001"
  }
}
```

### Supported Commands

*Note: Commands are published to the gateway feed. Currently, Valve Node is the only command receiver. Multi-device routing can be added later if needed.*

| Command | Parameters | Description |
|---------|------------|-------------|
| `valve_start` | (none) | Request fill operation (valve checks interlocks) |
| `valve_stop` | (none) | Stop fill operation |
| `device_reset` | (none) | Restart the device |

### Message Validation

*Addresses FR-MSG-014*

All nodes validate incoming messages before processing.

**Size Validation:**

- Maximum message size: 4KB
- Reject oversized messages and log with actual size

**Timestamp Freshness Validation:**

| Message Type | Maximum Age | Rationale |
|--------------|-------------|-----------|
| `command` | 5 minutes | Prevent replay attacks on actionable messages |
| Status messages | 15 minutes | Allow margin for network delays |

**Schema Validation:**

- Validate required envelope fields: `version`, `type`, `deviceId`, `timestamp`
- Validate payload structure per message type
- Log validation failures with full message content and specific error
- Increment error counter for observability

**Invalid Message Handling:**

- Log validation failure with context
- Increment error counter
- Do NOT crash or hang
- Publish validation errors to `events` feed for remote diagnostics
- Implement rate limiting if excessive invalid messages detected (>10/minute) - (DEFERRED to Phase 4+)

### Message Version Handling

*Addresses FR-MSG-016*

**Supported Versions:**

| Version | Status | Notes |
|---------|--------|-------|
| 2 | Current | JSON message format |

*Note: Version 1 does not exist. The predecessor is the legacy pipe-delimited format (see Legacy Feed Compatibility).*

**Version Processing Rules:**

1. Parse `version` field from message envelope
2. Check against list of supported versions
3. If version is supported: process message
4. If version is unsupported: reject and log error with:
   - Received version number
   - Sender device ID
   - List of supported versions
5. Do NOT attempt to parse payloads from unsupported versions

**Future Version Support:**

When new versions are introduced, implementations SHOULD support:
- Current version
- At least one prior version (for transition period)

---

## Reliability Patterns

### Watchdog Configuration

| Node Type | Timeout | Feed Interval | Rationale |
|-----------|---------|---------------|-----------|
| Pool Node | 60s | ≤15s | Long timeout for WiFi + HTTP operations |
| Valve Node | 30s | ≤7.5s | Moderate timeout; continuous operation |
| Display Node | 120s | ≤30s | Longest timeout; UI rendering can be slow |

### Pool Node Wake Cycle Timing Budget

The Pool Node must complete its wake cycle within the 60-second watchdog timeout. Watchdog is fed before and after each blocking operation to ensure no single stage exceeds the 15-second feed interval.

| Stage | Max Duration | Cumulative | Watchdog Feed |
|-------|--------------|------------|---------------|
| Init Watchdog | <1s | 1s | After |
| WiFi Connect | 15s | 16s | Before + After |
| Sync Time (HTTP) | 10s | 26s | Before + After |
| Read Sensors | ~5s (with retries) | 31s | Before + After |
| Transmit (HTTP) | 10s | 41s | Before + After |
| Cleanup | <1s | 42s | Before |
| **Total Maximum** | **~42s** | - | - |

**Safety Margin:** 18 seconds (60s timeout - 42s max = 30% margin)

This timing budget assumes worst-case durations for each stage. Typical cycles complete faster, providing additional margin.

### Failure Counter Pattern

```python
MAX_CONSECUTIVE_FAILURES = 5

def on_operation_failure():
    consecutive_failures += 1
    if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
        publish_error_to_cloud()
        schedule_reset(delay=90)  # Allow error to propagate

def on_operation_success():
    consecutive_failures = 0  # Reset on any success
```

### Sensor Retry Pattern

```python
def retry_with_backoff(func, max_retries=3, base_delay=0.1):
    """
    Retry with exponential backoff.
    Delays: 100ms, 200ms, 400ms, 800ms, 1600ms, 2000ms (capped)
    """
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            delay = min(base_delay * (2 ** attempt), 2.0)
            time.sleep(delay)
```

### Bus Recovery Pattern

```python
def recover_bus(bus_type):
    """
    Recover from stuck I2C or OneWire bus.
    Triggered after 3 consecutive failed operations.
    """
    deinit_bus()
    time.sleep(0.1)

    if bus_type == "i2c":
        toggle_scl_9_times()  # Release stuck device
    elif bus_type == "onewire":
        pull_data_low_500us()  # Reset bus

    reinit_bus()
    time.sleep(0.2)  # Allow devices to stabilize
```

### Network Reconnection Pattern

```python
def reconnect_with_backoff():
    """
    Reconnect with exponential backoff.
    Delays: 5s, 10s, 20s, 40s, 80s, 160s, 300s (capped)
    Reset device after 10 consecutive failures.
    """
    base_delay = 5
    max_delay = 300
    max_attempts = 10

    for attempt in range(max_attempts):
        try:
            wifi.connect()
            return True
        except Exception:
            delay = min(base_delay * (2 ** attempt), max_delay)
            time.sleep(delay)

    # All attempts failed - reset device
    publish_error_to_cloud()
    microcontroller.reset()
```

### Socket Resource Management

*Addresses NFR-REL-007*

**Pool Node (C++):**

- Maximum concurrent connections: 1 (sequential HTTP requests)
- Close HTTP response objects immediately after reading
- Reset socket pool before entering deep sleep
- Implement connection timeout: 10 seconds

**Valve Node / Display Node (CircuitPython):**

- Maximum concurrent connections: 2 (MQTT + occasional HTTP)
- Use connection pooling via `adafruit_connection_manager`
- Close unused sockets after 60 seconds idle
- Monitor socket count; reset if exceeding limit

**ConnectionManager API Reference:**

The `adafruit_connection_manager` library provides centralized socket management across libraries (requests, MiniMQTT).

| Function/Property | Description |
|-------------------|-------------|
| `get_connection_manager(socket_pool)` | Get or create singleton for socket pool |
| `connection_manager_close_all(pool, release_refs)` | Close all sockets, optionally release references |
| `manager.available_socket_count` | Count of freed sockets available for reuse |
| `manager.managed_socket_count` | Total sockets under management |
| `manager.get_socket(host, port, proto, ...)` | Acquire and connect a socket |
| `manager.free_socket(socket)` | Mark socket as available for reuse (not closed) |
| `manager.close_socket(socket)` | Close a managed socket |

*Reference: [ConnectionManager API Docs](https://docs.circuitpython.org/projects/connectionmanager/en/latest/api.html)*

```python
# Socket management pattern for CircuitPython
import adafruit_connection_manager

# Get the singleton manager
manager = adafruit_connection_manager.get_connection_manager(wifi.radio)

# Monitor socket usage
print(f"Available: {manager.available_socket_count}")
print(f"Managed: {manager.managed_socket_count}")

# Close all sockets (e.g., before deep sleep or on error recovery)
adafruit_connection_manager.connection_manager_close_all(
    socket_pool=wifi.radio,
    release_references=False
)
```

### Sensor Failure Fallback

*Addresses NFR-REL-002a*

When sensor reads fail after all retries:

1. **Send status message with null values** for failed sensors
2. **Publish error message** to `events` feed with context (sensor type, retry count, last error)
3. **Continue operation** with available sensors
4. **Do not block** transmission of valid readings due to other sensor failures

```python
# Example: Pool Node with partial sensor failure
{
  "version": 2,
  "type": "pool_status",
  "deviceId": "pool-node-001",
  "timestamp": "2026-01-21T10:30:00-08:00",
  "payload": {
    "waterLevel": {
      "floatSwitch": true,
      "confidence": 0.90
    },
    "temperature": null,  # Sensor read failed
    "battery": {
      "voltage": 3.85,
      "percentage": 72
    },
    "reportingInterval": 120
  }
}
```

### Blocking Operation Timeouts

*Addresses NFR-REL-005*

All blocking operations must have explicit timeouts. No single operation should exceed 50% of the watchdog timeout.

| Operation | Timeout | Node Types | Notes |
|-----------|---------|------------|-------|
| WiFi connection | 15s | All | C++ only; CircuitPython lacks timeout parameter |
| HTTP request | 10s | All | Includes connect + send + receive |
| MQTT connect | 10s | Valve, Display | Initial broker connection |
| I2C bus operation | 5s | All | Per-transaction timeout |
| OneWire bus operation | 5s | Pool, Valve | Per-read timeout |
| DNS resolution | 5s | All | Included in connection timeout |

**Watchdog Safety Rule:** Each timeout must be ≤50% of the node's watchdog timeout to ensure recovery from stuck operations.

| Node | Watchdog | Max Single Operation |
|------|----------|---------------------|
| Pool Node | 60s | ≤30s |
| Valve Node | 30s | ≤15s |
| Display Node | 120s | ≤60s |

---

## Environment Configuration

### Two-Environment Model

| Environment | Feed Group | API Key | Hardware | Use Case |
|-------------|------------|---------|----------|----------|
| `prod` | `poolio` | `AIO_KEY_PROD` | Enabled | Live production |
| `nonprod` | `poolio-nonprod` | `AIO_KEY_NONPROD` | Configurable | Development/testing |

### Adafruit IO Feed Organization

Feeds are organized into groups. Full feed name format: `{group}.{feed}`

**Feed Groups:**

| Group | Environment | Example |
|-------|-------------|---------|
| `poolio` | Production | `poolio.gateway` |
| `poolio-nonprod` | Development/Testing | `poolio-nonprod.gateway` |

**Feeds in Each Group:**

| Feed | Purpose | Publisher | Subscriber |
|------|---------|-----------|------------|
| `gateway` | JSON message bus (all message types) | All nodes | Valve, Display |
| `pooltemp` | Pool temperature (dashboard) | Pool Node | Dashboard |
| `outsidetemp` | Outside temperature (dashboard) | Valve Node | Dashboard |
| `insidetemp` | Inside temperature (dashboard) | Display Node | Dashboard |
| `poolnodebattery` | Battery percentage (dashboard) | Pool Node | Dashboard |
| `poolvalveruntime` | Last fill duration minutes | Valve Node | Dashboard |
| `valvestarttime` | Fill window start time (HH:MM) | Cloud/User | Valve Node |
| `config` | Configuration updates | Cloud/User | All nodes |
| `events` | Errors and significant events | All nodes | Alerting/Monitoring |

### Feed Name Resolution

```text
Logical Name    Environment    Full Feed Name
────────────    ───────────    ──────────────────────
gateway         prod           poolio.gateway
gateway         nonprod        poolio-nonprod.gateway
pooltemp        prod           poolio.pooltemp
pooltemp        nonprod        poolio-nonprod.pooltemp
```

### MQTT Topic Format

Adafruit IO MQTT topics include the username prefix. The full topic format is:

```text
{username}/feeds/{group}.{feed}
```

**Examples (username: `chrishenry`):**

| Environment | Feed | Full MQTT Topic |
|-------------|------|-----------------|
| prod | gateway | `chrishenry/feeds/poolio.gateway` |
| nonprod | gateway | `chrishenry/feeds/poolio-nonprod.gateway` |
| prod | pooltemp | `chrishenry/feeds/poolio.pooltemp` |
| nonprod | config-valve-node | `chrishenry/feeds/poolio-nonprod.config-valve-node` |

**Special Topics:**

| Topic Pattern | Purpose |
|---------------|---------|
| `{username}/feeds/{feed}/get` | Request last value (publish empty message) |
| `{username}/throttle` | Rate limit notifications |
| `{username}/errors` | API error notifications |

The username is read from `AIO_USERNAME` in settings.toml and interpolated at runtime.

### Configuration Example (settings.toml)

```toml
# CircuitPython settings.toml
CIRCUITPY_WIFI_SSID = "NetworkName"
CIRCUITPY_WIFI_PASSWORD = "password"
AIO_USERNAME = "your_username"
AIO_KEY_PROD = "aio_prod_api_key"
AIO_KEY_NONPROD = "aio_nonprod_api_key"
TIMEZONE = "America/Los_Angeles"
ENVIRONMENT = "nonprod"
```

### Environment-Specific Behavior

```json
{
  "environment": "nonprod",
  "environmentConfig": {
    "prod": {
      "feedGroup": "poolio",
      "hardwareEnabled": true,
      "debugLogging": false
    },
    "nonprod": {
      "feedGroup": "poolio-nonprod",
      "hardwareEnabled": true,
      "debugLogging": true
    }
  }
}
```

### Adafruit IO Rate Limit Handling

- Subscribe to `{username}/throttle` MQTT topic for rate limit notifications
  - This is a special Adafruit IO system topic (not a poolio feed)
  - Adafruit IO publishes here when your account is being throttled
- Implement client-side rate tracking to avoid exceeding limits
- Free tier: 30 data points/minute (system generates ~3/min)

**Throttle Response Behavior:**

When a throttle notification is received:

1. Log the throttle event with timestamp
2. Pause all publishing for 60 seconds
3. Resume normal operation after pause
4. If throttled again within 5 minutes: exponential backoff (120s, 240s, max 300s)
5. Reset backoff after 5 minutes without throttle

**Operations affected by throttle:**
- Status message publishing (pool_status, valve_status, display_status)
- Fill event publishing (fill_start, fill_stop)
- Error message publishing

**Operations NOT affected by throttle:**
- Subscribing to feeds (receiving messages)
- Local operations (valve control, sensor reading, display updates)

### Environment Switching (NFR-ENV-006)

**Rule:** Environment changes require device restart.

- Environment is read from configuration at startup only
- Runtime environment switching is NOT supported (prevents accidental production changes)
- On startup, validate environment against known list: `["prod", "nonprod"]`
- Log error and halt if unknown environment specified

**Validation on Startup:**

```python
VALID_ENVIRONMENTS = ["prod", "nonprod"]

def validate_environment(env):
    """Validate environment string. Raises ConfigurationError if invalid."""
    if env not in VALID_ENVIRONMENTS:
        logger.error(f"Invalid environment '{env}'. Valid: {VALID_ENVIRONMENTS}")
        raise ConfigurationError(f"Unknown environment: {env}")
```

### Production Safeguards (NFR-ENV-007)

**Pre-Deployment Checklist:**

1. Verify `ENVIRONMENT = "prod"` in device configuration
2. Confirm production API key (`AIO_KEY_PROD`) is configured
3. Verify device connects to production feed group (`poolio.*`)
4. Review `hardwareEnabled = true` in environment config
5. Confirm `debugLogging = false` for production

**Runtime Safeguards:**

- Log warning if production device detects non-production feed patterns in received messages
- Log warning if non-production device receives messages from production feed group
- Include environment name in all log entries and status messages

---

## Credential Provisioning

All nodes (C++ and CircuitPython) use WiFi AP captive portal for credential provisioning, with credentials stored in non-volatile memory.

### Storage by Language

| Language | Storage | Notes |
|----------|---------|-------|
| C++ | ESP-IDF NVS (Preferences) | Key-value store in flash partition |
| CircuitPython | `microcontroller.nvm` | Raw byte array, JSON serialized |

### Provisioning Flow

1. **First boot (no credentials) or BOOT button held during reset** → Device enters provisioning mode
2. **Device creates AP** → e.g., "Poolio-PoolNode-Setup"
3. **User connects** → Phone/laptop joins the AP network
4. **Captive portal** → Web page prompts for WiFi SSID/password and Adafruit IO credentials
5. **Credentials saved** → Stored in NVS (C++) or `microcontroller.nvm` (CircuitPython)
6. **Device reboots** → Connects to configured WiFi network

### Entering Provisioning Mode

| Trigger | Behavior |
|---------|----------|
| No credentials stored | Automatically enters provisioning mode on boot |
| BOOT button held during reset | Forces provisioning mode (to change credentials) |

The BOOT button (GPIO0) is present on all Adafruit Feather ESP32 boards. Hold it while pressing RESET to enter provisioning mode.

### C++ Implementation (ESP-IDF NVS)

```cpp
// lib/config/nvs_config.cpp
#include <Preferences.h>
Preferences prefs;

void save_credentials(const char* ssid, const char* password,
                      const char* aio_user, const char* aio_key) {
    prefs.begin("poolio", false);  // read-write mode
    prefs.putString("wifi_ssid", ssid);
    prefs.putString("wifi_pass", password);
    prefs.putString("aio_user", aio_user);
    prefs.putString("aio_key", aio_key);
    prefs.end();
}

String get_wifi_ssid() {
    prefs.begin("poolio", true);  // read-only mode
    String ssid = prefs.getString("wifi_ssid", "");
    prefs.end();
    return ssid;
}
```

### CircuitPython Implementation (microcontroller.nvm)

```python
# lib/config/nvm_config.py
import json
import microcontroller

def save_credentials(ssid, password, aio_user, aio_key):
    """Save credentials to NVM as JSON bytes.

    Args:
        ssid: WiFi SSID (str)
        password: WiFi password (str)
        aio_user: Adafruit IO username (str)
        aio_key: Adafruit IO API key (str)
    """
    data = {
        "wifi_ssid": ssid,
        "wifi_pass": password,
        "aio_user": aio_user,
        "aio_key": aio_key,
    }
    json_bytes = json.dumps(data).encode("utf-8")

    # Store length prefix (2 bytes) + JSON data
    length = len(json_bytes)
    microcontroller.nvm[0:2] = length.to_bytes(2, "little")
    microcontroller.nvm[2:2+length] = json_bytes

def load_credentials():
    """Load credentials from NVM. Returns empty dict if not provisioned."""
    try:
        length = int.from_bytes(microcontroller.nvm[0:2], "little")
        if length == 0 or length > len(microcontroller.nvm) - 2:
            return {}
        json_bytes = bytes(microcontroller.nvm[2:2+length])
        return json.loads(json_bytes.decode("utf-8"))
    except (ValueError, json.JSONDecodeError):
        return {}

def is_provisioned():
    """Check if device has stored credentials. Returns bool."""
    creds = load_credentials()
    return bool(creds.get("wifi_ssid"))
```

### Runtime Credential Access

```python
# CircuitPython: Check NVM first, fall back to settings.toml for development
import os
from config.nvm_config import load_credentials

creds = load_credentials()
wifi_ssid = creds.get("wifi_ssid") or os.getenv("CIRCUITPY_WIFI_SSID")
wifi_pass = creds.get("wifi_pass") or os.getenv("CIRCUITPY_WIFI_PASSWORD")
aio_key = creds.get("aio_key") or os.getenv("AIO_KEY_NONPROD")
```

### Development Shortcut

For development, credentials can be pre-configured without captive portal:

- **C++**: Use `secrets.h` (add to `.gitignore`)
- **CircuitPython**: Edit `settings.toml` directly on CIRCUITPY drive

**Note:** `settings.toml` is read-only to CircuitPython code at runtime (USB host has write access). The captive portal writes to `microcontroller.nvm` instead, which is always writable by CircuitPython.

Sources: [CircuitPython nvm module](https://docs.circuitpython.org/en/latest/shared-bindings/nvm/), [CircuitPython wifi module](https://docs.circuitpython.org/en/latest/shared-bindings/wifi/index.html)

---

## Deployment

### CircuitPython Node Deployment

CircuitPython devices mount as a USB mass storage drive named **CIRCUITPY** (can be renamed, but 11 character limit). A deploy script copies the shared libraries, node-specific files, and environment configuration to the device.

**Deploy Script Location:** `scripts/deploy_circuitpy.sh`

```bash
#!/bin/bash
# Deploy CircuitPython node to connected device
# Usage: ./scripts/deploy_circuitpy.sh <node_type> [environment]
#   node_type: valve_node | display_node
#   environment: nonprod (default) | prod

set -e

NODE_TYPE=$1
ENVIRONMENT=${2:-nonprod}
CIRCUITPY="/Volumes/CIRCUITPY"  # macOS mount point

# Linux mount point alternative: /media/$USER/CIRCUITPY

if [ -z "$NODE_TYPE" ]; then
    echo "Usage: $0 <valve_node|display_node> [nonprod|prod]"
    exit 1
fi

if [ ! -d "$CIRCUITPY" ]; then
    echo "Error: CIRCUITPY drive not found at $CIRCUITPY"
    echo "Make sure the device is connected and mounted."
    exit 1
fi

echo "Deploying $NODE_TYPE ($ENVIRONMENT) to $CIRCUITPY..."

# Copy shared libraries to lib/
echo "Copying shared libraries..."
mkdir -p "$CIRCUITPY/lib"
cp -r src/shared/messages "$CIRCUITPY/lib/"
cp -r src/shared/cloud "$CIRCUITPY/lib/"
cp -r src/shared/config "$CIRCUITPY/lib/"
cp -r src/shared/logging "$CIRCUITPY/lib/"
cp -r src/shared/sensors "$CIRCUITPY/lib/"

# Copy node-specific files
echo "Copying $NODE_TYPE files..."
cp "src/$NODE_TYPE/code.py" "$CIRCUITPY/"

# Copy additional node files (excluding lib/ symlink)
if [ "$NODE_TYPE" = "valve_node" ]; then
    cp src/valve_node/valve_controller.py "$CIRCUITPY/"
    cp src/valve_node/scheduler.py "$CIRCUITPY/"
    cp src/valve_node/safety.py "$CIRCUITPY/"
elif [ "$NODE_TYPE" = "display_node" ]; then
    cp src/display_node/dashboard.py "$CIRCUITPY/"
    cp -r src/display_node/ui "$CIRCUITPY/"
fi

# Copy environment-specific config
echo "Copying $ENVIRONMENT config..."
cp "config/$ENVIRONMENT/$NODE_TYPE.json" "$CIRCUITPY/config.json"

# Copy settings.toml template if it doesn't exist
if [ ! -f "$CIRCUITPY/settings.toml" ]; then
    echo "Creating settings.toml template..."
    cp "config/$ENVIRONMENT/settings.toml.template" "$CIRCUITPY/settings.toml"
    echo "WARNING: Edit $CIRCUITPY/settings.toml with your credentials!"
fi

echo "Deployment complete. Device will auto-reload."
```

**Environment Configuration Files:**

```text
config/
├── nonprod/
│   ├── valve_node.json         # Valve node config (nonprod feeds, debug on)
│   ├── display_node.json       # Display node config (nonprod feeds, debug on)
│   └── settings.toml.template  # Template with nonprod environment
└── prod/
    ├── valve_node.json         # Valve node config (prod feeds, debug off)
    ├── display_node.json       # Display node config (prod feeds, debug off)
    └── settings.toml.template  # Template with prod environment
```

**Example: `config/nonprod/valve_node.json`**

```json
{
  "environment": "nonprod",
  "deviceId": "valve-node-001",
  "feedGroup": "poolio-nonprod",
  "valveStartTime": "09:00",
  "maxFillMinutes": 9,
  "fillWindowHours": 2,
  "fillCheckInterval": 10,
  "statusUpdateInterval": 60,
  "stalenessMultiplier": 2,
  "debugLogging": true
}
```

**Example: `config/nonprod/settings.toml.template`**

```toml
# WiFi credentials (fill in your values)
CIRCUITPY_WIFI_SSID = "YOUR_WIFI_SSID"
CIRCUITPY_WIFI_PASSWORD = "YOUR_WIFI_PASSWORD"

# Adafruit IO credentials
AIO_USERNAME = "YOUR_AIO_USERNAME"
AIO_KEY_NONPROD = "YOUR_NONPROD_API_KEY"
AIO_KEY_PROD = "YOUR_PROD_API_KEY"

# Environment
ENVIRONMENT = "nonprod"
TIMEZONE = "America/Los_Angeles"
```

**Usage:**

```bash
# Deploy Valve Node to nonprod (default)
./scripts/deploy_circuitpy.sh valve_node

# Deploy Display Node to prod
./scripts/deploy_circuitpy.sh display_node prod
```

**File Structure on CIRCUITPY:**

```text
CIRCUITPY/
├── code.py                # Entry point (auto-runs on boot)
├── config.json            # Node configuration (environment-specific)
├── settings.toml          # Secrets (WiFi, API keys) - edit manually
├── lib/                   # Shared libraries
│   ├── messages/
│   ├── cloud/
│   ├── config/
│   ├── logging/
│   └── sensors/
├── valve_controller.py    # (Valve Node only)
├── scheduler.py           # (Valve Node only)
├── safety.py              # (Valve Node only)
├── dashboard.py           # (Display Node only)
└── ui/                    # (Display Node only)
    ├── screens.py
    ├── widgets.py
    ├── touch.py
    └── theme.py
```

**Notes:**

- The device auto-reloads `code.py` when files change
- `settings.toml` must be edited manually after first deploy (contains secrets)
- Drive name can be customized per device (e.g., "VALVE-NODE") for multi-device setups
- Config JSON is overwritten on each deploy; secrets in `settings.toml` are preserved

### C++ Pool Node Deployment

The C++ Pool Node uses PlatformIO for build and deployment:

```bash
cd pool_node_cpp

# Build for nonprod (default)
pio run -e nonprod

# Build for prod
pio run -e prod

# Upload to connected device
pio run -e nonprod --target upload

# Monitor serial output
pio device monitor
```

**PlatformIO Environment Configuration (`platformio.ini`):**

```ini
[env:nonprod]
platform = espressif32
board = adafruit_feather_esp32_v2
framework = arduino
build_flags =
    -DENVIRONMENT=\"nonprod\"
    -DFEED_PREFIX=\"nonprod-\"
    -DDEBUG_LOGGING=1

[env:prod]
platform = espressif32
board = adafruit_feather_esp32_v2
framework = arduino
build_flags =
    -DENVIRONMENT=\"prod\"
    -DFEED_PREFIX=\"\"
    -DDEBUG_LOGGING=0
```

Sources: [CircuitPython Storage](https://learn.adafruit.com/circuitpython-essentials/circuitpython-storage), [Renaming CIRCUITPY](https://learn.adafruit.com/welcome-to-circuitpython/renaming-circuitpy)

### Rollback Plan

If a deployment introduces issues, follow these steps to restore the previous version:

1. **Identify the last known good version** - Check GitHub releases/tags for previous stable version
2. **Retrieve previous version source** - Use `git checkout <tag>` to access the specific version
3. **Rebuild and redeploy** - Follow standard deployment procedure for the target node type
4. **Verify rollback** - Confirm device is operating correctly with previous version
5. **Document incident** - Create issue describing the problem for post-mortem analysis

**Version Control:**

- GitHub tags are created for each stable release (e.g., `v1.0.0`, `v1.1.0`)
- Tags preserve access to specific version source code for rollback
- Pre-release tags (e.g., `v1.1.0-rc1`) are used for nonprod testing

**Quick Rollback Commands:**

```bash
# List available tags
git tag -l

# Checkout previous version
git checkout v1.0.0

# Redeploy (CircuitPython)
./scripts/deploy_circuitpy.sh valve_node prod

# Redeploy (C++ Pool Node)
cd pool_node_cpp && pio run -e prod --target upload
```

### Data Migration

**Historical Data:**

- Adafruit IO retains historical feed data - no migration required
- New JSON messages will be stored alongside legacy data
- Display Node chart rendering works with both formats during transition

**Configuration Data:**

- Document current device configurations before migration
- Export current settings.toml / config.json from each device
- New configuration schema is backward compatible with existing values

---

## Testing & CI/CD

### Testing Strategy

CircuitPython runs on microcontrollers, not on desktop computers. To run unit tests locally or in CI, all Python tests require:

1. **Adafruit Blinka** - Provides CircuitPython API compatibility on desktop Python
2. **pytest mocks** - Mock hardware-specific modules (`board`, `digitalio`, `wifi`, etc.)

**Local test execution requires Blinka:**

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies (uses pyproject.toml)
uv sync

# Set Blinka board identifier (required even for mocked tests)
export BLINKA_MCP2221=1

# Run tests
uv run pytest tests/unit/ -v
```

**Unit Tests:**

- Test message parsing/formatting (encode, decode, validate)
- Test configuration loading and environment resolution
- Test feed name resolution and group mapping
- Use mock cloud backend for isolated testing
- Mock hardware modules (`board`, `digitalio`, `wifi`, etc.)

**Integration Tests:**

- End-to-end message flow: encode → publish → subscribe → decode
- Simulator-based multi-node communication tests
- Cloud backend connectivity tests (against nonprod feeds)

**Integration Test Scenarios:**

The following scenarios **SHALL** be tested during integration testing:

| Scenario | Description | Expected Behavior |
|----------|-------------|-------------------|
| Stale data during fill | Pool Node stops reporting while fill is in progress | Valve Node continues fill to max duration, logs warning |
| Network disconnect during command | Network drops after command sent but before acknowledgment | Display Node shows timeout, Valve Node executes command on reconnect |
| Watchdog reset recovery | Pool Node watchdog reset during measurement cycle | Device restarts, resumes normal operation on next cycle |
| Sensor failure mid-operation | Temperature sensor fails after successful reads | Status message sent with null temperature, error logged |
| Rate limit exceeded | Commands sent faster than rate limit allows | Excess commands ignored, rate limit violation logged (DEFERRED to Phase 4+) |
| Clock drift scenario | Device clock drifts >30 seconds from server time | Re-sync corrects time, scheduling remains accurate |

*Note: These scenarios test edge cases and failure modes that are difficult to encounter during normal operation but critical for system reliability.*

**Test Framework:**

| Language | Framework | Location |
|----------|-----------|----------|
| Python (shared libs) | pytest + Blinka + mocks | `tests/unit/`, `tests/integration/` |
| C++ (Pool Node) | PlatformIO Unity | `pool_node_cpp/test/` |

### CircuitPython Testing Pattern

```python
# tests/conftest.py - Shared fixtures for CircuitPython mocking
import pytest
from unittest.mock import MagicMock

@pytest.fixture(autouse=True)
def mock_circuitpython_modules(monkeypatch):
    """Mock CircuitPython hardware modules for all tests."""
    mock_board = MagicMock()
    mock_digitalio = MagicMock()
    mock_wifi = MagicMock()
    mock_microcontroller = MagicMock()

    monkeypatch.setitem(__import__('sys').modules, 'board', mock_board)
    monkeypatch.setitem(__import__('sys').modules, 'digitalio', mock_digitalio)
    monkeypatch.setitem(__import__('sys').modules, 'wifi', mock_wifi)
    monkeypatch.setitem(__import__('sys').modules, 'microcontroller', mock_microcontroller)
```

### GitHub Actions CI

**Workflow file:** `.github/workflows/ci.yml`

```yaml
name: CI

on:
  push:
    # Run on all branch pushes to catch errors early
  pull_request:
    # Run on all PRs

jobs:
  test-python:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v4

      - name: Set up Python
        run: uv python install 3.11

      - name: Install dependencies
        run: uv sync

      - name: Run unit tests
        env:
          BLINKA_MCP2221: 1
        run: uv run pytest tests/unit/ -v

      - name: Run integration tests
        env:
          BLINKA_MCP2221: 1
        run: uv run pytest tests/integration/ -v

  test-cpp:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v4

      - name: Set up PlatformIO
        uses: actions/cache@v4
        with:
          path: ~/.platformio
          key: ${{ runner.os }}-pio

      - name: Install PlatformIO
        run: uv pip install platformio --system

      - name: Run Pool Node tests
        run: cd pool_node_cpp && pio test

  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v4

      - name: Install dependencies
        run: uv sync

      - name: Run ruff (lint + format check)
        run: uv run ruff check src/shared/ tests/

      - name: Run mypy (type check)
        run: uv run mypy src/shared/ --ignore-missing-imports
```

**CI Requirements:**

- All tests must pass before merge to main
- Linting and type checking must pass
- Branch protection rule on `main` should require CI to pass

**Testing Limitations:**

- CI tests shared libraries and business logic only
- Hardware-specific code (sensors, display, WiFi) requires on-device testing
- Full integration testing with actual nodes is manual (see Phase 2 exit criteria)

### Development Dependencies

**`pyproject.toml`** (uv uses this for dependency management):

```toml
[project]
name = "poolio"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = []

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-asyncio>=0.21",
    "adafruit-blinka>=8.0",
    "ruff>=0.1",
    "mypy>=1.0",
]

[tool.uv]
dev-dependencies = [
    "pytest>=7.0",
    "pytest-asyncio>=0.21",
    "adafruit-blinka>=8.0",
    "ruff>=0.1",
    "mypy>=1.0",
]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.mypy]
python_version = "3.11"
ignore_missing_imports = true
```

---

## Build Sequence

The build sequence aligns with the migration phases defined in requirements.md Section 8.

### Phase 1: Foundation (2 weeks)

**Goal:** Shared libraries and message protocol fully functional.

**Tasks:**

- [ ] Set up project structure (src/shared/, schemas/, tests/)
- [ ] Define all message type dataclasses (types.py)
- [ ] Implement envelope creation/parsing (envelope.py)
- [ ] Implement message encoder/decoder
- [ ] Create JSON schemas for all message types
- [ ] Implement validator with full/simplified modes
- [ ] Implement CloudBackend abstract base
- [ ] Implement AdafruitIOHTTP client
- [ ] Implement AdafruitIOMQTT client
- [ ] Implement mock backend for testing
- [ ] Implement config loader and environment handler
- [ ] Implement logger with structured output
- [ ] Implement retry utilities and bus recovery helpers
- [ ] Write unit tests for all modules
- [ ] Write integration test: encode → publish → subscribe → decode

**Exit Criteria:** All unit tests pass; integration test demonstrates end-to-end flow.

### Phase 2: Device Framework (4 weeks)

**Goal:** All nodes operational with JSON messages. This is the **MVP**.

#### Phase 2a: Pool Node (2 weeks)

- [ ] Set up PlatformIO project
- [ ] Port message encoder to C++
- [ ] Port config loader to C++
- [ ] Implement watchdog wrapper
- [ ] Implement WiFi manager with 15s timeout
- [ ] Implement time sync
- [ ] Implement HTTP client with 10s timeout
- [ ] Implement temperature sensor with retry
- [ ] Implement float switch consensus logic
- [ ] Implement battery monitor with I2C recovery
- [ ] Implement sleep manager with cleanup
- [ ] Implement PoolNode controller
- [ ] Test with real hardware
- [ ] Run 24-hour stability test

**Exit Criteria:** Pool Node completes wake/measure/transmit/sleep cycle reliably.

#### Phase 2b: Valve Node (1 week)

- [ ] Set up CircuitPython project structure
- [ ] Implement scheduler (fill window logic)
- [ ] Implement safety interlocks
- [ ] Implement valve controller
- [ ] ~~Implement command rate limiting~~ (DEFERRED to Phase 4+)
- [ ] Deploy to hardware
- [ ] Verify all safety interlocks
- [ ] Run integration test with Pool Node

**Exit Criteria:** Valve Node schedules fills correctly; all interlocks verified.

#### Phase 2c: Display Node (1 week)

- [ ] Set up CircuitPython project structure
- [ ] Implement UI theme and widgets
- [ ] Implement touch handler with debouncing
- [ ] Implement screens (main, settings)
- [ ] Implement dashboard controller
- [ ] Deploy to hardware
- [ ] Calibrate touchscreen
- [ ] Verify status display and touch commands

**Exit Criteria:** Display updates in real-time; touch commands work reliably.

### Phase 3: Simulators & Testing (1 week)

**Goal:** Full system testable without hardware.

- [ ] Implement pool node simulator
- [ ] Implement valve node simulator
- [ ] Implement display node simulator (logging mode)
- [ ] Write integration tests using simulators
- [ ] Document simulator usage

**Exit Criteria:** Simulators can replace physical hardware for development.

### Phase 4: Deployment (2 weeks)

#### Phase 4a: Nonprod Deployment (1 week)

- [ ] Create nonprod feeds in Adafruit IO
- [ ] Configure all devices with ENVIRONMENT=nonprod
- [ ] Deploy all nodes to nonprod
- [ ] Run 1-week stability test
- [ ] Address any issues found

**Exit Criteria:** 1 week of stable operation; zero watchdog resets.

#### Phase 4b: Production Deployment (1 week)

- [ ] Review nonprod results
- [ ] Create production deployment checklist
- [ ] Deploy to production
- [ ] Monitor for 48 hours
- [ ] Document rollback plan

**Exit Criteria:** Production system operational.

### Phase 5: Smart Home Integration (2 weeks)

**Goal:** Apple HomeKit integration.

- [ ] Set up Node.js/TypeScript project
- [ ] Implement platform plugin
- [ ] Implement all accessories (temperature, valve, battery, water level)
- [ ] Implement cloud client (MQTT to Adafruit IO)
- [ ] Test with iOS Home app
- [ ] Verify Siri commands
- [ ] Publish to npm (optional)

**Exit Criteria:** Homebridge plugin pairs with Home app; Siri commands work.

### Phase 6: Reliability & Polish (Ongoing)

- [ ] Implement enhanced error handling
- [ ] Add comprehensive observability
- [ ] Performance testing and optimization
- [ ] Implement command message signing (NFR-SEC-003)
- [ ] Document all operational procedures

---

## Critical Details

### Error Handling

**Pool Node:**

- Catch specific exceptions (never bare `except:`)
- Log all exceptions with context before handling
- Graduated response within single wake cycle: retry → bus recovery → sensor disable → device reset
- Failure tracking is ephemeral (resets each wake cycle per stateless design)
- Send error message before reset (90s delay to allow propagation)

**Valve Node:**

- Validate all incoming messages (schema + freshness)
- Rate limit commands per the table in Components section (DEFERRED to Phase 4+ - implement only if abuse detected)
- Publish command_response for all commands (success or failure)
- Continue active fill to max duration if pool node data becomes stale
- Log warning when continuing fill without fresh pool data

**Display Node:**

- Handle stale data gracefully (alert color, not crash)
- Timeout on command acknowledgment (5s)
- Touch debouncing (250ms) to prevent double-commands
- Persist current screen for recovery from reset

### Unconfigured Device Behavior

If a device boots with missing or invalid credentials (WiFi SSID, password, or Adafruit IO API key):

**Pool Node (C++):**
- Log "Missing credentials" error to serial
- Enter deep sleep immediately (preserve battery)
- Retry on next wake cycle

**Valve Node (CircuitPython):**
- Log "Missing credentials" error to serial
- Do not attempt WiFi/MQTT connection
- Enter safe state (valve remains closed)
- Blink LED pattern to indicate configuration needed

**Display Node (CircuitPython):**
- Display "Not Configured" message on screen
- Show instructions: "Edit settings.toml with WiFi and API credentials"
- No MQTT connection attempted
- Touch input disabled until properly configured

*Note: MVP requires manual configuration via settings.toml (CircuitPython) or secrets.h (C++). Captive portal provisioning is deferred to Issue 4.18.*

### State Management

**Pool Node:**

- Stateless by design (each wake cycle is independent)
- Configuration persisted in NVS across sleep cycles
- No command handling (deep sleep prevents MQTT)

**Valve Node:**

- State machine: `idle` → `filling` → `idle`
- On reset, valve closes automatically (GPIO goes low), state resets to `idle`
- Track last pool_status timestamp for freshness checking
- Maintain command timestamps for rate limiting (DEFERRED to Phase 4+)

**Display Node:**

- Track latest message from each device type
- Calculate data staleness on each render cycle
- Persist current screen for recovery from reset
- Track pending commands for timeout handling

### Performance Targets

| Metric | Target |
|--------|--------|
| Pool Node wake cycle | <15s typical, <30s max |
| Pool Node battery life | 3+ months on 2000mAh |
| Valve command response | <1s |
| Display screen refresh | 1Hz |
| Message size | <300 bytes typical, <4KB max |
| System message rate | ~3/min (within 30/min free tier) |

### Security Considerations

- Never commit credentials to version control
- Use separate API keys per environment
- TLS/SSL for all communications (HTTPS, MQTT port 8883)
- Validate message timestamps (<5 min for commands, <15 min for status)
- Rate limit commands on receiving device (DEFERRED to Phase 4+ - implement only if abuse detected)
- Consider disabling USB mass storage in production (CircuitPython)
- Maintain list of trusted device IDs; ignore messages from unknown sources

### Source Control and Secrets Management

**Files to add to `.gitignore`** (contain actual secrets):

```gitignore
# CircuitPython secrets
settings.toml

# C++ secrets
pool_node_cpp/include/secrets.h

# IDE and build artifacts
.pio/
__pycache__/
*.pyc

# Local environment overrides
.env
.env.local
```

**Template files to commit** (contain placeholder values):

| Template File | Actual File | Purpose |
|---------------|-------------|---------|
| `config/nonprod/settings.toml.template` | `settings.toml` | CircuitPython secrets (nonprod) |
| `config/prod/settings.toml.template` | `settings.toml` | CircuitPython secrets (prod) |
| `pool_node_cpp/include/secrets.h.example` | `secrets.h` | C++ secrets |

**Template file pattern:**

- Template files use `.template` or `.example` suffix
- Templates contain placeholder values like `YOUR_WIFI_SSID`
- Templates are committed to version control
- Actual files are created by copying template and filling in real values
- Actual files are in `.gitignore` and never committed

**Example `secrets.h.example`:**

```cpp
// Copy to secrets.h and fill in your values
// secrets.h is in .gitignore - never commit actual secrets

#define WIFI_SSID "YOUR_WIFI_SSID"
#define WIFI_PASSWORD "YOUR_WIFI_PASSWORD"
#define AIO_USERNAME "YOUR_AIO_USERNAME"
#define AIO_KEY "YOUR_AIO_KEY"
```

---

## Resolved Questions

1. **Pump Node Communication Protocol:** TBD - will not be known until the pump is purchased and installed. Pump integration could easily be after Phase 5 or 6. The Pump Node is included in this architecture to demonstrate that additional components may be added to the system at a later date.

2. **Display Node Touch UI Design:** A separate UI design document will be created specifying button layouts, screen transitions, and confirmation dialogs. **This document must be completed before Display Node implementation can begin (Phase 2c).**

3. **HomeKit Service Types:** Water level will use **Contact Sensor** (not Leak Sensor). Water in a pool did not leak to get there - Contact Sensor is semantically more appropriate.

4. **C++ Shared Library Strategy:** Independent implementation. C++ Pool Node will implement the same message protocol with equivalent API contracts, not a direct port of Python libraries.

5. **OTA Updates:** Deferred. All architectural decisions around OTA updates are deferred to future phases.

6. **Device Discovery:** Simple queue-based discovery. A device is "discovered" the first time it posts to the gateway queue. Pre-registration requirements suggest that device registration data should be stored somewhere accessible to the Display Node - potentially in Adafruit IO as a dedicated feed (e.g., `poolio.devices`) containing a JSON list of registered device IDs and types.

---

*This architecture document synthesizes the best approaches from architecture1.md and architecture2.md, providing a complete blueprint for implementing the Poolio system. Each phase has concrete deliverables and exit criteria. The JSON message protocol serves as the integration contract, enabling mixed languages and future extensibility.*
