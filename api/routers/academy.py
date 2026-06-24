"""Finance Academy router — /api/v1/academy/*

Akademinin (kendi kendini geliştiren finansal okuryazarlık sözlüğü) HTTP yüzeyi.
AcademyOrchestrator'ı sarmalar; ağır içerik üretimi scheduler tarafından arka
planda yapılır, bu uçlar çoğunlukla hazır içeriği okur (hızlı).

Tasarım:
  - Orchestrator lazy singleton'dır; router import'u ucuzdur, uygulamayı yavaşlatmaz.
  - Akademi kritik-olmayan bir alt sistemdir; hatalar uygulamayı düşürmemeli,
    bu yüzden uçlar hataları HTTP 4xx/5xx olarak sarmalar.
  - Üretim/yönetim uçları (generate, seed, run/daily) manuel tetik içindir;
    gerçek otonomi scheduler'dadır.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/academy", tags=["academy"])

# ─────────────────────────────────────────────────────────────────────────────
# Lazy singleton orchestrator
# ─────────────────────────────────────────────────────────────────────────────
_ORCH: Any = None


def _get_orch() -> Any:
    """AcademyOrchestrator'ı ilk istek anında oluştur (init_db dahil)."""
    global _ORCH
    if _ORCH is None:
        from academy.orchestrator import AcademyOrchestrator

        _ORCH = AcademyOrchestrator()
    return _ORCH


# ─────────────────────────────────────────────────────────────────────────────
# Request models
# ─────────────────────────────────────────────────────────────────────────────
class OnboardRequest(BaseModel):
    user_id: str = Field(..., description="Kullanıcı kimliği")
    answers: dict[str, Any] = Field(default_factory=dict, description="Onboarding yanıtları")


class GenerateRequest(BaseModel):
    domain: str = Field(..., description="Domain slug, örn. 'temel-finans'")
    module: str = Field(..., description="Modül adı")
    title: str = Field(..., description="Ders başlığı")
    difficulty: str = Field("intermediate", description="beginner | intermediate | advanced")


# ─────────────────────────────────────────────────────────────────────────────
# Read endpoints (hızlı — sadece DB okuması)
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/status")
def academy_status() -> dict[str, Any]:
    """Akademi sağlık özeti: yayınlanmış ders sayısı, domain dağılımı, bekleyen iş."""
    try:
        return _get_orch().system_status()
    except Exception as exc:  # noqa: BLE001
        logger.warning("[academy] status failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"academy status error: {exc}") from exc


@router.get("/dashboard/{user_id}")
def academy_dashboard(user_id: str) -> dict[str, Any]:
    """Kullanıcıya özel pano: streak, sıradaki dersler, günlük kart, zayıf noktalar."""
    try:
        return _get_orch().get_user_dashboard(user_id)
    except Exception as exc:  # noqa: BLE001
        logger.warning("[academy] dashboard failed for %s: %s", user_id, exc)
        raise HTTPException(status_code=404, detail=f"dashboard unavailable: {exc}") from exc


@router.get("/lesson/{lesson_id}")
def academy_lesson(lesson_id: str) -> dict[str, Any]:
    """Tek bir dersi (bileşenleriyle) döndürür."""
    try:
        orch = _get_orch()
        lesson = orch.lesson_repo.get(lesson_id)
        if lesson is None:
            raise HTTPException(status_code=404, detail="lesson not found")
        components = orch.generator.component_repo.get_for_lesson(lesson_id)
        return {
            "id": lesson.id,
            "title": lesson.title,
            "domain": lesson.domain,
            "difficulty": lesson.difficulty,
            "status": lesson.status,
            "content": lesson.content,
            "key_takeaways": lesson.key_takeaways,
            "estimated_minutes": lesson.estimated_minutes,
            "components": components,
        }
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.warning("[academy] lesson fetch failed for %s: %s", lesson_id, exc)
        raise HTTPException(status_code=500, detail=f"lesson error: {exc}") from exc


# ─────────────────────────────────────────────────────────────────────────────
# User flow
# ─────────────────────────────────────────────────────────────────────────────
@router.post("/onboard")
def academy_onboard(req: OnboardRequest) -> dict[str, Any]:
    """Yeni kullanıcı onboarding'i: profil + ilk öğrenme yolu."""
    try:
        return _get_orch().onboard_user(req.user_id, req.answers)
    except Exception as exc:  # noqa: BLE001
        logger.warning("[academy] onboard failed for %s: %s", req.user_id, exc)
        raise HTTPException(status_code=400, detail=f"onboard error: {exc}") from exc


# ─────────────────────────────────────────────────────────────────────────────
# Admin / manual triggers (otonomi scheduler'dadır; bunlar manuel tetik)
# ─────────────────────────────────────────────────────────────────────────────
@router.post("/generate")
def academy_generate(req: GenerateRequest) -> dict[str, Any]:
    """Tek bir dersi hemen üret (bloklayıcı). LLM backend'i ortam değişkenine bağlı."""
    try:
        result = _get_orch().generate_lesson_now(
            domain=req.domain,
            module=req.module,
            title=req.title,
            difficulty=req.difficulty,
        )
        if not result.get("success"):
            raise HTTPException(status_code=422, detail=result.get("error", "generation failed"))
        return result
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.warning("[academy] generate failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"generate error: {exc}") from exc


@router.post("/seed")
def academy_seed() -> dict[str, Any]:
    """Domain'ler için başlangıç derslerini üretir (idempotent — varsa atlar)."""
    try:
        return _get_orch().seed_starter_content()
    except Exception as exc:  # noqa: BLE001
        logger.warning("[academy] seed failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"seed error: {exc}") from exc


@router.post("/run/daily")
def academy_run_daily() -> dict[str, Any]:
    """Günlük döngüyü manuel tetikle: boşluk tespiti → üretim → kalite denetimi."""
    try:
        return _get_orch().run_daily()
    except Exception as exc:  # noqa: BLE001
        logger.warning("[academy] run_daily failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"run_daily error: {exc}") from exc
