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
    args = parser.parse_args()

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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
