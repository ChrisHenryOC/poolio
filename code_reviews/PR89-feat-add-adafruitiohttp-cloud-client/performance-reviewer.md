# Performance Review - PR #89

## Summary

The AdafruitIOHTTP client implementation has two significant resource management issues that could cause problems on resource-constrained ESP32 devices: missing response cleanup (socket leaks) and missing timeouts on network operations. Both violate the project's reliability requirements. Other potential optimizations would be premature without profiling data.

## Findings

### High Severity

#### 1. Response Objects Not Closed - Socket/Memory Leak

**Files:** `/Users/chrishenry/source/poolio_rearchitect/src/shared/cloud/adafruit_io_http.py`

**Lines:** 132, 170, 199, 225

All HTTP operations obtain response objects but never close them. On CircuitPython with `adafruit_requests`, each unclosed response holds a socket from the limited socket pool (typically 4-10 sockets on ESP32). This will cause socket exhaustion after a small number of API calls.

```python
# Line 132 - publish() - response discarded without close
requests.post(url, headers=self._get_headers(), json={"value": value})

# Line 170 - fetch_latest() - response used but not closed
response = requests.get(url, headers=self._get_headers())

# Line 199 - fetch_history() - response used but not closed
response = requests.get(url, headers=self._get_headers(), params=params)

# Line 225 - sync_time() - response used but not closed
response = requests.get(url, headers=self._get_headers())
```

**Fix:** Use try/finally to ensure response cleanup:

```python
def fetch_latest(self, feed):
    # ... validation ...
    response = requests.get(url, headers=self._get_headers())
    try:
        if response.status_code == 404:
            return None
        return response.json()["value"]
    finally:
        response.close()
```

For `publish()` where the response is ignored:

```python
def publish(self, feed, value):
    # ... validation ...
    response = requests.post(url, headers=self._get_headers(), json={"value": value})
    response.close()  # Close even if we don't use the response
```

**Impact:** Critical on CircuitPython. After 4-10 API calls (depending on socket pool size), all subsequent network operations will fail.

---

#### 2. No Timeouts on Network Operations

**Files:** `/Users/chrishenry/source/poolio_rearchitect/src/shared/cloud/adafruit_io_http.py`

**Lines:** 132, 170, 199, 225

All HTTP requests lack timeout parameters. Per the project's reliability requirements in `CLAUDE.md`: "Explicit timeouts on all blocking operations" and "Feed watchdog before/after blocking operations."

```python
# Line 132 - can block indefinitely
requests.post(url, headers=self._get_headers(), json={"value": value})

# Lines 170, 199, 225 - same issue with GET requests
response = requests.get(url, headers=self._get_headers())
```

**Fix:** Add timeout parameter to all requests:

```python
# Use a reasonable timeout for IoT devices (e.g., 30 seconds)
DEFAULT_TIMEOUT = 30

response = requests.get(url, headers=self._get_headers(), timeout=DEFAULT_TIMEOUT)
```

**Impact:** On battery-powered devices (Pool Node), an indefinite block prevents deep sleep and drains the battery. On all devices, it can cause watchdog resets if the watchdog timer expires during a blocked network call.

---

### Medium Severity

#### 3. No Error Handling for Non-404 HTTP Errors

**Files:** `/Users/chrishenry/source/poolio_rearchitect/src/shared/cloud/adafruit_io_http.py`

**Lines:** 172-175, 201-206, 227-235

The code handles 404 gracefully but ignores other error status codes (500, 503, rate limiting 429, etc.). A 500 error would cause an exception when calling `.json()` on an error response, potentially leaving the response unclosed.

```python
# Line 172-175 - only checks 404, other errors will fail on json()
if response.status_code == 404:
    return None
return response.json()["value"]  # Will fail for 500, 503, etc.
```

**Fix:** Check for success before parsing:

```python
if response.status_code == 404:
    return None
if response.status_code != 200:
    # Log error and return None or raise specific exception
    return None
return response.json()["value"]
```

**Impact:** Without proper handling, a server error could cause an unhandled exception and leave sockets unclosed, compounding the socket leak issue.

---

### Low Severity

#### 4. Header Dictionary Created on Every Request

**Files:** `/Users/chrishenry/source/poolio_rearchitect/src/shared/cloud/adafruit_io_http.py`

**Lines:** 106-113

The `_get_headers()` method creates a new dictionary on every API call:

```python
def _get_headers(self):
    return {"X-AIO-Key": self._api_key}
```

**Assessment:** Following Kent Beck's "Make It Work, Make It Right, Make It Fast" principle, this is NOT a problem that needs fixing now. Network calls are infrequent (every few minutes at most), and the dictionary is small. Caching headers would be premature optimization without profiling evidence. The current implementation is clear and correct.

**Recommendation:** No change needed. The code correctly prioritizes clarity over micro-optimization.

---

#### 5. List Comprehension in fetch_history()

**Files:** `/Users/chrishenry/source/poolio_rearchitect/src/shared/cloud/adafruit_io_http.py`

**Line:** 206

```python
return [item[1] for item in data]
```

**Assessment:** For 24 hours at 6-minute resolution, this creates a list of ~240 items. On ESP32 with 2MB PSRAM, this is well within capacity. A generator would save memory but complicate downstream consumers who expect a list.

**Recommendation:** No change needed. This is not a hot path and the data volume is reasonable for the use case.

---

## Summary Table

| Issue | Severity | Line(s) | Fix Required |
|-------|----------|---------|--------------|
| Response objects not closed | High | 132, 170, 199, 225 | Yes |
| No timeouts on requests | High | 132, 170, 199, 225 | Yes |
| No error handling for non-404 | Medium | 172-175, 201-206, 227-235 | Recommended |
| Header dict on every call | Low | 106-113 | No (premature) |
| List comprehension | Low | 206 | No (premature) |

## Kent Beck Principle Applied

Per "Make It Work, Make It Right, Make It Fast":
- The high severity issues (socket leaks, no timeouts) affect **correctness** - the code will stop working after a few calls
- The low severity items are **performance** concerns without evidence of bottlenecks - optimizing them now would be premature
