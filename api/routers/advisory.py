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
from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field

from api.middleware.auth import require_auth
from auth.tokens import TokenPayload
from core.advisory_memory import (
    append_message,
    clear_history,
    format_history_as_context,
    get_history,
)

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
    history_used: int = 0


class HistoryMessage(BaseModel):
    role: str
    content: str
    ts: float


class HistoryResponse(BaseModel):
    advisor: str
    user_id: str
    messages: list[HistoryMessage]


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
def ask_advisor(
    name: str,
    body: AdvisoryRequest,
    user: TokenPayload = Depends(require_auth),
) -> AdvisoryResponse:
    """Belirtilen danışman agent'a LLM üzerinden soru sorar (JWT auth gerekli).

    Sliding-window memory: son 10 mesaj (user+assistant) Redis'te tutulur ve
    agent çağrısının context'ine enjekte edilir.
    """
    advisor_key = name.lower()
    try:
        agent = advisory_agent_for(advisor_key)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    user_id = user.user_id
    history = get_history(advisor_key, user_id, limit=10, chronological=True)
    history_block = format_history_as_context(history)
    enriched_context = (
        f"{history_block}\n\n{body.context_str}".strip() if history_block else body.context_str
    )

    ctx = AgentContext(symbols=body.symbols or [])
    result = agent.run(ctx, question=body.question, context_str=enriched_context)

    if not result.success:
        logger.error("Advisory agent '%s' failed: %s", advisor_key, result.error)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Danışman yanıt üretemedi: {result.error}",
        )

    data = result.data or {}
    advice = data.get("advice", "")

    # Persist exchange to sliding-window memory (best-effort)
    try:
        append_message(advisor_key, user_id, "user", body.question)
        append_message(
            advisor_key,
            user_id,
            "assistant",
            advice,
            extra={"provider": data.get("provider", "unknown")},
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Advisory: memory append failed for %s/%s: %s", advisor_key, user_id, exc)

    return AdvisoryResponse(
        advisor=advisor_key,
        role=data.get("role", name),
        question=data.get("question", body.question),
        advice=advice,
        provider=data.get("provider", "unknown"),
        latency_ms=data.get("latency_ms", 0.0),
        success=True,
        history_used=len(history),
    )


@router.get(
    "/{name}/history",
    response_model=HistoryResponse,
    summary="Danışmanla geçmiş konuşmayı getir",
)
def get_advisor_history(
    name: str,
    limit: int = 10,
    user: TokenPayload = Depends(require_auth),
) -> HistoryResponse:
    """Aktif kullanıcının (advisor,user) sliding-window mesaj geçmişini döner."""
    advisor_key = name.lower()
    if advisor_key not in list_advisory_keys():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Danışman '{name}' bulunamadı.",
        )
    history = get_history(advisor_key, user.user_id, limit=max(1, min(limit, 50)))
    return HistoryResponse(
        advisor=advisor_key,
        user_id=user.user_id,
        messages=[HistoryMessage(**m) for m in history],
    )


@router.delete(
    "/{name}/history",
    summary="Danışman konuşma geçmişini sil",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def delete_advisor_history(
    name: str,
    user: TokenPayload = Depends(require_auth),
) -> Response:
    """Aktif kullanıcının (advisor,user) konuşma geçmişini siler."""
    advisor_key = name.lower()
    if advisor_key not in list_advisory_keys():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Danışman '{name}' bulunamadı.",
        )
    clear_history(advisor_key, user.user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
