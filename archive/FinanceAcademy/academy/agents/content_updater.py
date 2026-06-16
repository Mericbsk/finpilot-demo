"""
AGENT 6 — Content Updater Agent
==================================
Mevcut içeriklerin güncelliğini korur. 90 günde bir denetim,
piyasa olayı tetikleyicisi ve kullanıcı geri bildiriminden gelen düzeltmeler.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta

from academy.models import (
    AgentLogRepository,
    ContentJob,
    ContentJobRepository,
    Lesson,
    LessonRepository,
)

logger = logging.getLogger(__name__)
AGENT_NAME = "content_updater"


class ContentUpdaterAgent:
    """Keeps Academy content fresh and accurate."""

    REVIEW_INTERVAL_DAYS = 90

    def __init__(self):
        self.lesson_repo = LessonRepository()
        self.job_repo = ContentJobRepository()
        self.log_repo = AgentLogRepository()

    def run_scheduled_review(self) -> dict:
        """Find and queue lessons due for review (every 90 days)."""
        cutoff = (datetime.utcnow() - timedelta(days=self.REVIEW_INTERVAL_DAYS)).isoformat()
        due_lessons = self.lesson_repo.list_for_review(before_date=cutoff)

        queued = 0
        for lesson in due_lessons:
            self.job_repo.enqueue(
                ContentJob(
                    agent_name=AGENT_NAME,
                    job_type="review_and_update",
                    payload={"lesson_id": lesson.id, "reason": "scheduled_90day"},
                    priority=2,
                )
            )
            queued += 1

        self.log_repo.log(
            agent_name=AGENT_NAME,
            action="scheduled_review",
            output_summary=f"{queued} lessons queued for update",
        )
        return {"queued": queued, "lessons": [lesson.id for lesson in due_lessons]}

    def update_lesson_from_feedback(self, lesson_id: str, feedback_summary: str) -> None:
        """Queue a lesson for update based on user feedback."""
        self.job_repo.enqueue(
            ContentJob(
                agent_name=AGENT_NAME,
                job_type="update_from_feedback",
                payload={"lesson_id": lesson_id, "feedback": feedback_summary},
                priority=1,
            )
        )
        logger.info("[%s] Queued feedback-driven update for %s", AGENT_NAME, lesson_id)

    def update_lesson(self, lesson: Lesson, update_prompt: str) -> Lesson | None:
        """Actually update a lesson using LLM. Returns updated lesson."""
        try:
            from llm import get_router

            llm = get_router()
        except Exception:
            logger.warning("[%s] LLM unavailable, skipping update for %s", AGENT_NAME, lesson.id)
            return None

        t0 = time.perf_counter()
        system = (
            "Sen Finance Academy içerik güncelleme uzmanısın. "
            "Verilen dersi güncel verilerle düzelt, eski örnekleri yenile, "
            "varsa hatalı bilgileri düzelt. İçeriği Türkçe tut."
        )

        prompt = f"""Şu dersi güncelle:
Başlık: {lesson.title}
Alan: {lesson.domain}
Mevcut içerik (ilk 1000 karakter):
{lesson.content[:1000]}

Güncelleme gerekçesi: {update_prompt}

Sadece güncellenmiş 'content' ve 'key_takeaways' alanlarını JSON olarak döndür:
{{"content": "...", "key_takeaways": ["...", "..."]}}"""

        try:
            resp = llm.generate(f"{system}\n\n{prompt}", language="tr")
            raw = resp.content if hasattr(resp, "content") else str(resp)
            import json
            import re

            text = re.sub(r"```(?:json)?\n?", "", raw).strip()
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                parsed = json.loads(match.group())
                lesson.content = parsed.get("content", lesson.content)
                lesson.key_takeaways = parsed.get("key_takeaways", lesson.key_takeaways)
                lesson.updated_at = datetime.utcnow().isoformat()
                lesson.next_review_at = (datetime.utcnow() + timedelta(days=90)).isoformat()
                # Bump minor version
                parts = lesson.version.split(".")
                lesson.version = f"{parts[0]}.{int(parts[1])+1}" if len(parts) == 2 else "1.1"
                self.lesson_repo.save(lesson)
        except Exception as e:
            logger.error("[%s] Update failed for %s: %s", AGENT_NAME, lesson.id, e)
            return None

        duration_ms = (time.perf_counter() - t0) * 1000
        self.log_repo.log(
            agent_name=AGENT_NAME,
            action="update_lesson",
            input_summary=f"lesson={lesson.id}, reason={update_prompt[:50]}",
            output_summary=f"v{lesson.version}, {len(lesson.content)} chars",
            duration_ms=duration_ms,
        )
        return lesson

    def trigger_market_event(self, event_description: str, affected_domains: list[str]) -> int:
        """
        Trigger immediate review of lessons in affected domains
        after a major market event (e.g. Fed rate change, market crash).
        """
        queued = 0
        for domain_slug in affected_domains:
            lessons = self.lesson_repo.list_by_domain(domain_slug, status="published")
            for lesson in lessons[:3]:  # Max 3 per domain per event
                self.job_repo.enqueue(
                    ContentJob(
                        agent_name=AGENT_NAME,
                        job_type="market_event_update",
                        payload={
                            "lesson_id": lesson.id,
                            "event": event_description,
                        },
                        priority=0,  # P0 — immediate
                    )
                )
                queued += 1

        logger.info(
            "[%s] Market event '%s': %d lessons queued", AGENT_NAME, event_description, queued
        )
        return queued
