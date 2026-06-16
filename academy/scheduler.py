"""
Finance Academy Scheduler
===========================
APScheduler-based automatic execution of all academy agents.

Schedule:
  Günlük 02:00 ET  → run_daily (gap detection + content generation)
  Pazartesi 07:00 ET → run_weekly (analytics + low-quality updates)
  1 Ocak / 1 Nisan / 1 Temmuz / 1 Ekim → quarterly review

Standalone:
  python -m academy.scheduler
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def start_academy_scheduler() -> bool:
    """Start the Academy background scheduler. Returns True on success."""
    try:
        import pytz
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.cron import CronTrigger

        from academy.orchestrator import AcademyOrchestrator

        tz = pytz.timezone("America/New_York")
        orch = AcademyOrchestrator()
        scheduler = BackgroundScheduler(timezone=tz)

        # Daily at 02:00 ET
        scheduler.add_job(
            func=orch.run_daily,
            trigger=CronTrigger(hour=2, minute=0, timezone=tz),
            id="academy_daily",
            name="Academy Daily Pipeline",
            replace_existing=True,
        )

        # Weekly Monday 07:00 ET
        scheduler.add_job(
            func=orch.run_weekly,
            trigger=CronTrigger(day_of_week="mon", hour=7, minute=0, timezone=tz),
            id="academy_weekly",
            name="Academy Weekly Analytics",
            replace_existing=True,
        )

        # Quarterly review (first day of each quarter)
        scheduler.add_job(
            func=orch.run_quarterly_review,
            trigger=CronTrigger(month="1,4,7,10", day=1, hour=3, minute=0, timezone=tz),
            id="academy_quarterly",
            name="Academy Quarterly Content Review",
            replace_existing=True,
        )

        scheduler.start()
        logger.info("[AcademyScheduler] Started: daily@02:00, weekly@Mon07:00, quarterly")
        return True

    except ImportError as e:
        logger.warning("[AcademyScheduler] APScheduler not available: %s", e)
        return False
    except Exception as e:
        logger.error("[AcademyScheduler] Failed to start: %s", e)
        return False


if __name__ == "__main__":
    import logging
    import time

    logging.basicConfig(level=logging.INFO)

    started = start_academy_scheduler()
    if started:
        print("✅ Academy scheduler running. Press Ctrl+C to stop.")
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            print("Stopped.")
    else:
        print("❌ Scheduler could not start. Check logs.")
