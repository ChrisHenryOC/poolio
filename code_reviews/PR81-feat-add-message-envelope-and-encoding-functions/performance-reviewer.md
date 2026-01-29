# Performance Review for PR #81

## Summary

This PR implements message envelope creation/parsing and encoder/decoder functions for converting between Python objects and JSON with case conversion. The implementation is well-structured with pre-compiled regex patterns and module-level lookup dictionaries. No significant performance issues were found; the code follows appropriate patterns for an IoT message processing library where messages are processed infrequently (not in hot loops).

## Findings by Severity

### High

None.

### Medium

None.

### Low

1. **String concatenation in loop** (`/Users/chrishenry/source/poolio_rearchitect/src/shared/messages/encoder.py:29-34`)

   The `snake_to_camel` function uses string concatenation in a loop:
   ```python
   result = parts[0]
   for part in parts[1:]:
       if part:  # Skip empty parts from trailing underscores
           result += part.capitalize()
   ```

   **Assessment:** This is a non-issue in practice. Field names are short (typically 2-4 parts), so the quadratic string concatenation behavior is negligible. Optimizing with `"".join()` would add complexity without measurable benefit. The code prioritizes readability appropriately.

2. **Regex called per key during decoding** (`/Users/chrishenry/source/poolio_rearchitect/src/shared/messages/decoder.py:46-47`)

   The `camel_to_snake` function calls `_CAMEL_PATTERN.sub()` for every dictionary key:
   ```python
   result = _CAMEL_PATTERN.sub(r"\1_\2", name)
   return result.lower()
   ```

   **Assessment:** The regex is correctly pre-compiled at module level (line 33), which is the appropriate optimization. Caching the conversion results (e.g., with `lru_cache`) would add memory overhead without justification since:
   - Messages have a fixed, small set of field names
   - IoT devices process messages infrequently (every 2+ minutes)
   - CircuitPython has limited memory, so caching should be avoided

3. **Dictionary created for envelope extraction** (`/Users/chrishenry/source/poolio_rearchitect/src/shared/messages/envelope.py:124-129`)

   The `parse_envelope` function creates a new dictionary for the envelope fields instead of returning the original:
   ```python
   envelope = {
       "version": data["version"],
       "type": data["type"],
       "deviceId": data["deviceId"],
       "timestamp": data["timestamp"],
   }
   ```

   **Assessment:** This is the correct design. Creating a clean envelope dict without the payload prevents accidental modification of shared state and keeps the API clean. The overhead is minimal (4 key-value pairs).

## Performance Strengths

1. **Pre-compiled regex patterns** - Both `_CAMEL_PATTERN` (decoder.py:33) and `DEVICE_ID_PATTERN` (envelope.py:26) are compiled at module load time, avoiding repeated compilation.

2. **Module-level lookup dictionaries** - `_MESSAGE_TYPES`, `_NESTED_SCHEMAS`, and `_PRESERVE_KEYS_FIELDS` are defined at module level, enabling O(1) lookups without per-call initialization.

3. **Compact JSON output** - `encode_message` uses `separators=(",", ":")` (encoder.py:102) to produce minimal JSON without whitespace, reducing message size for MQTT transmission.

4. **Early validation failure** - `validate_device_id` checks length before regex (envelope.py:42), failing fast on obvious violations.

5. **Appropriate use of isinstance checks** - The encoder uses a type dispatch pattern (encoder.py:48-64) that handles primitives first before more expensive object introspection.

## Not Flagged (By Design)

- **No `__slots__` on message classes** - The message classes in `types.py` do not use `__slots__`. While this would reduce memory per instance, these classes are instantiated once per message (not in tight loops), so the overhead is negligible. Adding `__slots__` would complicate the code without measurable benefit.

- **Recursive key conversion** - The `_convert_keys_to_snake` and `_encode_value` functions use recursion. For IoT message payloads (typically 2-3 levels deep), this is appropriate. Stack depth issues would only arise with pathological inputs not expected in this domain.

## Recommendations

No changes recommended. The implementation appropriately balances readability and performance for an IoT message processing library running on resource-constrained devices. The code avoids premature optimization while still following Python best practices (pre-compiled regex, module-level constants).
