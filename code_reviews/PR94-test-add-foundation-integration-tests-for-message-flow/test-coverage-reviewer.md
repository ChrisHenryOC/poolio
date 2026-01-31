# Test Coverage Review for PR #94

## Summary

This PR introduces integration tests that verify message round-trip flow (encode -> publish -> subscribe -> decode) through the MockBackend. The tests follow good Arrange-Act-Assert structure and verify nested object preservation. However, the test coverage is incomplete: only 3 of 9 message types are tested, error paths are absent, and there are no tests for edge cases or failure modes.

## Findings

### High

**Incomplete message type coverage** - `tests/integration/test_message_flow.py`

Only 3 of 9 message types defined in `src/shared/messages/types.py` have round-trip integration tests:

| Message Type | Tested |
|--------------|--------|
| PoolStatus | Yes (line 36) |
| ValveStatus | Yes (line 81) |
| Command | Yes (line 136) |
| DisplayStatus | No |
| FillStart | No |
| FillStop | No |
| CommandResponse | No |
| Error | No |
| ConfigUpdate | No |

While unit tests in `tests/unit/test_encoder.py` cover encoding for all types, the integration tests exist specifically to verify the full round-trip flow. The `DisplayStatus` type in particular has nested `local_temperature` and `local_humidity` fields with different snake_case patterns that should be validated in a round-trip test.

Recommendation: Add round-trip tests for at least `DisplayStatus` (different nested field naming pattern) and `Error` (has nullable `context` field and is critical for debugging).

---

**No error path testing** - `tests/integration/test_message_flow.py`

The tests only cover the happy path. There are no tests for:

- What happens when `decode_message` receives malformed JSON?
- What happens when message type is unknown?
- What happens when required fields are missing from payload?

Integration tests should verify that the system fails gracefully when encountering corrupt or incomplete messages during the full flow.

Recommendation: Add at least one test that publishes malformed JSON and verifies the decode raises `ValueError` with a useful message.

---

**Missing edge case tests for optional/nullable fields** - `tests/integration/test_message_flow.py`

The `ScheduleInfo.next_scheduled_fill` field is optional (can be None), as shown in `src/shared/messages/types.py:126`:

```python
def __init__(self, enabled, start_time, window_hours, next_scheduled_fill=None):
```

The test at line 84 always provides a value. Similarly, `Error.context` can be None, and `CommandResponse.error_code`/`error_message` are optional.

Recommendation: Add round-trip tests that exercise None/optional field handling to ensure they survive the encode/decode cycle.

---

### Medium

**No TDD evidence - tests appear written after implementation** - `tests/integration/test_message_flow.py`

The tests verify implementation details rather than specifying behavior:

1. Tests check specific field values rather than defining expected behavior
2. No edge cases tested (suggests tests were written to confirm working code)
3. All happy paths, no failure modes (TDD typically catches edge cases during red phase)

The test structure mirrors the implementation rather than describing requirements. For example, the tests manually compare each field rather than using `__eq__` methods already defined on some message types.

Recommendation: Consider using the `__eq__` methods where available (e.g., `WaterLevel`, `Temperature`, `Battery` have `__eq__` defined in `src/shared/messages/types.py`). This would make tests less brittle and more focused on behavior.

---

**Test duplication - repeated setup pattern** - `tests/integration/test_message_flow.py:36,81,136`

Each test method repeats the identical backend setup pattern:

```python
backend = MockBackend(environment="test")
backend.connect()
received_messages: list[str] = []
backend.subscribe("test-...", lambda f, v: received_messages.append(v))
```

And identical teardown:

```python
backend.disconnect()
```

This violates Kent Beck's "No duplication" rule and makes tests harder to maintain.

Recommendation: Extract common setup to a pytest fixture:

```python
@pytest.fixture
def backend_with_capture():
    backend = MockBackend(environment="test")
    backend.connect()
    received = []
    def capture_callback(feed, value):
        received.append(value)
    yield backend, received
    backend.disconnect()
```

---

**No cleanup on test failure** - `tests/integration/test_message_flow.py:79,134,172`

The `backend.disconnect()` calls are at the end of each test, not in a `finally` block or fixture teardown. If an assertion fails, `disconnect()` is never called. While this has no practical impact with `MockBackend`, it sets a poor pattern for future integration tests that might use real connections.

Recommendation: Use a fixture with proper cleanup (as suggested above) or use `try/finally`.

---

**Assertions could be more specific** - `tests/integration/test_message_flow.py:58`

```python
assert len(received_messages) == 1
```

This assertion fails with unhelpful message like `assert 0 == 1`. Using pytest's `assert ... == expected, "message"` pattern or comparing against `[json_str]` directly would provide better failure diagnostics.

Recommendation: Use more descriptive assertions:

```python
assert received_messages == [json_str], f"Expected one message, got {len(received_messages)}"
```

---

### Low

**Missing type annotations on test methods** - While the test file uses `-> None` return type annotations, the test class lacks a docstring explaining the test strategy.

**Hardcoded date values** - `tests/integration/test_message_flow.py:88,101` - The date `2026-01-30T06:00:00-08:00` is hardcoded. Consider documenting this is intentional or using a comment to explain the date choice.

## TDD Assessment

Based on the analysis, there is **no strong evidence of TDD** in this PR:

1. **Tests describe method names, not scenarios** - Test names like `test_pool_status_round_trip` describe what is tested, not the expected behavior or scenario.

2. **Only happy paths** - TDD typically produces tests for edge cases and failure modes during the "red" phase when writing failing tests first.

3. **Tests mirror implementation structure** - The field-by-field verification suggests tests were written to confirm existing code rather than drive implementation.

4. **Missing negative tests** - No tests verify what should NOT happen (e.g., invalid inputs should raise specific exceptions).

This is not necessarily a problem for this PR, but the codebase would benefit from more behavior-focused tests in the future.

## Recommendations Summary

| Priority | Recommendation |
|----------|----------------|
| High | Add round-trip tests for `DisplayStatus`, `Error`, `FillStart`, `FillStop`, `CommandResponse`, `ConfigUpdate` |
| High | Add at least one error path test (malformed JSON decode) |
| High | Test optional/nullable fields (ScheduleInfo.next_scheduled_fill = None) |
| Medium | Extract repeated setup to pytest fixture |
| Medium | Use `__eq__` methods where available for cleaner assertions |
| Medium | Ensure cleanup happens even on test failure (fixture teardown) |
