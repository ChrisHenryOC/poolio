# Poolio Rearchitect

A distributed IoT pool automation and monitoring system being rearchitected from three existing CircuitPython projects.

## System Overview

Poolio automates pool water management:

- **Pool Node** - Battery-powered sensor monitoring pool temperature, water level, and battery status
- **Valve Node** - Controls fill valve based on schedule and water level
- **Display Node** - TFT touchscreen dashboard showing real-time status
- **Pump Node** - Variable speed pump control (future)

All nodes communicate via JSON messages over MQTT (Adafruit IO).

```text
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Pool Node     │     │   Valve Node     │     │  Display Node   │
│  (Sensor Unit)  │     │ (Fill Controller)│     │   (Dashboard)   │
└────────┬────────┘     └────────┬─────────┘     └────────┬────────┘
         │                       │                        │
         └───────────────────────┴────────────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │      Adafruit IO        │
                    │   (Cloud Message Broker)│
                    └─────────────────────────┘
```

## Documentation

| Document | Purpose |
|----------|---------|
| [docs/requirements.md](docs/requirements.md) | Comprehensive system requirements |
| [docs/architecture.md](docs/architecture.md) | System architecture and implementation details |
| [CLAUDE.md](CLAUDE.md) | Development guidance for Claude Code |

## Original Projects (Reference)

This rearchitecture consolidates and improves upon:

- `~/source/Poolio-PoolNode` - Original pool sensor
- `~/source/PoolIO-ValveNode` - Original valve controller
- `~/source/Poolio-DisplayNode` - Original display dashboard

## Target Hardware

| Node | MCU | Key Components |
|------|-----|----------------|
| Pool Node | ESP32 Feather | DS18X20 temp, float switch, LC709203F battery gauge |
| Valve Node | ESP32-S3 Feather | DS18X20 temp, solenoid valve relay |
| Display Node | ESP32 Feather | ILI9341 TFT, STMPE610 touch, AHTx0 temp/humidity |

## Development

See [CLAUDE.md](CLAUDE.md) for detailed development workflow, code standards, and project guidance.

### Quick Start

```bash
# Install dependencies
uv sync

# Run unit tests
uv run pytest tests/unit/

# Lint markdown files
npx markdownlint-cli docs/*.md
```

### CircuitPython Deployment

Deploy code and libraries to a connected CircuitPython device:

```bash
# Deploy to specific node type
python circuitpython/deploy.py --target pool-node --source
python circuitpython/deploy.py --target valve-node --source
python circuitpython/deploy.py --target display-node --source

# List available targets
python circuitpython/deploy.py --list-targets
```

The deploy script automatically downloads the Adafruit CircuitPython bundle and installs the required libraries for each node type.

### On-Device Testing

Run tests directly on CircuitPython hardware:

```bash
# Deploy test framework to device
python circuitpython/deploy.py --target test --source --tests

# Monitor test output
python scripts/serial_monitor.py --reset --timeout 60
```

| Test Suite | Count | Location | Runner |
|------------|-------|----------|--------|
| Unit tests | 206 | `tests/unit/` | pytest (Blinka) |
| Device tests | 27 | `tests/device/` | CircuitPython hardware |

### CI/CD

GitHub Actions automatically validates all code on push and pull requests:

| Workflow | Purpose |
|----------|---------|
| Markdown | Documentation linting |
| CircuitPython | Python tests via [Adafruit Blinka](https://github.com/adafruit/Adafruit_Blinka) |
| C++ | PlatformIO builds for ESP32 |
| Node.js | Homebridge plugin tests |

## Implementation Phases

1. **Foundation** - Shared libraries, JSON messages, cloud abstraction
2. **Device Framework** - Pool Node, Valve Node, Display Node
3. **Simulators & Testing** - Node simulators, integration tests
4. **Deployment** - Nonprod and production environments
5. **Smart Home** - Homebridge plugin for Apple HomeKit
6. **Reliability & Polish** - Enhanced error handling, observability

## License

[Add your license here]
