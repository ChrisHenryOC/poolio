# Security Code Review for PR #82

## Summary

PR #82 adds message validation functions for the Poolio IoT system, implementing envelope validation, message size limits, payload field validation, and timestamp freshness checks. From a security perspective, this is a positive change that adds input validation at system boundaries. The implementation follows safe coding practices with no injection risks, proper input validation, and no sensitive data exposure concerns.

## Findings

### Critical

None.

### High

None.

### Medium

**M1: Timestamp parsing does not validate date/time component ranges** - `/Users/chrishenry/source/poolio_rearchitect/src/shared/messages/validator.py:203-252`

The `_parse_iso_timestamp` function uses a regex that matches the format but does not validate that date/time components are within valid ranges. An attacker could send malformed timestamps like `2026-99-99T99:99:99Z` that would pass the regex check and produce invalid Unix timestamps. This could lead to incorrect freshness validation decisions.

```python
# The regex matches the format but doesn't validate ranges
ISO_TIMESTAMP_PATTERN = re.compile(
    r"^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(Z|[+-]\d{2}:\d{2})$"
)
```

**Recommendation**: Add range validation for month (1-12), day (1-31), hour (0-23), minute (0-59), second (0-59). Consider returning `None` early if any component is out of range. CWE-20 (Improper Input Validation).

---

**M2: Timezone offset not validated for reasonable range** - `/Users/chrishenry/source/poolio_rearchitect/src/shared/messages/validator.py:244-250`

The timezone offset parsing accepts any values for hours and minutes without validating they are within reasonable bounds. An attacker could craft timestamps with extreme offsets (e.g., `+99:99`) that would produce unexpected Unix timestamp results.

```python
# No validation that tz_hour <= 14 or tz_min <= 59
tz_hour = int(tz_str[1:3])
tz_min = int(tz_str[4:6])
offset_seconds = sign * (tz_hour * 3600 + tz_min * 60)
```

**Recommendation**: Validate timezone offset hours are within -14 to +14 and minutes are 0-59 (standard timezone offsets range from UTC-12 to UTC+14). CWE-20 (Improper Input Validation).

### Low

**L1: Error messages expose internal details about message validation** - `/Users/chrishenry/source/poolio_rearchitect/src/shared/messages/validator.py:271,287,304`

Error messages return detailed information about validation failures including exact timestamps, byte counts, and age in seconds. While this aids debugging, in a production IoT environment, detailed error messages could help attackers understand system behavior and craft targeted attacks.

Example error messages:
- `"Message size {size_bytes} bytes exceeds maximum..."`
- `"Message timestamp is {-age_seconds} seconds in the future..."`

**Recommendation**: For an IoT system this is acceptable given the debugging benefits. Consider whether error details should be logged server-side rather than returned to potentially untrusted callers. This is informational only.

---

**L2: validate_payload allows unknown fields in payload** - `/Users/chrishenry/source/poolio_rearchitect/src/shared/messages/validator.py:170-191`

The `validate_payload` function only checks for required fields and does not reject payloads with unexpected additional fields. This is a permissive validation approach. While this provides flexibility, it means malicious actors could inject additional data into messages.

**Recommendation**: This is acceptable for IoT message evolution flexibility. The current approach follows the "be liberal in what you accept" principle. No action required unless strict schema enforcement is desired.

## Security Positives

The following security-relevant aspects of this PR are well implemented:

1. **Message size validation** (`validate_message_size`): Properly enforces 4KB limit at the byte level using UTF-8 encoding, preventing resource exhaustion attacks (CWE-400).

2. **Timestamp freshness validation**: Prevents replay attacks by rejecting stale messages (5 minutes for commands, 15 minutes for status). This is critical for command messages where an attacker could replay old commands.

3. **Future timestamp rejection**: Clock skew tolerance of 60 seconds while rejecting far-future timestamps prevents time manipulation attacks.

4. **No use of dangerous functions**: The code does not use `eval()`, `exec()`, `pickle`, or `subprocess` with user input.

5. **No hardcoded secrets**: No credentials or API keys in the validation code.

6. **Type-specific validation thresholds**: Command messages (which have higher security impact) use stricter 5-minute freshness vs 15 minutes for status messages.

## Attack Surface Analysis

This validation code operates at the message boundary where untrusted data enters the system. The validation functions are defensive and fail-safe:

- Invalid input returns `(False, [errors])` rather than raising exceptions
- No state is modified during validation
- Functions are pure and have no side effects

The primary attack vectors for IoT message systems (replay attacks, oversized messages, malformed data) are addressed by this implementation.
