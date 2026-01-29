# Documentation Accuracy Review for PR #80

## Summary

This PR adds message type classes implementing FR-MSG-004 through FR-MSG-013. The docstrings are well-written and CircuitPython-compatible, with types documented in attribute descriptions. However, there are several discrepancies between the implementation and the requirements specification in `docs/requirements.md`, primarily around field naming and missing fields in composite types.

## Findings

### High

**Inconsistent: ScheduleInfo missing `enabled` and `nextScheduledFill` fields** - `/Users/chrishenry/source/poolio_rearchitect/src/shared/messages/types.py:291-306`

The `ScheduleInfo` class documents and implements fields that differ from FR-MSG-005 in the requirements:

Implementation:
- `start_time`, `window_hours`, `next_fill_time`, `next_check_time`

Requirements (FR-MSG-005):
- `enabled`, `startTime`, `windowHours`, `nextScheduledFill`

The `enabled` field is missing entirely, and `nextScheduledFill` vs `next_fill_time`/`next_check_time` represents a structural difference. The docstring accurately describes the implemented fields but the implementation itself diverges from the specification.

Recommendation: Update either the requirements or the implementation to ensure consistency. If the implementation is the intended design, update `docs/requirements.md` to match.

---

**Inconsistent: ValveState field `currentFillDuration` documented as nullable but requirements show default of 0** - `/Users/chrishenry/source/poolio_rearchitect/src/shared/messages/types.py:280-281`

The docstring states:

```text
current_fill_duration: Seconds since fill started, or None (int or None)
max_fill_duration: Maximum fill duration in seconds, or None (int or None)
```

The requirements JSON example in FR-MSG-005 shows:

```json
"currentFillDuration": 0,
"maxFillDuration": 540
```

The requirements use `0` (not `null`) for no current fill. The docstring documents `None` which represents a different semantic meaning.

Recommendation: Clarify whether `None` or `0` should represent "not filling" and ensure both documentation and tests align with the requirements.

---

### Medium

**Docstring type inconsistency: Command.parameters documented as `dict` but stub uses `dict[str, Any]`** - `/Users/chrishenry/source/poolio_rearchitect/src/shared/messages/types.py:383`

The docstring says:

```text
parameters: Command parameters (dict)
```

The type stub in `types.pyi:604-605` specifies:

```python
parameters: dict[str, Any]
```

While both are technically correct, the docstring could be more precise about the expected structure (string keys, any values).

Recommendation: Update docstring to `parameters: Command parameters mapping string keys to values (dict)` for consistency with the stub.

---

**Docstring type inconsistency: Error.context documented as `dict or None` but stub uses `dict[str, Any] | None`** - `/Users/chrishenry/source/poolio_rearchitect/src/shared/messages/types.py:419`

Similar to above, the docstring is less precise than the type stub.

Recommendation: Update docstring to clarify the expected dict structure.

---

**Missing FR-MSG-010 (Heartbeat) acknowledgment** - `/Users/chrishenry/source/poolio_rearchitect/src/shared/messages/types.py:1-4`

The file header comment references "FR-MSG-004 through FR-MSG-013" but does not mention that FR-MSG-010 (Heartbeat) is intentionally deferred per the requirements. This could confuse readers wondering why there is no `Heartbeat` class.

Recommendation: Add a comment noting that FR-MSG-010 (Heartbeat) is deferred per requirements.

---

### Low

**Test docstrings use camelCase field names inconsistent with Python code** - `/Users/chrishenry/source/poolio_rearchitect/tests/unit/test_message_types.py:687-688`

Several test docstrings reference JSON field names (camelCase) rather than Python attribute names (snake_case):

```python
def test_create_with_all_fields(self) -> None:
    """WaterLevel requires floatSwitch and confidence."""
```

The Python class uses `float_switch` (snake_case), not `floatSwitch` (camelCase). This mixes naming conventions.

Recommendation: Use Python attribute names in docstrings for consistency: "WaterLevel requires float_switch and confidence."

---

**Undocumented: Type stubs use `int` for Battery.percentage but no range validation documented** - `/Users/chrishenry/source/poolio_rearchitect/src/shared/messages/types.py:234`

The docstring states "Battery charge percentage 0-100 (int)" which is accurate but the class does not validate this range. The docstring correctly describes the expected range but does not mention that validation is not performed.

Recommendation: This is acceptable per Kent Beck's "make it work first" principle. No action needed unless validation is later added, at which point the docstring should be updated.
