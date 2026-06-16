"""
AGENT 7 — Analytics Agent
============================
Tüm sistemi performans verisiyle izler ve haftalık rapor üretir.

Ölçülen metrikler:
  İçerik: tamamlanma oranı, quiz başarısı, en düşük puan
  Kullanıcı: aktif öğrenci, streak ortalaması, retention
  Kalite: 1-5 yıldız dağılımı, "kafa karıştırdı" oranı
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from academy.models import (
    AgentLogRepository,
    LessonRepository,
    UserProgressRepository,
    db_cursor,
)

logger = logging.getLogger(__name__)
AGENT_NAME = "analytics_agent"


class AnalyticsAgent:
    """Weekly Academy performance reporting."""

    def __init__(self):
        self.lesson_repo = LessonRepository()
        self.progress_repo = UserProgressRepository()
        self.log_repo = AgentLogRepository()

    def generate_weekly_report(self) -> dict[str, Any]:
        """Produce full weekly metrics report."""
        now = datetime.utcnow()
        week_ago = (now - timedelta(days=7)).isoformat()

        report = {
            "generated_at": now.isoformat(),
            "period": f"{week_ago[:10]} → {now.date().isoformat()}",
            "content_metrics": self._content_metrics(week_ago),
            "user_metrics": self._user_metrics(week_ago),
            "quality_metrics": self._quality_metrics(),
            "agent_activity": self._agent_activity(week_ago),
            "problems": [],
            "next_week_priorities": [],
        }

        # Detect problems
        cm = report["content_metrics"]
        qm = report["quality_metrics"]
        for item in cm.get("low_completion", []):
            report["problems"].append(
                f"[İçerik] '{item['lesson_id']}' tamamlanma oranı düşük: %{item['rate']:.0f}"
            )
        for item in qm.get("confusing_lessons", []):
            report["problems"].append(
                f"[Kalite] '{item['lesson_id']}' 'kafa karıştırıcı' bildirimi yüksek"
            )
        low_rated = qm.get("low_rated", [])
        for item in low_rated[:3]:
            report["problems"].append(
                f"[Kalite] '{item['lesson_id']}' ort. puan {item['avg_rating']:.1f}/5"
            )

        # Next week priorities
        if report["problems"]:
            report["next_week_priorities"] = [
                "Düşük puanlı dersleri Content Updater Agent ile güncelle",
                "Boş domain'lere başlangıç dersleri üret (Gap Detector çalıştır)",
            ]
        else:
            report["next_week_priorities"] = [
                "İleri seviye içerik üretimine devam et",
                "Yeni quiz soruları ekle",
            ]

        self.log_repo.log(
            agent_name=AGENT_NAME,
            action="weekly_report",
            output_summary=f"{len(report['problems'])} problems, "
            f"{report['user_metrics'].get('active_learners_7d', 0)} active learners",
        )
        return report

    def format_report_text(self, report: dict) -> str:
        """Format report as a readable text block."""
        lines = [
            f"\n{'='*55}",
            f"  📊 HAFTALIK AKADEMİ RAPORU — {report['period']}",
            f"{'='*55}",
            "",
            "📚 İÇERİK METRİKLERİ",
            f"  Toplam yayınlanan ders  : {report['content_metrics'].get('total_published', 0)}",
            f"  Bu hafta yeni ders      : {report['content_metrics'].get('new_this_week', 0)}",
            f"  Ort. tamamlanma oranı   : %{report['content_metrics'].get('avg_completion_rate', 0):.0f}",
            "",
            "👥 KULLANICI METRİKLERİ",
            f"  Aktif öğrenci (7 gün)   : {report['user_metrics'].get('active_learners_7d', 0)}",
            f"  Toplam tamamlanan ders  : {report['user_metrics'].get('completions_this_week', 0)}",
            f"  Ort. streak             : {report['user_metrics'].get('avg_streak', 0):.1f} gün",
            "",
            "⭐ KALİTE METRİKLERİ",
            f"  Ort. değerlendirme      : {report['quality_metrics'].get('avg_rating', 0):.1f}/5",
            f"  'Kafa karıştırdı' oranı : %{report['quality_metrics'].get('confusing_rate', 0):.1f}",
        ]

        if report["problems"]:
            lines += ["", "⚠️  TESPİT EDİLEN SORUNLAR"]
            for p in report["problems"]:
                lines.append(f"  • {p}")

        agent_act = report.get("agent_activity", {})
        if agent_act:
            lines += ["", "🤖 AGENT AKTİVİTESİ"]
            for agent, count in agent_act.items():
                lines.append(f"  {agent}: {count} işlem")

        lines += ["", "📋 SONRAKİ HAFTA ÖNCELİKLERİ"]
        for i, p in enumerate(report["next_week_priorities"], 1):
            lines.append(f"  {i}. {p}")

        lines.append(f"\n{'='*55}\n")
        return "\n".join(lines)

    # ──────────────────────────────────────────────────────────────────────
    # PRIVATE
    # ──────────────────────────────────────────────────────────────────────

    def _content_metrics(self, since: str) -> dict:
        try:
            with db_cursor() as cur:
                cur.execute("SELECT count(*) as n FROM lessons WHERE status='published'")
                total = cur.fetchone()["n"]
                cur.execute(
                    "SELECT count(*) as n FROM lessons WHERE status='published' AND created_at >= ?",
                    (since,),
                )
                new_week = cur.fetchone()["n"]

                # Completion rates per lesson
                cur.execute("""
                    SELECT lesson_id,
                           count(*) as attempts,
                           sum(CASE WHEN completed_at IS NOT NULL THEN 1 ELSE 0 END) as completions
                    FROM user_progress GROUP BY lesson_id
                """)
                lesson_stats = cur.fetchall()

            rates = []
            low_completion = []
            for row in lesson_stats:
                rate = row["completions"] / row["attempts"] * 100 if row["attempts"] > 0 else 0
                rates.append(rate)
                if rate < 40 and row["attempts"] >= 5:
                    low_completion.append({"lesson_id": row["lesson_id"], "rate": rate})

            return {
                "total_published": total,
                "new_this_week": new_week,
                "avg_completion_rate": sum(rates) / len(rates) if rates else 0,
                "low_completion": sorted(low_completion, key=lambda x: x["rate"])[:5],
            }
        except Exception as e:
            logger.debug("[%s] content_metrics error: %s", AGENT_NAME, e)
            return {}

    def _user_metrics(self, since: str) -> dict:
        try:
            with db_cursor() as cur:
                cur.execute(
                    "SELECT count(DISTINCT user_id) as n FROM user_progress WHERE completed_at >= ?",
                    (since,),
                )
                active = cur.fetchone()["n"]
                cur.execute(
                    "SELECT count(*) as n FROM user_progress WHERE completed_at >= ?", (since,)
                )
                completions = cur.fetchone()["n"]
                cur.execute("SELECT avg(streak) as s FROM user_profile")
                avg_streak = cur.fetchone()["s"] or 0

            return {
                "active_learners_7d": active,
                "completions_this_week": completions,
                "avg_streak": avg_streak,
            }
        except Exception as e:
            logger.debug("[%s] user_metrics error: %s", AGENT_NAME, e)
            return {}

    def _quality_metrics(self) -> dict:
        try:
            with db_cursor() as cur:
                cur.execute(
                    "SELECT avg(feedback_rating) as r FROM user_progress WHERE feedback_rating IS NOT NULL"
                )
                avg_rating = cur.fetchone()["r"] or 0

                cur.execute("""
                    SELECT lesson_id, count(*) as n FROM user_progress
                    WHERE feedback_tags LIKE '%confusing%'
                    GROUP BY lesson_id HAVING n >= 3
                    ORDER BY n DESC LIMIT 5
                """)
                confusing = [{"lesson_id": r["lesson_id"], "count": r["n"]} for r in cur.fetchall()]

                # Total feedback count
                cur.execute(
                    "SELECT count(*) as n FROM user_progress WHERE feedback_tags LIKE '%confusing%'"
                )
                confusing_total = cur.fetchone()["n"]
                cur.execute(
                    "SELECT count(*) as n FROM user_progress WHERE feedback_rating IS NOT NULL"
                )
                rated_total = cur.fetchone()["n"] or 1

            return {
                "avg_rating": avg_rating,
                "confusing_rate": confusing_total / rated_total * 100,
                "confusing_lessons": confusing,
                "low_rated": self.progress_repo.low_rated_lessons(),
            }
        except Exception as e:
            logger.debug("[%s] quality_metrics error: %s", AGENT_NAME, e)
            return {}

    def _agent_activity(self, since: str) -> dict:
        try:
            with db_cursor() as cur:
                cur.execute(
                    """
                    SELECT agent_name, count(*) as n FROM agent_logs
                    WHERE timestamp >= ? GROUP BY agent_name
                """,
                    (since,),
                )
                return {r["agent_name"]: r["n"] for r in cur.fetchall()}
        except Exception:
            return {}
