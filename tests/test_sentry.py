# -*- coding: utf-8 -*-
"""
Tests for Sentry Integration
=============================
"""

from unittest.mock import MagicMock, Mock, patch

import pytest


class TestSentryClient:
    """Tests for SentryClient class."""

    def test_init_returns_false_without_dsn(self):
        """Test that init returns False when no DSN is provided."""
        from core.monitoring import SentryClient

        client = SentryClient()

        with patch.dict("os.environ", {}, clear=True):
            # Remove SENTRY_DSN if it exists
            import os

            os.environ.pop("SENTRY_DSN", None)

            result = client.init(dsn=None)
            assert result is False
            assert client.is_enabled() is False

    def test_init_returns_false_without_sentry_sdk(self):
        """Test that init returns False when sentry_sdk is not installed."""
        from core.monitoring import SentryClient

        client = SentryClient()

        with patch.dict("sys.modules", {"sentry_sdk": None}):
            with patch("builtins.__import__", side_effect=ImportError):
                result = client.init(dsn="https://fake@sentry.io/123")
                # Will fail on import
                assert result is False

    def test_capture_exception_returns_none_when_disabled(self):
        """Test that capture_exception returns None when Sentry is disabled."""
        from core.monitoring import SentryClient

        client = SentryClient()
        # Don't initialize - should be disabled

        result = client.capture_exception(ValueError("test"))
        assert result is None

    def test_capture_message_returns_none_when_disabled(self):
        """Test that capture_message returns None when Sentry is disabled."""
        from core.monitoring import SentryClient

        client = SentryClient()

        result = client.capture_message("test message")
        assert result is None

    def test_set_user_does_nothing_when_disabled(self):
        """Test that set_user does nothing when Sentry is disabled."""
        from core.monitoring import SentryClient

        client = SentryClient()

        # Should not raise
        client.set_user({"id": "123", "email": "test@example.com"})

    def test_set_tag_does_nothing_when_disabled(self):
        """Test that set_tag does nothing when Sentry is disabled."""
        from core.monitoring import SentryClient

        client = SentryClient()

        # Should not raise
        client.set_tag("key", "value")

    def test_set_context_does_nothing_when_disabled(self):
        """Test that set_context does nothing when Sentry is disabled."""
        from core.monitoring import SentryClient

        client = SentryClient()

        # Should not raise
        client.set_context("name", {"key": "value"})

    def test_add_breadcrumb_does_nothing_when_disabled(self):
        """Test that add_breadcrumb does nothing when Sentry is disabled."""
        from core.monitoring import SentryClient

        client = SentryClient()

        # Should not raise
        client.add_breadcrumb(
            message="test",
            category="test",
            level="info",
            data={"key": "value"},
        )

    def test_start_transaction_yields_none_when_disabled(self):
        """Test that start_transaction yields None when disabled."""
        from core.monitoring import SentryClient

        client = SentryClient()

        with client.start_transaction("test", op="test") as transaction:
            assert transaction is None

    def test_flush_does_nothing_when_disabled(self):
        """Test that flush does nothing when Sentry is disabled."""
        from core.monitoring import SentryClient

        client = SentryClient()

        # Should not raise
        client.flush()


class TestTrackErrorsSentryDecorator:
    """Tests for track_errors_sentry decorator."""

    def test_decorator_passes_through_on_success(self):
        """Test that decorator passes through when function succeeds."""
        from core.monitoring import track_errors_sentry

        @track_errors_sentry()
        def successful_function():
            return "success"

        result = successful_function()
        assert result == "success"

    def test_decorator_reraises_by_default(self):
        """Test that decorator re-raises exception by default."""
        from core.monitoring import track_errors_sentry

        @track_errors_sentry()
        def failing_function():
            raise ValueError("test error")

        with pytest.raises(ValueError, match="test error"):
            failing_function()

    def test_decorator_can_suppress_reraise(self):
        """Test that decorator can suppress re-raising."""
        from core.monitoring import track_errors_sentry

        @track_errors_sentry(reraise=False)
        def failing_function():
            raise ValueError("test error")

        result = failing_function()
        assert result is None


class TestSentryClientWithMockedSDK:
    """Tests with mocked sentry_sdk."""

    def test_init_with_valid_dsn(self):
        """Test successful initialization with valid DSN."""
        from core.monitoring import SentryClient

        mock_sentry = MagicMock()
        mock_logging_integration = MagicMock()

        with patch.dict(
            "sys.modules",
            {
                "sentry_sdk": mock_sentry,
                "sentry_sdk.integrations.logging": MagicMock(
                    LoggingIntegration=mock_logging_integration
                ),
            },
        ):
            client = SentryClient()
            result = client.init(dsn="https://fake@sentry.io/123")

            # Should call sentry_sdk.init
            mock_sentry.init.assert_called_once()
            assert client._enabled is True

    def test_capture_exception_with_mocked_sdk(self):
        """Test capture_exception calls sentry_sdk properly."""
        from core.monitoring import SentryClient

        mock_sentry = MagicMock()
        mock_sentry.capture_exception.return_value = "event-id-123"
        mock_scope = MagicMock()
        mock_sentry.push_scope.return_value.__enter__ = Mock(return_value=mock_scope)
        mock_sentry.push_scope.return_value.__exit__ = Mock(return_value=False)

        client = SentryClient()
        client._initialized = True
        client._enabled = True
        client._sentry = mock_sentry  # type: ignore[assignment]

        error = ValueError("test error")
        result = client.capture_exception(error, extra_key="extra_value")

        mock_sentry.capture_exception.assert_called_once_with(error)
        assert result == "event-id-123"

    def test_capture_message_with_mocked_sdk(self):
        """Test capture_message calls sentry_sdk properly."""
        from core.monitoring import SentryClient

        mock_sentry = MagicMock()
        mock_sentry.capture_message.return_value = "event-id-456"
        mock_scope = MagicMock()
        mock_sentry.push_scope.return_value.__enter__ = Mock(return_value=mock_scope)
        mock_sentry.push_scope.return_value.__exit__ = Mock(return_value=False)

        client = SentryClient()
        client._initialized = True
        client._enabled = True
        client._sentry = mock_sentry  # type: ignore[assignment]

        result = client.capture_message("Test message", level="warning")

        mock_sentry.capture_message.assert_called_once_with("Test message", level="warning")
        assert result == "event-id-456"

    def test_set_user_with_mocked_sdk(self):
        """Test set_user calls sentry_sdk properly."""
        from core.monitoring import SentryClient

        mock_sentry = MagicMock()

        client = SentryClient()
        client._initialized = True
        client._enabled = True
        client._sentry = mock_sentry  # type: ignore[assignment]

        client.set_user({"id": "123", "email": "test@example.com"})

        mock_sentry.set_user.assert_called_once_with(
            {
                "id": "123",
                "email": "test@example.com",
            }
        )

    def test_set_tag_with_mocked_sdk(self):
        """Test set_tag calls sentry_sdk properly."""
        from core.monitoring import SentryClient

        mock_sentry = MagicMock()

        client = SentryClient()
        client._initialized = True
        client._enabled = True
        client._sentry = mock_sentry  # type: ignore[assignment]

        client.set_tag("environment", "production")

        mock_sentry.set_tag.assert_called_once_with("environment", "production")

    def test_add_breadcrumb_with_mocked_sdk(self):
        """Test add_breadcrumb calls sentry_sdk properly."""
        from core.monitoring import SentryClient

        mock_sentry = MagicMock()

        client = SentryClient()
        client._initialized = True
        client._enabled = True
        client._sentry = mock_sentry  # type: ignore[assignment]

        client.add_breadcrumb(
            message="Started scan",
            category="scan",
            level="info",
            data={"ticker": "AAPL"},
        )

        mock_sentry.add_breadcrumb.assert_called_once_with(
            message="Started scan",
            category="scan",
            level="info",
            data={"ticker": "AAPL"},
        )


class TestGlobalSentryClient:
    """Tests for global sentry_client instance."""

    def test_global_instance_exists(self):
        """Test that global sentry_client instance exists."""
        from core.monitoring import sentry_client

        assert sentry_client is not None

    def test_global_instance_is_sentry_client(self):
        """Test that global instance is SentryClient."""
        from core.monitoring import SentryClient, sentry_client

        assert isinstance(sentry_client, SentryClient)

    def test_global_instance_not_initialized_by_default(self):
        """Test that global instance is not initialized by default."""
        from core.monitoring import SentryClient

        # Create a new instance to test default state
        client = SentryClient()
        assert client._initialized is False
        assert client.is_enabled() is False
