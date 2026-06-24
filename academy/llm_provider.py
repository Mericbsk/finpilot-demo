"""
Finance Academy — LLM Provider Abstraction
===========================================
Akademiyi bulut LLM router'ından AYIRIR. Aynı içerik-üretim hattı, ortam
değişkeniyle seçilen farklı arka uçlara karşı çalışabilir:

  ACADEMY_LLM_BACKEND:
    "ollama" (varsayılan) → yerel Ollama HTTP sunucusu (CPU-only uyumlu)
    "cloud"               → mevcut llm.get_router() (FinPilot bulut sağlayıcıları)
    "mock"                → deterministik çevrimdışı stub (test / model yok)

Tüm sağlayıcılar şu arayüzü sunar:
    generate(prompt, *, system=None, language="tr", **kw) -> LLMReply
LLMReply.content (str) mevcut agent'ların beklediği biçimle uyumludur
(agent'lar `resp.content if hasattr(resp, "content") else str(resp)` kullanır).

Tasarım notları:
  - Sadece standart kütüphane (urllib) kullanılır → yeni bağımlılık yok,
    kullanıcının makinesinde ek kurulum gerektirmez.
  - Yerel model erişilemezse bulut router'a, o da yoksa None'a düşülür;
    None dönünce agent'lar kendi mevcut mock davranışına geçer (güvenli).
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class LLMReply:
    """Mevcut agent'ların `.content` erişimiyle uyumlu minimal yanıt sarmalayıcı."""

    content: str


class AcademyLLMProvider:
    """Tüm akademi LLM sağlayıcıları için ortak sözleşme."""

    name = "base"

    def available(self) -> bool:  # pragma: no cover - trivial
        return True

    def generate(
        self,
        prompt: str,
        *,
        system: str | None = None,
        language: str = "tr",
        **kwargs,
    ) -> LLMReply:
        raise NotImplementedError


# ─────────────────────────────────────────────────────────────────────────────
# 1) Yerel Ollama sağlayıcısı (CPU-only dostu)
# ─────────────────────────────────────────────────────────────────────────────
class OllamaProvider(AcademyLLMProvider):
    """Yerel Ollama sunucusuna stdlib urllib ile bağlanır.

    Ortam değişkenleri:
        ACADEMY_LLM_MODEL    (vars: "qwen2.5:7b")
        ACADEMY_OLLAMA_URL   (vars: "http://localhost:11434")
        ACADEMY_LLM_TIMEOUT  (saniye, vars: 600 — CPU'da uzun üretim için)
    """

    name = "ollama"

    def __init__(
        self,
        model: str | None = None,
        base_url: str | None = None,
        timeout: int | None = None,
    ) -> None:
        self.model = model or os.getenv("ACADEMY_LLM_MODEL", "qwen2.5:7b")
        self.base_url = (
            base_url or os.getenv("ACADEMY_OLLAMA_URL", "http://localhost:11434")
        ).rstrip("/")
        self.timeout = int(timeout or os.getenv("ACADEMY_LLM_TIMEOUT", "600"))

    def available(self) -> bool:
        """Ollama sunucusu ayakta ve erişilebilir mi?"""
        try:
            import requests  # noqa: PLC0415

            resp = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return 200 <= resp.status_code < 300
        except Exception as e:  # noqa: BLE001
            logger.warning("[academy.llm] Ollama erişilemiyor (%s): %s", self.base_url, e)
            return False

    def generate(
        self,
        prompt: str,
        *,
        system: str | None = None,
        language: str = "tr",
        temperature: float = 0.3,
        **kwargs,
    ) -> LLMReply:
        full_prompt = prompt if system is None else f"{system}\n\n{prompt}"
        payload = {
            "model": self.model,
            "prompt": full_prompt,
            "stream": False,
            "options": {"temperature": temperature},
        }
        import requests  # noqa: PLC0415

        resp = requests.post(
            f"{self.base_url}/api/generate",
            json=payload,
            timeout=self.timeout,
        )
        resp.raise_for_status()
        body = resp.json()
        return LLMReply(content=body.get("response", ""))


# ─────────────────────────────────────────────────────────────────────────────
# 2) Bulut router sağlayıcısı (geriye dönük uyumluluk)
# ─────────────────────────────────────────────────────────────────────────────
class CloudRouterProvider(AcademyLLMProvider):
    """Mevcut FinPilot llm.get_router() sarmalayıcısı."""

    name = "cloud"

    def __init__(self) -> None:
        from llm import get_router

        self._router = get_router()

    def available(self) -> bool:
        return self._router is not None

    def generate(
        self,
        prompt: str,
        *,
        system: str | None = None,
        language: str = "tr",
        **kwargs,
    ) -> LLMReply:
        if system is not None:
            resp = self._router.generate(prompt, system=system, language=language, **kwargs)
        else:
            resp = self._router.generate(prompt, language=language, **kwargs)
        content = resp.content if hasattr(resp, "content") else str(resp)
        return LLMReply(content=content)


# ─────────────────────────────────────────────────────────────────────────────
# 3) Mock sağlayıcı (çevrimdışı test / model yokken)
# ─────────────────────────────────────────────────────────────────────────────
_MOCK_JSON = json.dumps(
    {
        "title": "Mock Ders (Yerel Sağlayıcı Testi)",
        "content": (
            "Bu ders, llm_provider enjeksiyon hattını uçtan uca doğrulamak için üretilmiş "
            "deterministik bir mock içeriktir. Amacı, bulut bağımsız çalışan akademinin "
            "üretim → kalite denetimi → yayın döngüsünün doğru bağlandığını kanıtlamaktır. "
            "Gerçek üretimde bu metnin yerini, yerel modelin (Ollama) küratörlü kaynak "
            "külliyatından RAG ile ürettiği akademik içerik alır. Finansal okuryazarlıkta "
            "bir kavram anlatılırken önce tanım verilir, sonra gerçek bir piyasa örneğiyle "
            "somutlaştırılır, ardından yaygın yanlış anlamalar düzeltilir ve son olarak "
            "öğrenci küçük bir testle pekiştirilir. Bu mock ders, o pedagojik sıranın "
            "iskeletini taşır; içerik uzunluğu, kilit çıkarımlar, quiz ve flashcard "
            "sayıları kalite kapısının sezgisel eşiklerini geçecek biçimde ayarlanmıştır. "
            "Böylece backend=mock ile bile yayın yolu (published) gözlemlenebilir. "
            "ACADEMY_LLM_BACKEND=ollama ayarlandığında aynı hat gerçek yerel modeli kullanır."
        ),
        "key_takeaways": ["Hat çalışıyor", "Sağlayıcı takılabilir", "Bulut bağımsız"],
        "misconceptions": ["Mock içerik gerçek bilgi değildir"],
        "real_example": {"ticker": "AAPL", "context": "Örnek bağlam"},
        "estimated_minutes": 5,
        "quiz_questions": [
            {
                "question": "llm_provider neyi sağlar?",
                "options": ["A) Takılabilir LLM", "B) Hiçbir şey", "C) Grafik", "D) Veritabanı"],
                "correct": "A",
                "explanation": "Sağlayıcı, bulut/yerel/mock arka uçlarını soyutlar.",
            }
        ],
        "flashcards": [
            {"front": "Enjeksiyon dikişi nedir?", "back": "Bulut↔yerel takılabilir LLM noktası"},
        ],
        "pedagogy_notes": "Mock — sadece hat doğrulaması içindir.",
    },
    ensure_ascii=False,
)


# Kalite denetimi (review) istemlerini tanımak için işaretler — bu kelimeler
# yalnızca QualityGuard'ın review prompt'unda geçer, ders üretiminde geçmez.
_REVIEW_MARKERS = (
    "seviye_uygunlugu",
    "kavramin_butunlugu",
    "kalite denetçisi",
    "değerlendir",
)

_MOCK_REVIEW_JSON = json.dumps(
    {
        "scores": {
            "dogruluk": 9,
            "seviye_uygunlugu": 8,
            "pedagojik_akis": 8,
            "ornek_kalitesi": 8,
            "test_kalitesi": 8,
            "dil_akiciligi": 9,
            "kavramin_butunlugu": 8,
        },
        "average": 8.3,
        "decision": "APPROVED",
        "issues": [],
        "strengths": ["Net tanım", "Pedagojik sıra doğru", "Örnek somut"],
        "revision_notes": "",
    },
    ensure_ascii=False,
)


class MockProvider(AcademyLLMProvider):
    """Çevrimdışı test sağlayıcısı.

    İstem bir kalite denetimi (review) ise geçerli bir REVIEW JSON'u, aksi halde
    geçerli bir DERS JSON'u döndürür. Böylece backend=mock ile üretim + denetim +
    yayın yolu uçtan uca test edilebilir.
    """

    name = "mock"

    def generate(
        self,
        prompt: str,
        *,
        system: str | None = None,
        language: str = "tr",
        **kwargs,
    ) -> LLMReply:
        probe = f"{system or ''}\n{prompt}".lower()
        if any(marker in probe for marker in _REVIEW_MARKERS):
            return LLMReply(content=_MOCK_REVIEW_JSON)
        return LLMReply(content=_MOCK_JSON)


# ─────────────────────────────────────────────────────────────────────────────
# Fabrika
# ─────────────────────────────────────────────────────────────────────────────
def get_academy_provider() -> AcademyLLMProvider | None:
    """Ortam değişkenine göre uygun sağlayıcıyı döndürür.

    Erişilemezse zarif şekilde düşer:
        ollama → (yoksa) cloud → (yoksa) None
    None dönünce agent'lar mevcut mock davranışına geçer.
    """
    backend = os.getenv("ACADEMY_LLM_BACKEND", "ollama").lower()

    try:
        if backend == "mock":
            logger.info("[academy.llm] Backend: mock")
            return MockProvider()

        if backend == "cloud":
            provider = CloudRouterProvider()
            if provider.available():
                logger.info("[academy.llm] Backend: cloud router")
                return provider
            logger.warning("[academy.llm] Bulut router kullanılamıyor")
            return None

        # Varsayılan: ollama (yerel)
        provider = OllamaProvider()
        if provider.available():
            logger.info(
                "[academy.llm] Backend: ollama (model=%s, url=%s)",
                provider.model,
                provider.base_url,
            )
            return provider

        # Yerel yoksa buluta düş
        logger.warning("[academy.llm] Ollama yok — bulut router'a düşülüyor")
        try:
            cloud = CloudRouterProvider()
            if cloud.available():
                return cloud
        except Exception as e:  # noqa: BLE001
            logger.warning("[academy.llm] Bulut fallback da başarısız: %s", e)
        return None

    except Exception as e:  # noqa: BLE001
        logger.warning("[academy.llm] Sağlayıcı başlatılamadı: %s", e)
        return None
