"""
Finance Academy — Bağımsız FastAPI Uygulaması
===============================================
Borsa ana projesinden tamamen bağımsız çalışır.
Port: 8001 (Borsa API'si 8000'de çalışıyor)

Çalıştır:
    cd Borsa/FinanceAcademy
    uvicorn app:app --port 8001 --reload

Veya:
    python app.py
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

# FinanceAcademy klasörünü Python path'e ekle (Borsa'ya dokunmadan)
sys.path.insert(0, str(Path(__file__).parent))

from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="FinPilot Finance Academy",
    description="Self-evolving financial education system",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Lazy orchestrator
_orch = None


def orch():
    global _orch
    if _orch is None:
        from academy.orchestrator import AcademyOrchestrator

        _orch = AcademyOrchestrator()
    return _orch


# ─── Request models ────────────────────────────────────────────────────────────


class OnboardRequest(BaseModel):
    user_id: str
    answers: dict[str, Any]


class ProgressRequest(BaseModel):
    user_id: str
    lesson_id: str
    quiz_score: float | None = Field(None, ge=0, le=1)
    time_spent_sec: int | None = None
    feedback_rating: int | None = Field(None, ge=1, le=5)
    feedback_text: str | None = None
    feedback_tags: list[str] = []
    scroll_depth: float | None = None


class GenerateRequest(BaseModel):
    domain: str
    module: str
    title: str
    difficulty: str = "intermediate"


# ─── Endpoints ────────────────────────────────────────────────────────────────


@app.get("/")
def root():
    return {"app": "Finance Academy", "version": "1.0.0", "docs": "/docs", "status": "/status"}


@app.get("/status")
def status():
    return orch().system_status()


@app.get("/domains")
def domains():
    from academy.domains import DOMAINS
    from academy.models import LessonRepository

    stats = LessonRepository().stats()
    return {
        "domains": [{**d, "lesson_count": stats["by_domain"].get(d["slug"], 0)} for d in DOMAINS]
    }


@app.get("/lessons")
def list_lessons(
    domain: str = Query(...),
    difficulty: str | None = None,
    status: str = "published",
):
    from academy.models import LessonRepository

    lessons = LessonRepository().list_by_domain(domain, status=status)
    if difficulty:
        lessons = [l for l in lessons if l.difficulty == difficulty]
    return {
        "domain": domain,
        "count": len(lessons),
        "lessons": [
            {
                "id": l.id,
                "title": l.title,
                "module": l.module,
                "difficulty": l.difficulty,
                "estimated_minutes": l.estimated_minutes,
            }
            for l in lessons
        ],
    }


@app.get("/lessons/{lesson_id}")
def get_lesson(lesson_id: str):
    from academy.models import LessonComponentRepository, LessonRepository

    lesson = LessonRepository().get(lesson_id)
    if not lesson:
        raise HTTPException(404, f"'{lesson_id}' bulunamadı")
    comps = LessonComponentRepository().get_for_lesson(lesson_id)
    return {
        "id": lesson.id,
        "domain": lesson.domain,
        "module": lesson.module,
        "title": lesson.title,
        "difficulty": lesson.difficulty,
        "estimated_minutes": lesson.estimated_minutes,
        "content": lesson.content,
        "key_takeaways": lesson.key_takeaways,
        "misconceptions": lesson.misconceptions,
        "real_example": lesson.real_example,
        "related_lessons": lesson.related_lessons,
        "pedagogy_score": lesson.pedagogy_score,
        "version": lesson.version,
        "quizzes": [c["content"] for c in comps if c["type"] == "quiz"],
        "flashcards": [c["content"] for c in comps if c["type"] == "flashcard"],
        "case_studies": [c["content"] for c in comps if c["type"] == "case_study"],
        "updated_at": lesson.updated_at,
    }


@app.get("/onboarding-questions")
def onboarding_questions():
    from academy.agents.personalization import ONBOARDING_QUESTIONS

    return {"questions": ONBOARDING_QUESTIONS}


@app.post("/onboard")
def onboard(req: OnboardRequest):
    return orch().onboard_user(req.user_id, req.answers)


@app.get("/dashboard/{user_id}")
def dashboard(user_id: str):
    return orch().get_user_dashboard(user_id)


@app.get("/daily-card/{user_id}")
def daily_card(user_id: str):
    from academy.agents.personalization import PersonalizationAgent

    return PersonalizationAgent().get_daily_card(user_id)


@app.post("/progress")
def progress(req: ProgressRequest):
    from academy.models import UserProgressRepository

    UserProgressRepository().upsert(
        user_id=req.user_id,
        lesson_id=req.lesson_id,
        quiz_score=req.quiz_score,
        time_spent_sec=req.time_spent_sec,
        feedback_rating=req.feedback_rating,
        feedback_text=req.feedback_text,
        feedback_tags=req.feedback_tags,
        scroll_depth=req.scroll_depth,
    )
    if req.feedback_rating and req.feedback_rating <= 2:
        from academy.agents.content_updater import ContentUpdaterAgent

        ContentUpdaterAgent().update_lesson_from_feedback(
            req.lesson_id, f"Kullanıcı {req.feedback_rating}/5 verdi"
        )
    return {"success": True}


@app.post("/generate")
def generate(req: GenerateRequest):
    return orch().generate_lesson_now(
        domain=req.domain, module=req.module, title=req.title, difficulty=req.difficulty
    )


@app.get("/report")
def report():
    r = orch().analytics.generate_weekly_report()
    return {"report": r, "formatted": orch().analytics.format_report_text(r)}


@app.post("/run-daily")
def run_daily():
    return orch().run_daily()


@app.post("/seed")
def seed():
    """12 domain için başlangıç içeriğini yükle."""
    return orch().seed_starter_content()


# ─── CLI entry point ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    print("\n🎓 Finance Academy başlatılıyor — http://localhost:8001")
    print("   API Docs: http://localhost:8001/docs\n")
    uvicorn.run("app:app", host="0.0.0.0", port=8001, reload=True)
