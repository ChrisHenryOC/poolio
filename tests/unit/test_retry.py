# Tests for sensor retry utilities
# Tests the retry_with_backoff function

from unittest.mock import Mock, call, patch

import pytest


class TestRetryWithBackoff:
    """Tests for retry_with_backoff function."""

    def test_success_on_first_attempt(self):
        """Function succeeds on first call, no retries needed."""
        from src.shared.sensors.retry import retry_with_backoff

        func = Mock(return_value="success")
        result = retry_with_backoff(func)

        assert result == "success"
        assert func.call_count == 1

    def test_success_after_one_retry(self):
        """Function fails once then succeeds."""
        from src.shared.sensors.retry import retry_with_backoff

        func = Mock(side_effect=[ValueError("fail"), "success"])
        result = retry_with_backoff(func, max_retries=3)

        assert result == "success"
        assert func.call_count == 2

    def test_success_after_max_retries(self):
        """Function fails max_retries times then succeeds."""
        from src.shared.sensors.retry import retry_with_backoff

        func = Mock(
            side_effect=[
                ValueError("fail1"),
                ValueError("fail2"),
                ValueError("fail3"),
                "success",
            ]
        )
        result = retry_with_backoff(func, max_retries=3)

        assert result == "success"
        assert func.call_count == 4  # initial + 3 retries

    def test_all_retries_exhausted_raises_exception(self):
        """All retries fail, original exception is raised."""
        from src.shared.sensors.retry import retry_with_backoff

        func = Mock(side_effect=ValueError("persistent failure"))

        with pytest.raises(ValueError, match="persistent failure"):
            retry_with_backoff(func, max_retries=3)

        assert func.call_count == 4  # initial + 3 retries

    def test_delay_timing_with_default_parameters(self):
        """Verify exponential backoff delays: 0.1, 0.2, 0.4."""
        from src.shared.sensors.retry import retry_with_backoff

        func = Mock(side_effect=[ValueError(), ValueError(), ValueError(), "success"])

        with patch("src.shared.sensors.retry.time.sleep") as mock_sleep:
            retry_with_backoff(func, max_retries=3, base_delay=0.1)

        # Delays: 0.1s after 1st fail, 0.2s after 2nd, 0.4s after 3rd
        assert mock_sleep.call_count == 3
        calls = mock_sleep.call_args_list
        assert calls[0] == call(0.1)
        assert calls[1] == call(0.2)
        assert calls[2] == call(0.4)

    def test_delay_pattern_100_200_400_800_1600_2000(self):
        """Verify full delay pattern: 100ms, 200ms, 400ms, 800ms, 1600ms, 2000ms."""
        from src.shared.sensors.retry import retry_with_backoff

        func = Mock(
            side_effect=[
                ValueError(),
                ValueError(),
                ValueError(),
                ValueError(),
                ValueError(),
                ValueError(),
                "success",
            ]
        )

        with patch("src.shared.sensors.retry.time.sleep") as mock_sleep:
            retry_with_backoff(func, max_retries=6, base_delay=0.1, max_delay=2.0)

        # Full pattern with max_delay=2.0 capping
        expected_delays = [0.1, 0.2, 0.4, 0.8, 1.6, 2.0]
        calls = mock_sleep.call_args_list
        assert len(calls) == 6
        for i, expected in enumerate(expected_delays):
            assert calls[i] == call(expected)

    def test_max_delay_capping(self):
        """Delays are capped at max_delay."""
        from src.shared.sensors.retry import retry_with_backoff

        func = Mock(
            side_effect=[
                ValueError(),
                ValueError(),
                ValueError(),
                ValueError(),
                ValueError(),
                "success",
            ]
        )

        with patch("src.shared.sensors.retry.time.sleep") as mock_sleep:
            # With base_delay=1.0, delays would be 1, 2, 4, 8, 16...
            # But max_delay=2.0 caps them
            retry_with_backoff(func, max_retries=5, base_delay=1.0, max_delay=2.0)

        calls = mock_sleep.call_args_list
        assert len(calls) == 5
        # First delay is 1.0, then 2.0 (capped for all subsequent)
        assert calls[0] == call(1.0)
        assert calls[1] == call(2.0)
        assert calls[2] == call(2.0)
        assert calls[3] == call(2.0)
        assert calls[4] == call(2.0)

    def test_specific_exception_filtering(self):
        """Only specified exception types trigger retry."""
        from src.shared.sensors.retry import retry_with_backoff

        func = Mock(side_effect=[ValueError("retry this"), "success"])

        # Only catch ValueError
        result = retry_with_backoff(func, max_retries=3, exceptions=(ValueError,))
        assert result == "success"
        assert func.call_count == 2

    def test_non_matching_exception_propagates(self):
        """Exceptions not in the filter list propagate immediately."""
        from src.shared.sensors.retry import retry_with_backoff

        func = Mock(side_effect=TypeError("not caught"))

        # Only catching ValueError, so TypeError should propagate
        with pytest.raises(TypeError, match="not caught"):
            retry_with_backoff(func, max_retries=3, exceptions=(ValueError,))

        assert func.call_count == 1  # No retry attempted

    def test_multiple_exception_types(self):
        """Multiple exception types can be specified."""
        from src.shared.sensors.retry import retry_with_backoff

        func = Mock(side_effect=[ValueError("v"), TypeError("t"), "success"])

        result = retry_with_backoff(func, max_retries=3, exceptions=(ValueError, TypeError))
        assert result == "success"
        assert func.call_count == 3

    def test_logging_on_retry(self):
        """Logger is called on each retry."""
        from src.shared.sensors.retry import retry_with_backoff

        func = Mock(side_effect=[ValueError("fail"), "success"])
        logger = Mock()

        with patch("src.shared.sensors.retry.time.sleep"):
            result = retry_with_backoff(func, max_retries=3, logger=logger)

        assert result == "success"
        # Should log the retry attempt
        assert logger.debug.call_count >= 1

    def test_logging_on_all_retries_exhausted(self):
        """Logger warns when all retries are exhausted."""
        from src.shared.sensors.retry import retry_with_backoff

        func = Mock(side_effect=ValueError("fail"))
        logger = Mock()

        with patch("src.shared.sensors.retry.time.sleep"):
            with pytest.raises(ValueError):
                retry_with_backoff(func, max_retries=2, logger=logger)

        # Should log warning about exhausted retries
        assert logger.warning.call_count >= 1

    def test_zero_max_retries_means_single_attempt(self):
        """max_retries=0 means only the initial attempt, no retries."""
        from src.shared.sensors.retry import retry_with_backoff

        func = Mock(side_effect=ValueError("fail"))

        with pytest.raises(ValueError):
            retry_with_backoff(func, max_retries=0)

        assert func.call_count == 1

    def test_return_value_preserved(self):
        """Return value from function is passed through."""
        from src.shared.sensors.retry import retry_with_backoff

        func = Mock(return_value={"key": "value", "count": 42})
        result = retry_with_backoff(func)

        assert result == {"key": "value", "count": 42}

    def test_function_with_no_return_value(self):
        """Functions that return None work correctly."""
        from src.shared.sensors.retry import retry_with_backoff

        func = Mock(return_value=None)
        result = retry_with_backoff(func)

        assert result is None
        assert func.call_count == 1


class TestRetryWithBackoffEdgeCases:
    """Edge case tests for retry_with_backoff."""

    def test_exception_subclass_is_caught(self):
        """Subclasses of specified exceptions are caught."""
        from src.shared.sensors.retry import retry_with_backoff

        class CustomError(ValueError):
            pass

        func = Mock(side_effect=[CustomError("custom"), "success"])

        # ValueError should catch CustomError (its subclass)
        result = retry_with_backoff(func, max_retries=3, exceptions=(ValueError,))
        assert result == "success"

    def test_base_exception_not_caught_by_default(self):
        """BaseException subclasses like KeyboardInterrupt propagate."""
        from src.shared.sensors.retry import retry_with_backoff

        func = Mock(side_effect=KeyboardInterrupt())

        with pytest.raises(KeyboardInterrupt):
            retry_with_backoff(func, max_retries=3)

        assert func.call_count == 1

    def test_system_exit_propagates(self):
        """SystemExit propagates immediately."""
        from src.shared.sensors.retry import retry_with_backoff

        func = Mock(side_effect=SystemExit(1))

        with pytest.raises(SystemExit):
            retry_with_backoff(func, max_retries=3)

        assert func.call_count == 1

    def test_no_delay_on_last_attempt_failure(self):
        """No sleep after the final failed attempt."""
        from src.shared.sensors.retry import retry_with_backoff

        func = Mock(side_effect=ValueError("always fails"))

        with patch("src.shared.sensors.retry.time.sleep") as mock_sleep:
            with pytest.raises(ValueError):
                retry_with_backoff(func, max_retries=2)

        # 3 attempts (initial + 2 retries), but only 2 sleeps
        # (no sleep after final failure)
        assert func.call_count == 3
        assert mock_sleep.call_count == 2
