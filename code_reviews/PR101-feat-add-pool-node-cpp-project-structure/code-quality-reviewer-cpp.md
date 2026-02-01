# Code Quality Review (C++) for PR #101

## Summary

This PR establishes the foundational PlatformIO project structure for the C++ Pool Node, including environment configuration for nonprod/prod builds, native test scaffolding, and a minimal skeleton main.cpp. The code follows Beck's principles well with minimal scaffolding and clear intention, though the main.cpp could benefit from small improvements to modern C++ idioms and the native test environment has a minor configuration gap.

## Findings

### Critical

None

### High

None

### Medium

**Native test environment missing framework declaration** - `pool_node_cpp/platformio.ini:96-105`

The `[env:native]` section defines a test environment but does not declare a test framework (e.g., Unity, GoogleTest). While PlatformIO defaults to Unity, explicitly declaring the framework improves clarity and ensures consistent behavior.

```ini
[env:native]
; Native test environment for running unit tests on host machine
; Usage: pio test -e native
platform = native
build_flags =
    -DENVIRONMENT=\"test\"
    -DFEED_PREFIX=\"test-\"
    -DDEBUG_LOGGING=1
lib_deps =
    bblanchon/ArduinoJson@^7
```

**Recommendation**: Add `test_framework = unity` (or googletest if preferred) to make the test configuration explicit and self-documenting.

---

**Delay in setup() may mask boot issues** - `pool_node_cpp/src/main.cpp:143`

The 1000ms delay after Serial.begin() is a common pattern to allow serial connection, but on battery-powered devices this wastes power. Additionally, unconditional delays can mask timing-sensitive boot issues.

```cpp
void setup() {
    Serial.begin(115200);
    delay(1000);  // 1 second unconditional delay
```

**Recommendation**: Consider making this delay conditional on DEBUG_LOGGING, or use a shorter delay with a serial connection check. For battery-powered operation, minimize wake time.

### Low

**Magic number for serial baud rate** - `pool_node_cpp/src/main.cpp:142`

The baud rate 115200 is repeated inline. While common, extracting to a named constant improves readability and ensures consistency with `platformio.ini:68` which also specifies `monitor_speed = 115200`.

```cpp
Serial.begin(115200);
```

**Recommendation**: Define as `constexpr uint32_t SERIAL_BAUD_RATE = 115200;` or reference the platformio.ini value via build flag to avoid drift.

---

**Preprocessor fallback defines could use constexpr** - `pool_node_cpp/src/main.cpp:127-139`

The fallback definitions use C-style `#define` macros. While necessary for string macros like ENVIRONMENT, the DEBUG_LOGGING flag could be converted to a constexpr bool for type safety.

```cpp
#ifndef DEBUG_LOGGING
#define DEBUG_LOGGING 0
#endif
```

**Recommendation**: For boolean flags, consider `constexpr bool kDebugLogging = DEBUG_LOGGING;` after the preprocessor define, allowing type-safe usage in code. Not critical for this skeleton.

### Observations

**Good: Clear separation of environments** - `pool_node_cpp/platformio.ini:78-94`

The nonprod/prod environment separation with appropriate feed prefixes and debug flags is clean and follows the project's established environment model from CLAUDE.md.

**Good: Secrets handling** - `pool_node_cpp/include/secrets.h.example`

The example file with clear instructions and .gitignore protection prevents accidental credential commits. The comment "secrets.h is in .gitignore - never commit actual secrets" is helpful.

**Good: Minimal main.cpp** - `pool_node_cpp/src/main.cpp`

The skeleton follows Beck's "Fewest elements" rule - it compiles, prints diagnostic info, and stubs the loop. No premature abstractions or over-engineering.

**Good: ArduinoJson version pinning** - `pool_node_cpp/platformio.ini:76`

Using `@^7` pins to major version 7 with semver flexibility. ArduinoJson 7 uses a different API than v6, so major version pinning is appropriate.

**Good: Documentation in platformio.ini** - `pool_node_cpp/platformio.ini:47-59`

The header comments clearly explain build commands and usage. Self-documenting configuration.

**Beck's Four Rules Assessment**:

| Rule | Assessment |
|------|------------|
| Passes the tests | No tests yet, but native test environment is scaffolded - appropriate for initial setup |
| Reveals intention | Good - File header documents purpose, environment names are clear |
| No duplication | Good - Build flags properly inherit from [env] base |
| Fewest elements | Excellent - Minimal skeleton, no premature abstractions |

## C++ Best Practices Checklist

| Practice | Status | Notes |
|----------|--------|-------|
| Modern C++ (11/14/17) | N/A | Skeleton only, no complex code yet |
| RAII | N/A | No resources acquired yet |
| Const correctness | N/A | No functions to evaluate |
| Smart pointers | N/A | No dynamic allocation |
| Naming conventions | Good | UPPER_SNAKE_CASE for macros |
| ESP32/Arduino idioms | Good | Stack-based, minimal |
| ArduinoJson | Good | Version pinned, not used yet |
