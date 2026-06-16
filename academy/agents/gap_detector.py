"""
AGENT 4 — Gap Detector Agent
===============================
Sistemde eksik içerikleri tespit eder ve Content Generator'a görev gönderir.

Kontrol ettiği kaynaklar:
  - Kullanıcı arama logları
  - Quiz hata analizi
  - Mevcut domain boşlukları (modül bazında coverage)

Kör nokta:
  - Arama loglama alt yapısı yoksa kör çalışır
  - Rakip platform analizi manuel gerektirir
"""

from __future__ import annotations

import logging

from academy.domains import DOMAINS
from academy.models import (
    AgentLogRepository,
    ContentJob,
    ContentJobRepository,
    LessonRepository,
    db_cursor,
)

logger = logging.getLogger(__name__)
AGENT_NAME = "gap_detector"


class GapDetectorAgent:
    """Finds content gaps and enqueues generation jobs."""

    PRIORITY_MAP = {"P0": 0, "P1": 1, "P2": 2}

    def __init__(self):
        self.lesson_repo = LessonRepository()
        self.job_repo = ContentJobRepository()
        self.log_repo = AgentLogRepository()

    def run_daily_scan(self) -> list[dict]:
        """Full gap scan. Returns list of gap findings."""
        gaps = []
        gaps.extend(self._scan_domain_coverage())
        gaps.extend(self._scan_quiz_error_patterns())
        gaps.extend(self._scan_search_misses())

        # Enqueue generation jobs for P0 and P1 gaps
        enqueued = 0
        for gap in gaps:
            if gap["priority"] in ("P0", "P1"):
                self._enqueue_gap(gap)
                enqueued += 1

        self.log_repo.log(
            agent_name=AGENT_NAME,
            action="daily_scan",
            input_summary="full gap scan",
            output_summary=f"{len(gaps)} gaps found, {enqueued} jobs enqueued",
        )
        logger.info("[%s] Found %d gaps, enqueued %d jobs", AGENT_NAME, len(gaps), enqueued)
        return gaps

    # ──────────────────────────────────────────────────────────────────────
    # SCAN METHODS
    # ──────────────────────────────────────────────────────────────────────

    def _scan_domain_coverage(self) -> list[dict]:
        """Check which modules have no published lessons."""
        gaps = []
        stats = self.lesson_repo.stats()
        by_domain = stats.get("by_domain", {})

        for domain in DOMAINS:
            slug = domain["slug"]
            count = by_domain.get(slug, 0)
            module_count = len(domain["modules"])

            if count == 0:
                # No lessons at all in this domain
                priority = "P0" if domain["priority"] == 1 else "P1"
                gaps.append(
                    {
                        "gap_type": "empty_domain",
                        "domain": slug,
                        "topic": f"{domain['name']} — Başlangıç Dersi",
                        "module": domain["modules"][0],
                        "priority": priority,
                        "evidence": [f"Domain tamamen boş: {slug}"],
                        "difficulty": "beginner",
                    }
                )
            elif count < module_count * 2:
                # Fewer lessons than 2 per module
                missing_modules = self._find_uncovered_modules(slug, domain["modules"])
                for mod in missing_modules[:2]:  # Max 2 per domain per run
                    gaps.append(
                        {
                            "gap_type": "missing_module",
                            "domain": slug,
                            "topic": f"{domain['name']} — {mod}",
                            "module": mod,
                            "priority": "P2",
                            "evidence": [f"{slug} domain'ında {mod} modülü için ders yok"],
                            "difficulty": "intermediate",
                        }
                    )
        return gaps

    def _scan_quiz_error_patterns(self) -> list[dict]:
        """Find concepts with high quiz error rates (>60% wrong answers)."""
        gaps = []
        try:
            with db_cursor() as cur:
                cur.execute("""
                    SELECT lesson_id, avg(quiz_score) as avg_score, count(*) as n
                    FROM user_progress
                    WHERE quiz_score IS NOT NULL
                    GROUP BY lesson_id
                    HAVING n >= 3 AND avg_score < 0.5
                """)
                rows = cur.fetchall()

            for row in rows:
                gaps.append(
                    {
                        "gap_type": "high_quiz_error",
                        "lesson_id": row["lesson_id"],
                        "topic": f"Yeniden yazılmalı: {row['lesson_id']} (avg quiz {row['avg_score']:.0%})",
                        "priority": "P1",
                        "evidence": [
                            f"Quiz başarısı: {row['avg_score']:.0%} ({row['n']} öğrenci)",
                            "İçerik yeterince açıklayıcı değil",
                        ],
                        "action": "update",
                    }
                )
        except Exception as e:
            logger.debug("[%s] Quiz scan error: %s", AGENT_NAME, e)
        return gaps

    def _scan_search_misses(self) -> list[dict]:
        """Check search_log table for missed queries (if it exists)."""
        gaps = []
        try:
            with db_cursor() as cur:
                cur.execute("""
                    SELECT query, count(*) as n
                    FROM search_log
                    WHERE result_count = 0
                    GROUP BY query
                    HAVING n >= 5
                    ORDER BY n DESC
                    LIMIT 10
                """)
                rows = cur.fetchall()

            for row in rows:
                gaps.append(
                    {
                        "gap_type": "search_miss",
                        "topic": row["query"],
                        "priority": "P1" if row["n"] >= 10 else "P2",
                        "evidence": [f"{row['n']} kullanıcı '{row['query']}' aradı ama bulunamadı"],
                        "difficulty": "intermediate",
                    }
                )
        except Exception:
            pass  # search_log table may not exist yet
        return gaps

    # ──────────────────────────────────────────────────────────────────────
    # HELPERS
    # ──────────────────────────────────────────────────────────────────────

    def _find_uncovered_modules(self, domain_slug: str, modules: list[str]) -> list[str]:
        """Return module names that have no lesson."""
        covered = set()
        lessons = self.lesson_repo.list_by_domain(domain_slug, status="published")
        for lesson in lessons:
            covered.add(lesson.module)
        return [m for m in modules if m not in covered]

    def _enqueue_gap(self, gap: dict) -> None:
        if gap.get("action") == "update":
            return  # Updates handled by Content Updater Agent
        priority = self.PRIORITY_MAP.get(gap.get("priority", "P2"), 2)
        self.job_repo.enqueue(
            ContentJob(
                agent_name="content_generator",
                job_type="generate",
                payload={
                    "domain": gap.get("domain", "fundamental-finance"),
                    "module": gap.get("module", "Temel"),
                    "title": gap.get("topic", "Yeni İçerik"),
                    "difficulty": gap.get("difficulty", "beginner"),
                },
                priority=priority,
            )
        )
