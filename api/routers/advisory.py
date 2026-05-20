"""Advisory router — 15 AI danışman agent'ı REST API olarak expose eder.

Endpoints:
    GET  /advisory/          → Mevcut tüm danışmanları listele
    GET  /advisory/{name}    → Belirli bir danışmanın bilgilerini getir
    POST /advisory/{name}    → Danışmana soru sor (LLM çağrısı, auth gerekli)
"""

from __future__ import annotations

import logging

from agents.advisory import advisory_agent_for, list_advisory_keys
from agents.base import AgentContext
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/advisory", tags=["advisory"])

_ADVISOR_META: dict[str, dict[str, str]] = {
    "cto": {"role": "CTO", "description": "Mimari, altyapı, teknik kararlar"},
    "cpo": {"role": "CPO", "description": "Ürün stratejisi, roadmap, kullanıcı deneyimi"},
    "cmo": {"role": "CMO", "description": "Marka, büyüme, müşteri edinimi"},
    "senior_dev": {"role": "Senior Developer", "description": "Kod kalitesi, tasarım pattern'leri"},
    "frontend_dev": {
        "role": "Frontend Developer",
        "description": "Next.js, React, UI/UX, performans",
    },
    "ai_ml_dev": {"role": "AI/ML Developer", "description": "Model seçimi, eğitim, fine-tuning"},
    "devops": {"role": "DevOps Engineer", "description": "Docker, CI/CD, izleme, ölçeklendirme"},
    "growth_marketer": {
        "role": "Growth Marketer",
        "description": "Aktivasyon, retention, A/B testi",
    },
    "content_strategist": {
        "role": "Content Strategist",
        "description": "Blog, sosyal medya, eğitim içerikleri",
    },
    "biz_dev": {
        "role": "Business Development",
        "description": "Ortaklıklar, API entegrasyonları, iş modeli",
    },
    "competitive_intel": {
        "role": "Competitive Intelligence",
        "description": "Pazar analizi, rakip izleme",
    },
    "qa_test": {
        "role": "QA/Test Engineer",
        "description": "Test stratejisi, otomasyon, hata önleme",
    },
    "code_review": {"role": "Code Reviewer", "description": "Güvenlik, performans, okunabilirlik"},
    "pm": {
        "role": "Project Manager",
        "description": "Sprint planlama, önceliklendirme, risk yönetimi",
    },
    "customer_success": {
        "role": "Customer Success",
        "description": "Kullanıcı geri bildirimi, destek, churn azaltma",
    },
}


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------


class AdvisoryRequest(BaseModel):
    question: str = Field(
        ..., min_length=3, max_length=2000, description="Danışmana sorulacak soru"
    )
    context_str: str = Field(
        default="",
        max_length=4000,
        description="İsteğe bağlı bağlam bilgisi (piyasa verisi, kod parçası, vb.)",
    )
    symbols: list[str] = Field(
        default_factory=list,
        description="İlgili semboller (isteğe bağlı)",
    )


class AdvisorInfo(BaseModel):
    name: str
    role: str
    description: str


class AdvisoryResponse(BaseModel):
    advisor: str
    role: str
    question: str
    advice: str
    provider: str
    latency_ms: float
    success: bool


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/", response_model=list[AdvisorInfo], summary="Mevcut danışmanları listele")
def list_advisors() -> list[AdvisorInfo]:
    """15 advisory agent'ın listesini döndürür (auth gerektirmez)."""
    return [
        AdvisorInfo(
            name=key,
            role=_ADVISOR_META.get(key, {}).get("role", key),
            description=_ADVISOR_META.get(key, {}).get("description", ""),
        )
        for key in list_advisory_keys()
    ]


@router.get("/{name}", response_model=AdvisorInfo, summary="Danışman bilgilerini getir")
def get_advisor(name: str) -> AdvisorInfo:
    """Belirli bir danışmanın rol ve açıklamasını döndürür (auth gerektirmez)."""
    keys = list_advisory_keys()
    if name.lower() not in keys:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Danışman '{name}' bulunamadı. Mevcut: {keys}",
        )
    meta = _ADVISOR_META.get(name.lower(), {})
    return AdvisorInfo(
        name=name.lower(),
        role=meta.get("role", name),
        description=meta.get("description", ""),
    )


@router.post(
    "/{name}",
    response_model=AdvisoryResponse,
    summary="Danışmana soru sor",
)
def ask_advisor(name: str, body: AdvisoryRequest) -> AdvisoryResponse:
    """Belirtilen danışman agent'a LLM üzerinden soru sorar (JWT auth gerekli)."""
    try:
        agent = advisory_agent_for(name)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    ctx = AgentContext(symbols=body.symbols or [])

    result = agent.run(ctx, question=body.question, context_str=body.context_str)

    if not result.success:
        logger.error("Advisory agent '%s' failed: %s", name, result.error)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Danışman yanıt üretemedi: {result.error}",
        )

    data = result.data or {}
    return AdvisoryResponse(
        advisor=name.lower(),
        role=data.get("role", name),
        question=data.get("question", body.question),
        advice=data.get("advice", ""),
        provider=data.get("provider", "unknown"),
        latency_ms=data.get("latency_ms", 0.0),
        success=True,
    )
