# Test Coverage Review for PR #99

## Summary

This PR adds three nonprod configuration files (`valve_node.json`, `display_node.json`, `settings.toml.template`) but includes no tests for them. The JSON files reference non-existent schemas (`$schema": "../schemas/valve_node_config.json"`), and there are no tests validating that the configuration values match the system defaults or that the files can be loaded and validated. Per Kent Beck's first rule of simple design, "Passes the tests" is the primary goal, yet these configuration files have no tests verifying they work as intended.

## Findings

### High Severity

1. **Missing JSON Schema Definitions and Validation Tests**

   - **Location:** `/Users/chrishenry/source/poolio_rearchitect/config/nonprod/valve_node.json` (line 2), `/Users/chrishenry/source/poolio_rearchitect/config/nonprod/display_node.json` (line 2)
   - **Issue:** Both JSON files reference schemas that do not exist (`../schemas/valve_node_config.json`, `../schemas/display_node_config.json`). The `schemas/` directory does not exist in the project. This violates the project requirement NFR-ARCH-003: "SHALL support configuration validation against schema" (from `docs/requirements.md` line 1694).
   - **Evidence:** `Glob("**/schemas/**")` returned no files.
   - **TDD Analysis:** These configuration files could not have been written test-first since there is no schema to validate against and no tests to verify the schema references are correct.
   - **Recommendation:** Either create the schema files and add schema validation tests, or remove the `$schema` references if schemas are not yet implemented.

2. **No Tests for Configuration File Loading**

   - **Location:** New files in `/Users/chrishenry/source/poolio_rearchitect/config/nonprod/`
   - **Issue:** The deploy script (`circuitpython/deploy.py`) expects configs at `circuitpython/configs/{target}/{environment}/config.json` but these files are placed in `config/nonprod/`. This path mismatch means the new config files will not be deployed by the current deployment system.
   - **Evidence:** `deploy.py` line 43 defines `CONFIGS_DIR = SCRIPT_DIR / "configs"` (i.e., `circuitpython/configs/`), but the new files are in `config/nonprod/`.
   - **TDD Analysis:** If there were integration tests for the deployment workflow with these configs, this path issue would have been caught immediately.
   - **Recommendation:** Add tests that verify the configuration files can be found and loaded by the deployment system.

### Medium Severity

1. **Configuration Value Consistency Not Tested**

   - **Location:** `/Users/chrishenry/source/poolio_rearchitect/config/nonprod/valve_node.json`, `/Users/chrishenry/source/poolio_rearchitect/config/nonprod/display_node.json`
   - **Issue:** The JSON files define different field names and structures than `NODE_DEFAULTS` in `/Users/chrishenry/source/poolio_rearchitect/src/shared/config/defaults.py`. For example:
     - Defaults use `max_fill_minutes`, JSON uses `valve.max_fill_duration_minutes`
     - Defaults use `fill_window_hours`, JSON uses `safety.fill_window_hours`
     - Defaults use `chart_refresh_interval`, JSON uses `display.chart_refresh_interval_seconds`
   - **Evidence:** Compare `defaults.py` lines 17-31 with new JSON files.
   - **TDD Analysis:** Tests comparing JSON config keys against expected defaults would catch naming inconsistencies.
   - **Recommendation:** Add tests that verify the JSON configuration field names are compatible with the expected configuration schema, or document that the JSON structure is intentionally different from `NODE_DEFAULTS`.

2. **No Validation of Required Fields**

   - **Location:** Both JSON configuration files
   - **Issue:** There are no tests verifying that required fields (`environment`, `device_id`, `device_type`, `feed_group`) are present and have valid values. The project has environment validation in `shared.config.validate_environment()`, but no tests exercise the JSON files against this validation.
   - **Recommendation:** Add tests that load the JSON files and validate the `environment` field using `validate_environment()`.

3. **No Tests for settings.toml Template**

   - **Location:** `/Users/chrishenry/source/poolio_rearchitect/config/nonprod/settings.toml.template`
   - **Issue:** The template file has no tests verifying its structure matches what the system expects. The template defines `AIO_KEY_NONPROD` but `defaults.py` and existing tests use `AIO_KEY_PROD`/`AIO_KEY_NONPROD` pattern.
   - **Recommendation:** Add a test that parses the template and verifies all expected environment variable names are present.

### Low Severity

1. **No Boundary Value Tests for Numeric Configuration**

   - **Location:** Both JSON files contain numeric values (e.g., `max_fill_duration_minutes: 5`, `watchdog_timeout_seconds: 120`)
   - **Issue:** No tests verify these values are within acceptable ranges. For example, `watchdog_timeout_seconds: 120` in the JSON differs from the default `watchdog_timeout: 30` in `NODE_DEFAULTS["valve_node"]`.
   - **Recommendation:** Add property-based or boundary tests for numeric configuration values.

2. **_config_fields Documentation Not Validated**

   - **Location:** `_config_fields` section in both JSON files
   - **Issue:** The documentation fields list configuration options but there is no test verifying that all documented fields actually exist in the configuration object.
   - **Recommendation:** Add a test that verifies `_config_fields` keys (excluding `_description`) match actual configuration keys.

### Recommendations

1. **Create JSON Schema Files**

   Add actual JSON schema files at `config/schemas/valve_node_config.json` and `config/schemas/display_node_config.json` with field definitions, types, and constraints. Then add tests that validate the configuration files against these schemas.

2. **Add Configuration Loading Tests**

   Extend `/Users/chrishenry/source/poolio_rearchitect/tests/unit/test_config.py` with tests that:

   ```python
   class TestConfigFileLoading:
       def test_valve_node_nonprod_config_is_valid_json(self):
           """Verify valve node nonprod config can be parsed."""

       def test_valve_node_nonprod_has_required_fields(self):
           """Verify required fields are present."""

       def test_valve_node_nonprod_environment_is_valid(self):
           """Verify environment field is valid per VALID_ENVIRONMENTS."""

       def test_config_field_names_match_expected_schema(self):
           """Verify config keys are recognized by the loader."""
   ```

3. **Add Integration Test for Deploy Workflow**

   Add a test that simulates the deployment path lookup to verify configuration files are in the expected locations:

   ```python
   def test_nonprod_config_exists_at_expected_path(self):
       """Config files exist where deploy.py expects them."""
   ```

4. **Apply TDD Going Forward**

   Per Kent Beck's TDD principles, future configuration changes should follow red/green/refactor:
   - RED: Write a failing test for the expected configuration structure
   - GREEN: Create the configuration file to pass the test
   - REFACTOR: Clean up any duplication between config files

5. **Consider Parameterized Tests**

   Use pytest parameterization to test all configuration files with the same validation logic:

   ```python
   @pytest.mark.parametrize("config_file", [
       "config/nonprod/valve_node.json",
       "config/nonprod/display_node.json",
   ])
   def test_config_has_valid_structure(config_file):
       """All config files pass structural validation."""
   ```
