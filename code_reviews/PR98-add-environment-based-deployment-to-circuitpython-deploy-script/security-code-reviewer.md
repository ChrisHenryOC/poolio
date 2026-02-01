# Security Code Review for PR #98

## Summary

This PR adds environment-based deployment functionality to the CircuitPython deploy script, enabling separate `prod` and `nonprod` configurations. The security posture is reasonable for a local developer tool. The `--env` parameter is validated via argparse `choices`, which mitigates path traversal through that vector. However, the `--target` parameter lacks validation and could theoretically allow path traversal if a malicious value is provided. The risk is low given this is a CLI tool run by developers on their own machines.

## Findings

### Critical

None identified.

### High

None identified.

### Medium

**Path Traversal via `--target` Parameter** - `circuitpython/deploy.py:258` (CWE-22)

The `deploy_config` function constructs a file path using the `target` parameter without validation:

```python
config_source = CONFIGS_DIR / target / environment / "config.json"
```

While `environment` is validated via argparse `choices=VALID_ENVIRONMENTS`, the `target` parameter is not validated against an allowlist. An attacker with access to run the script could potentially use path traversal:

```bash
python deploy.py --target "../../etc" --env nonprod
```

This would attempt to read `/Users/.../circuitpython/configs/../../etc/nonprod/config.json`.

**Risk Assessment:**
- **Attack surface**: Low - this is a local CLI tool run by developers
- **Impact**: Low - worst case is reading an arbitrary JSON file and copying it to a mounted device
- **Likelihood**: Very low - requires malicious developer running their own tool
- **Existing mitigations**:
  - The script only works when a CIRCUITPY device is mounted
  - The file must be valid JSON to be copied
  - The file must exist at the traversed path with exact subdirectory structure

**Recommendation**: Add validation that `target` exists as a directory in `CONFIGS_DIR` or validate against the list of known targets from requirements files. This is defense-in-depth rather than fixing an actively exploitable vulnerability.

### Low

**Information Disclosure via Error Messages** - `circuitpython/deploy.py:141,269-270`

Full file paths are printed in warning and error messages:

```python
print(f"\nWARNING: Config not found: {config_source}")
print(f"\nERROR: Invalid JSON in {config_source}: {e}")
```

In the context of a local development tool, this is helpful debugging information. However, if this script were ever exposed in a CI/CD environment or shared context, full paths could leak system information.

**Recommendation**: No action needed for current use case. Be aware if script usage expands.

---

**No Security Issues Found In:**

1. **Environment validation** - The `--env` parameter is properly validated via `choices=VALID_ENVIRONMENTS` (line 315-316), preventing injection of arbitrary environment names.

2. **JSON validation** - Config files are validated as JSON before being copied (lines 266-271), preventing malformed data from being deployed.

3. **Zip extraction** - The existing `download_bundle` function (lines 96-102) already has proper path traversal protection for zip extraction using `resolve()` and path prefix checking.

4. **Device path handling** - The `--device` parameter allows arbitrary paths, but this is intentional and the user must have access to that path anyway.

5. **Config file contents** - The JSON config files (`config.json`) contain only configuration data (device IDs, intervals, etc.) with no executable content or secrets.

## Security Considerations for Future Development

1. **Secrets handling**: The `settings.toml` file containing WiFi passwords and API keys is correctly not managed by this script. The warning message (lines 242-249) appropriately reminds users to configure secrets manually.

2. **Environment separation**: The prod/nonprod separation is well-implemented with clear feed group differentiation (`poolio` vs `poolio-nonprod`), reducing risk of accidental production modifications during development.
