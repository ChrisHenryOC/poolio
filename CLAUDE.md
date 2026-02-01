# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Poolio Rearchitecture** - A distributed IoT pool automation and monitoring system being rearchitected from three existing CircuitPython projects (PoolIO-ValveNode, Poolio-PoolNode, Poolio-DisplayNode).

### Original Projects (Reference)

- `~/source/Poolio-PoolNode` - Battery-powered pool sensor (temperature, water level, battery)
- `~/source/PoolIO-ValveNode` - Fill valve controller with scheduling
- `~/source/Poolio-DisplayNode` - TFT touchscreen dashboard

### System Purpose

Automated pool water management:

- Monitor pool temperature and water level
- Automatically fill pool on schedule when water is low
- Control variable speed pump (future)
- Display status on touchscreen dashboard
- Integrate with Apple HomeKit

## Documentation

**`docs/requirements.md`** - Comprehensive requirements including:

- Functional requirements for each node type
- Reliability requirements (especially Pool Node)
- JSON message format specification
- Cloud backend abstraction (Adafruit IO with pluggable backends)
- Device extensibility architecture (plugin system for new devices)
- Apple HomeKit integration
- Implementation language considerations (CircuitPython vs C++)

**`docs/architecture.md`** - System architecture and implementation details:

- Component design and interfaces
- CircuitPython compatibility patterns (Section 8)
- Message protocol specification
- Reliability patterns (watchdog, retry, bus recovery)
- Environment configuration
- Deployment procedures
- Build sequence and phases

## Target Hardware

| Node         | MCU                | Key Hardware                                                    |
| ------------ | ------------------ | --------------------------------------------------------------- |
| Pool Node    | ESP32 (Feather)    | DS18X20 temp sensor, float switch, LC709203F battery gauge      |
| Valve Node   | ESP32-S3 (Feather) | DS18X20 temp sensor, solenoid valve relay                       |
| Display Node | ESP32 (Feather)    | ILI9341 TFT display, STMPE610 touchscreen, AHTx0 temp/humidity  |
| Pump Node    | TBD                | RS-485 interface for variable speed pump                        |

## Architecture Principles

### Communication

- All nodes communicate via **JSON messages** over MQTT (Adafruit IO)
- Standardized message envelope: `{version, type, deviceId, timestamp, payload}`
- Cloud backend is abstracted to support alternative providers (AWS IoT, etc.)

### Language Flexibility

Both **CircuitPython** and **C++ (Arduino/ESP-IDF)** are valid implementation choices:

- Pool Node: Prefer C++ for reliability (timeout control, bus recovery)
- Display Node: Prefer CircuitPython for rapid UI iteration
- Other nodes: Evaluate based on specific requirements

### Device Plugin Architecture

New device types can be added via configuration without core code changes:

- Devices declare capabilities (sensors, commands)
- Display Node dynamically generates UI based on capabilities
- Inter-device communication for coordination (e.g., valve + pump)

## Project Structure

```text
poolio_rearchitect/
├── .claude/
│   ├── agents/              # Code review agent definitions
│   ├── commands/            # Slash command definitions
│   ├── memories/            # Persistent context/patterns
│   └── references/          # Reference documentation
├── .github/
│   └── workflows/           # GitHub Actions CI/CD pipelines
│       ├── markdown.yml     # Documentation linting
│       ├── circuitpython.yml # Python tests (Adafruit Blinka)
│       ├── cpp.yml          # PlatformIO builds
│       └── nodejs.yml       # Homebridge plugin tests
├── circuitpython/           # CircuitPython deployment tools
│   ├── requirements/        # Library requirements per target
│   │   ├── base.txt         # Common libraries (all nodes)
│   │   ├── pool-node.txt    # Pool node specific
│   │   ├── valve-node.txt   # Valve node specific
│   │   ├── display-node.txt # Display node specific
│   │   └── test.txt         # On-device testing
│   ├── deploy.py            # Deployment script
│   └── bundle/              # Downloaded Adafruit bundle (.gitignore'd)
├── docs/
│   ├── requirements.md      # Comprehensive requirements document
│   └── architecture.md      # System architecture and implementation details
├── scripts/
│   └── serial_monitor.py    # Serial port monitor for device testing
├── src/
│   └── shared/              # Shared libraries (CircuitPython compatible)
│       └── messages/        # JSON message protocol (implemented)
├── tests/
│   ├── unit/                # Unit tests (pytest, runs with Blinka)
│   └── device/              # On-device tests (runs on actual hardware)
│       ├── runner.py        # Lightweight test runner for CircuitPython
│       ├── assertions.py    # CircuitPython-compatible assertions
│       └── shared/          # Tests for shared library
├── CLAUDE.md                # This file - project guidance
└── README.md                # Project overview
```

### Future Structure (to be created during implementation)

```text
poolio_rearchitect/
├── src/
│   ├── shared/              # Shared libraries (CircuitPython compatible)
│   │   ├── messages/        # JSON message protocol (implemented)
│   │   ├── cloud/           # Cloud backend abstraction
│   │   ├── config/          # Configuration management
│   │   ├── logging/         # Structured logging (adafruit_logging)
│   │   └── sensors/         # Sensor retry and bus recovery
│   ├── valve_node/          # Valve controller (CircuitPython)
│   ├── display_node/        # Display dashboard (CircuitPython)
│   └── simulators/          # Desktop simulators (CPython)
├── pool_node_cpp/           # Pool sensor (C++/PlatformIO)
├── homebridge/              # Homebridge plugin for HomeKit (Node.js)
└── schemas/                 # JSON schemas for validation
```

**See `docs/architecture.md` Section 5 (Directory Structure)** for complete file layout.

## Development Workflow

### For CircuitPython Nodes

```bash
# Deploy libraries, source code, and environment config to device
python circuitpython/deploy.py --target valve-node --env nonprod --source
python circuitpython/deploy.py --target display-node --env nonprod --source

# Deploy for on-device testing
python circuitpython/deploy.py --target test --source --tests

# List available deployment targets
python circuitpython/deploy.py --list-targets

# Monitor serial output (preferred - has timeout handling)
python scripts/serial_monitor.py --timeout 60

# Alternative: screen (interactive)
screen /dev/tty.usbmodem* 115200
# Exit: Ctrl+A, K, Y
```

The deploy script automatically:

- Downloads the Adafruit CircuitPython bundle if not present
- Installs base libraries + target-specific libraries
- Optionally copies `src/shared/` and `tests/device/` to device

### For C++ Nodes (Arduino/PlatformIO)

```bash
# Build
pio run

# Upload
pio run --target upload

# Monitor
pio device monitor
```

### For Homebridge Plugin

```bash
cd homebridge/
npm install
npm run build
npm link  # For local testing
```

### Git Workflow

All changes must go through a branch and pull request before merging to main:

1. Create a feature branch for your changes
2. Commit changes to the branch
3. Push the branch and create a pull request
4. Merge the PR (use `/merge-pr <number>` command)

Never push directly to the `main` branch.

### Markdown Linting

Run markdownlint on new or edited markdown files before committing:

```bash
npx markdownlint-cli docs/requirements.md
npx markdownlint-cli docs/architecture.md
npx markdownlint-cli **/*.md  # All markdown files
```

The project uses `.markdownlint.jsonc` for configuration. Fix any reported issues before committing. Files excluded via `.gitignore` do not need to be linted.

### CI/CD (GitHub Actions)

All code is validated automatically via GitHub Actions on push and PR:

| Workflow | Trigger | What It Does |
|----------|---------|--------------|
| `markdown.yml` | `**/*.md` changes | Runs markdownlint |
| `circuitpython.yml` | `src/**/*.py`, `tests/**/*.py` | Tests with [Adafruit Blinka](https://github.com/adafruit/Adafruit_Blinka) |
| `cpp.yml` | `pool_node_cpp/**` | PlatformIO build + native tests |
| `nodejs.yml` | `homebridge/**` | npm lint, test, build |

Workflows only run when relevant files change. All PRs to `main` must pass CI checks.

## Key Design Decisions

### Reliability (Pool Node)

- Watchdog timer with feeds at ≤25% of timeout
- Explicit timeouts on all blocking operations
- Bus recovery mechanisms (I2C, OneWire)
- Proper resource cleanup before deep sleep
- No bare `except:` clauses - always catch specific exceptions

### Message Protocol

- JSON format for extensibility and debugging
- MQTT broker (Adafruit IO) handles message ordering and deduplication
- Backward compatibility with legacy pipe-delimited format during migration

### Configuration

- Hardware pin mappings in config files, not code
- Remote configuration via cloud backend
- Schema validation for all configuration

### Environments

The system supports multiple deployment environments:

**Two-environment model:**

| Environment | Feed Prefix | Hardware     | Use Case                    |
| ----------- | ----------- | ------------ | --------------------------- |
| `prod`      | (none)      | Enabled      | Live production system      |
| `nonprod`   | `nonprod-`  | Configurable | Development and testing     |

**Three-environment model (if needed):**

| Environment | Feed Prefix | Hardware     | Use Case                    |
| ----------- | ----------- | ------------ | --------------------------- |
| `dev`       | `dev-`      | Disabled     | Local development           |
| `test`      | `test-`     | Configurable | Integration testing         |
| `prod`      | (none)      | Enabled      | Live production system      |

- Environment is set in `settings.toml` (CircuitPython) or build config (C++)
- Feed names are automatically prefixed: `nonprod-pooltemp`, `nonprod-gateway`, etc.
- Non-prod environments show visual indicator on Display Node
- Hardware can be disabled per environment (valve commands logged but not executed)

## Code Standards

### CircuitPython

- Feed watchdog before/after blocking operations
- Close all resources (sockets, responses, buses) explicitly
- Use `try/finally` for cleanup
- Log all exceptions with context before handling

#### CircuitPython Compatibility Constraints

CircuitPython is a subset of Python with limited standard library. The following modules are **NOT available**:

| Unavailable Module | Use Instead |
|--------------------|-------------|
| `dataclasses` | Plain classes with `__init__` |
| `abc` (ABC, abstractmethod) | Duck typing with `NotImplementedError` |
| `jsonschema` | Simplified manual validation on-device |
| `typing` (Any, Optional, etc.) | Conditional import with try/except (see below) |
| `datetime` | `adafruit_datetime` library (or conditional import) |
| `logging` | `adafruit_logging` library |
| `str.capitalize()` | Manual: `s[0].upper() + s[1:]` |

**Pattern Examples:**

```python
# WRONG - dataclass not available
@dataclass
class Temperature:
    value: float

# CORRECT - plain class
class Temperature:
    def __init__(self, value, unit="fahrenheit"):
        self.value = value
        self.unit = unit

# WRONG - abc not available
class CloudBackend(ABC):
    @abstractmethod
    def publish(self, feed, value): ...

# CORRECT - duck typing
class CloudBackend:
    def publish(self, feed, value):
        raise NotImplementedError("Subclasses must implement publish()")

# WRONG - type hints in signatures
def get_feed_name(logical_name: str, environment: str) -> str:

# CORRECT - types in docstrings
def get_feed_name(logical_name, environment):
    """Get feed name. Args are strings, returns string."""

# WRONG - unconditional typing import
from typing import Any

# CORRECT - conditional import for CircuitPython compatibility
try:
    from typing import Any
except ImportError:
    Any = None  # CircuitPython doesn't have typing module

# WRONG - unconditional datetime import
from datetime import datetime

# CORRECT - fallback to adafruit_datetime
try:
    from datetime import datetime
except ImportError:
    try:
        from adafruit_datetime import datetime
    except ImportError:
        datetime = None  # Timestamp features disabled
```

**See `docs/architecture.md` Section 8 (CircuitPython Compatibility)** for comprehensive patterns and dual-implementation strategy.

### C++ (Arduino/ESP-IDF)

- Use FreeRTOS tasks for timeout mechanisms
- Implement proper I2C/OneWire bus recovery
- Use ESP-IDF WiFi APIs for timeout control

### All Languages

- Structured logging with levels (DEBUG, INFO, WARNING, ERROR)
- Include deviceId and timestamp in all log entries
- Validate all incoming messages against schema

## Anti-Patterns to Avoid

- Bare `except:` or `catch(...)` that hide errors
- Blocking operations without timeouts
- Global state without clear ownership
- Hard-coded magic numbers (use configuration)
- Assuming network operations will succeed
- Skipping resource cleanup on error paths
- Using `@dataclass`, `ABC`, or `typing` imports in CircuitPython code
- Type hints in function signatures for CircuitPython (use docstrings instead)
- Importing `jsonschema` on-device (use simplified validation)

## Testing Strategy

### Unit Tests (CPython/Blinka)

- Run via pytest: `uv run pytest tests/unit/`
- 206 tests covering message types, encoding, decoding, validation
- Uses [Adafruit Blinka](https://github.com/adafruit/Adafruit_Blinka) for CircuitPython API compatibility
- CI runs automatically on push/PR via GitHub Actions

### On-Device Tests (CircuitPython Hardware)

- Run directly on ESP32 hardware via `/run-device-tests` command
- 27 tests covering core message functionality
- Validates actual CircuitPython compatibility (not just Blinka emulation)
- Uses lightweight test runner (`tests/device/runner.py`)

```bash
# Deploy and run device tests
python circuitpython/deploy.py --target test --source --tests

# Monitor test output
python scripts/serial_monitor.py --reset --timeout 60
```

Test output format:

```text
=== TEST RUN START ===
BOARD: adafruit_feather_esp32s3_4mbflash_2mbpsram
CIRCUITPYTHON: 9.2.8
MEMORY_START: 2053840 bytes free
---
MODULE: shared.messages
[PASS] test_water_level_creation (0ms)
[FAIL] test_example: assertion message
[ERROR] test_broken: ExceptionType: message
[SKIP] test_skipped: reason
---
=== TEST RUN END ===
SUMMARY: 27 passed, 0 failed, 0 error, 0 skipped
```

### Test Coverage

| Test Type | Location | Count | Purpose |
|-----------|----------|-------|---------|
| Unit tests | `tests/unit/` | 206 | Full coverage, runs in CI |
| Integration tests | `tests/integration/` | 3 | Message round-trip flow |
| Device tests | `tests/device/` | 71 | Hardware validation |

## Sequential Thinking

**Use `mcp__sequential-thinking__sequentialthinking`** for complex problem-solving tasks that benefit from structured reasoning.

### When to Use

| Scenario                     | Example                                                        |
| ---------------------------- | -------------------------------------------------------------- |
| **Architecture decisions**   | Choosing between CircuitPython vs C++ for a node               |
| **Debugging complex issues** | Tracing intermittent sensor failures across hardware/software  |
| **Implementation planning**  | Breaking down a feature into sized issues                      |
| **Tradeoff analysis**        | Reliability vs battery life for Pool Node                      |
| **Protocol design**          | Designing message formats for new device types                 |

### How to Use

1. **Start with an estimate** - How many thoughts needed? (typically 4-8)
2. **Think step by step** - Each thought builds on previous insights
3. **Revise when needed** - Use `isRevision: true` to reconsider earlier conclusions
4. **Branch for alternatives** - Use `branchFromThought` when exploring multiple approaches
5. **Adjust as you go** - Increase `totalThoughts` if problem is more complex than expected

### Project-Specific Applications

- **Reliability analysis**: Trace failure modes through watchdog → sensor → network → cloud
- **Message protocol changes**: Think through backward compatibility implications
- **Cross-node coordination**: Design valve + pump interaction sequences
- **Error recovery**: Plan bus recovery and retry strategies

### When NOT to Use

- Simple, straightforward tasks (adding a config field, fixing a typo)
- Well-understood patterns with clear implementations
- Tasks where the solution is obvious from requirements

## Migration Phases

1. **Foundation**: Shared libraries, JSON messages, cloud abstraction
2. **Device Framework**: Plugin architecture, migrate existing nodes
3. **Extensibility**: Variable speed pump, inter-device communication
4. **Smart Home**: Homebridge plugin for HomeKit
5. **Reliability**: Enhanced error handling, observability
