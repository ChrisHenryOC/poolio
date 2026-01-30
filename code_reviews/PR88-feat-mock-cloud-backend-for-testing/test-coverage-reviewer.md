# Test Coverage Review for PR #88

## Summary

This PR adds a MockBackend class for cloud testing with 28 tests covering core functionality. The tests are well-structured with clear naming and good Arrange-Act-Assert patterns. However, there are notable gaps in edge case coverage and error handling tests that suggest the tests may have been written after implementation rather than test-first.

## TDD Evidence Assessment

The tests show mixed evidence of TDD practices:

**Positive indicators:**
- Tests describe behavior rather than implementation details
- Test names follow the `test_<behavior>` pattern
- Each test focuses on a single assertion or closely related assertions

**Negative indicators:**
- No negative test cases (testing what should NOT happen)
- Limited edge case coverage (empty strings, None values, special characters)
- Error paths not tested (callback exceptions, datetime unavailable scenario)
- Tests access private attributes (`_feeds`, `_subscribers`, `_connected`) rather than public behavior

## Findings

### High

**Missing error path test for sync_time when datetime unavailable** - `tests/unit/test_mock_backend.py` - The implementation at `src/shared/cloud/mock.py:135-136` raises `RuntimeError` when datetime is None, but no test verifies this behavior. This is a critical error path that should be tested.

**Tests access private implementation details** - `tests/unit/test_mock_backend.py:176-186` - Tests like `test_starts_with_empty_feeds` directly access `backend._feeds`, `backend._subscribers`, and `backend._connected`. These tests will break on refactoring and test implementation rather than behavior. Consider testing through public API only (e.g., verify `fetch_latest` returns None on fresh instance).

**Missing callback exception handling test** - `src/shared/cloud/mock.py:69-70` - The `publish` method iterates through callbacks without try/except. If a callback raises an exception, subsequent callbacks will not be called and the exception will propagate. No test verifies this behavior or documents the intended semantics.

### Medium

**No tests for None/empty string feed names** - `tests/unit/test_mock_backend.py` - Tests use valid feed names like "pooltemp" and "waterlevel". No tests verify behavior with:
- Empty string feed name: `backend.publish("", 72.5)`
- None as feed name: `backend.publish(None, 72.5)`
- Feed names with special characters

**No tests for None callback** - `tests/unit/test_mock_backend.py` - The `subscribe` method accepts any callback without validation. Test is missing for:
```python
backend.subscribe("pooltemp", None)  # What happens?
```

**fetch_history hours parameter edge cases untested** - `tests/unit/test_mock_backend.py:375-418` - Tests use `hours=1` but do not test:
- `hours=0` (boundary condition)
- `hours=-1` (negative value - what's expected?)
- `hours=0.001` (fractional values near zero)

**No test for empty feed list in fetch_latest** - While `test_fetch_latest_returns_none_for_unknown_feed` tests unknown feeds, there's no test for the branch at `src/shared/cloud/mock.py:100-101` where feed exists but list is empty. This could occur if internal state becomes corrupted.

**Missing unsubscribe functionality** - The MockBackend has `subscribe` but no `unsubscribe`. While not strictly a test coverage issue, tests should document whether this is intentional (and test that multiple subscribes accumulate) or if this is missing functionality.

### Low

**Test isolation could be improved with fixtures** - `tests/unit/test_mock_backend.py` - Each test creates its own `MockBackend()` instance. Consider using a pytest fixture for consistency with other test files in the project, though current approach is not incorrect.

**Inconsistent type hint usage** - Implementation follows CircuitPython compatibility by omitting type hints in signatures, but tests could use type hints for better documentation since they only run in CPython/pytest environment.

## Missing Test Scenarios

Based on the implementation, these test scenarios are missing:

1. **Callback receives correct arguments** - Verify callback gets exact feed and value passed to publish
2. **Multiple publishes trigger multiple callback invocations** - Test callback is called once per publish
3. **fetch_history with exactly-at-boundary timestamp** - What if timestamp equals cutoff time exactly?
4. **Large scale testing** - Many values in a feed, many subscribers, many feeds
5. **Type preservation** - Test that complex values (dict, list) are stored and retrieved correctly
6. **Thread safety documentation** - If MockBackend is not thread-safe, test or document this

## Code Coverage Estimate

| Method | Lines | Covered | Gap |
|--------|-------|---------|-----|
| `__init__` | 3 | Yes | - |
| `connect` | 1 | Yes | - |
| `disconnect` | 1 | Yes | - |
| `publish` | 6 | Partial | Callback exception path |
| `subscribe` | 3 | Yes | None callback |
| `fetch_latest` | 4 | Partial | Empty list branch |
| `fetch_history` | 6 | Yes | Edge cases for hours |
| `sync_time` | 3 | Partial | datetime=None branch |

Estimated line coverage: ~85%
Estimated branch coverage: ~70%

## Recommendations

1. Add test for `sync_time` when datetime is unavailable (requires mocking)
2. Refactor initialization tests to use public API assertions
3. Add edge case tests for empty/None/special feed names
4. Document or test callback exception handling behavior
5. Consider property-based testing (hypothesis) for feed name and value types
