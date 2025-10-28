"""
Tests for retry handler.
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock

from core.retry_handler import (
    RetryConfig,
    retry_with_backoff,
    RateLimitError,
    TimeoutError,
    ServiceUnavailableError,
    DEFAULT_RETRY_CONFIG,
    AGGRESSIVE_RETRY_CONFIG,
    API_RATE_LIMIT_RETRY_CONFIG
)


class TestRetryConfig:
    """Tests for RetryConfig."""

    def test_retry_config_defaults(self):
        """Test default retry configuration."""
        config = RetryConfig()

        assert config.max_retries == 3
        assert config.initial_delay == 1.0
        assert config.max_delay == 60.0
        assert config.exponential_base == 2.0
        assert config.jitter is True

    def test_retry_config_custom(self):
        """Test custom retry configuration."""
        config = RetryConfig(
            max_retries=5,
            initial_delay=2.0,
            max_delay=120.0,
            exponential_base=3.0,
            jitter=False
        )

        assert config.max_retries == 5
        assert config.initial_delay == 2.0
        assert config.max_delay == 120.0
        assert config.exponential_base == 3.0
        assert config.jitter is False

    def test_calculate_delay_exponential(self):
        """Test exponential delay calculation."""
        config = RetryConfig(initial_delay=1.0, exponential_base=2.0, jitter=False)

        assert config.calculate_delay(0) == 1.0  # 1.0 * 2^0
        assert config.calculate_delay(1) == 2.0  # 1.0 * 2^1
        assert config.calculate_delay(2) == 4.0  # 1.0 * 2^2
        assert config.calculate_delay(3) == 8.0  # 1.0 * 2^3

    def test_calculate_delay_max_delay(self):
        """Test max delay limit."""
        config = RetryConfig(
            initial_delay=1.0,
            max_delay=5.0,
            exponential_base=2.0,
            jitter=False
        )

        assert config.calculate_delay(5) == 5.0  # Capped at max_delay

    def test_calculate_delay_with_jitter(self):
        """Test delay calculation with jitter."""
        config = RetryConfig(initial_delay=2.0, jitter=True)

        delays = [config.calculate_delay(0) for _ in range(100)]

        # With jitter, delays should vary but be in range [1.0, 2.0]
        assert all(1.0 <= d <= 2.0 for d in delays)
        # Should not all be the same
        assert len(set(delays)) > 1

    def test_should_retry_max_attempts(self):
        """Test should_retry respects max_retries."""
        config = RetryConfig(max_retries=3)

        assert config.should_retry(Exception(), 0)
        assert config.should_retry(Exception(), 1)
        assert config.should_retry(Exception(), 2)
        assert not config.should_retry(Exception(), 3)

    def test_should_retry_exception_types(self):
        """Test should_retry respects exception types."""
        config = RetryConfig(
            max_retries=3,
            retry_on_exceptions=(RateLimitError, TimeoutError)
        )

        # Should retry on specified exceptions
        assert config.should_retry(RateLimitError(), 0)
        assert config.should_retry(TimeoutError(), 0)

        # Should not retry on other exceptions
        assert not config.should_retry(ValueError(), 0)
        assert not config.should_retry(KeyError(), 0)


class TestRetryDecorator:
    """Tests for retry_with_backoff decorator."""

    @pytest.mark.asyncio
    async def test_async_function_success_no_retry(self):
        """Test async function succeeds without retry."""
        call_count = 0

        @retry_with_backoff(config=RetryConfig(max_retries=3))
        async def successful_function():
            nonlocal call_count
            call_count += 1
            return "success"

        result = await successful_function()

        assert result == "success"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_async_function_retry_then_succeed(self):
        """Test async function retries then succeeds."""
        call_count = 0

        @retry_with_backoff(config=RetryConfig(max_retries=3, initial_delay=0.01))
        async def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise RateLimitError("Rate limit exceeded")
            return "success"

        result = await flaky_function()

        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_async_function_max_retries_exceeded(self):
        """Test async function exceeds max retries."""
        call_count = 0

        @retry_with_backoff(config=RetryConfig(max_retries=2, initial_delay=0.01))
        async def always_fails():
            nonlocal call_count
            call_count += 1
            raise RateLimitError("Always fails")

        with pytest.raises(RateLimitError):
            await always_fails()

        assert call_count == 3  # Initial + 2 retries

    @pytest.mark.asyncio
    async def test_async_function_no_retry_on_non_retryable(self):
        """Test async function doesn't retry on non-retryable exceptions."""
        call_count = 0

        @retry_with_backoff(
            config=RetryConfig(
                max_retries=3,
                retry_on_exceptions=(RateLimitError,)
            )
        )
        async def fails_with_value_error():
            nonlocal call_count
            call_count += 1
            raise ValueError("Not retryable")

        with pytest.raises(ValueError):
            await fails_with_value_error()

        assert call_count == 1  # No retries

    def test_sync_function_success_no_retry(self):
        """Test sync function succeeds without retry."""
        call_count = 0

        @retry_with_backoff(config=RetryConfig(max_retries=3))
        def successful_function():
            nonlocal call_count
            call_count += 1
            return "success"

        result = successful_function()

        assert result == "success"
        assert call_count == 1

    def test_sync_function_retry_then_succeed(self):
        """Test sync function retries then succeeds."""
        call_count = 0

        @retry_with_backoff(config=RetryConfig(max_retries=3, initial_delay=0.01))
        def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise TimeoutError("Timeout")
            return "success"

        result = flaky_function()

        assert result == "success"
        assert call_count == 3

    def test_sync_function_max_retries_exceeded(self):
        """Test sync function exceeds max retries."""
        call_count = 0

        @retry_with_backoff(config=RetryConfig(max_retries=2, initial_delay=0.01))
        def always_fails():
            nonlocal call_count
            call_count += 1
            raise ServiceUnavailableError("Service down")

        with pytest.raises(ServiceUnavailableError):
            always_fails()

        assert call_count == 3  # Initial + 2 retries

    @pytest.mark.asyncio
    async def test_retry_callback(self):
        """Test on_retry callback is called."""
        callback_calls = []

        def on_retry_callback(exception, attempt, delay):
            callback_calls.append({
                'exception': type(exception).__name__,
                'attempt': attempt,
                'delay': delay
            })

        call_count = 0

        @retry_with_backoff(
            config=RetryConfig(max_retries=2, initial_delay=0.01),
            on_retry=on_retry_callback
        )
        async def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise RateLimitError("Rate limit")
            return "success"

        result = await flaky_function()

        assert result == "success"
        assert len(callback_calls) == 2
        assert all(c['exception'] == 'RateLimitError' for c in callback_calls)
        assert [c['attempt'] for c in callback_calls] == [0, 1]

    @pytest.mark.asyncio
    async def test_exponential_backoff_timing(self):
        """Test that exponential backoff delays are respected."""
        call_times = []

        @retry_with_backoff(
            config=RetryConfig(max_retries=3, initial_delay=0.1, jitter=False)
        )
        async def time_tracked_function():
            call_times.append(time.time())
            if len(call_times) < 3:
                raise TimeoutError("Timeout")
            return "success"

        result = await time_tracked_function()

        assert result == "success"
        assert len(call_times) == 3

        # Check delays are approximately exponential
        delay_1 = call_times[1] - call_times[0]
        delay_2 = call_times[2] - call_times[1]

        # First delay should be ~0.1s, second ~0.2s
        assert 0.08 < delay_1 < 0.15
        assert 0.18 < delay_2 < 0.25


class TestRetryExceptions:
    """Tests for retry exception classes."""

    def test_retryable_error(self):
        """Test RetryableError base class."""
        from core.retry_handler import RetryableError

        error = RetryableError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception)

    def test_rate_limit_error(self):
        """Test RateLimitError."""
        error = RateLimitError("Rate limit exceeded")
        assert str(error) == "Rate limit exceeded"

    def test_timeout_error(self):
        """Test TimeoutError."""
        error = TimeoutError("Request timed out")
        assert str(error) == "Request timed out"

    def test_service_unavailable_error(self):
        """Test ServiceUnavailableError."""
        error = ServiceUnavailableError("Service down")
        assert str(error) == "Service down"


class TestPredefinedConfigs:
    """Tests for predefined retry configurations."""

    def test_default_retry_config(self):
        """Test DEFAULT_RETRY_CONFIG."""
        assert DEFAULT_RETRY_CONFIG.max_retries == 3
        assert DEFAULT_RETRY_CONFIG.initial_delay == 1.0

    def test_aggressive_retry_config(self):
        """Test AGGRESSIVE_RETRY_CONFIG."""
        assert AGGRESSIVE_RETRY_CONFIG.max_retries == 5
        assert AGGRESSIVE_RETRY_CONFIG.initial_delay == 0.5

    def test_conservative_retry_config(self):
        """Test CONSERVATIVE_RETRY_CONFIG."""
        from core.retry_handler import CONSERVATIVE_RETRY_CONFIG

        assert CONSERVATIVE_RETRY_CONFIG.max_retries == 2
        assert CONSERVATIVE_RETRY_CONFIG.initial_delay == 2.0

    def test_api_rate_limit_retry_config(self):
        """Test API_RATE_LIMIT_RETRY_CONFIG."""
        assert API_RATE_LIMIT_RETRY_CONFIG.max_retries == 5
        assert API_RATE_LIMIT_RETRY_CONFIG.initial_delay == 5.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
