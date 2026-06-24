"""
AGENT 1 — Content Generator Agent
===================================
Yeni ders, flashcard, quiz ve case study üretir.
LLM'i pedagojik şablonla yönlendirir, JSON çıktısını doğrular.

Tetiklenme:
  - Haftalık schedule
  - Gap Detector sinyali
  - Trend Scout sinyali
  - API isteği (kullanıcı konuyu aradı ama bulunamadı)
"""

from __future__ import annotations

import json
import logging
import re
import time
from datetime import datetime, timedelta

from academy.domains import DOMAIN_BY_SLUG
from academy.models import (
    AgentLogRepository,
    ContentJob,
    ContentJobRepository,
    Lesson,
    LessonComponent,
    LessonComponentRepository,
    LessonRepository,
)

logger = logging.getLogger(__name__)

AGENT_NAME = "content_generator"

# ─────────────────────────────────────────────────────────────────────────────
# LLM SYSTEM PROMPT
# ─────────────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """Sen FinPilot Finance Academy için Türkçe finansal eğitim içerikleri üreten
uzman bir pedagoji ve finans yazarısın.

Ürettiğin her içerik:
1. Finansal olarak doğru ve güncel olmalı
2. Hedef zorluk seviyesine uygun dil kullanmalı (beginner=sade, advanced=teknik)
3. Gerçek piyasa örnekleri içermeli (ABD borsası veya Türk piyasaları)
4. Pedagojik sırayı takip etmeli: kavram → örnek → yanlış anlama → test
5. Öğrencinin "neden önemli?" sorusunu yanıtlamalı

Formatı kesinlikle JSON olarak ver. Markdown veya açıklama EKLEME, sadece JSON döndür."""

LESSON_TEMPLATE = """Şu konuda bir Finance Academy dersi üret:

Alan (Domain): {domain_name}
Modül: {module}
Başlık: {title}
Zorluk: {difficulty}
Hedef öğrenci: {audience}

JSON formatı (tam olarak bu yapıyı kullan):
{{
  "title": "...",
  "content": "... (Markdown, min 400 kelime, max 800 kelime) ...",
  "key_takeaways": ["...", "...", "..."],
  "misconceptions": ["...", "..."],
  "real_example": {{"ticker": "...", "context": "..."}},
  "estimated_minutes": 10,
  "quiz_questions": [
    {{
      "question": "...",
      "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
      "correct": "A",
      "explanation": "..."
    }}
  ],
  "flashcards": [
    {{"front": "...", "back": "..."}},
    {{"front": "...", "back": "..."}}
  ],
  "pedagogy_notes": "Bu derste hangi öğrenme prensipleri uygulandı?"
}}"""

AUDIENCE_MAP = {
    "beginner": "Hiç yatırım deneyimi olmayan, finansal terimleri bilmeyen kişiler",
    "intermediate": "Temel borsa bilgisi olan, alım-satım yapmaya başlamış yatırımcılar",
    "advanced": "Aktif trader, teknik analiz bilen, derinlemesine analiz yapan kişiler",
}

# ─────────────────────────────────────────────────────────────────────────────
# GENERATOR
# ─────────────────────────────────────────────────────────────────────────────


class ContentGeneratorAgent:
    """Generates Finance Academy lessons using the FinPilot LLM router."""

    def __init__(self):
        self.lesson_repo = LessonRepository()
        self.component_repo = LessonComponentRepository()
        self.job_repo = ContentJobRepository()
        self.log_repo = AgentLogRepository()
        self._llm = None

    @property
    def llm(self):
        if self._llm is None:
            try:
                from academy.llm_provider import get_academy_provider

                self._llm = get_academy_provider()
            except Exception as e:
                logger.warning("LLM provider unavailable: %s — using mock mode", e)
        return self._llm

    # ──────────────────────────────────────────────────────────────────────
    # PUBLIC API
    # ──────────────────────────────────────────────────────────────────────

    def generate_lesson(
        self,
        domain_slug: str,
        module: str,
        title: str,
        difficulty: str = "intermediate",
        lesson_id: str | None = None,
    ) -> Lesson | None:
        """Generate a single lesson and persist it."""
        t0 = time.perf_counter()
        domain = DOMAIN_BY_SLUG.get(domain_slug)
        if not domain:
            logger.error("Unknown domain slug: %s", domain_slug)
            return None

        # Build lesson ID if not provided
        if not lesson_id:
            slug = re.sub(r"[^a-z0-9]+", "-", title.lower())[:30]
            prefix = "".join(w[0].upper() for w in domain_slug.split("-"))[:3]
            lesson_id = f"{prefix}-{slug}"

        # Check for existing
        existing = self.lesson_repo.get(lesson_id)
        if existing and existing.status == "published":
            logger.info("Lesson %s already published, skipping", lesson_id)
            return existing

        prompt = LESSON_TEMPLATE.format(
            domain_name=domain["name"],
            module=module,
            title=title,
            difficulty=difficulty,
            audience=AUDIENCE_MAP.get(difficulty, AUDIENCE_MAP["intermediate"]),
        )

        raw = self._call_llm(SYSTEM_PROMPT, prompt)
        if not raw:
            return None

        parsed = self._parse_lesson_json(raw)
        if not parsed:
            return None

        now = datetime.utcnow().isoformat()
        review_at = (datetime.utcnow() + timedelta(days=90)).isoformat()

        lesson = Lesson(
            id=lesson_id,
            domain=domain_slug,
            domain_id=domain["id"],
            module=module,
            title=parsed.get("title", title),
            difficulty=difficulty,
            content=parsed.get("content", ""),
            estimated_minutes=parsed.get("estimated_minutes", 10),
            key_takeaways=parsed.get("key_takeaways", []),
            misconceptions=parsed.get("misconceptions", []),
            real_example=parsed.get("real_example", {}),
            related_lessons=[],
            status="draft",  # Quality Guard onaylayana kadar draft
            created_at=now,
            updated_at=now,
            next_review_at=review_at,
        )
        self.lesson_repo.save(lesson)

        # Save components
        order = 0
        for q in parsed.get("quiz_questions", []):
            self.component_repo.save(
                LessonComponent(
                    lesson_id=lesson_id,
                    type="quiz",
                    content=q,
                    order_idx=order,
                )
            )
            order += 1

        for card in parsed.get("flashcards", []):
            self.component_repo.save(
                LessonComponent(
                    lesson_id=lesson_id,
                    type="flashcard",
                    content=card,
                    order_idx=order,
                )
            )
            order += 1

        duration_ms = (time.perf_counter() - t0) * 1000
        self.log_repo.log(
            agent_name=AGENT_NAME,
            action="generate_lesson",
            input_summary=f"{domain_slug}/{module}: {title} [{difficulty}]",
            output_summary=f"lesson_id={lesson_id}, {len(parsed.get('quiz_questions',[]))} quizzes, "
            f"{len(parsed.get('flashcards',[]))} flashcards",
            duration_ms=duration_ms,
        )
        logger.info("[%s] Generated lesson: %s (%.0f ms)", AGENT_NAME, lesson_id, duration_ms)
        return lesson

    def process_job(self, job: dict) -> bool:
        """Process a content_jobs row. Returns True on success."""
        job_id = job["id"]
        payload = json.loads(job.get("payload") or "{}")
        self.job_repo.update_status(job_id, "running")

        try:
            lesson = self.generate_lesson(
                domain_slug=payload["domain"],
                module=payload["module"],
                title=payload["title"],
                difficulty=payload.get("difficulty", "intermediate"),
                lesson_id=payload.get("lesson_id"),
            )
            if lesson:
                self.job_repo.update_status(job_id, "done", result={"lesson_id": lesson.id})
                return True
            self.job_repo.update_status(job_id, "failed", error="Generation returned None")
            return False
        except Exception as exc:
            self.job_repo.update_status(job_id, "failed", error=str(exc))
            logger.error("[%s] Job %s failed: %s", AGENT_NAME, job_id, exc)
            return False

    def enqueue(
        self,
        domain: str,
        module: str,
        title: str,
        difficulty: str = "intermediate",
        priority: int = 2,
    ) -> int:
        """Add a generation task to the job queue."""
        return self.job_repo.enqueue(
            ContentJob(
                agent_name=AGENT_NAME,
                job_type="generate",
                payload={
                    "domain": domain,
                    "module": module,
                    "title": title,
                    "difficulty": difficulty,
                },
                priority=priority,
            )
        )

    # ──────────────────────────────────────────────────────────────────────
    # PRIVATE HELPERS
    # ──────────────────────────────────────────────────────────────────────

    def _call_llm(self, system: str, user: str) -> str | None:
        """Call LLM and return raw text, or None on failure."""
        if self.llm is None:
            logger.warning("[%s] LLM unavailable — returning mock content", AGENT_NAME)
            return self._mock_lesson_json()
        try:
            full_prompt = f"{system}\n\n{user}"
            response = self.llm.generate(full_prompt, language="tr")
            return response.content if hasattr(response, "content") else str(response)
        except Exception as e:
            logger.error("[%s] LLM call failed: %s", AGENT_NAME, e)
            return None

    def _parse_lesson_json(self, raw: str) -> dict | None:
        """Extract JSON from LLM output (may be wrapped in markdown code fences)."""
        # Strip markdown code fences if present
        text = re.sub(r"```(?:json)?\n?", "", raw).strip()
        # Find first { ... }
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            logger.error("[%s] No JSON found in LLM output", AGENT_NAME)
            return None
        try:
            return json.loads(match.group())
        except json.JSONDecodeError as e:
            logger.error("[%s] JSON parse error: %s", AGENT_NAME, e)
            return None

    @staticmethod
    def _mock_lesson_json() -> str:
        """Return a minimal valid lesson JSON for offline/dev mode."""
        return json.dumps(
            {
                "title": "Mock Ders (LLM Bağlantısı Yok)",
                "content": "Bu bir mock içeriktir. LLM bağlantısı kurulduğunda gerçek içerik üretilecek.",
                "key_takeaways": ["Anahtar çıkarım 1", "Anahtar çıkarım 2"],
                "misconceptions": ["Yaygın yanlış anlama örneği"],
                "real_example": {"ticker": "AAPL", "context": "Apple örnek bağlamı"},
                "estimated_minutes": 10,
                "quiz_questions": [
                    {
                        "question": "Örnek soru?",
                        "options": ["A) Seçenek", "B) Seçenek", "C) Seçenek", "D) Seçenek"],
                        "correct": "A",
                        "explanation": "Açıklama",
                    }
                ],
                "flashcards": [
                    {"front": "Kavram", "back": "Tanım"},
                ],
                "pedagogy_notes": "Mock — spaced repetition + active recall",
            }
        )
