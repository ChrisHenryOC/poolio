# Performance Review for PR #101

## Summary

This PR establishes the initial C++ project structure for the battery-powered Pool Node. The code is minimal scaffolding with appropriate build configuration. There are a few minor performance observations, but given this is foundational code with sensor reading and deep sleep cycles yet to be implemented, the current approach is reasonable.

## Findings

### Critical

None.

### High

None.

### Medium

**Startup Delay** - `pool_node_cpp/src/main.cpp:43` - The `delay(1000)` after `Serial.begin()` is a fixed blocking wait that consumes battery power unnecessarily on every wake cycle. For a battery-powered device using deep sleep, every millisecond of active time matters. Consider:

- Using a shorter delay (100-200ms is usually sufficient for serial initialization)
- Making the delay conditional on DEBUG_LOGGING (skip it entirely in production)
- Using `while (!Serial && millis() < 500)` pattern to wait only as long as needed

```cpp
#if DEBUG_LOGGING
    // Wait for serial only in debug mode
    unsigned long start = millis();
    while (!Serial && millis() - start < 500) {
        // Wait up to 500ms for serial connection
    }
#endif
```

**Loop Delay** - `pool_node_cpp/src/main.cpp:161` - The `delay(10000)` in loop is expected placeholder behavior per the comment, but should be replaced with deep sleep before any production use. A 10-second blocking delay with the ESP32 fully active would drain the battery rapidly. The comment correctly indicates this will be replaced.

### Low

**String Literals in Flash** - `pool_node_cpp/src/main.cpp:145-156` - Multiple string literals are used with `Serial.println()`. On ESP32 with Arduino framework, string literals are typically stored in flash by default (unlike AVR), so explicit PROGMEM is not required. However, if RAM becomes constrained as the project grows, consider using the `F()` macro for consistency and to ensure flash storage:

```cpp
Serial.println(F("Pool Node Starting"));
```

This is informational only; ESP32 has sufficient RAM and the strings are small.

### Info

**ArduinoJson Version** - `pool_node_cpp/platformio.ini:76` - ArduinoJson v7 is specified, which uses a more memory-efficient approach than v6. Good choice for an embedded device.

**Build Configuration** - The environment-based build flags (`-DENVIRONMENT`, `-DFEED_PREFIX`, `-DDEBUG_LOGGING`) allow for production builds with logging disabled, which will reduce code size and avoid unnecessary serial output that would otherwise consume CPU cycles and power during wake periods.

**Memory Efficiency Observations** - For future implementation:

- Use `StaticJsonDocument` rather than `DynamicJsonDocument` for fixed-size JSON messages to avoid heap allocation
- Consider pre-allocating WiFi and MQTT client buffers
- Monitor heap fragmentation if WiFi reconnections become frequent

## Power Consumption Notes for Future Implementation

Given this is a battery-powered device, these patterns should be considered as the implementation progresses:

1. **WiFi**: Minimize connection time; consider using static IP to skip DHCP
2. **Sensors**: Power sensors via GPIO pins that can be disabled during deep sleep
3. **I2C/OneWire**: Implement bus recovery with timeouts rather than infinite waits
4. **MQTT**: Single publish batch rather than multiple individual publishes
5. **Deep Sleep**: Use RTC memory to preserve state across sleep cycles

These are not issues with the current PR but guidance for the implementation phase.
