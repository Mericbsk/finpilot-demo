"""
Google Gemini LLM Provider
===========================

Wraps the Google GenAI SDK (gemini-2.0-flash).

Reads API key from:
  1. Constructor parameter
  2. Streamlit secrets (st.secrets["GOOGLE_API_KEY"])
  3. Environment variable GOOGLE_API_KEY
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

DEFAULT_MODEL = "gemini-2.0-flash"


def _resolve_api_key(explicit_key: str | None = None) -> str | None:
    """Resolve Google API key in priority order."""
    if explicit_key:
        return explicit_key
    try:
        import streamlit as st

        key = st.secrets.get("GOOGLE_API_KEY", "")
        if key:
            return key
    except Exception:
        pass
    return os.getenv("GOOGLE_API_KEY", "") or None


class GeminiProvider(LLMProvider):
    """Google Gemini provider — fast, multimodal, generous free tier."""

    name = "gemini"

    def __init__(
        self,
        api_key: str | None = None,
        model: str = DEFAULT_MODEL,
    ):
        self._api_key = _resolve_api_key(api_key)
        self._model = model
        self._client = None

    def _get_client(self):
        """Lazy-init Google GenAI client."""
        if self._client is None:
            try:
                from google import genai
            except ImportError as exc:
                raise LLMError(
                    "google-genai package not installed. Run: pip install google-genai",
                    provider=self.name,
                ) from exc

            if not self._api_key:
                raise LLMAuthError(
                    "GOOGLE_API_KEY not configured.",
                    provider=self.name,
                )
            self._client = genai.Client(api_key=self._api_key)
        return self._client

    def is_available(self) -> bool:
        """Check if Gemini is configured."""
        try:
            from google import genai  # noqa: F401

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
        """Single-shot generation via Google GenAI."""
        client = self._get_client()
        model = kwargs.pop("model", self._model)

        from google.genai import types

        # Build config
        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )

        # Combine messages into a single prompt for Gemini
        # (Gemini's chat is content-based, but we can also use system_instruction)
        system_text = ""
        prompt_parts = []
        for m in messages:
            if m.role == LLMRole.SYSTEM:
                system_text = m.content
            else:
                prompt_parts.append(m.content)

        if system_text:
            config.system_instruction = system_text

        prompt = "\n\n".join(prompt_parts)

        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=config,
            )
        except Exception as exc:
            exc_str = str(exc).lower()
            if "quota" in exc_str or "rate" in exc_str or "429" in exc_str:
                raise LLMRateLimitError(str(exc), provider=self.name) from exc
            if "api key" in exc_str or "auth" in exc_str or "403" in exc_str:
                raise LLMAuthError(str(exc), provider=self.name) from exc
            raise LLMError(str(exc), provider=self.name, retryable=True) from exc

        content = response.text or ""

        usage_data = {}
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            um = response.usage_metadata
            usage_data = {
                "input_tokens": getattr(um, "prompt_token_count", 0) or 0,
                "output_tokens": getattr(um, "candidates_token_count", 0) or 0,
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
        """Streaming generation via Gemini — yields tokens."""
        client = self._get_client()
        model = kwargs.pop("model", self._model)

        from google.genai import types

        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )

        system_text = ""
        prompt_parts = []
        for m in messages:
            if m.role == LLMRole.SYSTEM:
                system_text = m.content
            else:
                prompt_parts.append(m.content)

        if system_text:
            config.system_instruction = system_text

        prompt = "\n\n".join(prompt_parts)

        try:
            response = client.models.generate_content_stream(
                model=model,
                contents=prompt,
                config=config,
            )
            for chunk in response:
                text = chunk.text or ""
                if text:
                    yield text
        except Exception as exc:
            exc_str = str(exc).lower()
            if "quota" in exc_str or "rate" in exc_str or "429" in exc_str:
                raise LLMRateLimitError(str(exc), provider=self.name) from exc
            raise LLMError(str(exc), provider=self.name, retryable=True) from exc
