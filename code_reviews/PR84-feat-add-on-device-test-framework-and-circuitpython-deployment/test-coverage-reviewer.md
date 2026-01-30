# Test Coverage Review for PR #84

## Summary

This PR introduces a comprehensive on-device test framework for CircuitPython, including deployment tooling, a serial monitor, and 27 device tests. While the on-device tests for `shared.messages` are well-structured and provide good CircuitPython validation coverage, there are no unit tests for the newly introduced tooling (`deploy.py`, `serial_monitor.py`, `assertions.py`, `runner.py`). The test framework infrastructure itself is untested, which represents a moderate coverage gap.

## Findings

### High

**No tests for deployment script functions** - `circuitpython/deploy.py:502-782`

The deployment script introduces 322 lines of code with complex functionality that has no test coverage:

- `find_device()` (lines 502-520): Device auto-detection logic for macOS/Linux
- `download_bundle()` (lines 523-555): Network download, ZIP extraction, error handling
- `load_requirements()` (lines 558-575): Requirement file parsing with base + target merging
- `parse_requirements_file()` (lines 577-588): File parsing with comment/blank line handling
- `find_library_in_bundle()` (lines 590-601): Library resolution (mpy vs directory)
- `deploy_libraries()` (lines 621-645): Orchestration with missing library detection
- `deploy_source()` (lines 647-681): Source deployment with optional test inclusion
- `main()` (lines 692-778): CLI argument handling, error paths

**Recommendation**: Add unit tests in `tests/unit/test_deploy.py` using mocking for filesystem and network operations. Priority paths to test:
- `parse_requirements_file()` with comments, blank lines, valid entries
- `load_requirements()` merging base + target requirements
- `find_library_in_bundle()` for both .mpy files and directories
- `main()` argument validation and error handling

---

**No tests for serial monitor script** - `scripts/serial_monitor.py:876-979`

The serial monitor script (103 lines) has no test coverage:

- `find_serial_port()` (lines 896-906): Port auto-detection with glob patterns
- `monitor_serial()` (lines 909-959): Serial communication, timeout handling, test completion detection

**Recommendation**: Add unit tests with mocked serial communication. Key scenarios:
- Serial port detection on different platforms
- Timeout handling
- Test completion marker detection (`=== TEST RUN END ===`)
- Error handling for unavailable ports

---

**No tests for assertion helpers** - `tests/device/assertions.py:1091-1338`

The assertion library (243 lines) that forms the foundation of the test framework has no tests:

- 13 assertion functions
- `SkipTest` exception class
- Edge cases: type coercion, None handling, exception chaining

**Recommendation**: Add unit tests in `tests/unit/test_device_assertions.py`:
```python
# Example test cases needed:
def test_assert_equal_with_equal_values()
def test_assert_equal_with_unequal_values_raises()
def test_assert_raises_catches_expected_exception()
def test_assert_raises_wrong_exception_type_fails()
def test_assert_raises_no_exception_fails()
def test_assert_almost_equal_within_tolerance()
def test_skip_raises_skip_test_exception()
```

---

**No tests for test runner** - `tests/device/runner.py:1346-1673`

The test runner (322 lines) has no test coverage:

- `TestResult` class
- `TestRunner._discover_tests()` (line 1423-1439): Test discovery logic
- `TestRunner._run_single_test()` (line 1441-1482): Test execution with setup/teardown
- `TestRunner.run_module()` (line 1484-1514): Module execution with output formatting
- `run_all()`, `run_module_by_name()`, `run_pattern()` convenience functions

**Recommendation**: Add unit tests with mock modules to verify:
- Test discovery finds `test_` prefixed functions only
- Results are correctly categorized (PASS/FAIL/ERROR/SKIP)
- Setup/teardown hooks are called
- Pattern filtering works correctly
- Exit codes reflect test results

### Medium

**TDD Evidence Assessment: Mixed signals**

Examining the on-device tests in `tests/device/shared/test_messages.py`:

**Positive TDD indicators:**
- Tests describe behavior, not implementation (e.g., `test_water_level_creation`, `test_encode_converts_snake_to_camel`)
- Edge cases covered: `test_water_level_false_switch`, `test_parse_envelope_invalid_json`
- Tests are adapted from unit tests, showing consistency between test suites

**Negative TDD indicators:**
- Device tests (27) significantly fewer than unit tests (206) - suggests tests adapted after implementation
- No negative test cases for validation (e.g., invalid temperature units, out-of-range values)
- Missing edge cases that unit tests cover (validator tests not ported to device tests)

**Recommendation**: Consider adding device tests for:
- Invalid message handling
- Boundary conditions (max message size)
- Error recovery scenarios

---

**Assertion helpers missing edge case tests** - `tests/device/assertions.py`

While a Medium issue (as the assertions are tested transitively by their use in device tests), explicit edge case testing would improve confidence:

- `assert_almost_equal`: Behavior with NaN, infinity
- `assert_raises`: Behavior when exception subclass is raised
- `assert_in`/`assert_not_in`: Behavior with generators (may iterate exhaustively)
- `assert_is_instance`: Behavior with abstract base classes

---

**Device tests missing validator coverage** - `tests/device/shared/test_messages.py`

The unit tests include comprehensive validator tests (`tests/unit/test_validator.py`: 68 tests), but no validator tests are ported to device tests. The validator module was modified for CircuitPython compatibility:

- `validator.py:989-1051`: Added conditional datetime import with fallback
- `validator.py:1074-1082`: Added guard for `datetime is None` case

**Recommendation**: Add device tests for critical validator paths:
- `validate_envelope()` with valid/invalid envelopes
- `validate_message_size()` basic check
- Timestamp validation with/without datetime module available

### Low

**Test count discrepancy in documentation**

`CLAUDE.md` documents "27 tests" for device tests, which matches the actual count. However, there is no automated verification that this count stays in sync with the actual tests.

**Recommendation**: Consider generating test count from actual test discovery rather than hardcoding.

---

**Serial monitor lacks structured output parsing**

`scripts/serial_monitor.py:939-950` prints raw output but does not parse the structured test results. This limits automation capabilities.

**Recommendation**: Consider adding `--json` output mode for CI integration.

## Test Structure Assessment

### Positives

1. **Clear Arrange-Act-Assert pattern**: Device tests follow AAA structure consistently
2. **Descriptive test names**: `test_encode_decode_round_trip_temperature` clearly describes behavior
3. **Focused assertions**: Each test generally checks one behavior
4. **CircuitPython compatibility**: Tests use compatible constructs (no type hints in test code, string formatting instead of f-strings)

### Areas for Improvement

1. **Test isolation**: Some tests share import-time state; consider per-test setup
2. **Missing fixtures**: No shared test fixtures for common message objects
3. **No parameterized tests**: Could reduce duplication (e.g., multiple temperature unit tests)

## Coverage Summary

| Component | Lines Added | Tests | Gap |
|-----------|-------------|-------|-----|
| `circuitpython/deploy.py` | 322 | 0 | High |
| `scripts/serial_monitor.py` | 103 | 0 | High |
| `tests/device/assertions.py` | 243 | 0 | High |
| `tests/device/runner.py` | 322 | 0 | High |
| `tests/device/shared/test_messages.py` | 365 | N/A (is tests) | N/A |
| `src/shared/messages/*.py` changes | ~50 | Covered by existing 206 unit tests | Low |

**Total new code without tests: ~990 lines (excluding the test file itself)**

## Recommendations Priority

1. **Critical**: Add tests for `assertions.py` - foundation of test framework
2. **High**: Add tests for `deploy.py` - deployment failures are hard to debug
3. **Medium**: Add tests for `runner.py` - ensures test results are accurate
4. **Low**: Add tests for `serial_monitor.py` - interactive tool, harder to test
