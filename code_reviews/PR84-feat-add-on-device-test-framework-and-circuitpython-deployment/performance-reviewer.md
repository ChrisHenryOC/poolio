# Performance Review: PR #84 - On-Device Test Framework and CircuitPython Deployment

## Summary

This PR adds an on-device test framework for CircuitPython and a deployment script. The code is well-structured for a memory-constrained environment with appropriate garbage collection before tests. Most design decisions are sensible for the CircuitPython context. There are a few minor opportunities for optimization, but no critical performance issues were found. The code follows Beck's principle of "make it work" first - optimization should wait until profiling identifies actual bottlenecks.

## Findings

### Medium Severity

#### 1. Regex compilation on every camel_to_snake call (decoder.py)

**File:** `/Users/chrishenry/source/poolio_rearchitect/src/shared/messages/decoder.py:36`

```python
_CAMEL_PATTERN = re.compile(r"([a-z0-9])([A-Z])")
```

**Assessment:** This is actually already correct - the pattern is compiled once at module load time and reused. No issue here.

#### 2. TestRunner stores all results in memory (runner.py:41,155)

**File:** `/Users/chrishenry/source/poolio_rearchitect/tests/device/runner.py:41,155`

```python
def __init__(self):
    self.results = []
    ...
    self.results.append(result)
```

**Issue:** The `results` list accumulates all TestResult objects in memory until the test run completes. With 27+ tests, each storing name, status, duration_ms, and message strings, this could consume meaningful memory on a CircuitPython device with limited RAM (~150KB typical).

**Impact:** Low-Medium. At 27 tests, memory usage is probably acceptable. However, if the test suite grows significantly (100+ tests), this could become problematic. The TestResult class also does not use `__slots__`, meaning each instance has a `__dict__` with per-instance overhead.

**Recommendation:** Monitor memory delta in test output. If tests grow significantly, consider:
- Adding `__slots__` to TestResult class
- Computing summary statistics incrementally and discarding results
- Or accept current design as appropriate for expected test count

### Low Severity

#### 3. Repeated string formatting in print statements (runner.py)

**File:** `/Users/chrishenry/source/poolio_rearchitect/tests/device/runner.py:157-163,310-315`

```python
if result.status == PASS:
    print("[{}] {} ({}ms)".format(PASS, name, result.duration_ms))
elif result.status == SKIP:
    print("[{}] {}: {}".format(SKIP, name, result.message))
else:
    print("[{}] {}: {}".format(result.status, name, result.message))
```

**Assessment:** This pattern is duplicated in `run_module()` and `run_pattern()`. While string formatting has some overhead, this is not in a tight loop (runs once per test) and readability is more important here. The duplication is a maintainability concern more than a performance one.

**Impact:** Negligible. Not a hot path.

#### 4. Module-level re-import in run_pattern (runner.py:290-294)

**File:** `/Users/chrishenry/source/poolio_rearchitect/tests/device/runner.py:290-294`

```python
try:
    from .shared import test_messages
    modules.append((test_messages, "shared.messages"))
except ImportError:
    pass
```

**Assessment:** This import happens at function call time rather than module load. However, Python caches imports in `sys.modules`, so subsequent calls will be fast. The pattern is reasonable for optional module loading.

**Impact:** Negligible for typical usage patterns.

#### 5. Recursive _encode_value and _convert_keys_to_snake (encoder.py:45, decoder.py:90)

**File:** `/Users/chrishenry/source/poolio_rearchitect/src/shared/messages/encoder.py:45-89`
**File:** `/Users/chrishenry/source/poolio_rearchitect/src/shared/messages/decoder.py:90-115`

```python
def _encode_value(obj: Any, preserve_keys: bool = False) -> Any:
    ...
    if isinstance(obj, list):
        return [_encode_value(item, preserve_keys=preserve_keys) for item in obj]
    if isinstance(obj, dict):
        return {snake_to_camel(k): _encode_value(v) for k, v in obj.items()}
```

**Assessment:** These functions use recursion for nested structures. Message payloads are typically shallow (2-3 levels max based on PoolStatus, ValveStatus schemas). Python's default recursion limit (1000) and CircuitPython's stack are both sufficient for expected message depths.

**Impact:** Negligible. Message structures are shallow by design.

### Positive Performance Patterns (No Action Required)

#### Good: Garbage collection before each test (runner.py:151-152)

```python
for name, test_func in tests:
    # Collect garbage before each test for consistent memory
    self._collect_garbage()
```

This is excellent practice for memory-constrained CircuitPython devices. It ensures each test starts with a clean heap and helps identify memory leaks via the MEMORY_DELTA output.

#### Good: Using json.dumps with compact separators (encoder.py:120)

```python
return json.dumps(envelope, separators=(",", ":"))
```

The compact separators reduce JSON string size, which matters for MQTT payloads on constrained devices.

#### Good: Module-level constant compilation (decoder.py:36)

```python
_CAMEL_PATTERN = re.compile(r"([a-z0-9])([A-Z])")
```

Compiling the regex once at import rather than on each function call is correct.

#### Good: Early return pattern in find_device (deploy.py:42-60)

The deploy script uses early returns to short-circuit device detection, avoiding unnecessary glob operations.

## CircuitPython-Specific Considerations

The code demonstrates good awareness of CircuitPython constraints:

1. **Memory tracking:** Test framework reports MEMORY_START, MEMORY_END, and MEMORY_DELTA
2. **Conditional imports:** Typing module imported with try/except fallback
3. **No f-strings in on-device code:** Uses `.format()` for CircuitPython 8.x compatibility
4. **Explicit GC:** Calls `gc.collect()` before memory measurements

## Recommendations Summary

| Priority | Finding | Action |
|----------|---------|--------|
| Low | TestResult memory accumulation | Monitor; add `__slots__` if test count grows significantly |
| Info | Duplicated print formatting | Consider helper method for maintainability (not performance) |

## Conclusion

This PR has no significant performance issues. The code is appropriately designed for the CircuitPython memory-constrained environment. The test framework includes good memory monitoring that will surface any issues as the test suite grows. Following the principle of "make it work, make it right, make it fast" - optimization would be premature without profiling data showing actual bottlenecks.
