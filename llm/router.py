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
import os
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
    LLMRole,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Sprint 4 — response cache + per-provider rate limiting
# ---------------------------------------------------------------------------

_LLM_CACHE_NS = "llm_response"
_LLM_CACHE_TTL = int(os.environ.get("LLM_CACHE_TTL_SECONDS", "3600"))
_HEADROOM_ENABLED = os.environ.get("HEADROOM_ENABLED", "false").lower() == "true"


def _headroom_compress(messages: list[LLMMessage]) -> list[LLMMessage]:
    """Compress messages with headroom before sending to LLM provider.

    Silently returns original messages if headroom is disabled, not installed,
    or raises any error — never blocks the LLM call.
    """
    if not _HEADROOM_ENABLED:
        return messages
    try:
        from headroom import compress  # noqa: PLC0415

        dicts = [{"role": m.role.value, "content": m.content} for m in messages]
        compressed = compress(dicts)
        if not compressed or not isinstance(compressed, list):
            return messages
        result = [
            LLMMessage(role=LLMRole(c["role"]), content=c["content"])
            for c in compressed
            if isinstance(c, dict) and "role" in c and "content" in c
        ]
        if not result:
            return messages
        original_chars = sum(len(m.content) for m in messages)
        compressed_chars = sum(len(m.content) for m in result)
        if original_chars > 0:
            logger.debug(
                "Headroom compression: %d → %d chars (%.0f%% reduction)",
                original_chars,
                compressed_chars,
                (1 - compressed_chars / original_chars) * 100,
            )
        return result
    except Exception as exc:  # noqa: BLE001
        logger.debug("Headroom compression skipped: %s", exc)
        return messages


# Bucket defaults: ~5 RPS, burst 10. Override via env per provider:
#   LLM_RATE_GROQ=10, LLM_BURST_GROQ=20
_LLM_DEFAULT_RATE = float(os.environ.get("LLM_RATE_DEFAULT", "5"))
_LLM_DEFAULT_BURST = float(os.environ.get("LLM_BURST_DEFAULT", "10"))


def _llm_cache_key(
    messages: list[LLMMessage], temperature: float, max_tokens: int, model: str | None
) -> str:
    from core.cache import make_cache_key

    serialised = [
        (m.role.value if hasattr(m.role, "value") else str(m.role), m.content) for m in messages
    ]
    return make_cache_key("llm", model or "", (temperature, max_tokens, serialised), {})


def _provider_rate_limit(provider_name: str) -> tuple[float, float]:
    rate = float(os.environ.get(f"LLM_RATE_{provider_name.upper()}", _LLM_DEFAULT_RATE))
    burst = float(os.environ.get(f"LLM_BURST_{provider_name.upper()}", _LLM_DEFAULT_BURST))
    return rate, burst


# ---------------------------------------------------------------------------
# Langfuse — optional LLM observability
# ---------------------------------------------------------------------------

_langfuse: Any = None
_langfuse_checked: bool = False


def _get_langfuse() -> Any | None:  # noqa: ANN401
    """Return a shared Langfuse client, or None if not configured."""
    global _langfuse, _langfuse_checked  # noqa: PLW0603
    if _langfuse_checked:
        return _langfuse
    _langfuse_checked = True
    pk = os.environ.get("LANGFUSE_PUBLIC_KEY", "")
    sk = os.environ.get("LANGFUSE_SECRET_KEY", "")
    if not pk or not sk:
        return None
    try:
        from langfuse import Langfuse  # noqa: PLC0415

        _langfuse = Langfuse(
            public_key=pk,
            secret_key=sk,
            host=os.environ.get("LANGFUSE_HOST", "https://cloud.langfuse.com"),
        )
        logger.info(
            "Langfuse tracing enabled (host=%s)",
            os.environ.get("LANGFUSE_HOST", "https://cloud.langfuse.com"),
        )
    except Exception as exc:  # noqa: BLE001
        logger.debug("Langfuse unavailable: %s", exc)
    return _langfuse


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

        # ----- S4-2: response cache check (only for deterministic prompts) -----
        cache_enabled = (
            kwargs.pop("use_cache", True) and temperature < 0.7 and not kwargs.get("stream", False)
        )
        cache_key = None
        if cache_enabled:
            try:
                from core.cache import cache_manager

                cache_key = _llm_cache_key(messages, temperature, max_tokens, kwargs.get("model"))
                cached = cache_manager.get(cache_key)
                if cached is not None and isinstance(cached, dict):
                    logger.info("LLM cache HIT (%s)", cache_key[:12])
                    return LLMResponse(
                        content=cached.get("content", ""),
                        provider=cached.get("provider", "cache"),
                        model=cached.get("model", ""),
                        usage=cached.get("usage", {}),
                        latency_ms=0.0,
                        raw=None,
                    )
            except Exception as exc:  # noqa: BLE001
                logger.debug("llm cache lookup failed: %s", exc)
                cache_key = None

        lf = _get_langfuse()
        trace = (
            lf.trace(
                name="llm.generate",
                input={
                    "messages": [{"role": m.role, "content": m.content[:500]} for m in messages]
                },
            )
            if lf
            else None
        )

        last_error: Exception | None = None
        for provider in providers:
            generation = (
                trace.generation(
                    name=provider.name,
                    model=getattr(provider, "model", provider.name),
                    model_parameters={"temperature": temperature, "max_tokens": max_tokens},
                    input=[{"role": m.role, "content": m.content} for m in messages],
                )
                if trace
                else None
            )
            try:
                # ----- S4-4: per-provider token-bucket rate limit -----
                try:
                    from core.rate_limiter import get_bucket

                    rate, burst = _provider_rate_limit(provider.name)
                    bucket = get_bucket(f"llm:{provider.name}", rate=rate, capacity=burst)
                    if not bucket.wait(timeout=30.0):
                        logger.warning(
                            "rate limit timeout for %s (>30s) — failing over", provider.name
                        )
                        last_error = LLMRateLimitError(
                            "local rate limit timeout", provider=provider.name
                        )
                        if generation:
                            generation.end(level="WARNING", status_message="rate-limit-local")
                        continue
                except Exception as exc:  # noqa: BLE001
                    logger.debug("rate limiter unavailable: %s", exc)

                t0 = time.perf_counter()
                response = provider.generate(
                    _headroom_compress(messages),
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs,
                )
                latency = (time.perf_counter() - t0) * 1000
                response.latency_ms = latency
                self._record_success(provider.name, latency)

                # ----- S4-2: write-through to response cache -----
                if cache_enabled and cache_key is not None:
                    try:
                        from core.cache import cache_manager

                        cache_manager.set(
                            cache_key,
                            {
                                "content": response.content,
                                "provider": response.provider,
                                "model": response.model,
                                "usage": getattr(response, "usage", {}) or {},
                            },
                            ttl=_LLM_CACHE_TTL,
                        )
                    except Exception as exc:  # noqa: BLE001
                        logger.debug("llm cache write failed: %s", exc)

                if generation:
                    generation.end(
                        output=response.content,
                        usage={"input": response.input_tokens, "output": response.output_tokens},
                    )
                if trace:
                    trace.update(
                        output=response.content[:500],
                        metadata={
                            "provider": response.provider,
                            "model": response.model,
                            "latency_ms": round(latency, 1),
                        },
                    )

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
                if generation:
                    generation.end(level="ERROR", status_message=str(e))
                last_error = e
                continue

            except LLMRateLimitError as e:
                logger.warning("Rate limit for %s: %s", provider.name, e)
                self._record_error(provider.name, e)
                if generation:
                    generation.end(level="WARNING", status_message=str(e))
                last_error = e
                continue

            except LLMError as e:
                logger.warning("LLM error from %s: %s", provider.name, e)
                self._record_error(provider.name, e)
                if generation:
                    generation.end(level="ERROR", status_message=str(e))
                last_error = e
                if e.retryable:
                    continue
                # Non-retryable LLM errors
                break

            except Exception as e:
                logger.warning("Unexpected error from %s: %s", provider.name, e)
                self._record_error(provider.name, e)
                if generation:
                    generation.end(level="ERROR", status_message=str(e))
                last_error = e
                continue

        if trace:
            trace.update(level="ERROR", status_message=f"All providers failed. Last: {last_error}")
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

        lf = _get_langfuse()
        trace = (
            lf.trace(
                name="llm.stream",
                input={
                    "messages": [{"role": m.role, "content": m.content[:500]} for m in messages]
                },
            )
            if lf
            else None
        )

        last_error: Exception | None = None
        for provider in providers:
            generation = (
                trace.generation(
                    name=provider.name,
                    model=getattr(provider, "model", provider.name),
                    model_parameters={"temperature": temperature, "max_tokens": max_tokens},
                    input=[{"role": m.role, "content": m.content} for m in messages],
                )
                if trace
                else None
            )
            try:
                t0 = time.perf_counter()
                token_count = 0
                chunks: list[str] = []
                for token in provider.stream(
                    messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs,
                ):
                    token_count += 1
                    chunks.append(token)
                    yield token

                latency = (time.perf_counter() - t0) * 1000
                self._record_success(provider.name, latency)

                if generation:
                    output_text = "".join(chunks)
                    generation.end(output=output_text, usage={"output": token_count})
                if trace:
                    trace.update(
                        metadata={
                            "provider": provider.name,
                            "tokens": token_count,
                            "latency_ms": round(latency, 1),
                        }
                    )

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
                if generation:
                    generation.end(level="ERROR", status_message=str(e))
                last_error = e
                continue

            except (LLMRateLimitError, LLMError) as e:
                self._record_error(provider.name, e)
                if generation:
                    generation.end(level="WARNING", status_message=str(e))
                last_error = e
                continue

            except Exception as e:
                self._record_error(provider.name, e)
                if generation:
                    generation.end(level="ERROR", status_message=str(e))
                last_error = e
                continue

        if trace:
            trace.update(level="ERROR", status_message=f"All providers failed. Last: {last_error}")
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

# Sprint 16 (S16-11): single-provider mode. When FINPILOT_LLM_SINGLE_PROVIDER is set
# (e.g. "claude" or "groq" or "gemini") the router loads only that provider and the
# Groq → Claude → Gemini failover chain is disabled. Falls back to multi-provider
# when unset, "all", or "0".
_SINGLE_PROVIDER = os.environ.get("FINPILOT_LLM_SINGLE_PROVIDER", "claude").strip().lower()


def _should_load(provider_name: str) -> bool:
    if _SINGLE_PROVIDER in ("", "all", "0", "false", "off"):
        return True
    return provider_name == _SINGLE_PROVIDER


def get_router() -> LLMRouter:
    """Get (or create) the global LLM router with all configured providers.

    Default (Sprint 16): single-provider mode pinned to Claude via
    ``FINPILOT_LLM_SINGLE_PROVIDER=claude``. Set to "all" to restore the
    Groq → Claude → Gemini failover chain.
    """
    global _router_instance
    if _router_instance is not None:
        return _router_instance

    router = LLMRouter()

    if _should_load("groq"):
        try:
            from llm.groq_provider import GroqProvider

            router.add_provider(GroqProvider())
        except Exception as e:
            logger.debug("Could not init Groq provider: %s", e)

    if _should_load("claude"):
        try:
            from llm.claude_provider import ClaudeProvider

            router.add_provider(ClaudeProvider())
        except Exception as e:
            logger.debug("Could not init Claude provider: %s", e)

    if _should_load("gemini"):
        try:
            from llm.gemini_provider import GeminiProvider

            router.add_provider(GeminiProvider())
        except Exception as e:
            logger.debug("Could not init Gemini provider: %s", e)

    if _SINGLE_PROVIDER not in ("", "all", "0", "false", "off"):
        logger.info("LLM router: single-provider mode = %s", _SINGLE_PROVIDER)

    _router_instance = router
    return router


def reset_router() -> None:
    """Reset the global router (for testing or reconfiguration)."""
    global _router_instance
    _router_instance = None
