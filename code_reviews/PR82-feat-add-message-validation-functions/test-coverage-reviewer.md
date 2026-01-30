# Test Coverage Review for PR #82

## Summary

PR #82 adds message validation functions with a comprehensive test suite of 47 tests covering the four main validation functions. The tests follow good TDD patterns with behavior-focused assertions and clear naming. However, there are several coverage gaps in timestamp parsing edge cases, boundary conditions, and the internal `_parse_iso_timestamp` function lacks direct unit tests.

## TDD Evidence Assessment

**Evidence of TDD patterns:**
- Tests describe behavior (e.g., `test_stale_command_is_invalid`) rather than implementation details
- Tests cover both valid and invalid cases for each function
- Clear Arrange-Act-Assert structure throughout
- Tests are independent and deterministic with explicit `current_time` injection

**Minor concerns:**
- Heavy coverage of happy paths; some edge cases missing
- Internal `_parse_iso_timestamp` function only tested indirectly

## Findings

### High

**Missing boundary condition tests for timestamp freshness** - `tests/unit/test_validator.py`

The tests check values within thresholds and beyond thresholds, but do not test exact boundary values:
- No test for command exactly 300 seconds old (should pass)
- No test for command exactly 301 seconds old (should fail)
- No test for status exactly 900 seconds old (should pass)
- No test for timestamp exactly 60 seconds in the future (should pass)

Boundary conditions are common sources of off-by-one errors. The implementation uses `>` comparison on line 217 (`if age_seconds > max_age`), meaning exactly at threshold should pass, but this is not verified.

**Recommendation:** Add explicit boundary tests:
```python
def test_command_exactly_at_threshold_is_valid(self) -> None:
    """Command exactly 300 seconds old is valid."""
    timestamp = "2026-01-20T14:30:00-08:00"  # Exactly 300 seconds before reference
    valid, errors = validate_timestamp_freshness(timestamp, "command", self.REFERENCE_TIME)
    assert valid is True

def test_command_one_second_over_threshold_is_invalid(self) -> None:
    """Command 301 seconds old is invalid."""
    ...
```

---

**Missing timezone offset coverage** - `tests/unit/test_validator.py`

All timestamp tests use `-08:00` (Pacific time) offset. The `_parse_iso_timestamp` function has distinct code paths for:
1. UTC with 'Z' suffix (line 158)
2. Positive offsets like `+05:30` (line 162)
3. Negative offsets like `-08:00` (tested)

The positive offset branch and UTC 'Z' branch are not tested.

**Recommendation:** Add tests with varied timezone formats:
```python
def test_utc_timestamp_with_z_suffix(self) -> None:
    """UTC timestamp with Z suffix is parsed correctly."""
    timestamp = "2026-01-20T22:32:00Z"  # Same instant as 14:32-08:00
    valid, errors = validate_timestamp_freshness(timestamp, "command", self.REFERENCE_TIME)
    assert valid is True

def test_positive_timezone_offset(self) -> None:
    """Positive timezone offset parsed correctly."""
    timestamp = "2026-01-21T03:32:00+05:00"  # Same instant as 22:32 UTC
    ...
```

---

### Medium

**No direct unit tests for `_parse_iso_timestamp`** - `src/shared/messages/validator.py:111`

The internal timestamp parsing function is complex (60+ lines) with multiple code paths including leap year calculation, but is only tested indirectly through `validate_timestamp_freshness`. This makes debugging failures harder and leaves edge cases untested:
- Leap year dates (Feb 29)
- Month boundaries
- Year 2000 (divisible by 100 but also 400, so IS a leap year)
- Dates before 1970 (negative timestamps)

**Recommendation:** Add direct unit tests for `_parse_iso_timestamp` or extract as a public helper with tests:
```python
def test_parse_leap_year_feb_29(self) -> None:
    """Feb 29 in leap year parses correctly."""
    from shared.messages.validator import _parse_iso_timestamp
    result = _parse_iso_timestamp("2024-02-29T12:00:00Z")
    assert result == 1709208000  # Known Unix timestamp

def test_parse_year_2000_is_leap_year(self) -> None:
    """Year 2000 is a leap year (divisible by 400)."""
    ...
```

---

**Incomplete negative test coverage for payload validation** - `tests/unit/test_validator.py:219`

Only `pool_status` has a test for missing required fields (`test_missing_pool_status_field`). Other message types (`valve_status`, `display_status`, `fill_start`, etc.) only have happy path tests. If a message type's validation logic differs, the gap would not be caught.

**Recommendation:** Add at least one negative test per message type, or a parameterized test:
```python
@pytest.mark.parametrize("msg_type,payload,missing_field", [
    ("valve_status", {"valve": {}, "schedule": {}}, "temperature"),
    ("command", {"command": "test"}, "parameters"),
    ...
])
def test_missing_required_field_per_type(self, msg_type, payload, missing_field):
    ...
```

---

**No test for `current_time=None` default behavior** - `tests/unit/test_validator.py`

The `validate_timestamp_freshness` function has a `current_time=None` parameter that triggers `import time; time.time()`. All tests pass explicit `current_time`, so the default path with dynamic time is untested. This could hide import issues or timing bugs.

**Recommendation:** Add at least one test that uses the default:
```python
def test_freshness_uses_current_time_when_not_provided(self) -> None:
    """When current_time is None, uses time.time() dynamically."""
    # Create timestamp within the last minute
    import time
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    timestamp = now.strftime("%Y-%m-%dT%H:%M:%SZ")

    valid, errors = validate_timestamp_freshness(timestamp, "pool_status")
    assert valid is True
```

---

### Low

**Test for envelope field with None value** - `tests/unit/test_validator.py`

The `validate_envelope` function checks `if field not in envelope` but does not validate that field values are non-None. A test confirming current behavior (None values are accepted) would document this design decision.

---

**No test for invalid timestamp components** - The regex pattern accepts any digits, so `2026-13-45T99:99:99Z` would match but produce invalid results. However, since this is a CircuitPython-compatible simple validation (not full ISO 8601 compliance), this may be intentional.

## Coverage Summary

| Function | Lines | Tests | Coverage Assessment |
|----------|-------|-------|---------------------|
| `validate_envelope` | 9 | 8 | Good - all branches covered |
| `validate_message_size` | 11 | 6 | Good - includes UTF-8 edge case |
| `validate_payload` | 11 | 14 | Medium - happy paths only for most types |
| `_parse_iso_timestamp` | 48 | 0 direct | Low - only indirect coverage |
| `validate_timestamp_freshness` | 27 | 15 | Medium - missing boundaries and timezones |

## Test Quality Assessment

**Strengths:**
- Clear test class organization by function
- Descriptive test names following `test_<what>_<condition>` pattern
- Consistent use of Arrange-Act-Assert structure
- Good use of dependency injection (`current_time` parameter)
- Tests are isolated and deterministic

**Areas for improvement:**
- Consider using `pytest.mark.parametrize` to reduce duplication in similar tests
- Add negative test cases for each message type, not just `pool_status`
- Document the REFERENCE_TIME constant derivation in test class docstring
