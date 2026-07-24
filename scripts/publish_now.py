"""Publish one fresh, full-universe distribution edition manually."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

try:
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
except ImportError:
    pass

# Manual publication is the only active distribution path. This process-local
# override lets job_draft/job_publish run while scheduler distribution stays off.
os.environ["FINPILOT_ENABLE_DISTRIBUTION"] = "1"

from distribution import broadcast
from distribution.jobs import job_draft, job_publish


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--yes",
        action="store_true",
        help="approve the draft without an interactive prompt",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="publish even if the pre-publish gate reports problems (use consciously)",
    )
    args = parser.parse_args()

    # Pre-publish gate: the export must prove it is publishable (integrity +
    # enrichment quality). A degraded scan must never silently publish an
    # empty brief — 2026-07-24 diagnosis, silent-failure class #2.
    from distribution.prepublish_gate import check_export_health
    from distribution.snapshot_builder import SCAN_EXPORT_LATEST, read_json_object

    try:
        export = read_json_object(SCAN_EXPORT_LATEST)
    except (OSError, ValueError) as exc:
        print(f"PRE-PUBLISH GATE: export okunamadı: {exc}", file=sys.stderr)
        return 1
    problems = check_export_health(export)
    if problems:
        for problem in problems:
            print(f"PRE-PUBLISH GATE: {problem}", file=sys.stderr)
        if not args.force:
            print("Yayın DURDURULDU. Sorunları çöz ya da bilinçli --force kullan.", file=sys.stderr)
            return 1
        print("WARNING: gate sorunlarına rağmen --force ile devam ediliyor.", file=sys.stderr)

    draft = job_draft()
    print("draft:", json.dumps(draft, ensure_ascii=False, default=str))
    queue_id = draft.get("free_queue_id")
    if not queue_id:
        print("Draft was not created. Run a fresh full-universe scan first.", file=sys.stderr)
        return 1

    if not args.yes:
        try:
            input(f"Approve queue #{queue_id}? Press Enter to continue, Ctrl+C to cancel: ")
        except KeyboardInterrupt:
            print("Publication cancelled.")
            return 1

    if not broadcast.decide(queue_id, approve=True, decided_by="manual"):
        print(f"Queue #{queue_id} could not be approved.", file=sys.stderr)
        return 1

    published = job_publish()
    print("publish:", json.dumps(published, ensure_ascii=False, default=str))
    if published.get("blocked") or published.get("failed") or not published.get("web_pushed"):
        print("Publication did not complete successfully.", file=sys.stderr)
        return 1
    print("Publication completed: Telegram delivery and web snapshot are up to date.")
    try:
        from distribution.archive_bridge import (
            archive_snapshot_candidates,
            check_archive_continuity,
        )
        from distribution.snapshot_builder import EXPORT_DIR, read_json_object

        snap = read_json_object(EXPORT_DIR / "snapshot_latest.json")
        print("archive:", archive_snapshot_candidates(snap))
        # Immutable evidence copy: the exact export this publish used.
        # (2026-07-24: a later degraded scan overwrote the published export —
        # the selectivity funnel became unmeasurable. Never again.)
        published_copy = EXPORT_DIR / f"scan_export_{snap.get('date')}_published.json"
        if not published_copy.exists():
            import shutil

            shutil.copyfile(SCAN_EXPORT_LATEST, published_copy)
            print(f"published copy: {published_copy.name}")
        warning = check_archive_continuity()
        if warning:
            print(f"ARCHIVE WARNING: {warning}", file=sys.stderr)
            try:
                from distribution.telegram_client import notify_admin

                notify_admin(f"⚠️ {warning}")
            except Exception:
                pass
    except Exception as exc:  # loud but non-fatal — publish itself already succeeded
        print(f"WARNING: archive bridge failed: {exc}", file=sys.stderr)
    try:
        from scripts.daily_backup import run_backup

        run_backup()
    except Exception as exc:  # backup failure must be visible but not undo a publish
        print(f"WARNING: daily backup failed: {exc}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
