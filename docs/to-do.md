# Poolio Implementation To-Do

## Legend

- ✅ Complete
- 🔄 In Progress
- ⬚ Not Started

---

## Phase 1: Foundation

| Status | Issue | Title |
|--------|-------|-------|
| ✅ | #9 | [Setup] Project Setup and Structure |
| ✅ | #10 | [Model] Message Type Classes |
| ✅ | #11 | [Core] Message Envelope and Encoding |
| ✅ | #12 | [Core] Message Validation (Simple) |
| ✅ | #83 | feat: General-purpose on-device test framework for CircuitPython |
| ⬚ | #13 | [Core] Mock Cloud Backend for Testing |
| ⬚ | #14 | [Integration] AdafruitIO HTTP Client |
| ⬚ | #15 | [Integration] AdafruitIO MQTT Client and Base Class Extraction |
| ⬚ | #16 | [Core] Configuration Management |
| ⬚ | #17 | [Core] Logging Module |
| ⬚ | #18 | [Core] Sensor Utilities |
| ⬚ | #19 | [Test] Foundation Integration Test |
| ⬚ | #85 | feat: On-device tests for shared library modules (Phase 2) |

## Phase 2: Pool Node (C++)

| Status | Issue | Title |
|--------|-------|-------|
| ⬚ | #20 | [Setup] Pool Node Project Setup |
| ⬚ | #21 | [Model] C++ Message Library |
| ⬚ | #22 | [Core] C++ Config and Logging |
| ⬚ | #23 | [Core] WiFi Manager with Timeout |
| ⬚ | #24 | [Integration] Time Sync and HTTP Client |
| ⬚ | #25 | [Core] Temperature Sensor (DS18X20) |
| ⬚ | #26 | [Core] Water Level Sensor (Float Switch) |
| ⬚ | #27 | [Core] Battery Monitor (LC709203F) |
| ⬚ | #28 | [Core] Watchdog and Sleep Manager |
| ⬚ | #29 | [Integration] Pool Node Controller Integration |
| ⬚ | #30 | [Test] Pool Node Hardware Testing |

## Phase 3: Valve Node (CircuitPython)

| Status | Issue | Title |
|--------|-------|-------|
| ⬚ | #31 | [Setup] Valve Node Project Setup |
| ⬚ | #32 | [Core] Fill Scheduler |
| ⬚ | #33 | [Core] Safety Interlocks |
| ⬚ | #34 | [Core] Valve Controller Core |
| ⬚ | #35 | [Integration] Valve Node Integration |
| ⬚ | #36 | [Test] Valve Node Hardware Testing |

## Phase 4: Display Node (CircuitPython)

| Status | Issue | Title |
|--------|-------|-------|
| ⬚ | #37 | [Setup] Display Node Project Setup |
| ⬚ | #38 | [Core] Theme and Color Constants |
| ⬚ | #39 | [Core] Base Widget Classes |
| ⬚ | #40 | [Core] Touch Handler |
| ⬚ | #41 | [Spike] Display Node UI Spike |
| ⬚ | #42 | [Tool] Touch Calibration Utility |
| ⬚ | #43 | [Core] Main Dashboard Screen Layout |
| ⬚ | #44 | [Core] Pool Node Detail Screen |
| ⬚ | #45 | [Core] Valve Node Detail Screen |
| ⬚ | #46 | [Core] Settings Screen |
| ⬚ | #47 | [Core] Stale Data Indicators |
| ⬚ | #48 | [Core] Non-Production Indicator |
| ⬚ | #49 | [Core] Burn-In Prevention |
| ⬚ | #50 | [Core] Local Sensor Reading (AHTx0) |
| ⬚ | #51 | [Core] Dashboard State Management |
| ⬚ | #52 | [Integration] Dashboard Controller - Message Handling |
| ⬚ | #53 | [Integration] Dashboard Controller - Commands and Navigation |
| ⬚ | #54 | [Integration] Display Node Integration |
| ⬚ | #55 | [Test] Display Node Hardware Testing |
| ⬚ | #56 | [Core] Historical Screen |
| ⬚ | #86 | feat: On-device tests for node-specific modules (Phase 3) |

## Phase 5: Simulators

| Status | Issue | Title |
|--------|-------|-------|
| ⬚ | #57 | [Core] Simulator Common Utilities |
| ⬚ | #58 | [Core] Pool Node Simulator |
| ⬚ | #59 | [Core] Valve Node Simulator |
| ⬚ | #60 | [Core] Display Node Simulator |
| ⬚ | #61 | [Test] Integration Test Suite - Normal Flow |
| ⬚ | #62 | [Test] Integration Test Suite - Error Scenarios |
| ⬚ | #63 | [Test] Integration Test Suite - Edge Cases |

## Phase 6: Nonprod Deployment

| Status | Issue | Title |
|--------|-------|-------|
| ⬚ | #64 | [Setup] Adafruit IO Feed Setup - Nonprod |
| ⬚ | #65 | [Setup] Deploy Script for CircuitPython |
| ⬚ | #66 | [Setup] Configuration Files - Nonprod |
| ⬚ | #67 | [Integration] Pool Node Nonprod Build and Deploy |
| ⬚ | #68 | [Integration] Valve Node Nonprod Deployment |
| ⬚ | #69 | [Integration] Display Node Nonprod Deployment |
| ⬚ | #70 | [Test] Nonprod System Integration Test |
| ⬚ | #71 | [Test] Nonprod 1-Week Stability Test |

## Phase 7: Production Deployment

| Status | Issue | Title |
|--------|-------|-------|
| ⬚ | #72 | [Setup] Adafruit IO Feed Setup - Production |
| ⬚ | #73 | [Setup] Configuration Files - Production |
| ⬚ | #74 | [Docs] Pre-Production Checklist |
| ⬚ | #75 | [Integration] Production Deployment |
| ⬚ | #76 | [Test] Production Monitoring (48 hours) |
| ⬚ | #77 | [Docs] Post-Deployment Documentation |

---

## Summary

| Phase | Total | Complete | Remaining |
|-------|-------|----------|-----------|
| 1. Foundation | 13 | 5 | 8 |
| 2. Pool Node | 11 | 0 | 11 |
| 3. Valve Node | 6 | 0 | 6 |
| 4. Display Node | 21 | 0 | 21 |
| 5. Simulators | 7 | 0 | 7 |
| 6. Nonprod | 8 | 0 | 8 |
| 7. Production | 6 | 0 | 6 |
| **Total** | **72** | **5** | **67** |
