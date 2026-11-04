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

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from api.middleware.auth import require_admin, require_auth
from api.middleware.rate_limiter import limiter
from api.services.finsense_release import FinSenseReleaseError, load_catalog
from auth.tokens import TokenPayload

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
@router.get("/status", dependencies=[Depends(require_admin)])
def academy_status() -> dict[str, Any]:
    """Akademi sağlık özeti: yayınlanmış ders sayısı, domain dağılımı, bekleyen iş."""
    try:
        return _get_orch().system_status()
    except Exception as exc:  # noqa: BLE001
        logger.warning("[academy] status failed (%s)", type(exc).__name__)
        raise HTTPException(status_code=503, detail="academy status unavailable") from exc


@router.get("/dashboard/{user_id}")
def academy_dashboard(
    user_id: str,
    authenticated_user: TokenPayload = Depends(require_auth),
) -> dict[str, Any]:
    """Kullanıcıya özel pano: streak, sıradaki dersler, günlük kart, zayıf noktalar."""
    if user_id != authenticated_user.sub:
        raise HTTPException(status_code=404, detail="dashboard not found")
    try:
        return _get_orch().get_user_dashboard(user_id)
    except Exception as exc:  # noqa: BLE001
        logger.warning("[academy] dashboard failed (%s)", type(exc).__name__)
        raise HTTPException(status_code=503, detail="dashboard unavailable") from exc


@router.get("/catalog")
def academy_canonical_catalog(locale: str = "tr") -> dict[str, Any]:
    """Return one locale from the verified active FinSense release."""
    if locale not in {"tr", "en", "de"}:
        raise HTTPException(status_code=422, detail="unsupported lesson locale")
    try:
        return load_catalog(locale)
    except FinSenseReleaseError as exc:
        logger.warning("[academy] canonical catalog unavailable (%s)", type(exc).__name__)
        raise HTTPException(status_code=503, detail="canonical lesson catalog unavailable") from exc
    except Exception as exc:  # noqa: BLE001
        logger.warning("[academy] canonical catalog failed (%s)", type(exc).__name__)
        raise HTTPException(status_code=503, detail="canonical lesson catalog unavailable") from exc


@router.get("/lesson/{lesson_id}")
def academy_lesson(lesson_id: str) -> dict[str, Any]:
    """Legacy SQLite content is not a canonical public release source."""
    raise HTTPException(status_code=503, detail="canonical lesson catalog unavailable")


# ─────────────────────────────────────────────────────────────────────────────
# User flow
# ─────────────────────────────────────────────────────────────────────────────
@router.post("/onboard")
def academy_onboard(
    req: OnboardRequest,
    authenticated_user: TokenPayload = Depends(require_auth),
) -> dict[str, Any]:
    """Yeni kullanıcı onboarding'i: profil + ilk öğrenme yolu."""
    if req.user_id != authenticated_user.sub:
        raise HTTPException(status_code=403, detail="not authorized for this user")
    try:
        return _get_orch().onboard_user(req.user_id, req.answers)
    except Exception as exc:  # noqa: BLE001
        logger.warning("[academy] onboard failed (%s)", type(exc).__name__)
        raise HTTPException(status_code=500, detail="onboarding failed") from exc


# ─────────────────────────────────────────────────────────────────────────────
# Admin / manual triggers (otonomi scheduler'dadır; bunlar manuel tetik)
# ─────────────────────────────────────────────────────────────────────────────
@router.post("/generate", dependencies=[Depends(require_admin)])
@limiter.limit("60/minute")
def academy_generate(request: Request, req: GenerateRequest) -> dict[str, Any]:
    """Tek bir dersi hemen üret (bloklayıcı). LLM backend'i ortam değişkenine bağlı."""
    try:
        result = _get_orch().generate_lesson_now(
            domain=req.domain,
            module=req.module,
            title=req.title,
            difficulty=req.difficulty,
        )
        if not result.get("success"):
            raise HTTPException(status_code=422, detail="generation failed")
        return result
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.warning("[academy] generate failed (%s)", type(exc).__name__)
        raise HTTPException(status_code=500, detail="generation unavailable") from exc


@router.post("/seed", dependencies=[Depends(require_admin)])
@limiter.limit("60/minute")
def academy_seed(request: Request) -> dict[str, Any]:
    """Domain'ler için başlangıç derslerini üretir (idempotent — varsa atlar)."""
    try:
        return _get_orch().seed_starter_content()
    except Exception as exc:  # noqa: BLE001
        logger.warning("[academy] seed failed (%s)", type(exc).__name__)
        raise HTTPException(status_code=500, detail="seed unavailable") from exc


@router.post("/run/daily", dependencies=[Depends(require_admin)])
@limiter.limit("60/minute")
def academy_run_daily(request: Request) -> dict[str, Any]:
    """Günlük döngüyü manuel tetikle: boşluk tespiti → üretim → kalite denetimi."""
    try:
        return _get_orch().run_daily()
    except Exception as exc:  # noqa: BLE001
        logger.warning("[academy] run_daily failed (%s)", type(exc).__name__)
        raise HTTPException(status_code=500, detail="daily run unavailable") from exc
