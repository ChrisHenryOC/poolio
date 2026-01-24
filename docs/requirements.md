# Poolio System Requirements

Reverse-engineered from the original PoolIO-ValveNode, Poolio-PoolNode, and Poolio-DisplayNode projects.

## How to Use This Document

| Section | Purpose | Read When... |
|---------|---------|--------------|
| 2. Functional Requirements | What each node must do | Implementing node behavior |
| 3. Non-Functional Requirements | Reliability, security, performance | Implementing error handling, timeouts |
| 4. Hardware Requirements | MCU and sensor specifications | Setting up physical hardware |
| 5. Communication Protocol | MQTT feeds, REST endpoints, rate limits | Setting up cloud communication |
| 6. Configuration Requirements | Settings files and parameters | Configuring nodes |
| 7.1 Pool Node Reliability | Timeouts, bus recovery, watchdog | Implementing Pool Node |
| 7.2 JSON Message Format | Message schemas and payloads | Parsing or creating messages |
| 7.3 Device Extensibility | Adding new device types | Adding pump or other devices |
| 7.4 HomeKit Integration | Apple Home app support | Implementing Homebridge plugin |
| 7.5 Environment Configuration | Prod/nonprod setup | Configuring deployment |
| 7.6-7.7 Architecture & Simulators | Shared libraries, testing tools | Setting up development environment |
| Appendix A | JSON Schema definitions | Validating messages |

---

## 1. System Overview

The Poolio system is a distributed IoT pool automation and monitoring platform consisting of three node types that communicate via a cloud-based message broker (Adafruit IO).

### 1.1 System Architecture

```text
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Pool Node     │     │   Valve Node     │     │  Display Node   │
│  (Sensor Unit)  │     │ (Fill Controller)│     │   (Dashboard)   │
└────────┬────────┘     └────────┬─────────┘     └────────┬────────┘
         │                       │                        │
         │ HTTPS POST            │ MQTT PUB/SUB           │ MQTT SUB
         │                       │                        │
         └───────────────────────┴────────────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │      Adafruit IO        │
                    │   (Cloud Message Broker)│
                    └─────────────────────────┘
```

### 1.2 Node Descriptions

| Node         | Purpose                                                  | Power Source       | Communication             |
| ------------ | -------------------------------------------------------- | ------------------ | ------------------------- |
| Pool Node    | Monitors pool water temperature, level, and sensor battery | Battery (deep sleep) | HTTP REST API             |
| Valve Node   | Controls fill valve based on schedule and water level    | AC/DC powered      | MQTT bidirectional        |
| Display Node | Shows real-time status and historical data               | AC/DC powered      | MQTT subscribe + HTTP REST |

*Note: For detailed hardware specifications including MCU types and pin assignments, see Section 4 (Hardware Requirements).*

---

## 2. Functional Requirements

### 2.1 Pool Node (Sensor Unit)

#### FR-PN-001: Temperature Monitoring

- **SHALL** read pool water temperature using a DS18X20 one-wire sensor
- **SHALL** convert temperature per FR-SH-004 (Temperature Units)
- **SHALL** validate temperature readings are within 0°F to 110°F range
- **SHALL** retry failed sensor reads up to 3 times with exponential backoff (see NFR-REL-002)

*Note: Pool water temperature range (0-110°F) is narrower than outside temperature range (-20-130°F in FR-VN-004) because pool water cannot reasonably be below freezing or above hot tub temperatures.*

#### FR-PN-002: Water Level Detection

- **SHALL** detect pool water level using a float switch
- **SHALL** report float switch state as boolean: true=pool full (water at sensor level), false=pool low (needs fill)
- **SHALL** perform multiple reads (default: 30) to establish consensus
- **SHALL** establish consensus when >66% of reads agree (e.g., 20+ of 30 reads)
- **SHALL** report "full" (1) if consensus cannot be established (safety-first: prevent filling when uncertain)

#### FR-PN-003: Battery Monitoring

- **SHALL** monitor battery voltage using LC709203F fuel gauge over I2C
- **SHALL** report battery voltage with 2 decimal precision
- **SHALL** report battery percentage (0-100%) as provided by fuel gauge

#### FR-PN-004: Data Transmission

- **SHALL** transmit sensor data to cloud platform via HTTPS POST
- **SHALL** send `pool_status` JSON message as primary format (see FR-MSG-004)
- **SHOULD** support legacy pipe-delimited format during transition period (see Section 5.4) - *Deferred to Phase 4+*
- **SHALL** send individual temperature and battery feeds
- **SHALL** support configurable transmission interval (default: 120 seconds)

#### FR-PN-005: Power Management

- **SHALL** enter deep sleep between measurement cycles
- **SHALL** wake on timer alarm
- **SHALL** calculate remaining sleep duration accounting for execution time
- **SHALL** enforce minimum sleep duration of 10 seconds
- **SHALL** disable watchdog before entering deep sleep
- **SHALL** re-enable watchdog immediately after waking from deep sleep

*Note: The ESP32 hardware watchdog is automatically disabled during deep sleep mode and must be re-enabled on wake. This prevents false watchdog resets during the low-power state.*

#### FR-PN-006: Remote Configuration

- **SHALL** use compiled/flashed default configuration values
- **SHALL** support local configuration file (settings.toml) to override defaults
- **SHALL** persist configuration in non-volatile storage (NVS/flash) across sleep cycles
- **SHALL** optionally fetch configuration from cloud platform on wake cycle
- **SHALL** support configurable sleep duration and float switch read count

> **Note:** Due to deep sleep power management, Pool Node uses a pull model for configuration updates. Configuration priority: persisted NVS > local file > compiled defaults. The specific cloud endpoint/mechanism for remote config updates is TBD - initial implementation may rely solely on local configuration with reflashing for changes.

---

### 2.2 Valve Node (Fill Controller)

#### FR-VN-001: Valve Control

- **SHALL** control solenoid valve via GPIO digital output
- **SHALL** open valve (HIGH) to start fill, close valve (LOW) to stop fill
- **SHALL** enforce maximum fill duration (default: 9 minutes)

#### FR-VN-002: Scheduled Filling

- **SHALL** support configurable fill start time (HH:MM format, zero-padded, e.g., "09:00")
- **SHALL** limit filling to a configurable window (default: 2 hours from start time)
- **SHALL** check fill eligibility at fixed intervals from window start time (default: 10 minutes)
- **SHALL** calculate and report next scheduled fill time

*Note: Fill eligibility is checked at fixed intervals from window start (e.g., if window starts at 09:00 with 10-minute interval: 09:00, 09:10, 09:20...). This ensures predictable scheduling regardless of fill duration.*

#### FR-VN-003: Safety Interlocks

- **SHALL** require recent pool node data before starting fill
- **SHALL NOT** start fill if no pool node message received within data freshness threshold
- **SHALL** calculate data freshness threshold as: `poolNodeInterval × stalenessMultiplier`
- **SHALL** use default stalenessMultiplier of 2 (configurable)
- **SHALL** obtain poolNodeInterval from pool_status message `reportingInterval` field (see FR-MSG-004)
- **SHALL** stop fill immediately when float switch indicates pool full (true=full)
- **SHALL** stop fill when maximum duration exceeded
- **SHALL** prevent filling outside configured time window
- **SHALL** continue active fill to max duration if pool node data becomes stale mid-fill
- **SHALL** log warning when continuing fill without fresh pool data

*Note: With default pool node interval of 120 seconds and 2x multiplier, data freshness threshold is 240 seconds (4 minutes). If no pool_status message is received within this window, the valve node will refuse to start a fill operation. Once a fill is in progress, it will continue to the maximum duration even if pool data becomes stale - the max duration timeout serves as the safety backstop.*

#### FR-VN-004: Temperature Monitoring

- **SHALL** read local/outside temperature using DS18X20 sensor
- **SHALL** validate temperature readings are within -20°F to 130°F range
- **SHALL** receive and track pool temperature from pool node messages
- **SHALL** report outside temperature to cloud platform

#### FR-VN-005: Cloud Communication

- **SHALL** maintain persistent MQTT connection to cloud broker
- **SHALL** subscribe to gateway feed for incoming sensor data
- **SHALL** subscribe to configuration feeds for remote settings updates
- **SHALL** publish valve_status JSON messages at configurable interval (default: 60 seconds, see FR-MSG-005)
- **SHALL** publish fill_start/fill_stop events immediately (see FR-MSG-007/FR-MSG-008)

#### FR-VN-006: Remote Control

- **SHALL** accept manual valve start command via MQTT using JSON `command` message (see FR-MSG-008)
- **SHALL** accept valve start time configuration via MQTT feed
- **SHALL** accept remote reset command via MQTT using JSON `command` message
- **SHOULD** support legacy message types 6 and 99 during transition period (see Section 5.4) - *Deferred to Phase 4+*

#### FR-VN-007: Status Reporting

- **SHALL** report valve run duration in minutes after each fill
- **SHALL** report current state including: temperature, valve active, seconds remaining, next fill time

---

### 2.3 Display Node (Dashboard)

#### FR-DN-001: Real-Time Data Display

- **SHALL** display current pool water temperature
- **SHALL** display current outside temperature (from valve node)
- **SHALL** display local temperature and humidity (from onboard sensor)
- **SHALL** display current date and time

#### FR-DN-002: Fill Status Display

- **SHALL** display current fill state (FILLING or idle)
- **SHALL** display next scheduled fill time
- **SHALL** display float switch status (water level indicator)
- **SHALL** display pool node battery voltage

#### FR-DN-003: Historical Data Visualization (Phase 3)

*Note: This requirement is deferred to Phase 3. MVP includes real-time status display only.*

**24-Hour View (Sparkline):**

- **SHALL** display 24-hour pool temperature history as sparkline graph
- **SHALL** calculate data point interval to fit 24 hours into available chart width (see Section 6.4 for calculation)
- **SHALL** apply smoothing to sparkline data using simple moving average (window: 3 data points)

**7-Day and 30-Day Views (Whisker Charts):**

- **SHALL** display 7-day pool temperature history as whisker chart showing daily min/max/average
- **SHALL** display 30-day pool temperature history as whisker chart showing daily min/max/average
- **SHALL** provide touch buttons to switch between 24-hour, 7-day, and 30-day views

**Common Requirements:**

- **SHALL** fetch historical data from cloud REST API at configurable refresh rate (default: 5 minutes)
- **SHALL** display min/max temperature values on graph
- **SHALL** display temperature statistics (range, average) below chart

*Note: Smoothing is applied only to the 24-hour sparkline view. Whisker charts display actual daily aggregations without smoothing. See Section 6.4 (Display Node Configuration) for chart parameters and data point interval calculation.*

#### FR-DN-004: Data Freshness Indication

- **SHALL** display timestamp of last update for pool node and valve node in device detail views
- **SHALL** indicate stale data with visual alert (highlight color, warning icon) on main dashboard when no update received within stale data indicator threshold
- **SHALL** use configurable stale data indicator threshold (default: 30 minutes / 1800 seconds)

*Note: Timestamps are displayed in detail views rather than the main dashboard to reduce clutter. The main dashboard uses visual indicators (amber highlight, warning icon) to show stale data at a glance. The 30-minute default threshold allows devices time to recover from restarts, watchdog resets, or temporary network issues without triggering false stale alerts. This is distinct from the valve node's data freshness threshold (FR-VN-003) which is used for safety interlocks.*

#### FR-DN-005: Cloud Communication

- **SHALL** fetch latest status from gateway feed on startup before subscribing to updates
- **SHALL** subscribe to gateway MQTT feed for real-time updates
- **SHALL** fetch historical data via HTTP REST API
- **SHALL** publish startup and error events to cloud platform

#### FR-DN-006: Local Sensing

- **SHALL** read local temperature and humidity using AHTx0 sensor
- **SHALL** convert temperature per FR-SH-004 (Temperature Units)
- **SHALL** publish local temperature to cloud at configurable interval
- **SHALL** include local sensor data in display node status messages

*Note: Local humidity is read and displayed but not published to cloud.*

#### FR-DN-007: Display Burn-In Prevention

- **SHALL** implement burn-in prevention cycle to preserve display lifespan
- **SHALL** trigger burn-in prevention after configurable idle period (default: 5 minutes)
- **SHALL** rotate display orientation for 7 seconds (configurable) during prevention cycle
- **SHALL** cycle through 4 background colors (configurable) during prevention cycle
- **SHALL** return to normal status display after burn-in prevention cycle completes
- **SHALL** skip burn-in prevention cycle if touch input detected

#### FR-DN-008: Touchscreen Input

- **SHALL** support touch input via STMPE610 touchscreen controller
- **SHALL** detect touch events (press, release)
- **SHALL** map touch coordinates to screen elements
- **SHALL** provide visual feedback on touch (button highlight/press state)
- **SHALL** debounce touch input (minimum 250ms between registered taps) to prevent accidental double-taps

#### FR-DN-009: Interactive Controls

- **SHALL** provide touch buttons for sending commands to other devices
- **SHALL** support the following command buttons (UI design TBD):
  - Manual fill start/stop (valve control)
  - Pump speed adjustment (when pump device present)
  - Pump program selection (when pump device present)
  - System refresh/sync
- **SHALL** display confirmation dialog for critical actions (e.g., manual fill)
- **SHALL** indicate command sent status (pending, success, failed)

#### FR-DN-010: UI Navigation

- **SHALL** support multiple screens/views (UI design TBD):
  - Main dashboard (current status overview)
  - Device detail views (per-device status and controls)
  - Settings/configuration view
  - Historical data view
- **SHALL** provide navigation between views via touch
- **SHALL** return to main dashboard after configurable idle timeout (default: 60 seconds)

---

### 2.4 Shared/Cross-Cutting Requirements

#### FR-SH-001: Time Synchronization

- **SHALL** synchronize time from cloud platform time API at startup
- **SHALL** support timezone configuration (default: America/Los_Angeles)
- **SHALL** use synchronized time for all scheduling and timestamping
- Continuously-running nodes (Valve Node, Display Node) **SHALL** re-synchronize time every 12 hours to correct for clock drift
- Battery-powered nodes (Pool Node) **SHALL** synchronize time on each wake cycle

*Note: ESP32 internal RTC can drift several seconds per day. Regular re-synchronization ensures scheduling accuracy for time-sensitive operations like fill windows.*

#### FR-SH-002: WiFi Configuration

- **SHALL** support WiFi network configuration (SSID and password)
- **SHALL** attempt reconnection on connection loss

#### FR-SH-003: Message Protocol

- **SHALL** use JSON message format as primary protocol (see Section 7.2, FR-MSG-001 through FR-MSG-016)
- **SHOULD** support legacy pipe-delimited format during transition period (see Section 5.4 for format specification) - *Deferred to Phase 4+*

#### FR-SH-004: Temperature Units

- **SHALL** store and transmit all temperatures in Fahrenheit
- **SHALL** convert Celsius sensor readings to Fahrenheit using: F = (C × 9/5) + 32
- **SHALL** round temperature values to one decimal place for display and transmission

---

## 3. Non-Functional Requirements

### 3.1 Reliability

#### NFR-REL-001: Watchdog Protection

- **SHALL** implement hardware watchdog timer on all nodes
- **SHALL** configure watchdog timeout per node type:
  - Pool Node: 60 seconds
  - Valve Node: 30 seconds
  - Display Node: 120 seconds
- **SHALL** perform hardware reset on watchdog timeout

#### NFR-REL-002: Sensor Retry Logic

- **SHALL** retry failed sensor reads with configurable retry count (default: 3)
- **SHALL** implement exponential backoff between retries:
  - Base delay: 100 milliseconds
  - Multiplier: 2
  - Maximum delay: 2 seconds
  - Example sequence: 100ms, 200ms, 400ms, 800ms, 1600ms, 2000ms...
- **SHALL** reinitialize sensors after repeated failures

#### NFR-REL-002a: Sensor Failure Fallback

- **SHALL** send status message with null sensor values if reads fail after all retries
- **SHALL** publish error message to events feed with error context (sensor type, retry count, last error)
- **SHALL** continue operation with available sensors when some sensors fail
- **SHALL NOT** block transmission of valid readings due to other sensor failures

*Note: Sending null values for failed sensors allows downstream systems (Display Node, HomeKit) to show "unavailable" rather than stale data. The error message provides diagnostic information for troubleshooting.*

#### NFR-REL-003: Network Resilience

- **SHALL** automatically reconnect on network disconnection
- **SHALL** implement exponential backoff for reconnection attempts:
  - Base delay: 5 seconds
  - Maximum delay: 5 minutes
  - Multiplier: 2
  - Example sequence: 5s, 10s, 20s, 40s, 80s, 160s, 300s, 300s...
- **SHALL** reset device after 10 consecutive failed reconnection attempts
- **SHALL** discard messages that cannot be sent due to disconnection
- **SHOULD** log discarded messages to serial console when available
- **SHALL** reset backoff delay after successful reconnection

*Note: Message queuing is not required. Status data becomes stale quickly, and the next update cycle will send fresh values. Local file logging may not be available on CircuitPython devices due to storage constraints.*

#### NFR-REL-004: Failure Recovery

- **SHALL** track consecutive failures and force reset after threshold (default: 5)
- **SHALL** count each operation that fails after exhausting all retries as 1 consecutive failure
- **SHALL** reset consecutive failure counter on any successful operation
- **SHALL** publish error messages to cloud before reset
- **SHALL** wait configurable delay (default: 90 seconds) before reset to allow error logging

*Note: The per-operation failure model means that 5 consecutive operations must fail completely (after all retries) before triggering a device reset. A single successful operation anywhere in the sequence resets the counter. This prevents premature resets due to transient issues while ensuring recovery from persistent failures.*

### 3.2 Performance

#### NFR-PERF-001: Response Time

- Valve Node **SHALL** begin executing commands within 1 second of message receipt (e.g., valve GPIO toggled)
- Display Node **SHALL** update screen within 1 second of receiving data

#### NFR-PERF-002: Data Freshness

- Pool Node **SHALL** transmit data at configurable interval (default: 120 seconds)
- Valve Node **SHALL** publish status updates at configurable interval (default: 60 seconds)
- Display Node **SHALL** publish local sensor data at configurable interval (default: 60 seconds)

#### NFR-PERF-003: Power Efficiency

- Pool Node **SHALL** minimize active time to preserve battery
- Pool Node **SHALL** complete measurement and transmission cycle within 30 seconds maximum
- Pool Node **SHOULD** complete typical measurement and transmission cycle within 15 seconds

*Note: The 30-second maximum allows time for sensor retries and network delays. Typical cycles should complete in under 15 seconds. With a 120-second sleep interval, this provides approximately 75% duty cycle efficiency.*

*Degraded Mode: In degraded conditions (multiple sensor retries, network reconnection delays, or bus recovery operations), cycles MAY extend to 45 seconds before watchdog intervention. This extended window accommodates recovery from transient failures while maintaining the watchdog as the ultimate safety backstop.*

### 3.3 Security

#### NFR-SEC-001: Transport Security

- **SHALL** use TLS/SSL for all cloud communications
- **SHALL** use HTTPS for REST API calls
- **SHALL** use secure MQTT (port 8883) for MQTT connections

#### NFR-SEC-002: Credential Management

- **SHALL** store credentials in separate configuration file (not committed to version control)
- **SHALL NOT** commit credentials to version control
- **SHALL** support API key authentication for cloud platform

*Installation Note: The `gateway` feed (used for commands) **SHALL** be configured to require authentication for write access. In Adafruit IO, this means ensuring the feed is not set to public-writable. See deployment documentation for setup instructions.*

*Future Consideration: Command authentication (signing/verification) is deferred to Phase 3 per NFR-SEC-003. Phase 1-2 relies on Adafruit IO's API key requirement for broker access.*

#### NFR-SEC-002a: Command Rate Limiting (Deferred)

*Note: Rate limiting is enforced by the receiving device since the cloud broker (Adafruit IO) cannot filter incoming messages.*

*Implementation Note: Rate limiting is **DEFERRED** to Phase 4+ per Kent Beck's "no just-in-case code" principle. The system uses authenticated MQTT (Adafruit IO API key required for broker access). Implement only if abuse is detected in production.*

- **SHOULD** enforce minimum interval between command executions on receiving device (if implemented):
  - `valve_start`: Minimum 60 seconds between executions
  - `valve_stop`: Minimum 10 seconds between executions
  - `set_config`: Minimum 30 seconds between executions
  - `device_reset`: Minimum 300 seconds between executions
- **SHOULD** enforce general message ingestion rate limit of 10 messages per second (if abuse detected)
- **SHALL** ignore commands that exceed rate limits (if rate limiting is implemented)
- **SHALL** log rate-limited command attempts (if rate limiting is implemented)

#### NFR-SEC-002b: Device Identity Validation

*Note: Validation is enforced by the receiving device since the cloud broker cannot filter by sender.*

- **SHALL** maintain a list of trusted device IDs in configuration
- **SHALL** ignore status messages from untrusted device IDs
- **SHALL** log messages received from unknown device IDs

#### NFR-SEC-003: Command Message Signing (Phase 3+)

*Note: This requirement is deferred to Phase 3 or later. Phase 1-2 relies on Adafruit IO API key authentication at the broker level.*

- **SHALL** implement cryptographic signing for command messages
- **SHALL** use HMAC-SHA256 as minimum signing algorithm
- **SHALL** include timestamp in signed payload to prevent replay attacks
- **SHALL** reject commands with invalid or missing signatures
- **SHALL** reject commands with timestamps older than 5 minutes
- **SHOULD** support per-device signing keys for key rotation without full system impact
- **SHALL** log all signature validation failures with sender information

*Rationale: Command authentication prevents unauthorized control of physical actuators (valves, pumps) if API credentials are compromised. This is especially important if local network command paths are added in the future.*

### 3.4 Maintainability

#### NFR-MAINT-001: Logging

- All nodes **SHALL** output diagnostic messages to serial console
- All nodes **SHALL** publish significant events to cloud platform
- Nodes with writable local storage **MAY** maintain rotating log files:
  - Maximum file size: 125KB
  - Maximum file count: 3
  - Oldest file deleted when limit exceeded

*Note: CircuitPython devices typically cannot write to local storage while running. Local file logging is only available for C++ implementations or CircuitPython devices with dedicated storage partitions.*

#### NFR-MAINT-002: Remote Configuration

- Valve Node **SHALL** support remote configuration of fill start time
- Pool Node **SHALL** support remote configuration of sleep duration and sensor settings

#### NFR-MAINT-003: Remote Reset

- Valve Node **SHALL** support remote reset command via MQTT

#### NFR-MAINT-004: Firmware Updates

OTA (Over-The-Air) firmware updates are **out of scope** for Phases 1-4. Firmware updates require physical access to flash devices via USB.

*Future Consideration: OTA updates may be added in a future phase. Requirements would include firmware signing, rollback capability, and update verification.*

---

## 4. Hardware Requirements

### 4.1 Pool Node Hardware

| Component | Specification | Interface |
|-----------|---------------|-----------|
| Microcontroller | Adafruit Feather ESP32 V2 (8MB Flash, 2MB PSRAM) | - |
| Temperature Sensor | DS18X20 | OneWire (GPIO D10) |
| Water Level Sensor | Float switch | Digital I/O (D11 in, D12 power) |
| Battery Fuel Gauge | LC709203F | I2C |
| Status LED | NeoPixel | Digital (board.NEOPIXEL) |
| Power | LiPo battery with deep sleep support | - |

*Note: ESP32 V2 recommended for deep sleep reliability and battery monitoring integration.*

### 4.2 Valve Node Hardware

| Component | Specification | Interface |
|-----------|---------------|-----------|
| Microcontroller | Adafruit Feather ESP32S3 (4MB Flash, 2MB PSRAM) | - |
| Temperature Sensor | DS18X20 | OneWire (GPIO D10) |
| Valve Control | Solenoid valve (12/24V) | Digital output (GPIO D11) |
| Status LED | NeoPixel | Digital (board.NEOPIXEL) |
| Activity LED | Board LED | Digital (board.LED) |
| Power | AC/DC adapter | - |

### 4.3 Display Node Hardware

| Component | Specification | Interface |
|-----------|---------------|-----------|
| Microcontroller | Adafruit Feather ESP32-S2 (4MB Flash, 2MB PSRAM) | - |
| Display | ILI9341 2.4" TFT (320x240, 16-bit color) | SPI (CS: D9, DC: D10) |
| Touchscreen | STMPE610 (resistive touch input) | SPI (CS: D6) |
| Temp/Humidity Sensor | AHTx0 | I2C |
| Status LED | Board LED | Digital (board.LED) |
| Power | AC/DC adapter (5V USB) | - |

*Note: ESP32-S2 recommended for CircuitPython display support and adequate memory for UI rendering.*

**Note:** The touchscreen enables interactive control. Calibration data is required for accurate touch mapping. The display serves as the primary user interface for sending commands to other devices in the system.

---

## 5. Communication Protocol Specifications

### 5.1 Cloud Platform

- **Provider:** Adafruit IO
- **MQTT Broker:** io.adafruit.com (port 8883, TLS)
- **REST API:** `https://io.adafruit.com/api/v2/{username}/`

**MQTT Quality of Service (QoS):**

- **SHALL** use QoS 0 (at most once) for status messages - status data becomes stale quickly; retransmission is unnecessary
- **SHOULD** use QoS 1 (at least once) for command messages - ensures commands are delivered but allows duplicates
- **SHALL NOT** use QoS 2 (exactly once) - the overhead is not justified for this application

*Note: Adafruit IO supports QoS 0 and QoS 1. QoS 2 is not supported by the broker.*

*Future Consideration: A cloud backend abstraction layer could be added in a future phase to support alternative providers (AWS IoT, Azure IoT Hub, etc.). For Phase 1-4, the system uses Adafruit IO directly.*

### 5.2 MQTT Feeds (Topics)

Feed names **SHALL** be configurable and support environment-based prefixing per NFR-ENV-002 (see Section 7.5).

#### Logical Feed Names

The following logical feed names are used in code. Actual feed names are constructed by applying the environment prefix from configuration.

| Logical Name | Publisher | Subscriber | Purpose |
|--------------|-----------|------------|---------|
| `gateway` | Pool Node, Valve Node | Valve Node, Display Node | Main data exchange |
| `valvestarttime` | Cloud/User | Valve Node | Configure fill start time |
| `poolvalveruntime` | Valve Node | Cloud | Report fill duration |
| `outsidetemp` | Valve Node | Cloud | Report outside temperature |
| `poolnodebattery` | Pool Node | Cloud | Report battery voltage |
| `pooltemp` | Pool Node | Cloud | Report pool temperature |
| `insidetemp` | Display Node | Cloud | Report inside temperature |
| `config` | Cloud | Pool Node | Remote configuration |
| `events` | All Nodes | Cloud | Status and error events |

#### Feed Name Resolution

Actual feed names are constructed from configuration:

```text
{feedPrefix}{logicalName}

Examples:
  prod:    gateway, pooltemp, events
  nonprod: nonprod-gateway, nonprod-pooltemp, nonprod-events
  dev:     dev-gateway, dev-pooltemp, dev-events
```

#### Feed Configuration Example

```json
{
  "feeds": {
    "gateway": "gateway",
    "pooltemp": "pooltemp",
    "valvestarttime": "valvestarttime",
    "events": "events"
  }
}
```

*Note: Feed names can be customized in configuration to support different Adafruit IO account structures or alternative cloud backends.*

### 5.3 REST API Endpoints

These endpoints are provided by the **Adafruit IO REST API**. Full URLs are constructed from configuration.

**Base URL:** `https://io.adafruit.com/api/v2/{username}/`

| Endpoint | Method | Node | Purpose |
|----------|--------|------|---------|
| `/integrations/time/struct` | GET | All | Time synchronization |
| `/feeds/{feed}/data` | POST | Pool Node | Publish sensor data |
| `/feeds/{feed}/data` | GET | All | Retrieve latest feed value |
| `/feeds/{feed}/data/chart` | GET | Display Node | Fetch historical data |

**Full URL Examples:**

```text
Time sync:    https://io.adafruit.com/api/v2/{username}/integrations/time/struct?tz={timezone}
Publish:      https://io.adafruit.com/api/v2/{username}/feeds/{feed}/data
Historical:   https://io.adafruit.com/api/v2/{username}/feeds/{feed}/data/chart?hours=24&resolution=6
```

*Note: The `resolution` parameter specifies the data point interval in minutes (e.g., `resolution=6` returns one data point every 6 minutes).*

**Authentication:** API key passed via `X-AIO-Key` header or `x-aio-key` query parameter.

### 5.4 Legacy Message Format Specification (Deprecated)

> **DEPRECATED:** This section documents the legacy pipe-delimited message format used by the original system. New implementations **SHALL** use the JSON message format defined in Section 7.2 (FR-MSG-001 through FR-MSG-010). Legacy format support is maintained only for backward compatibility during migration.

The legacy format uses pipe-delimited fields: `TYPE|SIZE|FIELD1|FIELD2|...`

#### Type 0: Pool Sensor Data

```text
0|16|{floatSwitch}|{poolTemp}|{batteryVoltage}|99
```

#### Type 1: Valve Status Update

```text
1|24|{outsideTemp}|{valveActive}|{secsRemaining}|{nextFillEpoch}|{runDuration}
```

#### Type 3: Fill Start Event

```text
3|16|{startTime}|{endTime}|{duration}
```

#### Type 4: Fill Stop Event

```text
4|12|{stopTime}|{duration}
```

#### Type 6: Manual Start Command

```text
6
```

#### Type 99: Reset Command

```text
99
```

*For field definitions, see the original project documentation. For new implementations, use JSON format per Section 7.2 (FR-MSG-001 through FR-MSG-016).*

### 5.5 Adafruit IO Rate Limits

| Plan | Rate Limit | Feeds | Dashboards | Storage |
|------|------------|-------|------------|---------|
| Free | 30 data points/minute | 10 | 5 | 30 days |
| Plus ($99/year) | 60 data points/minute | Unlimited | Unlimited | 60 days |

- **SHALL** implement client-side rate tracking to avoid exceeding limits
- **SHALL** subscribe to `{username}/throttle` topic for throttle notifications
- **SHOULD** implement backoff when throttle notification received
- **SHALL** log rate limit events for diagnostics

*Note: Boosts available for Plus tier: +10 data points/minute for $2/month. With default intervals (Pool Node: 120s, Valve Node: 60s, Display Node: 60s), the system generates approximately 3 data points/minute, well within Free tier limits.*

---

## 6. Configuration Requirements

### 6.1 Secrets Configuration

All nodes require sensitive configuration (WiFi credentials, API keys) that must not be committed to version control.

#### Required Secrets

| Secret | Description |
|--------|-------------|
| `CIRCUITPY_WIFI_SSID` | WiFi network name (CircuitPython - enables auto-connect) |
| `CIRCUITPY_WIFI_PASSWORD` | WiFi password (CircuitPython) |
| `WIFI_SSID` | WiFi network name (C++ implementations) |
| `WIFI_PASSWORD` | WiFi password (C++ implementations) |
| `AIO_USERNAME` | Adafruit IO username |
| `AIO_KEY_PROD` | Adafruit IO API key for production environment |
| `AIO_KEY_NONPROD` | Adafruit IO API key for non-production environment |
| `TIMEZONE` | Timezone string (e.g., "America/Los_Angeles") |
| `ENVIRONMENT` | Deployment environment ("prod" or "nonprod") |

*Note: CircuitPython 8.0+ uses the `CIRCUITPY_` prefix to enable automatic WiFi connection on boot. C++ implementations use the non-prefixed names.*

*Security Note: Separate API keys per environment are required (see NFR-ENV-008). This ensures credential compromise in one environment does not affect the other.*

#### Credential Storage Security Warnings

**Plaintext Storage Risk:** Credentials in `settings.toml` and `secrets.h` are stored in plaintext. Physical access to any device allows credential extraction.

**CircuitPython USB Exposure:** CircuitPython devices mount as USB mass storage (CIRCUITPY drive) when connected via USB. Anyone with physical USB access can read `settings.toml` and extract credentials. Mitigations:

- Deploy devices in physically secured enclosures
- Use `boot.py` to disable USB mass storage in production (see CircuitPython documentation)
- Consider disabling USB after provisioning where hardware supports it

**C++ Recommendations:**

- Use ESP32 NVS encrypted storage instead of compiled-in values
- Implement a secure provisioning mode (e.g., BLE or AP mode for initial setup)
- Consider ESP32 secure boot and flash encryption for production deployments

**General Recommendations:**

- Document and follow a secure device provisioning procedure
- Rotate API keys periodically and after any suspected compromise
- Monitor Adafruit IO for unexpected device activity

**Network Isolation (Deployment Note):**

Devices **SHOULD** be deployed on an isolated network segment (IoT VLAN) separate from general-purpose devices. This provides defense-in-depth by:

- Limiting lateral movement if a device is compromised
- Reducing attack surface from other network devices
- Enabling network-level monitoring and firewall rules for IoT traffic
- Isolating devices with known firmware vulnerabilities

*Note: Network segmentation is a deployment recommendation, not a functional requirement. The system operates correctly on flat networks but benefits from isolation when available.*

#### CircuitPython: settings.toml (Recommended)

```toml
# settings.toml - CircuitPython 8.0+
CIRCUITPY_WIFI_SSID = "NetworkName"
CIRCUITPY_WIFI_PASSWORD = "password"
AIO_USERNAME = "adafruit_io_username"
AIO_KEY_PROD = "aio_prod_api_key"
AIO_KEY_NONPROD = "aio_nonprod_api_key"
TIMEZONE = "America/Los_Angeles"
ENVIRONMENT = "nonprod"
```

Access via `os.getenv("AIO_USERNAME")`

#### C++ (Arduino/ESP-IDF): Options

##### Option A: secrets.h header file (credentials only)

```cpp
// secrets.h - add to .gitignore
// Credentials only - environment selection should use NVS or build flags
#define WIFI_SSID "NetworkName"
#define WIFI_PASSWORD "password"
#define AIO_USERNAME "adafruit_io_username"
#define AIO_KEY_PROD "aio_prod_api_key"
#define AIO_KEY_NONPROD "aio_nonprod_api_key"
```

##### Option B: ESP32 NVS (Non-Volatile Storage) (Recommended)

- Store secrets and environment in NVS partition
- Provision via serial command or setup mode
- Allows runtime configuration without recompilation
- More secure than compiled-in values

##### Option C: PlatformIO build flags (environment selection)

```ini
; platformio.ini
; Environment set via build flag - use separate build targets for prod/nonprod
build_flags =
    -DWIFI_SSID=\"${sysenv.WIFI_SSID}\"
    -DWIFI_PASSWORD=\"${sysenv.WIFI_PASSWORD}\"
    -DENVIRONMENT=\"${sysenv.ENVIRONMENT}\"
```

*Note: For C++ implementations, environment selection via NVS (Option B) is preferred as it allows changing environments without recompilation.*

### 6.2 Pool Node Configuration (config.json)

```json
{
    "pool": {
        "sleepDuration": 120,
        "floatSwitchReads": 30
    }
}
```

### 6.3 Valve Node Configuration

| Parameter | Default | Source | Description |
|-----------|---------|--------|-------------|
| maxFillDurationMinutes | 9 | Config | Maximum fill duration |
| fillWindowHours | 2 | Config | Fill window duration |
| valveStartTime | Remote | MQTT feed | Time to begin fill window (HH:MM) |
| statusUpdateInterval | 60 | Config | Seconds between status updates |
| poolDataStalenessMultiplier | 2 | Config | Multiplier of pool node interval for staleness threshold |

### 6.4 Display Node Configuration

| Parameter                   | Default | Source | Description                                          |
| --------------------------- | ------- | ------ | ---------------------------------------------------- |
| chartHistoryHours           | 24      | Config | Hours of history to display                          |
| chartRefreshInterval        | 300     | Config | Seconds between historical data fetches              |
| staleDataIndicatorThreshold | 1800    | Config | Seconds before data is considered stale (30 minutes) |
| localSensorPublishInterval  | 60      | Config | Seconds between publishing local temp to cloud       |

*Note: Chart width is determined by display hardware (ILI9341: 320x240, portrait orientation = 240 pixels wide). Data point interval is calculated as `(chartHistoryHours × 60) / chartWidthPixels`. With 24 hours and 240 pixels: (24 × 60) / 240 = 6 minutes per data point.*

---

## 7. Rearchitecture Requirements

This section defines requirements for the system rearchitecture based on analysis of the original codebase, identified issues, and future extensibility needs.

### 7.1 Pool Node Reliability Requirements

Analysis of the original Pool Node identified multiple potential hang sources that must be addressed:

#### NFR-REL-005: Blocking Operation Timeouts

- **SHALL** implement timeouts on all blocking operations:
  - WiFi connection: Maximum 15 seconds per network attempt
  - HTTP requests: Maximum 10 seconds
  - I2C bus operations: Maximum 5 seconds
  - OneWire bus operations: Maximum 5 seconds
- **SHALL** feed watchdog timer before and after all blocking operations
- **SHALL NOT** allow any single operation to exceed 50% of watchdog timeout

*Note: CircuitPython implementations cannot enforce WiFi connection timeouts due to library limitations (`wifi.radio.connect()` has no timeout parameter). CircuitPython nodes (e.g., Display Node) rely on the watchdog timer (NFR-REL-001) for recovery from connection hangs. C++ implementations can use ESP-IDF WiFi APIs which support timeouts. See "Implementation Language Considerations" below for more detail.*

#### NFR-REL-006: Bus Recovery Mechanisms

- **SHALL** implement I2C bus recovery with automatic deinit/reinit on failure
- **SHALL** implement OneWire bus recovery with GPIO pin reset capability
- **SHALL** release all bus resources before deep sleep
- **SHALL** log all bus recovery attempts for diagnostics

**Bus Recovery Procedure:**

1. **Trigger**: Bus recovery is triggered after 3 consecutive failed operations on the same bus
2. **I2C Recovery**: Deinitialize bus, wait 100ms, toggle SCL line 9 times if stuck, reinitialize bus
3. **OneWire Recovery**: Deinitialize bus, wait 100ms, toggle data pin low for 500μs, reinitialize bus
4. **Post-Recovery**: Wait 200ms before next operation attempt
5. **Escalation**: If recovery fails 3 times consecutively, increment failure counter per NFR-REL-009

#### NFR-REL-007: Socket Resource Management

- **SHALL** explicitly close all HTTP response objects after use
- **SHALL** implement socket pool cleanup on repeated failures
- **SHALL** limit maximum concurrent socket connections
- **SHALL** reset socket pool before deep sleep

#### NFR-REL-008: Watchdog Coverage

- **SHALL** feed watchdog at intervals no greater than 25% of timeout period (see NFR-REL-001 for per-node timeouts)
- **SHALL** feed watchdog within sensor read retry loops
- **SHALL** feed watchdog within network operation loops
- **SHALL NOT** have any code path that can exceed watchdog timeout

*Note: With Pool Node timeout of 60 seconds (NFR-REL-001), watchdog must be fed at least every 15 seconds. This accommodates the maximum WiFi connection timeout (15 seconds) specified in NFR-REL-005.*

#### NFR-REL-009: Error Handling

- **SHALL** replace all bare `except:` clauses with specific exception types
- **SHALL** log all caught exceptions with context information
- **SHALL** implement graduated failure response (retry → recover → reset)
- **SHALL** track failure counts by category (network, sensor, bus)

#### NFR-REL-010: Resource Cleanup Order

- **SHALL** deinitialize sensors before deinitializing buses
- **SHALL** close network connections before entering deep sleep
- **SHALL** implement cleanup in finally blocks to guarantee execution

#### Implementation Language Considerations

When architecting the solution, both **CircuitPython** and **C++ (Arduino/ESP-IDF)** should be evaluated for each node type based on reliability requirements.

**CircuitPython Strengths:**

- Rapid development and iteration (no compile step)
- Easier debugging (REPL, readable stack traces)
- Excellent readability and maintainability
- Strong Adafruit library ecosystem

**CircuitPython Limitations for Reliability:**

- No true multitasking - cannot implement hard timeouts on blocking operations
- `wifi.radio.connect()` has no timeout parameter (can block indefinitely)
- Limited low-level bus recovery (I2C, OneWire)
- Higher memory overhead reduces headroom for complex error handling
- Garbage collection pauses can affect timing-sensitive operations

**C++ (Arduino/ESP-IDF) Strengths:**

- FreeRTOS tasks enable true concurrent timeout mechanisms
- Direct hardware register access for bus recovery
- Native ESP-IDF WiFi stack with full timeout control
- Lower memory footprint, faster execution
- Built-in OTA update support
- More predictable timing behavior

**C++ Limitations:**

- Longer development cycle (compile, flash, test)
- More complex debugging
- Steeper learning curve for maintenance

**Recommendations by Node Type:**

| Node | Recommendation | Rationale |
|------|----------------|-----------|
| Pool Node | **Prefer C++** | Battery-powered, reliability-critical, timeout control essential |
| Valve Node | Either | AC-powered, can recover from hangs, but controls safety-critical hardware |
| Display Node | **Prefer CircuitPython** | UI-focused, rapid iteration valuable, hangs less critical |
| Pump Node | Either | Depends on communication protocol complexity (RS-485 timing) |

**Architecture Principle:** The JSON message format enables mixed-language implementations. Nodes communicate via standardized messages regardless of implementation language. Each node type can be implemented in the language best suited to its reliability and development requirements.

---

### 7.2 JSON Message Format Requirements

The rearchitecture will migrate from pipe-delimited messages to JSON for improved extensibility and debugging.

#### FR-MSG-001: JSON Message Structure

- **SHALL** use JSON as the message payload format
- **SHALL** include standard envelope fields in all messages:

  ```json
  {
    "version": 2,
    "type": "pool_status",
    "deviceId": "pool-node-001",
    "timestamp": "2026-01-20T14:30:00-08:00",
    "payload": { "...": "message-specific fields" }
  }
  ```

#### FR-MSG-002: Message Envelope Fields

- **version**: Protocol version number (integer)
- **type**: Message type identifier (string, lowercase with underscores)
- **deviceId**: Unique identifier for sending device (string)
  - **SHALL** use format: `{device-type}-{identifier}` (e.g., `pool-node-001`, `valve-node-001`, `display-node-001`)
  - **SHALL** use lowercase letters, numbers, and hyphens only
  - **SHALL** be 1-64 characters in length
- **timestamp**: ISO 8601 formatted date/time when message was created (string)
- **payload**: Message-specific data (object)

*Note: Message ordering and deduplication are handled by the MQTT broker (Adafruit IO). No application-level sequence numbers are required.*

*Note: All date/time values use ISO 8601 format in local time with timezone offset (e.g., "2026-01-20T14:30:00-08:00"). Local time is preferred for human readability; the offset preserves timezone context.*

#### FR-MSG-003: Message Types

The following message types **SHALL** be supported:

| Type String      | Direction      | Purpose                                  | Payload Definition |
| ---------------- | -------------- | ---------------------------------------- | ------------------ |
| `pool_status`    | Pool→Cloud     | Sensor readings from pool node           | FR-MSG-004         |
| `valve_status`   | Valve→Cloud    | Current state of valve controller        | FR-MSG-005         |
| `display_status` | Display→Cloud  | Local sensor readings from display node  | FR-MSG-006         |
| `fill_start`     | Valve→Cloud    | Fill operation started                   | FR-MSG-007         |
| `fill_stop`      | Valve→Cloud    | Fill operation stopped                   | FR-MSG-008         |
| `command`          | Cloud→Device   | Remote command to device                 | FR-MSG-009         |
| `command_response` | Device→Cloud   | Command execution result                 | FR-MSG-013         |
| `heartbeat`        | Device→Cloud   | Device alive signal                      | FR-MSG-010         |
| `error`            | Device→Cloud   | Error report                             | FR-MSG-011         |
| `config_update`    | Cloud→Device   | Configuration update                     | FR-MSG-012         |

*Note: Pump-related message types (`pump_status`, `pump_speed_change`) will be added when pump implementation is defined (see FR-EXT-005).*

#### FR-MSG-004: Pool Status Payload

```json
{
  "waterLevel": {
    "floatSwitch": true,
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
```

#### FR-MSG-005: Valve Status Payload

```json
{
  "valve": {
    "state": "closed",
    "isFilling": false,
    "currentFillDuration": 0,
    "maxFillDuration": 540
  },
  "schedule": {
    "enabled": true,
    "startTime": "09:00",
    "windowHours": 2,
    "nextScheduledFill": "2026-01-20T09:00:00-08:00"
  },
  "temperature": {
    "value": 72.0,
    "unit": "fahrenheit"
  }
}
```

#### FR-MSG-006: Display Status Payload

```json
{
  "localTemperature": {
    "value": 72.5,
    "unit": "fahrenheit"
  },
  "localHumidity": {
    "value": 45,
    "unit": "percent"
  }
}
```

#### FR-MSG-007: Fill Start Payload

```json
{
  "fillStartTime": "2026-01-20T09:00:00-08:00",
  "scheduledEndTime": "2026-01-20T09:09:00-08:00",
  "maxDuration": 540,
  "trigger": "scheduled"
}
```

- **fillStartTime**: ISO 8601 timestamp when fill started
- **scheduledEndTime**: Expected end time based on max duration
- **maxDuration**: Maximum fill duration in seconds
- **trigger**: What initiated the fill - `"scheduled"`, `"manual"`, or `"low_water"`

#### FR-MSG-008: Fill Stop Payload

```json
{
  "fillStopTime": "2026-01-20T09:05:30-08:00",
  "actualDuration": 330,
  "reason": "water_full"
}
```

- **fillStopTime**: ISO 8601 timestamp when fill stopped
- **actualDuration**: Actual fill duration in seconds
- **reason**: Why fill stopped - `"water_full"`, `"max_duration"`, `"manual"`, `"error"`, or `"window_closed"`

#### FR-MSG-009: Command Payload

```json
{
  "command": "valve_start",
  "parameters": {
    "maxDuration": 540
  },
  "source": "display-node-001"
}
```

- **command**: Command to execute (required)
- **parameters**: Command-specific parameters (optional, depends on command)
- **source**: Device ID of the command sender (optional, for audit/debugging)

*Note: For command/response correlation, use the `timestamp` field from the message envelope (FR-MSG-002). The receiving device echoes this timestamp in the `command_response` message (FR-MSG-013).*

*Assumption: The current design assumes a single instance of each command-receiving device type (e.g., one Valve Node). Status-reporting nodes (Pool Node, Display Node) can have multiple instances, each with a unique `deviceId` in their status messages. Future consideration: When multiple command-receiving devices of the same type are needed, implement device-specific command feeds or add device routing to the command schema.*

Supported commands:

| Command       | Target     | Parameters               | Description            |
| ------------- | ---------- | ------------------------ | ---------------------- |
| `valve_start` | Valve Node | `maxDuration` (optional) | Start fill operation   |
| `valve_stop`  | Valve Node | (none)                   | Stop fill operation    |
| `device_reset`| Any        | (none)                   | Restart the device     |
| `set_config`  | Any        | config key-value pairs   | Update configuration   |

**set_config Allowed Parameters:**

The `set_config` command **SHALL** only accept the following parameters:

| Parameter | Type | Description |
|-----------|------|-------------|
| `valveStartTime` | string (HH:MM) | Fill window start time |
| `reportInterval` | integer (seconds) | Status reporting interval |
| `floatSwitchReads` | integer | Number of float switch reads for consensus |
| `logLevel` | string | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `debugLogging` | boolean | Enable/disable debug logging |

The following parameters **SHALL NOT** be remotely configurable (require device reflash):

- `deviceId` - Device identity
- `environment` - Deployment environment
- `hardwareEnabled` - Hardware actuation enable
- GPIO pin assignments
- I2C/SPI addresses
- API keys and credentials

*Rationale: Restricting remote configuration to operational parameters prevents accidental or malicious misconfiguration of security-critical settings.*

#### FR-MSG-010: Heartbeat Payload

```json
{
  "uptime": 3600,
  "freeMemory": 45000,
  "errorCount": 0,
  "lastError": null
}
```

- **uptime**: Seconds since device boot
- **freeMemory**: Available memory in bytes (if available)
- **errorCount**: Number of errors since boot
- **lastError**: Description of last error, or null if none

**Null Handling:** Fields with null values SHOULD be explicitly included rather than omitted. This ensures schema compliance and provides explicit indication of "no value" vs "unknown/missing."

#### FR-MSG-011: Error Payload

```json
{
  "errorCode": "SENSOR_READ_FAILURE",
  "errorMessage": "Failed to read temperature sensor after 3 retries",
  "severity": "warning",
  "context": {
    "sensor": "DS18X20",
    "retryCount": 3
  }
}
```

- **errorCode**: Machine-readable error identifier (see standard codes below)
- **errorMessage**: Human-readable description
- **severity**: `"debug"`, `"info"`, `"warning"`, `"error"`, or `"critical"`
- **context**: Additional diagnostic information (optional)

**Standard Error Codes:**

| Category | Code                        | Description                          |
| -------- | --------------------------- | ------------------------------------ |
| SENSOR   | `SENSOR_READ_FAILURE`       | Failed to read sensor after retries  |
| SENSOR   | `SENSOR_INIT_FAILURE`       | Failed to initialize sensor          |
| SENSOR   | `SENSOR_OUT_OF_RANGE`       | Reading outside valid range          |
| NETWORK  | `NETWORK_CONNECTION_FAILED` | Failed to connect to WiFi or broker  |
| NETWORK  | `NETWORK_TIMEOUT`           | Network operation timed out          |
| NETWORK  | `NETWORK_AUTH_FAILURE`      | Authentication failed                |
| BUS      | `BUS_I2C_FAILURE`           | I2C bus error                        |
| BUS      | `BUS_ONEWIRE_FAILURE`       | OneWire bus error                    |
| BUS      | `BUS_SPI_FAILURE`           | SPI bus error                        |
| CONFIG   | `CONFIG_INVALID_VALUE`      | Configuration value invalid          |
| CONFIG   | `CONFIG_MISSING_REQUIRED`   | Required configuration missing       |
| CONFIG   | `CONFIG_SCHEMA_VIOLATION`   | Configuration fails schema validation|
| SYSTEM   | `SYSTEM_MEMORY_LOW`         | Available memory critically low      |
| SYSTEM   | `SYSTEM_WATCHDOG_RESET`     | Device reset by watchdog             |
| SYSTEM   | `SYSTEM_UNEXPECTED_RESET`   | Device reset unexpectedly            |
| VALVE    | `VALVE_SAFETY_INTERLOCK`    | Fill prevented by safety interlock   |
| VALVE    | `VALVE_MAX_DURATION`        | Fill stopped due to max duration     |
| VALVE    | `VALVE_ALREADY_ACTIVE`      | Fill rejected, fill already active   |
| VALVE    | `VALVE_DATA_STALE`          | Fill prevented due to stale data     |
| VALVE    | `VALVE_HARDWARE_FAILURE`    | Valve hardware failure detected      |

#### FR-MSG-012: Config Update Payload

```json
{
  "configKey": "valveStartTime",
  "configValue": "10:00",
  "source": "cloud"
}
```

- **configKey**: Configuration parameter being updated
- **configValue**: New value for the parameter
- **source**: Origin of update - `"cloud"`, `"local"`, or `"default"`

#### FR-MSG-013: Command Response Payload

```json
{
  "commandTimestamp": "2026-01-20T09:00:00-08:00",
  "command": "valve_start",
  "status": "success",
  "errorCode": null,
  "errorMessage": null
}
```

- **commandTimestamp**: The `timestamp` from the original command message envelope (required)
- **command**: The command that was executed (required)
- **status**: Execution result - `"success"`, `"failed"`, or `"rejected"` (required)
- **errorCode**: Machine-readable error code if status is not success (see FR-MSG-011 for codes)
- **errorMessage**: Human-readable error description if status is not success

*Note: Devices **SHALL** publish a command_response after processing any command. The `commandTimestamp` enables the sender to correlate the response with the original command.*

#### FR-MSG-014: Message Validation

Message validation is critical for system reliability and security.

**Size Validation:**

- **SHALL** reject messages exceeding 4KB in size
- **SHALL** log rejected oversized messages with actual size

**Schema Validation:**

- **SHALL** validate all incoming messages against defined JSON schema
- **SHALL** define schemas for each message type (pool_status, valve_status, etc.)
- **SHALL** store schemas in configuration or code for each node type
- **SHOULD** version schemas to support evolution
- **MAY** simplify schema validation in production for resource-constrained nodes while retaining full validation in development

*Note: Full schema validation provides better error messages and catches edge cases during development. Production nodes may use simplified validation (required fields, basic types) to reduce memory usage and processing time. The `debugLogging` configuration flag can control validation depth.*

**Required Field Validation:**

- **SHALL** reject messages with missing required envelope fields (version, type, deviceId, timestamp)
- **SHALL** reject messages with missing required payload fields per message type
- **SHALL** distinguish between required and optional fields in schema definitions

**Type and Format Validation:**

- **SHALL** validate field data types (string, number, boolean, object, array)
- **SHALL** validate date/time fields conform to ISO 8601 format
- **SHALL** validate enum fields contain allowed values (e.g., valve.state: "open"|"closed")
- **SHALL** validate numeric fields are within acceptable ranges where defined

**Timestamp Freshness Validation (Replay Protection):**

- **SHALL** ignore command messages with timestamps older than 5 minutes
- **SHOULD** ignore status messages with timestamps older than 15 minutes
- **SHALL** log ignored stale messages with timestamp age
- **SHALL** allow configurable freshness window per message type

*Note: Timestamp freshness validation prevents replay attacks where captured messages are re-sent later. The 5-minute window for commands provides margin for clock drift while limiting the attack window. Status messages have a longer window since they are informational rather than actionable.*

**Handling Invalid Messages:**

- **SHALL** log validation failures with full message content and specific error
- **SHALL** increment error counter for observability
- **SHALL NOT** crash or hang on malformed messages
- **SHOULD** publish validation errors to cloud for remote diagnostics
- **MAY** implement rate limiting if excessive invalid messages detected

**Unknown Field Handling:**

- **SHOULD** ignore unknown fields in payload (forward compatibility)
- **SHALL** log warning when unknown fields encountered

#### FR-MSG-015: Backward Compatibility (Deferred)

*Implementation Note: Legacy message support is **DEFERRED** to Phase 4+ per Kent Beck's "no just-in-case code" principle. The rearchitecture is a clean break - legacy nodes can continue using the existing system until migrated. Implement only if parallel operation with legacy nodes proves necessary.*

- **SHOULD** support legacy pipe-delimited format during transition period (if migration requires coexistence)
- **SHALL** detect message format by first character ('{' = JSON, digit = legacy) (if legacy support implemented)
- **MAY** remove legacy support in future version

#### FR-MSG-016: Message Version Handling

- **SHALL** declare an explicit list of supported message versions in configuration
- **SHALL** process messages with versions in the supported list
- **SHALL** reject messages with unsupported versions and log error including:
  - Received version number
  - Device ID of sender
  - List of supported versions
- **SHALL NOT** attempt to parse payloads from unsupported versions

*Note: Version 2 is the initial JSON message format. There is no version 1 - the predecessor is the legacy pipe-delimited format (see FR-MSG-015 and Section 5.4). When future versions (3, 4, etc.) are introduced, implementations SHOULD support the current version and at least one prior version during transitions. Explicit version support prevents infinite backward/forward compatibility maintenance burden.*

---

### 7.3 Device Extensibility Requirements

The architecture shall support adding new device types without modifying core system code.

#### FR-EXT-001: Device Integration Architecture

- **SHALL** use the JSON message protocol (Section 7.2) as the integration contract between devices
- **SHALL** enable new device types by implementing the message protocol without modifying core system code
- **SHALL** support mixed-language implementations (C++, CircuitPython) communicating via standardized messages
- **SHALL** allow each device type to manage its own lifecycle appropriate to its power and operational mode

*Note: The original requirement specified a base `Device` class with lifecycle methods (`initialize`, `read_sensors`, `process_command`, `get_status`, `cleanup`). This was revised because the Pool Node's deep sleep lifecycle fundamentally doesn't fit this pattern—it has no `process_command()` since it's asleep 99% of the time. The message protocol approach provides equivalent extensibility while accommodating diverse device lifecycles.*

#### FR-EXT-002: Device Registration

- **SHALL** support device registration via configuration file
- **SHALL** assign unique device IDs automatically or via configuration
- **MAY** support dynamic device discovery (Phase 3+)

*Note: Initial implementation uses static configuration. Dynamic device discovery (mDNS, cloud registry, etc.) is deferred to Phase 3+ when multi-device scenarios become relevant.*

#### FR-EXT-003: Device Configuration Schema

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

*Note: Pump node configuration will be added when pump implementation details are defined (see FR-EXT-005).*

#### FR-EXT-004: Supported Device Types

Initial device types to support:

- `pool_sensor` - Temperature, water level, battery monitoring
- `valve_controller` - Fill valve control with scheduling
- `display` - Status display dashboard with touchscreen control interface
- `variable_speed_pump` - Variable speed pump control (NEW)

#### FR-EXT-004a: Display Node Command Dispatch

- **SHALL** support sending commands to any registered device via touch UI
- **SHALL** discover available commands from device capability declarations
- **SHALL** dynamically generate UI controls based on device capabilities
- **SHALL** display command sent status to user (pending, sent, failed)

#### FR-EXT-005: Variable Speed Pump Requirements (Phase 3+)

> **Note:** Implementation deferred to Phase 3. Communication method (serial/RS-485, web API, proprietary protocol, etc.) depends on pump model selection.

**Functional Requirements (when implemented):**

- **SHALL** support speed control (RPM or percentage)
- **SHALL** support programmable schedules (multiple daily programs)
- **SHOULD** read pump diagnostics (power consumption, motor temp, runtime) if supported by pump
- **SHALL** support manual override commands
- **SHOULD** integrate with fill valve (reduce speed during fill, increase after)

**Implementation TBD:**

- Communication interface (RS-485, RS-232, WiFi/HTTP API, proprietary)
- Protocol details (Modbus, proprietary, REST, etc.)
- Specific pump model and manufacturer
- Available diagnostic data points

#### FR-EXT-006: Device Capability Declaration (Phase 3+)

*Note: This requirement is deferred to Phase 3 when pump device implementation begins. The capability declaration schema will be finalized based on pump communication protocol requirements.*

- **SHALL** support devices declaring their capabilities
- **SHALL** support capability-based feature discovery
- **SHALL** gracefully handle devices with limited capabilities
- **SHALL** include command parameter schemas for Display Node UI generation
- **SHALL** include sensor metadata (units, ranges) for proper display formatting

Example capability declaration:

```json
{
  "deviceType": "variable_speed_pump",
  "capabilities": {
    "speedControl": true,
    "scheduling": true,
    "powerMonitoring": true,
    "diagnostics": true,
    "remoteControl": true
  },
  "commands": ["set_speed", "run_program", "stop", "get_status"],
  "sensors": ["speed", "power", "motor_temp", "runtime"]
}
```

#### FR-EXT-007: Inter-Device Communication

*Note: This requirement is deferred to Phase 3+ when pump integration is implemented. The scope below defines the target behavior.*

- **SHALL** route all inter-device messages through the `gateway` feed
- **SHALL** include `target` field in command messages to specify intended recipient device
- **SHOULD** support event-based coordination where one device's status triggers actions in another:
  - Example: Valve Node reduces pump speed when fill starts (requires pump integration)
  - Example: Display Node updates immediately when valve status changes

**Priority/Conflict Resolution (Phase 3+):**

When multiple commands conflict (e.g., manual valve start while scheduled fill is pending):

- **SHALL** process commands in timestamp order
- **SHALL** reject conflicting commands with `VALVE_ALREADY_ACTIVE` error
- **SHOULD** log rejected commands with reason

*Testability Note: Inter-device communication is verified by:*

1. *Sending a command message with `target` field and confirming correct device processes it*
2. *Verifying command_response is published for all commands*
3. *Simulating conflicting commands and verifying rejection behavior*

---

### 7.4 Apple HomeKit Integration Requirements

The system shall support integration with Apple HomeKit for display in the Home app and Siri voice control.

#### FR-HK-001: HomeKit Bridge Architecture

- **SHALL** support HomeKit integration via a bridge component
- **MAY** implement bridge as:
  - Homebridge plugin (Node.js-based, runs on separate device)
  - Home Assistant integration
  - Custom HAP (HomeKit Accessory Protocol) server
- **SHALL** communicate with Poolio system via cloud backend or local network

#### FR-HK-002: Exposed Accessories

The following Poolio devices/sensors **SHALL** be exposed as HomeKit accessories:

| Poolio Component | HomeKit Service Type | Characteristics |
| ------------------ | --------------------- | ----------------- |
| Pool Temperature | Temperature Sensor | Current Temperature |
| Outside Temperature | Temperature Sensor | Current Temperature |
| Local Temp/Humidity | Temperature Sensor + Humidity Sensor | Current Temperature, Current Relative Humidity |
| Water Level | Contact Sensor or Leak Sensor | Contact State (full/needs water) |
| Fill Valve | Valve or Switch | Active, In Use, Valve Type |
| Variable Speed Pump | Fan (speed control) or Switch | Active, Rotation Speed |
| Pool Node Battery | Battery Service | Battery Level, Status Low Battery |

> **Note:** Specific HomeKit service type choices (e.g., Contact Sensor vs Leak Sensor for water level) are preliminary and will be finalized during HomeKit implementation phase based on Home app UX testing.

#### FR-HK-003: HomeKit Commands

- **SHALL** support controlling fill valve from Home app (start/stop)
- **SHALL** support controlling pump from Home app (on/off, speed adjustment)
- **SHALL** support HomeKit automations (e.g., scenes, schedules)
- **SHALL** support Siri voice commands for supported actions

#### FR-HK-004: Data Synchronization

- **SHALL** update HomeKit accessory state when Poolio state changes
- **SHALL** propagate HomeKit commands to appropriate Poolio devices
- **SHALL** handle offline scenarios gracefully (show "No Response" in Home app)
- **SHOULD** minimize latency between state changes and HomeKit updates

#### FR-HK-005: HomeKit Configuration

- **SHALL** support configurable accessory names for Home app display
- **SHALL** support room assignment hints for initial setup
- **SHALL** support accessory grouping (e.g., "Pool" group containing all pool accessories)

#### FR-HK-006: Homebridge Plugin Specification (Recommended Implementation)

If implemented as a Homebridge plugin:

- **SHALL** be published as npm package for easy installation
- **SHALL** support configuration via Homebridge Config UI
- **SHALL** connect to Poolio cloud backend (Adafruit IO or abstracted backend)
- **SHALL** subscribe to device status updates via MQTT
- **SHALL** publish commands via MQTT

Example Homebridge config structure:

```json
{
  "platform": "PoolioHomebridge",
  "name": "Poolio",
  "cloudBackend": {
    "type": "adafruit_io",
    "username": "your_username",
    "apiKey": "your_api_key"
  },
  "accessories": {
    "poolTemperature": { "name": "Pool Temperature", "room": "Backyard" },
    "outsideTemperature": { "name": "Outside Temperature", "room": "Backyard" },
    "waterLevel": { "name": "Pool Water Level", "room": "Backyard" },
    "fillValve": { "name": "Pool Fill Valve", "room": "Backyard" },
    "pump": { "name": "Pool Pump", "room": "Backyard" }
  }
}
```

#### FR-HK-007: Alternative Integration - Home Assistant

If integrated via Home Assistant:

- **SHALL** provide MQTT sensor/switch configurations for Home Assistant
- **SHALL** document Home Assistant configuration for HomeKit bridge
- **SHALL** support Home Assistant automations

---

### 7.5 Environment Configuration Requirements

The system shall support multiple deployment environments to enable safe development and testing.

#### NFR-ENV-001: Supported Environments

- **SHALL** support two-environment model: `prod` and `nonprod`
- **MAY** support three-environment model: `dev`, `test`, `prod`
- **SHALL** determine active environment from device configuration

**Two-environment model (default):**

| Environment | Purpose |
| ------------- | --------- |
| `prod` | Live production system |
| `nonprod` | All development and testing |

**Three-environment model (optional):**

| Environment | Purpose |
| ------------- | --------- |
| `dev` | Local development, hardware typically disabled |
| `test` | Integration testing with real or simulated hardware |
| `prod` | Live production system |

#### NFR-ENV-002: Environment-Specific Feed Names

- **SHALL** support environment prefix for Adafruit IO feed names
- **SHALL** isolate non-production data from production feeds
- **SHALL** use consistent naming convention across all nodes
- **SHALL** use no prefix for `prod` environment

Example feed naming:

| Environment | Feed Pattern | Example |
| ------------- | -------------- | --------- |
| `prod` | `{feed}` | `pooltemp` |
| `nonprod` | `nonprod-{feed}` | `nonprod-pooltemp` |
| `dev` | `dev-{feed}` | `dev-pooltemp` |
| `test` | `test-{feed}` | `test-pooltemp` |

#### NFR-ENV-003: Environment Configuration Schema

**Two-environment configuration:**

```json
{
  "environment": "nonprod",
  "environmentConfig": {
    "prod": {
      "feedPrefix": "",
      "hardwareEnabled": true,
      "debugLogging": false
    },
    "nonprod": {
      "feedPrefix": "nonprod-",
      "hardwareEnabled": true,
      "debugLogging": true
    }
  }
}
```

**Three-environment configuration:**

```json
{
  "environment": "dev",
  "environmentConfig": {
    "dev": {
      "feedPrefix": "dev-",
      "hardwareEnabled": false,
      "debugLogging": true
    },
    "test": {
      "feedPrefix": "test-",
      "hardwareEnabled": true,
      "debugLogging": true
    },
    "prod": {
      "feedPrefix": "",
      "hardwareEnabled": true,
      "debugLogging": false
    }
  }
}
```

#### NFR-ENV-004: Hardware Safety in Non-Production

- **SHALL** support `hardwareEnabled` flag per environment
- **SHOULD** allow disabling actual hardware actuation in dev/test (simulate only)
- **SHALL** log simulated actions when hardware is disabled
- Example: In `dev` environment, valve commands are logged but GPIO not toggled

#### NFR-ENV-005: Environment Identification

- **SHALL** include environment name in all log entries
- **SHALL** include environment name in device status messages
- **SHALL** display current environment on Display Node UI
- **SHOULD** use visual indicator for non-production (e.g., colored banner)

#### NFR-ENV-006: Environment Switching

- **SHALL** require device restart to change environments
- **SHALL NOT** allow runtime environment switching (prevents accidental prod changes)
- **SHALL** validate environment name against known list on startup

#### NFR-ENV-007: Production Safeguards

- **SHALL** require explicit confirmation for production deployments
- **SHOULD** support configuration checksum verification
- **SHOULD** log warning if production device connects to non-production feeds (or vice versa)

#### NFR-ENV-008: Cloud Environment Support

- **SHALL** use separate API credentials for prod vs nonprod environments
- **SHALL** support environment-aware feed prefix configuration
- **SHALL** select API key based on configured environment
- **MAY** support entirely separate Adafruit IO accounts per environment

*Note: Separate API credentials are required because feed prefix isolation alone cannot prevent a compromised nonprod device from publishing to prod feeds if it has the same API key. Environment-specific keys ensure credential compromise in one environment does not affect the other.*

Example settings.toml with environment support:

```toml
# settings.toml
CIRCUITPY_WIFI_SSID = "NetworkName"
CIRCUITPY_WIFI_PASSWORD = "password"
ENVIRONMENT = "nonprod"
AIO_USERNAME = "your_username"

# Environment-specific API keys (required)
AIO_KEY_PROD = "aio_prod_key"
AIO_KEY_NONPROD = "aio_nonprod_key"
```

*Implementation Note: The application selects the appropriate key based on `ENVIRONMENT` value. For example: `AIO_KEY = AIO_KEY_PROD if ENVIRONMENT == "prod" else AIO_KEY_NONPROD`*

---

### 7.6 Architecture Improvement Requirements

#### NFR-ARCH-001: Shared Code Library

- **SHALL** extract common functionality into reusable modules for each implementation language
- **SHALL** provide shared modules for:
  - **Network** - WiFi connection management, reconnection logic, time synchronization
  - **Logging** - Structured logging with levels and context
  - **Sensors** - Common sensor initialization, reading, and retry patterns
  - **Messages** - JSON message formatting, parsing, and validation
  - **Configuration** - Settings loading, validation, and defaults
  - **Cloud** - Adafruit IO client (publish, subscribe, historical data)
- **SHALL** ensure functional parity between language implementations (Python and C++)

*Note: Specific file/directory structure for each language is defined in implementation documentation.*

#### NFR-ARCH-002: Structured Logging

- **SHALL** implement log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **SHALL** include timestamps in all log entries
- **SHALL** include device ID in all log entries
- **SHALL** support log output to console, file, and cloud
- **SHALL** support configurable log level per output

#### NFR-ARCH-003: Configuration Externalization

- **SHALL** externalize all magic numbers to configuration
- **SHALL** support configuration validation against schema
- **SHALL** support configuration hot-reload for continuously-running nodes (Valve Node, Display Node)
- **SHALL** apply configuration changes on next wake cycle for deep-sleep nodes (Pool Node)
- **SHALL** support configuration versioning

**Hot-reloadable configurations** (no restart required):

- Timing parameters: reportInterval, staleDataIndicatorThreshold, chartRefreshInterval, screensaverTimeout
- Logging: logLevel, debugLogging
- Scheduling: valveStartTime, fillWindowHours, maxFillDuration

**Restart-required configurations**:

- Network: WiFi credentials, MQTT broker settings, API keys
- Hardware: GPIO pin assignments, I2C addresses, sensor types
- Identity: deviceId, environment
- Protocol: supported message versions

#### NFR-ARCH-004: Hardware Abstraction

- **SHALL** abstract hardware interfaces for testability
- **SHALL** support mock implementations for unit testing
- **SHALL** support hardware capability detection

#### NFR-ARCH-005: Observability

- **SHALL** implement health check endpoint/message
- **SHALL** track and report device uptime
- **SHALL** track and report error rates by category
- **SHALL** support remote diagnostics queries

---

### 7.7 Node Simulator Requirements

The system shall provide simulators for each node type to enable development and testing without physical hardware.

#### FR-SIM-001: Simulator Purpose

- **SHALL** provide software simulators for each node type (Pool Node, Valve Node, Display Node)
- **SHALL** enable development of one node while simulating messages from other nodes
- **SHALL** support testing inter-node communication without full hardware deployment
- **SHALL** run on standard development machines (Mac, Linux, Windows)

#### FR-SIM-002: Pool Node Simulator

- **SHALL** generate simulated pool_status messages at configurable intervals
- **SHALL** support configurable sensor values (temperature, water level, battery)
- **SHALL** support scenario scripting (e.g., simulate water level dropping over time)
- **SHALL** publish messages to cloud backend using same format as real Pool Node

#### FR-SIM-003: Valve Node Simulator

- **SHALL** generate simulated valve_status messages at configurable intervals
- **SHALL** respond to command messages (valve_start, valve_stop)
- **SHALL** simulate fill operations with configurable behavior
- **SHALL** generate fill_start/fill_stop events
- **SHALL** subscribe to pool_status messages and apply safety interlock logic

#### FR-SIM-004: Display Node Simulator

- **SHALL** subscribe to all device status messages
- **SHALL** log received messages for debugging
- **SHALL** optionally render a simple text-based or web UI for status display
- **MAY** simulate sending commands to other devices

#### FR-SIM-005: Simulator Configuration

- **SHALL** use same configuration format as real nodes (settings.toml or config.json)
- **SHALL** support command-line overrides for common parameters
- **SHALL** support environment selection (nonprod recommended for simulators)
- **SHALL** clearly identify simulator messages (e.g., deviceId includes "-sim" suffix)

#### FR-SIM-006: Simulator Implementation

- **SHOULD** be implemented in Python for cross-platform compatibility
- **SHALL** reuse shared libraries (messages.py, Adafruit IO client)
- **SHALL** be runnable via simple command: `python -m poolio.simulators.pool_node`
- **MAY** provide Docker containers for easy deployment

*Note: Simulators enable rapid development iteration and integration testing. When developing the valve node, run a pool node simulator to generate test data. When developing the display node, run simulators for both pool and valve nodes.*

---

## 8. Migration Strategy

### 8.0 Minimum Viable Product (MVP) Definition

The MVP represents the first releasable increment, achieved at the end of Phase 2:

**MVP Scope:**

- **Pool Node**: Temperature, water level, and battery reporting via JSON messages
- **Valve Node**: Scheduled filling with safety interlocks, manual control via commands
- **Display Node**: Real-time status display (historical charts deferred to Phase 3)
- **Infrastructure**: JSON message format, Adafruit IO client library

**MVP Exit Criteria:**

- All nodes communicating via JSON messages on nonprod environment
- Valve safety interlocks verified (staleness check, max duration, water level)
- 1-week stability test completed without watchdog resets or data loss
- Manual testing checklist completed for all core scenarios

### 8.1 Implementation Phases

Implementation proceeds in six phases. For detailed tasks, exit criteria, and build sequence, see [Architecture Document - Build Sequence](architecture.md#build-sequence).

| Phase | Name | Summary |
|-------|------|---------|
| 1 | Foundation | Shared libraries, JSON messages, cloud abstraction |
| 2 | Device Framework | Pool Node (2a), Valve Node (2b), Display Node (2c) |
| 3 | Simulators & Testing | Node simulators, integration tests |
| 4 | Deployment | Nonprod (4a), Production (4b) |
| 5 | Smart Home Integration | Homebridge plugin, HomeKit |
| 6 | Reliability & Polish | Error handling, observability, command signing |

**Future (post-Phase 6):** Variable Speed Pump device type (see FR-EXT-005)

---

## 9. Legacy Considerations

### 9.1 Technical Debt from Original Projects

- Hardcoded magic numbers in message parsing
- Mixed message type numbering (gaps in sequence: 0,1,3,4,6,99)
- Inconsistent timestamp formats across nodes
- Duplicate code for WiFi connection handling (~90% duplication)
- No automated testing infrastructure
- Bare `except:` clauses hiding errors (14+ instances)
- Global state management issues

### 9.2 Security Considerations

- Credentials currently stored in plaintext files
- No message authentication or integrity verification
- Single API key shared across all operations
- No access control for remote commands
- No audit trail for command execution

### 9.3 Backward Compatibility

- Support legacy pipe-delimited messages during transition
- Maintain existing Adafruit IO feed structure
- Provide migration guide for existing deployments

---

## 10. Glossary

| Term/Acronym  | Definition                                                                  |
| ------------- | --------------------------------------------------------------------------- |
| CircuitPython | Python implementation for microcontrollers by Adafruit                      |
| Consensus     | Agreement threshold for sensor readings (e.g., >66% of float switch reads must agree) |
| Deep Sleep    | Low-power mode where MCU is mostly off, waking only on timer/interrupt      |
| ESP32         | Espressif microcontroller family (ESP32, ESP32-S2, ESP32-S3) with WiFi/BLE  |
| Feed          | Adafruit IO term for a data stream/topic                                    |
| Fill Window   | Time period during which automatic pool filling is permitted (e.g., 09:00-11:00) |
| GPIO          | General Purpose Input/Output - digital pins on a microcontroller            |
| HAP           | HomeKit Accessory Protocol - Apple's protocol for smart home devices        |
| Homebridge    | Node.js server that exposes non-HomeKit devices to Apple Home               |
| I2C           | Inter-Integrated Circuit - two-wire serial communication bus                |
| Interlock     | Safety condition that must be satisfied before an action is permitted (e.g., fresh pool data required before fill) |
| JSON Schema   | Vocabulary for annotating and validating JSON documents                     |
| MQTT          | Message Queuing Telemetry Transport - lightweight messaging protocol        |
| NeoPixel      | Adafruit brand name for addressable RGB/RGBW LEDs (WS2812/SK6812)           |
| NVS           | Non-Volatile Storage - persistent storage that survives power cycles        |
| OTA           | Over-The-Air - wireless firmware/software updates                           |
| QoS           | Quality of Service - MQTT delivery guarantee levels (0, 1, 2)               |
| REPL          | Read-Eval-Print Loop - interactive programming interface                    |
| REST          | Representational State Transfer - architectural style for web APIs          |
| Sparkline     | Small inline chart showing data trends without axes or labels (used for temperature history) |
| SPI           | Serial Peripheral Interface - synchronous serial communication bus          |
| Staleness     | Age threshold beyond which data is considered too old to be reliable (see FR-VN-003, FR-DN-004) |
| TLS           | Transport Layer Security - cryptographic protocol for secure communications |
| TOML          | Tom's Obvious Minimal Language - configuration file format                  |
| Watchdog      | Hardware timer that resets device if not periodically fed                   |

---

## Appendix A: JSON Message Schemas

This appendix provides JSON Schema definitions for message validation (see FR-MSG-014).

**Schema Version Requirement:** Implementations SHALL support JSON Schema Draft 2020-12 as indicated by `"$schema": "https://json-schema.org/draft/2020-12/schema"` in each schema definition.

### A.1 Message Envelope Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://poolio.local/schemas/message-envelope.json",
  "title": "Poolio Message Envelope",
  "description": "Standard envelope for all Poolio messages",
  "type": "object",
  "required": ["version", "type", "deviceId", "timestamp", "payload"],
  "properties": {
    "version": {
      "type": "integer",
      "minimum": 1,
      "description": "Protocol version number"
    },
    "type": {
      "type": "string",
      "enum": ["pool_status", "valve_status", "display_status", "fill_start", "fill_stop", "command", "command_response", "heartbeat", "error", "config_update"],
      "description": "Message type identifier"
    },
    "deviceId": {
      "type": "string",
      "pattern": "^[a-z0-9-]+$",
      "minLength": 1,
      "maxLength": 64,
      "description": "Unique identifier for sending device"
    },
    "timestamp": {
      "type": "string",
      "format": "date-time",
      "description": "ISO 8601 formatted date/time with timezone offset"
    },
    "payload": {
      "type": "object",
      "description": "Message-specific data"
    }
  }
}
```

*Note: The `type` enum will be extended when pump-related message types (`pump_status`, `pump_speed_change`) are implemented per FR-EXT-005.*

### A.2 Pool Status Payload Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://poolio.local/schemas/pool-status.json",
  "title": "Pool Status Payload",
  "type": "object",
  "required": ["waterLevel", "temperature", "battery", "reportingInterval"],
  "properties": {
    "waterLevel": {
      "type": "object",
      "required": ["floatSwitch"],
      "properties": {
        "floatSwitch": {
          "type": "boolean",
          "description": "true=pool full, false=pool low"
        },
        "confidence": {
          "type": "number",
          "minimum": 0,
          "maximum": 1,
          "description": "Confidence level of reading (0-1)"
        }
      }
    },
    "temperature": {
      "type": "object",
      "required": ["value", "unit"],
      "properties": {
        "value": {
          "type": "number",
          "minimum": 0,
          "maximum": 110,
          "description": "Temperature value"
        },
        "unit": {
          "type": "string",
          "const": "fahrenheit"
        }
      }
    },
    "battery": {
      "type": "object",
      "required": ["voltage", "percentage"],
      "properties": {
        "voltage": {
          "type": "number",
          "minimum": 0,
          "maximum": 5,
          "description": "Battery voltage"
        },
        "percentage": {
          "type": "integer",
          "minimum": 0,
          "maximum": 100,
          "description": "Battery percentage"
        }
      }
    },
    "reportingInterval": {
      "type": "integer",
      "minimum": 10,
      "description": "Seconds between reports"
    }
  }
}
```

### A.3 Valve Status Payload Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://poolio.local/schemas/valve-status.json",
  "title": "Valve Status Payload",
  "type": "object",
  "required": ["valve", "schedule", "temperature"],
  "properties": {
    "valve": {
      "type": "object",
      "required": ["state", "isFilling"],
      "properties": {
        "state": {
          "type": "string",
          "enum": ["open", "closed"]
        },
        "isFilling": {
          "type": "boolean"
        },
        "currentFillDuration": {
          "type": "integer",
          "minimum": 0,
          "description": "Current fill duration in seconds"
        },
        "maxFillDuration": {
          "type": "integer",
          "minimum": 0,
          "description": "Maximum fill duration in seconds"
        }
      }
    },
    "schedule": {
      "type": "object",
      "required": ["enabled", "startTime", "windowHours"],
      "properties": {
        "enabled": {
          "type": "boolean"
        },
        "startTime": {
          "type": "string",
          "pattern": "^([01][0-9]|2[0-3]):[0-5][0-9]$",
          "description": "Fill start time in HH:MM format (zero-padded)"
        },
        "windowHours": {
          "type": "integer",
          "minimum": 1,
          "maximum": 24
        },
        "nextScheduledFill": {
          "type": "string",
          "format": "date-time"
        }
      }
    },
    "temperature": {
      "type": "object",
      "required": ["value", "unit"],
      "properties": {
        "value": {
          "type": "number",
          "minimum": -20,
          "maximum": 130
        },
        "unit": {
          "type": "string",
          "const": "fahrenheit"
        }
      }
    }
  }
}
```

### A.4 Command Payload Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://poolio.local/schemas/command.json",
  "title": "Command Payload",
  "type": "object",
  "required": ["command"],
  "properties": {
    "command": {
      "type": "string",
      "enum": ["valve_start", "valve_stop", "device_reset", "set_config"],
      "description": "Command to execute"
    },
    "parameters": {
      "type": "object",
      "description": "Command-specific parameters",
      "properties": {
        "maxDuration": {
          "type": "integer",
          "minimum": 0,
          "maximum": 3600,
          "description": "Maximum duration in seconds (valve_start only)"
        }
      }
    },
    "source": {
      "type": "string",
      "pattern": "^[a-z0-9-]+$",
      "minLength": 1,
      "maxLength": 64,
      "description": "Device ID of the command sender (optional, for audit/debugging)"
    }
  }
}
```

*Note: Parameter validation is command-specific. The `maxDuration` parameter for `valve_start` is capped at 3600 seconds (1 hour) to prevent unbounded fills. For request/response correlation, use the `timestamp` from the message envelope (see FR-MSG-009). The optional `source` field allows tracking which device sent a command for audit and debugging purposes.*

### A.5 Error Payload Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://poolio.local/schemas/error.json",
  "title": "Error Payload",
  "type": "object",
  "required": ["errorCode", "errorMessage", "severity"],
  "properties": {
    "errorCode": {
      "type": "string",
      "pattern": "^[A-Z_]+$",
      "description": "Machine-readable error identifier"
    },
    "errorMessage": {
      "type": "string",
      "description": "Human-readable description"
    },
    "severity": {
      "type": "string",
      "enum": ["debug", "info", "warning", "error", "critical"]
    },
    "context": {
      "type": "object",
      "description": "Additional diagnostic information"
    }
  }
}
```

### A.6 Display Status Payload Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://poolio.local/schemas/display-status.json",
  "title": "Display Status Payload",
  "type": "object",
  "required": ["localTemperature", "localHumidity"],
  "properties": {
    "localTemperature": {
      "type": "object",
      "required": ["value", "unit"],
      "properties": {
        "value": {
          "type": "number",
          "minimum": -20,
          "maximum": 130
        },
        "unit": {
          "type": "string",
          "const": "fahrenheit"
        }
      }
    },
    "localHumidity": {
      "type": "object",
      "required": ["value", "unit"],
      "properties": {
        "value": {
          "type": "number",
          "minimum": 0,
          "maximum": 100
        },
        "unit": {
          "type": "string",
          "const": "percent"
        }
      }
    }
  }
}
```

### A.7 Fill Start Payload Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://poolio.local/schemas/fill-start.json",
  "title": "Fill Start Payload",
  "type": "object",
  "required": ["fillStartTime", "scheduledEndTime", "maxDuration", "trigger"],
  "properties": {
    "fillStartTime": {
      "type": "string",
      "format": "date-time",
      "description": "ISO 8601 timestamp when fill started"
    },
    "scheduledEndTime": {
      "type": "string",
      "format": "date-time",
      "description": "Expected end time based on max duration"
    },
    "maxDuration": {
      "type": "integer",
      "minimum": 0,
      "maximum": 3600,
      "description": "Maximum fill duration in seconds"
    },
    "trigger": {
      "type": "string",
      "enum": ["scheduled", "manual", "low_water"],
      "description": "What initiated the fill"
    }
  }
}
```

### A.8 Fill Stop Payload Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://poolio.local/schemas/fill-stop.json",
  "title": "Fill Stop Payload",
  "type": "object",
  "required": ["fillStopTime", "actualDuration", "reason"],
  "properties": {
    "fillStopTime": {
      "type": "string",
      "format": "date-time",
      "description": "ISO 8601 timestamp when fill stopped"
    },
    "actualDuration": {
      "type": "integer",
      "minimum": 0,
      "description": "Actual fill duration in seconds"
    },
    "reason": {
      "type": "string",
      "enum": ["water_full", "max_duration", "manual", "error", "window_closed"],
      "description": "Why fill stopped"
    }
  }
}
```

### A.9 Heartbeat Payload Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://poolio.local/schemas/heartbeat.json",
  "title": "Heartbeat Payload",
  "type": "object",
  "required": ["uptime"],
  "properties": {
    "uptime": {
      "type": "integer",
      "minimum": 0,
      "description": "Seconds since device boot"
    },
    "freeMemory": {
      "type": "integer",
      "minimum": 0,
      "description": "Available memory in bytes"
    },
    "errorCount": {
      "type": "integer",
      "minimum": 0,
      "description": "Number of errors since boot"
    },
    "lastError": {
      "type": ["string", "null"],
      "description": "Description of last error, or null if none"
    }
  }
}
```

### A.10 Config Update Payload Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://poolio.local/schemas/config-update.json",
  "title": "Config Update Payload",
  "type": "object",
  "required": ["configKey", "configValue", "source"],
  "properties": {
    "configKey": {
      "type": "string",
      "minLength": 1,
      "maxLength": 64,
      "description": "Configuration parameter being updated"
    },
    "configValue": {
      "description": "New value for the parameter (type depends on configKey)"
    },
    "source": {
      "type": "string",
      "enum": ["cloud", "local", "default"],
      "description": "Origin of update"
    }
  }
}
```

### A.11 Command Response Payload Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://poolio.local/schemas/command-response.json",
  "title": "Command Response Payload",
  "type": "object",
  "required": ["commandTimestamp", "command", "status"],
  "properties": {
    "commandTimestamp": {
      "type": "string",
      "format": "date-time",
      "description": "Timestamp from the original command message envelope"
    },
    "command": {
      "type": "string",
      "description": "The command that was executed"
    },
    "status": {
      "type": "string",
      "enum": ["success", "failed", "rejected"],
      "description": "Execution result"
    },
    "errorCode": {
      "type": ["string", "null"],
      "pattern": "^[A-Z_]+$",
      "description": "Machine-readable error code if status is not success"
    },
    "errorMessage": {
      "type": ["string", "null"],
      "description": "Human-readable error description if status is not success"
    }
  }
}
```

*Note: Full schemas should be maintained in the codebase at `schemas/` (project root) for runtime validation.*
