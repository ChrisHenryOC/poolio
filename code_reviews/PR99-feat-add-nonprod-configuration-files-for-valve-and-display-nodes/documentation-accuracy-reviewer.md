# Documentation Accuracy Review for PR #99

## Summary

This PR introduces configuration files for valve and display nodes in a new `config/nonprod/` directory with embedded `_config_fields` documentation blocks and a `settings.toml.template`. The inline documentation is generally accurate and comprehensive, but there are inconsistencies with the existing architecture documentation regarding directory structure, discrepancies between the new extended configs and existing minimal configs, and references to schemas that do not exist.

## Findings

### High Severity

1. **Directory structure inconsistency with architecture documentation**

   The PR creates files in `config/nonprod/` but `docs/architecture.md` Section 13 (Deployment) specifies configuration files should be in:
   ```
   circuitpython/configs/
   ├── valve-node/
   │   ├── nonprod/
   │   │   └── config.json
   ```

   The new files are placed in:
   ```
   config/nonprod/
   ├── valve_node.json
   ├── display_node.json
   └── settings.toml.template
   ```

   This creates parallel config locations which will cause confusion about which is the source of truth. Either the PR should use the documented structure or the architecture documentation needs updating.

2. **Schema references to non-existent files**

   Both JSON files reference schemas that do not exist:
   - `"$schema": "../schemas/display_node_config.json"` (display_node.json line 2)
   - `"$schema": "../schemas/valve_node_config.json"` (valve_node.json line 2)

   The `config/schemas/` directory does not exist in the repository.

### Medium Severity

1. **Inconsistent naming convention between PR and existing configs**

   - PR uses underscore: `valve_node.json`, `display_node.json`
   - Existing configs use hyphen: `valve-node/`, `display-node/`
   - Architecture documentation uses hyphen in examples

2. **New configs have many more fields than existing configs**

   The existing `circuitpython/configs/valve-node/nonprod/config.json` has 12 lines with minimal fields. The new `config/nonprod/valve_node.json` has 56 lines with extensive fields (`safety`, extended `valve` options, `hardware.enabled`, etc.). These either represent an undocumented schema expansion or the new files are a different format intended for a different purpose.

3. **settings.toml.template uses different key naming than architecture docs**

   The template uses `AIO_KEY_NONPROD` but the architecture documentation example in Section 11 shows:
   ```toml
   AIO_KEY_PROD = "aio_prod_api_key"
   AIO_KEY_NONPROD = "aio_nonprod_api_key"
   ```
   while Section 13 shows just `AIO_KEY`:
   ```toml
   AIO_KEY = "your_aio_key"
   ```

   The template correctly matches Section 11, but this creates inconsistency with Section 13.

### Low Severity

1. **_config_fields documentation references unclear hot-reload behavior**

   Multiple fields are documented as "Hot-reloadable" but there is no implementation or documentation explaining how hot-reload works in CircuitPython (which typically requires device reset). This may mislead developers about capabilities that do not exist yet.

2. **Architecture doc reference is imprecise**

   Both JSON files reference "Section 11" in their $comment but the section is titled "Environment Configuration" - including the section title would improve findability:
   ```
   "$comment": "See docs/architecture.md Section 11 (Environment Configuration) for details."
   ```

3. **Missing documentation for valve.default_start_time**

   The `valve_node.json` includes `"default_start_time": "06:00"` but this field is not mentioned in the architecture documentation's valve configuration examples.

4. **Touch calibration wildcard documentation**

   The field description `"touch.calibration.*": "Touch screen calibration values. Restart required."` uses a wildcard pattern, which is reasonable, but the actual nested fields (x_min, x_max, y_min, y_max) are not individually documented. Consider documenting the expected range and purpose.

### Recommendations

1. **Consolidate configuration file locations** - Choose either `config/` or `circuitpython/configs/` as the canonical location and update both the PR and architecture documentation to match. Given the deployment script uses `circuitpython/configs/`, that may be the better choice.

2. **Add the referenced schema files** - Create `config/schemas/display_node_config.json` and `config/schemas/valve_node_config.json` or remove the $schema references if schemas are not yet implemented.

3. **Align naming conventions** - Use consistent hyphen-based naming (`valve-node.json`) to match existing patterns, or update all existing files to underscore-based naming.

4. **Document hot-reload capability** - Either implement hot-reload and document how it works, or remove the "Hot-reloadable" claims until the feature exists. Consider adding a note explaining that this is planned functionality.

5. **Update architecture documentation Section 13** - The settings.toml example shows generic `AIO_KEY` but should match Section 11's environment-specific keys (`AIO_KEY_PROD`, `AIO_KEY_NONPROD`).

6. **Clarify relationship between minimal and extended configs** - If the new extended configs represent a schema evolution, document this transition. If they serve different purposes, document when each should be used.
