"""
AGENT 2 — Quality Guard Agent
================================
Üretilen içeriklerin finansal doğruluğunu, pedagojik kalitesini
ve dil netliğini denetler.

Kararlar:
  APPROVED        → yayına hazır
  REVISION_NEEDED → belirli bölümler düzeltme gerektiriyor
  REJECTED        → temel sorun var, yeniden üret

Kör nokta:
  - Çok spesifik/akademik finans hatalarını hep yakalayamaz
  - Türkçe gramer sorunlarını İngilizce LLM'ler kaçırabilir
"""

from __future__ import annotations

import json
import logging
import re
import time
from datetime import datetime

from academy.models import (
    AgentLogRepository,
    Lesson,
    LessonComponentRepository,
    LessonRepository,
)

logger = logging.getLogger(__name__)
AGENT_NAME = "quality_guard"

QUALITY_SYSTEM_PROMPT = """Sen bir Finance Academy içerik kalite denetçisisin.
Görevin: sunulan finansal eğitim içeriğini aşağıdaki 7 boyutta değerlendirmek.

Değerlendirme boyutları:
1. finansal_dogruluk (0-10): Bilgiler doğru ve güncel mi?
2. seviye_uygunlugu (0-10): Dil/derinlik hedef zorluk seviyesine uygun mu?
3. pedagojik_yapi (0-10): Kavram → örnek → test sırası var mı?
4. dil_netligi (0-10): Açık, anlaşılır Türkçe mi?
5. ornek_kalitesi (0-10): Örnekler gerçekçi ve güncel mi?
6. quiz_kalitesi (0-10): Sorular ölçüyor mu, seçenekler makul mu?
7. kavramin_butunlugu (0-10): Konu tam kapanıyor mu, boşluk var mı?

Karar:
- Ortalama >= 7.5 ve herhangi bir boyut < 5 yoksa: APPROVED
- Ortalama 5-7.5 veya tek bir boyut < 5: REVISION_NEEDED
- Ortalama < 5 veya 2+ boyut < 5: REJECTED

Sadece JSON döndür."""

REVIEW_PROMPT = """Şu Finance Academy dersini değerlendir:

Başlık: {title}
Alan: {domain}
Zorluk: {difficulty}

İçerik:
{content}

Quiz soruları: {quiz_count} adet
Flashcard: {flashcard_count} adet

JSON formatı:
{{
  "scores": {{
    "finansal_dogruluk": 8,
    "seviye_uygunlugu": 7,
    "pedagojik_yapi": 9,
    "dil_netligi": 8,
    "ornek_kalitesi": 7,
    "quiz_kalitesi": 8,
    "kavramin_butunlugu": 8
  }},
  "average": 7.86,
  "decision": "APPROVED",
  "issues": [],
  "revision_notes": "",
  "strengths": ["...", "..."]
}}"""


class QualityGuardAgent:
    """Automated content quality check for Finance Academy lessons."""

    MIN_APPROVE_SCORE = 7.5
    MIN_DIMENSION_SCORE = 5.0

    def __init__(self):
        self.lesson_repo = LessonRepository()
        self.component_repo = LessonComponentRepository()
        self.log_repo = AgentLogRepository()
        self._llm = None

    @property
    def llm(self):
        if self._llm is None:
            try:
                from llm import get_router

                self._llm = get_router()
            except Exception:
                pass
        return self._llm

    def review_lesson(self, lesson: Lesson) -> dict:
        """
        Review a lesson. Returns dict with decision and scores.
        Side-effect: updates lesson status in DB.
        """
        t0 = time.perf_counter()

        components = self.component_repo.get_for_lesson(lesson.id)
        quiz_count = sum(1 for c in components if c["type"] == "quiz")
        flashcard_count = sum(1 for c in components if c["type"] == "flashcard")

        # Content length heuristic check (fast, no LLM needed)
        issues = self._heuristic_checks(lesson, quiz_count, flashcard_count)

        # LLM review
        llm_result = self._llm_review(lesson, quiz_count, flashcard_count)

        if llm_result:
            decision = llm_result.get("decision", "REVISION_NEEDED")
            scores = llm_result.get("scores", {})
            avg = llm_result.get("average", sum(scores.values()) / len(scores) if scores else 5.0)
        else:
            # Fallback: heuristic-only decision
            decision = "APPROVED" if len(issues) == 0 else "REVISION_NEEDED"
            scores = {}
            avg = 7.0 if decision == "APPROVED" else 5.5

        # Override if heuristic found serious issues
        if len(issues) >= 3:
            decision = "REJECTED"

        # Update lesson status
        new_status = {
            "APPROVED": "published",
            "REVISION_NEEDED": "draft",
            "REJECTED": "draft",
        }.get(decision, "draft")

        lesson.status = new_status
        lesson.updated_at = datetime.utcnow().isoformat()
        self.lesson_repo.save(lesson)

        duration_ms = (time.perf_counter() - t0) * 1000
        result = {
            "lesson_id": lesson.id,
            "decision": decision,
            "average_score": round(avg, 2),
            "scores": scores,
            "issues": issues + llm_result.get("issues", []) if llm_result else issues,
            "revision_notes": llm_result.get("revision_notes", "") if llm_result else "",
            "strengths": llm_result.get("strengths", []) if llm_result else [],
        }

        self.log_repo.log(
            agent_name=AGENT_NAME,
            action="review_lesson",
            input_summary=f"{lesson.id} ({lesson.difficulty})",
            output_summary=f"decision={decision}, avg={avg:.1f}",
            duration_ms=duration_ms,
        )
        logger.info("[%s] %s → %s (avg %.1f)", AGENT_NAME, lesson.id, decision, avg)
        return result

    def review_pending_lessons(self) -> list[dict]:
        """Review all lessons with status='draft'."""
        results = []
        from academy.models import db_cursor

        with db_cursor() as cur:
            cur.execute("SELECT id FROM lessons WHERE status='draft'")
            lesson_ids = [r["id"] for r in cur.fetchall()]

        for lid in lesson_ids:
            lesson = self.lesson_repo.get(lid)
            if lesson:
                results.append(self.review_lesson(lesson))
        return results

    # ──────────────────────────────────────────────────────────────────────
    # PRIVATE
    # ──────────────────────────────────────────────────────────────────────

    def _heuristic_checks(self, lesson: Lesson, quiz_count: int, flashcard_count: int) -> list[str]:
        issues = []
        word_count = len(lesson.content.split())
        if word_count < 200:
            issues.append(f"İçerik çok kısa: {word_count} kelime (min 200)")
        if not lesson.key_takeaways or len(lesson.key_takeaways) < 2:
            issues.append("Yetersiz kilit çıkarım (min 2 gerekli)")
        if quiz_count < 1:
            issues.append("Quiz sorusu yok")
        if flashcard_count < 1:
            issues.append("Flashcard yok")
        if not lesson.real_example.get("ticker") and not lesson.real_example.get("context"):
            issues.append("Gerçek hayat örneği eksik")
        return issues

    def _llm_review(self, lesson: Lesson, quiz_count: int, flashcard_count: int) -> dict | None:
        if self.llm is None:
            return None
        prompt = REVIEW_PROMPT.format(
            title=lesson.title,
            domain=lesson.domain,
            difficulty=lesson.difficulty,
            content=lesson.content[:1500],  # Truncate for token efficiency
            quiz_count=quiz_count,
            flashcard_count=flashcard_count,
        )
        try:
            full = f"{QUALITY_SYSTEM_PROMPT}\n\n{prompt}"
            resp = self.llm.generate(full, language="tr")
            raw = resp.content if hasattr(resp, "content") else str(resp)
            text = re.sub(r"```(?:json)?\n?", "", raw).strip()
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                return json.loads(match.group())
        except Exception as e:
            logger.warning("[%s] LLM review failed: %s", AGENT_NAME, e)
        return None
