# Documentation Accuracy Review: PR #98

## Summary

This PR adds environment-based deployment support to the CircuitPython deploy script, with a new comprehensive deployment guide. The inline documentation in `deploy.py` is accurate and complete. However, the PR does not update existing documentation in `README.md` or `CLAUDE.md` that still shows outdated examples without the `--env` flag, and the new deployment guide contains a broken "See Also" link.

## Findings

### High Severity

**H1: Outdated deployment examples in README.md**

File: `/Users/chrishenry/source/poolio_rearchitect/README.md` (lines 77-79)

The README still shows the old deployment syntax without the `--env` flag:

```python
python circuitpython/deploy.py --target pool-node --source
python circuitpython/deploy.py --target valve-node --source
python circuitpython/deploy.py --target display-node --source
```

This will cause confusion since the PR changes the primary deployment workflow to include environment specification. Users following README instructions will miss deploying environment-specific `config.json` files.

**Recommendation:** Update README examples to include `--env` flag, e.g.:
```bash
python circuitpython/deploy.py --target valve-node --env nonprod --source
```

---

**H2: Outdated deployment examples in CLAUDE.md**

File: `/Users/chrishenry/source/poolio_rearchitect/CLAUDE.md` (lines 149-151)

CLAUDE.md contains the same outdated examples:

```python
python circuitpython/deploy.py --target pool-node --source
python circuitpython/deploy.py --target valve-node --source
python circuitpython/deploy.py --target display-node --source
```

As the primary development guidance document, this must be updated to reflect the new deployment workflow.

**Recommendation:** Update to show environment-based deployment as the standard approach.

---

### Medium Severity

**M1: Broken link in "See Also" section**

File: `/Users/chrishenry/source/poolio_rearchitect/docs/deployment/circuitpy-deployment.md` (line 189)

The link `[Adafruit IO Setup](../adafruit-io-setup.md)` references a file that does not exist at the specified path. The actual file is at `docs/deployment/adafruit-io-nonprod-setup.md`.

```markdown
- [Adafruit IO Setup](../adafruit-io-setup.md) - Creating feeds
```

**Recommendation:** Update the link to:
```markdown
- [Adafruit IO Setup](./adafruit-io-nonprod-setup.md) - Creating feeds
```

---

**M2: Inconsistency between architecture.md and actual implementation**

File: `/Users/chrishenry/source/poolio_rearchitect/docs/architecture.md` (lines 2128, 2183, 2197-2207)

The architecture.md deployment section documents:
- A different deploy script: `scripts/deploy_circuitpy.sh` (bash script)
- A different config path structure: `config/<env>/<node_type>.json`

The actual implementation uses:
- `circuitpython/deploy.py` (Python script)
- Config path: `circuitpython/configs/<target>/<environment>/config.json`

This inconsistency may confuse developers referencing architecture documentation.

**Recommendation:** Update architecture.md Section 13 (Deployment) to reflect the actual Python-based deployment script and config structure, or add a note that the bash script is deprecated/conceptual.

---

### Low Severity

**L1: Missing pool-node config files**

While the PR adds config files for `valve-node` and `display-node`, there are no corresponding `pool-node` config files, though `pool-node` is listed as a valid target in the argument help:

```python
help="Deployment target (pool-node, valve-node, display-node, test)"
```

The deployment will silently skip config deployment for pool-node with `--env`:
```
WARNING: Config not found: circuitpython/configs/pool-node/nonprod/config.json
Skipping config deployment.
```

**Recommendation:** Either add pool-node config files or document that pool-node uses C++ and does not support `--env` flag (which aligns with architecture.md stating Pool Node uses C++).

---

**L2: Documentation could clarify optional nature of --env flag**

File: `/Users/chrishenry/source/poolio_rearchitect/docs/deployment/circuitpy-deployment.md` (line 26)

The documentation shows `--env` in examples but does not explicitly note that it is optional. The script allows deployment without `--env`:
```bash
# Libraries only (no source or config)
python circuitpython/deploy.py --target valve-node
```

The arguments table could note "(optional)" for the `--env` argument to clarify this is not required for library-only deployments.

---

**L3: Example config in documentation has different field names than actual config**

File: `/Users/chrishenry/source/poolio_rearchitect/docs/architecture.md` (lines 2209-2221)

The architecture.md example uses camelCase field names (`deviceId`, `feedGroup`, `valveStartTime`), while the actual config files in the PR use snake_case (`device_id`, `feed_group`):

Architecture.md example:
```json
{
  "deviceId": "valve-node-001",
  "feedGroup": "poolio-nonprod"
}
```

Actual config (from PR):
```json
{
  "device_id": "valve-node-dev",
  "feed_group": "poolio-nonprod"
}
```

**Recommendation:** Standardize naming convention across documentation and implementation.

---

## Summary Table

| ID | Severity | File | Issue |
|----|----------|------|-------|
| H1 | High | README.md:77-79 | Outdated deployment examples without --env |
| H2 | High | CLAUDE.md:149-151 | Outdated deployment examples without --env |
| M1 | Medium | circuitpy-deployment.md:189 | Broken "See Also" link |
| M2 | Medium | architecture.md:2128 | Inconsistent deploy script path and config structure |
| L1 | Low | circuitpython/configs/ | Missing pool-node config files |
| L2 | Low | circuitpy-deployment.md:26 | --env flag optionality not clarified |
| L3 | Low | architecture.md:2209 | camelCase vs snake_case field name inconsistency |
