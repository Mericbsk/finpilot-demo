"""
Mock LLM Provider (offline / test)
==================================

Deterministik, ağ gerektirmeyen sağlayıcı. FINPILOT_LLM_BACKEND=mock ile
etkinleşir. Çıktısı, bull/bear researcher agent'larının beklediği JSON şemasına
uyumludur (arguments / strength_score / key_catalysts), böylece tüm shortlist
zenginleştirme yolu yerel model olmadan uçtan uca test edilebilir.
"""

from __future__ import annotations

import json
from collections.abc import Generator
from typing import Any

from llm.base import LLMMessage, LLMProvider, LLMResponse

_MOCK_PAYLOAD = json.dumps(
    {
        "arguments": [
            "Mock argüman 1 (yerel model bağlı değil)",
            "Mock argüman 2",
        ],
        "strength_score": 0.5,
        "key_catalysts": ["mock-katalizör"],
        "summary": "Bu, llm backend=mock çıktısıdır; gerçek üretim için backend=ollama.",
    },
    ensure_ascii=False,
)


class MockProvider(LLMProvider):
    """Her zaman geçerli, sabit JSON döndüren çevrimdışı sağlayıcı."""

    name = "mock"

    def is_available(self) -> bool:
        return True

    def generate(
        self,
        messages: list[LLMMessage],
        *,
        temperature: float = 0.3,
        max_tokens: int = 2048,
        **kwargs: Any,
    ) -> LLMResponse:
        return LLMResponse(
            content=_MOCK_PAYLOAD,
            provider=self.name,
            model="mock",
            usage={"input_tokens": 0, "output_tokens": 0},
            raw=None,
        )

    def stream(
        self,
        messages: list[LLMMessage],
        *,
        temperature: float = 0.3,
        max_tokens: int = 2048,
        **kwargs: Any,
    ) -> Generator[str, None, None]:
        yield _MOCK_PAYLOAD
