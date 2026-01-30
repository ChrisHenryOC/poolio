---
allowed-tools: Bash(python3:*),Bash(ls:*),Bash(rsync:*),Bash(kill:*),Bash(lsof:*)
description: Run tests on CircuitPython device via serial monitoring
---

Run on-device tests for CircuitPython: $ARGUMENTS

## Overview

This command deploys test code to a connected CircuitPython device (ESP32-S3),
runs the tests, and monitors the serial output to report results.

## Usage

- `/run-device-tests` - Run all device tests
- `/run-device-tests messages` - Run shared/messages tests only
- `/run-device-tests -k temperature` - Run tests matching pattern

## Workflow

### 1. Pre-flight Checks

Run these checks before proceeding:

```bash
# Check if CIRCUITPY volume is mounted
ls /Volumes/CIRCUITPY 2>/dev/null && echo "CIRCUITPY mounted" || echo "ERROR: CIRCUITPY not mounted"

# Check for serial port
ls /dev/cu.usbmodem* 2>/dev/null || echo "ERROR: No serial port found"

# Check if serial port is busy
lsof /dev/cu.usbmodem* 2>/dev/null && echo "WARNING: Serial port in use" || echo "Serial port available"
```

If the serial port is busy, kill the process holding it:
```bash
lsof /dev/cu.usbmodem* | awk 'NR>1 {print $2}' | xargs kill 2>/dev/null
```

### 2. Deploy Code to Device

Copy the source code and tests to the CIRCUITPY volume:

```bash
# Create lib directory structure
mkdir -p /Volumes/CIRCUITPY/lib/shared/messages
mkdir -p /Volumes/CIRCUITPY/lib/tests/device/shared

# Copy shared library
rsync -av --delete src/shared/ /Volumes/CIRCUITPY/lib/shared/

# Copy device tests
rsync -av --delete tests/device/ /Volumes/CIRCUITPY/lib/tests/device/
```

### 3. Create Test Entry Point

Write a `code.py` that runs the tests on boot:

```python
# Write to /Volumes/CIRCUITPY/code.py
import sys
sys.path.insert(0, '/lib')

from tests.device import runner

# Determine what to run based on arguments
# Default: run all tests
exit_code = runner.run_all()
```

If a specific module was requested (e.g., `messages`), modify to:
```python
exit_code = runner.run_module_by_name("shared.test_messages")
```

If a pattern was requested (e.g., `-k temperature`), modify to:
```python
exit_code = runner.run_pattern("temperature")
```

### 4. Monitor Serial Output

Use Python with pyserial to monitor the serial output. The test framework outputs
structured results that can be parsed.

```python
import serial
import time

SERIAL_PORT = "/dev/cu.usbmodem..."  # Use detected port
BAUD_RATE = 115200
TIMEOUT_SECONDS = 60

ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)

# Send Ctrl+D to soft-reset the board
ser.write(b'\x04')

# Collect output until test run completes or timeout
output_lines = []
end_time = time.time() + TIMEOUT_SECONDS

while time.time() < end_time:
    if ser.in_waiting:
        line = ser.readline().decode('utf-8', errors='replace').strip()
        if line:
            print(line)
            output_lines.append(line)
            if "=== TEST RUN END ===" in line:
                # Collect summary lines
                for _ in range(5):
                    time.sleep(0.1)
                    if ser.in_waiting:
                        line = ser.readline().decode('utf-8', errors='replace').strip()
                        if line:
                            print(line)
                            output_lines.append(line)
                break

ser.close()
```

### 5. Parse and Report Results

Parse the output to extract test results:

**Expected Output Format:**
```
=== TEST RUN START ===
BOARD: adafruit_feather_esp32s3
CIRCUITPYTHON: 9.2.0
MEMORY_START: 142384 bytes free
---
MODULE: shared.messages
[PASS] test_water_level_creation (12ms)
[FAIL] test_invalid_unit: ValueError expected but not raised
[ERROR] test_memory_heavy: MemoryError - not enough memory
[SKIP] test_large_payload: marked skip - memory constrained
---
=== TEST RUN END ===
SUMMARY: 25 passed, 1 failed, 1 error, 1 skipped
DURATION: 3.2 seconds
MEMORY_END: 138240 bytes free
MEMORY_DELTA: -4144 bytes (potential leak)
```

**Parse Results:**
- Count `[PASS]`, `[FAIL]`, `[ERROR]`, `[SKIP]` lines
- Extract SUMMARY line for verification
- Report memory delta if significant (>1KB loss)

### 6. Report Summary

Display a formatted summary:

```
## Device Test Results

| Status | Count |
|--------|-------|
| Passed | 25    |
| Failed | 1     |
| Errors | 1     |
| Skipped| 1     |

**Duration:** 3.2 seconds
**Memory:** 138,240 bytes free (-4,144 bytes)

### Failed Tests
- `test_invalid_unit`: ValueError expected but not raised

### Errors
- `test_memory_heavy`: MemoryError - not enough memory
```

## Error Handling

- **CIRCUITPY not mounted**: Ask user to connect the board and ensure it's in CircuitPython mode
- **Serial port busy**: Kill the process holding it (after user confirmation)
- **Timeout**: Report partial results and note the timeout
- **Import errors**: Usually means a dependency is missing from the device

## Notes

- The board soft-resets when receiving Ctrl+D (0x04) on serial
- CircuitPython auto-runs `code.py` after reset
- Tests output to serial at 115200 baud
- Memory is limited; tests should be memory-conscious
