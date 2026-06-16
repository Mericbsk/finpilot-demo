"""
Finance Academy Orchestrator
==============================
Tüm agent'ları koordine eden merkezi yönetici.
Borsa ana projesiyle hiçbir bağımlılığı yoktur.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime

from academy.agents import (
    AnalyticsAgent,
    ContentGeneratorAgent,
    ContentUpdaterAgent,
    GapDetectorAgent,
    PersonalizationAgent,
    QualityGuardAgent,
)
from academy.models import ContentJobRepository, LessonRepository, init_db

logger = logging.getLogger(__name__)


class AcademyOrchestrator:
    def __init__(self):
        init_db()
        self.generator = ContentGeneratorAgent()
        self.quality_guard = QualityGuardAgent()
        self.personalization = PersonalizationAgent()
        self.gap_detector = GapDetectorAgent()
        self.analytics = AnalyticsAgent()
        self.updater = ContentUpdaterAgent()
        self.job_repo = ContentJobRepository()
        self.lesson_repo = LessonRepository()

    # ── Scheduled runs ────────────────────────────────────────────────

    def run_daily(self) -> dict:
        logger.info("[Orchestrator] Daily run...")
        gaps = self.gap_detector.run_daily_scan()
        jobs = self._process_jobs(max_jobs=5)
        reviewed = self.quality_guard.review_pending_lessons()
        result = {
            "date": datetime.utcnow().date().isoformat(),
            "gaps_found": len(gaps),
            "jobs_processed": jobs,
            "reviewed": len(reviewed),
            "published": sum(1 for r in reviewed if r.get("decision") == "APPROVED"),
        }
        logger.info("[Orchestrator] Daily done: %s", result)
        return result

    def run_weekly(self) -> dict:
        report = self.analytics.generate_weekly_report()
        updated = 0
        for item in report.get("quality_metrics", {}).get("low_rated", [])[:3]:
            lesson = self.lesson_repo.get(item["lesson_id"])
            if lesson:
                self.updater.update_lesson_from_feedback(
                    lesson.id, f"Düşük puan: {item.get('avg_rating', 0):.1f}/5"
                )
                updated += 1
        report["lessons_queued_for_update"] = updated
        return report

    def run_quarterly_review(self) -> dict:
        return self.updater.run_scheduled_review()

    # ── On-demand ─────────────────────────────────────────────────────

    def generate_lesson_now(
        self, domain: str, module: str, title: str, difficulty: str = "intermediate"
    ) -> dict:
        lesson = self.generator.generate_lesson(
            domain_slug=domain, module=module, title=title, difficulty=difficulty
        )
        if not lesson:
            return {"success": False, "error": "Generation failed"}
        review = self.quality_guard.review_lesson(lesson)
        return {"success": True, "lesson_id": lesson.id, "status": lesson.status, "review": review}

    def onboard_user(self, user_id: str, answers: dict) -> dict:
        profile = self.personalization.process_onboarding(user_id, answers)
        return {
            "user_id": user_id,
            "next_lessons": profile.next_lessons,
            "streak": profile.streak,
            "primary_goal": profile.primary_goal,
        }

    def get_user_dashboard(self, user_id: str) -> dict:
        profile = self.personalization.refresh_profile(user_id)
        daily = self.personalization.get_daily_card(user_id)
        lessons = []
        for lid in profile.next_lessons[:5]:
            l = self.lesson_repo.get(lid)
            if l:
                lessons.append(
                    {
                        "id": l.id,
                        "title": l.title,
                        "domain": l.domain,
                        "difficulty": l.difficulty,
                        "estimated_minutes": l.estimated_minutes,
                    }
                )
        return {
            "user_id": user_id,
            "streak": profile.streak,
            "total_lessons": profile.total_lessons,
            "engagement_score": profile.engagement_score,
            "domain_scores": profile.domain_scores,
            "next_lessons": lessons,
            "daily_card": daily,
            "weak_spots": profile.weak_spots,
        }

    def seed_starter_content(self) -> dict:
        from academy.seed_content import seed_all

        result = seed_all()
        logger.info("[Orchestrator] Seed: %s", result)
        return result

    def system_status(self) -> dict:
        stats = self.lesson_repo.stats()
        pending = 0
        try:
            from academy.models import db_cursor

            with db_cursor() as cur:
                cur.execute("SELECT count(*) n FROM content_jobs WHERE status='pending'")
                pending = cur.fetchone()["n"]
        except Exception:
            pass
        return {
            "total_published_lessons": stats.get("total_published", 0),
            "by_domain": stats.get("by_domain", {}),
            "pending_jobs": pending,
            "timestamp": datetime.utcnow().isoformat(),
        }

    # ── Internal job runner ───────────────────────────────────────────

    def _process_jobs(self, max_jobs: int = 10) -> int:
        processed = 0
        for _ in range(max_jobs):
            job = self.job_repo.next_pending()
            if not job:
                break
            agent = job.get("agent_name", "")
            if agent == "content_generator":
                ok = self.generator.process_job(job)
                processed += 1
                if ok:
                    try:
                        res = json.loads(job.get("result") or "{}")
                        lid = res.get("lesson_id")
                        if lid:
                            lesson = self.lesson_repo.get(lid)
                            if lesson:
                                self.quality_guard.review_lesson(lesson)
                    except Exception:
                        pass
            elif agent == "content_updater":
                payload = json.loads(job.get("payload") or "{}")
                lesson = self.lesson_repo.get(payload.get("lesson_id", ""))
                if lesson:
                    reason = payload.get("reason", payload.get("feedback", ""))
                    self.updater.update_lesson(lesson, reason)
                self.job_repo.update_status(job["id"], "done")
                processed += 1
        return processed
