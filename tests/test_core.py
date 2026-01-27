"""
Core Infrastructure Tests
==========================

Test suite for core modules: config, exceptions, cache, logging, monitoring.

Run with: pytest tests/test_core.py -v
"""

import time
from pathlib import Path

import pytest

# =============================================================================
# CONFIG TESTS
# =============================================================================


class TestConfig:
    """Test core.config module."""

    def test_settings_singleton(self):
        """Settings should be singleton."""
        from core.config import get_settings, settings

        s1 = get_settings()
        s2 = get_settings()
        assert s1 is s2

    def test_default_values(self):
        """Check default configuration values."""
        from core.config import settings

        assert settings.APP_NAME == "FinPilot"
        assert settings.ENVIRONMENT == "development"
        assert settings.DEBUG is False

    def test_scanner_config(self):
        """Test nested scanner configuration."""
        from core.config import settings

        assert settings.scanner.rsi_oversold == 30.0
        assert settings.scanner.rsi_overbought == 70.0
        assert settings.scanner.rsi_period == 14
        assert settings.scanner.volume_surge_threshold == 2.0

    def test_drl_config(self):
        """Test nested DRL configuration."""
        from core.config import settings

        assert settings.drl.algorithm == "PPO"
        assert settings.drl.learning_rate == 3e-4
        assert settings.drl.total_timesteps == 100_000

    def test_paths_exist(self):
        """Project paths should exist."""
        from core.config import settings

        assert settings.project_root.exists()
        assert settings.data_dir.exists()
        assert settings.models_dir.exists()

    def test_scanner_presets(self):
        """Test scanner preset configurations."""
        from core.config import settings

        conservative = settings.get_scanner_preset("conservative")
        assert conservative.rsi_oversold == 25.0
        assert conservative.signal_threshold == 4

        aggressive = settings.get_scanner_preset("aggressive")
        assert aggressive.rsi_oversold == 35.0
        assert aggressive.signal_threshold == 2

    def test_to_dict_masks_secrets(self):
        """Sensitive values should be masked in export."""
        from core.config import settings

        data = settings.to_dict()
        # API keys should be masked
        assert data.get("POLYGON_API_KEY", "") in ["", "***"]

    def test_override_settings(self):
        """Test settings override for testing."""
        from core.config import override_settings

        test_settings = override_settings(DEBUG=True, ENVIRONMENT="staging")
        assert test_settings.DEBUG is True
        assert test_settings.ENVIRONMENT == "staging"


# =============================================================================
# EXCEPTIONS TESTS
# =============================================================================


class TestExceptions:
    """Test core.exceptions module."""

    def test_finpilot_error_base(self):
        """Base exception should have all attributes."""
        from core.exceptions import FinPilotError

        error = FinPilotError("Test error", code="TEST_001", details={"key": "value"})

        assert error.message == "Test error"
        assert error.code == "TEST_001"
        assert error.details["key"] == "value"
        assert error.timestamp is not None

    def test_exception_to_dict(self):
        """Exception should serialize to dict."""
        from core.exceptions import DataFetchError

        error = DataFetchError("API failed", source="polygon")
        data = error.to_dict()

        assert data["error"] == "DataFetchError"
        assert data["message"] == "API failed"
        assert data["details"]["source"] == "polygon"

    def test_exception_hierarchy(self):
        """Test exception inheritance."""
        from core.exceptions import (
            AuthenticationError,
            AuthError,
            DataError,
            DataFetchError,
            FinPilotError,
        )

        assert issubclass(DataFetchError, DataError)
        assert issubclass(DataError, FinPilotError)
        assert issubclass(AuthenticationError, AuthError)

    def test_handle_errors_decorator(self):
        """Test error handling decorator."""
        from core.exceptions import DataFetchError, handle_errors

        @handle_errors(DataFetchError, default_return="fallback", log_error=False)
        def failing_func():
            raise DataFetchError("Test")

        result = failing_func()
        assert result == "fallback"

    def test_handle_errors_reraise(self):
        """Test error handling with reraise."""
        from core.exceptions import DataError, DataFetchError, handle_errors

        @handle_errors(DataFetchError, reraise=True, log_error=False)
        def failing_func():
            raise DataFetchError("Test")

        with pytest.raises(DataFetchError):
            failing_func()

    def test_safe_execute(self):
        """Test safe_execute utility."""
        from core.exceptions import DataFetchError, safe_execute

        def success_func():
            return 42

        def failure_func():
            raise DataFetchError("Fail")

        result, error = safe_execute(success_func)
        assert result == 42
        assert error is None

        result, error = safe_execute(failure_func, default=0)
        assert result == 0
        assert isinstance(error, DataFetchError)


# =============================================================================
# CACHE TESTS
# =============================================================================


class TestCache:
    """Test core.cache module."""

    def test_memory_cache_basic(self):
        """Test basic cache operations."""
        from core.cache import MemoryCache

        cache = MemoryCache(max_size=100, default_ttl=60)

        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
        assert cache.exists("key1")

        cache.delete("key1")
        assert cache.get("key1") is None

    def test_memory_cache_ttl(self):
        """Test cache TTL expiration."""
        from core.cache import MemoryCache

        cache = MemoryCache(max_size=100, default_ttl=1)
        cache.set("key", "value", ttl=1)

        assert cache.get("key") == "value"
        time.sleep(1.1)
        assert cache.get("key") is None

    def test_memory_cache_lru(self):
        """Test LRU eviction."""
        from core.cache import MemoryCache

        cache = MemoryCache(max_size=3, default_ttl=60)

        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)

        # Access 'a' to make it recently used
        cache.get("a")

        # Add new item, should evict 'b' (least recently used)
        cache.set("d", 4)

        assert cache.exists("a")
        assert cache.exists("c")
        assert cache.exists("d")
        # 'b' should be evicted
        assert not cache.exists("b")

    def test_cache_manager(self):
        """Test CacheManager."""
        from core.cache import CacheManager

        manager = CacheManager(memory_max_size=100, memory_ttl=60)

        manager.set("test", {"data": 123})
        assert manager.get("test") == {"data": 123}

        # Test get_or_set
        value = manager.get_or_set("computed", lambda: 42)
        assert value == 42
        assert manager.get("computed") == 42

    def test_cached_decorator(self):
        """Test @cached decorator."""
        from core.cache import cached

        call_count = 0

        @cached(ttl=60, prefix="test")
        def expensive_func(x: int) -> int:
            nonlocal call_count
            call_count += 1
            return x * 2

        # First call
        result1 = expensive_func(5)
        assert result1 == 10
        assert call_count == 1

        # Second call (should be cached)
        result2 = expensive_func(5)
        assert result2 == 10
        assert call_count == 1  # No new call

        # Different argument
        result3 = expensive_func(10)
        assert result3 == 20
        assert call_count == 2

    def test_cache_stats(self):
        """Test cache statistics."""
        from core.cache import MemoryCache

        cache = MemoryCache(max_size=100, default_ttl=60)

        cache.set("a", 1)
        cache.get("a")  # Hit
        cache.get("a")  # Hit
        cache.get("b")  # Miss

        stats = cache.get_stats()
        assert stats["hits"] == 2
        assert stats["misses"] == 1
        assert stats["size"] == 1


# =============================================================================
# LOGGING TESTS
# =============================================================================


class TestLogging:
    """Test core.logging module."""

    def test_get_logger(self):
        """Test logger creation."""
        from core.logging import get_logger

        logger = get_logger("test_module")
        assert logger is not None
        assert "finpilot" in logger.name

    def test_log_context(self):
        """Test logging context."""
        from core.logging import clear_context, get_context, log_context

        clear_context()

        with log_context(request_id="abc123", user_id=42):
            ctx = get_context()
            assert ctx["request_id"] == "abc123"
            assert ctx["user_id"] == 42

        # Context should be cleared
        ctx = get_context()
        assert "request_id" not in ctx

    def test_timer_context_manager(self):
        """Test Timer context manager."""
        from core.logging import Timer

        with Timer("test_operation") as t:
            time.sleep(0.1)

        assert t.duration >= 0.1
        assert t.duration < 0.2

    def test_json_formatter(self):
        """Test JSON log formatting."""
        import logging

        from core.logging import JSONFormatter

        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        output = formatter.format(record)
        import json

        data = json.loads(output)

        assert data["level"] == "INFO"
        assert data["message"] == "Test message"
        assert "timestamp" in data


# =============================================================================
# MONITORING TESTS
# =============================================================================


class TestMonitoring:
    """Test core.monitoring module."""

    def test_counter(self):
        """Test Counter metric."""
        from core.monitoring import Counter

        counter = Counter("test_counter", "Test counter")

        counter.inc()
        assert counter.get() == 1

        counter.inc(5)
        assert counter.get() == 6

    def test_counter_with_labels(self):
        """Test Counter with labels."""
        from core.monitoring import Counter

        counter = Counter("requests", "Requests", labels=["method", "status"])

        counter.inc(method="GET", status="200")
        counter.inc(method="GET", status="200")
        counter.inc(method="POST", status="201")

        assert counter.get(method="GET", status="200") == 2
        assert counter.get(method="POST", status="201") == 1

    def test_gauge(self):
        """Test Gauge metric."""
        from core.monitoring import Gauge

        gauge = Gauge("temperature", "Temperature")

        gauge.set(25.5)
        assert gauge.get() == 25.5

        gauge.inc(1.0)
        assert gauge.get() == 26.5

        gauge.dec(0.5)
        assert gauge.get() == 26.0

    def test_histogram(self):
        """Test Histogram metric."""
        from core.monitoring import Histogram

        histogram = Histogram(
            "latency",
            "Request latency",
            buckets=(0.1, 0.5, 1.0, float("inf")),
        )

        histogram.observe(0.05)
        histogram.observe(0.3)
        histogram.observe(0.8)
        histogram.observe(2.0)

        stats = histogram.get_stats()
        assert stats["count"] == 4
        assert stats["min"] == 0.05
        assert stats["max"] == 2.0

    def test_histogram_timer(self):
        """Test Histogram timer context."""
        from core.monitoring import Histogram

        histogram = Histogram("duration", "Duration")

        with histogram.time():
            time.sleep(0.1)

        stats = histogram.get_stats()
        assert stats["count"] == 1
        assert stats["min"] >= 0.1

    def test_metrics_registry(self):
        """Test MetricsRegistry."""
        from core.monitoring import metrics

        # Built-in metrics should exist
        assert hasattr(metrics, "signals_generated")
        assert hasattr(metrics, "scan_duration")
        assert hasattr(metrics, "errors_total")

    def test_health_checker(self):
        """Test HealthChecker."""
        from core.monitoring import HealthChecker, HealthCheckResult, HealthStatus

        checker = HealthChecker()

        @checker.register("test_check")
        def test_check():
            return True

        @checker.register("failing_check")
        def failing_check():
            return False

        result = checker.run()

        assert result["status"] == "unhealthy"  # One check failed
        assert len(result["checks"]) == 2

    def test_prometheus_export(self):
        """Test Prometheus format export."""
        from core.monitoring import MetricsRegistry

        registry = MetricsRegistry()
        registry.signals_generated.inc(ticker="AAPL", signal_type="buy")  # type: ignore[union-attr]

        output = registry.export_prometheus()

        assert "finpilot_signals_generated_total" in output
        assert 'ticker="AAPL"' in output


# =============================================================================
# INTEGRATION TESTS
# =============================================================================


class TestIntegration:
    """Integration tests for core modules."""

    def test_config_with_cache(self):
        """Test config integration with cache."""
        from core.cache import CacheManager
        from core.config import settings

        manager = CacheManager(
            memory_max_size=settings.cache.memory_max_size,
            memory_ttl=settings.cache.memory_ttl_seconds,
        )

        manager.set("test", "value")
        assert manager.get("test") == "value"

    def test_exception_with_logging(self):
        """Test exception handling with logging."""
        from core.exceptions import DataFetchError, handle_errors
        from core.logging import get_logger

        @handle_errors(DataFetchError, default_return=None, log_error=True)
        def test_func():
            raise DataFetchError("Test error")

        result = test_func()
        assert result is None

    def test_monitoring_with_decorator(self):
        """Test monitoring decorators."""
        from core.monitoring import count_calls, metrics, track_time

        @count_calls(metrics.scans_total, scan_type="test")  # type: ignore[arg-type]
        @track_time(metrics.scan_duration, scan_type="test")  # type: ignore[arg-type]
        def test_scan():
            time.sleep(0.05)
            return "done"

        result = test_scan()
        assert result == "done"

        assert metrics.scans_total.get(scan_type="test") >= 1  # type: ignore[union-attr]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
