"""
Claude (Anthropic) LLM Provider
================================

Wraps the Anthropic Python SDK (claude-sonnet-4-20250514).

Reads API key from:
  1. Constructor parameter
  2. Streamlit secrets (st.secrets["ANTHROPIC_API_KEY"])
  3. Environment variable ANTHROPIC_API_KEY
"""

from __future__ import annotations

import logging
import os
from collections.abc import Generator
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

DEFAULT_MODEL = "claude-sonnet-4-20250514"


def _resolve_api_key(explicit_key: str | None = None) -> str | None:
    """Resolve Anthropic API key in priority order."""
    if explicit_key:
        return explicit_key
    try:
        import streamlit as st

        key = st.secrets.get("ANTHROPIC_API_KEY", "")
        if key:
            return key
    except Exception:
        pass
    return os.getenv("ANTHROPIC_API_KEY", "") or None


class ClaudeProvider(LLMProvider):
    """Anthropic Claude provider — advanced reasoning & long context."""

    name = "claude"

    def __init__(
        self,
        api_key: str | None = None,
        model: str = DEFAULT_MODEL,
    ):
        self._api_key = _resolve_api_key(api_key)
        self._model = model
        self._client = None

    def _get_client(self):
        """Lazy-init Anthropic client."""
        if self._client is None:
            try:
                from anthropic import Anthropic
            except ImportError as exc:
                raise LLMError(
                    "anthropic package not installed. Run: pip install anthropic",
                    provider=self.name,
                ) from exc

            if not self._api_key:
                raise LLMAuthError(
                    "ANTHROPIC_API_KEY not configured.",
                    provider=self.name,
                )
            self._client = Anthropic(api_key=self._api_key)
        return self._client

    def is_available(self) -> bool:
        """Check if Claude is configured."""
        try:
            from anthropic import Anthropic  # noqa: F401

            return bool(_resolve_api_key(self._api_key))
        except ImportError:
            return False

    def generate(
        self,
        messages: list[LLMMessage],
        *,
        temperature: float = 0.3,
        max_tokens: int = 2048,
        **kwargs: Any,
    ) -> LLMResponse:
        """Single-shot generation via Anthropic messages API."""
        client = self._get_client()
        model = kwargs.pop("model", self._model)

        # Anthropic separates system from messages
        system_text = ""
        api_messages = []
        for m in messages:
            if m.role == LLMRole.SYSTEM:
                system_text = m.content
            else:
                api_messages.append({"role": m.role.value, "content": m.content})

        # Ensure at least one user message
        if not api_messages:
            api_messages = [{"role": "user", "content": "Hello"}]

        try:
            response = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_text or "You are a senior financial analyst. Answer in Markdown.",
                messages=api_messages,
                **kwargs,
            )
        except Exception as exc:
            exc_str = str(exc).lower()
            if "rate" in exc_str or "429" in exc_str:
                raise LLMRateLimitError(str(exc), provider=self.name) from exc
            if "auth" in exc_str or "key" in exc_str or "401" in exc_str:
                raise LLMAuthError(str(exc), provider=self.name) from exc
            raise LLMError(str(exc), provider=self.name, retryable=True) from exc

        content = ""
        if response.content:
            content = "".join(block.text for block in response.content if hasattr(block, "text"))

        usage_data = {}
        if hasattr(response, "usage") and response.usage:
            usage_data = {
                "input_tokens": response.usage.input_tokens or 0,
                "output_tokens": response.usage.output_tokens or 0,
            }

        return LLMResponse(
            content=content,
            provider=self.name,
            model=model,
            usage=usage_data,
            raw=response,
        )

    def stream(
        self,
        messages: list[LLMMessage],
        *,
        temperature: float = 0.3,
        max_tokens: int = 2048,
        **kwargs: Any,
    ) -> Generator[str, None, None]:
        """Streaming generation via Anthropic — yields tokens."""
        client = self._get_client()
        model = kwargs.pop("model", self._model)

        system_text = ""
        api_messages = []
        for m in messages:
            if m.role == LLMRole.SYSTEM:
                system_text = m.content
            else:
                api_messages.append({"role": m.role.value, "content": m.content})

        if not api_messages:
            api_messages = [{"role": "user", "content": "Hello"}]

        try:
            with client.messages.stream(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_text or "You are a senior financial analyst. Answer in Markdown.",
                messages=api_messages,
                **kwargs,
            ) as stream:
                for text in stream.text_stream:
                    if text:
                        yield text
        except Exception as exc:
            exc_str = str(exc).lower()
            if "rate" in exc_str or "429" in exc_str:
                raise LLMRateLimitError(str(exc), provider=self.name) from exc
            raise LLMError(str(exc), provider=self.name, retryable=True) from exc
