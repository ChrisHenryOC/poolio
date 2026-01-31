# Test Coverage Review for PR #95

## Summary

This PR adds 44 on-device tests across three new test files covering MockBackend, configuration management, and retry logic. The tests follow good Arrange-Act-Assert structure and use descriptive names. However, the tests largely duplicate existing unit tests rather than testing device-specific behavior, and critical on-device functionality (bus recovery, Config/load_config) remains untested.

## Findings

### High

**Bus recovery functions completely untested** - `src/shared/sensors/bus_recovery.py`

The `recover_i2c_bus()` and `recover_onewire_bus()` functions are exported from the sensors module but have no on-device tests. These are precisely the functions that **require** device testing since they interact with actual hardware GPIO:

```python
# From src/shared/sensors/__init__.py
from .bus_recovery import recover_i2c_bus, recover_onewire_bus
```

The `tests/device/fixtures.py` provides `requires_i2c()` and `requires_onewire()` helpers specifically for conditionally running hardware tests, but they are not used.

Recommendation: Add tests in `tests/device/shared/test_sensors.py` that:
1. Skip when hardware unavailable using fixtures
2. Test basic recovery sequence executes without error
3. Verify recovery returns True on success

---

**Config and load_config not tested on device** - `tests/device/shared/test_config.py`

The `Config` class and `load_config()` function are exported from `shared.config` but have no on-device tests:

| Export | Unit Tests | Device Tests |
|--------|------------|--------------|
| ConfigurationError | Yes | No (via assert_raises) |
| VALID_ENVIRONMENTS | Yes | No |
| NODE_DEFAULTS | Yes | Yes |
| validate_environment | Yes | Yes |
| get_feed_name | Yes | Yes |
| select_api_key | Yes | Yes |
| EnvironmentConfig | Yes | Yes |
| **Config** | Yes | **No** |
| **load_config** | Yes | **No** |

The `load_config()` function is the primary entry point for configuration on actual devices. Testing it on-device would validate CircuitPython dictionary handling.

Recommendation: Add tests for `Config.get()` and `load_config()` for each node type.

---

**On-device tests duplicate unit tests rather than testing device-specific behavior** - All test files

Comparing device tests to unit tests shows significant overlap:

| Test | Device File | Unit File |
|------|-------------|-----------|
| retry success first try | `test_sensors.py:36` | `test_retry.py:12` |
| retry fails then succeeds | `test_sensors.py:60` | `test_retry.py:22` |
| retry exhausted | `test_sensors.py:71` | `test_retry.py:49` |
| validate_environment prod | `test_config.py:55` | `test_config.py:142` |
| get_feed_name prod | `test_config.py:82` | `test_config.py:194` |

These tests are valuable for validating CircuitPython compatibility, but they don't test **device-specific** behavior like:
- Actual time.sleep() behavior on ESP32
- Memory constraints on device
- Hardware GPIO interactions

Recommendation: Add at least one hardware-integration test per module that exercises actual device capabilities (timing, I2C initialization, etc.).

---

### Medium

**MockBackend publish/disconnect race condition not tested** - `tests/device/shared/test_cloud.py`

The device tests verify MockBackend state transitions but miss a potential race condition: what happens when you publish after disconnect?

```python
# Missing test case
def test_mock_backend_publish_after_disconnect():
    backend = MockBackend(environment="test")
    backend.connect()
    backend.disconnect()
    # What should happen here?
    result = backend.publish("test-feed", "value")
```

The current implementation allows publishing while disconnected, which may or may not be intended behavior. Per Kent Beck's "Passes the tests" rule, if this behavior is intentional, there should be a test documenting it.

Recommendation: Add explicit test for publish-after-disconnect behavior to document expected behavior.

---

**Retry timing tests may be flaky on resource-constrained devices** - `tests/device/shared/test_sensors.py:117,132`

The timing tests use `assert_greater(delay_1, 0.005)` which assumes precise timing. CircuitPython on ESP32 may have timing jitter due to WiFi interrupts or garbage collection:

```python
# Line 128-129
delay_1 = tracker.call_times[1] - tracker.call_times[0]
assert_greater(delay_1, 0.005, "Expected delay between retries")
```

With base_delay=0.01 (10ms), requiring >5ms may occasionally fail due to measurement overhead.

Recommendation: Use more generous timing tolerances (e.g., 0.001 instead of 0.005) or document that test may be flaky under load.

---

**MockCallTracker in fixtures.py but only used for retry tests** - `tests/device/fixtures.py:136`

The `MockCallTracker` class is well-designed with `call_times` tracking for timing verification, but it is only used by `test_sensors.py`. Consider whether it belongs in a shared fixtures module or should be local to test_sensors.py.

Additionally, `MockCallTracker.reset()` method is defined but never called in any test.

Recommendation: Either use `reset()` in tests or remove it to follow Kent Beck's "Fewest elements" rule.

---

**No negative test for validate_environment error message content** - `tests/device/shared/test_config.py:69`

The test verifies that invalid environment raises `ConfigurationError` but doesn't verify the error message contains useful information:

```python
def test_validate_environment_invalid():
    """validate_environment rejects invalid environment."""
    assert_raises(ConfigurationError, validate_environment, "invalid")
```

The unit tests in `test_config.py:160` verify message content with `match="Unknown environment"`.

Recommendation: Device test should verify error message includes the invalid environment name for debugging on actual hardware.

---

### Low

**Test count in docs (71) should be verified** - `CLAUDE.md:424`, `README.md:100`

The PR updates device test count from 27 to 71, a delta of 44 new tests. Manual count:

| File | Tests |
|------|-------|
| test_cloud.py | 17 |
| test_config.py | 17 |
| test_sensors.py | 10 |
| **New total** | **44** |

Plus existing 27 = 71. The count appears accurate.

---

**Hardcoded environment strings** - Multiple locations

Tests use hardcoded `"test"`, `"prod"`, `"nonprod"` strings rather than constants. This is acceptable for tests but could lead to drift if environment names change.

---

## TDD Assessment

The tests show **mixed evidence of TDD practices**:

**Positive TDD indicators:**
- Tests describe behavior ("validate_environment accepts 'prod'") not implementation
- Good coverage of edge cases (invalid environment, missing API key)
- Tests are simple and focused with single assertions per test

**Negative TDD indicators:**
- Tests closely mirror existing unit tests (suggests copy-paste, not test-first)
- No hardware-specific tests despite device test framework (suggests code-first)
- Missing tests for exported functions (Config, load_config, bus recovery)

The `MockCallTracker` fixture demonstrates good test infrastructure design that could have been written before implementation. However, the lack of bus recovery tests despite providing `requires_i2c()` and `requires_onewire()` fixtures suggests the tests were written to validate existing code rather than drive new implementation.

## Recommendations Summary

| Priority | Recommendation |
|----------|----------------|
| High | Add on-device tests for `recover_i2c_bus()` and `recover_onewire_bus()` with hardware skip |
| High | Add tests for `Config` class and `load_config()` function |
| High | Add at least one true hardware-integration test per module |
| Medium | Add test for publish-after-disconnect behavior |
| Medium | Increase timing tolerances to reduce flakiness on device |
| Medium | Remove unused `MockCallTracker.reset()` method or add test using it |
| Low | Verify error message content in negative tests |
