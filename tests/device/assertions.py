"""
CircuitPython-compatible assertion helpers for on-device testing.

These functions provide pytest-like assertions without pytest dependencies.
All functions raise AssertionError on failure with descriptive messages.
"""


class SkipTest(Exception):
    """Raised to skip a test with a reason."""

    def __init__(self, reason):
        self.reason = reason
        super().__init__(reason)


def assert_equal(actual, expected, msg=None):
    """Assert two values are equal.

    Args:
        actual: The actual value
        expected: The expected value
        msg: Optional custom message on failure
    """
    if actual != expected:
        if msg:
            raise AssertionError(msg)
        raise AssertionError(f"assert_equal failed: {repr(actual)} != {repr(expected)}")


def assert_not_equal(actual, expected, msg=None):
    """Assert two values are not equal.

    Args:
        actual: The actual value
        expected: The value that should not match
        msg: Optional custom message on failure
    """
    if actual == expected:
        if msg:
            raise AssertionError(msg)
        raise AssertionError(f"assert_not_equal failed: {repr(actual)} == {repr(expected)}")


def assert_true(value, msg=None):
    """Assert value is truthy.

    Args:
        value: The value to check
        msg: Optional custom message on failure
    """
    if not value:
        if msg:
            raise AssertionError(msg)
        raise AssertionError(f"assert_true failed: {repr(value)} is not truthy")


def assert_false(value, msg=None):
    """Assert value is falsy.

    Args:
        value: The value to check
        msg: Optional custom message on failure
    """
    if value:
        if msg:
            raise AssertionError(msg)
        raise AssertionError(f"assert_false failed: {repr(value)} is not falsy")


def assert_is_none(value, msg=None):
    """Assert value is None.

    Args:
        value: The value to check
        msg: Optional custom message on failure
    """
    if value is not None:
        if msg:
            raise AssertionError(msg)
        raise AssertionError(f"assert_is_none failed: {repr(value)} is not None")


def assert_is_not_none(value, msg=None):
    """Assert value is not None.

    Args:
        value: The value to check
        msg: Optional custom message on failure
    """
    if value is None:
        if msg:
            raise AssertionError(msg)
        raise AssertionError("assert_is_not_none failed: value is None")


def assert_raises(exception_type, callable_obj, *args, **kwargs):
    """Assert that callable raises the expected exception.

    Args:
        exception_type: The expected exception type (or tuple of types)
        callable_obj: The callable to invoke
        *args: Positional arguments to pass to callable
        **kwargs: Keyword arguments to pass to callable

    Returns:
        The caught exception instance (for further inspection)
    """
    try:
        callable_obj(*args, **kwargs)
    except exception_type as e:
        return e
    except Exception as e:
        raise AssertionError(
            f"assert_raises failed: expected {exception_type.__name__}, got {type(e).__name__}"
        ) from None
    else:
        raise AssertionError(f"assert_raises failed: {exception_type.__name__} not raised")


def assert_almost_equal(actual, expected, places=7, msg=None):
    """Assert floats are equal within tolerance.

    Args:
        actual: The actual float value
        expected: The expected float value
        places: Decimal places for comparison (default 7)
        msg: Optional custom message on failure
    """
    tolerance = 10 ** (-places)
    diff = abs(actual - expected)
    if diff > tolerance:
        if msg:
            raise AssertionError(msg)
        raise AssertionError(
            f"assert_almost_equal failed: {actual} != {expected} within {places} places (diff={diff})"
        )


def assert_in(item, container, msg=None):
    """Assert item is in container.

    Args:
        item: The item to find
        container: The container to search
        msg: Optional custom message on failure
    """
    if item not in container:
        if msg:
            raise AssertionError(msg)
        raise AssertionError(f"assert_in failed: {repr(item)} not in {repr(container)}")


def assert_not_in(item, container, msg=None):
    """Assert item is not in container.

    Args:
        item: The item that should not be present
        container: The container to search
        msg: Optional custom message on failure
    """
    if item in container:
        if msg:
            raise AssertionError(msg)
        raise AssertionError(f"assert_not_in failed: {repr(item)} found in {repr(container)}")


def assert_is_instance(obj, class_or_tuple, msg=None):
    """Assert object is an instance of class(es).

    Args:
        obj: The object to check
        class_or_tuple: A class or tuple of classes
        msg: Optional custom message on failure
    """
    if not isinstance(obj, class_or_tuple):
        if msg:
            raise AssertionError(msg)
        raise AssertionError(
            f"assert_is_instance failed: {type(obj).__name__} is not instance of {class_or_tuple}"
        )


def assert_greater(a, b, msg=None):
    """Assert a > b.

    Args:
        a: First value
        b: Second value
        msg: Optional custom message on failure
    """
    if not a > b:
        if msg:
            raise AssertionError(msg)
        raise AssertionError(f"assert_greater failed: {repr(a)} is not greater than {repr(b)}")


def assert_less(a, b, msg=None):
    """Assert a < b.

    Args:
        a: First value
        b: Second value
        msg: Optional custom message on failure
    """
    if not a < b:
        if msg:
            raise AssertionError(msg)
        raise AssertionError(f"assert_less failed: {repr(a)} is not less than {repr(b)}")


def skip(reason):
    """Skip the current test with a reason.

    Args:
        reason: Why the test is being skipped

    Raises:
        SkipTest: Always raised to signal skip
    """
    raise SkipTest(reason)
