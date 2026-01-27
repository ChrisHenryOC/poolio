# Implementation Plan: Poolio Rearchitecture (Phases 1-4)

> Generated from:
>
> - Requirements: docs/requirements.md
> - Architecture: docs/architecture.md
> - UI Design: docs/display-node-ui-design.md
> - Date: 2026-01-23
> - Revised: 2026-01-23 (Kent Beck principles alignment, TDD workflow, issue splitting)
> - Revised: 2026-01-23 (Architecture alignment: added ScheduleInfo/ValveState classes, message size/freshness validation, time resync, socket management, deferred captive portal)
> - Revised: 2026-01-23 (Consistency fixes: cross-references, acceptance criteria clarity, removed cooldown state)
> - Revised: 2026-01-26 (GitHub issues created: #9-#77)

## Overview

This implementation plan covers Phases 1-4 of the Poolio pool automation system rearchitecture:

- **Phase 1**: Foundation - Shared libraries, JSON message protocol, cloud abstraction
- **Phase 2**: Device Framework - Pool Node (C++), Valve Node (CircuitPython), Display Node (CircuitPython)
- **Phase 3**: Simulators & Testing - Node simulators, integration test suite
- **Phase 4**: Deployment - Nonprod validation, production rollout

The plan decomposes the work into 71 issues (67 MVP + 4 deferred) suitable for focused implementation sessions.

## Sequential Thinking Summary

**Initial approach**: Started by mapping the architecture document's build sequence (Section 15) to concrete implementation tasks, then decomposed each phase into issues sized for 1-2 hour sessions.

**Revisions made**:

- Split the Dashboard Controller (originally one issue) into three parts: local sensors, state management, and MQTT/navigation - the original was too large for a single session
- Grouped cloud client implementations (HTTP and MQTT) as separate issues since they serve different node types and have distinct testing requirements

**Kent Beck alignment revision (2026-01-23)**:

- Defer abstractions: CloudBackend base class extracted only when second implementation (MQTT) is added
- Defer full jsonschema validation to Phase 4+ (use simple required-field checks on-device)
- Defer command rate limiting to Phase 4+ (implement only if abuse detected)
- Defer legacy message support to Phase 4 (implement only if migration proves it necessary)
- Add Display Node UI spike before detailed screen issues (iterate on hardware first)
- Keep burn-in prevention (observed issue in legacy implementation)

**Key insights**:

- Phase 2 sub-phases (2a, 2b, 2c) can be parallelized since they target different node types
- The C++ Pool Node requires its own message library implementation (can't share Python code)
- Simulators (Phase 3) enable testing even before all hardware nodes are complete
- Display Node has the most issues (16) due to the complex UI requirements from the design document
- Follow "Make it work, make it right, make it fast" - concrete implementations before abstractions

---

## Issue Workflow (TDD)

Each issue follows the red/green/refactor cycle per Kent Beck's Test-Driven Development:

1. **Red** - Write a failing test that defines the expected behavior (based on acceptance criteria)
2. **Green** - Write the minimum code to make the test pass
3. **Refactor** - Clean up while keeping tests green

Repeat for each acceptance criterion. Integration issues may require end-to-end tests first, then unit tests for individual components.

---

## Phases

| Phase | Name | Description | Issues |
| ----- | ---- | ----------- | ------ |
| 1 | Foundation | Shared libraries, messages, cloud abstraction | #9-#19 |
| 2a | Pool Node | C++ sensor node with deep sleep | #20-#30 |
| 2b | Valve Node | CircuitPython fill controller | #31-#36 |
| 2c | Display Node | CircuitPython touchscreen dashboard | #37-#56 |
| 3 | Simulators | Desktop simulators and integration tests | #57-#63 |
| 4 | Deployment | Nonprod and production deployment | #64-#77 |
| 4+ | Deferred | Features to implement only if needed | (not created) |

**Note**: Phase 2a, 2b, and 2c can be worked in parallel. Deferred features (4.15-4.18) are not tracked in GitHub until needed.

---

## Issue Backlog

### Phase 1: Foundation

---

### Issue #9: Project Setup and Structure

- **Phase**: 1 - Foundation
- **Type**: Setup
- **Description**: Create the project directory structure, Python package configuration, and CI/CD pipeline as defined in architecture.md Section 5.
- **Acceptance Criteria**:
  - [ ] Directory structure matches architecture document
  - [ ] pyproject.toml configured with uv for dependency management
  - [ ] .gitignore includes secrets patterns (settings.toml, secrets.h)
  - [ ] GitHub Actions CI workflow runs pytest and ruff
  - [ ] BLINKA_MCP2221 environment variable set in CI for CircuitPython compatibility
- **Files**:
  - `pyproject.toml`
  - `.gitignore`
  - `.github/workflows/ci.yml`
  - `src/shared/__init__.py`
  - `tests/__init__.py`
- **Dependencies**: None
- **Tests**: CI workflow runs successfully on empty test suite

---

### Issue #10: Message Type Classes

- **Phase**: 1 - Foundation
- **Type**: Model
- **Description**: Implement plain Python classes for all message payload types defined in FR-MSG-004 through FR-MSG-013. Classes must be CircuitPython compatible (no dataclasses, no type annotations in signatures).
- **Acceptance Criteria**:
  - [ ] WaterLevel class with floatSwitch (bool) and confidence (float)
  - [ ] Temperature class with value (float) and unit (str)
  - [ ] Battery class with voltage (float) and percentage (int)
  - [ ] PoolStatus class with waterLevel, temperature, battery, reportingInterval
  - [ ] ValveState class with state (str: "open" or "closed"), isFilling (bool), currentFillDuration (int seconds or None), maxFillDuration (int seconds or None)
  - [ ] ScheduleInfo class with startTime (str "HH:MM"), windowHours (int), nextFillTime (str ISO 8601), nextCheckTime (str ISO 8601)
  - [ ] ValveStatus class with valve (ValveState), schedule (ScheduleInfo), temperature (Temperature)
  - [ ] DisplayStatus class with localTemperature, localHumidity
  - [ ] FillStart class with fillStartTime, scheduledEndTime, maxDuration, trigger
  - [ ] FillStop class with fillStopTime, actualDuration, reason
  - [ ] Command class with command, parameters, source
  - [ ] CommandResponse class with commandTimestamp, command, status, errorCode, errorMessage
  - [ ] Error class with errorCode, errorMessage, severity, context
  - [ ] ConfigUpdate class with configKey, configValue, source
  - [ ] ErrorCode constants for all 22 codes from FR-MSG-011 (SENSOR_*, NETWORK_*, BUS_*, CONFIG_*, SYSTEM_*, VALVE_*)
  - [ ] All classes have `__init__` with documented parameter types
- **Files**:
  - `src/shared/messages/__init__.py`
  - `src/shared/messages/types.py`
  - `tests/unit/test_message_types.py`
- **Dependencies**: #9
- **Tests**: Unit tests verify class instantiation and attribute access

---

### Issue #11: Message Envelope and Encoding

- **Phase**: 1 - Foundation
- **Type**: Core
- **Description**: Implement envelope creation/parsing and message encoding/decoding per FR-MSG-001 and FR-MSG-002. The envelope includes version, type, deviceId, timestamp, and payload.
- **Acceptance Criteria**:
  - [ ] `create_envelope(msg_type, device_id, payload)` returns dict with all envelope fields
  - [ ] `parse_envelope(json_str)` returns (envelope_dict, payload_dict) tuple
  - [ ] `encode_message(message)` returns JSON string with proper envelope
  - [ ] `decode_message(json_str)` returns appropriate message type object
  - [ ] Encoder converts Python `snake_case` attributes to JSON `camelCase` keys
  - [ ] Decoder converts JSON `camelCase` keys to Python `snake_case` attributes
  - [ ] Timestamps use ISO 8601 format with timezone offset
  - [ ] Device ID format validated: lowercase letters, numbers, hyphens, 1-64 chars
- **Files**:
  - `src/shared/messages/envelope.py`
  - `src/shared/messages/encoder.py`
  - `src/shared/messages/decoder.py`
  - `tests/unit/test_envelope.py`
  - `tests/unit/test_encoder.py`
  - `tests/unit/test_decoder.py`
- **Dependencies**: #10
- **Tests**: Round-trip encoding/decoding preserves all data; case conversion verified

---

### Issue #12: Message Validation (Simple)

- **Phase**: 1 - Foundation
- **Type**: Core
- **Description**: Implement simple required-field validation for CircuitPython. JSON Schema files and strict validation deferred to Phase 4+ per Kent Beck's "fewest elements" principle.
- **Acceptance Criteria**:
  - [ ] `validate_envelope(envelope)` checks required fields: version, type, deviceId, timestamp, payload
  - [ ] `validate_payload(msg_type, payload)` checks required fields per message type
  - [ ] Returns (valid: bool, errors: list) tuple
  - [ ] Invalid messages logged with specific error details
  - [ ] No external dependencies (no jsonschema library)
  - [ ] `validate_message_size(json_str)` rejects messages exceeding 4KB, logs actual size
  - [ ] `validate_timestamp_freshness(timestamp, msg_type)` checks message age:
    - Commands: reject if older than 5 minutes (prevents replay attacks)
    - Status messages: reject if older than 15 minutes
    - All messages: reject if more than 1 minute in future (clock skew protection)
  - [ ] Freshness validation uses device's current time (synced from cloud)
- **Files**:
  - `src/shared/messages/validator.py`
  - `tests/unit/test_validator.py`
- **Dependencies**: #11
- **Tests**: Validate both valid and invalid messages; verify error messages are descriptive; test size limits and timestamp rejection
- **Deferred**: JSON Schema files and `strict=True` mode moved to Phase 4+ (implement only if needed)

---

### Issue #13: Mock Cloud Backend for Testing

- **Phase**: 1 - Foundation
- **Type**: Core
- **Description**: Create MockBackend for testing. Base class extraction deferred until MQTT client is implemented (#15) per Kent Beck's "no premature abstraction" principle.
- **Acceptance Criteria**:
  - [ ] MockBackend with in-memory storage for testing
  - [ ] MockBackend.publish(feed, value) stores messages by feed name
  - [ ] MockBackend.subscribe(feed, callback) registers callback, calls it for matching publishes
  - [ ] MockBackend.fetch_latest(feed) returns most recent value
  - [ ] MockBackend.fetch_history(feed, hours) returns list of values
  - [ ] MockBackend.sync_time() returns current time as adafruit_datetime
  - [ ] connect() and disconnect() are no-ops for mock
- **Files**:
  - `src/shared/cloud/__init__.py`
  - `src/shared/cloud/mock.py`
  - `tests/unit/test_mock_backend.py`
- **Dependencies**: #9
- **Tests**: MockBackend publish/subscribe flow works correctly
- **Note**: CloudBackend base class will be extracted in #15 when MQTT is implemented (see common interface pattern)

---

### Issue #14: AdafruitIO HTTP Client

- **Phase**: 1 - Foundation
- **Type**: Integration
- **Description**: Implement AdafruitIOHTTP client for Pool Node (HTTPS POST, no MQTT subscription). Handles publish, fetch, and time sync.
- **Acceptance Criteria**:
  - [ ] AdafruitIOHTTP class extends CloudBackend pattern
  - [ ] Constructor takes username, api_key, environment
  - [ ] publish(feed, value) posts to Adafruit IO REST API
  - [ ] fetch_latest(feed) gets most recent value
  - [ ] fetch_history(feed, hours) gets historical data with resolution parameter
  - [ ] sync_time() calls /integrations/time/struct endpoint
  - [ ] Uses HTTPS with X-AIO-Key header
  - [ ] subscribe() raises NotImplementedError (HTTP doesn't support subscriptions)
  - [ ] Feed names include environment prefix per NFR-ENV-002
- **Files**:
  - `src/shared/cloud/adafruit_io_http.py`
  - `tests/unit/test_adafruit_io_http.py`
- **Dependencies**: #13
- **Tests**: Unit tests with mocked HTTP responses; integration test against nonprod (manual)

---

### Issue #15: AdafruitIO MQTT Client and Base Class Extraction

- **Phase**: 1 - Foundation
- **Type**: Integration
- **Description**: Implement AdafruitIOMQTT client for Valve and Display Nodes. Extract CloudBackend base class now that we have two implementations (HTTP and MQTT).
- **Acceptance Criteria**:
  - [ ] **Extract CloudBackend base class** from common patterns in HTTP and Mock implementations
  - [ ] CloudBackend defines interface: connect, disconnect, publish, subscribe, fetch_latest, fetch_history, sync_time
  - [ ] AdafruitIOMQTT implements CloudBackend interface
  - [ ] Constructor takes username, api_key, environment
  - [ ] connect() establishes MQTT connection to io.adafruit.com:8883 (TLS)
  - [ ] disconnect() cleanly closes connection
  - [ ] publish(feed, value, qos=0) publishes message
  - [ ] subscribe(feed, callback) registers callback for feed
  - [ ] subscribe_throttle(callback) subscribes to {username}/throttle
  - [ ] Throttle handling: pause publishing 60s on throttle, exponential backoff on repeated throttles (120s, 240s, max 300s)
  - [ ] fetch_latest, fetch_history, sync_time use HTTP (fallback)
  - [ ] Uses QoS 0 for status messages, QoS 1 for commands
  - [ ] Feed names include environment prefix
  - [ ] Update MockBackend and AdafruitIOHTTP to extend CloudBackend
- **Files**:
  - `src/shared/cloud/base.py` (new - extracted from implementations)
  - `src/shared/cloud/adafruit_io_mqtt.py`
  - `src/shared/cloud/mock.py` (updated to extend base)
  - `src/shared/cloud/adafruit_io_http.py` (updated to extend base)
  - `tests/unit/test_adafruit_io_mqtt.py`
- **Dependencies**: #13, #14
- **Tests**: Unit tests with mocked MQTT client; verify callback invocation; verify all backends implement same interface

---

### Issue #16: Configuration Management

- **Phase**: 1 - Foundation
- **Type**: Core
- **Description**: Implement configuration loading, validation, and environment handling per architecture.md Config Module section.
- **Acceptance Criteria**:
  - [ ] `load_config(node_type, env_override=None)` loads config for node type
  - [ ] Config loaded from settings.toml (secrets) and config.json (settings)
  - [ ] NODE_DEFAULTS dict provides defaults per node type
  - [ ] `get_feed_name(logical_name, environment)` returns full feed name with group
  - [ ] `select_api_key(environment, secrets)` returns appropriate AIO_KEY
  - [ ] `get_environment_config(environment)` returns EnvironmentConfig
  - [ ] Validates environment against ["prod", "nonprod"]
  - [ ] Hot-reloadable vs restart-required config items documented
- **Files**:
  - `src/shared/config/__init__.py`
  - `src/shared/config/loader.py`
  - `src/shared/config/schema.py`
  - `src/shared/config/defaults.py`
  - `src/shared/config/environment.py`
  - `tests/unit/test_config.py`
- **Dependencies**: #9
- **Tests**: Test config loading with various combinations of defaults and overrides

---

### Issue #17: Logging Module

- **Phase**: 1 - Foundation
- **Type**: Core
- **Description**: Implement structured logging wrapper around adafruit_logging with rotating file handler support.
- **Acceptance Criteria**:
  - [ ] `get_logger(device_id, debug_logging=False)` returns configured logger
  - [ ] Logger includes device_id in all messages
  - [ ] StreamHandler (console) always added
  - [ ] `add_file_logging(logger, log_path)` adds RotatingFileHandler if writable
  - [ ] RotatingFileHandler rotates at 125KB, keeps 3 files
  - [ ] `is_writable()` gracefully handles read-only filesystem
  - [ ] Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Files**:
  - `src/shared/logging/__init__.py`
  - `src/shared/logging/logger.py`
  - `src/shared/logging/rotating_handler.py`
  - `tests/unit/test_logging.py`
- **Dependencies**: #9
- **Tests**: Verify log output format; test file rotation

---

### Issue #18: Sensor Utilities

- **Phase**: 1 - Foundation
- **Type**: Core
- **Description**: Implement retry with exponential backoff and bus recovery helpers per NFR-REL-002 and NFR-REL-006.
- **Acceptance Criteria**:
  - [ ] `retry_with_backoff(func, max_retries=3, base_delay=0.1, max_delay=2.0, exceptions=(Exception,))`
  - [ ] Delays follow pattern: 100ms, 200ms, 400ms, 800ms, 1600ms, 2000ms (capped)
  - [ ] `recover_i2c_bus(scl_pin, sda_pin)` deinits bus, toggles SCL 9 times, reinits
  - [ ] `recover_onewire_bus(data_pin)` deinits bus, pulls data low 500μs, reinits
  - [ ] Recovery functions return True on success, False on failure
  - [ ] All operations logged for diagnostics
- **Files**:
  - `src/shared/sensors/__init__.py`
  - `src/shared/sensors/retry.py`
  - `src/shared/sensors/bus_recovery.py`
  - `tests/unit/test_retry.py`
  - `tests/unit/test_bus_recovery.py`
- **Dependencies**: #17
- **Tests**: Verify retry count and delay timing; mock bus operations

---

### Issue #19: Foundation Integration Test

- **Phase**: 1 - Foundation
- **Type**: Test
- **Description**: Create end-to-end integration test verifying all Phase 1 modules work together: encode message → publish to mock → subscribe receives → decode message.
- **Acceptance Criteria**:
  - [ ] Test creates PoolStatus message object
  - [ ] Encodes message to JSON with envelope
  - [ ] Publishes to MockBackend
  - [ ] Subscribe callback receives message
  - [ ] Decodes message back to PoolStatus object
  - [ ] Verifies all fields match original
  - [ ] Test covers at least 3 message types (PoolStatus, ValveStatus, Command)
- **Files**:
  - `tests/integration/test_message_flow.py`
- **Dependencies**: #10, #11, #12, #13
- **Tests**: Integration test passes with mock backend

---

### Phase 2a: Pool Node (C++)

---

### Issue #20: Pool Node Project Setup

- **Phase**: 2a - Pool Node
- **Type**: Setup
- **Description**: Create PlatformIO project structure for C++ Pool Node with environment configurations for nonprod and prod.
- **Acceptance Criteria**:
  - [ ] platformio.ini with [env:nonprod] and [env:prod] sections
  - [ ] Board: adafruit_feather_esp32_v2
  - [ ] Build flags include ENVIRONMENT, FEED_PREFIX, DEBUG_LOGGING
  - [ ] secrets.h.example template with placeholders
  - [ ] main.cpp stub that compiles
  - [ ] Directory structure per architecture.md
- **Files**:
  - `pool_node_cpp/platformio.ini`
  - `pool_node_cpp/src/main.cpp`
  - `pool_node_cpp/include/secrets.h.example`
  - `pool_node_cpp/lib/.gitkeep`
  - `pool_node_cpp/test/.gitkeep`
- **Dependencies**: #9
- **Tests**: `pio run -e nonprod` compiles successfully

---

### Issue #21: C++ Message Library

- **Phase**: 2a - Pool Node
- **Type**: Model
- **Description**: Port message types and encoding to C++ using ArduinoJson. Implement only the message types Pool Node needs to send.
- **Acceptance Criteria**:
  - [ ] PoolStatus struct with nested WaterLevel, Temperature, Battery
  - [ ] createEnvelope function adds version, type, deviceId, timestamp
  - [ ] encodePoolStatus returns JSON string
  - [ ] JSON output matches schema from Appendix A
  - [ ] Timestamp formatted as ISO 8601 with timezone offset
  - [ ] Uses ArduinoJson for serialization
- **Files**:
  - `pool_node_cpp/lib/messages/messages.h`
  - `pool_node_cpp/lib/messages/messages.cpp`
  - `pool_node_cpp/lib/messages/pool_status.h`
  - `pool_node_cpp/lib/messages/pool_status.cpp`
  - `pool_node_cpp/test/test_messages.cpp`
- **Dependencies**: #20
- **Tests**: PlatformIO test verifies JSON output format

---

### Issue #22: C++ Config and Logging

- **Phase**: 2a - Pool Node
- **Type**: Core
- **Description**: Implement NVS-based credential storage, structured logging, and environment configuration for C++.
- **Acceptance Criteria**:
  - [ ] save_credentials and load_credentials using ESP32 Preferences
  - [ ] is_provisioned check for first-boot detection
  - [ ] Structured log macros: LOG_DEBUG, LOG_INFO, LOG_WARNING, LOG_ERROR
  - [ ] Log output includes timestamp and device ID
  - [ ] Environment config struct with feedPrefix, hardwareEnabled, debugLogging
  - [ ] select_api_key based on environment
- **Files**:
  - `pool_node_cpp/lib/config/nvs_config.h`
  - `pool_node_cpp/lib/config/nvs_config.cpp`
  - `pool_node_cpp/lib/config/environment.h`
  - `pool_node_cpp/lib/config/environment.cpp`
  - `pool_node_cpp/lib/logging/logger.h`
  - `pool_node_cpp/lib/logging/logger.cpp`
- **Dependencies**: #20
- **Tests**: Unit tests for config loading

---

### Issue #23: WiFi Manager with Timeout

- **Phase**: 2a - Pool Node
- **Type**: Core
- **Description**: Implement WiFi connection manager with 15-second timeout and exponential backoff reconnection per NFR-REL-005 and NFR-REL-003.
- **Acceptance Criteria**:
  - [ ] connect() attempts connection with 15s timeout
  - [ ] Returns connection status (success/failure)
  - [ ] reconnect_with_backoff uses delays: 5s, 10s, 20s... up to 300s
  - [ ] Resets device after 10 consecutive failures
  - [ ] Feeds watchdog during connection attempts
  - [ ] disconnect() cleanly closes WiFi
- **Files**:
  - `pool_node_cpp/src/network/wifi_manager.h`
  - `pool_node_cpp/src/network/wifi_manager.cpp`
  - `pool_node_cpp/test/test_wifi_manager.cpp`
- **Dependencies**: #22
- **Tests**: Unit test with mocked WiFi library

---

### Issue #24: Time Sync and HTTP Client

- **Phase**: 2a - Pool Node
- **Type**: Integration
- **Description**: Implement time synchronization from Adafruit IO and HTTP client with 10-second timeout for publishing.
- **Acceptance Criteria**:
  - [ ] sync_time() fetches from /integrations/time/struct endpoint
  - [ ] Parses response and sets ESP32 RTC
  - [ ] Uses configured timezone (America/Los_Angeles default)
  - [ ] HTTPClient with 10s timeout for requests
  - [ ] publish(feed, value) posts to Adafruit IO REST API
  - [ ] Uses HTTPS with X-AIO-Key header
  - [ ] Handles HTTP errors gracefully
- **Files**:
  - `pool_node_cpp/src/network/time_sync.h`
  - `pool_node_cpp/src/network/time_sync.cpp`
  - `pool_node_cpp/src/network/http_client.h`
  - `pool_node_cpp/src/network/http_client.cpp`
- **Dependencies**: #23
- **Tests**: Unit tests with mocked HTTP responses

---

### Issue #25: Temperature Sensor (DS18X20)

- **Phase**: 2a - Pool Node
- **Type**: Core
- **Description**: Implement DS18X20 OneWire temperature sensor reading with retry and validation per FR-PN-001.
- **Acceptance Criteria**:
  - [ ] Initialize OneWire bus on GPIO D10
  - [ ] read_temperature() returns temperature in Fahrenheit
  - [ ] Validates reading in range 0°F to 110°F (pool water range)
  - [ ] Retries up to 3 times with exponential backoff
  - [ ] Returns null/error indicator on failure after retries
  - [ ] Implements bus recovery on repeated failures
  - [ ] Converts Celsius to Fahrenheit: F = (C × 9/5) + 32
- **Files**:
  - `pool_node_cpp/src/sensors/temperature.h`
  - `pool_node_cpp/src/sensors/temperature.cpp`
  - `pool_node_cpp/test/test_temperature.cpp`
- **Dependencies**: #20
- **Tests**: Unit test with mocked sensor

---

### Issue #26: Water Level Sensor (Float Switch)

- **Phase**: 2a - Pool Node
- **Type**: Core
- **Description**: Implement float switch reading with consensus logic per FR-PN-002.
- **Acceptance Criteria**:
  - [ ] Float switch input on GPIO D11, power control on GPIO D12
  - [ ] read_water_level() performs 30 reads (configurable)
  - [ ] Consensus when >66% of reads agree
  - [ ] Returns floatSwitch (bool) and confidence (0-1)
  - [ ] Returns "full" (true) if consensus cannot be established (safety-first)
  - [ ] Power pin controlled to save battery between reads
- **Files**:
  - `pool_node_cpp/src/sensors/water_level.h`
  - `pool_node_cpp/src/sensors/water_level.cpp`
  - `pool_node_cpp/test/test_water_level.cpp`
- **Dependencies**: #20
- **Tests**: Unit test verifying consensus calculation

---

### Issue #27: Battery Monitor (LC709203F)

- **Phase**: 2a - Pool Node
- **Type**: Core
- **Description**: Implement LC709203F fuel gauge reading over I2C with bus recovery per FR-PN-003.
- **Acceptance Criteria**:
  - [ ] Initialize I2C communication with LC709203F
  - [ ] read_battery() returns voltage (2 decimal precision) and percentage (0-100)
  - [ ] Retries on I2C errors with exponential backoff
  - [ ] Implements I2C bus recovery after 3 consecutive failures
  - [ ] Returns null values on complete failure
- **Files**:
  - `pool_node_cpp/src/sensors/battery.h`
  - `pool_node_cpp/src/sensors/battery.cpp`
  - `pool_node_cpp/test/test_battery.cpp`
- **Dependencies**: #20
- **Tests**: Unit test with mocked I2C

---

### Issue #28: Watchdog and Sleep Manager

- **Phase**: 2a - Pool Node
- **Type**: Core
- **Description**: Implement hardware watchdog (60s timeout) and deep sleep manager with proper cleanup per NFR-REL-001 and FR-PN-005.
- **Acceptance Criteria**:
  - [ ] enable_watchdog() configures 60s hardware watchdog
  - [ ] feed_watchdog() resets watchdog timer
  - [ ] disable_watchdog() for pre-sleep
  - [ ] enter_deep_sleep(duration_seconds) with proper cleanup
  - [ ] Calculates remaining sleep accounting for execution time
  - [ ] Enforces minimum 10 second sleep
  - [ ] Releases all bus resources before sleep
  - [ ] Re-enables watchdog on wake
- **Files**:
  - `pool_node_cpp/src/watchdog/watchdog.h`
  - `pool_node_cpp/src/watchdog/watchdog.cpp`
  - `pool_node_cpp/src/power/sleep_manager.h`
  - `pool_node_cpp/src/power/sleep_manager.cpp`
- **Dependencies**: #20
- **Tests**: Verify watchdog timing; sleep duration calculation

---

### Issue #29: Pool Node Controller Integration

- **Phase**: 2a - Pool Node
- **Type**: Integration
- **Description**: Implement main PoolNode controller that orchestrates all components through the wake cycle.
- **Size Note**: This issue is intentionally kept as one unit because the wake cycle is a single coherent sequence. Split would create artificial boundaries between tightly coupled steps.
- **Acceptance Criteria**:
  - [ ] PoolNode class with init(), run() methods
  - [ ] Wake cycle: Init Watchdog → WiFi → Time Sync → Read Sensors → Transmit → Cleanup → Sleep
  - [ ] Feeds watchdog at each stage (≤15s intervals)
  - [ ] Handles sensor failures per NFR-REL-002a (sends null values, continues)
  - [ ] Publishes pool_status to gateway feed
  - [ ] Publishes pooltemp and poolnodebattery to individual feeds
  - [ ] Tracks consecutive failures; resets after threshold
  - [ ] Logs errors before reset (90s delay)
  - [ ] Socket resource management per NFR-REL-007:
    - Maximum 1 concurrent HTTP connection (sequential requests)
    - Close HTTP response objects immediately after reading
    - Reset socket pool before entering deep sleep
    - Connection timeout: 10 seconds
- **Files**:
  - `pool_node_cpp/src/pool_node.h`
  - `pool_node_cpp/src/pool_node.cpp`
  - `pool_node_cpp/src/main.cpp` (updated)
- **Dependencies**: #21, #22, #23, #24, #25, #26, #27, #28
- **Tests**: Integration test of full cycle with mocked hardware
- **TDD Approach**: Write end-to-end test for complete wake cycle first, then add unit tests for error paths

---

### Issue #30: Pool Node Hardware Testing

- **Phase**: 2a - Pool Node
- **Type**: Test
- **Description**: Deploy Pool Node to real hardware and verify all functionality with 24-hour stability test.
- **Acceptance Criteria**:
  - [ ] Flash nonprod build to Feather ESP32 V2
  - [ ] Verify WiFi connection and time sync
  - [ ] Verify temperature sensor readings
  - [ ] Verify float switch consensus logic
  - [ ] Verify battery monitoring
  - [ ] Verify deep sleep and wake cycles
  - [ ] Run 24-hour stability test
  - [ ] Zero watchdog resets during stability test
  - [ ] Data appears correctly in Adafruit IO nonprod feeds
- **Files**:
  - `docs/testing/pool-node-hardware-test.md` (test results)
- **Dependencies**: #29
- **Tests**: Manual hardware testing with documented results

---

### Phase 2b: Valve Node (CircuitPython)

---

### Issue #31: Valve Node Project Setup

- **Phase**: 2b - Valve Node
- **Type**: Setup
- **Description**: Create CircuitPython project structure for Valve Node with configuration and shared library access.
- **Acceptance Criteria**:
  - [ ] code.py entry point stub
  - [ ] config.json template with all valve settings
  - [ ] lib/ symlink to ../shared
  - [ ] Settings match architecture defaults (9 min max fill, 2 hour window, etc.)
- **Files**:
  - `src/valve_node/code.py`
  - `src/valve_node/config.json`
  - `src/valve_node/lib` (symlink)
- **Dependencies**: #19
- **Tests**: code.py imports shared modules without error

---

### Issue #32: Fill Scheduler

- **Phase**: 2b - Valve Node
- **Type**: Core
- **Description**: Implement FillScheduler class for fill window logic per FR-VN-002.
- **Acceptance Criteria**:
  - [ ] FillScheduler.**init**(start_time, window_hours, check_interval)
  - [ ] start_time as "HH:MM" string (zero-padded)
  - [ ] is_within_window(current_time) returns bool
  - [ ] next_check_time() returns adafruit_datetime for next eligibility check
  - [ ] next_fill_time() returns adafruit_datetime for next window start
  - [ ] Check intervals are fixed from window start (09:00, 09:10, 09:20...)
- **Files**:
  - `src/valve_node/scheduler.py`
  - `tests/unit/test_scheduler.py`
- **Dependencies**: #31
- **Tests**: Unit tests for various time scenarios including edge cases

---

### Issue #33: Safety Interlocks

- **Phase**: 2b - Valve Node
- **Type**: Core
- **Description**: Implement SafetyInterlocks class for all fill safety checks per FR-VN-003.
- **Acceptance Criteria**:
  - [ ] SafetyInterlocks.**init**(config)
  - [ ] check_data_freshness(pool_msg, now) - verifies pool data within staleness threshold
  - [ ] Staleness threshold = poolNodeInterval × stalenessMultiplier (default 2)
  - [ ] check_water_level(pool_msg) - returns (ok, reason) based on floatSwitch
  - [ ] check_fill_window(scheduler, now) - returns (ok, reason)
  - [ ] check_all(pool_msg, scheduler) - runs all checks, returns first failure or (True, None)
  - [ ] All check methods return (ok: bool, reason: str) tuple
- **Files**:
  - `src/valve_node/safety.py`
  - `tests/unit/test_safety.py`
- **Dependencies**: #31
- **Tests**: Unit tests for each interlock condition and combinations

---

### Issue #34: Valve Controller Core

- **Phase**: 2b - Valve Node
- **Type**: Core
- **Description**: Implement ValveController class for GPIO control and state machine.
- **Acceptance Criteria**:
  - [ ] ValveController.**init**(config, cloud, logger)
  - [ ] GPIO D11 controls solenoid valve (HIGH = open, LOW = close)
  - [ ] State machine: idle → filling → idle
  - [ ] start_fill(trigger) opens valve, publishes fill_start message
  - [ ] stop_fill(reason) closes valve, publishes fill_stop message
  - [ ] check_fill_eligibility() uses SafetyInterlocks
  - [ ] Enforces max fill duration (default 9 minutes)
  - [ ] Continues active fill to max duration if pool data becomes stale
  - [ ] Logs warning when continuing without fresh data
- **Files**:
  - `src/valve_node/valve_controller.py`
  - `tests/unit/test_valve_controller.py`
- **Dependencies**: #32, #33
- **Tests**: Unit tests with mocked GPIO and cloud

---

> **Note**: Command Rate Limiting and Legacy Message Support were originally planned for Phase 2b but have been deferred to Phase 4+ (implement only if needed).

---

### Issue #35: Valve Node Integration

- **Phase**: 2b - Valve Node
- **Type**: Integration
- **Description**: Connect all Valve Node components and implement main loop with MQTT communication.
- **Acceptance Criteria**:
  - [ ] code.py initializes all components
  - [ ] Subscribes to gateway feed for pool_status and commands
  - [ ] Subscribes to valvestarttime feed for configuration
  - [ ] Publishes valve_status at configurable interval (default 60s)
  - [ ] Publishes outsidetemp to individual feed
  - [ ] Handles incoming commands (valve_start, valve_stop, set_config, device_reset)
  - [ ] Publishes command_response for all commands
  - [ ] Reads local DS18X20 temperature sensor
  - [ ] Implements watchdog (30s timeout)
  - [ ] Time resync every 12 hours to correct RTC drift (per architecture Section 4)
  - [ ] Socket resource management per NFR-REL-007:
    - Maximum 2 concurrent connections (MQTT + occasional HTTP)
    - Use adafruit_connection_manager for connection pooling
    - Close unused sockets after 60 seconds idle
- **Files**:
  - `src/valve_node/code.py` (updated)
- **Dependencies**: #34
- **Tests**: Integration test with simulator
- **Note**: Rate limiting and legacy message support deferred to Phase 4+
- **Note**: CircuitPython `wifi.radio.connect()` has no timeout parameter. Watchdog (30s) provides recovery from WiFi hangs.

---

### Issue #36: Valve Node Hardware Testing

- **Phase**: 2b - Valve Node
- **Type**: Test
- **Description**: Deploy Valve Node to real hardware and verify all safety interlocks.
- **Acceptance Criteria**:
  - [ ] Deploy to Feather ESP32-S3
  - [ ] Verify MQTT connection to nonprod feeds
  - [ ] Verify temperature sensor reading
  - [ ] Verify valve GPIO control (with relay/LED test)
  - [ ] Verify safety interlocks prevent fill when:
    - Pool data stale
    - Water level full
    - Outside fill window
  - [ ] Verify scheduled fill starts correctly
  - [ ] Verify manual fill command works
  - [ ] Verify max duration timeout stops fill
  - [ ] Integration test with Pool Node (or simulator)
- **Files**:
  - `docs/testing/valve-node-hardware-test.md` (test results)
- **Dependencies**: #35
- **Tests**: Manual hardware testing with documented results

---

### Phase 2c: Display Node (CircuitPython)

---

### Issue #37: Display Node Project Setup

- **Phase**: 2c - Display Node
- **Type**: Setup
- **Description**: Create CircuitPython project structure for Display Node with UI directory and font files.
- **Acceptance Criteria**:
  - [ ] code.py entry point stub
  - [ ] config.json template with display settings
  - [ ] lib/ symlink to ../shared
  - [ ] ui/ directory structure created
  - [ ] fonts/ directory with FreeSans PCF fonts from circuitpython-fonts bundle
  - [ ] adafruit_bitmap_font library installed
- **Font Source**:
  - Repository: <https://github.com/adafruit/circuitpython-fonts>
  - Format: PCF (Portable Compiled Format)
  - License: GNU FreeFont (GPL + Font Exception) - allows embedding
  - Install via: `circup install font_free_sans_18` or download from Releases
  - Required sizes determined during UI spike (#41)
- **Files**:
  - `src/display_node/code.py`
  - `src/display_node/config.json`
  - `src/display_node/lib` (symlink)
  - `src/display_node/ui/__init__.py`
  - `src/display_node/fonts/*.pcf` (FreeSans fonts from circuitpython-fonts)
- **Dependencies**: #19
- **Tests**: code.py imports shared modules without error

---

### Issue #38: Theme and Color Constants

- **Phase**: 2c - Display Node
- **Type**: Core
- **Description**: Implement theme module with color palette, font loading, and layout constants from UI design doc.
- **Acceptance Criteria**:
  - [ ] COLORS dict with all colors from UI design (background, text, accent, alert, etc.)
  - [ ] Font loading functions for Adafruit Free Sans fonts (8, 10, 12, 14, 18, 24pt)
  - [ ] Fallback to terminalio.FONT if custom fonts unavailable
  - [ ] SPACING dict with margins and padding values
  - [ ] Screen zone constants (header: 0-70, content: 70-205, chart: 205-320)
- **Files**:
  - `src/display_node/ui/theme.py`
  - `tests/unit/test_theme.py`
- **Dependencies**: #37
- **Tests**: Verify color values and font loading

---

### Issue #39: Base Widget Classes

- **Phase**: 2c - Display Node
- **Type**: Core
- **Description**: Implement base widget classes for text labels, buttons, progress bars, and confirmation dialogs.
- **Acceptance Criteria**:
  - [ ] TextLabel class with position, text, font, color, alignment
  - [ ] Button class with normal, pressed, disabled states
  - [ ] Button minimum touch target 44x44 pixels
  - [ ] ProgressBar class for battery display
  - [ ] ConfirmationDialog class with title, message, Yes/Cancel buttons
  - [ ] ConfirmationDialog modal overlay (dims background)
  - [ ] ConfirmationDialog returns user selection (confirmed/cancelled)
  - [ ] All widgets can add themselves to displayio Group
  - [ ] update() method for dynamic content
- **Files**:
  - `src/display_node/ui/widgets.py`
  - `tests/unit/test_widgets.py`
- **Dependencies**: #38
- **Tests**: Verify widget creation, state changes, and dialog interactions

---

### Issue #40: Touch Handler

- **Phase**: 2c - Display Node
- **Type**: Core
- **Description**: Implement touch input handling with STMPE610, calibration, and debouncing per FR-DN-008.
- **Acceptance Criteria**:
  - [ ] TouchHandler.**init**(touch_controller, screen_width, screen_height)
  - [ ] Configurable calibration values from config.json
  - [ ] get_touch() returns (x, y) tuple or None
  - [ ] 250ms debounce between registered taps
  - [ ] register_button(name, bounds) for hit testing
  - [ ] check_buttons() returns touched button name or None
  - [ ] Touch detection on press (not release) for faster response
- **Files**:
  - `src/display_node/ui/touch.py`
  - `tests/unit/test_touch.py`
- **Dependencies**: #37
- **Tests**: Unit tests with mocked touch controller

---

### Issue #41: Display Node UI Spike

- **Phase**: 2c - Display Node
- **Type**: Spike
- **Description**: Build minimal working dashboard on hardware before detailed screen implementation. Iterate layout based on actual hardware feedback per Kent Beck's "make it work first" principle.
- **Acceptance Criteria**:
  - [ ] Basic screen displays on TFT hardware
  - [ ] Touch input detected and coordinates logged
  - [ ] One screen with placeholder data (time, temperature)
  - [ ] Validate font rendering at different sizes
  - [ ] Validate color palette visibility on actual display
  - [ ] Document any adjustments needed to UI design based on hardware testing
- **Files**:
  - `src/display_node/ui/spike.py` (temporary, can be deleted after spike)
- **Dependencies**: #38, #39, #40
- **Tests**: Manual hardware testing - no automated tests for spike
- **Outcome**: Learnings inform #43-#46 implementation; UI design doc updated if needed

---

### Issue #42: Touch Calibration Utility

- **Phase**: 2c - Display Node
- **Type**: Tool
- **Description**: Create touch calibration utility that displays targets at screen corners, captures raw touch coordinates, calculates calibration values, and publishes them to the device's config feed. Default calibration is stored in local `config.json` and overridden by config feed values on boot.
- **Acceptance Criteria**:
  - [ ] Displays crosshair target at each corner (top-left, top-right, bottom-left, bottom-right)
  - [ ] User touches each target; utility captures raw STMPE610 coordinates
  - [ ] Calculates calibration coefficients (x_min, x_max, y_min, y_max) from raw values
  - [ ] Publishes updated config (with calibration values) to `config-display-node` feed
  - [ ] Outputs calibration values to serial console as backup
  - [ ] Instructions displayed on screen for each step
  - [ ] Can be run standalone or as boot option (hold button during boot)
- **Files**:
  - `src/display_node/tools/calibrate_touch.py`
- **Dependencies**: #40, #15
- **Tests**: Manual testing on hardware
- **Note**: Default calibration is stored in local `config.json`. On boot, Display Node fetches latest config from config feed via HTTP GET and merges over defaults. If network unavailable, defaults are used (touch calibration non-critical when display has no data).

---

### Issue #43: Main Dashboard Screen Layout

- **Phase**: 2c - Display Node
- **Type**: Core
- **Description**: Implement main dashboard screen visual layout per UI design document (informed by spike findings). Touch zones for navigation are added by each destination screen's issue.
- **Acceptance Criteria**:
  - [ ] Header zone: date (aqua), time (cornsilk 22pt), AM/PM, FILLING indicator (blue)
  - [ ] Content zone: Outside/Pool/Inside temperatures with labels
  - [ ] Right side: Next Fill time, Needs Water status, battery voltage, humidity
  - [ ] Chart zone: 24-hour temperature sparkline per UI design (chart zone 205-320px)
  - [ ] Sparkline displays pool temperature history fetched from cloud API
  - [ ] Sparkline downsamples 288 data points (5-min intervals) to 240 pixels (full screen width)
  - [ ] Sparkline min/max values displayed on right edge per UI design
  - [ ] Sparkline uses 3-point moving average smoothing per FR-DN-003
  - [ ] Fallback to "No Data" message if historical data unavailable
  - [ ] update(state) refreshes all displayed values
- **Files**:
  - `src/display_node/ui/screens.py`
  - `src/display_node/ui/sparkline.py` (new - sparkline rendering)
  - `tests/unit/test_main_dashboard.py`
  - `tests/unit/test_sparkline.py`
- **Dependencies**: #41
- **Tests**: Verify layout renders correctly with mock state data; verify sparkline renders with test data
- **Note**: This issue covers the main dashboard 24-hour sparkline. The separate Historical Screen with 7d/30d range selection is covered by #56.

---

### Issue #44: Pool Node Detail Screen

- **Phase**: 2c - Display Node
- **Type**: Core
- **Description**: Implement Pool Node detail screen with temperature, water level, battery, and message timing. Includes navigation from main dashboard.
- **Acceptance Criteria**:
  - [ ] Register touch zone on main dashboard: pool row → Pool detail screen
  - [ ] Back button (←) in header with touch zone → main dashboard
  - [ ] Large temperature display with trend (previous reading, delta)
  - [ ] Water level status: "NEEDS WATER" (orange) or "OK" (green)
  - [ ] Battery bar with percentage fill and voltage text
  - [ ] Message status section: last received timestamp, reporting interval, message age
  - [ ] Message age color-coded (green if fresh, orange if stale)
- **Files**:
  - `src/display_node/ui/screens.py` (updated)
  - `tests/unit/test_pool_detail.py`
- **Dependencies**: #43
- **Tests**: Verify display elements, touch zone on main dashboard, and back navigation

---

### Issue #45: Valve Node Detail Screen

- **Phase**: 2c - Display Node
- **Type**: Core
- **Description**: Implement Valve Node detail screen with fill status, controls, and confirmation dialog. Includes navigation from main dashboard.
- **Acceptance Criteria**:
  - [ ] Register touch zone on main dashboard: outside row → Valve detail screen
  - [ ] Back button in header with touch zone → main dashboard
  - [ ] Outside temperature display
  - [ ] Fill status section with indicator dot (green=IDLE, blue=FILLING)
  - [ ] When IDLE: Next fill time, countdown, window, max duration
  - [ ] When FILLING: Elapsed time, remaining time, blue border
  - [ ] START FILL button (disabled when filling)
  - [ ] STOP FILL button (always enabled)
  - [ ] START FILL shows confirmation dialog before sending command
  - [ ] Last fill info and message timestamp
- **Files**:
  - `src/display_node/ui/screens.py` (updated)
  - `tests/unit/test_valve_detail.py`
- **Dependencies**: #43, #39
- **Tests**: Verify layout, touch zones, button states, and confirmation dialog

---

### Issue #46: Settings Screen

- **Phase**: 2c - Display Node
- **Type**: Core
- **Description**: Implement Settings screen with system info and action buttons. Includes navigation from main dashboard.
- **Acceptance Criteria**:
  - [ ] Register touch zone on main dashboard: time area → Settings screen
  - [ ] Back button in header with touch zone → main dashboard
  - [ ] System info: Environment, Device ID, WiFi status, IP, signal strength
  - [ ] Status: Last sync, uptime, error count, free memory
  - [ ] REFRESH ALL button - triggers data re-fetch
  - [ ] RESET DEVICE button with confirmation dialog
- **Files**:
  - `src/display_node/ui/screens.py` (updated)
  - `tests/unit/test_settings.py`
- **Dependencies**: #43, #39
- **Tests**: Verify layout, touch zones, and button actions

---

### Issue #47: Stale Data Indicators

- **Phase**: 2c - Display Node
- **Type**: Core
- **Description**: Implement stale data visual indicators per FR-DN-004.
- **Acceptance Criteria**:
  - [ ] 30-minute threshold (configurable via staleDataIndicatorThreshold)
  - [ ] Main dashboard: Amber background (#3C2800) on stale row
  - [ ] Warning icon (⚠) before label on stale row
  - [ ] Detail screens: Warning banner at top, orange message age text
  - [ ] Check staleness on each render cycle (every 30 seconds)
  - [ ] Staleness calculated from message timestamp vs current time
- **Files**:
  - `src/display_node/ui/screens.py` (updated)
  - `tests/unit/test_stale_indicators.py`
- **Dependencies**: #43
- **Tests**: Verify indicator appears at correct threshold

---

### Issue #48: Non-Production Indicator

- **Phase**: 2c - Display Node
- **Type**: Core
- **Description**: Implement 1-pixel orange border when environment != "prod" per NFR-ENV-005.
- **Acceptance Criteria**:
  - [ ] Check environment from config on startup
  - [ ] Draw 1px orange border on all screen edges if nonprod
  - [ ] Border visible on all screens
  - [ ] No border in prod environment
- **Files**:
  - `src/display_node/ui/theme.py` (updated)
  - `src/display_node/ui/screens.py` (updated)
- **Dependencies**: #38
- **Tests**: Verify border presence/absence based on environment

---

### Issue #49: Burn-In Prevention

- **Phase**: 2c - Display Node
- **Type**: Core
- **Description**: Implement display burn-in prevention cycle per FR-DN-007.
- **Acceptance Criteria**:
  - [ ] Idle detection after configurable period (default 5 minutes)
  - [ ] Rotate display through 0°, 90°, 180°, 270° orientations
  - [ ] Cycle through background colors (black, white, red, blue)
  - [ ] Each color displayed for configurable duration (default 7 seconds)
  - [ ] Abort cycle immediately if touch detected during rotation, return to normal display
  - [ ] Return to normal display after cycle completes
  - [ ] Resume idle timer after returning to normal
- **Files**:
  - `src/display_node/ui/burn_in.py`
  - `tests/unit/test_burn_in.py`
- **Dependencies**: #40
- **Tests**: Verify timing and touch interrupt

---

### Issue #50: Local Sensor Reading (AHTx0)

- **Phase**: 2c - Display Node
- **Type**: Core
- **Description**: Implement local temperature and humidity sensor reading per FR-DN-006.
- **Acceptance Criteria**:
  - [ ] Initialize AHTx0 over I2C
  - [ ] read_local_sensors() returns temperature (F) and humidity (%)
  - [ ] Temperature converted to Fahrenheit
  - [ ] Retry with backoff on I2C errors
  - [ ] Return null values on complete failure
  - [ ] Publish display_status message at configurable interval (default 60s)
  - [ ] Publish insidetemp to individual feed
- **Files**:
  - `src/display_node/local_sensors.py`
  - `tests/unit/test_local_sensors.py`
- **Dependencies**: #37
- **Tests**: Unit test with mocked I2C

---

### Issue #51: Dashboard State Management

- **Phase**: 2c - Display Node
- **Type**: Core
- **Description**: Implement state management for tracking device data and staleness.
- **Acceptance Criteria**:
  - [ ] DeviceState class tracks latest message per device type
  - [ ] Stores pool_status, valve_status, and timestamps
  - [ ] calculate_staleness(device_type) returns age in seconds
  - [ ] is_stale(device_type, threshold) returns bool
  - [ ] update_from_message(message) updates appropriate state
  - [ ] get_display_data() returns dict formatted for screen rendering
- **Files**:
  - `src/display_node/state.py`
  - `tests/unit/test_state.py`
- **Dependencies**: #37
- **Tests**: Unit tests for state updates and staleness

---

### Issue #52: Dashboard Controller - Message Handling

- **Phase**: 2c - Display Node
- **Type**: Integration
- **Description**: Implement Dashboard controller for receiving and processing MQTT messages.
- **Acceptance Criteria**:
  - [ ] Dashboard.**init**(config, cloud, display, touch)
  - [ ] Subscribes to gateway feed for all status messages
  - [ ] Fetches latest gateway value on startup before subscribing
  - [ ] handle_message(message) updates state and refreshes display
- **Files**:
  - `src/display_node/dashboard.py`
  - `tests/unit/test_dashboard_messages.py`
- **Dependencies**: #50, #51
- **Tests**: Verify message subscription, initial fetch, and state updates

---

### Issue #53: Dashboard Controller - Commands and Navigation

- **Phase**: 2c - Display Node
- **Type**: Integration
- **Description**: Extend Dashboard controller with command sending and screen navigation.
- **Acceptance Criteria**:
  - [ ] send_command(command, target, params) publishes command message
  - [ ] Command feedback: pending spinner, success checkmark (2s), failure X (2s auto-dismiss)
  - [ ] 5-second timeout for command acknowledgment
  - [ ] Screen navigation: main → pool/valve/settings → main
  - [ ] Idle timeout (60s) returns to main dashboard
- **Files**:
  - `src/display_node/dashboard.py` (updated)
  - `tests/unit/test_dashboard_commands.py`
  - `tests/unit/test_dashboard_navigation.py`
- **Dependencies**: #52
- **Tests**: Verify command publishing with feedback, navigation flow, and idle timeout

---

### Issue #54: Display Node Integration

- **Phase**: 2c - Display Node
- **Type**: Integration
- **Description**: Wire all Display Node components together in code.py with full functionality.
- **Acceptance Criteria**:
  - [ ] code.py initializes display, touch, cloud, config, logger
  - [ ] Creates Dashboard controller
  - [ ] Main loop: handle MQTT, check touch, update display, read local sensors
  - [ ] Implements watchdog (120s timeout)
  - [ ] Feeds watchdog at appropriate intervals
  - [ ] Handles screen transitions
  - [ ] Time display updates every second
  - [ ] Triggers burn-in prevention after idle timeout
  - [ ] Time resync every 12 hours to correct RTC drift (per architecture Section 4)
  - [ ] Socket resource management per NFR-REL-007:
    - Maximum 2 concurrent connections (MQTT + occasional HTTP)
    - Use adafruit_connection_manager for connection pooling
    - Close unused sockets after 60 seconds idle
- **Files**:
  - `src/display_node/code.py` (updated)
- **Dependencies**: #43, #44, #45, #46, #47, #48, #49, #50, #51, #52, #53
- **Tests**: Integration test with simulators
- **Note**: CircuitPython `wifi.radio.connect()` has no timeout parameter. Watchdog (120s) provides recovery from WiFi hangs.

---

### Issue #55: Display Node Hardware Testing

- **Phase**: 2c - Display Node
- **Type**: Test
- **Description**: Deploy Display Node to real hardware and verify all screens and touch interaction.
- **Acceptance Criteria**:
  - [ ] Deploy to Feather ESP32-S2 with TFT FeatherWing
  - [ ] Calibrate touchscreen and update config.json
  - [ ] Verify main dashboard displays correctly
  - [ ] Verify all navigation touch zones work
  - [ ] Verify Pool detail screen updates from pool_status
  - [ ] Verify Valve detail screen updates from valve_status
  - [ ] Verify START FILL command sends to Valve Node
  - [ ] Verify stale data indicator appears after 30 minutes
  - [ ] Verify burn-in prevention activates after 5 minutes
  - [ ] Integration test with Pool and Valve nodes
- **Files**:
  - `docs/testing/display-node-hardware-test.md` (test results)
- **Dependencies**: #54
- **Tests**: Manual hardware testing with documented results

---

### Issue #56: Historical Screen

- **Phase**: 2c - Display Node
- **Type**: Core
- **Description**: Implement Historical Screen with 24h/7d/30d range selection per UI design. Accessible from main dashboard chart zone. The 24h view reuses the sparkline. The 7d and 30d views display whisker charts with client-side daily aggregation from 60-minute resolution data.
- **Acceptance Criteria**:
  - [ ] Register touch zone on main dashboard chart area → Historical Screen
  - [ ] Back button (←) in header with touch zone → main dashboard
  - [ ] Range selector: three touch buttons (24h, 7d, 30d) with active state indicator
  - [ ] 24h view: displays sparkline (reuses sparkline rendering from #43)
  - [ ] 7d view: fetches 60-min resolution data (168 points), calculates daily min/max/avg client-side
  - [ ] 30d view: fetches 60-min resolution data (720 points), calculates daily min/max/avg client-side
  - [ ] Whisker chart renders daily min (bottom cap), max (top cap), average (center square)
  - [ ] 7d whisker chart: 7 bars with day labels (M, T, W, T, F, S, S)
  - [ ] 30d whisker chart: 30 bars with date labels (1, 8, 15, 22, 30)
  - [ ] Chart uses full screen width (240px) per UI design
  - [ ] Statistics section below chart: temperature range (min-max), average
- **Data Fetching**:
  - 7d: `GET /feeds/{feed}/data/chart?hours=168&resolution=60` → 168 data points (~2 KB)
  - 30d: `GET /feeds/{feed}/data/chart?hours=720&resolution=60` → 720 data points (~8 KB)
  - Group by day (24 points/day), calculate min/max/avg per day client-side
- **Files**:
  - `src/display_node/ui/screens.py` (updated - add HistoricalScreen)
  - `src/display_node/ui/whisker_chart.py` (new - whisker chart rendering)
  - `src/display_node/ui/history_data.py` (new - cloud API fetch + daily aggregation)
  - `tests/unit/test_historical_screen.py`
- **Dependencies**: #43
- **Tests**: Verify range switching, whisker chart rendering, API data fetching, daily aggregation calculation, navigation

---

### Phase 3: Simulators & Testing

---

### Issue #57: Simulator Common Utilities

- **Phase**: 3 - Simulators
- **Type**: Core
- **Description**: Create shared utilities for all node simulators.
- **Acceptance Criteria**:
  - [ ] CLI argument parsing (--interval, --environment, --device-id)
  - [ ] Environment configuration loading
  - [ ] Simulated value generators (random temperature, battery drain, etc.)
  - [ ] Device ID suffix (-sim) enforcement
  - [ ] Common logging setup
- **Files**:
  - `src/simulators/__init__.py`
  - `src/simulators/common.py`
  - `tests/unit/test_simulator_common.py`
- **Dependencies**: #19
- **Tests**: Unit tests for argument parsing and value generation

---

### Issue #58: Pool Node Simulator

- **Phase**: 3 - Simulators
- **Type**: Core
- **Description**: Implement Pool Node simulator that generates pool_status messages.
- **Acceptance Criteria**:
  - [ ] Runs as: `python -m poolio.simulators.pool_node --interval 120`
  - [ ] Generates pool_status at configurable interval
  - [ ] Configurable initial values (temperature, water level, battery)
  - [ ] Scenario scripting: water level can drop over time
  - [ ] Battery can drain over time
  - [ ] Publishes to gateway feed using AdafruitIO client
  - [ ] Device ID: pool-node-001-sim
- **Files**:
  - `src/simulators/pool_node.py`
  - `tests/unit/test_pool_simulator.py`
- **Dependencies**: #57
- **Tests**: Verify message format and timing

---

### Issue #59: Valve Node Simulator

- **Phase**: 3 - Simulators
- **Type**: Core
- **Description**: Implement Valve Node simulator that responds to commands and generates status.
- **Acceptance Criteria**:
  - [ ] Runs as: `python -m poolio.simulators.valve_node`
  - [ ] Generates valve_status at configurable interval
  - [ ] Subscribes to gateway and processes pool_status
  - [ ] Responds to valve_start/valve_stop commands
  - [ ] Simulates fill operations (duration, stop reasons)
  - [ ] Applies safety interlock logic
  - [ ] Generates fill_start/fill_stop events
  - [ ] Publishes command_response
  - [ ] Device ID: valve-node-001-sim
- **Files**:
  - `src/simulators/valve_node.py`
  - `tests/unit/test_valve_simulator.py`
- **Dependencies**: #57
- **Tests**: Verify command handling and event generation

---

### Issue #60: Display Node Simulator

- **Phase**: 3 - Simulators
- **Type**: Core
- **Description**: Implement Display Node simulator for message logging and debugging.
- **Acceptance Criteria**:
  - [ ] Runs as: `python -m poolio.simulators.display_node`
  - [ ] Subscribes to all status messages on gateway
  - [ ] Logs received messages with formatting
  - [ ] Optional text-based status display (table format)
  - [ ] Can simulate sending commands to other devices
  - [ ] Device ID: display-node-001-sim
- **Files**:
  - `src/simulators/display_node.py`
- **Dependencies**: #57
- **Tests**: Verify subscription and logging

---

### Issue #61: Integration Test Suite - Normal Flow

- **Phase**: 3 - Simulators
- **Type**: Test
- **Description**: Create integration tests for normal system operation flows.
- **Acceptance Criteria**:
  - [ ] Test: Pool → Valve → Display message propagation
  - [ ] Test: Scheduled fill operation (water low, in window, fresh data)
  - [ ] Test: Float switch stops fill when full
  - [ ] Test: Max duration timeout stops fill
  - [ ] Tests use MockBackend, not real Adafruit IO
  - [ ] Each test documented with scenario description
- **Files**:
  - `tests/integration/test_normal_flow.py`
- **Dependencies**: #58, #59, #60
- **Tests**: All integration tests pass

---

### Issue #62: Integration Test Suite - Error Scenarios

- **Phase**: 3 - Simulators
- **Type**: Test
- **Description**: Create integration tests for error and edge case scenarios from architecture.md.
- **Acceptance Criteria**:
  - [ ] Test: Stale data during fill - continues to max duration
  - [ ] Test: Network disconnect during command - timeout handling
  - [ ] Test: Sensor failure - null values sent, operation continues
  - [ ] All tests use MockBackend
- **Files**:
  - `tests/integration/test_error_scenarios.py`
- **Dependencies**: #58, #59
- **Tests**: All error scenario tests pass
- **Note**: Rate limit testing deferred to Phase 4+

---

### Issue #63: Integration Test Suite - Edge Cases

- **Phase**: 3 - Simulators
- **Type**: Test
- **Description**: Create integration tests for edge cases and boundary conditions.
- **Acceptance Criteria**:
  - [ ] Test: Clock drift correction on time sync
  - [ ] Test: Watchdog reset recovery (simulated)
  - [ ] Test: Message validation failures (malformed JSON, missing fields)
  - [ ] Test: Unsupported message version handling
- **Files**:
  - `tests/integration/test_edge_cases.py`
- **Dependencies**: #58, #59
- **Tests**: All edge case tests pass
- **Note**: Legacy message format testing deferred to Phase 4+

---

### Phase 4: Deployment

---

### Issue #64: Adafruit IO Feed Setup - Nonprod

- **Phase**: 4 - Deployment
- **Type**: Setup
- **Description**: Create nonprod feed group and all feeds in Adafruit IO.
- **Acceptance Criteria**:
  - [ ] Create poolio-nonprod feed group
  - [ ] Create feeds: gateway, pooltemp, outsidetemp, insidetemp, poolnodebattery
  - [ ] Create feeds: poolvalveruntime, valvestarttime, config, events
  - [ ] Configure feed permissions (gateway requires auth for write)
  - [ ] Document feed URLs and structure
- **Files**:
  - `docs/deployment/adafruit-io-nonprod-setup.md`
- **Dependencies**: None
- **Tests**: Verify feeds accessible via API

---

### Issue #65: Deploy Script for CircuitPython

- **Phase**: 4 - Deployment
- **Type**: Setup
- **Description**: Create deployment script for CircuitPython nodes per architecture.md Deployment section.
- **Acceptance Criteria**:
  - [ ] scripts/deploy_circuitpy.sh takes node_type and environment args
  - [ ] Detects CIRCUITPY mount point (macOS and Linux)
  - [ ] Copies shared libraries to lib/
  - [ ] Copies node-specific files
  - [ ] Copies environment-specific config.json
  - [ ] Preserves existing settings.toml (secrets)
  - [ ] Outputs completion message
- **Files**:
  - `scripts/deploy_circuitpy.sh`
  - `docs/deployment/circuitpy-deployment.md`
- **Dependencies**: #19
- **Tests**: Script runs successfully on test device

---

### Issue #66: Configuration Files - Nonprod

- **Phase**: 4 - Deployment
- **Type**: Setup
- **Description**: Create nonprod configuration files for all nodes.
- **Acceptance Criteria**:
  - [ ] config/nonprod/valve_node.json with nonprod settings
  - [ ] config/nonprod/display_node.json with nonprod settings
  - [ ] config/nonprod/settings.toml.template with placeholders
  - [ ] debugLogging: true for nonprod
  - [ ] feedGroup: "poolio-nonprod"
  - [ ] All configurable values documented
- **Files**:
  - `config/nonprod/valve_node.json`
  - `config/nonprod/display_node.json`
  - `config/nonprod/settings.toml.template`
- **Dependencies**: #64
- **Tests**: Config files validate against schema

---

### Issue #67: Pool Node Nonprod Build and Deploy

- **Phase**: 4 - Deployment
- **Type**: Integration
- **Description**: Build and deploy Pool Node to nonprod environment.
- **Acceptance Criteria**:
  - [ ] Build with `pio run -e nonprod`
  - [ ] Flash to device with `pio run -e nonprod --target upload`
  - [ ] Configure secrets via serial or NVS
  - [ ] Verify WiFi connection
  - [ ] Verify data appears in poolio-nonprod feeds
  - [ ] Document deployment steps
- **Files**:
  - `docs/deployment/pool-node-deployment.md`
- **Dependencies**: #30, #64
- **Tests**: Data visible in Adafruit IO nonprod

---

### Issue #68: Valve Node Nonprod Deployment

- **Phase**: 4 - Deployment
- **Type**: Integration
- **Description**: Deploy Valve Node to nonprod environment.
- **Acceptance Criteria**:
  - [ ] Run deploy script: `./scripts/deploy_circuitpy.sh valve_node nonprod`
  - [ ] Configure settings.toml with nonprod credentials
  - [ ] Verify MQTT connection to nonprod feeds
  - [ ] Verify valve_status messages appear in gateway
  - [ ] Test manual command via Adafruit IO dashboard
  - [ ] Document deployment steps
- **Files**:
  - `docs/deployment/valve-node-deployment.md`
- **Dependencies**: #36, #65, #66
- **Tests**: Commands processed correctly

---

### Issue #69: Display Node Nonprod Deployment

- **Phase**: 4 - Deployment
- **Type**: Integration
- **Description**: Deploy Display Node to nonprod environment.
- **Acceptance Criteria**:
  - [ ] Run deploy script: `./scripts/deploy_circuitpy.sh display_node nonprod`
  - [ ] Configure settings.toml with nonprod credentials
  - [ ] Copy font files to lib/
  - [ ] Calibrate touchscreen and update config.json
  - [ ] Verify all screens display correctly
  - [ ] Verify nonprod orange border visible
  - [ ] Document deployment steps
- **Files**:
  - `docs/deployment/display-node-deployment.md`
- **Dependencies**: #55, #65, #66
- **Tests**: All screens functional

---

### Issue #70: Nonprod System Integration Test

- **Phase**: 4 - Deployment
- **Type**: Test
- **Description**: Verify all three nodes communicate correctly in nonprod environment.
- **Acceptance Criteria**:
  - [ ] Pool Node data appears on Display Node
  - [ ] Valve Node status appears on Display Node
  - [ ] Manual fill command from Display reaches Valve
  - [ ] Scheduled fill operation completes successfully
  - [ ] Float switch (simulated) stops fill
  - [ ] Stale data indicator appears when Pool Node stopped
  - [ ] Document all test scenarios and results
- **Files**:
  - `docs/testing/nonprod-integration-test.md`
- **Dependencies**: #67, #68, #69
- **Tests**: All integration scenarios pass

---

### Issue #71: Nonprod 1-Week Stability Test

- **Phase**: 4 - Deployment
- **Type**: Test
- **Description**: Run system continuously for 1 week to verify stability.
- **Acceptance Criteria**:
  - [ ] All three nodes running for 7 days
  - [ ] Monitor for watchdog resets (target: zero)
  - [ ] Monitor for memory leaks (free memory trend)
  - [ ] Verify scheduled fills execute daily
  - [ ] Check for missed messages or data gaps
  - [ ] Document any anomalies or issues
  - [ ] Create stability report
- **Files**:
  - `docs/testing/nonprod-stability-report.md`
- **Dependencies**: #70
- **Tests**: Zero critical issues during stability test

---

### Issue #72: Adafruit IO Feed Setup - Production

- **Phase**: 4 - Deployment
- **Type**: Setup
- **Description**: Create production feed group and configure legacy feed compatibility.
- **Acceptance Criteria**:
  - [ ] Create poolio feed group (no prefix)
  - [ ] Create all feeds matching nonprod structure
  - [ ] Configure legacy feed aliases if needed
  - [ ] Set up legacy feeds for backward compatibility (per architecture.md)
  - [ ] Document migration path from legacy feeds
- **Files**:
  - `docs/deployment/adafruit-io-prod-setup.md`
- **Dependencies**: #71
- **Tests**: Verify feeds accessible via API

---

### Issue #73: Configuration Files - Production

- **Phase**: 4 - Deployment
- **Type**: Setup
- **Description**: Create production configuration files for all nodes.
- **Acceptance Criteria**:
  - [ ] config/prod/valve_node.json with production settings
  - [ ] config/prod/display_node.json with production settings
  - [ ] config/prod/settings.toml.template with placeholders
  - [ ] debugLogging: false for production
  - [ ] feedGroup: "poolio" (no prefix)
  - [ ] legacyFeedsEnabled: true for backward compatibility
- **Files**:
  - `config/prod/valve_node.json`
  - `config/prod/display_node.json`
  - `config/prod/settings.toml.template`
- **Dependencies**: #72
- **Tests**: Config files validate against schema

---

### Issue #74: Pre-Production Checklist

- **Phase**: 4 - Deployment
- **Type**: Docs
- **Description**: Document pre-deployment verification checklist and rollback procedure.
- **Acceptance Criteria**:
  - [ ] Checklist per NFR-ENV-007 (environment, API key, feeds, hardware, logging)
  - [ ] Rollback procedure documented
  - [ ] Git tag created for release (e.g., v1.0.0)
  - [ ] Monitoring plan documented
  - [ ] Emergency contact/escalation documented
- **Files**:
  - `docs/deployment/pre-production-checklist.md`
  - `docs/deployment/rollback-procedure.md`
- **Dependencies**: #71, #73
- **Tests**: Checklist reviewed by team

---

### Issue #75: Production Deployment

- **Phase**: 4 - Deployment
- **Type**: Integration
- **Description**: Deploy all nodes to production environment.
- **Acceptance Criteria**:
  - [ ] Complete pre-production checklist
  - [ ] Deploy Pool Node with prod build
  - [ ] Deploy Valve Node with prod config
  - [ ] Deploy Display Node with prod config
  - [ ] Verify no nonprod border on Display
  - [ ] Verify all feeds receiving data
  - [ ] Verify scheduled fill operation
  - [ ] Document deployment time and any issues
- **Files**:
  - `docs/deployment/production-deployment-log.md`
- **Dependencies**: #74
- **Tests**: All nodes operational in production

---

### Issue #76: Production Monitoring (48 hours)

- **Phase**: 4 - Deployment
- **Type**: Test
- **Description**: Monitor production system for 48 hours post-deployment.
- **Acceptance Criteria**:
  - [ ] No watchdog resets
  - [ ] No unexpected errors in events feed
  - [ ] Scheduled fills execute correctly
  - [ ] Data freshness maintained
  - [ ] Memory usage stable
  - [ ] Document any issues observed
  - [ ] Create monitoring summary
- **Files**:
  - `docs/deployment/production-monitoring-48h.md`
- **Dependencies**: #75
- **Tests**: System stable for 48 hours

---

### Issue #77: Post-Deployment Documentation

- **Phase**: 4 - Deployment
- **Type**: Docs
- **Description**: Update all documentation with deployment status and operational procedures.
- **Acceptance Criteria**:
  - [ ] Update README.md with current deployment status
  - [ ] Create operational runbook (common tasks, troubleshooting)
  - [ ] Document known issues and workarounds
  - [ ] Update architecture.md with any deviations from plan
  - [ ] Archive nonprod test results
- **Files**:
  - `README.md` (updated)
  - `docs/operations/runbook.md`
  - `docs/operations/known-issues.md`
- **Dependencies**: #76
- **Tests**: Documentation reviewed

---

### Phase 4+: Deferred Features (Implement Only If Needed)

These issues were deferred per Kent Beck's principles ("no just-in-case code", "fewest elements"). Implement only when production experience proves they are necessary. GitHub issues will be created when/if implementation is decided.

- **4.15: Full JSON Schema Validation** - Implement only if simple validation proves insufficient
- **4.16: Command Rate Limiting** - Implement only if command abuse detected in production
- **4.17: Legacy Message Support** - Implement only if migration requires parallel operation with legacy nodes
- **4.18: Credential Provisioning Captive Portal** - Implement only when end-user deployment requires it

---

## Dependency Graph

```text
Phase 1: Foundation
=========================================
[#9] ─┬─> [#10] ──> [#11] ──> [#12] ─┐
      │                              │
      ├─> [#13] ──> [#14] ──────────┤
      │        └──> [#15] ──────────┤
      │                              │
      ├─> [#16] ────────────────────┤
      │                              │
      ├─> [#17] ──> [#18] ─────────┤
      │                              │
      └──────────────────────────────┴──> [#19]

Phase 2a: Pool Node (can parallel with 2b, 2c)
=========================================
[#20] ──> [#21] ──> [#22] ──> [#23] ──> [#24]
  │         │                             │
  └─────────┴──> [#25]                    │
  │              [#26]                    │
  │              [#27]                    │
  │                                       │
  └──> [#28] ─────────────────────────────┘
                                          │
       [#25] + [#26] + [#27] + [#28] ─────┴──> [#29] ──> [#30]

Phase 2b: Valve Node (can parallel with 2a, 2c)
=========================================
[#19] ──> [#31] ──> [#32] ──┐
                    [#33] ──┼──> [#34] ──> [#35] ──> [#36]

Phase 2c: Display Node (can parallel with 2a, 2b)
=========================================
[#19] ──> [#37] ──> [#38] ──> [#39] ──> [#40] ──> [#41] (spike)
                      │                     │            │
                      └─────────────────────┴────────────┘
                                                         │
                                                      [#43]
                             │
                      ┌──────┴──────┬──────────────┐
                      ▼             ▼              ▼
                   [#44]        [#45]         [#46]
                      │             │              │
                      └─────────────┴──────────────┘
                                    │
                             ┌──────┴──────┐
                             ▼             ▼
                          [#47]        [#48]
                             │
                          [#49]
                             │
[#37] ────────────────────> [#50]
                             │
                          [#51]
                             │
                          [#52]
                             │
                         [#53] ◄──────────────────────┐
                             │                          │
                          [#54] ──> [#55]             │
                                                         │
Phase 3: Simulators                                      │
=========================================                │
[#19] ──> [#57] ──> [#58] ─┐                           │
                   [#59] ──┼──> [#61] ──> [#62] ──> [#63]
                   [#60] ──┘                            │
                                                         │
Phase 4: Deployment                                      │
=========================================                │
[#64] ───────────────────────────────────────────────────┘
  │
  └──> [#65] ──> [#66]
         │         │
         ├─────────┼──> [#67] ──┐
         │         │            │
         │         ├──> [#68] ──┼──> [#70] ──> [#71]
         │         │            │
         │         └──> [#69] ──┘
         │
         └──> [#72] ──> [#73] ──> [#74] ──> [#75] ──> [#76] ──> [#77]
```

---

## Critical Path

The minimum timeline is determined by this sequence:

**Phase 1 → Phase 2 → Phase 3 → Phase 4**

Within phases, the critical paths are:

**Phase 1**: `#9 → #10 → #11 → #12 → #19` (message protocol must be complete first)

**Phase 2**: `#37 → #38 → #39 → #40 → #43 → ... → #55` (Display Node has most issues)

**Phase 4**: `#64 → #66 → #68 → #70 → #71 → #72 → ... → #77` (sequential deployment steps)

**Parallelization Opportunities**:

- Phase 2a, 2b, 2c can all run in parallel after Phase 1 completes
- Within Phase 1: Cloud clients (#13-#15) parallel with Config/Logging (#16-#18)
- Phase 3 simulators (#58-#60) can develop in parallel

---

## Risk Items

| Risk | Impact | Mitigation |
|------|--------|------------|
| C++ message library incompatibility | Pool Node messages rejected by other nodes | #61 includes cross-language validation test |
| CircuitPython memory constraints | Display Node crashes or hangs | Use memory profiling, minimize displayio groups |
| STMPE610 touch calibration | Inaccurate touch zones | Store calibration in config.json, provide calibration utility |
| ESP32 WiFi reliability | Dropped connections, missed messages | Implement reconnection with backoff (#23, #35) |
| Deep sleep affecting reliability | Pool Node fails to wake or transmit | 24-hour stability test (#30), watchdog protection |
| Adafruit IO rate limits | Throttled data, missed updates | Monitor rate usage, subscribe to throttle topic |
| Font file size | Display Node storage exceeded | Use subset fonts, verify available space |

---

## Open Questions

All questions from architecture.md Section "Resolved Questions" have been addressed:

1. ~~Pump Node Communication Protocol~~ - Deferred to Phase 5+
2. ~~Display Node Touch UI Design~~ - Covered by display-node-ui-design.md
3. ~~HomeKit Service Types~~ - Deferred to Phase 5
4. ~~C++ Shared Library Strategy~~ - Independent implementation (#21)
5. ~~OTA Updates~~ - Deferred to future phases
6. ~~Device Discovery~~ - Static configuration for MVP

---

## Summary

| Metric | Count |
|--------|-------|
| **Total Issues (MVP)** | 67 |
| Phase 1 (Foundation) | 11 (#9-#19) |
| Phase 2a (Pool Node) | 11 (#20-#30) |
| Phase 2b (Valve Node) | 6 (#31-#36) |
| Phase 2c (Display Node) | 20 (#37-#56) |
| Phase 3 (Simulators) | 7 (#57-#63) |
| Phase 4 (Deployment) | 14 (#64-#77) |
| Phase 4+ (Deferred) | 4 (not created) |
| **Critical Path Length** | ~25 issues (Phase 1 + longest Phase 2 + Phase 3-4) |
| **Parallelizable Work** | Phase 2a/2b/2c, Phase 3 simulators |

**Kent Beck Alignment Notes**:

- Deferred 4 features (rate limiting, legacy support, full schema validation, captive portal provisioning) per "no just-in-case code"
- Added UI spike per "make it work first"
- Defer abstractions: CloudBackend base class extracted only when needed (#15)
- Simplified validation: required-field checks plus size/freshness limits
- TDD workflow (red/green/refactor) documented for all issues
- Split large integration issues (#52 → #52 + #53) for smaller increments
- Touch zone navigation tied to destination screen issues for cohesive feature delivery
- Credential provisioning uses development shortcut (settings.toml/secrets.h) for MVP
