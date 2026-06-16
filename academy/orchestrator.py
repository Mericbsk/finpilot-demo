"""
Finance Academy Orchestrator
==============================
Tüm agent'ları koordine eden merkezi yönetici.

Scheduler akışı:
  Günlük  → Gap Detector → Content Generator (P0/P1 jobları)
  Haftalık → Analytics Agent raporu → Content Updater (düşük puanlılar)
  90 günlük → Content Updater scheduled review
  Her yeni içerik → Quality Guard → publish/reject

Ayrıca CLI ve API üzerinden manuel tetikleme desteği sağlar.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime
from typing import Any

from academy.agents import (
    AnalyticsAgent,
    ContentGeneratorAgent,
    ContentUpdaterAgent,
    GapDetectorAgent,
    PersonalizationAgent,
    QualityGuardAgent,
)
from academy.models import (
    ContentJobRepository,
    LessonRepository,
    init_db,
)

logger = logging.getLogger(__name__)


class AcademyOrchestrator:
    """Central coordinator for all Finance Academy agents."""

    def __init__(self):
        init_db()  # ensure schema exists
        self.generator = ContentGeneratorAgent()
        self.quality_guard = QualityGuardAgent()
        self.personalization = PersonalizationAgent()
        self.gap_detector = GapDetectorAgent()
        self.analytics = AnalyticsAgent()
        self.updater = ContentUpdaterAgent()
        self.job_repo = ContentJobRepository()
        self.lesson_repo = LessonRepository()

    # ──────────────────────────────────────────────────────────────────────
    # SCHEDULED RUNS
    # ──────────────────────────────────────────────────────────────────────

    def run_daily(self) -> dict[str, Any]:
        """Daily pipeline: gap detection → job processing → quality review."""
        logger.info("[Orchestrator] Starting daily run...")
        t0 = time.perf_counter()
        results: dict[str, Any] = {"date": datetime.utcnow().date().isoformat()}

        # 1. Gap detection
        gaps = self.gap_detector.run_daily_scan()
        results["gaps_found"] = len(gaps)

        # 2. Process pending generation jobs (max 5 per day)
        results["jobs_processed"] = self._process_pending_jobs(max_jobs=5)

        # 3. Quality guard: review all draft lessons
        reviewed = self.quality_guard.review_pending_lessons()
        results["reviewed"] = len(reviewed)
        results["published"] = sum(1 for r in reviewed if r.get("decision") == "APPROVED")

        duration_ms = (time.perf_counter() - t0) * 1000
        logger.info("[Orchestrator] Daily run done in %.0f ms: %s", duration_ms, results)
        return results

    def run_weekly(self) -> dict[str, Any]:
        """Weekly pipeline: analytics report → update low-quality content."""
        logger.info("[Orchestrator] Starting weekly run...")
        report = self.analytics.generate_weekly_report()

        # Trigger updates for low-rated lessons
        updated = 0
        for item in report.get("quality_metrics", {}).get("low_rated", [])[:3]:
            lesson = self.lesson_repo.get(item["lesson_id"])
            if lesson:
                self.updater.update_lesson_from_feedback(
                    lesson.id, f"Düşük kullanıcı puanı: {item.get('avg_rating', 0):.1f}/5"
                )
                updated += 1

        report["lessons_queued_for_update"] = updated
        logger.info("[Orchestrator] Weekly run: %d updates queued", updated)
        return report

    def run_quarterly_review(self) -> dict[str, Any]:
        """90-day content freshness review."""
        return self.updater.run_scheduled_review()

    # ──────────────────────────────────────────────────────────────────────
    # CONTENT GENERATION (API-triggered)
    # ──────────────────────────────────────────────────────────────────────

    def generate_lesson_now(
        self,
        domain: str,
        module: str,
        title: str,
        difficulty: str = "intermediate",
    ) -> dict[str, Any]:
        """Generate a lesson immediately (blocking). Returns lesson dict."""
        lesson = self.generator.generate_lesson(
            domain_slug=domain,
            module=module,
            title=title,
            difficulty=difficulty,
        )
        if not lesson:
            return {"success": False, "error": "Generation failed"}

        # Immediate quality review
        review = self.quality_guard.review_lesson(lesson)
        return {
            "success": True,
            "lesson_id": lesson.id,
            "status": lesson.status,
            "review": review,
        }

    # ──────────────────────────────────────────────────────────────────────
    # USER FLOWS
    # ──────────────────────────────────────────────────────────────────────

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
        daily_card = self.personalization.get_daily_card(user_id)

        # Enrich next_lessons with lesson details
        enriched_lessons = []
        for lid in profile.next_lessons[:5]:
            lesson = self.lesson_repo.get(lid)
            if lesson:
                enriched_lessons.append(
                    {
                        "id": lesson.id,
                        "title": lesson.title,
                        "domain": lesson.domain,
                        "difficulty": lesson.difficulty,
                        "estimated_minutes": lesson.estimated_minutes,
                    }
                )

        return {
            "user_id": user_id,
            "streak": profile.streak,
            "total_lessons": profile.total_lessons,
            "engagement_score": profile.engagement_score,
            "domain_scores": profile.domain_scores,
            "next_lessons": enriched_lessons,
            "daily_card": daily_card,
            "weak_spots": profile.weak_spots,
        }

    # ──────────────────────────────────────────────────────────────────────
    # SEED INITIAL CONTENT
    # ──────────────────────────────────────────────────────────────────────

    def seed_starter_content(self) -> dict[str, int]:
        """
        Generate starter lessons for all 12 domains (1 beginner lesson each).
        Designed to run once at system initialization.
        """
        from academy.domains import DOMAINS

        stats = self.lesson_repo.stats()
        generated = 0
        skipped = 0

        for domain in sorted(DOMAINS, key=lambda d: d["priority"]):
            slug = domain["slug"]
            existing = stats["by_domain"].get(slug, 0)
            if existing > 0:
                skipped += 1
                continue

            first_module = domain["modules"][0]
            title = f"{domain['name']}: Temel Kavramlar ve Giriş"

            logger.info("[Orchestrator] Seeding: %s / %s", slug, title)
            self.generator.enqueue(
                domain=slug,
                module=first_module,
                title=title,
                difficulty="beginner",
                priority=0,  # High priority for seed
            )
            generated += 1

        # Process all queued seed jobs
        processed = self._process_pending_jobs(max_jobs=generated + 5)
        logger.info("[Orchestrator] Seed complete: %d generated, %d skipped", generated, skipped)
        return {"generated": generated, "skipped": skipped, "processed": processed}

    # ──────────────────────────────────────────────────────────────────────
    # JOB RUNNER
    # ──────────────────────────────────────────────────────────────────────

    def _process_pending_jobs(self, max_jobs: int = 10) -> int:
        """Process up to max_jobs pending content jobs. Returns count processed."""
        processed = 0
        for _ in range(max_jobs):
            job = self.job_repo.next_pending()
            if not job:
                break
            agent_name = job.get("agent_name", "")
            if agent_name == "content_generator":
                success = self.generator.process_job(job)
                processed += 1
                if success:
                    # Immediately review the generated lesson
                    result_raw = job.get("result")
                    if result_raw:
                        try:
                            result = (
                                json.loads(result_raw)
                                if isinstance(result_raw, str)
                                else result_raw
                            )
                            lesson_id = result.get("lesson_id")
                            if lesson_id:
                                lesson = self.lesson_repo.get(lesson_id)
                                if lesson:
                                    self.quality_guard.review_lesson(lesson)
                        except Exception:
                            pass
            elif agent_name == "content_updater":
                payload = json.loads(job.get("payload") or "{}")
                lesson = self.lesson_repo.get(payload.get("lesson_id", ""))
                if lesson:
                    reason = payload.get(
                        "reason", payload.get("feedback", payload.get("event", ""))
                    )
                    self.updater.update_lesson(lesson, reason)
                self.job_repo.update_status(job["id"], "done")
                processed += 1
        return processed

    # ──────────────────────────────────────────────────────────────────────
    # SYSTEM STATUS
    # ──────────────────────────────────────────────────────────────────────

    def system_status(self) -> dict[str, Any]:
        """Quick health check of the Academy system."""
        stats = self.lesson_repo.stats()

        pending_jobs = 0
        try:
            from academy.models import db_cursor

            with db_cursor() as cur:
                cur.execute("SELECT count(*) as n FROM content_jobs WHERE status='pending'")
                pending_jobs = cur.fetchone()["n"]
        except Exception:
            pass

        return {
            "total_published_lessons": stats.get("total_published", 0),
            "by_domain": stats.get("by_domain", {}),
            "pending_jobs": pending_jobs,
            "timestamp": datetime.utcnow().isoformat(),
        }
