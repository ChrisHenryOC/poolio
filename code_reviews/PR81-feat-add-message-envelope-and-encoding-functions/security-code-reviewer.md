# Security Review for PR #81

## Summary

This PR implements message envelope creation, parsing, encoding, and decoding for the Poolio IoT system. The code uses safe JSON parsing (not pickle) and implements an allowlist-based approach for message type instantiation, which prevents arbitrary class instantiation attacks. The device ID validation is well-implemented with a strict regex. However, there are some medium-severity concerns around unbounded input processing and lack of payload validation that could lead to DoS or unexpected behavior on resource-constrained IoT devices.

## Findings by Severity

### Critical

None identified.

### High

None identified.

### Medium

**M1: No size limit on JSON input - potential DoS vector (CWE-400)**

`/Users/chrishenry/source/poolio_rearchitect/src/shared/messages/envelope.py:111-113`

```python
def parse_envelope(json_str: str) -> tuple[dict[str, Any], dict[str, Any]]:
    ...
    data = json.loads(json_str)
```

The `parse_envelope()` function accepts a JSON string of arbitrary size. On resource-constrained IoT devices (ESP32 with limited RAM), a maliciously large JSON payload sent via MQTT could cause memory exhaustion and device crashes.

**Recommendation**: Add an optional size limit parameter or document maximum expected message size. For IoT devices, consider validating `len(json_str)` before parsing, for example:

```python
MAX_MESSAGE_SIZE = 4096  # 4KB reasonable for IoT messages
if len(json_str) > MAX_MESSAGE_SIZE:
    raise ValueError(f"Message exceeds maximum size of {MAX_MESSAGE_SIZE} bytes")
```

**M2: Arbitrary kwargs passed to class constructors (CWE-20)**

`/Users/chrishenry/source/poolio_rearchitect/src/shared/messages/decoder.py:130` and `:166`

```python
result[key] = cls(**value)  # line 130
...
return cls(**snake_payload)  # line 166
```

While the class selection is restricted to an allowlist, the payload fields are passed directly to constructors via `**kwargs` without validation. An attacker could inject unexpected fields that:
1. Cause TypeError on CircuitPython if the class does not expect extra arguments
2. Potentially set arbitrary attributes if a class has a permissive `__init__`

The current message type classes have strict `__init__` signatures, so extra arguments would raise TypeError. This is acceptable behavior but could be made more explicit.

**Recommendation**: This is acceptable given the strict class definitions, but consider catching TypeError in `decode_message()` and raising a more informative ValueError indicating which fields were unexpected.

**M3: Unbounded recursion depth in nested structure processing (CWE-674)**

`/Users/chrishenry/source/poolio_rearchitect/src/shared/messages/decoder.py:87-112` and `/Users/chrishenry/source/poolio_rearchitect/src/shared/messages/encoder.py:38-75`

```python
def _convert_keys_to_snake(data: Any, preserve_keys: bool = False) -> Any:
    if isinstance(data, dict):
        ...
        result[snake_key] = _convert_keys_to_snake(v, ...)  # recursive
    elif isinstance(data, list):
        return [_convert_keys_to_snake(item, ...) for item in data]  # recursive
```

Both `_convert_keys_to_snake()` and `_encode_value()` use recursion to process nested structures. A deeply nested payload could trigger stack overflow, especially on CircuitPython where stack depth is limited.

**Recommendation**: Add a depth parameter with a reasonable limit (e.g., 10 levels) to prevent stack exhaustion:

```python
def _convert_keys_to_snake(data: Any, preserve_keys: bool = False, _depth: int = 0) -> Any:
    if _depth > 10:
        raise ValueError("Message nesting exceeds maximum depth")
```

### Low

**L1: Message type parameter not validated in create_envelope()**

`/Users/chrishenry/source/poolio_rearchitect/src/shared/messages/envelope.py:66-95`

The `msg_type` parameter is included in the envelope without validation. While this allows flexibility, it could lead to messages with invalid types being created. The `decode_message()` function validates types on the receiving end, so this is a minor consistency issue.

**L2: Timestamp parameter not validated**

`/Users/chrishenry/source/poolio_rearchitect/src/shared/messages/envelope.py:86-87`

```python
if timestamp is None:
    timestamp = _get_current_timestamp()
```

When a timestamp is provided, it is accepted without format validation. An invalid timestamp format would only be caught on the receiving/parsing side if at all.

**L3: Error messages include user-controlled field names**

`/Users/chrishenry/source/poolio_rearchitect/src/shared/messages/decoder.py:154`

```python
raise ValueError(f"Unknown message type: {msg_type}")
```

While not directly exploitable, error messages that include user-controlled input could potentially be used for log injection if the error message is logged without sanitization downstream. This is very low risk given the context.

## Positive Security Observations

1. **Safe deserialization**: Uses `json.loads()` instead of pickle or similar unsafe deserializers
2. **Allowlist for class instantiation**: `_MESSAGE_TYPES` and `_NESTED_SCHEMAS` dictionaries restrict which classes can be instantiated
3. **Input validation on device_id**: Well-implemented with precompiled regex (`^[a-z0-9-]+$`) and length check (1-64 chars)
4. **Non-vulnerable regex**: The device ID regex is simple and not susceptible to ReDoS
5. **Explicit required field checking**: Envelope fields are validated before use
6. **No eval/exec usage**: No dynamic code execution
7. **Private attributes skipped in encoding**: `_encode_value()` skips attributes starting with `_`, preventing accidental exposure of internal state
