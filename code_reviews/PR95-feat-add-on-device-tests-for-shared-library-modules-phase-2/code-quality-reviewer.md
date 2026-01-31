# Code Quality Review: PR #95

**PR Title:** feat: Add on-device tests for shared library modules (Phase 2)

**Reviewer:** Code Quality (Kent Beck Principles)

**Date:** 2026-01-31

## Summary

This PR adds 44 new on-device tests covering the `shared.cloud`, `shared.config`, and `shared.sensors` modules, along with a `fixtures.py` file providing hardware detection helpers and a `MockCallTracker` for testing retry logic. The code is well-structured, follows established project patterns, and adheres to Beck's Four Rules of Simple Design. The test organization is clear, naming is descriptive, and there is no significant duplication.

## Findings

### High Severity

None.

### Medium Severity

**M1. Unused Hardware Fixtures**

`/Users/chrishenry/source/poolio_rearchitect/tests/device/fixtures.py:80-133`

The hardware fixture helpers (`requires_i2c`, `requires_onewire`, `requires_wifi`) are defined but never used in any of the new test files. While the docstring in `fixtures.py` shows intended usage, none of the actual tests import or use these functions.

Per Beck's "Fewest Elements" rule: code that isn't used should not be added. These fixtures may be intended for future hardware-dependent tests (e.g., bus recovery tests mentioned in `test_sensors.py` docstring), but "just in case" code paths should be avoided.

**Recommendation:** Either:
- Add tests that use these fixtures in this PR, or
- Remove the unused fixtures and add them when actual hardware tests are implemented

---

### Low Severity

**L1. Hardcoded OneWire Pin in Fixture**

`/Users/chrishenry/source/poolio_rearchitect/tests/device/fixtures.py:114`

```python
if not hasattr(board, "D10"):
    return False
ow = onewireio.OneWire(board.D10)
```

The OneWire pin is hardcoded to `D10` with a comment "This assumes D10 is available for OneWire". This is a magic value that may not match actual hardware configuration.

**Recommendation:** Consider making the pin configurable or documenting why D10 was chosen as the default.

---

**L2. Defensive Test for Unavailable Datetime Module**

`/Users/chrishenry/source/poolio_rearchitect/tests/device/shared/test_cloud.py:402-408`

```python
def test_mock_backend_sync_time():
    """Sync time returns a datetime object."""
    backend = MockBackend(environment="test")
    backend.connect()

    # sync_time may raise if datetime module is not available
    try:
        result = backend.sync_time()
        assert_is_not_none(result)
    except RuntimeError:
        # Expected if datetime module is not available on device
        pass
```

This test silently passes when `datetime` is unavailable. While reasonable for portability, this reduces the test's value since it may not actually verify anything on some devices.

**Recommendation:** Consider using `skip()` from assertions module when `datetime` is unavailable to make test results more transparent:

```python
try:
    result = backend.sync_time()
    assert_is_not_none(result)
except RuntimeError:
    skip("datetime module not available")
```

---

**L3. Test Count Discrepancy in Documentation**

`/Users/chrishenry/source/poolio_rearchitect/CLAUDE.md:427` and `/Users/chrishenry/source/poolio_rearchitect/README.md:103`

The documentation updates show device tests increasing from 27 to 71. Counting the tests in the diff:

- `test_cloud.py`: 17 tests
- `test_config.py`: 18 tests
- `test_sensors.py`: 9 tests

This adds 44 new tests. 27 + 44 = 71, which matches the documentation. This is correct.

(No action needed - verification confirmed the count is accurate.)

---

## Beck's Four Rules Assessment

### 1. Passes the Tests

**Status:** PASS

The PR adds comprehensive tests for three modules. Test coverage appears thorough, including:
- Happy path scenarios
- Error conditions (invalid environments, missing keys)
- Edge cases (empty feeds, specific exception types)
- Behavioral verification (exponential backoff timing)

### 2. Reveals Intention

**Status:** PASS

- Test names clearly describe what is being verified
- Section headers (`# === MockBackend Connection Tests ===`) organize tests logically
- Docstrings explain the test purpose
- `MockCallTracker` class has clear documentation of its purpose

### 3. No Duplication

**Status:** PASS

The `MockCallTracker` class appropriately centralizes retry testing logic that would otherwise be duplicated across multiple tests. The fixture pattern follows the existing project conventions.

Minor observation: The `backend.connect()` call is repeated in nearly every cloud test. This is acceptable as it makes each test self-contained and explicit rather than relying on shared state.

### 4. Fewest Elements

**Status:** MINOR CONCERN (see M1)

The hardware fixtures (`requires_i2c`, `requires_onewire`, `requires_wifi`) add elements without corresponding usage. This violates "build what you need now" principle, though the impact is limited to a single file.

---

## Positive Observations

1. **Consistent Structure:** Test files follow the established pattern from `test_messages.py` with clear section headers and logical grouping.

2. **Good Test Isolation:** Each test creates its own `MockBackend` or `MockCallTracker` instance, ensuring tests don't affect each other.

3. **Appropriate Test Granularity:** Tests are focused and verify single behaviors (e.g., `test_mock_backend_connect` only checks connection state).

4. **CircuitPython Compatibility:** Tests avoid type hints, dataclasses, and other CPython-only features per project guidelines.

5. **Runner Integration:** The `runner.py` updates follow the existing pattern for module registration.

---

## Files Reviewed

| File | Status |
|------|--------|
| `tests/device/fixtures.py` | New - Minor concern |
| `tests/device/runner.py` | Modified - Acceptable |
| `tests/device/shared/test_cloud.py` | New - Good |
| `tests/device/shared/test_config.py` | New - Good |
| `tests/device/shared/test_sensors.py` | New - Good |
| `CLAUDE.md` | Modified - Acceptable |
| `README.md` | Modified - Acceptable |
| `docs/to-do.md` | Modified - Acceptable |
