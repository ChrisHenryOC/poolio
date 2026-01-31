# Code Quality Review for PR #93

## Summary

This PR adds sensor utilities for retry with exponential backoff and bus recovery (I2C/OneWire). The implementation is clean, follows CircuitPython compatibility patterns, and has excellent test coverage (592 new test lines for 250 lines of implementation). The code reveals intention well through docstrings and clear naming, with minimal duplication.

## Findings

### Critical

None.

### High

**H1: Logger API mismatch with logging module** - `src/shared/sensors/bus_recovery.py:56-58`

The fallback `get_logger(name)` function signature differs from the actual `logging.get_logger(device_id, debug_logging=False)` signature. When the import from `..logging` succeeds, `_get_module_logger()` calls `get_logger("sensors")` which passes a single string argument, but the actual `get_logger` expects `device_id` and optional `debug_logging`.

This happens to work because Python accepts positional arguments, but the semantic mismatch is confusing - "sensors" is not a device_id.

Recommendation: Either update the call to use a more appropriate identifier or consider whether the logging module's `get_logger` API should be more flexible for non-device loggers.

**H2: Bare `except Exception` in bus recovery functions** - `src/shared/sensors/bus_recovery.py:95,160`

The CLAUDE.md explicitly calls out "No bare `except:` clauses - always catch specific exceptions". While `except Exception` is better than bare `except`, the code catches all exceptions without distinguishing between:
- Hardware failures (expected, should return False)
- Programming errors (unexpected, might want to propagate)

```python
except Exception as e:
    logger.error("I2C bus recovery failed: %s", e)
    return False
```

The docstring promises "Returns True if recovery succeeded, False if an error occurred" which is reasonable for hardware recovery, but consider catching more specific exceptions like `RuntimeError`, `OSError`, or `ValueError` that CircuitPython hardware libraries typically raise.

### Medium

**M1: Magic numbers for timing constants** - `src/shared/sensors/bus_recovery.py:74-76,108,139,145`

The bus recovery timing values are hardcoded:
- `0.00001` (10 microseconds) for I2C clock toggles
- `0.0005` (500 microseconds) for OneWire reset pulse
- `0.0001` (100 microseconds) for presence pulse window

These are well-documented in comments, but making them module-level constants would improve readability and make them easier to tune if needed:

```python
I2C_CLOCK_PERIOD_US = 0.00001  # 10 microseconds
ONEWIRE_RESET_PULSE_US = 0.0005  # 500 microseconds
ONEWIRE_PRESENCE_WINDOW_US = 0.0001  # 100 microseconds
```

**M2: Duplication in bus recovery functions** - `src/shared/sensors/bus_recovery.py:40-105,108-170`

Both `recover_i2c_bus` and `recover_onewire_bus` follow the same pattern:
1. Get logger and log start
2. Initialize GPIO as None
3. Try: configure GPIO, do recovery, cleanup, reinit bus
4. Except: log error, return False
5. Finally: cleanup GPIO if still set

The duplication is acceptable given the functions are only 60-65 lines each and the differences are meaningful (different pin configurations, different recovery sequences). Extracting a common pattern would likely over-complicate the code.

This is noted but **not flagged as a problem** per Beck's "fewest elements" rule - the current implementation is simple and readable.

**M3: Test assertions could be more specific** - `tests/unit/test_bus_recovery.py:353-354`

```python
# Verify mock was used (basic check that toggle happened)
assert mock_scl_gpio.value is not None
```

This assertion does not actually verify SCL was toggled 9 times. The test name promises verification but the assertion is weak. Consider asserting on the number of value assignments or using `call_count` on a property mock.

### Low

**L1: Inconsistent logger usage** - `src/shared/sensors/retry.py` vs `src/shared/sensors/bus_recovery.py`

`retry_with_backoff` takes an optional `logger` parameter while `bus_recovery` functions use a module-level logger. Both approaches are valid, but the inconsistency within the same package is worth noting.

The design choice makes sense: retry is a utility that might be used with different loggers, while bus recovery is more specialized. No change needed.

## Beck's Four Rules Assessment

| Rule | Assessment |
|------|------------|
| **1. Passes the tests** | Excellent - 592 lines of tests covering success paths, failure paths, edge cases, timing verification, and cleanup |
| **2. Reveals intention** | Good - Clear docstrings, descriptive function names, commented recovery sequences |
| **3. No duplication** | Good - Some structural similarity in bus recovery functions but not problematic |
| **4. Fewest elements** | Good - Simple design with no unnecessary abstractions, no over-engineering detected |

## Over-Engineering Check

No over-engineering detected:
- No unnecessary abstractions or factory patterns
- No premature generalization
- Simple functions that do one thing
- No "just in case" code paths
- Appropriate use of module-level caching for logger (single instance needed)

## Summary Statistics

| File | Lines | Tests | Coverage Focus |
|------|-------|-------|----------------|
| `retry.py` | 80 | 274 lines (22 tests) | All retry scenarios, timing, exception filtering |
| `bus_recovery.py` | 170 | 318 lines (14 tests) | Both I2C and OneWire paths, error handling, cleanup |
| `__init__.py` | 11 | - | Simple exports |

The test-to-implementation ratio (~2.3:1) indicates thorough testing.
