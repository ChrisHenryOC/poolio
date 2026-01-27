# Pre-Implementation Review: Issues to Resolve

> **Status:** Complete
> **Created:** 2026-01-26
> **Purpose:** Track resolution of documentation inconsistencies and gaps before starting implementation

---

## Background

Before beginning Phase 1 implementation, a review of the three core documentation files identified inconsistencies, gaps, and ambiguities that should be resolved. This document tracks those issues and their resolution.

### Documents Reviewed

| Document | Purpose | Key Sections |
|----------|---------|--------------|
| `docs/requirements.md` | Comprehensive requirements including functional specs, message schemas, reliability requirements | FR-MSG-\* (message formats), NFR-\* (non-functional), Appendix A (JSON schemas) |
| `docs/architecture.md` | System design, component interfaces, deployment procedures | Components, CircuitPython Compatibility, Build Sequence |
| `docs/implementation-plan.md` | 67 MVP issues + 4 deferred, organized into Phases 1-4 | Issue definitions with acceptance criteria |
| `docs/display-node-ui-design.md` | Screen layouts, touch zones, visual specifications | Mockups, touch specifications |

### How to Use This Document

1. Work through each issue in priority order (Critical → Important → Minor)
2. Check the resolution checkbox when the issue is resolved
3. Document the resolution in the "Resolution" section of each issue
4. Update the related source documents as needed

---

## Critical Issues (Must Resolve Before Phase 1)

### Issue 1: ValveStatus Schema Inconsistency

- [x] **Resolved**

**Problem:** The valve state representation differs between documents.

| Source | Representation |
|--------|----------------|
| requirements.md FR-MSG-005 | `valve.state` as string: `"open"` or `"closed"` |
| requirements.md Appendix A.3 (JSON Schema) | `state` as string enum: `["open", "closed"]` |
| implementation-plan.md Issue 1.2 | `ValveState` class with `isOpen: bool` |

**Impact:** Implementation will not match the authoritative JSON schema. Message validation will fail.

**Recommendation:** The JSON Schema in Appendix A is authoritative. Update implementation-plan.md Issue 1.2 to use:

```python
class ValveState:
    def __init__(self, state, is_filling, current_fill_duration=None, max_fill_duration=None):
        self.state = state  # "open" or "closed"
        self.is_filling = is_filling  # bool
        self.current_fill_duration = current_fill_duration  # int (seconds) or None
        self.max_fill_duration = max_fill_duration  # int (seconds) or None
```

**Files to Update:**
- [x] `docs/implementation-plan.md` Issue 1.2 - Change ValveState definition

**Resolution:**
Updated ValveState class definition to use `state` (str: "open" or "closed") instead of `isOpen` (bool), and `currentFillDuration` instead of `fillElapsedSeconds` to match JSON Schema in Appendix A.3. This also resolves Issue 14 (field naming consistency).

---

### Issue 2: Valve State Machine - Missing "Cooldown" State

- [x] **Resolved**

**Problem:** Architecture mentions a state that doesn't exist elsewhere.

| Source | States Mentioned |
|--------|------------------|
| architecture.md "State Management" | `idle → filling → cooldown` |
| requirements.md | Only `filling` and `idle` implied |
| implementation-plan.md Issue 1.2 | `isFilling: bool` (only two states) |
| JSON Schema valve.state | `"open"` or `"closed"` (physical state, not operational state) |

**Impact:** Confusion about whether cooldown is a real operational state.

**Analysis:** Looking at requirements FR-VN-002 and FR-VN-003:
- Fill checks occur at fixed intervals (e.g., every 10 minutes)
- After a fill completes, the next check is at the next interval
- There's no explicit "cooldown period" requirement

**Recommendation:** Remove "cooldown" from architecture.md. The behavior described (waiting until next check interval) is the normal scheduling, not a distinct state.

**Files to Update:**
- [x] `docs/architecture.md` Section "State Management" - Remove cooldown reference
- [x] `docs/architecture.md` Data Flow diagram - Remove cooldown reference

**Resolution:**
Removed two cooldown references from architecture.md:
1. Removed "[Enter cooldown period]" from Fill Operation Flow diagram
2. Changed state machine from `idle → filling → cooldown` to `idle → filling → idle`

The requirements don't define a cooldown state - after a fill completes, the valve simply returns to idle and waits for the next scheduled check interval.

---

### Issue 3: Main Dashboard Sparkline - MVP or Deferred?

- [x] **Resolved**

**Problem:** Conflicting statements about whether the 24-hour sparkline is part of MVP.

| Source | Statement |
|--------|-----------|
| implementation-plan.md Issue 2.24 | "Chart zone: Gray rectangle with centered 'Chart' label (actual sparkline deferred)" |
| display-node-ui-design.md Section 3 | Main Dashboard mockup shows sparkline; sparkline listed in "Chart Zone" |
| display-node-ui-design.md Section 6 | "Historical Data View" with "Priority: Deferred (Phase 3)" |

**Analysis:** The UI design distinguishes between:
1. **Main Dashboard sparkline** - Simple 24-hour view integrated into main screen
2. **Historical Data View** - Separate screen with 24h/7d/30d options and range buttons

**Recommendation:** Clarify that:
- The main dashboard 24-hour sparkline IS part of MVP
- The separate Historical Data View screen (with 7d/30d options) is deferred to Phase 6

**Files to Update:**
- [x] `docs/implementation-plan.md` Issue 2.24 - Correct acceptance criteria to include sparkline
- [x] Add new Issue for sparkline rendering (or expand 2.24)

**Resolution:**
Updated Issue 2.24 to include sparkline in MVP:
- Added acceptance criteria for 24-hour temperature sparkline per UI design
- Added sparkline data fetching from cloud API
- Added min/max value display and 3-point moving average smoothing per FR-DN-003
- Added fallback for unavailable historical data
- Added sparkline.py and test_sparkline.py to file list
- Added clarifying note that the separate Historical Data View screen (7d/30d options) requires separate implementation issues

---

### Issue 4: Historical Charts Phase Number Confusion

- [x] **Resolved**

**Problem:** FR-DN-003 references "Phase 3" but that means something different in the implementation plan.

| Context | "Phase 3" Means |
|---------|-----------------|
| requirements.md Section 8.1 | Simulators & Testing |
| implementation-plan.md | Simulators & Testing |
| requirements.md FR-DN-003 | When historical charts should be added |
| architecture.md Build Sequence | Phase 6 includes "Add historical charts to Display Node" |

**Impact:** Implementers will be confused about when to add historical chart features.

**Recommendation:** Update FR-DN-003 to reference "Phase 6" or use descriptive text like "post-MVP" instead of phase numbers.

**Files to Update:**
- [x] `docs/requirements.md` FR-DN-003 - Change phase reference

**Resolution:**
Restructured historical chart documentation:
- Removed confusing "(Phase 3)" from FR-DN-003 title
- 24-hour sparkline marked as MVP in FR-DN-003
- 7d/30d Historical Screen marked as separate implementation issues
- Added Issue 2.36 (Historical Screen) to implementation-plan.md for Phase 2c
- Removed "Add historical charts to Display Node" from Phase 6 in architecture.md
- Updated Issue 2.24 note to reference Issue 2.36
- Corrected chart width to 240px (full screen) across all documents
- Corrected data point math: 288 points (5-min intervals) downsampled to 240 pixels

---

### Issue 5: Font File Licensing and Source

- [x] **Resolved**

**Problem:** Implementation plan references Arial BDF fonts but doesn't specify source or licensing.

| Reference | Details |
|-----------|---------|
| implementation-plan.md Issue 2.20 | "Arial BDF font files listed (7, 8, 10, 12, 14, 20, 22 point)" |
| display-node-ui-design.md | Font specifications reference Arial at various sizes |
| docs/fonts-needed.md | File to be created (doesn't exist yet) |

**Impact:** Could block Display Node implementation if fonts are not available or not licensed for embedded use.

**Options:**
1. **Use Adafruit's open-source BDF fonts** - Available in CircuitPython bundle, definitely licensed
2. **Use Liberation Sans** - Open-source Arial-compatible font
3. **Create Arial BDF from licensed source** - Requires font license investigation

**Recommendation:** Use Adafruit's bundled fonts (terminalio.FONT as fallback, Adafruit BDF fonts for larger sizes). Update UI design to reference available fonts.

**Files to Update:**
- [x] ~~Create `docs/fonts-needed.md`~~ Not needed - using Adafruit bundled fonts
- [x] `docs/display-node-ui-design.md` - Update font references if changing from Arial
- [x] `docs/implementation-plan.md` Issue 2.20 - Update font file references

**Resolution:**
Selected Adafruit circuitpython-fonts bundle (Free Sans) as font source:
- Available sizes: 6, 8, 10, 12, 14, 18, 24, 30, 36, 42, 48, 54, 60, 72
- Adjusted UI spec sizes to match: 7pt→8pt, 20pt→18pt, 22pt→24pt
- Updated display-node-ui-design.md font specifications table and loading code
- Updated implementation-plan.md Issues 2.20 and 2.21 to reference Adafruit fonts
- No need for docs/fonts-needed.md - fonts come from Adafruit bundle

---

## Important Issues (Should Resolve Before or During Phase 1)

### Issue 6: Heartbeat Message Implementation Missing

- [x] **Resolved**

**Problem:** Requirements define heartbeat message type but no implementation issue covers it.

**Requirements FR-MSG-010 defines:**

```json
{
  "uptime": 3600,
  "freeMemory": 45000,
  "errorCount": 0,
  "lastError": null
}
```

**Questions not answered:**
- Which nodes send heartbeats?
- At what interval?
- Is this the same as "health check" mentioned in NFR-ARCH-005?

**Recommendation:** Either:
1. Add heartbeat sending to node integration issues (2.10, 2.18, 2.34), OR
2. Explicitly defer to Phase 4+ with trigger condition

**Files to Update:**
- [x] `docs/requirements.md` FR-MSG-010 - Add deferral note
- [x] `docs/implementation-plan.md` Issue 1.2 - Remove Heartbeat class
- [x] `docs/implementation-plan.md` Issue 4.15 - Remove heartbeat.json schema
- [x] `docs/architecture.md` - Remove heartbeat from QoS table and message types table

**Resolution:**
Deferred indefinitely and removed references. The Pool Node and Valve Node already send status messages at regular intervals, which serve as implicit heartbeats. The Display Node is a listener and doesn't need to signal its presence. FR-MSG-010 retained in requirements with "(DEFERRED)" note for future reference if explicit health monitoring becomes necessary.

---

### Issue 7: Trusted Device ID Validation Missing

- [x] **Resolved**

**Problem:** Security requirement has no implementation issue.

**Requirements NFR-SEC-002b states:**
> - SHALL maintain a list of trusted device IDs in configuration
> - SHALL ignore status messages from untrusted device IDs
> - SHALL log messages received from unknown device IDs

**Recommendation:** Add to Issue 1.4 (Message Validation) or create new deferred issue with trigger: "Implement if devices are deployed in environments where untrusted messages could be injected."

**Files to Update:**
- [x] `docs/requirements.md` NFR-SEC-002b - Add deferral note

**Resolution:**
Deferred indefinitely. MQTT is already authenticated via Adafruit IO API key - only authorized users can publish to feeds. Added "(DEFERRED)" to NFR-SEC-002b title and changed SHALL to SHOULD with conditional "(if implemented)" clauses.

---

### Issue 8: Confirmation Dialog Widget Not in Base Widgets

- [x] **Resolved**

**Problem:** Issues 2.26 and 2.27 require confirmation dialogs, but Issue 2.22 (Base Widget Classes) doesn't include dialog widget.

**Issue 2.22 currently lists:**
- TextLabel class
- Button class
- ProgressBar class

**Missing:** Modal dialog/confirmation dialog widget needed for:
- Manual fill start confirmation (Issue 2.26)
- Device reset confirmation (Issue 2.27)

**Recommendation:** Add ConfirmationDialog to Issue 2.22 acceptance criteria:
- [ ] ConfirmationDialog class with title, message, Yes/Cancel buttons
- [ ] Modal overlay (dims background)
- [ ] Returns user selection (confirmed/cancelled)

**Files to Update:**
- [x] `docs/implementation-plan.md` Issue 2.22 - Add ConfirmationDialog acceptance criteria

**Resolution:**
Added ConfirmationDialog to Issue 2.22 acceptance criteria with title, message, Yes/Cancel buttons, modal overlay, and return value for user selection.

**Resolution:**
<!-- Document the resolution here when complete -->

---

### Issue 9: Config Hot-Reload Trigger Mechanism Not Specified

- [x] **Resolved**

**Problem:** Documents say config hot-reload is supported but don't specify how it's triggered.

**What's documented:**
- NFR-ARCH-003 says "support configuration hot-reload for continuously-running nodes"
- Architecture lists which parameters are hot-reloadable vs restart-required
- Valve/Display Nodes subscribe to `config` feed

**Not documented:**
- Is hot-reload triggered by MQTT message on `config` feed?
- Is it polled on a timer?
- Does it watch for file changes?

**Recommendation:** Document in architecture.md that hot-reload is triggered by:
1. Receiving `config_update` message on `config` feed (primary)
2. Optionally: periodic re-read of config.json (if file system supports it)

**Files to Update:**
- [x] `docs/architecture.md` Config Module section - Add reload trigger mechanism

**Resolution:**
Documented per-device config feeds approach:
- Each device has its own config feed (`config-pool-node`, `config-valve-node`, `config-display-node`)
- Full config JSON is published to the feed (not individual key updates)
- Adafruit IO retains the last message
- On boot, device subscribes and receives current config
- Falls back to local `config.json` if network unavailable
- Hot-reloadable changes applied immediately; restart-required changes logged

---

### Issue 10: Touch Calibration Utility Missing

- [x] **Resolved**

**Problem:** Calibration is mentioned but no utility or procedure is documented.

| Reference | Statement |
|-----------|-----------|
| implementation-plan.md Issue 2.35 | "Calibrate touchscreen and update config.json" |
| implementation-plan.md Risk Items | "STMPE610 touch calibration... provide calibration utility" |

**No issue creates the calibration utility.**

**Recommendation:** Either:
1. Add Issue 2.23b: Touch Calibration Utility, OR
2. Document manual calibration procedure (touch corners, note raw values, calculate coefficients)

**Files to Update:**
- [x] `docs/implementation-plan.md` - Add calibration issue

**Resolution:**
Added Issue 2.23b: Touch Calibration Utility
- Displays crosshair targets at screen corners
- Captures raw STMPE610 coordinates
- Calculates calibration coefficients
- Publishes updated config to `config-display-node` feed (since local storage may be read-only)
- Also outputs to serial console as backup

---

### Issue 11: Error Code Constants Location

- [x] **Resolved**

**Problem:** Requirements define 22 standard error codes but no issue explicitly creates them as constants.

**Requirements FR-MSG-011 defines error codes:**
- SENSOR_READ_FAILURE, SENSOR_INIT_FAILURE, SENSOR_OUT_OF_RANGE
- NETWORK_CONNECTION_FAILED, NETWORK_TIMEOUT, NETWORK_AUTH_FAILURE
- BUS_I2C_FAILURE, BUS_ONEWIRE_FAILURE, BUS_SPI_FAILURE
- CONFIG_INVALID_VALUE, CONFIG_MISSING_REQUIRED, CONFIG_SCHEMA_VIOLATION
- SYSTEM_MEMORY_LOW, SYSTEM_WATCHDOG_RESET, SYSTEM_UNEXPECTED_RESET
- VALVE_SAFETY_INTERLOCK, VALVE_MAX_DURATION, VALVE_ALREADY_ACTIVE, VALVE_DATA_STALE, VALVE_HARDWARE_FAILURE

**Recommendation:** Add to Issue 1.2 (Message Type Classes) acceptance criteria:
- [ ] ErrorCode constants/enum with all 22 codes from FR-MSG-011

**Files to Update:**
- [x] `docs/implementation-plan.md` Issue 1.2 - Add ErrorCode constants

**Resolution:**
Added ErrorCode constants requirement to Issue 1.2 acceptance criteria: "ErrorCode constants for all 22 codes from FR-MSG-011 (SENSOR_*, NETWORK_*, BUS_*, CONFIG_*, SYSTEM_*, VALVE_*)"

---

### Issue 12: Unconfigured Device Behavior (No Credentials)

- [x] **Resolved**

**Problem:** Captive portal is deferred but there's no specified behavior for unconfigured devices.

**Context:**
- Captive portal provisioning deferred to Issue 4.18
- MVP uses settings.toml (CircuitPython) or secrets.h (C++)
- What happens if device boots with missing/empty credentials?

**Impact:** Device could crash, hang, or behave unexpectedly if credentials are missing.

**Recommendation:** Document graceful failure behavior:
- Display Node: Show "Not Configured - Edit settings.toml" message on screen
- Valve Node: Log error, do not attempt MQTT connection, enter safe state (valve closed)
- Pool Node: Log error, enter deep sleep, retry on next wake

**Files to Update:**
- [x] `docs/architecture.md` - Add "Unconfigured Device Behavior" section

**Resolution:**
Added "Unconfigured Device Behavior" section to architecture.md documenting graceful failure behavior for each node type when credentials are missing:
- Pool Node: Log error, enter deep sleep, retry on next wake
- Valve Node: Log error, safe state (valve closed), blink LED pattern
- Display Node: Show "Not Configured" message with instructions

---

### Issue 13: Throttle Handling Strategy

- [x] **Resolved**

**Problem:** Documents say subscribe to throttle topic but don't specify response behavior.

**What's documented:**
- Requirements Section 5.5: "SHOULD implement backoff when throttle notification received"
- Issue 1.7: `subscribe_throttle(callback)` method

**Not documented:**
- What backoff strategy?
- How long to wait?
- Which operations to pause?

**Recommendation:** Document in architecture.md Cloud Module:
- On throttle notification: pause publishing for 60 seconds
- Log throttle event
- Resume normal operation after pause
- If repeated throttles: exponential backoff (60s, 120s, 240s, max 300s)

**Files to Update:**
- [x] `docs/architecture.md` - Add throttle response behavior section
- [x] `docs/implementation-plan.md` Issue 1.7 - Add throttle handling to acceptance criteria

**Resolution:**
Documented throttle response behavior in architecture.md:
- Pause publishing 60s on throttle notification
- Exponential backoff on repeated throttles (120s, 240s, max 300s)
- Reset backoff after 5 minutes without throttle
- Listed operations affected vs not affected by throttle
Added acceptance criterion to Issue 1.7 for throttle handling implementation.

---

## Minor Issues (Resolve When Convenient)

### Issue 14: Field Naming Consistency

- [x] **Resolved**

**Problem:** Minor naming inconsistency between documents.

| Source | Field Name |
|--------|------------|
| requirements.md FR-MSG-005 | `currentFillDuration` |
| requirements.md Appendix A.3 | `currentFillDuration` |
| implementation-plan.md Issue 1.2 | `fillElapsedSeconds` |

**Recommendation:** Use `currentFillDuration` to match JSON schema.

**Files to Update:**
- [x] `docs/implementation-plan.md` Issue 1.2 - Change to `currentFillDuration`

**Resolution:**
Resolved as part of Issue 1. Updated ValveState to use `currentFillDuration` matching the JSON schema.

---

### Issue 15: Legacy Feed Dual-Publishing Decision

- [x] **Resolved**

**Problem:** Architecture mentions `legacyFeedsEnabled` config for publishing to both new and legacy feeds, but no implementation issue covers this.

**Context:**
- Architecture mentions legacy feed mapping (poolio.pooltemp → cabelanet.pooltemp)
- Config includes `legacyFeedsEnabled: true` for prod
- If replacing entire system at once, dual-publishing may not be needed

**Question:** Is this needed? Will legacy nodes or dashboards need to continue receiving data during migration?

**Recommendation:** Make a decision and document it:
- If YES: Add to node integration issues (2.10, 2.18, 2.34)
- If NO: Remove `legacyFeedsEnabled` from architecture.md config examples

**Files to Update:**
- [x] Decision documented here
- [x] `docs/architecture.md` - Update based on decision

**Resolution:**
Decision: NO legacy feed support in the new implementation. The new system will be independent from the legacy system. If legacy dashboard support is needed during migration, a separate bridge service can be deployed on an Ubuntu server to:
- Subscribe to new `poolio.*` feeds
- Extract values from JSON messages
- Publish to legacy `cabelanet.*` feeds

Updated architecture.md:
- Replaced Legacy Feed Compatibility section with bridge service documentation
- Removed `legacyFeedsEnabled` from all config examples

**Resolution:**
<!-- Document the resolution here when complete -->

---

## Resolution Summary

| # | Issue | Status | Resolved By | Date |
|---|-------|--------|-------------|------|
| 1 | ValveStatus Schema | **Resolved** | Claude | 2026-01-26 |
| 2 | Cooldown State | **Resolved** | Claude | 2026-01-26 |
| 3 | Main Dashboard Sparkline | **Resolved** | Claude | 2026-01-26 |
| 4 | Historical Charts Phase | **Resolved** | Claude | 2026-01-26 |
| 5 | Font File Source | **Resolved** | Claude | 2026-01-26 |
| 6 | Heartbeat Implementation | **Resolved** | Claude | 2026-01-26 |
| 7 | Trusted Device ID | **Resolved** | Claude | 2026-01-26 |
| 8 | Confirmation Dialog Widget | **Resolved** | Claude | 2026-01-26 |
| 9 | Config Hot-Reload Trigger | **Resolved** | Claude | 2026-01-26 |
| 10 | Touch Calibration Utility | **Resolved** | Claude | 2026-01-26 |
| 11 | Error Code Constants | **Resolved** | Claude | 2026-01-26 |
| 12 | Unconfigured Device Behavior | **Resolved** | Claude | 2026-01-26 |
| 13 | Throttle Handling Strategy | **Resolved** | Claude | 2026-01-26 |
| 14 | Field Naming Consistency | **Resolved** | Claude | 2026-01-26 |
| 15 | Legacy Feed Dual-Publishing | **Resolved** | Claude | 2026-01-26 |

---

## Next Steps

All 15 pre-implementation issues have been resolved. The documentation is now consistent and ready for Phase 1 implementation.

**Implementation can begin with Issue 1.1 (Message Envelope Structure).**

Key decisions made during this review:
- 24-hour sparkline is MVP; Historical Screen (7d/30d) added as Issue 2.36
- Adafruit circuitpython-fonts (Free Sans) for Display Node fonts
- Heartbeat messages deferred indefinitely (status messages serve as implicit heartbeats)
- Per-device config feeds for runtime configuration
- Touch calibration utility publishes to config feed (Issue 2.23b)
- No legacy feed support in new implementation (separate bridge service if needed)
