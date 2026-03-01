"""
Groq LLM Provider
=================

Wraps the Groq Python SDK (llama-3.3-70b-versatile).

Reads API key from:
  1. Constructor parameter
  2. Streamlit secrets (st.secrets["GROQ_API_KEY"])
  3. Environment variable GROQ_API_KEY
"""

from __future__ import annotations

import logging
import os
from typing import Any, Generator

from llm.base import (
    LLMAuthError,
    LLMError,
    LLMMessage,
    LLMProvider,
    LLMRateLimitError,
    LLMResponse,
)

logger = logging.getLogger(__name__)

# Default model — can be overridden per-call via kwargs
DEFAULT_MODEL = "llama-3.3-70b-versatile"


def _resolve_api_key(explicit_key: str | None = None) -> str | None:
    """Resolve Groq API key in priority order."""
    if explicit_key:
        return explicit_key

    # Streamlit secrets
    try:
        import streamlit as st

        key = st.secrets.get("GROQ_API_KEY", "")
        if key:
            return key
    except Exception:
        pass

    # Environment variable
    return os.getenv("GROQ_API_KEY", "") or None


class GroqProvider(LLMProvider):
    """Groq LLM provider — fast inference on open-source models."""

    name = "groq"

    def __init__(
        self,
        api_key: str | None = None,
        model: str = DEFAULT_MODEL,
    ):
        self._api_key = _resolve_api_key(api_key)
        self._model = model
        self._client = None

    def _get_client(self):
        """Lazy-init Groq client."""
        if self._client is None:
            try:
                from groq import Groq
            except ImportError as exc:
                raise LLMError(
                    "groq package not installed. Run: pip install groq",
                    provider=self.name,
                ) from exc

            if not self._api_key:
                raise LLMAuthError(
                    "GROQ_API_KEY not configured.",
                    provider=self.name,
                )
            self._client = Groq(api_key=self._api_key)
        return self._client

    def is_available(self) -> bool:
        """Check if Groq is configured."""
        try:
            from groq import Groq  # noqa: F401

            return bool(self._api_key)
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
        """Single-shot generation via Groq chat completions."""
        client = self._get_client()
        model = kwargs.pop("model", self._model)

        api_messages = [{"role": m.role.value, "content": m.content} for m in messages]

        try:
            completion = client.chat.completions.create(
                model=model,
                messages=api_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=1,
                stream=False,
                stop=None,
                **kwargs,
            )
        except Exception as exc:
            exc_str = str(exc).lower()
            if "rate" in exc_str and "limit" in exc_str:
                raise LLMRateLimitError(str(exc), provider=self.name) from exc
            if "auth" in exc_str or "key" in exc_str or "401" in exc_str:
                raise LLMAuthError(str(exc), provider=self.name) from exc
            raise LLMError(str(exc), provider=self.name, retryable=True) from exc

        choice = completion.choices[0]
        usage_data = {}
        if hasattr(completion, "usage") and completion.usage:
            usage_data = {
                "input_tokens": completion.usage.prompt_tokens or 0,
                "output_tokens": completion.usage.completion_tokens or 0,
            }

        return LLMResponse(
            content=choice.message.content or "",
            provider=self.name,
            model=model,
            usage=usage_data,
            raw=completion,
        )

    def stream(
        self,
        messages: list[LLMMessage],
        *,
        temperature: float = 0.3,
        max_tokens: int = 2048,
        **kwargs: Any,
    ) -> Generator[str, None, None]:
        """Streaming generation via Groq — yields tokens."""
        client = self._get_client()
        model = kwargs.pop("model", self._model)

        api_messages = [{"role": m.role.value, "content": m.content} for m in messages]

        try:
            completion = client.chat.completions.create(
                model=model,
                messages=api_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=1,
                stream=True,
                **kwargs,
            )
            for chunk in completion:
                delta = chunk.choices[0].delta.content or ""
                if delta:
                    yield delta
        except Exception as exc:
            exc_str = str(exc).lower()
            if "rate" in exc_str and "limit" in exc_str:
                raise LLMRateLimitError(str(exc), provider=self.name) from exc
            raise LLMError(str(exc), provider=self.name, retryable=True) from exc
