"""
AGENT 3 — Personalization Engine Agent
========================================
Her kullanıcı için benzersiz öğrenme yolu oluşturur ve günceller.

Kör nokta:
  - Kullanıcı platformdan dışında öğrendiyse bunu bilemez
  - Soğuk başlangıç: ilk 3 ders tamamlanmadan profil çok seyrek kalır
"""

from __future__ import annotations

import logging
import time
from datetime import date, timedelta

from academy.domains import DOMAINS
from academy.models import (
    AgentLogRepository,
    LessonRepository,
    UserProfile,
    UserProfileRepository,
    UserProgressRepository,
)

logger = logging.getLogger(__name__)
AGENT_NAME = "personalization_engine"

# ─────────────────────────────────────────────────────────────────────────────
# ONBOARDING QUESTIONS
# ─────────────────────────────────────────────────────────────────────────────

ONBOARDING_QUESTIONS = [
    {
        "id": "experience",
        "question": "Yatırım deneyimin nedir?",
        "options": [
            {"value": "none", "label": "Hiç yatırım yapmadım"},
            {"value": "beginner", "label": "1-2 yıldır az az alım-satım yapıyorum"},
            {"value": "intermediate", "label": "Teknik analiz biliyorum, aktif işlem yapıyorum"},
            {"value": "advanced", "label": "Profesyonel seviyede, sistem/strateji kullanıyorum"},
        ],
    },
    {
        "id": "focus",
        "question": "Neye odaklanmak istiyorsun?",
        "options": [
            {"value": "swing_trading", "label": "Günlük/haftalık alım-satım (swing)"},
            {"value": "long_term", "label": "Uzun vadeli portföy büyütmek"},
            {"value": "options", "label": "Opsiyon ve türev araçlar"},
            {"value": "algo", "label": "Algoritmik trading / AI"},
        ],
    },
    {
        "id": "time",
        "question": "Günde kaç dakika ayırabilirsin?",
        "options": [
            {"value": 5, "label": "5 dakika (hızlı tekrar modu)"},
            {"value": 15, "label": "15 dakika (standart)"},
            {"value": 30, "label": "30 dakika (yoğun öğrenme)"},
            {"value": 60, "label": "1 saat+ (tam immersion)"},
        ],
    },
]

# Goal → priority domain slugs
GOAL_DOMAIN_MAP: dict[str, list[str]] = {
    "swing_trading": [
        "technical-analysis",
        "risk-management",
        "behavioral-finance",
        "stocks-market",
    ],
    "long_term": ["fundamental-analysis", "portfolio-management", "etf-passive", "macro-analysis"],
    "options": [
        "options-derivatives",
        "technical-analysis",
        "risk-management",
        "behavioral-finance",
    ],
    "algo": ["algo-trading-ai", "technical-analysis", "risk-management", "fundamental-finance"],
}

# ─────────────────────────────────────────────────────────────────────────────
# PERSONALIZATION ENGINE
# ─────────────────────────────────────────────────────────────────────────────


class PersonalizationAgent:
    """Builds and maintains personalized learning paths."""

    def __init__(self):
        self.profile_repo = UserProfileRepository()
        self.progress_repo = UserProgressRepository()
        self.lesson_repo = LessonRepository()
        self.log_repo = AgentLogRepository()

    # ──────────────────────────────────────────────────────────────────────
    # ONBOARDING
    # ──────────────────────────────────────────────────────────────────────

    def get_onboarding_questions(self) -> list[dict]:
        return ONBOARDING_QUESTIONS

    def process_onboarding(self, user_id: str, answers: dict) -> UserProfile:
        """
        answers = {
          "experience": "beginner",
          "focus": "swing_trading",
          "time": 15
        }
        """
        profile = self.profile_repo.get_or_create(user_id)

        experience = answers.get("experience", "beginner")
        focus = answers.get("focus", "swing_trading")
        daily_min = int(answers.get("time", 15))

        # Map experience to domain scores baseline
        baseline = {"none": 5, "beginner": 15, "intermediate": 35, "advanced": 60}
        base_score = baseline.get(experience, 10)
        profile.domain_scores = {str(d["id"]): float(base_score) for d in DOMAINS}

        profile.daily_minutes = daily_min
        profile.primary_goal = focus
        profile.preferences["onboarding_done"] = True
        profile.preferences["experience_level"] = experience

        # Build initial learning path
        priority_domains = GOAL_DOMAIN_MAP.get(focus, GOAL_DOMAIN_MAP["swing_trading"])
        path = self._build_path(priority_domains, completed=[], limit=14)
        profile.learning_path = path
        profile.next_lessons = path[:3]

        self.profile_repo.save(profile)
        self.log_repo.log(
            agent_name=AGENT_NAME,
            action="onboarding",
            input_summary=f"user={user_id}, exp={experience}, focus={focus}",
            output_summary=f"path={len(path)} lessons",
        )
        return profile

    # ──────────────────────────────────────────────────────────────────────
    # PROFILE REFRESH
    # ──────────────────────────────────────────────────────────────────────

    def refresh_profile(self, user_id: str) -> UserProfile:
        """Recalculate domain scores and next_lessons from latest progress."""
        t0 = time.perf_counter()
        profile = self.profile_repo.get_or_create(user_id)
        completed_ids = set(self.progress_repo.completed_for_user(user_id))

        # Recalculate domain scores
        all_lessons = self.lesson_repo.all_published()
        domain_total: dict[str, int] = {}
        domain_done: dict[str, int] = {}
        for lesson in all_lessons:
            domain_total[lesson.domain] = domain_total.get(lesson.domain, 0) + 1
            if lesson.id in completed_ids:
                domain_done[lesson.domain] = domain_done.get(lesson.domain, 0) + 1

        new_scores: dict[str, float] = {}
        for domain_id_str, old_score in profile.domain_scores.items():
            # Map by domain slug
            total = 0
            done = 0
            for d in DOMAINS:
                if str(d["id"]) == domain_id_str:
                    slug = d["slug"]
                    total = domain_total.get(slug, 0)
                    done = domain_done.get(slug, 0)
                    break
            if total > 0:
                completion_pct = done / total * 100
                new_scores[domain_id_str] = min(100.0, completion_pct + old_score * 0.2)
            else:
                new_scores[domain_id_str] = old_score

        profile.domain_scores = new_scores

        # Update streak
        profile = self._update_streak(profile, user_id)

        # Rebuild next_lessons
        focus = profile.primary_goal
        priority_domains = GOAL_DOMAIN_MAP.get(focus, GOAL_DOMAIN_MAP["swing_trading"])
        # Also add weak domains
        weak_domains = self._find_weak_domains(profile)
        combined_priority = list(dict.fromkeys(priority_domains + weak_domains))
        new_path = self._build_path(combined_priority, completed=list(completed_ids), limit=20)
        profile.learning_path = new_path
        profile.next_lessons = new_path[:5]
        profile.total_lessons = len(completed_ids)

        # Engagement score: streak × 10 + completion rate × 50
        total_available = len(all_lessons)
        completion_rate = len(completed_ids) / total_available if total_available > 0 else 0
        profile.engagement_score = min(100.0, profile.streak * 3 + completion_rate * 70)

        self.profile_repo.save(profile)
        duration_ms = (time.perf_counter() - t0) * 1000
        self.log_repo.log(
            agent_name=AGENT_NAME,
            action="refresh_profile",
            input_summary=f"user={user_id}",
            output_summary=f"next_lessons={profile.next_lessons[:3]}, streak={profile.streak}",
            duration_ms=duration_ms,
        )
        return profile

    # ──────────────────────────────────────────────────────────────────────
    # DAILY CARD
    # ──────────────────────────────────────────────────────────────────────

    def get_daily_card(self, user_id: str) -> dict:
        """Return today's recommended lesson + a spaced repetition review card."""
        profile = self.profile_repo.get_or_create(user_id)
        completed = set(self.progress_repo.completed_for_user(user_id))

        next_lesson_id = None
        for lid in profile.next_lessons:
            if lid not in completed:
                next_lesson_id = lid
                break

        next_lesson = self.lesson_repo.get(next_lesson_id) if next_lesson_id else None

        return {
            "date": date.today().isoformat(),
            "streak": profile.streak,
            "next_lesson": {
                "id": next_lesson.id if next_lesson else None,
                "title": next_lesson.title if next_lesson else "Tüm dersler tamamlandı!",
                "estimated_minutes": next_lesson.estimated_minutes if next_lesson else 0,
                "domain": next_lesson.domain if next_lesson else None,
            },
            "daily_goal_minutes": profile.daily_minutes,
            "lessons_completed_total": profile.total_lessons,
            "engagement_score": profile.engagement_score,
            "weak_spots": profile.weak_spots[:3],
            "motivation": self._motivation_message(profile),
        }

    # ──────────────────────────────────────────────────────────────────────
    # PRIVATE HELPERS
    # ──────────────────────────────────────────────────────────────────────

    def _build_path(
        self, priority_domain_slugs: list[str], completed: list[str], limit: int = 20
    ) -> list[str]:
        """Build ordered lesson list from priority domains, excluding completed."""
        path = []
        completed_set = set(completed)

        # First pass: priority domains in order
        for slug in priority_domain_slugs:
            lessons = self.lesson_repo.list_by_domain(slug, status="published")
            # Sort: beginner first, then intermediate, then advanced
            order_map = {"beginner": 0, "intermediate": 1, "advanced": 2}
            lessons.sort(key=lambda lesson: order_map.get(lesson.difficulty, 1))
            for lesson in lessons:
                if lesson.id not in completed_set and lesson.id not in path:
                    path.append(lesson.id)
                    if len(path) >= limit:
                        return path

        # Second pass: remaining domains
        remaining = [d["slug"] for d in DOMAINS if d["slug"] not in priority_domain_slugs]
        for slug in remaining:
            lessons = self.lesson_repo.list_by_domain(slug, status="published")
            for lesson in lessons:
                if lesson.id not in completed_set and lesson.id not in path:
                    path.append(lesson.id)
                    if len(path) >= limit:
                        return path
        return path

    def _update_streak(self, profile: UserProfile, user_id: str) -> UserProfile:
        """Update streak based on today's activity."""
        today = date.today().isoformat()
        yesterday = (date.today() - timedelta(days=1)).isoformat()

        if profile.streak_updated == today:
            return profile  # Already updated today

        if profile.streak_updated == yesterday:
            profile.streak += 1
        elif profile.streak_updated and profile.streak_updated < yesterday:
            profile.streak = 1  # Reset streak

        profile.streak_updated = today
        return profile

    def _find_weak_domains(self, profile: UserProfile) -> list[str]:
        """Return domain slugs where score < 30 (weak spots)."""
        weak = []
        for d in DOMAINS:
            score = profile.domain_scores.get(str(d["id"]), 0)
            if score < 30:
                weak.append(d["slug"])
        return weak[:3]

    @staticmethod
    def _motivation_message(profile: UserProfile) -> str:
        if profile.streak == 0:
            return "Bugün ilk dersine başla! 🚀"
        elif profile.streak < 7:
            return f"{profile.streak} günlük serisini sürdür! 🔥"
        elif profile.streak < 30:
            return f"{profile.streak} gün! Mükemmel gidiyorsun! ⭐"
        else:
            return f"{profile.streak} günlük seri — Gerçek bir yatırımcısın! 🏆"
