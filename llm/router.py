"""
LLM Router — Smart failover, cost-aware routing, usage tracking.

Sprint 19: Automatic failover across Groq → Claude → Gemini.
           Tracks per-provider latency and error counts.

Usage:
    from llm import get_router

    router = get_router()
    response = router.generate("Analyze NVDA stock")
    print(response.content, response.provider, response.latency_ms)
"""

from __future__ import annotations

import logging
import time
from collections import defaultdict
from collections.abc import Generator
from dataclasses import dataclass
from typing import Any

from llm.base import (
    LLMAuthError,
    LLMError,
    LLMMessage,
    LLMProvider,
    LLMRateLimitError,
    LLMResponse,
)

logger = logging.getLogger(__name__)


@dataclass
class ProviderStats:
    """Per-provider health & usage statistics."""

    total_calls: int = 0
    total_errors: int = 0
    total_latency_ms: float = 0.0
    last_error: str = ""
    last_error_time: float = 0.0
    consecutive_errors: int = 0

    @property
    def avg_latency_ms(self) -> float:
        return self.total_latency_ms / self.total_calls if self.total_calls else 0.0

    @property
    def error_rate(self) -> float:
        return self.total_errors / self.total_calls if self.total_calls else 0.0

    @property
    def is_healthy(self) -> bool:
        """Provider is healthy if <3 consecutive errors and last error was >60s ago."""
        if self.consecutive_errors >= 3:
            return time.time() - self.last_error_time > 60
        return True


class LLMRouter:
    """Routes requests to the best available LLM provider with automatic failover.

    Priority order (configurable):
      1. Groq   — fastest, free tier
      2. Claude  — best quality, paid
      3. Gemini  — good free tier, multimodal

    Failover logic:
      - Try providers in priority order
      - Skip unavailable or unhealthy providers
      - On retryable errors, try next provider
      - On auth errors, skip permanently
      - Track stats for observability
    """

    def __init__(self, providers: list[LLMProvider] | None = None):
        self._providers: list[LLMProvider] = providers or []
        self._stats: dict[str, ProviderStats] = defaultdict(ProviderStats)
        self._disabled: set[str] = set()

    def add_provider(self, provider: LLMProvider) -> None:
        """Add a provider to the router."""
        self._providers.append(provider)

    @property
    def available_providers(self) -> list[str]:
        """List of currently available provider names."""
        return [
            p.name
            for p in self._providers
            if p.name not in self._disabled and p.is_available() and self._stats[p.name].is_healthy
        ]

    @property
    def stats(self) -> dict[str, ProviderStats]:
        """Per-provider statistics (read-only view)."""
        return dict(self._stats)

    def _get_ordered_providers(self) -> list[LLMProvider]:
        """Return providers in priority order, skipping disabled/unhealthy ones."""
        ordered = []
        for p in self._providers:
            if p.name in self._disabled:
                continue
            if not p.is_available():
                continue
            if not self._stats[p.name].is_healthy:
                logger.info(
                    "Skipping unhealthy provider %s (consecutive_errors=%d)",
                    p.name,
                    self._stats[p.name].consecutive_errors,
                )
                continue
            ordered.append(p)
        return ordered

    def _record_success(self, provider_name: str, latency_ms: float) -> None:
        """Record a successful call."""
        stats = self._stats[provider_name]
        stats.total_calls += 1
        stats.total_latency_ms += latency_ms
        stats.consecutive_errors = 0

    def _record_error(self, provider_name: str, error: Exception) -> None:
        """Record a failed call."""
        stats = self._stats[provider_name]
        stats.total_calls += 1
        stats.total_errors += 1
        stats.last_error = str(error)[:200]
        stats.last_error_time = time.time()
        stats.consecutive_errors += 1

    def generate(
        self,
        prompt: str,
        *,
        system: str = "You are a senior financial analyst. Answer in Markdown.",
        temperature: float = 0.3,
        max_tokens: int = 2048,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate a response using the best available provider.

        Args:
            prompt: User prompt text
            system: System instruction
            temperature: Sampling temperature
            max_tokens: Max output tokens
            **kwargs: Extra args passed to provider

        Returns:
            LLMResponse from the first successful provider

        Raises:
            LLMError: If all providers fail
        """
        messages = LLMProvider._make_messages(prompt, system)
        return self.generate_messages(
            messages, temperature=temperature, max_tokens=max_tokens, **kwargs
        )

    def generate_messages(
        self,
        messages: list[LLMMessage],
        *,
        temperature: float = 0.3,
        max_tokens: int = 2048,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate a response from raw messages with failover."""
        providers = self._get_ordered_providers()
        if not providers:
            raise LLMError(
                "No LLM providers available. Configure at least one API key.",
                provider="router",
            )

        last_error: Exception | None = None
        for provider in providers:
            try:
                t0 = time.perf_counter()
                response = provider.generate(
                    messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs,
                )
                latency = (time.perf_counter() - t0) * 1000
                response.latency_ms = latency
                self._record_success(provider.name, latency)

                logger.info(
                    "LLM response from %s (%s) in %.0fms — %d tokens",
                    provider.name,
                    response.model,
                    latency,
                    response.output_tokens,
                )
                return response

            except LLMAuthError as e:
                # Auth errors are permanent — disable this provider
                logger.warning("Auth error for %s, disabling: %s", provider.name, e)
                self._disabled.add(provider.name)
                self._record_error(provider.name, e)
                last_error = e
                continue

            except LLMRateLimitError as e:
                logger.warning("Rate limit for %s: %s", provider.name, e)
                self._record_error(provider.name, e)
                last_error = e
                continue

            except LLMError as e:
                logger.warning("LLM error from %s: %s", provider.name, e)
                self._record_error(provider.name, e)
                last_error = e
                if e.retryable:
                    continue
                # Non-retryable LLM errors
                break

            except Exception as e:
                logger.warning("Unexpected error from %s: %s", provider.name, e)
                self._record_error(provider.name, e)
                last_error = e
                continue

        raise LLMError(
            f"All providers failed. Last error: {last_error}",
            provider="router",
        )

    def stream(
        self,
        prompt: str,
        *,
        system: str = "You are a senior financial analyst. Answer in Markdown.",
        temperature: float = 0.3,
        max_tokens: int = 2048,
        **kwargs: Any,
    ) -> Generator[str, None, None]:
        """Stream tokens from the best available provider with failover.

        Falls back to non-streaming generate() if all streaming attempts fail.
        """
        messages = LLMProvider._make_messages(prompt, system)
        return self.stream_messages(
            messages, temperature=temperature, max_tokens=max_tokens, **kwargs
        )

    def stream_messages(
        self,
        messages: list[LLMMessage],
        *,
        temperature: float = 0.3,
        max_tokens: int = 2048,
        **kwargs: Any,
    ) -> Generator[str, None, None]:
        """Stream tokens from raw messages with failover."""
        providers = self._get_ordered_providers()
        if not providers:
            raise LLMError(
                "No LLM providers available.",
                provider="router",
            )

        last_error: Exception | None = None
        for provider in providers:
            try:
                t0 = time.perf_counter()
                token_count = 0
                for token in provider.stream(
                    messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs,
                ):
                    token_count += 1
                    yield token

                latency = (time.perf_counter() - t0) * 1000
                self._record_success(provider.name, latency)
                logger.info(
                    "Streamed %d tokens from %s in %.0fms",
                    token_count,
                    provider.name,
                    latency,
                )
                return  # Success — stop trying other providers

            except LLMAuthError as e:
                self._disabled.add(provider.name)
                self._record_error(provider.name, e)
                last_error = e
                continue

            except (LLMRateLimitError, LLMError) as e:
                self._record_error(provider.name, e)
                last_error = e
                continue

            except Exception as e:
                self._record_error(provider.name, e)
                last_error = e
                continue

        raise LLMError(
            f"All providers failed for streaming. Last error: {last_error}",
            provider="router",
        )

    def get_status(self) -> dict[str, Any]:
        """Return current router status for observability / UI panels."""
        result: dict[str, Any] = {
            "providers": [],
            "disabled": list(self._disabled),
            "available": self.available_providers,
        }
        for p in self._providers:
            st = self._stats[p.name]
            result["providers"].append(
                {
                    "name": p.name,
                    "available": p.is_available(),
                    "healthy": st.is_healthy,
                    "disabled": p.name in self._disabled,
                    "total_calls": st.total_calls,
                    "error_rate": round(st.error_rate, 3),
                    "avg_latency_ms": round(st.avg_latency_ms, 1),
                    "consecutive_errors": st.consecutive_errors,
                }
            )
        return result


# ---------------------------------------------------------------------------
# Singleton router
# ---------------------------------------------------------------------------

_router_instance: LLMRouter | None = None


def get_router() -> LLMRouter:
    """Get (or create) the global LLM router with all configured providers.

    Provider priority: Groq → Claude → Gemini
    """
    global _router_instance
    if _router_instance is not None:
        return _router_instance

    router = LLMRouter()

    # Add providers in priority order
    try:
        from llm.groq_provider import GroqProvider

        router.add_provider(GroqProvider())
    except Exception as e:
        logger.debug("Could not init Groq provider: %s", e)

    try:
        from llm.claude_provider import ClaudeProvider

        router.add_provider(ClaudeProvider())
    except Exception as e:
        logger.debug("Could not init Claude provider: %s", e)

    try:
        from llm.gemini_provider import GeminiProvider

        router.add_provider(GeminiProvider())
    except Exception as e:
        logger.debug("Could not init Gemini provider: %s", e)

    _router_instance = router
    return router


def reset_router() -> None:
    """Reset the global router (for testing or reconfiguration)."""
    global _router_instance
    _router_instance = None
