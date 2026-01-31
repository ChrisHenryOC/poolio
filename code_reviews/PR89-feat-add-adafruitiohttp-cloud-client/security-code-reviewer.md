# Security Review - PR #89

## Summary

This PR introduces an HTTP client for Adafruit IO cloud communication. The implementation correctly uses HTTPS for all API requests and properly handles API key transmission via headers. However, there are **no request timeouts** on any HTTP operations, which can lead to indefinite blocking and potential denial-of-service conditions on resource-constrained IoT devices. Additionally, HTTP responses are not closed/released, which could lead to resource exhaustion.

## Findings

### High Severity

#### SEC-001: Missing HTTP Request Timeouts (CWE-400: Uncontrolled Resource Consumption)

**Location:** `/Users/chrishenry/source/poolio_rearchitect/src/shared/cloud/adafruit_io_http.py:132, 170, 199, 225`

All HTTP requests (`requests.post` and `requests.get`) are made without timeout parameters. This directly violates project requirements in **NFR-REL-005** which specifies:

> "HTTP requests: Maximum 10 seconds"

On IoT devices with limited resources, a request that hangs indefinitely will:
1. Block the main execution loop
2. Eventually trigger a watchdog reset (recovery), but this wastes battery on Pool Node
3. Could be exploited by an attacker performing a slowloris-style attack if the device is on a compromised network

**Affected code:**

```python
# Line 132 - publish()
requests.post(url, headers=self._get_headers(), json={"value": value})

# Line 170 - fetch_latest()
response = requests.get(url, headers=self._get_headers())

# Line 199 - fetch_history()
response = requests.get(url, headers=self._get_headers(), params=params)

# Line 225 - sync_time()
response = requests.get(url, headers=self._get_headers())
```

**Recommendation:** Add `timeout=10` parameter to all requests per NFR-REL-005:

```python
requests.post(url, headers=self._get_headers(), json={"value": value}, timeout=10)
```

---

### Medium Severity

#### SEC-002: HTTP Response Objects Not Closed (CWE-404: Improper Resource Shutdown or Release)

**Location:** `/Users/chrishenry/source/poolio_rearchitect/src/shared/cloud/adafruit_io_http.py:170, 199, 225`

HTTP response objects from `requests.get()` are used but never explicitly closed. This violates **NFR-REL-007** which states:

> "SHALL explicitly close all HTTP response objects after use"

On CircuitPython devices with limited sockets, this can lead to socket exhaustion after repeated API calls.

**Affected code:**

```python
# Line 170-175 - fetch_latest()
response = requests.get(url, headers=self._get_headers())
if response.status_code == 404:
    return None
return response.json()["value"]  # response never closed

# Line 199-206 - fetch_history()
response = requests.get(url, headers=self._get_headers(), params=params)
# ...
return [item[1] for item in data]  # response never closed

# Line 225-236 - sync_time()
response = requests.get(url, headers=self._get_headers())
# ...
return datetime(...)  # response never closed
```

**Recommendation:** Use try/finally or context manager to ensure response closure:

```python
response = requests.get(url, headers=self._get_headers(), timeout=10)
try:
    if response.status_code == 404:
        return None
    return response.json()["value"]
finally:
    response.close()
```

---

#### SEC-003: No Validation of API Response Data (CWE-20: Improper Input Validation)

**Location:** `/Users/chrishenry/source/poolio_rearchitect/src/shared/cloud/adafruit_io_http.py:175, 204, 227-235`

API responses are parsed without validation. If the Adafruit IO API returns unexpected data (malformed JSON, missing keys, wrong types), the code will raise unhandled exceptions.

**Examples:**

```python
# Line 175 - assumes "value" key exists
return response.json()["value"]

# Line 204 - assumes "data" key exists and items are arrays with index [1]
data = response.json().get("data", [])
return [item[1] for item in data]  # IndexError if item has <2 elements

# Lines 229-236 - assumes all time struct keys exist
return datetime(
    year=data["year"],    # KeyError if missing
    month=data["mon"],
    # ...
)
```

**Impact:** While this is primarily a reliability issue, unexpected API responses (from network issues, API changes, or man-in-the-middle attacks) could cause unhandled exceptions that crash the device.

**Recommendation:** Add defensive validation:

```python
def fetch_latest(self, feed):
    # ...
    data = response.json()
    if "value" not in data:
        return None  # or raise a specific exception
    return data["value"]
```

---

### Low Severity

#### SEC-004: No HTTP Response Status Code Validation Beyond 404

**Location:** `/Users/chrishenry/source/poolio_rearchitect/src/shared/cloud/adafruit_io_http.py:172-175, 200-206, 227`

Only 404 status codes are explicitly handled. Other error status codes (401, 403, 429, 500, etc.) are silently ignored and treated as success.

**Examples:**

```python
# Line 172-175 - only checks 404
if response.status_code == 404:
    return None
return response.json()["value"]  # Will fail on 401, 500, etc.
```

**Impact:**
- 401 (Unauthorized) with invalid API key will try to parse error response as data
- 429 (Rate Limited) will not trigger appropriate backoff behavior
- 500 (Server Error) will cause JSON parse failures

**Recommendation:** Add status code validation:

```python
if response.status_code == 404:
    return None
if response.status_code != 200:
    raise RuntimeError(f"API error: {response.status_code}")
```

---

#### SEC-005: API Key Stored in Memory Without Protection

**Location:** `/Users/chrishenry/source/poolio_rearchitect/src/shared/cloud/adafruit_io_http.py:65`

The API key is stored as a plain string attribute (`self._api_key`). While this is standard practice and the underscore convention indicates private use, on embedded devices with limited security boundaries, this could theoretically be extracted via memory inspection.

**Impact:** Low - this is expected behavior for IoT devices, and the API key must be accessible to make requests. The leading underscore appropriately signals internal use.

**Note:** This is an observation rather than a required fix. The project already follows best practices by excluding `settings.toml` from version control.

---

## Security Strengths

1. **HTTPS enforced** - Base URL uses `https://io.adafruit.com` (line 67)
2. **API key in header** - Uses `X-AIO-Key` header instead of URL parameter (line 113), preventing key leakage in logs/URLs
3. **Environment separation** - Feed prefixing prevents cross-environment data pollution (lines 92-104)
4. **No credential logging** - API key is not logged or exposed in error messages
5. **No shell injection risk** - No subprocess or eval usage
6. **No path traversal risk** - Feed names are used directly in URL construction without file system access

## Summary Table

| ID | Severity | CWE | Issue | Line(s) |
|----|----------|-----|-------|---------|
| SEC-001 | High | CWE-400 | Missing HTTP timeouts | 132, 170, 199, 225 |
| SEC-002 | Medium | CWE-404 | Response objects not closed | 170, 199, 225 |
| SEC-003 | Medium | CWE-20 | No response data validation | 175, 204, 227-235 |
| SEC-004 | Low | N/A | Incomplete status code handling | 172-175, 200-206 |
| SEC-005 | Low | N/A | API key in plain memory | 65 |

## Recommendation

**SEC-001 (timeouts) should be addressed before merge** as it directly violates documented reliability requirements (NFR-REL-005) and could cause device hangs on network issues. SEC-002 (response closure) is also important for production stability. SEC-003 and SEC-004 are quality improvements that could be addressed in a follow-up PR.
