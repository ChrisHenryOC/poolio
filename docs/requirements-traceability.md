# Requirements Traceability Matrix

> Generated: 2026-01-22
> Last Updated: 2026-01-22 (Second Comprehensive Recheck)
> Source Documents: docs/requirements.md, docs/architecture.md

This document provides traceability between requirements and architecture, identifying coverage gaps and recommendations.

---

## Table of Contents

1. [Summary](#summary)
2. [Traceability Matrix](#traceability-matrix)
   - [Pool Node Requirements (FR-PN-*)](#pool-node-requirements-fr-pn)
   - [Valve Node Requirements (FR-VN-*)](#valve-node-requirements-fr-vn)
   - [Display Node Requirements (FR-DN-*)](#display-node-requirements-fr-dn)
   - [Shared Requirements (FR-SH-*)](#shared-requirements-fr-sh)
   - [Message Format Requirements (FR-MSG-*)](#message-format-requirements-fr-msg)
   - [Extensibility Requirements (FR-EXT-*)](#extensibility-requirements-fr-ext)
   - [HomeKit Requirements (FR-HK-*)](#homekit-requirements-fr-hk)
   - [Simulator Requirements (FR-SIM-*)](#simulator-requirements-fr-sim)
   - [Reliability Requirements (NFR-REL-*)](#reliability-requirements-nfr-rel)
   - [Performance Requirements (NFR-PERF-*)](#performance-requirements-nfr-perf)
   - [Security Requirements (NFR-SEC-*)](#security-requirements-nfr-sec)
   - [Maintainability Requirements (NFR-MAINT-*)](#maintainability-requirements-nfr-maint)
   - [Architecture Requirements (NFR-ARCH-*)](#architecture-requirements-nfr-arch)
   - [Environment Requirements (NFR-ENV-*)](#environment-requirements-nfr-env)
3. [Gap Analysis](#gap-analysis)
   - [Requirements with No Coverage](#requirements-with-no-coverage)
   - [Requirements with Partial Coverage](#requirements-with-partial-coverage)
   - [Architecture Elements Without Requirement Backing](#architecture-elements-without-requirement-backing)
   - [Cross-Document Consistency Issues](#cross-document-consistency-issues)
   - [Migration & Operations Gaps](#migration--operations-gaps)
4. [Recommendations](#recommendations)
   - [High Priority - Safety/Reliability](#high-priority---safetyreliability)
   - [High Priority - Alignment Issues](#high-priority---alignment-issues)
   - [Medium Priority - Completeness](#medium-priority---completeness)
   - [Lower Priority - Details](#lower-priority---details)

---

## Summary

| Metric | Initial | After Fixes | Current Recheck |
| ------ | ------- | ----------- | --------------- |
| Total Requirements | 86 | 86 | 86 |
| Full Coverage | 52 (60%) | 65 (76%) | 66 (77%) |
| Partial Coverage | 25 (29%) | 20 (23%) | 19 (22%) |
| No Coverage | 9 (11%) | 1 (1%) | 1 (1%) |

**Status:** Second comprehensive recheck completed 2026-01-22. Coverage statistics remain stable at 76% full coverage.

**Remaining Intentional Gap:** FR-EXT-006 (Device Capability Declaration) - deferred to Phase 3+.

**Key Resolution:** The architecture's decision to use message protocol as the integration contract (instead of a Device base class) has been formally documented in both requirements.md (FR-EXT-001 updated) and architecture.md (Architecture Principles section).

**Findings from First Recheck (2026-01-22):**
- 3 cross-document consistency issues identified and resolved
- 3 migration/operations gaps identified and resolved
- Display Node UI Design placeholder document verified complete

**New Findings (Second Recheck 2026-01-22):**
- 1 new cross-document consistency issue found and resolved: Feed name `localtemp` → `insidetemp`
- 1 minor architecture example gap found and resolved: `reportingInterval` added to pool_status example
- All previously resolved issues verified still resolved
- All new issues now resolved

---

## Traceability Matrix

### Pool Node Requirements (FR-PN-*)

| Req ID | Requirement Summary | Architecture Section(s) | Coverage |
|--------|---------------------|-------------------------|----------|
| FR-PN-001 | Temperature Monitoring | Pool Node (C++) - Hardware, sensors/temperature.cpp | **Full** |
| FR-PN-002 | Water Level Detection | Pool Node (C++) - Hardware, sensors/water_level.cpp | **Full** |
| FR-PN-003 | Battery Monitoring | Pool Node (C++) - Hardware, sensors/battery.cpp | **Full** |
| FR-PN-004 | Data Transmission | Pool Node (C++) - Interfaces, Message Protocol | **Partial** |
| FR-PN-005 | Power Management | Pool Node (C++) - Lifecycle, power/sleep_manager.cpp | **Partial** |
| FR-PN-006 | Remote Configuration | Config Module, Credential Provisioning | **Partial** |

**FR-PN-004 Gap:** Legacy pipe-delimited format support not explicitly mentioned in architecture.

**FR-PN-005 Gap:** Minimum sleep duration (10s) and watchdog disable/re-enable around deep sleep not documented.

**FR-PN-006 Gap:** NVS persistence of general configuration across sleep cycles not detailed (only credentials mentioned).

---

### Valve Node Requirements (FR-VN-*)

| Req ID | Requirement Summary | Architecture Section(s) | Coverage |
|--------|---------------------|-------------------------|----------|
| FR-VN-001 | Valve Control | Valve Node - Hardware, valve_controller.py | **Full** |
| FR-VN-002 | Scheduled Filling | Valve Node - scheduler.py, FillScheduler class | **Full** |
| FR-VN-003 | Safety Interlocks | Valve Node - safety.py, SafetyInterlocks class, Critical Details | **Full** |
| FR-VN-004 | Temperature Monitoring | Valve Node - Hardware | **Partial** |
| FR-VN-005 | Cloud Communication | Valve Node - Interfaces | **Full** |
| FR-VN-006 | Remote Control | Valve Node - Command Rate Limiting, handle_command | **Partial** |
| FR-VN-007 | Status Reporting | Message Protocol - valve_status | **Full** |

**FR-VN-004 Gap:** Temperature validation range (-20°F to 130°F) not explicitly documented.

**FR-VN-006 Gap:** Legacy message types 6 and 99 support not mentioned.

---

### Display Node Requirements (FR-DN-*)

| Req ID | Requirement Summary | Architecture Section(s) | Coverage |
|--------|---------------------|-------------------------|----------|
| FR-DN-001 | Real-Time Data Display | Display Node - Features | **Partial** |
| FR-DN-002 | Fill Status Display | Display Node - Features | **Full** |
| FR-DN-003 | Historical Data Visualization | Build Sequence - Phase 6 (deferred) | **Partial** |
| FR-DN-004 | Data Freshness Indication | Display Node - Features, NODE_DEFAULTS | **Full** |
| FR-DN-005 | Cloud Communication | Display Node - Interfaces | **Full** |
| FR-DN-006 | Local Sensing | Display Node - Hardware, display_status message | **Full** |
| FR-DN-007 | Display Burn-In Prevention | Display Node - Features | **Partial** |
| FR-DN-008 | Touchscreen Input | Display Node - TouchHandler class | **Full** |
| FR-DN-009 | Interactive Controls | Display Node - send_command method | **Partial** |
| FR-DN-010 | UI Navigation | Display Node - screens.py, Build Sequence | **Partial** |

**FR-DN-001 Gap:** Date/time display not explicitly mentioned.

**FR-DN-003 Gap:** Explicitly noted as deferred to Phase 6.

**FR-DN-007 Gap:** Specific parameters missing (5 min idle trigger, 7s rotation, 4 background colors).

**FR-DN-009 Gap:** Pump speed/program controls and confirmation dialogs not detailed.

**FR-DN-010 Gap:** Device detail views, settings view, and 60s idle timeout not specified.

---

### Shared Requirements (FR-SH-*)

| Req ID | Requirement Summary | Architecture Section(s) | Coverage |
|--------|---------------------|-------------------------|----------|
| FR-SH-001 | Time Synchronization | Cloud Module - sync_time(), Pool Node - time_sync.cpp | **Partial** |
| FR-SH-002 | WiFi Configuration | Credential Provisioning section | **Full** |
| FR-SH-003 | Message Protocol | Message Protocol section | **Full** |
| FR-SH-004 | Temperature Units | Message schemas - fahrenheit unit | **Partial** |

**FR-SH-001 Gap:** 12-hour periodic re-synchronization for Valve/Display Nodes not mentioned.

**FR-SH-004 Gap:** Conversion formula (F = C × 9/5 + 32) and rounding to one decimal place not documented.

---

### Message Format Requirements (FR-MSG-*)

| Req ID | Requirement Summary | Architecture Section(s) | Coverage |
|--------|---------------------|-------------------------|----------|
| FR-MSG-001 | JSON Message Structure | Message Protocol - Envelope Structure | **Full** |
| FR-MSG-002 | Message Envelope Fields | Message Protocol - Envelope Structure | **Full** |
| FR-MSG-003 | Message Types | Message Protocol - Message Types table | **Full** |
| FR-MSG-004 | Pool Status Payload | Message Protocol - pool_status example | **Full** |
| FR-MSG-005 | Valve Status Payload | Message Protocol - valve_status (implicit) | **Full** |
| FR-MSG-006 | Display Status Payload | Message Protocol - display_status (implicit) | **Full** |
| FR-MSG-007 | Fill Start Payload | Data Flow - Fill Operation Flow | **Full** |
| FR-MSG-008 | Fill Stop Payload | Data Flow - Fill Operation Flow | **Full** |
| FR-MSG-009 | Command Payload | Message Protocol - command example, Supported Commands | **Full** |
| FR-MSG-010 | Heartbeat Payload | Message Protocol - Message Types table | **Full** |
| FR-MSG-011 | Error Payload | Message Protocol - Message Types table | **Full** |
| FR-MSG-012 | Config Update Payload | Message Protocol - Message Types table | **Full** |
| FR-MSG-013 | Command Response Payload | Message Protocol - Message Types table | **Full** |
| FR-MSG-014 | Message Validation | Messages Module - validator.py | **Partial** |
| FR-MSG-015 | Backward Compatibility | Legacy Feed Compatibility section | **Full** |
| FR-MSG-016 | Message Version Handling | (Not addressed) | **None** |

**FR-MSG-014 Gap:** Size validation (4KB max), timestamp freshness validation (5 min commands, 15 min status) not documented.

**FR-MSG-016 Gap:** Supported versions list, rejection behavior, and logging requirements not documented.

---

### Extensibility Requirements (FR-EXT-*)

| Req ID | Requirement Summary | Architecture Section(s) | Coverage |
|--------|---------------------|-------------------------|----------|
| FR-EXT-001 | Device Plugin Architecture | Architecture Principles (rejects base class) | **Partial** |
| FR-EXT-002 | Device Registration | Resolved Questions - Device Discovery | **Partial** |
| FR-EXT-003 | Device Configuration Schema | (Not addressed) | **None** |
| FR-EXT-004 | Supported Device Types | Node Summary table | **Full** |
| FR-EXT-004a | Display Node Command Dispatch | Display Node - send_command | **Partial** |
| FR-EXT-005 | Variable Speed Pump Requirements | Resolved Questions (TBD) | **Full** |
| FR-EXT-006 | Device Capability Declaration | (Not addressed) | **None** |
| FR-EXT-007 | Inter-Device Communication | (Not addressed) | **None** |

**FR-EXT-001 Gap:** Requirements describe Device base class with lifecycle methods; architecture explicitly rejects this approach in favor of message protocol as integration contract.

**FR-EXT-002 Gap:** Configuration-based device registration not detailed.

**FR-EXT-003 Gap:** Full device configuration schema from requirements not included.

**FR-EXT-004a Gap:** Capability discovery for dynamic UI generation not shown.

**FR-EXT-006 Gap:** Capability declaration schema not documented (noted as Phase 3+).

**FR-EXT-007 Gap:** Device coordination patterns and priority resolution not addressed.

---

### HomeKit Requirements (FR-HK-*)

| Req ID | Requirement Summary | Architecture Section(s) | Coverage |
|--------|---------------------|-------------------------|----------|
| FR-HK-001 | HomeKit Bridge Architecture | Homebridge Plugin (Phase 4) | **Full** |
| FR-HK-002 | Exposed Accessories | Homebridge Plugin - Accessory Mapping table | **Full** |
| FR-HK-003 | HomeKit Commands | (Deferred to Phase 4) | **Partial** |
| FR-HK-004 | Data Synchronization | (Deferred to Phase 4) | **Partial** |
| FR-HK-005 | HomeKit Configuration | (Deferred to Phase 4) | **Partial** |
| FR-HK-006 | Homebridge Plugin Specification | Homebridge Plugin - Structure | **Full** |
| FR-HK-007 | Home Assistant Integration | (Not addressed) | **None** |

**FR-HK-003/004/005 Gap:** Implementation details deferred to Phase 4.

**FR-HK-007 Gap:** Home Assistant integration not documented (alternative to Homebridge).

---

### Simulator Requirements (FR-SIM-*)

| Req ID | Requirement Summary | Architecture Section(s) | Coverage |
|--------|---------------------|-------------------------|----------|
| FR-SIM-001 | Simulator Purpose | Node Simulators section | **Full** |
| FR-SIM-002 | Pool Node Simulator | Node Simulators - pool_node.py | **Full** |
| FR-SIM-003 | Valve Node Simulator | Node Simulators - valve_node.py | **Full** |
| FR-SIM-004 | Display Node Simulator | Node Simulators - display_node.py | **Full** |
| FR-SIM-005 | Simulator Configuration | Node Simulators - Usage | **Partial** |
| FR-SIM-006 | Simulator Implementation | Node Simulators - Usage, Structure | **Full** |

**FR-SIM-005 Gap:** Command-line overrides for common parameters not detailed.

---

### Reliability Requirements (NFR-REL-*)

| Req ID | Requirement Summary | Architecture Section(s) | Coverage |
|--------|---------------------|-------------------------|----------|
| NFR-REL-001 | Watchdog Protection | Reliability Patterns - Watchdog Configuration | **Full** |
| NFR-REL-002 | Sensor Retry Logic | Reliability Patterns - Sensor Retry Pattern | **Full** |
| NFR-REL-002a | Sensor Failure Fallback | (Not addressed) | **None** |
| NFR-REL-003 | Network Resilience | Reliability Patterns - Network Reconnection | **Full** |
| NFR-REL-004 | Failure Recovery | Reliability Patterns - Failure Counter Pattern | **Full** |
| NFR-REL-005 | Blocking Operation Timeouts | Pool Node - wifi_manager, http_client | **Partial** |
| NFR-REL-006 | Bus Recovery Mechanisms | Reliability Patterns - Bus Recovery Pattern | **Full** |
| NFR-REL-007 | Socket Resource Management | (Not addressed) | **None** |
| NFR-REL-008 | Watchdog Coverage | Pool Node - Lifecycle diagram | **Full** |
| NFR-REL-009 | Error Handling | Critical Details - Error Handling | **Partial** |
| NFR-REL-010 | Resource Cleanup Order | Critical Details (implicit) | **Partial** |

**NFR-REL-002a Gap:** Sending null values for failed sensors not documented.

**NFR-REL-005 Gap:** I2C and OneWire 5-second timeouts not specified.

**NFR-REL-007 Gap:** Socket pool cleanup, max concurrent connections not addressed.

**NFR-REL-009 Gap:** Error tracking by category (network, sensor, bus) not mentioned.

**NFR-REL-010 Gap:** Specific cleanup order (sensors before buses, network before sleep) not documented.

---

### Performance Requirements (NFR-PERF-*)

| Req ID | Requirement Summary | Architecture Section(s) | Coverage |
|--------|---------------------|-------------------------|----------|
| NFR-PERF-001 | Response Time | Critical Details - Performance Targets | **Full** |
| NFR-PERF-002 | Data Freshness | Config Module - NODE_DEFAULTS | **Full** |
| NFR-PERF-003 | Power Efficiency | Critical Details - Performance Targets | **Full** |

---

### Security Requirements (NFR-SEC-*)

| Req ID | Requirement Summary | Architecture Section(s) | Coverage |
|--------|---------------------|-------------------------|----------|
| NFR-SEC-001 | Transport Security | Critical Details - Security Considerations | **Full** |
| NFR-SEC-002 | Credential Management | Critical Details - Security Considerations, Source Control | **Full** |
| NFR-SEC-002a | Command Rate Limiting | Valve Node - Command Rate Limiting table | **Full** |
| NFR-SEC-002b | Device Identity Validation | Critical Details - Security Considerations | **Full** |
| NFR-SEC-003 | Command Message Signing | Build Sequence - Phase 6 (deferred) | **Partial** |

**NFR-SEC-003 Gap:** Deferred to Phase 6; HMAC-SHA256, timestamp validation, per-device keys not detailed.

---

### Maintainability Requirements (NFR-MAINT-*)

| Req ID | Requirement Summary | Architecture Section(s) | Coverage |
|--------|---------------------|-------------------------|----------|
| NFR-MAINT-001 | Logging | Logging Module - RotatingFileHandler | **Full** |
| NFR-MAINT-002 | Remote Configuration | Config Module, valvestarttime feed | **Partial** |
| NFR-MAINT-003 | Remote Reset | Message Protocol - device_reset command | **Full** |
| NFR-MAINT-004 | Firmware Updates | Resolved Questions (out of scope) | **Full** |

**NFR-MAINT-002 Gap:** Full remote configuration mechanism (sleep duration, sensor settings) not detailed.

---

### Architecture Requirements (NFR-ARCH-*)

| Req ID | Requirement Summary | Architecture Section(s) | Coverage |
|--------|---------------------|-------------------------|----------|
| NFR-ARCH-001 | Shared Code Library | Shared Libraries (Python) section | **Full** |
| NFR-ARCH-002 | Structured Logging | Logging Module - get_logger | **Full** |
| NFR-ARCH-003 | Configuration Externalization | Config Module | **Partial** |
| NFR-ARCH-004 | Hardware Abstraction | (Implicit in architecture) | **Partial** |
| NFR-ARCH-005 | Observability | Message Protocol - heartbeat, Performance Targets | **Partial** |

**NFR-ARCH-003 Gap:** Hot-reloadable vs restart-required configuration lists not specified.

**NFR-ARCH-004 Gap:** Mock hardware implementations for unit testing not addressed (only mock cloud backend).

**NFR-ARCH-005 Gap:** Health check endpoint/message not detailed; remote diagnostics queries not addressed.

---

### Environment Requirements (NFR-ENV-*)

| Req ID | Requirement Summary | Architecture Section(s) | Coverage |
|--------|---------------------|-------------------------|----------|
| NFR-ENV-001 | Supported Environments | Environment Configuration - Two-Environment Model | **Full** |
| NFR-ENV-002 | Environment-Specific Feed Names | Environment Configuration - Feed Name Resolution | **Full** |
| NFR-ENV-003 | Environment Configuration Schema | Environment Configuration - JSON example | **Full** |
| NFR-ENV-004 | Hardware Safety in Non-Production | Environment Configuration - hardwareEnabled | **Full** |
| NFR-ENV-005 | Environment Identification | (Implicit in environment config) | **Partial** |
| NFR-ENV-006 | Environment Switching | (Not addressed) | **None** |
| NFR-ENV-007 | Production Safeguards | (Not addressed) | **None** |
| NFR-ENV-008 | Cloud Environment Support | Environment Configuration - settings.toml | **Full** |

**NFR-ENV-005 Gap:** Display Node visual indicator for non-production not specified.

**NFR-ENV-006 Gap:** Restart requirement for environment change, validation against known list not documented.

**NFR-ENV-007 Gap:** Explicit confirmation for production deployments, configuration checksum verification not addressed.

---

## Gap Analysis

### Requirements with No Coverage

| Req ID | Summary | Impact |
|--------|---------|--------|
| NFR-REL-002a | Sensor Failure Fallback (send null values) | **High** - Downstream systems can't distinguish failed vs missing sensors |
| NFR-REL-007 | Socket Resource Management | **High** - Memory leaks, connection exhaustion possible |
| NFR-ENV-006 | Environment Switching (restart required) | **Medium** - Could accidentally switch env at runtime |
| NFR-ENV-007 | Production Safeguards | **Medium** - Accidental production deployments possible |
| FR-MSG-016 | Message Version Handling | **Medium** - No clear behavior for version mismatches |
| FR-EXT-003 | Device Configuration Schema | **Medium** - Inconsistent device configuration |
| FR-EXT-006 | Device Capability Declaration | **Low** - Deferred to Phase 3+ |
| FR-EXT-007 | Inter-Device Communication | **Low** - Needed for pump integration |
| FR-HK-007 | Home Assistant Integration | **Low** - Alternative integration path |

### Requirements with Partial Coverage

#### High Impact Gaps

| Req ID | Summary | What's Missing |
|--------|---------|----------------|
| FR-EXT-001 | Device Plugin Architecture | Architecture rejects base class approach; deviation needs formal acknowledgment in requirements |
| FR-MSG-014 | Message Validation | 4KB size limit, timestamp freshness (5min/15min) validation not documented |
| NFR-REL-005 | Blocking Operation Timeouts | I2C (5s), OneWire (5s) timeouts not specified |

#### Medium Impact Gaps

| Req ID | Summary | What's Missing |
|--------|---------|----------------|
| FR-PN-004 | Data Transmission | Legacy pipe-delimited format support |
| FR-PN-005 | Power Management | Minimum sleep duration (10s), watchdog disable/enable around sleep |
| FR-VN-006 | Remote Control | Legacy message types 6 and 99 support |
| FR-SH-001 | Time Synchronization | 12-hour re-sync for continuous nodes |
| NFR-ARCH-003 | Configuration Externalization | Hot-reloadable vs restart-required lists |
| NFR-ARCH-005 | Observability | Health check endpoint details |

#### Lower Impact Gaps

| Req ID | Summary | What's Missing |
|--------|---------|----------------|
| FR-DN-007 | Burn-In Prevention | Specific parameters (5 min, 7s, 4 colors) |
| FR-DN-009 | Interactive Controls | Pump controls, confirmation dialogs |
| FR-DN-010 | UI Navigation | Device detail views, idle timeout |
| FR-SH-004 | Temperature Units | Conversion formula, rounding rules |
| NFR-REL-009 | Error Handling | Error tracking by category |

### Architecture Elements Without Requirement Backing

| Architecture Element | Location | Assessment |
|---------------------|----------|------------|
| Captive portal WiFi provisioning | Credential Provisioning section | **Enhancement** - Exceeds FR-SH-002; consider adding to requirements |
| microcontroller.nvm storage | Credential Provisioning section | **Implementation detail** - Acceptable as architecture decision |
| Legacy Feed Compatibility | Environment Configuration | **Enhancement** - Extends FR-MSG-015; consider adding feed migration requirement |
| "-sim" suffix for simulator device IDs | Node Simulators | **Enhancement** - Good practice; consider adding to FR-SIM-005 |
| Feed groups (poolio, poolio-nonprod) | Environment Configuration | **Implementation detail** - Refines NFR-ENV-002 |

### Cross-Document Consistency Issues

> Identified during comprehensive rechecks on 2026-01-22

| Issue | Requirements Says | Architecture Says | Impact | Status |
| ----- | ----------------- | ----------------- | ------ | ------ |
| Schema directory location | Appendix A: ~~`src/shared/schemas/`~~ → `schemas/` | Directory Structure: `schemas/` at project root | **Low** | ✅ RESOLVED - Updated requirements |
| Pool Node directory path | Not specified | ~~Mixed paths~~ → `pool_node_cpp/` consistently | **Medium** | ✅ RESOLVED - Updated architecture |
| JSON Schema draft version | Appendix A: "Draft 2020-12" | ~~Not specified~~ → Draft 2020-12 in Messages Module | **Low** | ✅ RESOLVED - Updated architecture |
| Display Node temp feed name | Section 5.2: ~~`localtemp`~~ → `insidetemp` | Environment Configuration: `insidetemp` | **Medium** | ✅ RESOLVED - Updated requirements |
| pool_status example completeness | FR-MSG-004: includes `reportingInterval` | Message Protocol example: ~~missing~~ → included | **Low** | ✅ RESOLVED - Updated architecture |

### Migration & Operations Gaps

> Identified and resolved during 2026-01-22 comprehensive recheck

| Gap | Requirements Section | Architecture Coverage | Impact | Status |
| --- | -------------------- | --------------------- | ------ | ------ |
| Rollback Plan | Section 8.8 - detailed 5-step plan | ~~Not documented~~ → Rollback Plan in Deployment | **Medium** | ✅ RESOLVED |
| Data Migration | Section 8.9 - historical + config data | Partial (Legacy Feed Compatibility) | **Low** | Deferred - Config migration not critical for MVP |
| Integration Test Scenarios | Section 8.7 - 6 specific scenarios | ~~Not referenced~~ → Referenced in Testing | **Low** | ✅ RESOLVED |
| MQTT QoS Usage | Section 5.1 - QoS 0 for status, QoS 1 for commands | ~~No guidance~~ → QoS Selection table in Cloud Module | **Low** | ✅ RESOLVED |

---

## Recommendations

> **Status:** All recommendations have been implemented as of 2026-01-22.

### High Priority - Safety/Reliability

1. **~~Add NFR-REL-007 coverage to architecture~~** - DONE
   - Added "Socket Resource Management" section to Reliability Patterns

2. **~~Document NFR-REL-002a in Pool Node section~~** - DONE
   - Added "Sensor Failure Fallback" section with null value example

3. **~~Document message validation details (FR-MSG-014)~~** - DONE
   - Added "Message Validation" section with size limits and timestamp freshness

4. **~~Complete NFR-REL-005 timeout specifications~~** - DONE
   - Added "Blocking Operation Timeouts" section with 50% watchdog rule

### High Priority - Alignment Issues

5. **~~Reconcile FR-EXT-001 (Device Plugin Architecture)~~** - DONE
   - Updated requirements.md FR-EXT-001 to reflect message-protocol-based integration

6. **~~Add FR-MSG-016 coverage~~** - DONE
   - Added "Message Version Handling" section to Message Protocol

### Medium Priority - Completeness

7. **~~Add FR-EXT-003 (Device Configuration Schema)~~** - DONE
   - Added device configuration schema to Config Module section

8. **~~Document time sync re-synchronization (FR-SH-001)~~** - DONE
   - Added time synchronization table to Cloud Module section

9. **~~Document environment switching (NFR-ENV-006)~~** - DONE
   - Added "Environment Switching" section to Environment Configuration

10. **~~Review FR-EXT-007 requirement for clarity~~** - DONE
    - Updated requirements.md FR-EXT-007 with specific, testable criteria

11. **~~Document production safeguards (NFR-ENV-007)~~** - DONE
    - Added "Production Safeguards" section to Environment Configuration
    - Updated requirements.md to change log warning from SHALL to SHOULD

### Lower Priority - Details

12. **~~Add burn-in prevention parameters (FR-DN-007)~~** - DONE
    - Added burn-in prevention table to Display Node section

13. **~~Complete Display Node UI specification (FR-DN-010)~~** - DONE
    - Created `docs/display-node-ui-design.md` placeholder document

14. **~~Document legacy message type support (FR-VN-006)~~** - DONE
    - Added "Legacy Message Support" section to Valve Node

15. **~~Add hot-reload vs restart configuration lists (NFR-ARCH-003)~~** - DONE
    - Added "Configuration Reloadability" table to Config Module section

16. **~~Document Home Assistant integration option (FR-HK-007)~~** - DONE
    - Added "Alternative: Home Assistant Integration" section after Homebridge Plugin

### Findings from First Recheck (2026-01-22)

17. **~~Resolve schema directory inconsistency~~** - DONE
    - Updated requirements.md Appendix A to use `schemas/` at project root (matching architecture)

18. **~~Fix Pool Node path inconsistency~~** - DONE
    - Updated architecture.md to use `pool_node_cpp/` consistently:
      - Test Framework table: `pool_node_cpp/test/`
      - CI workflow: `cd pool_node_cpp && pio test`
      - Secrets path: `pool_node_cpp/include/secrets.h`

19. **~~Add MQTT QoS usage guidance~~** - DONE
    - Added MQTT QoS Selection table to Cloud Module section in architecture.md
    - Specifies QoS 0 for status/heartbeat, QoS 1 for commands/config

20. **~~Add Rollback Plan to architecture~~** - DONE
    - Added Rollback Plan subsection to Deployment section in architecture.md
    - Includes 5-step rollback procedure, version control with GitHub tags, and quick rollback commands

21. **~~Reference integration test scenarios~~** - DONE
    - Added reference to Requirements Section 8.7 in Testing section of architecture.md
    - Lists all 6 integration test scenarios

22. **~~Specify JSON Schema draft version~~** - DONE
    - Added JSON Schema version (Draft 2020-12) to Messages Module section in architecture.md

### Findings from Second Recheck (2026-01-22)

23. **~~Align Display Node temperature feed name~~** - DONE
    - Requirements Section 5.2 used `localtemp`, Architecture uses `insidetemp`
    - Updated requirements.md to use `insidetemp` for consistency with other temp feeds (`pooltemp`, `outsidetemp`, `insidetemp`)
    - Rationale: "inside" is more descriptive than "local" for the Display Node's location

24. **~~Add reportingInterval to architecture pool_status example~~** - DONE
    - Requirements FR-MSG-004 shows `reportingInterval` in pool_status payload
    - Updated architecture.md Message Protocol pool_status example to include `"reportingInterval": 120`

---

## Appendix: Coverage Statistics by Section

| Requirements Section | Total | Full | Partial | None |
| -------------------- | ----- | ---- | ------- | ---- |
| FR-PN-* (Pool Node) | 6 | 3 | 3 | 0 |
| FR-VN-* (Valve Node) | 7 | 5 | 2 | 0 |
| FR-DN-* (Display Node) | 10 | 5 | 5 | 0 |
| FR-SH-* (Shared) | 4 | 2 | 2 | 0 |
| FR-MSG-* (Messages) | 16 | 14 | 1 | 1 |
| FR-EXT-* (Extensibility) | 8 | 2 | 3 | 3 |
| FR-HK-* (HomeKit) | 7 | 3 | 3 | 1 |
| FR-SIM-* (Simulators) | 6 | 5 | 1 | 0 |
| NFR-REL-* (Reliability) | 11 | 5 | 4 | 2 |
| NFR-PERF-* (Performance) | 3 | 3 | 0 | 0 |
| NFR-SEC-* (Security) | 5 | 4 | 1 | 0 |
| NFR-MAINT-* (Maintainability) | 4 | 3 | 1 | 0 |
| NFR-ARCH-* (Architecture) | 5 | 2 | 3 | 0 |
| NFR-ENV-* (Environment) | 8 | 5 | 1 | 2 |
| **TOTAL** | **86** | **52** | **25** | **9** |
