# Test Coverage Review for PR #92

## Summary

The logging module has good foundational test coverage with 29 tests covering the core happy paths. However, several important edge cases and error handling paths are untested, particularly around rotation edge conditions, exception handling in emit(), and the no-rotation mode (`maxBytes=0`). The tests show evidence of behavior-first thinking (TDD patterns) but lack negative test cases for failure modes.

## Findings

### High

**Missing test for rotation disabled mode** - `src/shared/logging/rotating_handler.py:71` - The `_should_rotate()` method has a branch for `maxBytes <= 0` that disables rotation entirely, but no test verifies this behavior. This is a documented feature (per the docstring "Maximum file size before rotation") that could regress silently.

```python
def _should_rotate(self):
    if self.maxBytes <= 0:  # Line 71 - untested branch
        return False
```

Recommendation: Add test `test_rotating_file_handler_no_rotation_when_max_bytes_zero` to verify rotation is disabled.

**Missing test for emit() exception handling** - `src/shared/logging/rotating_handler.py:66-67` - The `emit()` method catches exceptions and calls `handleError(record)`, but no test verifies this error path. File I/O failures are common on embedded devices (flash wear, read-only filesystem after mount issues).

```python
except Exception:
    self.handleError(record)  # Lines 66-67 - untested path
```

Recommendation: Add test that triggers write failure (e.g., close the file handle) and verify `handleError()` is called.

**Missing test for repeated get_logger() calls** - `src/shared/logging/logger.py:38-48` - The code explicitly prevents duplicate handlers when `get_logger()` is called multiple times for the same device_id (per comment on line 34-36), but no test verifies this behavior.

```python
# Only add handler if this logger doesn't have direct handlers
if len(logger.handlers) == 0:  # Line 38 - branch untested for repeated calls
```

Recommendation: Add test `test_get_logger_does_not_duplicate_handlers_on_repeated_calls` calling `get_logger("same-id")` twice and asserting handler count equals 1.

### Medium

**Missing test for directory creation** - `src/shared/logging/rotating_handler.py:45-47` - The `_open_file()` method creates parent directories if they do not exist, but no test verifies this behavior.

```python
if dirname and not os.path.exists(dirname):
    os.makedirs(dirname)  # Lines 46-47 - untested path
```

Recommendation: Add test with nested path like `tmp_path / "nested" / "dir" / "test.log"` and verify directories are created.

**Missing test for OSError in _should_rotate()** - `src/shared/logging/rotating_handler.py:78-79` - When `os.path.getsize()` fails with OSError, the method returns False, but this is untested.

Recommendation: This is a defensive code path that is difficult to test without mocking. Consider if this branch is necessary or document it as untestable.

**Missing test for add_file_logging with bare filename** - `src/shared/logging/filesystem.py:61-62` - When `log_path` has no directory component (e.g., "test.log"), `log_dir` defaults to ".". This path is untested.

```python
if not log_dir:
    log_dir = "."  # Lines 61-62 - untested branch
```

Recommendation: Add test `test_add_file_logging_with_bare_filename` using just "test.log" as path.

**Missing test for formatter inheritance** - `src/shared/logging/filesystem.py:72` - The code copies the formatter from existing handlers, but the test only implicitly verifies this through output content. No explicit assertion on formatter being set.

Recommendation: Add assertion that `new_handler.formatter` matches the original handler's formatter.

### Low

**Test name consistency** - `tests/unit/test_logging.py` - Test names like `test_get_logger_can_be_imported` are minimal smoke tests. Consider if these add value or are just noise.

**No negative tests for is_writable()** - While `is_writable()` has good coverage, there is no test for a path that is a file (not directory). The code checks `os.path.isdir(path)` on line 27.

## TDD Evidence Assessment

**Positive indicators:**
- Tests describe behavior ("returns True for writable directory") rather than implementation
- Tests are well-isolated with proper cleanup (using pytest fixtures)
- Arrange-Act-Assert pattern is followed consistently
- Tests focus on public API (what) not internal methods (how)

**Negative indicators:**
- Missing edge case coverage suggests tests may have been written after initial implementation
- No negative test cases (what should NOT happen)
- Several defensive code paths are untested (error handling in emit, OSError paths)

**Verdict:** Inconclusive - the tests show good TDD patterns in structure, but the coverage gaps on edge cases suggest they may not have been written test-first for all scenarios.

## File References

| File | Untested Lines | Issue |
|------|----------------|-------|
| `src/shared/logging/rotating_handler.py` | 71 | maxBytes <= 0 branch |
| `src/shared/logging/rotating_handler.py` | 66-67 | Exception handler in emit() |
| `src/shared/logging/rotating_handler.py` | 45-47 | Directory creation |
| `src/shared/logging/rotating_handler.py` | 78-79 | OSError in _should_rotate() |
| `src/shared/logging/logger.py` | 38-48 | Duplicate handler prevention |
| `src/shared/logging/filesystem.py` | 61-62 | Bare filename default to "." |
| `src/shared/logging/filesystem.py` | 72 | Formatter inheritance assertion |
