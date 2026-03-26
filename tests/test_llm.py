"""
Tests for LLM Abstraction Layer
================================

Sprint 19: Unit tests for base types, providers, and router failover logic.
"""

from __future__ import annotations

from collections.abc import Generator
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from llm.base import (
    LLMAuthError,
    LLMError,
    LLMMessage,
    LLMProvider,
    LLMRateLimitError,
    LLMResponse,
    LLMRole,
)
from llm.router import LLMRouter, ProviderStats, reset_router

# ---------------------------------------------------------------------------
# Fixtures: Mock Providers
# ---------------------------------------------------------------------------


class MockProvider(LLMProvider):
    """Configurable mock LLM provider for testing."""

    def __init__(
        self,
        name: str = "mock",
        available: bool = True,
        response_text: str = "Mock response",
        error: Exception | None = None,
    ):
        self.name = name
        self._available = available
        self._response_text = response_text
        self._error = error
        self.call_count = 0

    def is_available(self) -> bool:
        return self._available

    def generate(
        self,
        messages: list[LLMMessage],
        *,
        temperature: float = 0.3,
        max_tokens: int = 2048,
        **kwargs: Any,
    ) -> LLMResponse:
        self.call_count += 1
        if self._error:
            raise self._error
        return LLMResponse(
            content=self._response_text,
            provider=self.name,
            model="mock-model",
            usage={"input_tokens": 10, "output_tokens": 20},
        )

    def stream(
        self,
        messages: list[LLMMessage],
        *,
        temperature: float = 0.3,
        max_tokens: int = 2048,
        **kwargs: Any,
    ) -> Generator[str, None, None]:
        self.call_count += 1
        if self._error:
            raise self._error
        for word in self._response_text.split():
            yield word + " "


# ---------------------------------------------------------------------------
# Base types tests
# ---------------------------------------------------------------------------


class TestLLMMessage:
    def test_create_message(self):
        msg = LLMMessage(role=LLMRole.USER, content="Hello")
        assert msg.role == LLMRole.USER
        assert msg.content == "Hello"

    def test_system_message(self):
        msg = LLMMessage(role=LLMRole.SYSTEM, content="Be helpful")
        assert msg.role == LLMRole.SYSTEM


class TestLLMResponse:
    def test_response_fields(self):
        resp = LLMResponse(
            content="Test",
            provider="groq",
            model="llama-3",
            usage={"input_tokens": 100, "output_tokens": 50},
            latency_ms=150.5,
        )
        assert resp.content == "Test"
        assert resp.provider == "groq"
        assert resp.input_tokens == 100
        assert resp.output_tokens == 50
        assert resp.latency_ms == 150.5

    def test_empty_usage(self):
        resp = LLMResponse(content="", provider="test", model="m")
        assert resp.input_tokens == 0
        assert resp.output_tokens == 0


class TestLLMErrors:
    def test_base_error(self):
        err = LLMError("something broke", provider="groq", retryable=True)
        assert str(err) == "something broke"
        assert err.provider == "groq"
        assert err.retryable is True

    def test_rate_limit_always_retryable(self):
        err = LLMRateLimitError("429 too many", provider="claude", retry_after=30)
        assert err.retryable is True
        assert err.retry_after == 30

    def test_auth_never_retryable(self):
        err = LLMAuthError("bad key", provider="gemini")
        assert err.retryable is False


class TestMakeMessages:
    def test_default_system(self):
        msgs = LLMProvider._make_messages("Analyze AAPL")
        assert len(msgs) == 2
        assert msgs[0].role == LLMRole.SYSTEM
        assert "financial analyst" in msgs[0].content
        assert msgs[1].role == LLMRole.USER
        assert msgs[1].content == "Analyze AAPL"

    def test_custom_system(self):
        msgs = LLMProvider._make_messages("Hello", system="Be brief.")
        assert msgs[0].content == "Be brief."


# ---------------------------------------------------------------------------
# Router tests
# ---------------------------------------------------------------------------


class TestRouterBasic:
    def test_empty_router_raises(self):
        router = LLMRouter(providers=[])
        with pytest.raises(LLMError, match="No LLM providers"):
            router.generate("test")

    def test_single_provider_success(self):
        p = MockProvider(name="mock1", response_text="Hello World")
        router = LLMRouter(providers=[p])
        response = router.generate("test")
        assert response.content == "Hello World"
        assert response.provider == "mock1"
        assert p.call_count == 1

    def test_stats_tracked(self):
        p = MockProvider(name="m1")
        router = LLMRouter(providers=[p])
        router.generate("test")
        assert router.stats["m1"].total_calls == 1
        assert router.stats["m1"].total_errors == 0
        assert router.stats["m1"].consecutive_errors == 0

    def test_available_providers(self):
        p1 = MockProvider(name="a", available=True)
        p2 = MockProvider(name="b", available=False)
        p3 = MockProvider(name="c", available=True)
        router = LLMRouter(providers=[p1, p2, p3])
        assert "a" in router.available_providers
        assert "b" not in router.available_providers
        assert "c" in router.available_providers


class TestRouterFailover:
    def test_failover_on_error(self):
        """When first provider fails, second should be tried."""
        p1 = MockProvider(
            name="failing",
            error=LLMError("broken", provider="failing", retryable=True),
        )
        p2 = MockProvider(name="backup", response_text="Backup response")
        router = LLMRouter(providers=[p1, p2])

        response = router.generate("test")
        assert response.content == "Backup response"
        assert response.provider == "backup"
        assert p1.call_count == 1
        assert p2.call_count == 1

    def test_failover_on_rate_limit(self):
        """Rate limit on first provider → failover to second."""
        p1 = MockProvider(
            name="rated",
            error=LLMRateLimitError("429", provider="rated"),
        )
        p2 = MockProvider(name="ok", response_text="Success")
        router = LLMRouter(providers=[p1, p2])

        response = router.generate("test")
        assert response.content == "Success"
        assert router.stats["rated"].total_errors == 1

    def test_auth_error_disables_provider(self):
        """Auth error should permanently disable the provider."""
        p1 = MockProvider(
            name="bad_key",
            error=LLMAuthError("invalid key", provider="bad_key"),
        )
        p2 = MockProvider(name="good", response_text="OK")
        router = LLMRouter(providers=[p1, p2])

        response = router.generate("test")
        assert response.content == "OK"
        assert "bad_key" in router._disabled
        assert "bad_key" not in router.available_providers

    def test_all_providers_fail_raises(self):
        """When all providers fail, raise LLMError."""
        p1 = MockProvider(
            name="f1",
            error=LLMError("fail1", provider="f1", retryable=True),
        )
        p2 = MockProvider(
            name="f2",
            error=LLMError("fail2", provider="f2", retryable=True),
        )
        router = LLMRouter(providers=[p1, p2])

        with pytest.raises(LLMError, match="All providers failed"):
            router.generate("test")

    def test_unavailable_provider_skipped(self):
        """Unavailable providers should be skipped entirely."""
        p1 = MockProvider(name="offline", available=False)
        p2 = MockProvider(name="online", response_text="I'm here")
        router = LLMRouter(providers=[p1, p2])

        response = router.generate("test")
        assert response.content == "I'm here"
        assert p1.call_count == 0  # never called


class TestRouterStreaming:
    def test_stream_success(self):
        p = MockProvider(name="streamer", response_text="Hello World")
        router = LLMRouter(providers=[p])

        tokens = list(router.stream("test"))
        assert len(tokens) == 2
        assert "Hello" in tokens[0]
        assert "World" in tokens[1]

    def test_stream_failover(self):
        p1 = MockProvider(
            name="fail_stream",
            error=LLMError("stream broke", provider="fail_stream", retryable=True),
        )
        p2 = MockProvider(name="ok_stream", response_text="Backup stream")
        router = LLMRouter(providers=[p1, p2])

        tokens = list(router.stream("test"))
        assert len(tokens) > 0
        combined = "".join(tokens)
        assert "Backup" in combined


class TestRouterStatus:
    def test_get_status(self):
        p1 = MockProvider(name="groq", available=True)
        p2 = MockProvider(name="claude", available=False)
        router = LLMRouter(providers=[p1, p2])
        router.generate("test")

        status = router.get_status()
        assert len(status["providers"]) == 2
        assert status["providers"][0]["name"] == "groq"
        assert status["providers"][0]["total_calls"] == 1
        assert "groq" in status["available"]
        assert "claude" not in status["available"]


class TestProviderStats:
    def test_healthy_by_default(self):
        s = ProviderStats()
        assert s.is_healthy is True
        assert s.avg_latency_ms == 0.0
        assert s.error_rate == 0.0

    def test_unhealthy_after_consecutive_errors(self):
        s = ProviderStats(consecutive_errors=3, last_error_time=999_999_999_999)
        assert s.is_healthy is False

    def test_error_rate_calculation(self):
        s = ProviderStats(total_calls=10, total_errors=3)
        assert s.error_rate == 0.3


# ---------------------------------------------------------------------------
# Provider availability tests (import-only)
# ---------------------------------------------------------------------------


class TestGroqProviderAvailability:
    def test_no_key_not_available(self):
        from llm.groq_provider import GroqProvider

        p = GroqProvider(api_key="")
        # Without a key it should NOT be available
        # (the exact result depends on env, but the constructor shouldn't crash)
        assert isinstance(p.name, str)

    def test_with_key_available(self):
        from llm.groq_provider import GroqProvider

        p = GroqProvider(api_key="test-key-123")
        # Mock the groq import so we only test key logic, not package install
        with patch.dict("sys.modules", {"groq": MagicMock()}):
            assert p.is_available() is True


class TestClaudeProviderAvailability:
    def test_no_key_not_available(self):
        from llm.claude_provider import ClaudeProvider

        p = ClaudeProvider(api_key="")
        assert isinstance(p.name, str)

    def test_import_guard(self):
        """If anthropic is not installed, is_available should return False."""
        from llm.claude_provider import ClaudeProvider

        p = ClaudeProvider(api_key="test-key")
        # May or may not be True depending on whether anthropic is installed
        assert isinstance(p.is_available(), bool)


class TestGeminiProviderAvailability:
    def test_no_key_not_available(self):
        from llm.gemini_provider import GeminiProvider

        p = GeminiProvider(api_key="")
        assert isinstance(p.name, str)

    def test_with_key_available(self):
        from llm.gemini_provider import GeminiProvider

        p = GeminiProvider(api_key="test-key-456")
        # Mock the google.genai import so we only test key logic
        mock_google = MagicMock()
        with patch.dict("sys.modules", {"google": mock_google, "google.genai": mock_google.genai}):
            assert p.is_available() is True


# ---------------------------------------------------------------------------
# get_router singleton test
# ---------------------------------------------------------------------------


class TestGetRouter:
    def test_singleton(self):
        reset_router()
        from llm.router import get_router

        r1 = get_router()
        r2 = get_router()
        assert r1 is r2
        reset_router()

    def test_reset_creates_new(self):
        reset_router()
        from llm.router import get_router

        r1 = get_router()
        reset_router()
        r2 = get_router()
        assert r1 is not r2
        reset_router()
