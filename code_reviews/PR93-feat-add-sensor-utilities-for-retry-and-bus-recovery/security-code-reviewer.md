# Security Code Review for PR #93

## Summary

This PR adds sensor utilities for retry logic and I2C/OneWire bus recovery for an embedded IoT system. The code is well-structured with proper resource cleanup. From a security perspective, the code is low-risk as it operates on local hardware pins with no user input, network exposure, or data persistence. The main considerations are resource exhaustion via retry parameters and proper exception handling.

## Findings

### Critical

None.

### High

None.

### Medium

**M1: Unbounded retry delay could cause DoS in caller** - `src/shared/sensors/retry.py:7-14`

The `retry_with_backoff` function accepts `max_retries`, `base_delay`, and `max_delay` as parameters with default values. While default values are reasonable (3 retries, 0.1-2.0 second delays), there is no validation to prevent extremely large values that could block the calling thread for extended periods.

```python
def retry_with_backoff(
    func,
    max_retries=3,      # No upper bound check
    base_delay=0.1,     # No validation
    max_delay=2.0,      # No upper bound check
    ...
):
```

With `max_retries=1000` and `max_delay=60`, this would block for approximately 16+ hours. In an embedded system with limited resources, this could effectively DoS the device.

**Risk Assessment**: Low likelihood in practice since this is internal library code called by trusted node implementations. The IoT devices are not exposed to external input that would set these parameters.

**Recommendation**: Consider adding reasonable upper bounds validation (e.g., `max_retries <= 10`, `max_delay <= 30.0`) or document expected ranges clearly. For embedded systems, extremely long blocking is rarely desirable.

---

**M2: Broad exception catching in retry logic** - `src/shared/sensors/retry.py:53`

The default exception tuple `exceptions=(Exception,)` catches all exceptions derived from `Exception`. This could mask programming errors or unexpected failures that should propagate.

```python
def retry_with_backoff(
    ...
    exceptions=(Exception,),  # Catches everything
    ...
):
    ...
    except exceptions as e:  # Too broad by default
```

**CWE Reference**: CWE-755 (Improper Handling of Exceptional Conditions)

**Risk Assessment**: Low. The code allows callers to specify narrower exception types, and the tests verify that `BaseException` subclasses like `KeyboardInterrupt` and `SystemExit` propagate correctly.

**Recommendation**: Consider a more restrictive default such as `exceptions=(OSError, RuntimeError)` for hardware operations, or document that callers should specify appropriate exception types.

### Low

**L1: Exception details logged without sanitization** - `src/shared/sensors/bus_recovery.py:96,161`

Exception messages are logged directly without sanitization:

```python
logger.error("I2C bus recovery failed: %s", e)
logger.error("OneWire bus recovery failed: %s", e)
```

In embedded/IoT contexts, exception messages typically do not contain sensitive data, and logs are local to the device. This is informational only.

**CWE Reference**: CWE-209 (Generation of Error Message Containing Sensitive Information)

**Risk Assessment**: Very low. This is embedded hardware code with no user-controlled data in exception messages.

---

**L2: Silent exception suppression in finally blocks** - `src/shared/sensors/bus_recovery.py:103-105,168-170`

Cleanup exceptions are silently ignored:

```python
except Exception:
    pass  # Ignore cleanup errors
```

While this is a common pattern for resource cleanup, it could hide important hardware failures. The pattern is acceptable here since:
1. The primary operation result is already determined
2. GPIO cleanup failures are typically benign (pin already released)
3. This follows embedded best practices for resource cleanup

---

**L3: No input validation on pin objects** - `src/shared/sensors/bus_recovery.py:40,108`

The `scl_pin`, `sda_pin`, and `data_pin` parameters are not validated before use:

```python
def recover_i2c_bus(scl_pin, sda_pin):
    ...
    scl_gpio = digitalio.DigitalInOut(scl_pin)  # No validation
```

**Risk Assessment**: Very low. These functions are internal library code called with `board.*` constants. Invalid pins will raise exceptions that are properly caught and logged.

## Positive Security Observations

1. **Proper resource cleanup**: Both bus recovery functions use `try/finally` blocks to ensure GPIO resources are released even on failure paths.

2. **No hardcoded credentials**: The code contains no secrets, API keys, or credentials.

3. **No user input processing**: All inputs are internal (pin objects, callable functions) with no external/user-controlled data.

4. **No network operations**: This is purely local hardware manipulation with no network attack surface.

5. **No file operations**: No path traversal or file manipulation concerns.

6. **No deserialization**: No pickle, eval, exec, or other dangerous deserialization.

7. **BaseException subclasses propagate**: The retry logic correctly allows `KeyboardInterrupt` and `SystemExit` to propagate (verified in tests).

## Conclusion

This PR introduces low-risk utility code for embedded hardware operations. The code follows defensive programming practices with proper resource cleanup. The medium-severity findings are recommendations for additional robustness rather than exploitable vulnerabilities. Given the embedded IoT context with no external input or network exposure, the security posture is appropriate for the use case.
