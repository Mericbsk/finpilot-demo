"""Security regressions for the legacy Borsa Academy API surface."""

from __future__ import annotations

import asyncio
import json
import time

import pytest
from auth.tokens import JWTHandler
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from api.middleware.rate_limiter import limiter
from api.routers import academy

TEST_SECRET = "academy-api-test-secret-not-for-production"  # pragma: allowlist secret


class FakeOrchestrator:
    def system_status(self):
        return {"total_published_lessons": 0, "pending_jobs": 0}

    def get_user_dashboard(self, user_id: str):
        return {"user_id": user_id, "next_lessons": []}

    def onboard_user(self, user_id: str, answers: dict):
        return {"user_id": user_id, "answers": answers}

    def generate_lesson_now(self, **kwargs):
        return {"success": True, "lesson_id": "synthetic-lesson", "status": "draft"}

    def seed_starter_content(self):
        return {"generated": 0, "skipped": 0, "processed": 0}

    def run_daily(self):
        return {"jobs_processed": 0, "published": 0}


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("FINPILOT_SECRET_KEY", TEST_SECRET)
    app = FastAPI()
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    from api.middleware.request_body_limit import AcademyRequestBodyLimitMiddleware

    app.add_middleware(AcademyRequestBodyLimitMiddleware)
    app.include_router(academy.router, prefix="/api/v1")
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def fake_orchestrator(monkeypatch: pytest.MonkeyPatch):
    orchestrator = FakeOrchestrator()
    monkeypatch.setattr(academy, "_get_orch", lambda: orchestrator)
    return orchestrator


def _token(user_id: str, role: str = "user", token_type: str = "access") -> str:
    now = int(time.time())
    return JWTHandler(TEST_SECRET).encode(
        {
            "sub": user_id,
            "exp": now + 3600,
            "iat": now,
            "jti": f"academy-test-{user_id}-{role}",
            "type": token_type,
            "role": role,
        }
    )


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_admin_routes_require_admin_and_authorize_admin(client, fake_orchestrator):
    routes = [
        ("/api/v1/academy/generate", {"domain": "budgeting", "module": "intro", "title": "Budgeting"}),
        ("/api/v1/academy/seed", None),
        ("/api/v1/academy/run/daily", None),
    ]
    user_headers = _auth(_token("regular-user"))
    admin_headers = _auth(_token("academy-admin", "admin"))

    for path, payload in routes:
        anonymous = client.post(path, json=payload) if payload else client.post(path)
        regular = client.post(path, json=payload, headers=user_headers) if payload else client.post(path, headers=user_headers)
        allowed = client.post(path, json=payload, headers=admin_headers) if payload else client.post(path, headers=admin_headers)

        assert anonymous.status_code == 401
        assert regular.status_code == 403
        assert allowed.status_code == 200


def test_invalid_token_and_refresh_token_are_rejected(client):
    path = "/api/v1/academy/seed"
    assert client.post(path, headers=_auth("not-a-jwt")).status_code == 401
    assert client.post(path, headers=_auth(_token("admin", "admin", "refresh"))).status_code == 401


def test_dashboard_and_onboarding_are_bound_to_authenticated_identity(
    client, fake_orchestrator
):
    headers = _auth(_token("learner-1"))

    anonymous_dashboard = client.get("/api/v1/academy/dashboard/learner-1")
    anonymous_onboarding = client.post(
        "/api/v1/academy/onboard",
        json={"user_id": "learner-1", "answers": {}},
    )
    own_dashboard = client.get("/api/v1/academy/dashboard/learner-1", headers=headers)
    other_dashboard = client.get("/api/v1/academy/dashboard/learner-2", headers=headers)
    own_onboarding = client.post(
        "/api/v1/academy/onboard",
        json={"user_id": "learner-1", "answers": {"goal": "basics"}},
        headers=headers,
    )
    other_onboarding = client.post(
        "/api/v1/academy/onboard",
        json={"user_id": "learner-2", "answers": {}},
        headers=headers,
    )

    assert anonymous_dashboard.status_code == 401
    assert anonymous_onboarding.status_code == 401
    assert own_dashboard.status_code == 200
    assert other_dashboard.status_code == 404
    assert own_onboarding.status_code == 200
    assert other_onboarding.status_code == 403


def test_legacy_lesson_route_fails_closed_without_querying_sqlite(monkeypatch, client):
    monkeypatch.setattr(academy, "_get_orch", lambda: pytest.fail("legacy DB must not be read"))

    response = client.get("/api/v1/academy/lesson/draft-id")

    assert response.status_code == 503
    assert response.json()["detail"] == "canonical lesson catalog unavailable"


def test_status_is_admin_only_and_route_errors_are_sanitized(monkeypatch, client):
    monkeypatch.setattr(
        academy,
        "_get_orch",
        lambda: (_ for _ in ()).throw(RuntimeError("private database detail")),
    )
    admin_headers = _auth(_token("academy-admin", "admin"))

    assert client.get("/api/v1/academy/status").status_code == 401
    assert client.get("/api/v1/academy/status", headers=_auth(_token("user"))).status_code == 403
    response = client.get("/api/v1/academy/status", headers=admin_headers)

    assert response.status_code == 503
    assert "private database detail" not in response.text


def test_costly_admin_route_is_rate_limited(client, fake_orchestrator):
    headers = _auth(_token("academy-admin", "admin"))
    payload = {"domain": "budgeting", "module": "intro", "title": "Budgeting"}
    responses = [
        client.post("/api/v1/academy/generate", json=payload, headers=headers)
        for _ in range(65)
    ]

    assert any(response.status_code == 429 for response in responses)
    assert all(response.status_code in {200, 429} for response in responses)


def test_request_validation_response_does_not_echo_body(monkeypatch):
    monkeypatch.setenv("FINPILOT_SKIP_DOTENV", "1")
    from fastapi.exceptions import RequestValidationError
    from starlette.requests import Request

    from api.main import validation_exception_handler

    request = Request({"type": "http", "method": "POST", "path": "/academy/onboard", "headers": []})
    error = RequestValidationError([], body={"answer": "private-marker"})
    response = asyncio.run(validation_exception_handler(request, error))

    assert response.status_code == 422
    assert b"private-marker" not in response.body
    assert json.loads(response.body) == {"detail": "Request validation failed"}


def test_quality_guard_approval_waits_for_human_publication(monkeypatch, tmp_path):
    from academy import models
    from academy.agents.quality_guard import QualityGuardAgent
    from academy.models import AgentLogRepository, Lesson, LessonComponentRepository, LessonRepository

    db_path = tmp_path / "academy.sqlite3"
    models.init_db(db_path)
    original_cursor = models.db_cursor
    monkeypatch.setattr(models, "db_cursor", lambda: original_cursor(db_path))

    repository = LessonRepository()
    lesson = Lesson(
        id="synthetic-human-review",
        domain="fundamental-finance",
        domain_id=1,
        module="review-test",
        title="Synthetic review lesson",
        difficulty="beginner",
        content="Synthetic test content only.",
    )
    repository.save(lesson)
    guard = QualityGuardAgent()
    guard.lesson_repo = repository
    guard.component_repo = LessonComponentRepository()
    guard.log_repo = AgentLogRepository()
    monkeypatch.setattr(guard, "_heuristic_checks", lambda *args: [])
    monkeypatch.setattr(
        guard,
        "_llm_review",
        lambda *args: {"decision": "APPROVED", "scores": {}, "average": 8.0},
    )

    result = guard.review_lesson(lesson)

    assert result["decision"] == "APPROVED"
    assert repository.get(lesson.id).status == "pending_review"
    assert repository.stats()["total_published"] == 0


def test_lesson_repository_cannot_publish_or_overwrite_published_rows(monkeypatch, tmp_path):
    from academy import models
    from academy.models import Lesson, LessonRepository

    db_path = tmp_path / "academy.sqlite3"
    models.init_db(db_path)
    original_cursor = models.db_cursor
    monkeypatch.setattr(models, "db_cursor", lambda: original_cursor(db_path))
    repository = LessonRepository()

    forbidden = Lesson(
        id="synthetic-forbidden-publish",
        domain="fundamental-finance",
        domain_id=1,
        module="review-test",
        title="Synthetic publication boundary",
        difficulty="beginner",
        content="Synthetic test content only.",
        status="published",
    )
    with pytest.raises(ValueError, match="human-approved release"):
        repository.save(forbidden)
    assert repository.get(forbidden.id) is None

    lesson = Lesson(
        id="synthetic-immutable-release",
        domain="fundamental-finance",
        domain_id=1,
        module="version-test",
        title="Synthetic released lesson",
        difficulty="beginner",
        content="Original synthetic release.",
    )
    repository.save(lesson)
    with models.db_cursor() as cur:
        cur.execute("UPDATE lessons SET status='published' WHERE id=?", (lesson.id,))
    changed = repository.get(lesson.id)
    assert changed is not None
    changed.status = "draft"
    changed.title = "Changed synthetic title"
    changed.content = "Changed synthetic content."

    with pytest.raises(ValueError, match="lessons are immutable"):
        repository.save(changed)

    persisted = repository.get(lesson.id)
    assert persisted is not None
    assert persisted.status == "published"
    assert persisted.title == "Synthetic released lesson"
    assert persisted.content == "Original synthetic release."


def test_lesson_repository_rejects_unverified_approval_insert(monkeypatch, tmp_path):
    from academy import models
    from academy.models import Lesson, LessonRepository

    db_path = tmp_path / "approval.sqlite3"
    models.init_db(db_path)
    original_cursor = models.db_cursor
    monkeypatch.setattr(models, "db_cursor", lambda: original_cursor(db_path))
    repository = LessonRepository()
    lesson = Lesson(
        id="synthetic-unverified-approval",
        domain="fundamental-finance",
        domain_id=1,
        module="approval-test",
        title="Synthetic approval boundary",
        difficulty="beginner",
        content="Synthetic test content only.",
        status="approved",
    )

    with pytest.raises(ValueError, match="explicit human approval operation"):
        repository.save(lesson)

    assert repository.get(lesson.id) is None


def test_starter_seed_keeps_lessons_draft(monkeypatch, tmp_path):
    from academy import models
    from academy.models import LessonRepository
    from academy import seed_content

    db_path = tmp_path / "seed.sqlite3"
    original_cursor = models.db_cursor
    monkeypatch.setattr(models, "db_cursor", lambda: original_cursor(db_path))
    monkeypatch.setattr(seed_content, "init_db", lambda: models.init_db(db_path))
    monkeypatch.setattr(
        seed_content,
        "SEED_LESSONS",
        [{
            "id": "synthetic-seed",
            "domain": "fundamental-finance",
            "domain_id": 1,
            "module": "seed-test",
            "title": "Synthetic seed lesson",
            "difficulty": "beginner",
            "content": "Synthetic test content only.",
            "quizzes": [],
            "flashcards": [],
        }],
    )

    result = seed_content.seed_all()

    lesson = LessonRepository().get("synthetic-seed")
    assert result == {"inserted": 1, "skipped": 0}
    assert lesson is not None and lesson.status == "draft"
    assert LessonRepository().stats()["total_published"] == 0


@pytest.mark.parametrize("protected_status", ["published", "archived"])
def test_updater_skips_protected_lesson_before_provider_call(
    monkeypatch, tmp_path, protected_status
):
    from academy import models
    from academy.agents.content_updater import ContentUpdaterAgent
    from academy.models import Lesson, LessonRepository

    db_path = tmp_path / "updater.sqlite3"
    models.init_db(db_path)
    original_cursor = models.db_cursor
    monkeypatch.setattr(models, "db_cursor", lambda: original_cursor(db_path))
    repository = LessonRepository()
    lesson = Lesson(
        id="synthetic-updater-protected",
        domain="fundamental-finance",
        domain_id=1,
        module="version-test",
        title="Synthetic protected lesson",
        difficulty="beginner",
        content="Original synthetic release.",
    )
    repository.save(lesson)
    with models.db_cursor() as cur:
        cur.execute("UPDATE lessons SET status=? WHERE id=?", (protected_status, lesson.id))
    protected = repository.get(lesson.id)
    assert protected is not None

    provider_calls = []
    monkeypatch.setattr(
        "academy.llm_provider.get_academy_provider",
        lambda: provider_calls.append(True),
    )
    updater = ContentUpdaterAgent()
    updater.lesson_repo = repository

    assert updater.update_lesson(protected, "synthetic test update") is None
    assert provider_calls == []
    assert repository.get(lesson.id).content == "Original synthetic release."


def test_daily_approval_is_reported_as_pending_not_published(monkeypatch):
    from academy.orchestrator import AcademyOrchestrator

    orchestrator = AcademyOrchestrator.__new__(AcademyOrchestrator)
    orchestrator.gap_detector = type("GapDetector", (), {"run_daily_scan": lambda self: []})()
    orchestrator.quality_guard = type(
        "QualityGuard",
        (),
        {"review_pending_lessons": lambda self: [{"decision": "APPROVED"}]},
    )()
    orchestrator._process_pending_jobs = lambda max_jobs: 0

    result = orchestrator.run_daily()

    assert result["pending_human_review"] == 1
    assert result["published"] == 0


def test_academy_body_limit_at_and_around_boundary():
    from api.middleware.request_body_limit import (
        ACADEMY_MAX_REQUEST_BODY_BYTES,
        AcademyRequestBodyLimitMiddleware,
    )
    app = FastAPI()
    app.add_middleware(AcademyRequestBodyLimitMiddleware)
    received_sizes = []

    @app.post("/api/v1/academy/body-probe")
    async def body_probe(request: Request):
        body = await request.body()
        received_sizes.append(len(body))
        return {"size": len(body)}

    responses = []
    with TestClient(app) as test_client:
        for size in (
            ACADEMY_MAX_REQUEST_BODY_BYTES - 1,
            ACADEMY_MAX_REQUEST_BODY_BYTES,
            ACADEMY_MAX_REQUEST_BODY_BYTES + 1,
        ):
            prefix, suffix = b'{"title":"', b'"}'
            body = prefix + b"x" * (size - len(prefix) - len(suffix)) + suffix
            responses.append(
                test_client.post(
                    "/api/v1/academy/body-probe",
                    content=body,
                    headers={"Content-Type": "application/json"},
                )
            )

    assert [response.status_code for response in responses] == [200, 200, 413]
    assert [response.json() for response in responses[:2]] == [
        {"size": ACADEMY_MAX_REQUEST_BODY_BYTES - 1},
        {"size": ACADEMY_MAX_REQUEST_BODY_BYTES},
    ]
    assert responses[2].json() == {"detail": "Request body too large"}
    assert received_sizes == [
        ACADEMY_MAX_REQUEST_BODY_BYTES - 1,
        ACADEMY_MAX_REQUEST_BODY_BYTES,
    ]


@pytest.mark.parametrize(
    "headers",
    [[], [(b"content-length", b"1")]],
    ids=["chunked-without-length", "underreported-length"],
)
def test_academy_body_limit_counts_streamed_bytes(headers):
    from api.middleware.request_body_limit import AcademyRequestBodyLimitMiddleware
    from fastapi.responses import JSONResponse

    handler_calls = []
    sent = []
    messages = iter(
        [
            {"type": "http.request", "body": b"1234", "more_body": True},
            {"type": "http.request", "body": b"5", "more_body": False},
        ]
    )

    async def receive():
        return next(messages)

    async def send(message):
        sent.append(message)

    async def downstream(scope, receive, send):
        handler_calls.append(True)
        await JSONResponse({"ok": True})(scope, receive, send)

    scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.3"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "http",
        "path": "/api/v1/academy/onboard",
        "raw_path": b"/api/v1/academy/onboard",
        "query_string": b"",
        "root_path": "",
        "headers": headers,
        "client": ("127.0.0.1", 1234),
        "server": ("testserver", 80),
    }

    async def run_middleware():
        await AcademyRequestBodyLimitMiddleware(downstream, max_body_bytes=4)(
            scope, receive, send
        )

    asyncio.run(run_middleware())

    assert not handler_calls
    assert sent[0]["type"] == "http.response.start"
    assert sent[0]["status"] == 413


def test_main_app_registers_academy_body_limit(monkeypatch):
    monkeypatch.setenv("FINPILOT_SKIP_DOTENV", "1")
    from api.main import app as main_app
    from api.middleware.request_body_limit import AcademyRequestBodyLimitMiddleware

    assert any(item.cls is AcademyRequestBodyLimitMiddleware for item in main_app.user_middleware)


def test_oversized_generate_request_does_not_reach_orchestrator(
    client, fake_orchestrator, monkeypatch
):
    from api.middleware.request_body_limit import ACADEMY_MAX_REQUEST_BODY_BYTES

    monkeypatch.setattr(
        fake_orchestrator,
        "generate_lesson_now",
        lambda **kwargs: pytest.fail("oversized requests must not reach generation"),
    )
    body = json.dumps({
        "domain": "budgeting",
        "module": "intro",
        "title": "x" * ACADEMY_MAX_REQUEST_BODY_BYTES,
    }).encode()

    response = client.post(
        "/api/v1/academy/generate",
        content=body,
        headers={**_auth(_token("academy-admin", "admin")), "Content-Type": "application/json"},
    )

    assert len(body) > ACADEMY_MAX_REQUEST_BODY_BYTES
    assert response.status_code == 413


@pytest.mark.parametrize(
    "protected_status", ["approved", "pending_review", "published", "archived"]
)
def test_generation_preserves_protected_lessons(monkeypatch, protected_status):
    from academy.agents.content_generator import ContentGeneratorAgent
    from academy.models import Lesson

    existing = Lesson(
        id="synthetic-protected-generation",
        domain="fundamental-finance",
        domain_id=1,
        module="review-test",
        title="Synthetic protected lesson",
        difficulty="beginner",
        content="Original synthetic content.",
        status=protected_status,
    )

    class ExistingLessonRepository:
        def get(self, lesson_id):
            assert lesson_id == existing.id
            return existing

    generator = ContentGeneratorAgent()
    generator.lesson_repo = ExistingLessonRepository()
    monkeypatch.setattr(
        generator,
        "_call_llm",
        lambda *args, **kwargs: pytest.fail("protected lessons must not be regenerated"),
    )

    result = generator.generate_lesson(
        domain_slug="fundamental-finance",
        module="review-test",
        title="Synthetic protected lesson",
        lesson_id=existing.id,
    )

    assert result is existing
    assert result.status == protected_status
    assert result.content == "Original synthetic content."


@pytest.mark.parametrize(
    "protected_status", ["approved", "pending_review", "archived"]
)
def test_repository_does_not_overwrite_protected_lessons(
    monkeypatch, tmp_path, protected_status
):
    from academy import models
    from academy.models import Lesson, LessonRepository

    db_path = tmp_path / "academy.sqlite3"
    models.init_db(db_path)
    original_cursor = models.db_cursor
    monkeypatch.setattr(models, "db_cursor", lambda: original_cursor(db_path))
    repository = LessonRepository()
    lesson = Lesson(
        id="synthetic-protected-review",
        domain="fundamental-finance",
        domain_id=1,
        module="review-test",
        title="Synthetic protected lesson",
        difficulty="beginner",
        content="Original synthetic content.",
        status="draft",
        version="1.2",
    )
    repository.save(lesson)
    with models.db_cursor() as cur:
        cur.execute("UPDATE lessons SET status=? WHERE id=?", (protected_status, lesson.id))
    changed = repository.get(lesson.id)
    assert changed is not None
    changed.status = "draft"
    changed.title = "Changed synthetic lesson"
    changed.content = "Changed synthetic content."
    changed.version = "9.9"

    with pytest.raises(
        ValueError,
        match="approved, pending_review, published, and archived lessons are immutable",
    ):
        repository.save(changed)

    persisted = repository.get(lesson.id)
    assert persisted is not None
    assert persisted.status == protected_status
    assert persisted.title == "Synthetic protected lesson"
    assert persisted.content == "Original synthetic content."
    assert persisted.version == "1.2"


def test_repository_allows_draft_upserts(monkeypatch, tmp_path):
    from academy import models
    from academy.models import Lesson, LessonRepository

    db_path = tmp_path / "academy.sqlite3"
    models.init_db(db_path)
    original_cursor = models.db_cursor
    monkeypatch.setattr(models, "db_cursor", lambda: original_cursor(db_path))
    repository = LessonRepository()
    lesson = Lesson(
        id="synthetic-draft-upsert",
        domain="fundamental-finance",
        domain_id=1,
        module="draft-test",
        title="Original draft lesson",
        difficulty="beginner",
        content="Original draft content.",
        version="1.0",
    )

    repository.save(lesson)
    changed = repository.get(lesson.id)
    assert changed is not None
    changed.title = "Updated draft lesson"
    changed.content = "Updated draft content."
    changed.version = "1.1"
    repository.save(changed)

    persisted = repository.get(lesson.id)
    assert persisted is not None
    assert persisted.status == "draft"
    assert persisted.title == "Updated draft lesson"
    assert persisted.content == "Updated draft content."
    assert persisted.version == "1.1"
    with models.db_cursor() as cur:
        cur.execute("SELECT COUNT(*) AS count FROM lessons WHERE id=?", (lesson.id,))
        assert cur.fetchone()["count"] == 1