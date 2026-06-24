"""
Finance Academy — Data Models
================================
SQLite-backed ORM models for all Academy entities.
Uses sqlite3 directly (no extra dep needed) with a thin Repository layer.

Tables:
  lessons              — Course content
  lesson_components    — Quizzes, flashcards, case studies per lesson
  user_progress        — Completed lessons, scores, feedback
  user_profile         — Per-user learning state and preferences
  content_jobs         — Agent task queue
  agent_logs           — Agent execution audit trail
"""

from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

# DB konumu: kararlı ve yapılandırılabilir.
#   ACADEMY_DB_PATH ayarlıysa onu kullan; değilse repo içindeki data/academy.db.
# (Eski sürümdeki sabit /sessions/... oturum yolu kaldırıldı — veri kaybı riskiydi.)
_DATA_BASE = Path(__file__).parent.parent / "data"
_ENV_DB = os.getenv("ACADEMY_DB_PATH")
DB_PATH = Path(_ENV_DB).expanduser() if _ENV_DB else _DATA_BASE / "academy.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────────────────────────────────────────
# SCHEMA
# ─────────────────────────────────────────────────────────────────────────────

SCHEMA_SQL = """
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS lessons (
    id              TEXT PRIMARY KEY,       -- e.g. "TA-006-macd"
    domain          TEXT NOT NULL,          -- e.g. "technical-analysis"
    domain_id       INTEGER NOT NULL,       -- 1-12
    module          TEXT NOT NULL,          -- e.g. "oscillators"
    title           TEXT NOT NULL,
    difficulty      TEXT NOT NULL,          -- beginner/intermediate/advanced
    estimated_minutes INTEGER DEFAULT 10,
    content         TEXT NOT NULL,          -- Markdown
    key_takeaways   TEXT DEFAULT '[]',      -- JSON array
    misconceptions  TEXT DEFAULT '[]',      -- JSON array
    real_example    TEXT DEFAULT '{}',      -- JSON object {ticker, context}
    related_lessons TEXT DEFAULT '[]',      -- JSON array of lesson ids
    pedagogy_score  REAL DEFAULT 0.0,       -- 1-10 from Learning Design Agent
    status          TEXT DEFAULT 'draft',   -- draft/approved/published/archived
    version         TEXT DEFAULT '1.0',
    created_at      TEXT,
    updated_at      TEXT,
    next_review_at  TEXT                    -- for Content Updater Agent
);

CREATE TABLE IF NOT EXISTS lesson_components (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    lesson_id   TEXT NOT NULL REFERENCES lessons(id),
    type        TEXT NOT NULL,  -- quiz/flashcard/case_study/glossary/cheat_sheet
    content     TEXT NOT NULL,  -- JSON payload
    order_idx   INTEGER DEFAULT 0,
    created_at  TEXT
);

CREATE TABLE IF NOT EXISTS user_progress (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         TEXT NOT NULL,
    lesson_id       TEXT NOT NULL REFERENCES lessons(id),
    completed_at    TEXT,
    quiz_score      REAL,           -- 0.0 – 1.0
    time_spent_sec  INTEGER,
    feedback_rating INTEGER,        -- 1-5
    feedback_text   TEXT,
    feedback_tags   TEXT DEFAULT '[]',  -- ["confusing","helpful","example_good"]
    scroll_depth    REAL,           -- 0.0 – 1.0
    return_count    INTEGER DEFAULT 0,
    UNIQUE(user_id, lesson_id)
);

CREATE TABLE IF NOT EXISTS user_profile (
    user_id         TEXT PRIMARY KEY,
    domain_scores   TEXT DEFAULT '{}',      -- JSON {domain_id: 0-100}
    learning_path   TEXT DEFAULT '[]',      -- JSON ordered lesson id list
    weak_spots      TEXT DEFAULT '[]',      -- JSON list of concept slugs
    next_lessons    TEXT DEFAULT '[]',      -- JSON list of lesson ids (top 5)
    streak          INTEGER DEFAULT 0,
    streak_updated  TEXT,
    total_lessons   INTEGER DEFAULT 0,
    learning_style  TEXT DEFAULT 'visual',  -- visual/reading/practice
    daily_minutes   INTEGER DEFAULT 15,
    primary_goal    TEXT DEFAULT 'active_trader',
    engagement_score REAL DEFAULT 0.0,
    last_active     TEXT,
    preferences     TEXT DEFAULT '{}'       -- JSON misc prefs
);

CREATE TABLE IF NOT EXISTS content_jobs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_name  TEXT NOT NULL,
    job_type    TEXT NOT NULL,    -- generate/update/review/detect_gap/scout_trend
    payload     TEXT DEFAULT '{}',
    status      TEXT DEFAULT 'pending',  -- pending/running/done/failed/retrying
    priority    INTEGER DEFAULT 2,       -- 0=P0 immediate, 1=P1, 2=P2 backlog
    attempts    INTEGER DEFAULT 0,
    result      TEXT,
    error_msg   TEXT,
    created_at  TEXT,
    started_at  TEXT,
    completed_at TEXT
);

CREATE TABLE IF NOT EXISTS agent_logs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_name      TEXT NOT NULL,
    action          TEXT NOT NULL,
    input_summary   TEXT,
    output_summary  TEXT,
    tokens_used     INTEGER DEFAULT 0,
    duration_ms     REAL DEFAULT 0,
    status          TEXT DEFAULT 'ok',   -- ok/error/warn
    timestamp       TEXT
);

CREATE INDEX IF NOT EXISTS idx_lessons_domain ON lessons(domain);
CREATE INDEX IF NOT EXISTS idx_lessons_status ON lessons(status);
CREATE INDEX IF NOT EXISTS idx_progress_user ON user_progress(user_id);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON content_jobs(status, priority);
CREATE INDEX IF NOT EXISTS idx_logs_agent ON agent_logs(agent_name, timestamp);
"""

# ─────────────────────────────────────────────────────────────────────────────
# DATABASE
# ─────────────────────────────────────────────────────────────────────────────


def get_connection(path: Path = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(str(path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(path: Path = DB_PATH) -> None:
    """Create all tables (idempotent)."""
    with get_connection(path) as conn:
        conn.executescript(SCHEMA_SQL)
        conn.commit()


@contextmanager
def db_cursor(path: Path = DB_PATH):
    conn = get_connection(path)
    try:
        cur = conn.cursor()
        yield cur
        conn.commit()
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# DATACLASSES (lightweight — mirrors DB schema)
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class Lesson:
    id: str
    domain: str
    domain_id: int
    module: str
    title: str
    difficulty: str
    content: str
    estimated_minutes: int = 10
    key_takeaways: list[str] = field(default_factory=list)
    misconceptions: list[str] = field(default_factory=list)
    real_example: dict = field(default_factory=dict)
    related_lessons: list[str] = field(default_factory=list)
    pedagogy_score: float = 0.0
    status: str = "draft"
    version: str = "1.0"
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    next_review_at: str = ""


@dataclass
class LessonComponent:
    lesson_id: str
    type: str  # quiz / flashcard / case_study / glossary / cheat_sheet
    content: dict
    order_idx: int = 0
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class UserProfile:
    user_id: str
    domain_scores: dict[str, float] = field(default_factory=dict)
    learning_path: list[str] = field(default_factory=list)
    weak_spots: list[str] = field(default_factory=list)
    next_lessons: list[str] = field(default_factory=list)
    streak: int = 0
    streak_updated: str = ""
    total_lessons: int = 0
    learning_style: str = "visual"
    daily_minutes: int = 15
    primary_goal: str = "active_trader"
    engagement_score: float = 0.0
    last_active: str = ""
    preferences: dict = field(default_factory=dict)


@dataclass
class ContentJob:
    agent_name: str
    job_type: str
    payload: dict = field(default_factory=dict)
    status: str = "pending"
    priority: int = 2
    attempts: int = 0
    result: dict | None = None
    error_msg: str | None = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    started_at: str = ""
    completed_at: str = ""


# ─────────────────────────────────────────────────────────────────────────────
# REPOSITORIES
# ─────────────────────────────────────────────────────────────────────────────


class LessonRepository:
    def save(self, lesson: Lesson) -> None:
        with db_cursor() as cur:
            cur.execute(
                """
                INSERT INTO lessons
                  (id, domain, domain_id, module, title, difficulty,
                   estimated_minutes, content, key_takeaways, misconceptions,
                   real_example, related_lessons, pedagogy_score, status,
                   version, created_at, updated_at, next_review_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(id) DO UPDATE SET
                  content=excluded.content,
                  title=excluded.title,
                  status=excluded.status,
                  updated_at=excluded.updated_at,
                  key_takeaways=excluded.key_takeaways,
                  misconceptions=excluded.misconceptions,
                  real_example=excluded.real_example,
                  related_lessons=excluded.related_lessons,
                  pedagogy_score=excluded.pedagogy_score,
                  version=excluded.version,
                  next_review_at=excluded.next_review_at
            """,
                (
                    lesson.id,
                    lesson.domain,
                    lesson.domain_id,
                    lesson.module,
                    lesson.title,
                    lesson.difficulty,
                    lesson.estimated_minutes,
                    lesson.content,
                    json.dumps(lesson.key_takeaways, ensure_ascii=False),
                    json.dumps(lesson.misconceptions, ensure_ascii=False),
                    json.dumps(lesson.real_example, ensure_ascii=False),
                    json.dumps(lesson.related_lessons, ensure_ascii=False),
                    lesson.pedagogy_score,
                    lesson.status,
                    lesson.version,
                    lesson.created_at,
                    lesson.updated_at,
                    lesson.next_review_at,
                ),
            )

    def get(self, lesson_id: str) -> Lesson | None:
        with db_cursor() as cur:
            cur.execute("SELECT * FROM lessons WHERE id=?", (lesson_id,))
            row = cur.fetchone()
        return self._row_to_lesson(row) if row else None

    def list_by_domain(self, domain: str, status: str = "published") -> list[Lesson]:
        with db_cursor() as cur:
            cur.execute(
                "SELECT * FROM lessons WHERE domain=? AND status=? ORDER BY module, id",
                (domain, status),
            )
            rows = cur.fetchall()
        return [self._row_to_lesson(r) for r in rows]

    def list_for_review(self, before_date: str) -> list[Lesson]:
        with db_cursor() as cur:
            cur.execute(
                "SELECT * FROM lessons WHERE next_review_at <= ? AND status='published'",
                (before_date,),
            )
            return [self._row_to_lesson(r) for r in cur.fetchall()]

    def all_published(self) -> list[Lesson]:
        with db_cursor() as cur:
            cur.execute("SELECT * FROM lessons WHERE status='published'")
            return [self._row_to_lesson(r) for r in cur.fetchall()]

    def stats(self) -> dict:
        with db_cursor() as cur:
            cur.execute("SELECT domain, count(*) as n FROM lessons GROUP BY domain")
            by_domain = {r["domain"]: r["n"] for r in cur.fetchall()}
            cur.execute("SELECT count(*) as n FROM lessons WHERE status='published'")
            total = cur.fetchone()["n"]
        return {"total_published": total, "by_domain": by_domain}

    @staticmethod
    def _row_to_lesson(row) -> Lesson:
        return Lesson(
            id=row["id"],
            domain=row["domain"],
            domain_id=row["domain_id"],
            module=row["module"],
            title=row["title"],
            difficulty=row["difficulty"],
            content=row["content"],
            estimated_minutes=row["estimated_minutes"],
            key_takeaways=json.loads(row["key_takeaways"] or "[]"),
            misconceptions=json.loads(row["misconceptions"] or "[]"),
            real_example=json.loads(row["real_example"] or "{}"),
            related_lessons=json.loads(row["related_lessons"] or "[]"),
            pedagogy_score=row["pedagogy_score"] or 0.0,
            status=row["status"],
            version=row["version"],
            created_at=row["created_at"] or "",
            updated_at=row["updated_at"] or "",
            next_review_at=row["next_review_at"] or "",
        )


class LessonComponentRepository:
    def save(self, component: LessonComponent) -> int:
        with db_cursor() as cur:
            cur.execute(
                """
                INSERT INTO lesson_components (lesson_id, type, content, order_idx, created_at)
                VALUES (?,?,?,?,?)
            """,
                (
                    component.lesson_id,
                    component.type,
                    json.dumps(component.content, ensure_ascii=False),
                    component.order_idx,
                    component.created_at,
                ),
            )
            return cur.lastrowid

    def get_for_lesson(self, lesson_id: str, type_: str | None = None) -> list[dict]:
        with db_cursor() as cur:
            if type_:
                cur.execute(
                    "SELECT * FROM lesson_components WHERE lesson_id=? AND type=? ORDER BY order_idx",
                    (lesson_id, type_),
                )
            else:
                cur.execute(
                    "SELECT * FROM lesson_components WHERE lesson_id=? ORDER BY order_idx",
                    (lesson_id,),
                )
            rows = cur.fetchall()
        return [
            {
                "id": r["id"],
                "type": r["type"],
                "content": json.loads(r["content"]),
                "order_idx": r["order_idx"],
            }
            for r in rows
        ]


class UserProgressRepository:
    def upsert(self, user_id: str, lesson_id: str, **fields) -> None:
        now = datetime.utcnow().isoformat()
        with db_cursor() as cur:
            cur.execute(
                """
                INSERT INTO user_progress
                  (user_id, lesson_id, completed_at, quiz_score, time_spent_sec,
                   feedback_rating, feedback_text, feedback_tags, scroll_depth, return_count)
                VALUES (?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(user_id, lesson_id) DO UPDATE SET
                  completed_at = COALESCE(excluded.completed_at, completed_at),
                  quiz_score = COALESCE(excluded.quiz_score, quiz_score),
                  time_spent_sec = COALESCE(excluded.time_spent_sec, time_spent_sec),
                  feedback_rating = COALESCE(excluded.feedback_rating, feedback_rating),
                  feedback_text = COALESCE(excluded.feedback_text, feedback_text),
                  feedback_tags = COALESCE(excluded.feedback_tags, feedback_tags),
                  scroll_depth = COALESCE(excluded.scroll_depth, scroll_depth),
                  return_count = return_count + 1
            """,
                (
                    user_id,
                    lesson_id,
                    fields.get("completed_at", now),
                    fields.get("quiz_score"),
                    fields.get("time_spent_sec"),
                    fields.get("feedback_rating"),
                    fields.get("feedback_text"),
                    json.dumps(fields.get("feedback_tags", [])),
                    fields.get("scroll_depth"),
                    0,
                ),
            )

    def completed_for_user(self, user_id: str) -> list[str]:
        with db_cursor() as cur:
            cur.execute(
                "SELECT lesson_id FROM user_progress WHERE user_id=? AND completed_at IS NOT NULL",
                (user_id,),
            )
            return [r["lesson_id"] for r in cur.fetchall()]

    def low_rated_lessons(self, min_count: int = 5, max_avg: float = 3.0) -> list[dict]:
        with db_cursor() as cur:
            cur.execute(
                """
                SELECT lesson_id,
                       count(*) as n,
                       avg(feedback_rating) as avg_rating,
                       sum(CASE WHEN 'confusing' IN (feedback_tags) THEN 1 ELSE 0 END) as confusing_count
                FROM user_progress
                WHERE feedback_rating IS NOT NULL
                GROUP BY lesson_id
                HAVING n >= ? AND avg_rating <= ?
                ORDER BY avg_rating ASC
            """,
                (min_count, max_avg),
            )
            return [dict(r) for r in cur.fetchall()]


class UserProfileRepository:
    def get_or_create(self, user_id: str) -> UserProfile:
        with db_cursor() as cur:
            cur.execute("SELECT * FROM user_profile WHERE user_id=?", (user_id,))
            row = cur.fetchone()
            if row:
                return self._row_to_profile(row)
            # Create default
            now = datetime.utcnow().isoformat()
            cur.execute(
                """
                INSERT INTO user_profile (user_id, last_active) VALUES (?,?)
            """,
                (user_id, now),
            )
        return UserProfile(user_id=user_id, last_active=now)

    def save(self, profile: UserProfile) -> None:
        now = datetime.utcnow().isoformat()
        with db_cursor() as cur:
            cur.execute(
                """
                INSERT INTO user_profile
                  (user_id, domain_scores, learning_path, weak_spots, next_lessons,
                   streak, streak_updated, total_lessons, learning_style,
                   daily_minutes, primary_goal, engagement_score, last_active, preferences)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(user_id) DO UPDATE SET
                  domain_scores=excluded.domain_scores,
                  learning_path=excluded.learning_path,
                  weak_spots=excluded.weak_spots,
                  next_lessons=excluded.next_lessons,
                  streak=excluded.streak,
                  streak_updated=excluded.streak_updated,
                  total_lessons=excluded.total_lessons,
                  learning_style=excluded.learning_style,
                  daily_minutes=excluded.daily_minutes,
                  primary_goal=excluded.primary_goal,
                  engagement_score=excluded.engagement_score,
                  last_active=excluded.last_active,
                  preferences=excluded.preferences
            """,
                (
                    profile.user_id,
                    json.dumps(profile.domain_scores),
                    json.dumps(profile.learning_path),
                    json.dumps(profile.weak_spots),
                    json.dumps(profile.next_lessons),
                    profile.streak,
                    profile.streak_updated,
                    profile.total_lessons,
                    profile.learning_style,
                    profile.daily_minutes,
                    profile.primary_goal,
                    profile.engagement_score,
                    now,
                    json.dumps(profile.preferences),
                ),
            )

    @staticmethod
    def _row_to_profile(row) -> UserProfile:
        return UserProfile(
            user_id=row["user_id"],
            domain_scores=json.loads(row["domain_scores"] or "{}"),
            learning_path=json.loads(row["learning_path"] or "[]"),
            weak_spots=json.loads(row["weak_spots"] or "[]"),
            next_lessons=json.loads(row["next_lessons"] or "[]"),
            streak=row["streak"] or 0,
            streak_updated=row["streak_updated"] or "",
            total_lessons=row["total_lessons"] or 0,
            learning_style=row["learning_style"] or "visual",
            daily_minutes=row["daily_minutes"] or 15,
            primary_goal=row["primary_goal"] or "active_trader",
            engagement_score=row["engagement_score"] or 0.0,
            last_active=row["last_active"] or "",
            preferences=json.loads(row["preferences"] or "{}"),
        )


class ContentJobRepository:
    def enqueue(self, job: ContentJob) -> int:
        with db_cursor() as cur:
            cur.execute(
                """
                INSERT INTO content_jobs
                  (agent_name, job_type, payload, status, priority, attempts, created_at)
                VALUES (?,?,?,?,?,?,?)
            """,
                (
                    job.agent_name,
                    job.job_type,
                    json.dumps(job.payload, ensure_ascii=False),
                    job.status,
                    job.priority,
                    job.attempts,
                    job.created_at,
                ),
            )
            return cur.lastrowid

    def next_pending(self) -> dict | None:
        with db_cursor() as cur:
            cur.execute("""
                SELECT * FROM content_jobs
                WHERE status='pending'
                ORDER BY priority ASC, created_at ASC
                LIMIT 1
            """)
            row = cur.fetchone()
        return dict(row) if row else None

    def update_status(
        self, job_id: int, status: str, result: dict | None = None, error: str | None = None
    ) -> None:
        now = datetime.utcnow().isoformat()
        with db_cursor() as cur:
            if status == "running":
                cur.execute(
                    "UPDATE content_jobs SET status=?, started_at=?, attempts=attempts+1 WHERE id=?",
                    (status, now, job_id),
                )
            else:
                cur.execute(
                    """
                    UPDATE content_jobs SET status=?, completed_at=?,
                      result=?, error_msg=? WHERE id=?
                """,
                    (status, now, json.dumps(result) if result else None, error, job_id),
                )


class AgentLogRepository:
    def log(
        self,
        agent_name: str,
        action: str,
        input_summary: str = "",
        output_summary: str = "",
        tokens_used: int = 0,
        duration_ms: float = 0,
        status: str = "ok",
    ) -> None:
        with db_cursor() as cur:
            cur.execute(
                """
                INSERT INTO agent_logs
                  (agent_name, action, input_summary, output_summary,
                   tokens_used, duration_ms, status, timestamp)
                VALUES (?,?,?,?,?,?,?,?)
            """,
                (
                    agent_name,
                    action,
                    input_summary,
                    output_summary,
                    tokens_used,
                    duration_ms,
                    status,
                    datetime.utcnow().isoformat(),
                ),
            )

    def recent(self, agent_name: str | None = None, limit: int = 50) -> list[dict]:
        with db_cursor() as cur:
            if agent_name:
                cur.execute(
                    "SELECT * FROM agent_logs WHERE agent_name=? ORDER BY timestamp DESC LIMIT ?",
                    (agent_name, limit),
                )
            else:
                cur.execute("SELECT * FROM agent_logs ORDER BY timestamp DESC LIMIT ?", (limit,))
            return [dict(r) for r in cur.fetchall()]
