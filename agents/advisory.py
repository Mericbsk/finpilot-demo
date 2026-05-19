"""FinPilot Advisory Agents — 15 LLM danışman agent (tek dosyada).

Her danışman, kendi uzmanlık alanında LLM üzerinden tavsiye üretir.
Tüm advisory agent'lar aynı pattern'ı izler:
    - ROLE: Rolü tanımlar
    - SYSTEM: Sistem prompt'u
    - run(context, question=...) → AgentResult

Kullanım:
    from agents.advisory import CTOAgent, CMOAgent, advisory_agent_for

    result = CTOAgent().run(ctx, question="Redis mi MongoDB mi?")
    agent  = advisory_agent_for("cmo")
    result = agent.run(ctx, question="Fiyatlama stratejisi ne olmalı?")
"""

from __future__ import annotations

import logging

from agents.base import AgentContext, AgentResult, BaseAgent

logger = logging.getLogger(__name__)

_DEFAULT_MAX_TOKENS = 500
_DEFAULT_TEMPERATURE = 0.4


def _ask_llm(system_prompt: str, question: str, context_str: str = "") -> tuple[str, str, float]:
    """LLM'e sor, (yanıt, provider, latency_ms) döndür."""
    import time

    try:
        from llm import get_router
        from llm.base import LLMMessage, LLMRole
    except ImportError as exc:
        raise ImportError(f"LLM modülü bulunamadı: {exc}") from exc

    router = get_router()
    messages = [LLMMessage(role=LLMRole.SYSTEM, content=system_prompt)]
    if context_str:
        messages.append(
            LLMMessage(role=LLMRole.USER, content=f"Bağlam:\n{context_str}\n\nSoru: {question}")
        )
    else:
        messages.append(LLMMessage(role=LLMRole.USER, content=question))

    t0 = time.perf_counter()
    response = router.generate_messages(
        messages=messages,
        temperature=_DEFAULT_TEMPERATURE,
        max_tokens=_DEFAULT_MAX_TOKENS,
    )
    latency = (time.perf_counter() - t0) * 1000
    provider = getattr(response, "provider", "unknown")
    return response.content, provider, round(latency, 1)


class _AdvisoryBase(BaseAgent):
    """Tüm danışman agent'ların temel sınıfı."""

    ROLE: str = "Danışman"
    SYSTEM: str = "Sen FinPilot'un danışmanısın."

    def run(self, context: AgentContext, **kwargs: object) -> AgentResult:
        import time

        t0 = time.perf_counter()
        question: str = str(kwargs.get("question", "FinPilot hakkında ne düşünüyorsun?"))
        ctx_str: str = str(kwargs.get("context_str", ""))

        try:
            answer, provider, latency = _ask_llm(self.SYSTEM, question, ctx_str)
        except Exception as exc:
            return AgentResult(
                agent=self.name,
                success=False,
                error=str(exc),
                duration_ms=(time.perf_counter() - t0) * 1000,
            )

        return AgentResult(
            agent=self.name,
            success=True,
            data={
                "role": self.ROLE,
                "question": question,
                "advice": answer,
                "provider": provider,
                "latency_ms": latency,
            },
            duration_ms=(time.perf_counter() - t0) * 1000,
        )


# ---------------------------------------------------------------------------
# Management Layer
# ---------------------------------------------------------------------------


class CTOAgent(_AdvisoryBase):
    """Baş Teknoloji Sorumlusu — mimari, altyapı, teknik kararlar."""

    name = "cto"
    ROLE = "CTO"
    SYSTEM = (
        "Sen FinPilot'un CTO'susun. "
        "Yazılım mimarisi, altyapı, güvenlik ve teknik borç konularında "
        "pratik, uygulanabilir öneriler verirsin. "
        "Yanıtlarını Türkçe ve maddeler halinde ver."
    )


class CPOAgent(_AdvisoryBase):
    """Baş Ürün Sorumlusu — ürün stratejisi, roadmap, kullanıcı deneyimi."""

    name = "cpo"
    ROLE = "CPO"
    SYSTEM = (
        "Sen FinPilot'un CPO'susun. "
        "Ürün stratejisi, özellik önceliklendirmesi, kullanıcı deneyimi ve "
        "pazar uyumu konularında kararlar verirsin. "
        "Yanıtlarını Türkçe, net ve aksiyon odaklı ver."
    )


class CMOAgent(_AdvisoryBase):
    """Baş Pazarlama Sorumlusu — marka, büyüme, müşteri edinimi."""

    name = "cmo"
    ROLE = "CMO"
    SYSTEM = (
        "Sen FinPilot'un CMO'susun. "
        "Marka stratejisi, kullanıcı edinimi, içerik pazarlaması ve "
        "büyüme kanalları konularında uzman görüşü verirsin. "
        "Yanıtlarını Türkçe ve ölçülebilir hedefler içerecek şekilde ver."
    )


# ---------------------------------------------------------------------------
# Engineering Layer
# ---------------------------------------------------------------------------


class SeniorDevAgent(_AdvisoryBase):
    """Kıdemli Geliştirici — kod kalitesi, tasarım pattern'leri, code review."""

    name = "senior_dev"
    ROLE = "Senior Developer"
    SYSTEM = (
        "Sen FinPilot'un kıdemli back-end geliştiricisisin. "
        "Python, FastAPI, veri yapıları, tasarım kalıpları ve "
        "temiz kod prensipleri konularında rehberlik edersin. "
        "Kod örnekleri verirken kısa tut."
    )


class FrontendDevAgent(_AdvisoryBase):
    """Frontend Geliştirici — Next.js, React, UI/UX, performans."""

    name = "frontend_dev"
    ROLE = "Frontend Developer"
    SYSTEM = (
        "Sen FinPilot'un kıdemli frontend geliştiricisisin. "
        "Next.js, React, TypeScript, Tailwind ve web performansı konularında "
        "pratik tavsiyeler verirsin. "
        "Yanıtlarını Türkçe ver."
    )


class AIMLDevAgent(_AdvisoryBase):
    """AI/ML Geliştirici — model seçimi, eğitim, fine-tuning, inference."""

    name = "ai_ml_dev"
    ROLE = "AI/ML Developer"
    SYSTEM = (
        "Sen FinPilot'un AI/ML geliştiricisisin. "
        "Makine öğrenimi, derin öğrenme, model optimizasyonu, "
        "özellik mühendisliği ve LLM entegrasyonu konularında "
        "teknik rehberlik edersin. "
        "Yanıtlarını Türkçe, somut ve uygulanabilir biçimde ver."
    )


class DevOpsAgent(_AdvisoryBase):
    """DevOps Mühendisi — Docker, CI/CD, izleme, ölçeklendirme."""

    name = "devops"
    ROLE = "DevOps Engineer"
    SYSTEM = (
        "Sen FinPilot'un DevOps mühendisisin. "
        "Docker, Kubernetes, CI/CD pipeline, log izleme, "
        "güvenlik ve altyapı maliyeti konularında "
        "operasyonel tavsiyeler verirsin. "
        "Yanıtlarını Türkçe ver."
    )


# ---------------------------------------------------------------------------
# Growth Layer
# ---------------------------------------------------------------------------


class GrowthMarketerAgent(_AdvisoryBase):
    """Growth Marketer — kullanıcı aktivasyonu, retention, A/B testi."""

    name = "growth_marketer"
    ROLE = "Growth Marketer"
    SYSTEM = (
        "Sen FinPilot'un growth marketerısın. "
        "Kullanıcı aktivasyonu, onboarding, retention ve viral büyüme "
        "konularında veriye dayalı öneriler verirsin. "
        "Yanıtlarını Türkçe ver."
    )


class ContentStrategistAgent(_AdvisoryBase):
    """İçerik Stratejisti — blog, sosyal medya, eğitim içerikleri."""

    name = "content_strategist"
    ROLE = "Content Strategist"
    SYSTEM = (
        "Sen FinPilot'un içerik stratejistisin. "
        "Fintech alanında içerik planlaması, SEO, sosyal medya stratejisi "
        "ve eğitici içerik oluşturma konularında rehberlik edersin. "
        "Yanıtlarını Türkçe ver."
    )


class BusinessDevAgent(_AdvisoryBase):
    """İş Geliştirme — ortaklıklar, API entegrasyonları, iş modeli."""

    name = "biz_dev"
    ROLE = "Business Development"
    SYSTEM = (
        "Sen FinPilot'un iş geliştirme müdürüsün. "
        "Stratejik ortaklıklar, gelir modelleri, API monetizasyonu "
        "ve pazar genişleme fırsatları konularında tavsiye verirsin. "
        "Yanıtlarını Türkçe ver."
    )


class CompetitiveIntelAgent(_AdvisoryBase):
    """Rekabet İstihbaratı — pazar analizi, rakip izleme."""

    name = "competitive_intel"
    ROLE = "Competitive Intelligence"
    SYSTEM = (
        "Sen FinPilot'un rekabet istihbarat analistisin. "
        "Fintech rakipleri, pazar trendleri ve diferansiyasyon "
        "stratejileri konularında analiz yaparsın. "
        "Yanıtlarını Türkçe ver."
    )


# ---------------------------------------------------------------------------
# Quality Layer
# ---------------------------------------------------------------------------


class QATestAgent(_AdvisoryBase):
    """QA / Test Mühendisi — test stratejisi, otomasyon, hata önleme."""

    name = "qa_test"
    ROLE = "QA/Test Engineer"
    SYSTEM = (
        "Sen FinPilot'un kıdemli QA mühendisisin. "
        "Test stratejisi, otomasyon, regresyon ve performans testleri "
        "konularında rehberlik edersin. "
        "Yanıtlarını Türkçe ver."
    )


class CodeReviewAgent(_AdvisoryBase):
    """Code Review Uzmanı — güvenlik, performans, okunabilirlik."""

    name = "code_review"
    ROLE = "Code Reviewer"
    SYSTEM = (
        "Sen FinPilot'un kod inceleme uzmanısın. "
        "Güvenlik açıkları, performans sorunları, okunabilirlik "
        "ve best practice ihlalleri konularında kapsamlı inceleme yaparsın. "
        "Yanıtlarını Türkçe, madde madde ver."
    )


# ---------------------------------------------------------------------------
# Ops Layer
# ---------------------------------------------------------------------------


class PMAgent(_AdvisoryBase):
    """Proje Yöneticisi — sprint planlama, önceliklendirme, risk yönetimi."""

    name = "pm"
    ROLE = "Project Manager"
    SYSTEM = (
        "Sen FinPilot'un proje yöneticisisin. "
        "Sprint planlaması, görev önceliklendirme, ekip koordinasyonu "
        "ve proje risk yönetimi konularında rehberlik edersin. "
        "Yanıtlarını Türkçe ver."
    )


class CustomerSuccessAgent(_AdvisoryBase):
    """Müşteri Başarısı — kullanıcı geri bildirimi, destek, churn azaltma."""

    name = "customer_success"
    ROLE = "Customer Success"
    SYSTEM = (
        "Sen FinPilot'un müşteri başarısı uzmanısın. "
        "Kullanıcı sorunları, onboarding iyileştirme, NPS artırma "
        "ve churn azaltma konularında tavsiyeler verirsin. "
        "Yanıtlarını Türkçe ver."
    )


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

_ADVISORY_REGISTRY: dict[str, type[_AdvisoryBase]] = {
    "cto": CTOAgent,
    "cpo": CPOAgent,
    "cmo": CMOAgent,
    "senior_dev": SeniorDevAgent,
    "frontend_dev": FrontendDevAgent,
    "ai_ml_dev": AIMLDevAgent,
    "devops": DevOpsAgent,
    "growth_marketer": GrowthMarketerAgent,
    "content_strategist": ContentStrategistAgent,
    "biz_dev": BusinessDevAgent,
    "competitive_intel": CompetitiveIntelAgent,
    "qa_test": QATestAgent,
    "code_review": CodeReviewAgent,
    "pm": PMAgent,
    "customer_success": CustomerSuccessAgent,
}


def advisory_agent_for(key: str) -> _AdvisoryBase:
    """Anahtar adına göre danışman agent instance'ı döndür.

    Örnek: advisory_agent_for("cto") → CTOAgent()
    """
    cls = _ADVISORY_REGISTRY.get(key.lower())
    if cls is None:
        raise ValueError(f"Bilinmeyen danışman: '{key}'. Mevcut: {list(_ADVISORY_REGISTRY)}")
    return cls()


def list_advisory_keys() -> list[str]:
    """Tüm danışman anahtarlarını döndür."""
    return list(_ADVISORY_REGISTRY.keys())


__all__ = [
    "CTOAgent",
    "CPOAgent",
    "CMOAgent",
    "SeniorDevAgent",
    "FrontendDevAgent",
    "AIMLDevAgent",
    "DevOpsAgent",
    "GrowthMarketerAgent",
    "ContentStrategistAgent",
    "BusinessDevAgent",
    "CompetitiveIntelAgent",
    "QATestAgent",
    "CodeReviewAgent",
    "PMAgent",
    "CustomerSuccessAgent",
    "advisory_agent_for",
    "list_advisory_keys",
]
