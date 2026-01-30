#!/usr/bin/env python3
"""
Serial monitor for CircuitPython device testing.

Usage:
    python scripts/serial_monitor.py                    # Auto-detect port, monitor for 60s
    python scripts/serial_monitor.py --timeout 120     # Monitor for 120 seconds
    python scripts/serial_monitor.py --port /dev/...   # Specify port
    python scripts/serial_monitor.py --reset           # Send Ctrl+D to reset first
"""

import argparse
import glob
import sys
import time

import serial


def find_serial_port():
    """Auto-detect CircuitPython serial port."""
    patterns = [
        "/dev/cu.usbmodem*",  # macOS
        "/dev/ttyACM*",       # Linux
    ]
    for pattern in patterns:
        ports = glob.glob(pattern)
        if ports:
            return ports[0]
    return None


def monitor_serial(port, timeout_seconds=60, reset=False):
    """Monitor serial port and print output."""
    print(f"Connecting to {port}...")

    try:
        ser = serial.Serial(port, 115200, timeout=1)
    except serial.SerialException as e:
        print(f"ERROR: Could not open serial port: {e}")
        return 1

    time.sleep(0.3)

    if reset:
        print("Sending Ctrl+D to reset...")
        ser.write(b'\x04')
        time.sleep(0.5)

    print("Monitoring serial output...")
    print("=" * 60)

    end_time = time.time() + timeout_seconds
    test_complete = False

    while time.time() < end_time:
        if ser.in_waiting:
            line = ser.readline().decode('utf-8', errors='replace').strip()
            if line:
                # Filter out terminal escape sequences
                if not line.startswith(']0;'):
                    print(line)
                if '=== TEST RUN END ===' in line:
                    test_complete = True
                    # Collect remaining summary lines
                    for _ in range(10):
                        time.sleep(0.1)
                        if ser.in_waiting:
                            line = ser.readline().decode('utf-8', errors='replace').strip()
                            if line and not line.startswith(']0;'):
                                print(line)
                    break
        time.sleep(0.05)

    print("=" * 60)
    ser.close()

    if test_complete:
        print("Test run completed successfully")
        return 0
    else:
        print("Test run may not have completed (timeout or no test output)")
        return 1


def main():
    parser = argparse.ArgumentParser(description="Monitor CircuitPython serial output")
    parser.add_argument("--port", "-p", help="Serial port (auto-detected if not specified)")
    parser.add_argument("--timeout", "-t", type=int, default=60, help="Timeout in seconds (default: 60)")
    parser.add_argument("--reset", "-r", action="store_true", help="Send Ctrl+D to reset board first")

    args = parser.parse_args()

    port = args.port or find_serial_port()
    if not port:
        print("ERROR: No serial port found. Connect a CircuitPython device or specify --port")
        return 1

    return monitor_serial(port, args.timeout, args.reset)


if __name__ == "__main__":
    sys.exit(main())
