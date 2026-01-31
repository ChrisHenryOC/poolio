# Performance Reviewer for PR #93

## Summary

This PR introduces sensor utilities for retry logic and bus recovery (I2C/OneWire) that are well-designed for the ESP32/CircuitPython memory-constrained environment. The code follows resource cleanup best practices with proper try/finally patterns. One minor optimization opportunity exists in the retry function's delay calculation, and the bus recovery logging could potentially be streamlined in resource-critical scenarios.

## Findings

### Critical

None.

### High

None.

### Medium

**Potential memory allocation in tight retry loops** - `src/shared/sensors/retry.py:263-271`

In the retry loop, on each failed attempt, the code performs string formatting for debug logging:

```python
if logger:
    logger.debug(
        "Attempt %d/%d failed: %s, retrying in %.3fs",
        attempt_num,
        total_attempts,
        e,
        delay,
    )
```

On memory-constrained ESP32 devices (~240KB RAM), this allocates a new formatted string on each retry. With `max_retries=6` and sensor polling occurring frequently, this could contribute to memory fragmentation.

**Recommendation**: This is acceptable for the current use case since retries are exceptional (not the common path), and the logging is guarded by `if logger`. No action required unless profiling shows memory pressure. This follows the "make it right before make it fast" principle - the current design is correct and readable.

---

**Logger instantiation on every bus recovery call** - `src/shared/sensors/bus_recovery.py:95,161`

Each call to `recover_i2c_bus` or `recover_onewire_bus` calls `_get_module_logger()` which checks and potentially sets a global. This is efficient due to the module-level caching pattern at lines 63-71:

```python
def _get_module_logger():
    """Get or create the module logger."""
    global _logger
    if _logger is None:
        _logger = get_logger("sensors")
    return _logger
```

**Status**: No issue - this is a correct lazy initialization pattern with O(1) lookup after first call.

### Low

**Minor: Sleep precision not guaranteed on CircuitPython** - `src/shared/sensors/bus_recovery.py:108-110,173`

The code uses `time.sleep(0.00001)` for 10 microsecond delays. CircuitPython's `time.sleep()` precision on ESP32 varies; sleeps under ~1ms may not be accurate. However, for the I2C recovery protocol, approximate timing is sufficient.

**Status**: Acceptable - the 10us value is within I2C spec tolerances and works in practice.

---

**Exception storage in retry loop** - `src/shared/sensors/retry.py:255,262`

```python
last_exception = None
# ...
last_exception = e
```

Storing the exception reference is O(1) and the exception object is already allocated by Python. No memory concern.

## Performance Characteristics Summary

| Operation | Time Complexity | Memory Impact | Hot Path? |
|-----------|-----------------|---------------|-----------|
| `retry_with_backoff` | O(n) where n=retries | Minimal (reuses delay var) | Yes - sensor reads |
| `recover_i2c_bus` | O(1) - 9 toggles fixed | Minimal (1 GPIO object) | No - recovery only |
| `recover_onewire_bus` | O(1) - single pulse | Minimal (1 GPIO object) | No - recovery only |

## Resource Management

**Positive patterns observed:**

1. **try/finally cleanup** - Both bus recovery functions properly clean up GPIO resources in finally blocks (`bus_recovery.py:133-139,198-204`)

2. **Explicit deinit calls** - GPIO and bus objects are explicitly deinitialized rather than relying on garbage collection, which is important on CircuitPython where GC may not run predictably

3. **No memory leaks** - Resources are cleaned up even on exception paths

4. **Bounded delays** - The `max_delay` cap in retry logic prevents unbounded blocking (`retry.py:279`)

## Blocking Operations Assessment

The code has appropriate timeouts for blocking operations:

- `time.sleep()` calls are bounded (max 2.0 seconds in retry, sub-millisecond in bus recovery)
- I2C and OneWire bus creation/deinit are inherently fast operations
- No network I/O or unbounded waits

**Note**: The bus recovery functions temporarily block during the recovery pulse sequences (180us for I2C, 600us for OneWire). This is acceptable and necessary for the hardware protocol, and should not interfere with watchdog feeding if fed before calling recovery.

## Verdict

This code is appropriate for the ESP32/CircuitPython target environment. The resource cleanup patterns are correct, there are no algorithmic inefficiencies, and memory usage is minimal. The code prioritizes correctness and reliability over micro-optimization, which is the right trade-off for sensor reliability utilities.
