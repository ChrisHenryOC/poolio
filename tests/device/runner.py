"""
Minimal test runner for CircuitPython on-device testing.

This module provides test discovery and execution with structured
serial output for monitoring by Claude Code or other tools.

Usage on device:
    import tests.device.runner as runner
    runner.run_all()  # Run all discovered tests
    runner.run_module_by_name("shared.test_messages")  # Run specific module
    runner.run_pattern("temperature")  # Run tests matching pattern
"""

import gc
import sys
import time

from .assertions import SkipTest

# Test result constants
PASS = "PASS"
FAIL = "FAIL"
ERROR = "ERROR"
SKIP = "SKIP"


class TestResult:
    """Stores result of a single test."""

    def __init__(self, name, status, duration_ms, message=None):
        self.name = name
        self.status = status
        self.duration_ms = duration_ms
        self.message = message


class TestRunner:
    """Discovers and runs tests with structured output."""

    def __init__(self):
        self.results = []
        self.memory_start = 0
        self.memory_end = 0
        self.start_time = 0

    def _get_board_info(self):
        """Get board and CircuitPython version info."""
        board_name = "Unknown"
        cp_version = "Unknown"

        try:
            import board

            board_name = board.board_id
        except (ImportError, AttributeError):
            pass

        try:
            cp_version = sys.implementation.version
            cp_version = f"{cp_version[0]}.{cp_version[1]}.{cp_version[2]}"
        except (AttributeError, IndexError):
            pass

        return board_name, cp_version

    def _collect_garbage(self):
        """Run garbage collection and return free memory."""
        gc.collect()
        return gc.mem_free()

    def _discover_tests(self, module):
        """Discover test functions in a module.

        Args:
            module: The module object to search

        Returns:
            List of (name, function) tuples
        """
        tests = []
        for name in dir(module):
            if name.startswith("test_"):
                obj = getattr(module, name)
                if callable(obj):
                    tests.append((name, obj))
        # Sort by name for consistent ordering
        tests.sort(key=lambda x: x[0])
        return tests

    def _run_single_test(self, name, test_func):
        """Run a single test function and record result.

        Args:
            name: Test function name
            test_func: The test function to call

        Returns:
            TestResult instance
        """
        start = time.monotonic()

        try:
            # Check for setup function (CircuitPython functions may lack __module__)
            module_name = getattr(test_func, "__module__", None)
            module = sys.modules.get(module_name) if module_name else None
            if module and hasattr(module, "setup"):
                module.setup()

            # Run the test
            test_func()

            # Check for teardown function
            if module and hasattr(module, "teardown"):
                module.teardown()

            duration_ms = int((time.monotonic() - start) * 1000)
            return TestResult(name, PASS, duration_ms)

        except SkipTest as e:
            duration_ms = int((time.monotonic() - start) * 1000)
            return TestResult(name, SKIP, duration_ms, str(e))

        except AssertionError as e:
            duration_ms = int((time.monotonic() - start) * 1000)
            return TestResult(name, FAIL, duration_ms, str(e))

        except Exception as e:
            duration_ms = int((time.monotonic() - start) * 1000)
            error_msg = f"{type(e).__name__}: {str(e)}"
            return TestResult(name, ERROR, duration_ms, error_msg)

    def _print_result(self, name, result):
        """Print a single test result.

        Args:
            name: Test function name
            result: TestResult instance
        """
        if result.status == PASS:
            print(f"[{PASS}] {name} ({result.duration_ms}ms)")
        elif result.status == SKIP:
            print(f"[{SKIP}] {name}: {result.message}")
        else:
            print(f"[{result.status}] {name}: {result.message}")

    def run_module(self, module, module_name=None):
        """Run all tests in a module.

        Args:
            module: The module object containing tests
            module_name: Display name for the module (optional)
        """
        if module_name is None:
            module_name = getattr(module, "__name__", "unknown")

        tests = self._discover_tests(module)
        if not tests:
            return

        print("---")
        print(f"MODULE: {module_name}")

        for name, test_func in tests:
            # Collect garbage before each test for consistent memory
            self._collect_garbage()

            result = self._run_single_test(name, test_func)
            self.results.append(result)
            self._print_result(name, result)

    def run_modules(self, modules):
        """Run tests from multiple modules.

        Args:
            modules: List of (module_object, module_name) tuples
        """
        for module, name in modules:
            self.run_module(module, name)

    def print_header(self):
        """Print test run header with system info."""
        board_name, cp_version = self._get_board_info()
        self.memory_start = self._collect_garbage()
        self.start_time = time.monotonic()

        print("=== TEST RUN START ===")
        print(f"BOARD: {board_name}")
        print(f"CIRCUITPYTHON: {cp_version}")
        print(f"MEMORY_START: {self.memory_start} bytes free")

    def print_summary(self):
        """Print test run summary."""
        self.memory_end = self._collect_garbage()
        duration = time.monotonic() - self.start_time
        memory_delta = self.memory_end - self.memory_start

        # Count results
        passed = sum(1 for r in self.results if r.status == PASS)
        failed = sum(1 for r in self.results if r.status == FAIL)
        errors = sum(1 for r in self.results if r.status == ERROR)
        skipped = sum(1 for r in self.results if r.status == SKIP)

        print("---")
        print("=== TEST RUN END ===")
        print(f"SUMMARY: {passed} passed, {failed} failed, {errors} error, {skipped} skipped")
        print(f"DURATION: {duration:.1f} seconds")
        print(f"MEMORY_END: {self.memory_end} bytes free")

        if memory_delta < 0:
            print(f"MEMORY_DELTA: {memory_delta} bytes (potential leak)")
        else:
            print(f"MEMORY_DELTA: +{memory_delta} bytes")

    def get_exit_code(self):
        """Get exit code based on results (0=success, 1=failure)."""
        for r in self.results:
            if r.status in (FAIL, ERROR):
                return 1
        return 0


# Convenience functions for common use cases


def _get_test_modules():
    """Import all known test modules.

    Returns:
        List of (module_object, module_name) tuples.
        Add new test modules here as they are created.
    """
    modules = []

    try:
        from .shared import test_messages

        modules.append((test_messages, "shared.messages"))
    except ImportError:
        pass

    return modules


def run_all():
    """Run all discovered device tests.

    This function imports and runs tests from known test modules.
    """
    runner = TestRunner()
    runner.print_header()

    modules = _get_test_modules()

    if modules:
        runner.run_modules(modules)
    else:
        print("---")
        print("WARNING: No test modules found")

    runner.print_summary()
    return runner.get_exit_code()


def run_module_by_name(module_name):
    """Run tests from a specific module by name.

    Args:
        module_name: Dot-separated module path (e.g., "shared.test_messages")

    Returns:
        Exit code (0=success, 1=failure)
    """
    runner = TestRunner()
    runner.print_header()

    try:
        # Convert module name to import path
        import_path = "tests.device." + module_name.replace("/", ".")
        module = __import__(import_path, fromlist=[""])
        runner.run_module(module, module_name)
    except ImportError as e:
        print("---")
        print(f"ERROR: Could not import {module_name}: {e}")

    runner.print_summary()
    return runner.get_exit_code()


def run_pattern(pattern):
    """Run tests matching a name pattern.

    Args:
        pattern: Substring to match in test names

    Returns:
        Exit code (0=success, 1=failure)
    """
    runner = TestRunner()
    runner.print_header()

    modules = _get_test_modules()

    # Filter and run matching tests
    for module, module_name in modules:
        tests = runner._discover_tests(module)
        matching = [(n, f) for n, f in tests if pattern.lower() in n.lower()]

        if matching:
            print("---")
            print(f"MODULE: {module_name} (filtered)")

            for name, test_func in matching:
                runner._collect_garbage()
                result = runner._run_single_test(name, test_func)
                runner.results.append(result)
                runner._print_result(name, result)

    if not runner.results:
        print("---")
        print(f"WARNING: No tests matched pattern '{pattern}'")

    runner.print_summary()
    return runner.get_exit_code()
