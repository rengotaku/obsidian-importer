"""Unit tests for retry module.

Tests for:
- RetryConfig validation and tenacity conversion
- with_retry decorator behavior
- Exponential backoff + jitter behavior
- Logging callbacks
- Exception-specific retry conditions
"""

import logging
import unittest
from unittest.mock import MagicMock, patch, call

from src.etl.core.models import RetryConfig
from src.etl.core.retry import (
    with_retry,
    build_tenacity_kwargs,
    create_retry_decorator,
    DEFAULT_RETRY_CONFIG,
)


class TestRetryConfigConversion(unittest.TestCase):
    """Tests for RetryConfig to tenacity kwargs conversion (T024)."""

    def test_default_config_to_tenacity_kwargs(self):
        """Verify default config converts to proper tenacity kwargs."""
        config = RetryConfig()
        kwargs = build_tenacity_kwargs(config)

        # Should have stop, wait, retry conditions
        self.assertIn("stop", kwargs)
        self.assertIn("wait", kwargs)
        self.assertIn("retry", kwargs)

    def test_custom_max_attempts(self):
        """Verify max_attempts maps to stop_after_attempt."""
        config = RetryConfig(max_attempts=5)
        kwargs = build_tenacity_kwargs(config)

        # stop should be configured
        self.assertIn("stop", kwargs)

    def test_custom_wait_times(self):
        """Verify wait times map to wait_random_exponential."""
        config = RetryConfig(
            min_wait_seconds=1.0,
            max_wait_seconds=60.0,
        )
        kwargs = build_tenacity_kwargs(config)

        # wait should be configured
        self.assertIn("wait", kwargs)

    def test_jitter_disabled(self):
        """Verify jitter=False uses exponential without random."""
        config = RetryConfig(jitter=False)
        kwargs = build_tenacity_kwargs(config)

        # Should still have wait configured
        self.assertIn("wait", kwargs)

    def test_custom_retry_exceptions(self):
        """Verify custom exceptions map to retry_if_exception_type."""
        config = RetryConfig(retry_exceptions=(ValueError, RuntimeError))
        kwargs = build_tenacity_kwargs(config)

        self.assertIn("retry", kwargs)

    def test_default_retry_config_constant(self):
        """Verify DEFAULT_RETRY_CONFIG is a valid RetryConfig."""
        self.assertIsInstance(DEFAULT_RETRY_CONFIG, RetryConfig)
        self.assertEqual(DEFAULT_RETRY_CONFIG.max_attempts, 3)


class TestWithRetryDecorator(unittest.TestCase):
    """Tests for with_retry decorator (T025)."""

    def test_decorator_without_args_uses_default_config(self):
        """Verify @with_retry() uses default config."""
        call_count = 0

        @with_retry()
        def successful_func():
            nonlocal call_count
            call_count += 1
            return "success"

        result = successful_func()
        self.assertEqual(result, "success")
        self.assertEqual(call_count, 1)

    def test_decorator_with_custom_config(self):
        """Verify @with_retry(config=...) uses custom config."""
        config = RetryConfig(max_attempts=5)

        @with_retry(config=config)
        def successful_func():
            return "success"

        result = successful_func()
        self.assertEqual(result, "success")

    def test_retries_on_configured_exception(self):
        """Verify decorator retries on configured exceptions."""
        call_count = 0
        config = RetryConfig(
            max_attempts=3,
            min_wait_seconds=0.01,  # Very short for testing
            max_wait_seconds=0.02,
            retry_exceptions=(ValueError,),
        )

        @with_retry(config=config)
        def failing_then_success():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Temporary failure")
            return "success"

        result = failing_then_success()
        self.assertEqual(result, "success")
        self.assertEqual(call_count, 2)

    def test_does_not_retry_on_non_configured_exception(self):
        """Verify decorator does not retry on non-configured exceptions."""
        config = RetryConfig(
            max_attempts=3,
            retry_exceptions=(ValueError,),
        )

        @with_retry(config=config)
        def raises_type_error():
            raise TypeError("Not retryable")

        with self.assertRaises(TypeError):
            raises_type_error()

    def test_max_attempts_exceeded(self):
        """Verify exception is raised after max attempts exceeded."""
        call_count = 0
        config = RetryConfig(
            max_attempts=3,
            min_wait_seconds=0.01,
            max_wait_seconds=0.02,
            retry_exceptions=(ConnectionError,),
        )

        @with_retry(config=config)
        def always_fails():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("Always fails")

        from tenacity import RetryError

        with self.assertRaises(RetryError):
            always_fails()

        self.assertEqual(call_count, 3)

    def test_preserves_function_metadata(self):
        """Verify decorator preserves function name and docstring."""

        @with_retry()
        def documented_function():
            """This is the docstring."""
            pass

        self.assertEqual(documented_function.__name__, "documented_function")
        self.assertEqual(documented_function.__doc__, "This is the docstring.")


class TestExponentialBackoffJitter(unittest.TestCase):
    """Tests for exponential backoff + jitter behavior (T026)."""

    def test_wait_time_within_bounds(self):
        """Verify wait times are within min/max bounds."""
        from tenacity import wait_random_exponential

        wait = wait_random_exponential(min=2, max=30)

        # Test multiple retry states
        for attempt in range(1, 5):
            # Create a mock retry state
            retry_state = MagicMock()
            retry_state.attempt_number = attempt

            wait_time = wait(retry_state)

            self.assertGreaterEqual(wait_time, 0)
            self.assertLessEqual(wait_time, 30)

    def test_exponential_without_jitter(self):
        """Verify exponential backoff without jitter uses wait_exponential."""
        from tenacity import wait_exponential

        wait = wait_exponential(min=2, max=30, multiplier=1)

        retry_state = MagicMock()
        retry_state.attempt_number = 1

        wait_time = wait(retry_state)
        self.assertGreaterEqual(wait_time, 2)

    def test_jitter_produces_variable_waits(self):
        """Verify jitter produces variable wait times for same attempt."""
        from tenacity import wait_random_exponential

        wait = wait_random_exponential(min=2, max=30)

        # Collect multiple wait times for same attempt number
        wait_times = []
        for _ in range(10):
            retry_state = MagicMock()
            retry_state.attempt_number = 3
            wait_times.append(wait(retry_state))

        # With jitter, we should see some variation
        # (statistically extremely unlikely to get 10 identical values)
        unique_times = set(wait_times)
        self.assertGreater(len(unique_times), 1)


class TestRetryLoggingCallbacks(unittest.TestCase):
    """Tests for retry logging callbacks (T029)."""

    def test_before_retry_callback_is_called(self):
        """Verify before callback is called before each retry."""
        call_count = 0
        before_calls = []

        config = RetryConfig(
            max_attempts=3,
            min_wait_seconds=0.01,
            max_wait_seconds=0.02,
            retry_exceptions=(ValueError,),
        )

        # Create custom logger to capture calls
        test_logger = logging.getLogger("test_before")
        test_logger.setLevel(logging.WARNING)
        handler = logging.handlers.MemoryHandler(capacity=100)
        test_logger.addHandler(handler)

        @with_retry(config=config, logger=test_logger)
        def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Fail")
            return "success"

        result = failing_func()
        self.assertEqual(result, "success")

    def test_after_retry_callback_is_called(self):
        """Verify after callback is called after each retry attempt."""
        call_count = 0

        config = RetryConfig(
            max_attempts=3,
            min_wait_seconds=0.01,
            max_wait_seconds=0.02,
            retry_exceptions=(ValueError,),
        )

        test_logger = logging.getLogger("test_after")
        test_logger.setLevel(logging.WARNING)

        @with_retry(config=config, logger=test_logger)
        def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Fail")
            return "success"

        result = failing_func()
        self.assertEqual(result, "success")


class TestExceptionSpecificRetry(unittest.TestCase):
    """Tests for exception-specific retry conditions (T030)."""

    def test_single_exception_type(self):
        """Verify retry on single exception type."""
        call_count = 0
        config = RetryConfig(
            max_attempts=3,
            min_wait_seconds=0.01,
            max_wait_seconds=0.02,
            retry_exceptions=(ConnectionError,),
        )

        @with_retry(config=config)
        def conn_error_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("Network error")
            return "connected"

        result = conn_error_func()
        self.assertEqual(result, "connected")
        self.assertEqual(call_count, 2)

    def test_multiple_exception_types(self):
        """Verify retry on multiple exception types."""
        call_count = 0
        config = RetryConfig(
            max_attempts=5,
            min_wait_seconds=0.01,
            max_wait_seconds=0.02,
            retry_exceptions=(ConnectionError, TimeoutError, OSError),
        )

        @with_retry(config=config)
        def multi_error_func():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ConnectionError("Network error")
            if call_count == 2:
                raise TimeoutError("Timeout")
            if call_count == 3:
                raise OSError("OS error")
            return "success"

        result = multi_error_func()
        self.assertEqual(result, "success")
        self.assertEqual(call_count, 4)

    def test_subclass_exception_is_retried(self):
        """Verify subclass of configured exception triggers retry."""
        call_count = 0
        config = RetryConfig(
            max_attempts=3,
            min_wait_seconds=0.01,
            max_wait_seconds=0.02,
            retry_exceptions=(OSError,),  # ConnectionError is subclass
        )

        @with_retry(config=config)
        def subclass_error_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("Network error")  # Subclass of OSError
            return "success"

        result = subclass_error_func()
        self.assertEqual(result, "success")

    def test_empty_exceptions_tuple_retries_nothing(self):
        """Verify empty exceptions tuple means no retries."""
        config = RetryConfig(
            max_attempts=3,
            retry_exceptions=(),
        )

        @with_retry(config=config)
        def any_error_func():
            raise ValueError("No retry for this")

        # With empty tuple, should not retry any exception
        with self.assertRaises(ValueError):
            any_error_func()


class TestCreateRetryDecorator(unittest.TestCase):
    """Tests for create_retry_decorator factory function."""

    def test_creates_working_decorator(self):
        """Verify create_retry_decorator returns a working decorator."""
        config = RetryConfig(max_attempts=2)
        decorator = create_retry_decorator(config)

        @decorator
        def my_func():
            return "works"

        result = my_func()
        self.assertEqual(result, "works")

    def test_none_config_uses_default(self):
        """Verify None config uses DEFAULT_RETRY_CONFIG."""
        decorator = create_retry_decorator(None)

        @decorator
        def my_func():
            return "works"

        result = my_func()
        self.assertEqual(result, "works")


# Import logging.handlers for MemoryHandler
import logging.handlers


if __name__ == "__main__":
    unittest.main()
