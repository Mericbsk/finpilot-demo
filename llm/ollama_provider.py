"""
Ollama LLM Provider (local-first)
=================================

Yerel Ollama sunucusuna konuşan, LLMProvider ABC'ye uyumlu sağlayıcı.
`requests` kütüphanesini kullanır (proje zaten gerektiriyor).

Ortam değişkenleri:
  FINPILOT_OLLAMA_MODEL   (vars: "qwen2.5:3b")  — üretim modeli
  FINPILOT_OLLAMA_URL     (vars: "http://localhost:11434")
  FINPILOT_OLLAMA_TIMEOUT (saniye, vars: 300)   — CPU'da uzun üretim için

Etkinleştirme: FINPILOT_LLM_BACKEND=ollama (bkz. llm.router.get_router).
"""

from __future__ import annotations

import json
import logging
import os
from collections.abc import Generator
from typing import Any

import requests

from llm.base import (
    LLMError,
    LLMMessage,
    LLMProvider,
    LLMResponse,
)

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "qwen2.5:3b"
DEFAULT_URL = "http://localhost:11434"
DEFAULT_TIMEOUT = 300


class OllamaProvider(LLMProvider):
    """Yerel Ollama sağlayıcısı (/api/chat + /api/tags)."""

    name = "ollama"

    def __init__(
        self,
        model: str | None = None,
        base_url: str | None = None,
        timeout: int | None = None,
    ) -> None:
        self._model = model or os.getenv("FINPILOT_OLLAMA_MODEL", DEFAULT_MODEL)
        self._base_url = (base_url or os.getenv("FINPILOT_OLLAMA_URL", DEFAULT_URL)).rstrip("/")
        self._timeout = int(timeout or os.getenv("FINPILOT_OLLAMA_TIMEOUT", str(DEFAULT_TIMEOUT)))

    # ──────────────────────────────────────────────────────────────────────
    def is_available(self) -> bool:
        """Ollama sunucusu ayakta ve erişilebilir mi? (istisna fırlatmaz)"""
        try:
            resp = requests.get(f"{self._base_url}/api/tags", timeout=5)
            return 200 <= resp.status_code < 300
        except Exception as exc:  # noqa: BLE001
            logger.debug("[ollama] erişilemiyor (%s): %s", self._base_url, exc)
            return False

    # ──────────────────────────────────────────────────────────────────────
    def _post(self, path: str, payload: dict, stream: bool) -> requests.Response:
        resp = requests.post(
            f"{self._base_url}{path}",
            json=payload,
            stream=stream,
            timeout=self._timeout,
        )
        resp.raise_for_status()
        return resp

    @staticmethod
    def _to_api_messages(messages: list[LLMMessage]) -> list[dict]:
        # m.role is LLMRole(StrEnum); .value -> "system"|"user"|"assistant"
        return [{"role": m.role.value, "content": m.content} for m in messages]

    # ──────────────────────────────────────────────────────────────────────
    def generate(
        self,
        messages: list[LLMMessage],
        *,
        temperature: float = 0.3,
        max_tokens: int = 2048,
        **kwargs: Any,
    ) -> LLMResponse:
        """Tek-seferlik üretim — Ollama /api/chat (stream=false)."""
        model = kwargs.pop("model", self._model)
        payload = {
            "model": model,
            "messages": self._to_api_messages(messages),
            "stream": False,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }
        try:
            resp = self._post("/api/chat", payload, stream=False)
            body = resp.json()
        except requests.HTTPError as exc:
            detail = ""
            try:
                detail = exc.response.text[:200] if exc.response is not None else ""
            except Exception:  # noqa: BLE001
                pass
            raise LLMError(
                f"Ollama HTTP {exc.response.status_code if exc.response else '?'}: {detail}",
                provider=self.name,
                retryable=(exc.response is not None and exc.response.status_code >= 500),
            ) from exc
        except Exception as exc:  # noqa: BLE001 — timeout / connreset / json
            raise LLMError(str(exc), provider=self.name, retryable=True) from exc

        content = (body.get("message") or {}).get("content", "") or ""
        usage = {
            "input_tokens": int(body.get("prompt_eval_count", 0) or 0),
            "output_tokens": int(body.get("eval_count", 0) or 0),
        }
        return LLMResponse(
            content=content,
            provider=self.name,
            model=model,
            usage=usage,
            raw=body,
        )

    # ──────────────────────────────────────────────────────────────────────
    def stream(
        self,
        messages: list[LLMMessage],
        *,
        temperature: float = 0.3,
        max_tokens: int = 2048,
        **kwargs: Any,
    ) -> Generator[str, None, None]:
        """Akışlı üretim — Ollama /api/chat (stream=true), satır-bazlı JSON."""
        model = kwargs.pop("model", self._model)
        payload = {
            "model": model,
            "messages": self._to_api_messages(messages),
            "stream": True,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }
        try:
            resp = self._post("/api/chat", payload, stream=True)
            for raw_line in resp.iter_lines():
                if not raw_line:
                    continue
                line = raw_line.decode("utf-8") if isinstance(raw_line, bytes) else raw_line
                obj = json.loads(line)
                delta = (obj.get("message") or {}).get("content", "")
                if delta:
                    yield delta
                if obj.get("done"):
                    break
        except Exception as exc:  # noqa: BLE001
            raise LLMError(str(exc), provider=self.name, retryable=True) from exc
