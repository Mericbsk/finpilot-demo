"""Publish one human-approved web snapshot to Vercel.

The release manifest binds approval to the export, snapshot, artifact hash and
destination. This command is web-only; Telegram publication uses its own queue.
"""

from __future__ import annotations

import argparse
import hashlib
import http.client
import json
import re
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
WEB_ARTIFACT = "web/public/demo_snapshot.json"
REQUIRED_MANIFEST_FIELDS = {
    "schema_version",
    "approval_id",
    "approved_by",
    "approved_at",
    "destination",
    "source_commit",
    "date",
    "run_id",
    "scan_id",
    "snapshot_id",
    "artifact_path",
    "artifact_sha256",
    "public_copy_reviewed",
}
MAX_APPROVAL_AGE = timedelta(minutes=30)
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
ALLOWED_DESTINATION_HOSTS = {"www.finpilot.at"}

# Windows consoles often default stdout to cp1252, which cannot encode the
# "\u2192" used below. That crashed this script with UnicodeEncodeError AFTER
# the git push had already succeeded (2026-08-03 finding) — the caller then saw
# a non-zero exit code for what was actually a successful publish, which is
# indistinguishable from a real failure once callers start checking the exit
# code. Force UTF-8 stdout so the success message never crashes the process.
if hasattr(sys.stdout, "reconfigure"):
    _reconfigure_stdout = getattr(sys.stdout, "reconfigure", None)
    if callable(_reconfigure_stdout):
        _reconfigure_stdout(encoding="utf-8")


def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True)


def _git_bytes(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(ROOT), *args], capture_output=True, text=False
    )


def _now_vienna() -> datetime:
    import pytz

    return datetime.now(pytz.timezone("Europe/Vienna"))


def _validate_release(manifest_path: Path) -> dict:
    from distribution.prepublish_gate import check_export_health
    from distribution.schema import demo_view, validate_snapshot
    from distribution.snapshot_builder import (
        EXPORT_DIR,
        load_scan_export_record,
        validate_scan_export,
    )

    manifest_path = manifest_path.resolve()
    try:
        manifest_path.relative_to(ROOT.resolve())
    except ValueError:
        pass
    else:
        raise ValueError("approval manifest must be stored outside the Git worktree")

    manifest = _read_json_object(manifest_path)
    missing = sorted(REQUIRED_MANIFEST_FIELDS - manifest.keys())
    if missing:
        raise ValueError(f"approval manifest missing fields: {', '.join(missing)}")
    if manifest["schema_version"] != 1:
        raise ValueError("unsupported approval manifest schema")
    for field in (
        "approval_id",
        "approved_by",
        "date",
        "run_id",
        "scan_id",
        "snapshot_id",
        "destination",
        "source_commit",
    ):
        if not isinstance(manifest[field], str) or not manifest[field].strip():
            raise ValueError(f"approval manifest has empty {field}")
    if manifest["artifact_path"] != WEB_ARTIFACT:
        raise ValueError("manifest artifact_path must be the web demo snapshot")
    if manifest["public_copy_reviewed"] is not True:
        raise ValueError("manifest must attest that public copy was reviewed")
    destination = urlparse(manifest["destination"])
    if (
        destination.scheme != "https"
        or destination.hostname not in ALLOWED_DESTINATION_HOSTS
        or destination.username
        or destination.password
        or destination.port not in (None, 443)
        or destination.path not in ("", "/")
        or destination.query
        or destination.fragment
    ):
        raise ValueError("destination must be the approved FinPilot HTTPS origin")
    if not _SHA256_RE.fullmatch(str(manifest["artifact_sha256"])):
        raise ValueError("artifact_sha256 must be a lowercase SHA-256")

    try:
        approved_at = datetime.fromisoformat(str(manifest["approved_at"]).replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("approved_at must be an ISO-8601 timestamp with timezone") from exc
    if approved_at.tzinfo is None:
        raise ValueError("approved_at must include a timezone")
    age = _now_vienna().astimezone(UTC) - approved_at.astimezone(UTC)
    if age < timedelta(0) or age > MAX_APPROVAL_AGE:
        raise ValueError("approval is expired or from the future")

    head = _git("rev-parse", "HEAD")
    if head.returncode or head.stdout.strip() != manifest["source_commit"]:
        raise ValueError("source_commit does not match current HEAD")

    today = _now_vienna().date().isoformat()
    export = load_scan_export_record()
    if export.get("scan_complete") is not True:
        raise ValueError("scan export is not explicitly complete")
    problems = validate_scan_export(export) + check_export_health(export, today=today)
    if problems:
        raise ValueError("scan export gates failed: " + "; ".join(dict.fromkeys(problems)))
    rows = export.get("results")
    if not isinstance(rows, list) or export.get("result_count") != len(rows):
        raise ValueError("scan export result_count does not match results")
    if export.get("date") != today:
        raise ValueError("scan export is not dated today in Europe/Vienna")

    snapshot = _read_json_object(EXPORT_DIR / "snapshot_en_latest.json")
    snapshot_problems = validate_snapshot(snapshot)
    if snapshot_problems:
        raise ValueError("English snapshot is invalid: " + "; ".join(snapshot_problems))
    for field in ("date", "scan_id", "universe"):
        if snapshot.get(field) != export.get(field):
            raise ValueError(f"snapshot/export mismatch for {field}")
    if snapshot["date"] != today:
        raise ValueError("snapshot is not dated today in Europe/Vienna")
    if not snapshot.get("candidates"):
        raise ValueError("snapshot has no public candidate")

    artifact_path = ROOT / WEB_ARTIFACT
    artifact_bytes = artifact_path.read_bytes()
    artifact = _read_json_object(artifact_path)
    expected = demo_view(snapshot, max_candidates=len(snapshot.get("candidates", [])))
    if artifact != expected:
        raise ValueError("web artifact is not the generated projection of snapshot_en_latest")
    artifact_sha256 = hashlib.sha256(artifact_bytes).hexdigest()

    expected_values = {
        "date": export["date"],
        "run_id": export.get("run_id"),
        "scan_id": export.get("scan_id"),
        "snapshot_id": snapshot.get("snapshot_id"),
        "artifact_sha256": artifact_sha256,
    }
    for field, actual in expected_values.items():
        if manifest.get(field) != actual:
            raise ValueError(f"approval manifest mismatch for {field}")
    return manifest


def _read_json_object(path: Path) -> dict:
    raw = path.read_bytes()
    if b"\x00" in raw:
        raise ValueError(f"JSON contains NUL bytes: {path}")
    value = json.loads(raw.decode("utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON must be an object: {path}")
    return value


def _canonical_json_sha256(raw: bytes) -> str:
    value = json.loads(raw.decode("utf-8"))
    canonical = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _check_git_preflight() -> bool:
    """Require clean main/index; allow only the generated web artifact dirty."""
    branch = _git("branch", "--show-current")
    if branch.returncode or branch.stdout.strip() != "main":
        raise ValueError("publication is allowed only from main")
    head = _git("rev-parse", "HEAD")
    remote_head = _git("rev-parse", "origin/main")
    if (
        head.returncode
        or remote_head.returncode
        or head.stdout.strip() != remote_head.stdout.strip()
    ):
        raise ValueError("local main must exactly match origin/main before publication")
    status = _git("status", "--porcelain=v1", "--untracked-files=all")
    if status.returncode:
        raise ValueError("could not inspect Git working tree")
    lines = status.stdout.splitlines()
    if not lines:
        return False
    if lines != [f" M {WEB_ARTIFACT}"]:
        raise ValueError("working tree must contain only an unstaged demo_snapshot.json change")
    cached = _git("diff", "--cached", "--quiet")
    if cached.returncode != 0:
        raise ValueError("Git index must be clean before publication")
    return True


def _publish(manifest: dict) -> int:
    artifact_bytes = (ROOT / WEB_ARTIFACT).read_bytes()
    if hashlib.sha256(artifact_bytes).hexdigest() != manifest["artifact_sha256"]:
        print("publish_web: working artifact hash differs from approved manifest", file=sys.stderr)
        return 1
    expected_json_hash = _canonical_json_sha256(artifact_bytes)
    staged = _git("add", "--", WEB_ARTIFACT)
    if staged.returncode:
        print(f"publish_web: git add failed: {staged.stderr.strip()}", file=sys.stderr)
        return 1

    names = _git("diff", "--cached", "--name-only")
    if names.returncode or names.stdout.splitlines() != [WEB_ARTIFACT]:
        print("publish_web: refusing commit; staged paths are not exactly the web snapshot", file=sys.stderr)
        return 1
    diff_check = _git("diff", "--cached", "--check")
    if diff_check.returncode:
        print(f"publish_web: staged diff check failed: {diff_check.stderr.strip()}", file=sys.stderr)
        return 1
    staged_blob = _git_bytes("show", f":{WEB_ARTIFACT}")
    if (
        staged_blob.returncode
        or _canonical_json_sha256(staged_blob.stdout) != expected_json_hash
    ):
        print("publish_web: staged artifact hash differs from approved manifest", file=sys.stderr)
        return 1
    branch = _git("branch", "--show-current")
    if branch.returncode or branch.stdout.strip() != "main":
        print("publish_web: branch changed before commit; refusing publication", file=sys.stderr)
        return 1

    message = f"chore(web): daily snapshot {manifest['date']}"
    body = (
        f"Approval-ID: {manifest['approval_id']}\n"
        f"Snapshot-ID: {manifest['snapshot_id']}\n"
        f"Destination: {manifest['destination']}"
    )
    commit = _git("commit", "-m", message, "-m", body)
    if commit.returncode != 0:
        print(
            f"publish_web: commit failed (exit {commit.returncode}):\n"
            f"{commit.stdout.strip()}\n{commit.stderr.strip()}",
            file=sys.stderr,
        )
        return 1
    committed_names = _git("show", "--pretty=format:", "--name-only", "HEAD")
    committed_blob = _git_bytes("show", f"HEAD:{WEB_ARTIFACT}")
    if (
        committed_names.returncode
        or committed_names.stdout.splitlines() != [WEB_ARTIFACT]
        or committed_blob.returncode
        or _canonical_json_sha256(committed_blob.stdout) != expected_json_hash
    ):
        print("publish_web: commit contents differ from approved artifact; refusing push", file=sys.stderr)
        return 1
    branch = _git("branch", "--show-current")
    status = _git("status", "--porcelain=v1", "--untracked-files=all")
    if branch.returncode or branch.stdout.strip() != "main" or status.returncode or status.stdout.strip():
        print("publish_web: branch or worktree changed after commit; refusing push", file=sys.stderr)
        return 1
    pushed = _git("push", "origin", "main")
    if pushed.returncode != 0:
        print(
            f"publish_web: PUSH FAILED (exit {pushed.returncode}):\n"
            f"{pushed.stdout.strip()}\n{pushed.stderr.strip()}",
            file=sys.stderr,
        )
        return 1

    print(
        f"publish_web: pushed {manifest['snapshot_id']} to "
        f"{manifest['destination']}; Vercel deploy triggered"
    )
    return _smoke_test(manifest)


def _smoke_test(manifest: dict) -> int:
    url = manifest["destination"].rstrip("/") + "/demo_snapshot.json"
    try:
        if not url.startswith("https://"):
            raise ValueError("deploy smoke-test URL must use HTTPS")
        connection = http.client.HTTPSConnection("www.finpilot.at", timeout=15)
        connection.request("GET", "/demo_snapshot.json")
        response = connection.getresponse()
        try:
            if response.status != 200:
                raise ValueError(f"HTTP {response.status}")
            live = json.loads(response.read().decode("utf-8"))
        finally:
            connection.close()
        if (
            live.get("date") != manifest["date"]
            or live.get("universe") != 1812
            or not live.get("candidates")
            or live.get("snapshot_id") != manifest["snapshot_id"]
        ):
            raise ValueError("live snapshot metadata does not match approved release")
    except Exception as exc:
        print(f"publish_web: deploy smoke test failed after push: {exc}", file=sys.stderr)
        return 2
    print("publish_web: deploy smoke test passed")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args(argv)

    try:
        manifest = _validate_release(args.manifest)
        changed = _check_git_preflight()
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"publish_web: preflight failed: {exc}", file=sys.stderr)
        return 1
    if not changed:
        print("publish_web: no web snapshot changes; nothing to publish")
        return 0

    print(
        "Release preflight passed: "
        f"date={manifest['date']} run_id={manifest['run_id']} scan_id={manifest['scan_id']} "
        f"snapshot_id={manifest['snapshot_id']} destination={manifest['destination']}"
    )
    expected = f"PUBLISH {manifest['snapshot_id']} TO {manifest['destination']}"
    try:
        confirmation = input(f"Type exactly '{expected}' to commit and push: ")
    except (EOFError, KeyboardInterrupt):
        print("publish_web: interactive approval unavailable; publication cancelled", file=sys.stderr)
        return 1
    if confirmation != expected:
        print("publish_web: confirmation did not match; publication cancelled", file=sys.stderr)
        return 1

    try:
        # Recheck approval freshness, source identity, artifact hash and Git state
        # after confirmation and immediately before staging.
        manifest = _validate_release(args.manifest)
        if not _check_git_preflight():
            raise ValueError("web artifact changed or no longer needs publication")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"publish_web: final preflight failed: {exc}", file=sys.stderr)
        return 1
    return _publish(manifest)


if __name__ == "__main__":
    raise SystemExit(main())
