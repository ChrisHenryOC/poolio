# Security Code Review for PR #91

## Summary

This PR introduces a configuration management module for the Poolio IoT system with environment-specific settings, API key selection, and node defaults. The code demonstrates good security practices including input validation at boundaries, separation of prod/nonprod environments, and no secrets in code. One medium-severity concern exists around future file loading functionality that will need careful implementation to avoid path traversal vulnerabilities.

## Findings

### Critical

None.

### High

None.

### Medium

**Missing validation on feed name inputs** - `/Users/chrishenry/source/poolio_rearchitect/src/shared/config/environment.py:33-57`

The `get_feed_name()` function validates the environment but does not validate the `logical_name` parameter. While currently the feed names appear to come from internal code, if this function is ever called with user-controlled input, it could lead to feed name injection. For example, a malicious `logical_name` containing dots or slashes could potentially target unintended feeds.

```python
def get_feed_name(logical_name: str, environment: str) -> str:
    # environment is validated, but logical_name is used directly
    validate_environment(environment)
    group = FEED_GROUPS[environment]
    if environment == "prod":
        return f"{group}.{logical_name}"  # logical_name not validated
```

Recommendation: If `logical_name` will ever accept external input, add validation to ensure it contains only alphanumeric characters, hyphens, and underscores (matching Adafruit IO feed name requirements).

CWE-20: Improper Input Validation

---

**Future file loading needs path traversal protection** - `/Users/chrishenry/source/poolio_rearchitect/src/shared/config/loader.py:89-90`

The TODO comments indicate file loading from `config.json` and `settings.toml` will be implemented. When this is added, care must be taken to:

1. Use fixed file paths or validate against a whitelist
2. Avoid concatenating user input into file paths
3. Consider using `os.path.realpath()` to resolve symlinks and prevent traversal

```python
    # TODO: Load from config.json and merge
    # TODO: Load from settings.toml and merge secrets
```

Recommendation: When implementing file loading, ensure paths are hardcoded or derived from a trusted source. Do not allow environment variables or user input to control config file paths without validation.

CWE-22: Improper Limitation of a Pathname to a Restricted Directory

### Low

**API key handling relies on caller providing secrets dict** - `/Users/chrishenry/source/poolio_rearchitect/src/shared/config/environment.py:60-80`

The `select_api_key()` function receives secrets as a dictionary parameter. This is actually a good pattern (dependency injection), but worth noting that the calling code must ensure:

1. The secrets dict does not get logged
2. The returned API key is not exposed in logs or error messages

The current implementation does not log the key value, which is correct. This is informational for future maintenance.

---

**Environment defaults to prod** - `/Users/chrishenry/source/poolio_rearchitect/src/shared/config/loader.py:82`

The `load_config()` function defaults to "prod" environment when no override is provided:

```python
    environment = env_override if env_override else "prod"
```

This is a safe default (fail-secure), but could potentially cause production impact if a developer forgets to set the environment. Consider whether requiring explicit environment specification might be safer for your deployment model.

## Positive Security Observations

1. **Environment validation at boundaries**: All public functions validate the `environment` parameter before use via `validate_environment()`.

2. **No hardcoded secrets**: API keys are referenced by name only (`AIO_KEY_PROD`, `AIO_KEY_NONPROD`), not stored in code.

3. **Prod/nonprod separation**: Different feed groups and API keys per environment prevent accidental cross-environment operations.

4. **Allowlist validation**: Uses explicit allowlists for valid environments and node types rather than denylists.

5. **Fail-fast on invalid input**: `ConfigurationError` exceptions are raised immediately for invalid inputs rather than silently falling back to defaults.

## Files Reviewed

- `/Users/chrishenry/source/poolio_rearchitect/src/shared/config/__init__.py`
- `/Users/chrishenry/source/poolio_rearchitect/src/shared/config/defaults.py`
- `/Users/chrishenry/source/poolio_rearchitect/src/shared/config/environment.py`
- `/Users/chrishenry/source/poolio_rearchitect/src/shared/config/loader.py`
- `/Users/chrishenry/source/poolio_rearchitect/src/shared/config/schema.py`
- `/Users/chrishenry/source/poolio_rearchitect/tests/unit/test_config.py`
