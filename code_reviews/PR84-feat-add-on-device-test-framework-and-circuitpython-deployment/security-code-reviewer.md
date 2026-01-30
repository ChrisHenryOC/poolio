# Security Code Review for PR #84

## Summary

This PR introduces a CircuitPython deployment system and on-device test framework. The code is primarily developer-focused tooling for deploying to locally-connected hardware. The main security considerations involve path traversal in file operations, unsafe download practices without integrity verification, and a command file that documents shell commands for process termination. Overall risk is low given the local development context, but several improvements would harden the code.

## Findings

### High

**Zip Extraction Without Path Validation (CWE-22: Path Traversal)** - `circuitpython/deploy.py:88-89`

The `zipfile.extractall()` call extracts files without validating member paths. A malicious zip file from a compromised GitHub release could contain entries with path traversal sequences (e.g., `../../etc/cron.d/malicious`) that write files outside the intended extraction directory.

```python
with zipfile.ZipFile(zip_path, "r") as zf:
    zf.extractall(bundle_dir)
```

Recommendation: Validate each zip member's path before extraction to ensure it stays within the target directory:

```python
for member in zf.namelist():
    member_path = (bundle_dir / member).resolve()
    if not str(member_path).startswith(str(bundle_dir.resolve())):
        raise ValueError(f"Zip member escapes target directory: {member}")
```

**No Integrity Verification for Downloaded Bundle (CWE-494: Download Without Integrity Check)** - `circuitpython/deploy.py:79-80`

The bundle is downloaded over HTTPS but without verifying a checksum or signature. If the Adafruit GitHub release is compromised or a MITM attack occurs (e.g., via corporate proxy or compromised CA), malicious code could be deployed to devices.

```python
urllib.request.urlretrieve(url, zip_path)
```

Recommendation: Add SHA256 checksum verification. Adafruit publishes checksums for their releases. Store the expected hash in the code and verify after download.

### Medium

**User-Controlled Device Path Without Validation (CWE-22: Path Traversal)** - `circuitpython/deploy.py:299-303`

The `--device` argument is used directly to construct paths for file operations. While the existence check provides some protection, a malicious actor with access to CLI arguments could potentially target arbitrary writable directories.

```python
device_path = Path(args.device) if args.device else find_device()
if not device_path or not device_path.exists():
    ...
```

Recommendation: Validate that the device path looks like a legitimate CIRCUITPY mount (contains expected files like `boot_out.txt`) before writing to it. This also prevents accidental deployment to the wrong location.

**Target Name Used in Path Construction Without Sanitization** - `circuitpython/deploy.py:108`

The `--target` argument is used to construct a file path without validation:

```python
target_file = REQUIREMENTS_DIR / f"{target}.txt"
```

While argparse limits direct path injection and the file must exist, a target like `../../../etc/passwd` would attempt to read an arbitrary file. The existing logic only reads existing files and ignores invalid targets, reducing actual risk.

Recommendation: Validate target names against an allowlist of expected values (e.g., `pool-node`, `valve-node`, `display-node`, `test`).

**Unsafe Process Termination Pattern in Documentation** - `.claude/commands/run-device-tests.md:44-45`

The command documentation includes shell patterns that could kill unintended processes if misused:

```bash
lsof /dev/cu.usbmodem* | awk 'NR>1 {print $2}' | xargs kill 2>/dev/null
```

While this is documentation rather than code, and is guarded by "after user confirmation", the pattern pipes external command output to `kill` without validation. A race condition or glob mismatch could target wrong processes.

Recommendation: Document a safer pattern that validates the process name before killing, or use specific PID handling rather than shell pipelines.

### Low

**Serial Port Glob Pattern Could Match Unexpected Devices** - `scripts/serial_monitor.py:22-26`

The glob patterns `/dev/cu.usbmodem*` and `/dev/ttyACM*` could potentially match non-CircuitPython devices, though the impact is limited to reading serial data.

**Broad Exception Handling Hides Errors** - `circuitpython/deploy.py:81`

The bare `except Exception as e:` catches all exceptions during download, which could mask security-relevant errors (e.g., SSL certificate validation failures).

```python
except Exception as e:
    print(f"ERROR: Failed to download bundle: {e}")
```

Recommendation: Catch more specific exceptions (`urllib.error.URLError`, `ssl.SSLError`) and handle them differently, potentially refusing to continue on SSL errors.

## Security Considerations - Not Findings

The following were evaluated but are not security issues in this context:

1. **Serial port communication**: The serial monitor reads/writes to locally-connected hardware. This is the intended use case for embedded development and does not present a remote attack vector.

2. **File operations to CIRCUITPY volume**: Writing to a removable USB volume is the explicit purpose of the deployment tool. The device path auto-detection uses known safe patterns.

3. **No authentication for serial reset**: The `Ctrl+D` reset sent over serial is a standard CircuitPython debugging feature. Physical access to the device is already required.

4. **Requirements files parsed without validation**: While arbitrary text could be placed in requirements files, they only specify library names to look up in the bundle directory. No injection is possible since the names are used for path lookup, not execution.
