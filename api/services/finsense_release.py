"""Read and verify the active canonical FinSense release package."""

from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from jsonschema import Draft7Validator, FormatChecker

LOCALES = ("tr", "en", "de")
REQUIRED_REVIEW_ROLES = ("accuracy", "pedagogy", "critical")
CONDITIONAL_REVIEW_ROLES = ("jurisdiction",)
REVIEW_ROLES = REQUIRED_REVIEW_ROLES + CONDITIONAL_REVIEW_ROLES
POLICY_VERSION = "autonomous-content-v1.1.0"
MANIFEST_SCHEMA_VERSION = "2.1.0"
PRODUCER_VERSION = "1.0.0"
CONTENT_SCHEMA_VERSION = "1.0.0"
CATALOG_SCHEMA_VERSION = "1.0.0"
REQUIRED_GATE_CHECKS = frozenset({
    "lesson_and_source_schema",
    "deterministic_content_gates",
    "included_locale_consistency",
    "independent_hash_bound_reviews",
    "package_integrity",
})
PUBLIC_SOURCE_FIELDS = (
    "id", "title", "publisher", "url", "section", "published", "accessed",
    "authority", "jurisdiction",
)
_RELEASE_ID = re.compile(r"^rel-[0-9]{4}-[0-9]{2}-[0-9]{2}-[a-z0-9]+(?:-[a-z0-9]+)*$")
_SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_SOURCE_ID = re.compile(r"^src-[a-z0-9-]+$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class FinSenseReleaseError(RuntimeError):
    """Raised when the configured canonical release is missing or invalid."""


def _configured_root(root: Path | None) -> Path:
    if root is None:
        configured = os.getenv("FINSENSE_CONTENT_ROOT")
        if not configured:
            raise FinSenseReleaseError("canonical content root is not configured")
        root = Path(configured).expanduser()
    else:
        root = Path(root)
    if not root.is_absolute() or root.is_symlink():
        raise FinSenseReleaseError("canonical content root is invalid")
    try:
        resolved = root.resolve(strict=True)
    except OSError as exc:
        raise FinSenseReleaseError("canonical content root is unavailable") from exc
    if not resolved.is_dir():
        raise FinSenseReleaseError("canonical content root is unavailable")
    return resolved


def _safe_path(root: Path, relative: str, *, directory: bool = False) -> Path:
    if (
        not isinstance(relative, str)
        or not relative
        or relative.startswith("/")
        or "\\" in relative
    ):
        raise FinSenseReleaseError("release contains an unsafe path")
    parts = relative.split("/")
    if any(part in {"", ".", ".."} or ":" in part for part in parts):
        raise FinSenseReleaseError("release contains an unsafe path")

    candidate = root
    for part in parts:
        candidate = candidate / part
        if candidate.is_symlink():
            raise FinSenseReleaseError("release contains a symbolic link")
    try:
        resolved = candidate.resolve(strict=True)
    except OSError as exc:
        raise FinSenseReleaseError("required release file is unavailable") from exc
    if not resolved.is_relative_to(root.resolve()):
        raise FinSenseReleaseError("release path escapes its root")
    if directory and not resolved.is_dir():
        raise FinSenseReleaseError("release directory is unavailable")
    if not directory and not resolved.is_file():
        raise FinSenseReleaseError("release file is unavailable")
    return resolved


def _read_json(path: Path) -> tuple[Any, bytes]:
    try:
        raw = path.read_bytes()
        value = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise FinSenseReleaseError("release JSON is unreadable") from exc
    return value, raw


def _validator(root: Path, name: str) -> Draft7Validator:
    path = _safe_path(root, f"schemas/{name}.schema.json")
    value, _ = _read_json(path)
    if not isinstance(value, dict):
        raise FinSenseReleaseError("canonical content schema is invalid")
    try:
        Draft7Validator.check_schema(value)
    except Exception as exc:  # invalid canonical schemas block consumption
        raise FinSenseReleaseError("canonical content schema is invalid") from exc
    return Draft7Validator(value, format_checker=FormatChecker())


def _validate(validator: Draft7Validator, value: Any, label: str) -> None:
    errors = sorted(
        validator.iter_errors(value),
        key=lambda error: tuple(str(part) for part in error.path),
    )
    if errors:
        raise FinSenseReleaseError(f"{label} failed canonical schema validation")


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _identity(value: Any) -> str:
    return value.strip().casefold() if isinstance(value, str) else ""


def _valid_timestamp(value: Any) -> bool:
    try:
        timestamp = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return False
    return timestamp.tzinfo is not None and timestamp.utcoffset() is not None


def _read_package_entry(
    package: Path,
    item: dict[str, Any],
    expected_path: str,
    validator: Draft7Validator,
    label: str,
    *,
    schema_as_single_item_array: bool = False,
) -> dict[str, Any]:
    if item.get("path") != expected_path or not _SHA256.fullmatch(str(item.get("sha256", ""))):
        raise FinSenseReleaseError(f"{label} manifest entry is invalid")
    path = _safe_path(package, expected_path)
    raw = path.read_bytes()
    if _sha256(raw) != item["sha256"]:
        raise FinSenseReleaseError(f"{label} hash does not match its manifest")
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise FinSenseReleaseError(f"{label} JSON is invalid") from exc
    _validate(validator, [value] if schema_as_single_item_array else value, label)
    if not isinstance(value, dict):
        raise FinSenseReleaseError(f"{label} is not an object")
    return value


def load_catalog(locale: str = "tr", root: Path | None = None) -> dict[str, Any]:
    """Return one locale from the verified active release, without legacy fallback."""
    if locale not in LOCALES:
        raise FinSenseReleaseError("unsupported lesson locale")
    canonical_root = _configured_root(root)
    validators = {
        name: _validator(canonical_root, name)
        for name in ("release", "lesson", "review", "source")
    }

    active_path = _safe_path(canonical_root, "content/releases/active.json")
    active, active_raw = _read_json(active_path)
    if not isinstance(active, dict) or set(active) != {"release_id", "manifest_sha256", "activated_at"}:
        raise FinSenseReleaseError("active release pointer is invalid")
    release_id = active.get("release_id")
    manifest_sha256 = active.get("manifest_sha256")
    if not isinstance(release_id, str) or not _RELEASE_ID.fullmatch(release_id):
        raise FinSenseReleaseError("active release ID is invalid")
    if not isinstance(manifest_sha256, str) or not _SHA256.fullmatch(manifest_sha256):
        raise FinSenseReleaseError("active manifest hash is invalid")
    if not _valid_timestamp(active.get("activated_at")):
        raise FinSenseReleaseError("active release time is invalid")

    package = _safe_path(canonical_root, f"content/releases/{release_id}", directory=True)
    manifest_path = _safe_path(package, "manifest.json")
    manifest, manifest_raw = _read_json(manifest_path)
    if _sha256(manifest_raw) != manifest_sha256:
        raise FinSenseReleaseError("active manifest hash does not match")
    if not isinstance(manifest, dict) or manifest.get("manifest_schema_version") != MANIFEST_SCHEMA_VERSION:
        raise FinSenseReleaseError("unsupported release manifest version")
    _validate(validators["release"], manifest, "release manifest")
    manifest_keys = {
        "release_id", "manifest_schema_version", "producer_version", "created_at",
        "content_schema_version", "policy_version", "lessons", "review_evidence",
        "source_evidence", "package_inventory", "release_gate",
    }
    if set(manifest) != manifest_keys or manifest.get("release_id") != release_id:
        raise FinSenseReleaseError("release manifest identity is invalid")
    if manifest.get("producer_version") != PRODUCER_VERSION:
        raise FinSenseReleaseError("unsupported release producer version")
    if manifest.get("content_schema_version") != CONTENT_SCHEMA_VERSION:
        raise FinSenseReleaseError("unsupported lesson schema version")
    if manifest.get("policy_version") != POLICY_VERSION:
        raise FinSenseReleaseError("unsupported release policy version")

    gate = manifest.get("release_gate")
    if not isinstance(gate, dict) or (
        gate.get("decision") != "PASS"
        or gate.get("publisher") != "central-release-gate"
        or gate.get("policy_version") != POLICY_VERSION
    ):
        raise FinSenseReleaseError("release gate evidence is not passing")
    checks = gate.get("checks", [])
    check_statuses = {item.get("name"): item.get("status") for item in checks if isinstance(item, dict)}
    if (
        not isinstance(checks, list)
        or len(checks) != len(REQUIRED_GATE_CHECKS)
        or len(check_statuses) != len(checks)
        or check_statuses != {name: "PASS" for name in REQUIRED_GATE_CHECKS}
    ):
        raise FinSenseReleaseError("release gate checks are incomplete")

    lessons: dict[tuple[str, str], tuple[dict[str, Any], dict[str, Any]]] = {}
    claims_by_lesson: dict[tuple[str, str], dict[str, set[str]]] = {}
    referenced_source_ids: set[str] = set()
    expected_files = {"manifest.json"}
    for item in manifest["lessons"]:
        concept_id, lesson_locale = item.get("concept_id"), item.get("locale")
        if not isinstance(concept_id, str) or not _SLUG.fullmatch(concept_id) or lesson_locale not in LOCALES:
            raise FinSenseReleaseError("release lesson identity is invalid")
        key = (concept_id, lesson_locale)
        if key in lessons:
            raise FinSenseReleaseError("release contains a duplicate lesson")
        relative = f"content/lessons/{concept_id}/{lesson_locale}.json"
        lesson = _read_package_entry(package, item, relative, validators["lesson"], "lesson")
        if (
            lesson.get("concept_id") != concept_id
            or lesson.get("locale") != lesson_locale
            or lesson.get("version") != item.get("version")
            or lesson.get("status") != "published"
        ):
            raise FinSenseReleaseError("release lesson identity or status is invalid")
        claim_sources = {}
        for claim in lesson["claims"]:
            if claim["id"] in claim_sources:
                raise FinSenseReleaseError("release lesson contains duplicate claim IDs")
            source_ids = set(claim["source_ids"])
            claim_sources[claim["id"]] = source_ids
            referenced_source_ids.update(source_ids)
        claim_ids = set(claim_sources)
        for quiz in lesson["quiz"]:
            if (
                quiz["correct_index"] >= len(quiz["options"])
                or not set(quiz["claim_ids"]).issubset(claim_ids)
            ):
                raise FinSenseReleaseError("release lesson assessment references are invalid")
        claims_by_lesson[key] = claim_sources
        lessons[key] = (lesson, item)
        expected_files.add(relative)

    if not lessons or gate.get("lesson_count") != len(lessons):
        raise FinSenseReleaseError("release lesson count is invalid")
    locales_by_concept: dict[str, set[str]] = {}
    for concept_id, lesson_locale in lessons:
        locales_by_concept.setdefault(concept_id, set()).add(lesson_locale)
    if any(locales != set(LOCALES) for locales in locales_by_concept.values()):
        raise FinSenseReleaseError("release is missing a required locale")

    sources: dict[str, dict[str, Any]] = {}
    for item in manifest["source_evidence"]:
        source_id = item.get("source_id")
        if not isinstance(source_id, str) or not _SOURCE_ID.fullmatch(source_id) or source_id in sources:
            raise FinSenseReleaseError("release source identity is invalid")
        relative = f"sources/{source_id}.json"
        source = _read_package_entry(
            package,
            item,
            relative,
            validators["source"],
            "source evidence",
            schema_as_single_item_array=True,
        )
        if source.get("id") != source_id:
            raise FinSenseReleaseError("release source identity does not match its manifest")
        sources[source_id] = source
        expected_files.add(relative)
    if set(sources) != referenced_source_ids:
        raise FinSenseReleaseError("release source set does not match lesson citations")

    reviews: dict[tuple[str, str, str], tuple[dict[str, Any], dict[str, Any]]] = {}
    reviewers_by_lesson: dict[tuple[str, str], tuple[set[str], set[str], set[str], set[str]]] = {}
    for item in manifest["review_evidence"]:
        concept_id, review_locale, role = item.get("concept_id"), item.get("locale"), item.get("role")
        if role not in REVIEW_ROLES:
            raise FinSenseReleaseError("release review role is unsupported")
        key = (concept_id, review_locale, role)
        if key in reviews or (concept_id, review_locale) not in lessons:
            raise FinSenseReleaseError("release review identity is duplicate or orphaned")
        relative = f"review_evidence/{concept_id}/{review_locale}.{role}.json"
        review = _read_package_entry(package, item, relative, validators["review"], "review evidence")
        if (
            review.get("concept_id") != concept_id
            or review.get("locale") != review_locale
            or review.get("role") != role
            or review.get("reviewer_type") != "agent"
            or review.get("verdict") != "approved"
            or review.get("policy_version") != POLICY_VERSION
            or review.get("content_hash") != lessons[(concept_id, review_locale)][1].get("content_hash")
            or review.get("content_version") != lessons[(concept_id, review_locale)][0].get("version")
            or review.get("error") is not None
            or "human_signoff" in review
            or "approved_by" in review
        ):
            raise FinSenseReleaseError("release review evidence is not approved or hash-bound")
        for field in (
            "reviewer_id", "model_provider", "model_family", "model_id", "model_digest",
            "policy_version", "prompt_version", "prompt_sha256", "run_id", "reviewed_at",
            "evidence_refs",
        ):
            if review.get(field) != item.get(field):
                raise FinSenseReleaseError("release review evidence does not match its manifest")
        if not _valid_timestamp(review.get("reviewed_at")):
            raise FinSenseReleaseError("release review timestamp is invalid")
        lesson = lessons[(concept_id, review_locale)][0]
        if _identity(review.get("reviewer_id")) == _identity(lesson.get("author", {}).get("id")):
            raise FinSenseReleaseError("release lesson author cannot review their own content")

        refs = review.get("evidence_refs", [])
        if not refs:
            raise FinSenseReleaseError("release review has no evidence references")
        for ref in refs:
            claim_id, source_id = ref.get("claim_id"), ref.get("source_id")
            if (
                claim_id not in claims_by_lesson[(concept_id, review_locale)]
                or source_id not in sources
                or source_id not in claims_by_lesson[(concept_id, review_locale)][claim_id]
            ):
                raise FinSenseReleaseError("release review references unknown evidence")
        if role in {"accuracy", "source", "critical"} and not set(
            claims_by_lesson[(concept_id, review_locale)]
        ).issubset({ref["claim_id"] for ref in refs}):
            raise FinSenseReleaseError("release review does not cover every claim")
        for finding in review.get("findings", []):
            if finding.get("severity") in {"critical", "high"} and finding.get("status") == "open":
                raise FinSenseReleaseError("release contains an unresolved critical finding")

        identity_sets = reviewers_by_lesson.setdefault(
            (concept_id, review_locale), (set(), set(), set(), set())
        )
        for seen, field in zip(
            identity_sets, ("reviewer_id", "model_family", "model_id", "model_digest")
        ):
            identity = _identity(review.get(field))
            if not identity or identity in seen:
                raise FinSenseReleaseError("release reviewers are not independent")
            seen.add(identity)
        reviews[key] = (review, item)
        expected_files.add(relative)

    expected_reviews = set()
    for (concept_id, lesson_locale), (lesson, _) in lessons.items():
        required_roles = REQUIRED_REVIEW_ROLES
        if lesson.get("jurisdiction") != ["GLOBAL"]:
            required_roles += CONDITIONAL_REVIEW_ROLES
        expected_reviews.update(
            (concept_id, lesson_locale, role)
            for role in required_roles
        )
    if set(reviews) != expected_reviews or gate.get("review_count") != len(reviews):
        raise FinSenseReleaseError("release review coverage is incomplete")

    inventory_items = manifest.get("package_inventory")
    if not isinstance(inventory_items, list) or not inventory_items:
        raise FinSenseReleaseError("release package inventory is invalid")
    inventory: dict[str, dict[str, Any]] = {}
    for item in inventory_items:
        relative = item.get("path") if isinstance(item, dict) else None
        if (
            not isinstance(relative, str)
            or relative in inventory
            or relative not in expected_files - {"manifest.json"}
        ):
            raise FinSenseReleaseError("release package inventory is incomplete or invalid")
        raw = _safe_path(package, relative).read_bytes()
        if (
            item.get("sha256") != _sha256(raw)
            or type(item.get("size_bytes")) is not int
            or item["size_bytes"] != len(raw)
        ):
            raise FinSenseReleaseError("release package inventory hash or size does not match")
        inventory[relative] = item
    if set(inventory) != expected_files - {"manifest.json"}:
        raise FinSenseReleaseError("release package inventory is incomplete or invalid")

    actual_files = set()
    for path in package.rglob("*"):
        if path.is_symlink():
            raise FinSenseReleaseError("release package contains a symbolic link")
        if path.is_file():
            actual_files.add(path.relative_to(package).as_posix())
    if actual_files != expected_files:
        raise FinSenseReleaseError("release package contains missing or unexpected files")
    if _sha256(_safe_path(canonical_root, "content/releases/active.json").read_bytes()) != _sha256(active_raw):
        raise FinSenseReleaseError("active release pointer changed during read")
    if _sha256(_safe_path(package, "manifest.json").read_bytes()) != manifest_sha256:
        raise FinSenseReleaseError("active release manifest changed during read")

    selected_lessons = []
    for (concept_id, lesson_locale), (lesson, item) in sorted(lessons.items()):
        if lesson_locale != locale:
            continue
        source_ids = sorted({source_id for claim in lesson["claims"] for source_id in claim["source_ids"]})
        selected_lessons.append({
            "lesson": lesson,
            "manifest_entry": item,
            "sources": [
                {field: sources[source_id][field] for field in PUBLIC_SOURCE_FIELDS if field in sources[source_id]}
                for source_id in source_ids
            ],
        })
    return {
        "catalog_schema_version": CATALOG_SCHEMA_VERSION,
        "locale": locale,
        "manifest_sha256": manifest_sha256,
        "manifest": manifest,
        "lessons": selected_lessons,
    }