# Pre-Implementation Review: Issues to Resolve

> **Created:** 2026-01-26
> **Status:** In Progress
> **Purpose:** Track and resolve documentation gaps, inconsistencies, and ambiguities before beginning Phase 1 implementation.

## Background

This document captures issues identified during a comprehensive review of the three core project documents:

- **`requirements.md`** - Functional and non-functional requirements, JSON message schemas, reliability specifications
- **`architecture.md`** - System design, component interfaces, CircuitPython patterns, deployment procedures
- **`implementation-plan.md`** - 67 MVP issues across 4 phases, dependencies, acceptance criteria

The Poolio system is a distributed IoT pool automation platform with three node types:

| Node | Purpose | Language | Communication |
|------|---------|----------|---------------|
| Pool Node | Battery-powered sensor (temp, water level, battery) | C++ | HTTPS POST |
| Valve Node | Fill valve controller with scheduling | CircuitPython | MQTT bidirectional |
| Display Node | Touchscreen dashboard with controls | CircuitPython | MQTT + HTTP |

All nodes communicate via Adafruit IO (cloud message broker) using a standardized JSON message protocol.

**Adafruit IO Account:** IO+ tier ($10/month)
- 60 days data retention
- 60 data points/minute rate limit
- Unlimited feeds and dashboards

---

## Issue Tracking

### Summary

| Priority | Total | Resolved | Remaining |
|----------|-------|----------|-----------|
| Critical | 5 | 5 | 0 |
| High | 4 | 4 | 0 |
| Medium | 4 | 4 | 0 |
| Minor | 4 | 4 | 0 |
| **Total** | **17** | **17** | **0** |

### Quick Reference

| ID | Issue | Priority | Status |
|----|-------|----------|--------|
| C1 | Historical Data API Gap | Critical | **Resolved** |
| C2 | Pool Node → MQTT Bridge | Critical | **Resolved** |
| C3 | Command Target Field | Critical | **Resolved** |
| C4 | Touch Calibration Storage | Critical | **Resolved** |
| C5 | Watchdog Timing Budget | Critical | **Resolved** |
| H1 | Field Naming Convention | High | **Resolved** |
| H2 | Config Feed Retained Messages | High | **Resolved** |
| H3 | Font Files Source | High | **Resolved** |
| H4 | CircuitPython WiFi Timeout | High | **Resolved** |
| M1 | Message Freshness Validation | Medium | **Resolved** |
| M2 | Error Code to Node Mapping | Medium | **Resolved** |
| M3 | Adafruit IO Topic Format | Medium | **Resolved** |
| M4 | Socket Pool Management | Medium | **Resolved** |
| N1 | RTC Deep Sleep Persistence | Minor | **Resolved** |
| N2 | Sparkline Data Resolution | Minor | **Resolved** |
| N3 | Feed Write Permissions | Minor | **Resolved** |
| N4 | Legacy Feed Bridge | Minor | **Resolved** |

---

## Critical Issues

These must be resolved before starting Phase 1 implementation.

---

### C1: Historical Data API Gap

- [x] **Resolved** (2026-01-26)

**Problem:**

The Display Node's Historical Screen (Issue 2.36) requires daily aggregated data (min/max/avg) for 7-day and 30-day whisker charts. However, Adafruit IO's REST API does not provide pre-aggregated daily summaries.

The `/feeds/{feed}/data/chart` endpoint returns raw data points at a specified resolution, not aggregated statistics.

**Affected Locations:**

- `implementation-plan.md` Issue 2.36 (Historical Screen)
- `requirements.md` FR-DN-003 (Historical Data Visualization)

**Current Requirement (FR-DN-003):**

> - SHALL display 7-day pool temperature history as whisker chart showing daily min/max/average
> - SHALL display 30-day pool temperature history as whisker chart showing daily min/max/average

**Options:**

| Option | Approach | Pros | Cons |
|--------|----------|------|------|
| A | Client-side aggregation on Display Node | No backend changes | Memory-intensive; 30 days × 288 points/day = 8,640 data points |
| B | Backend aggregation service | Clean separation | Additional infrastructure; deployment complexity |
| C | Reduce data granularity | Simpler implementation | Less precise charts; may miss daily extremes |
| D | Fetch only needed resolution | Balance of accuracy/memory | Still requires client-side min/max/avg calculation per day |

**Updated Analysis (IO+ tier confirmed):**

With IO+ tier (60-day retention), all 30 days of historical data are available. The question is aggregation strategy.

**Chart Endpoint Behavior:**
- Resolution parameter aggregates data using `avg` (average) by default
- Available resolutions: 1, 5, 10, 30, 60, 120, 240, 480, 960 minutes
- Does NOT provide min/max per aggregation window - only average

**Data Volume Analysis:**

| View | Days | Resolution | Data Points | Memory (est.) |
|------|------|------------|-------------|---------------|
| 24h sparkline | 1 | 5 min | 288 | ~3 KB |
| 7d whisker | 7 | 60 min | 168 | ~2 KB |
| 30d whisker | 30 | 240 min | 180 | ~2 KB |

**The Min/Max Problem:**

Whisker charts need daily min/max/avg, but Adafruit IO chart endpoint only returns averages. Options:

| Option | Approach | Data Points | Pros | Cons |
|--------|----------|-------------|------|------|
| D1 | Fetch at 5-min resolution, calculate min/max/avg per day client-side | 30 days × 288 = 8,640 | Accurate min/max | High memory; slow fetch |
| D2 | Fetch at 30-min resolution, calculate per day client-side | 30 days × 48 = 1,440 | Lower memory | May miss daily extremes |
| D3 | Fetch at 60-min resolution, display averages only (no whiskers) | 30 days × 24 = 720 | Simple; low memory | Not a true whisker chart |
| D4 | Use `/data` endpoint with limit/pagination | Configurable | Full control | More complex; multiple requests |

**Decision: Use 60-minute resolution with client-side daily aggregation**

Pool temperature changes slowly, so hourly resolution captures daily trends accurately.

| View | Resolution | Data Points | Memory | Fetch Time |
|------|------------|-------------|--------|------------|
| 7d whisker | 60 min | 168 | ~2 KB | Fast |
| 30d whisker | 60 min | 720 | ~8 KB | Fast |

**Implementation:**
1. Fetch chart data at 60-minute resolution
2. Group data points by day (24 points per day)
3. Calculate min, max, avg for each day
4. Render whisker chart with daily aggregates

**Action Required:**
- [x] Update architecture.md with "Historical Data Strategy" section
- [x] Update Issue 2.36 to specify 60-minute resolution approach

---

### C2: Pool Node → MQTT Bridge Mechanism

- [x] **Resolved** (2026-01-26)

**Problem:**

Pool Node publishes sensor data via HTTPS POST (due to deep sleep preventing persistent MQTT connections). Valve Node and Display Node subscribe to the `gateway` feed via MQTT. The mechanism by which HTTP-posted data appears to MQTT subscribers is not explicitly documented.

**Affected Locations:**

- `requirements.md` Section 5.1-5.3 (Communication Protocol)
- `architecture.md` Data Flow section

**Resolution:**

**CONFIRMED via Adafruit IO documentation:** Data posted via HTTP REST API IS automatically delivered to MQTT subscribers.

From [Adafruit IO API Cookbook](https://io.adafruit.com/api/docs/cookbook.html):
> "sending the string will result in that data being stored in IO and **sent to MQTT subscribers**"

**Action Required:** Add explicit documentation to `architecture.md` Data Flow section:

```text
### HTTP to MQTT Bridge

Adafruit IO automatically bridges HTTP REST API and MQTT:
- Data posted via HTTP POST appears to MQTT subscribers immediately
- Data published via MQTT is accessible via HTTP GET
- This enables Pool Node (HTTP-only) to communicate with Valve/Display Nodes (MQTT)

Pool Node posts to: POST /api/v2/{username}/feeds/{feed}/data
Valve/Display subscribe to: {username}/feeds/{feed}
```

**Verification:**

- [x] Confirmed via official Adafruit IO documentation
- [x] Added "HTTP to MQTT Bridge" section to architecture.md

---

### C3: Command Message `target` Field Discrepancy

- [x] **Resolved** (2026-01-26)

**Problem:**

Discrepancy between architecture.md (mentions `target` field) and requirements.md (no `target` in schema).

**Decision: Remove `target` field - keep single-device assumption**

Per Kent Beck's "no just-in-case code" principle, the `target` field is not needed for MVP. The system assumes a single instance of each command-receiving device type (one Valve Node). Multi-device routing can be added later if needed.

**Current Command Schema (no changes needed):**

```json
{
  "command": "valve_start",
  "parameters": { "maxDuration": 540 },
  "source": "display-node-001"
}
```

**Action Required:**
- [x] Remove `target` from architecture.md (send_command, command example, Supported Commands table)
- [x] Verify requirements.md FR-MSG-009 and Appendix A are correct (they are)
- [x] Issue 1.2 Command class verified: `command`, `parameters`, `source` (no `target`)

---

### C4: Touch Calibration Storage Inconsistency

- [x] **Resolved** (2026-01-26)

**Problem:**

Issue 2.23b states calibration values are published to config feed, but storage/retrieval pattern wasn't clear.

**Decision: Use config.json defaults + config feed updates**

Calibration follows the same pattern as other configuration:

1. **Default calibration** stored in local `config.json` (shipped with device)
2. **Updated calibration** fetched from `config-display-node` feed on boot via HTTP GET
3. **Config feed** configured to retain only latest value (single data point)
4. **If network unavailable**: Display Node can't show data anyway, so touch calibration isn't critical

**Boot Sequence:**

```text
1. Load defaults from local config.json (includes default calibration)
2. Connect to WiFi
3. HTTP GET /feeds/config-display-node/data/last
4. Merge fetched config over defaults (calibration overrides if present)
5. Subscribe to config feed for runtime updates
6. Start normal operation
```

**Calibration Utility (Issue 2.23b):**
- Displays calibration targets on screen
- User touches each target
- Calculates calibration values
- Publishes updated config JSON to `config-display-node` feed
- Outputs values to serial console as backup

**Action Required:**
- [x] Update Issue 2.23b to match this pattern
- [x] Update architecture.md Configuration Distribution section
- [ ] Ensure config feed is set to "last value only" in Adafruit IO setup (Issue 4.1)

---

### C5: Watchdog Timing Budget

- [x] **Resolved** (2026-01-26)

**Problem:**

The Pool Node wake cycle must complete within watchdog constraints, but the timing budget is not documented. Potential conflict exists:

**NFR-REL-001:** Pool Node watchdog timeout: 60 seconds
**NFR-REL-008:** Feed watchdog at intervals ≤25% of timeout = ≤15 seconds
**NFR-REL-005:** WiFi connection timeout: 15 seconds

If WiFi connection takes the full 15 seconds, there is zero margin for the next watchdog feed.

**Affected Locations:**

- `requirements.md` NFR-REL-001, NFR-REL-005, NFR-REL-008
- `architecture.md` Pool Node Lifecycle, Reliability Patterns

**Current Wake Cycle (from architecture.md):**

```text
Wake → Init Watchdog → WiFi Connect → Sync Time → Read Sensors → Transmit → Cleanup → Sleep
              ↓              ↓            ↓            ↓           ↓
         [feed watchdog at each stage, max 15s intervals]
```

**Decision: Analysis confirms design is safe; document during Phase 1**

**Timing Analysis:**

| Stage | Max Duration | Cumulative | Watchdog Feed |
|-------|--------------|------------|---------------|
| Init Watchdog | <1s | 1s | After |
| WiFi Connect | 15s | 16s | Before + After |
| Sync Time (HTTP) | 10s | 26s | Before + After |
| Read Sensors | ~5s (with retries) | 31s | Before + After |
| Transmit (HTTP) | 10s | 41s | Before + After |
| Cleanup | <1s | 42s | Before |
| **Total Maximum** | **~42s** | - | - |

**Safety Margin:** 18 seconds (60s timeout - 42s max duration = 30% margin)

The design is safe. Watchdog is fed before and after each blocking operation, ensuring no single stage exceeds the 15-second feed interval requirement.

**Action Required:**
- [x] Added "Pool Node Wake Cycle Timing Budget" section to architecture.md

---

## High Priority Issues

Should be resolved before starting the affected phase.

---

### H1: Field Naming Convention (Python ↔ JSON)

- [x] **Resolved** (2026-01-26)

**Problem:**

Python uses `snake_case` for attributes; JSON schema uses `camelCase`. The encoding/decoding convention is not documented.

**Example:**

```python
# Python class (Issue 1.2)
class ValveState:
    def __init__(self, state, is_filling, current_fill_duration, max_fill_duration):
        self.is_filling = is_filling
        self.current_fill_duration = current_fill_duration
```

```json
// JSON schema (FR-MSG-005)
{
  "valve": {
    "isFilling": false,
    "currentFillDuration": 0
  }
}
```

**Decision: Encoder/decoder handle case conversion automatically**

| Direction | Conversion | Example |
|-----------|------------|---------|
| Python → JSON | `snake_case` → `camelCase` | `is_filling` → `isFilling` |
| JSON → Python | `camelCase` → `snake_case` | `currentFillDuration` → `current_fill_duration` |

**Action Required:**
- [x] Document convention in architecture.md Messages Module section
- [x] Add acceptance criteria to Issue 1.3

---

### H2: Config Feed "Retained Message" Behavior

- [x] **Resolved** (2026-01-26)

**Problem:**

Architecture.md states devices receive config via MQTT retained message, but Adafruit IO does not support true MQTT retained messages.

**Affected Locations:**

- `architecture.md` Configuration Distribution section

**Resolution:**

**CONFIRMED:** Adafruit IO does NOT support standard MQTT retained messages. They provide a `/get` topic modifier as an alternative.

From [Adafruit IO MQTT API](https://io.adafruit.com/api/docs/mqtt.html):
> "Since we don't actually store data in the broker but at a lower level and can't support PUBLISH retain directly, we're proposing a different solution: the /get topic modifier."

**The `/get` Pattern:**
1. Subscribe to `{username}/feeds/{feed}`
2. Publish anything (e.g., `\0`) to `{username}/feeds/{feed}/get`
3. Adafruit IO immediately sends the last value to your subscription

**Action Required:** Update architecture.md Boot Sequence to use `/get` pattern:

```text
Boot Sequence (Corrected):
1. Device connects to WiFi and MQTT
2. Subscribes to its config feed: {username}/feeds/{config-feed}
3. Publishes to {username}/feeds/{config-feed}/get to request last value
4. Receives config JSON on subscription
5. Applies configuration and starts normal operation
6. Continues listening for runtime config updates
7. Falls back to local config.json if network unavailable
```

**Alternative Pattern (HTTP):**
- Use HTTP GET `/feeds/{feed}/data/last` endpoint for initial config
- Subscribe to MQTT for runtime updates only

**Verification:**

- [x] Confirmed via official Adafruit IO documentation
- [x] Updated architecture.md Configuration Distribution section with HTTP GET + MQTT pattern

---

### H3: Font Files Source and Licensing

- [x] **Resolved** (2026-01-26)

**Problem:**

Issue 2.20 references "Adafruit Free Sans fonts from circuitpython-fonts bundle" without specific source URL or license verification.

**Resolution:**

| Attribute | Value |
|-----------|-------|
| Repository | <https://github.com/adafruit/circuitpython-fonts> |
| Format | PCF (Portable Compiled Format) |
| License | GNU FreeFont - GPL with Font Exception (allows embedding) |
| Font family | FreeSans (Regular, Bold, Oblique, BoldOblique) |
| Sizes | Generated in multiple pixel sizes (8, 10, 12, 14, 18, 24, etc.) |
| Dependency | `adafruit_bitmap_font` library required |
| Installation | `circup install font_free_sans_18` or download from Releases |

**Action Required:**
- [x] Document font source in architecture.md Display Node section
- [x] Update Issue 2.20 with specific installation details

---

### H4: CircuitPython WiFi Connection Timeout

- [x] **Resolved** (2026-01-26)

**Problem:**

NFR-REL-005 specifies 15-second WiFi timeout, but architecture.md notes:

> *Note: CircuitPython implementations cannot enforce WiFi connection timeouts due to library limitations (`wifi.radio.connect()` has no timeout parameter).*

This affects Valve Node and Display Node reliability.

**Decision: Accept limitation - watchdog provides recovery**

CircuitPython's `wifi.radio.connect()` has no timeout parameter. The watchdog timer provides reliable recovery from WiFi hangs:

| Node | Watchdog Timeout | Recovery |
|------|------------------|----------|
| Valve Node | 30s | Device reset and reconnect |
| Display Node | 120s | Device reset and reconnect |

**Action Required:**
- [x] Document limitation in Issue 2.18 (Valve Node)
- [x] Document limitation in Issue 2.34 (Display Node)

---

## Medium Priority Issues

Should be resolved before the affected issue is implemented.

---

### M1: Message Freshness Validation Addition

- [x] **Resolved** (2026-01-26)

**Problem:**

Issue 1.4 adds timestamp freshness validation including "reject if more than 1 minute in future (clock skew protection)" which is not in requirements.md FR-MSG-014.

**Decision: Add future timestamp rejection to FR-MSG-014**

Added to requirements.md FR-MSG-014 Timestamp Freshness Validation:
- **SHALL** ignore messages with timestamps more than 1 minute in the future (clock skew protection)

**Action Required:**
- [x] Update FR-MSG-014 in requirements.md

---

### M2: Error Code to Node Mapping

- [x] **Resolved** (2026-01-26)

**Problem:**

FR-MSG-011 defines 22 error codes but doesn't specify which nodes generate which codes.

**Decision: Defer - let implementation determine usage**

Error codes are self-documenting by their prefix:
- `VALVE_*` codes → Valve Node only
- `SENSOR_*` codes → Any node with sensors
- `NETWORK_*` codes → Any node
- `BUS_*` codes → Pool Node (I2C/OneWire), others as needed

Over-specifying upfront would be unnecessarily rigid. Each node's implementation will use the appropriate subset of error codes.

---

### M3: Adafruit IO Topic Format Documentation

- [x] **Resolved** (2026-01-26)

**Problem:**

Documents use shorthand `poolio.gateway` but the full MQTT topic is `{username}/feeds/{group}.{feed}`. Username interpolation is not documented.

**Decision: Add MQTT Topic Format section to architecture.md**

Added section documenting:
- Full topic format: `{username}/feeds/{group}.{feed}`
- Examples for prod/nonprod environments
- Special topics (`/get`, `/throttle`, `/errors`)
- Username interpolation from `AIO_USERNAME`

**Action Required:**
- [x] Add MQTT Topic Format section to architecture.md

---

### M4: Socket Pool Management Details

- [x] **Resolved** (2026-01-26)

**Problem:**

Issues 2.10, 2.18, 2.34 reference socket management and `adafruit_connection_manager` but specific API usage patterns are not documented.

**Decision: Document ConnectionManager API in architecture.md**

Added complete API reference including:
- `get_connection_manager()` - get singleton
- `connection_manager_close_all()` - close all sockets
- `available_socket_count` / `managed_socket_count` properties
- `get_socket()`, `free_socket()`, `close_socket()` methods
- Usage example with monitoring and cleanup

*Reference: [ConnectionManager API Docs](https://docs.circuitpython.org/projects/connectionmanager/en/latest/api.html)*

**Action Required:**
- [x] Document ConnectionManager API in architecture.md

---

## Minor Issues

Can be resolved during implementation if encountered.

---

### N1: RTC Deep Sleep Persistence

- [x] **Resolved** (2026-01-26)

**Problem:**

Architecture says Pool Node syncs time on each wake, implying RTC doesn't survive deep sleep. Verify this assumption.

**Decision: Not applicable - time obtained during normal HTTP cycle**

Pool Node boots fresh each wake cycle and connects to WiFi to publish sensor data. Time can be obtained from:
- HTTP response headers (`Date` header)
- Adafruit IO API response

No separate "time sync" step is needed - time acquisition is part of the normal HTTP communication. RTC persistence across deep sleep is therefore irrelevant.

---

### N2: Sparkline Data Resolution Verification

- [x] **Resolved** (2026-01-26)

**Problem:**

FR-DN-003 assumes 288 data points (5-minute intervals over 24 hours) are available from Adafruit IO.

**Resolution:**

**CONFIRMED:** The chart endpoint supports 5-minute resolution.

From [Adafruit IO API Reference](https://io.adafruit.com/api/docs/):
> Resolution parameter: "Size of aggregation slice in minutes. Must be one of: 1, 5, 10, 30, 60, 120, 240, 480, or 960"

**Calculation:**
- 24 hours × 60 minutes = 1440 minutes
- 1440 ÷ 5-minute resolution = 288 data points ✓

**Account Status:** IO+ tier (60 days retention, 60 data points/min)
- 30-day historical charts are fully supported
- 60 days of data available for analysis

**Endpoint:**

```text
GET /api/v2/{username}/feeds/{feed}/data/chart?hours=24&resolution=5
```

**Response includes:**
- `parameters.resolution`: 5 (minutes)
- `columns`: ["date", "avg"]
- `data`: Array of [timestamp, value] pairs

**Verification:**

- [x] Confirmed via official Adafruit IO documentation
- [x] IO+ tier provides sufficient data retention (60 days)

---

### N3: Feed Write Permissions Documentation

- [x] **Resolved** (2026-01-26)

**Problem:**

NFR-SEC-002 mentions `gateway` feed should require authentication for write access, but configuration steps are not documented.

**Decision: No special configuration needed**

Adafruit IO authentication is simple: API key provides full read/write access to all feeds. No per-feed permission configuration exists or is needed. Authentication via API key is already required for all operations.

---

### N4: Legacy Feed Bridge Clarification

- [x] **Resolved** (2026-01-26)

**Problem:**

Architecture.md mentions a "bridge service" for legacy feed compatibility but it's unclear if this is part of MVP.

**Decision: Remove legacy bridge section entirely**

The legacy feed bridge is not part of the rearchitecture scope. Removed the "Legacy Feed Compatibility" section from architecture.md to avoid confusion.

**Action Required:**
- [x] Remove Legacy Feed Compatibility section from architecture.md

---

## Resolution Log

Track when issues are resolved and what decisions were made.

| Date | Issue ID | Resolution Summary | Updated Files |
|------|----------|-------------------|---------------|
| 2026-01-26 | C1 | Use 60-min resolution for 7d/30d charts; client-side daily min/max/avg aggregation | architecture.md, implementation-plan.md Issue 2.36 |
| 2026-01-26 | C2 | HTTP POST to feeds IS delivered to MQTT subscribers (confirmed via Adafruit docs) | architecture.md (HTTP to MQTT Bridge section) |
| 2026-01-26 | C3 | Remove `target` field; keep single-device assumption per YAGNI | architecture.md (send_command, command example, Supported Commands) |
| 2026-01-26 | C4 | Use config.json defaults + config feed updates; fetch last value via HTTP GET on boot | architecture.md, implementation-plan.md Issue 2.23b |
| 2026-01-26 | C5 | Timing analysis confirms 42s max cycle vs 60s timeout (30% margin) | architecture.md (Wake Cycle Timing Budget section) |
| 2026-01-26 | H1 | Encoder/decoder handle snake_case ↔ camelCase conversion automatically | architecture.md, implementation-plan.md Issue 1.3 |
| 2026-01-26 | H2 | Adafruit IO doesn't support MQTT retain; use HTTP GET + MQTT subscribe pattern | architecture.md (Configuration Distribution section) |
| 2026-01-26 | H3 | FreeSans from circuitpython-fonts; PCF format; GPL + Font Exception license | architecture.md, implementation-plan.md Issue 2.20 |
| 2026-01-26 | H4 | Accept WiFi timeout limitation; watchdog provides recovery | implementation-plan.md Issues 2.18, 2.34 |
| 2026-01-26 | M1 | Add future timestamp rejection (1 min) to FR-MSG-014 | requirements.md |
| 2026-01-26 | M2 | Defer - error codes are self-documenting by prefix | None needed |
| 2026-01-26 | M3 | Add MQTT Topic Format section with username interpolation | architecture.md |
| 2026-01-26 | M4 | Document ConnectionManager API for socket management | architecture.md |
| 2026-01-26 | N1 | RTC persistence not needed - time obtained during HTTP cycle | None needed |
| 2026-01-26 | N3 | API key provides full access - no per-feed permissions to configure | None needed |
| 2026-01-26 | N4 | Remove legacy bridge section - not part of rearchitecture scope | architecture.md |
| 2026-01-26 | N2 | Chart endpoint supports 5-min resolution; 288 points for 24h confirmed; IO+ has 60-day retention | None needed |

---

## Next Steps

1. ~~**Before Phase 1 starts:** Resolve all Critical issues (C1-C5)~~ **DONE**
2. ~~**Before Phase 2c starts:** Resolve H1-H4 (Display Node dependencies)~~ **DONE**
3. ~~**During implementation:** Resolve Medium/Minor issues as encountered~~ **DONE**

### Status: COMPLETE

All 17 issues have been reviewed and resolved. The project is ready for Phase 1 implementation.
