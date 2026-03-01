"""
LLM Base — Abstract provider interface and shared types.

All LLM providers must implement the LLMProvider ABC.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Generator


class LLMRole(str, Enum):
    """Message roles for chat completion APIs."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass
class LLMMessage:
    """A single message in a chat conversation."""

    role: LLMRole
    content: str


@dataclass
class LLMResponse:
    """Standardised response from any LLM provider."""

    content: str
    provider: str
    model: str
    usage: dict[str, int] = field(default_factory=dict)
    latency_ms: float = 0.0
    cached: bool = False
    raw: Any = None

    @property
    def input_tokens(self) -> int:
        return self.usage.get("input_tokens", 0)

    @property
    def output_tokens(self) -> int:
        return self.usage.get("output_tokens", 0)


class LLMError(Exception):
    """Base exception for LLM operations."""

    def __init__(self, message: str, provider: str = "unknown", retryable: bool = False):
        super().__init__(message)
        self.provider = provider
        self.retryable = retryable


class LLMRateLimitError(LLMError):
    """Rate limit hit — always retryable."""

    def __init__(self, message: str, provider: str = "unknown", retry_after: float = 0):
        super().__init__(message, provider=provider, retryable=True)
        self.retry_after = retry_after


class LLMAuthError(LLMError):
    """Authentication / API-key error — never retryable."""

    def __init__(self, message: str, provider: str = "unknown"):
        super().__init__(message, provider=provider, retryable=False)


class LLMProvider(ABC):
    """Abstract base class for all LLM providers.

    Subclasses must implement:
    - generate()  — single-shot generation
    - stream()    — streaming generation (token-by-token)
    - is_available() — check if provider is configured & reachable
    """

    name: str = "base"

    @abstractmethod
    def generate(
        self,
        messages: list[LLMMessage],
        *,
        temperature: float = 0.3,
        max_tokens: int = 2048,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate a complete response (blocking)."""
        ...

    @abstractmethod
    def stream(
        self,
        messages: list[LLMMessage],
        *,
        temperature: float = 0.3,
        max_tokens: int = 2048,
        **kwargs: Any,
    ) -> Generator[str, None, None]:
        """Yield response tokens one-by-one (streaming)."""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is configured and can serve requests."""
        ...

    def _timed_generate(
        self,
        messages: list[LLMMessage],
        *,
        temperature: float = 0.3,
        max_tokens: int = 2048,
        **kwargs: Any,
    ) -> LLMResponse:
        """Wrapper that records latency. Subclasses use generate() internally."""
        t0 = time.perf_counter()
        response = self.generate(
            messages, temperature=temperature, max_tokens=max_tokens, **kwargs
        )
        response.latency_ms = (time.perf_counter() - t0) * 1000
        return response

    @staticmethod
    def _make_messages(
        prompt: str,
        system: str = "You are a senior financial analyst. Answer in Markdown.",
    ) -> list[LLMMessage]:
        """Convenience: convert a plain prompt string into [system, user] messages."""
        return [
            LLMMessage(role=LLMRole.SYSTEM, content=system),
            LLMMessage(role=LLMRole.USER, content=prompt),
        ]
