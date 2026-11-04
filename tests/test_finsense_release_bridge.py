from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from api.middleware.rate_limiter import limiter
from api.routers import academy
from api.services.finsense_release import FinSenseReleaseError, load_catalog

LOCALES = ("tr", "en", "de")
ROLES = ("accuracy", "pedagogy", "critical")
POLICY_VERSION = "autonomous-content-v1.1.0"
RELEASE_ID = "rel-2026-10-19-budgeting"
GATE_CHECKS = (
    "lesson_and_source_schema",
    "deterministic_content_gates",
    "included_locale_consistency",
    "independent_hash_bound_reviews",
    "package_integrity",
)


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def _write(root: Path, relative: str, value: object) -> bytes:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = _json_bytes(value)
    path.write_bytes(raw)
    return raw


def _schema(root: Path, name: str, value: dict) -> None:
    _write(root, f"schemas/{name}.schema.json", value)


def _lesson(locale: str) -> dict:
    return {
        "concept_id": "budgeting",
        "locale": locale,
        "version": 1,
        "status": "published",
        "level": "beginner",
        "jurisdiction": ["GLOBAL"],
        "author": {"role": "writer", "id": "writer-1"},
        "title": {"tr": "Test bütçesi", "en": "Test budget", "de": "Testbudget"}[locale],
        "learning_objectives": ["Identify planned income and spending in a simple budget."],
        "body_md": "A budget is a plan for expected income and spending over a chosen period.",
        "claims": [{
            "id": "c1",
            "text": "A budget records planned income and spending.",
            "type": "conceptual",
            "source_ids": ["src-test-primary"],
        }],
        "quiz": [{
            "id": "q1",
            "question": "What does a simple budget organize?",
            "options": ["Planned income and spending", "Only a person's age", "The weather"],
            "correct_index": 0,
            "explanation": "A budget organizes expected income and planned spending.",
            "claim_ids": ["c1"],
        }],
    }


def _create_package(root: Path, *, jurisdiction: tuple[str, ...] = ("GLOBAL",)) -> Path:
    lesson_schema = {
        "type": "object",
        "required": [
            "concept_id", "locale", "version", "status", "level", "jurisdiction",
            "author", "title", "learning_objectives", "body_md", "claims", "quiz",
        ],
    }
    for name in ("release", "review"):
        _schema(root, name, {"type": "object"})
    _schema(root, "lesson", lesson_schema)
    _schema(root, "source", {
        "type": "array",
        "items": {"type": "object", "required": ["id", "title", "publisher", "url", "published", "accessed", "authority"]},
    })

    package_rel = f"content/releases/{RELEASE_ID}"
    package = root / package_rel
    source = {
        "id": "src-test-primary",
        "title": "Test financial education reference",
        "publisher": "Test institution",
        "url": "https://example.edu/finance-basics",
        "published": "2024",
        "accessed": "2026-10-17",
        "authority": "primary_official",
        "jurisdiction": ["GLOBAL"],
    }
    source_raw = _write(package, "sources/src-test-primary.json", source)
    source_entries = [{
        "source_id": source["id"],
        "path": "sources/src-test-primary.json",
        "sha256": hashlib.sha256(source_raw).hexdigest(),
    }]

    lesson_entries = []
    review_entries = []
    review_roles = ROLES + (("jurisdiction",) if jurisdiction != ("GLOBAL",) else ())
    for locale in LOCALES:
        lesson = _lesson(locale)
        lesson["jurisdiction"] = list(jurisdiction)
        lesson_digest = hashlib.sha256(_json_bytes(lesson)).hexdigest()
        lesson_path = f"content/lessons/budgeting/{locale}.json"
        lesson_raw = _write(package, lesson_path, lesson)
        lesson_entries.append({
            "concept_id": "budgeting",
            "locale": locale,
            "version": 1,
            "path": lesson_path,
            "sha256": hashlib.sha256(lesson_raw).hexdigest(),
            "content_hash": lesson_digest,
        })

        for role in review_roles:
            reviewer_id = f"reviewer-{role}"
            review = {
                "concept_id": "budgeting",
                "locale": locale,
                "content_version": lesson["version"],
                "role": role,
                "verdict": "approved",
                "reviewer_type": "agent",
                "reviewer_id": reviewer_id,
                "model_provider": f"provider-{role}",
                "model_family": f"family-{role}",
                "model_id": f"model-{role}",
                "model_digest": hashlib.sha256(f"model-digest-{role}".encode()).hexdigest(),
                "model_verified_before_at": "2026-10-19T11:59:59Z",
                "model_verified_after_at": "2026-10-19T12:00:01Z",
                "policy_version": POLICY_VERSION,
                "prompt_version": f"{role}-review-v1",
                "prompt_sha256": hashlib.sha256(f"prompt-{role}".encode()).hexdigest(),
                "run_id": f"run-{locale}-{role}",
                "attempt": 1,
                "reviewed_at": "2026-10-19T12:00:00Z",
                "execution_time_ms": 1200,
                "content_hash": lesson_digest,
                "response_sha256": hashlib.sha256(f"response-{locale}-{role}".encode()).hexdigest(),
                "summary": "The supplied claim matches the supplied source passage.",
                "findings": [],
                "evidence_refs": [{"claim_id": "c1", "source_id": source["id"]}],
                "attempt_errors": [],
                "error": None,
            }
            review_path = f"review_evidence/budgeting/{locale}.{role}.json"
            review_raw = _write(package, review_path, review)
            review_entries.append({
                "concept_id": "budgeting",
                "locale": locale,
                "role": role,
                "path": review_path,
                "sha256": hashlib.sha256(review_raw).hexdigest(),
                "content_hash": lesson_digest,
                "reviewer_id": reviewer_id,
                "model_provider": review["model_provider"],
                "model_family": review["model_family"],
                "model_id": review["model_id"],
                "model_digest": review["model_digest"],
                "policy_version": POLICY_VERSION,
                "prompt_version": review["prompt_version"],
                "prompt_sha256": review["prompt_sha256"],
                "run_id": review["run_id"],
                "reviewed_at": review["reviewed_at"],
                "evidence_refs": review["evidence_refs"],
            })

    inventory_entries = []
    for path in sorted(package.rglob("*")):
        if path.is_file():
            raw = path.read_bytes()
            inventory_entries.append({
                "path": path.relative_to(package).as_posix(),
                "sha256": hashlib.sha256(raw).hexdigest(),
                "size_bytes": len(raw),
            })

    manifest = {
        "release_id": RELEASE_ID,
        "manifest_schema_version": "2.1.0",
        "producer_version": "1.0.0",
        "created_at": "2026-10-19T12:00:00Z",
        "content_schema_version": "1.0.0",
        "policy_version": POLICY_VERSION,
        "lessons": lesson_entries,
        "review_evidence": review_entries,
        "source_evidence": source_entries,
        "package_inventory": inventory_entries,
        "release_gate": {
            "decision": "PASS",
            "publisher": "central-release-gate",
            "policy_version": POLICY_VERSION,
            "evaluated_at": "2026-10-19T12:00:00Z",
            "lesson_count": len(lesson_entries),
            "review_count": len(review_entries),
            "checks": [{"name": name, "status": "PASS"} for name in GATE_CHECKS],
        },
    }
    manifest_raw = _write(package, "manifest.json", manifest)
    _write(root, "content/releases/active.json", {
        "release_id": RELEASE_ID,
        "manifest_sha256": hashlib.sha256(manifest_raw).hexdigest(),
        "activated_at": "2026-10-19T12:00:00Z",
    })
    return package


@pytest.fixture
def client() -> TestClient:
    app = FastAPI()
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.include_router(academy.router, prefix="/api/v1")
    return TestClient(app)


def test_load_catalog_returns_hash_bound_canonical_content(tmp_path: Path) -> None:
    _create_package(tmp_path)

    catalog = load_catalog("tr", tmp_path)

    assert catalog["catalog_schema_version"] == "1.0.0"
    assert catalog["manifest"]["release_gate"]["decision"] == "PASS"
    assert catalog["lessons"][0]["lesson"] == _lesson("tr")
    assert catalog["lessons"][0]["manifest_entry"]["version"] == 1
    assert catalog["lessons"][0]["sources"][0]["id"] == "src-test-primary"


def test_load_catalog_requires_jurisdiction_review_for_scoped_lessons(tmp_path: Path) -> None:
    _create_package(tmp_path, jurisdiction=("EU",))

    catalog = load_catalog("tr", tmp_path)

    assert len(catalog["manifest"]["review_evidence"]) == 12


def test_load_catalog_rejects_tampered_lesson_file(tmp_path: Path) -> None:
    package = _create_package(tmp_path)
    lesson_path = package / "content/lessons/budgeting/tr.json"
    lesson_path.write_bytes(lesson_path.read_bytes() + b"\n")

    with pytest.raises(FinSenseReleaseError, match="lesson hash does not match"):
        load_catalog("tr", tmp_path)


def test_load_catalog_rejects_unsupported_manifest_version(tmp_path: Path) -> None:
    package = _create_package(tmp_path)
    manifest_path = package / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["manifest_schema_version"] = "99.0.0"
    manifest_raw = _write(package, "manifest.json", manifest)
    active_path = tmp_path / "content/releases/active.json"
    active = json.loads(active_path.read_text(encoding="utf-8"))
    active["manifest_sha256"] = hashlib.sha256(manifest_raw).hexdigest()
    _write(tmp_path, "content/releases/active.json", active)

    with pytest.raises(FinSenseReleaseError, match="unsupported release manifest version"):
        load_catalog("tr", tmp_path)


def test_load_catalog_rejects_non_independent_reviewers(tmp_path: Path) -> None:
    package = _create_package(tmp_path)
    manifest_path = package / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    first, second = manifest["review_evidence"][:2]
    second["reviewer_id"] = first["reviewer_id"]
    review_path = package / second["path"]
    review = json.loads(review_path.read_text(encoding="utf-8"))
    review["reviewer_id"] = first["reviewer_id"]
    review_raw = _write(package, second["path"], review)
    second["sha256"] = hashlib.sha256(review_raw).hexdigest()
    inventory_item = next(
        item for item in manifest["package_inventory"] if item["path"] == second["path"]
    )
    inventory_item["sha256"] = hashlib.sha256(review_raw).hexdigest()
    inventory_item["size_bytes"] = len(review_raw)
    manifest_raw = _write(package, "manifest.json", manifest)
    active_path = tmp_path / "content/releases/active.json"
    active = json.loads(active_path.read_text(encoding="utf-8"))
    active["manifest_sha256"] = hashlib.sha256(manifest_raw).hexdigest()
    _write(tmp_path, "content/releases/active.json", active)

    with pytest.raises(FinSenseReleaseError, match="reviewers are not independent"):
        load_catalog("tr", tmp_path)


def test_load_catalog_rejects_unsupported_producer_version(tmp_path: Path) -> None:
    package = _create_package(tmp_path)
    manifest_path = package / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["producer_version"] = "99.0.0"
    manifest_raw = _write(package, "manifest.json", manifest)
    active_path = tmp_path / "content/releases/active.json"
    active = json.loads(active_path.read_text(encoding="utf-8"))
    active["manifest_sha256"] = hashlib.sha256(manifest_raw).hexdigest()
    _write(tmp_path, "content/releases/active.json", active)

    with pytest.raises(FinSenseReleaseError, match="unsupported release producer version"):
        load_catalog("tr", tmp_path)


def test_load_catalog_rejects_tampered_package_inventory(tmp_path: Path) -> None:
    package = _create_package(tmp_path)
    manifest_path = package / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["package_inventory"][0]["size_bytes"] += 1
    manifest_raw = _write(package, "manifest.json", manifest)
    active_path = tmp_path / "content/releases/active.json"
    active = json.loads(active_path.read_text(encoding="utf-8"))
    active["manifest_sha256"] = hashlib.sha256(manifest_raw).hexdigest()
    _write(tmp_path, "content/releases/active.json", active)

    with pytest.raises(FinSenseReleaseError, match="inventory hash or size"):
        load_catalog("tr", tmp_path)


def test_load_catalog_rejects_incomplete_package_inventory(tmp_path: Path) -> None:
    package = _create_package(tmp_path)
    manifest_path = package / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["package_inventory"].pop()
    manifest_raw = _write(package, "manifest.json", manifest)
    active_path = tmp_path / "content/releases/active.json"
    active = json.loads(active_path.read_text(encoding="utf-8"))
    active["manifest_sha256"] = hashlib.sha256(manifest_raw).hexdigest()
    _write(tmp_path, "content/releases/active.json", active)

    with pytest.raises(FinSenseReleaseError, match="inventory is incomplete"):
        load_catalog("tr", tmp_path)


def test_load_catalog_rejects_unsupported_locale(tmp_path: Path) -> None:
    with pytest.raises(FinSenseReleaseError, match="unsupported lesson locale"):
        load_catalog("fr", tmp_path)


def test_load_catalog_requires_explicit_root_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("FINSENSE_CONTENT_ROOT", raising=False)

    with pytest.raises(FinSenseReleaseError, match="not configured"):
        load_catalog()


def test_academy_catalog_route_returns_verified_content_without_auth(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _create_package(tmp_path)
    monkeypatch.setenv("FINSENSE_CONTENT_ROOT", str(tmp_path))

    response = client.get("/api/v1/academy/catalog?locale=tr")

    assert response.status_code == 200
    assert response.json()["manifest"]["release_id"] == RELEASE_ID
    assert response.json()["lessons"][0]["lesson"]["concept_id"] == "budgeting"


def test_academy_catalog_route_fails_closed_without_canonical_root(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("FINSENSE_CONTENT_ROOT", raising=False)

    response = client.get("/api/v1/academy/catalog")

    assert response.status_code == 503
    assert response.json() == {"detail": "canonical lesson catalog unavailable"}