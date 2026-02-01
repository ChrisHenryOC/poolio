---
allowed-tools: Bash(pio test:*),Bash(pio run:*),Bash(pio device:*)
description: Run PlatformIO C++ tests (native and device)
---

Run C++ tests for pool node: $ARGUMENTS

## Test Environments

| Environment | Purpose | Command |
|-------------|---------|---------|
| `native` | Host-based unit tests | `pio test -e native` |
| `nonprod` | Build verification | `pio run -e nonprod` |
| `prod` | Production build | `pio run -e prod` |

## Step 1: Run Native Unit Tests

```bash
cd pool_node_cpp
pio test -e native
```

These tests run on the host machine (no hardware required).

**Pass criteria:** All tests pass, no memory errors.

## Step 2: Build Verification

```bash
pio run -e nonprod
```

Verify the build compiles without errors or warnings.

## Step 3: Device Tests (Optional)

If `--device` is specified or hardware testing requested:

```bash
# Upload to device
pio run -e nonprod -t upload

# Monitor serial output
pio device monitor --baud 115200
```

Exit monitor: `Ctrl+]`

## Test Patterns

**Unit tests location:** `pool_node_cpp/test/`

**Test file naming:** `test_*.cpp`

**Test structure (Unity framework):**

```cpp
#include <unity.h>

void setUp(void) { /* runs before each test */ }
void tearDown(void) { /* runs after each test */ }

void test_function_does_expected_thing(void) {
    // Arrange
    int input = 42;

    // Act
    int result = myFunction(input);

    // Assert
    TEST_ASSERT_EQUAL(84, result);
}

int main(int argc, char **argv) {
    UNITY_BEGIN();
    RUN_TEST(test_function_does_expected_thing);
    return UNITY_END();
}
```

## Troubleshooting

**Tests not found:**

- Check test files are in `test/` directory
- Verify `test_filter` in `platformio.ini` if using filters

**Build errors:**

- Run `pio run -e native -v` for verbose output
- Check library dependencies in `platformio.ini`

**Device upload fails:**

- Verify device connected: `pio device list`
- Check correct port in `platformio.ini`
