"""Web yayın kancası — snapshot'ı git ile commit+push eder → Vercel otomatik deploy.

Neden: Vercel, github.com/Mericbsk/finpilot-demo (monorepo) push'unda build eder.
demo_snapshot.json + academy_lessons.json git'te İZLENEN dosyalar; bu script SADECE
o iki dosyayı stage'ler, commit'ler ve push'lar (başka değişiklik karışmaz).

Kullanım (tek komut — FINPILOT_WEB_PUBLISH_CMD'ye konur):
    python scripts/publish_web.py
Ortam: FINPILOT_REQUIRE_VERCEL_DEPLOY=0 ayarla (push zaten deploy'u tetikler,
ayrı deploy-hook gerekmez).
"""

from __future__ import annotations

import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = ["web/public/demo_snapshot.json", "web/public/academy_lessons.json"]

# Windows consoles often default stdout to cp1252, which cannot encode the
# "\u2192" used below. That crashed this script with UnicodeEncodeError AFTER
# the git push had already succeeded (2026-08-03 finding) — the caller then saw
# a non-zero exit code for what was actually a successful publish, which is
# indistinguishable from a real failure once callers start checking the exit
# code. Force UTF-8 stdout so the success message never crashes the process.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True)


def main() -> int:
    existing = [f for f in FILES if (ROOT / f).exists()]
    if not existing:
        print("publish_web: yayınlanacak dosya yok", file=sys.stderr)
        return 0
    _git("add", *existing)
    # sadece bu dosyalarda değişiklik var mı?
    staged = _git("diff", "--cached", "--name-only", "--", *existing)
    if not staged.stdout.strip():
        print("publish_web: değişiklik yok — commit atlanıyor")
        return 0
    msg = f"chore(web): daily snapshot {date.today().isoformat()}"
    c = _git("commit", "-m", msg, "--", *existing)
    if c.returncode != 0:
        print(f"publish_web: commit hatası: {c.stderr.strip()[:160]}", file=sys.stderr)
        return 1
    pushr = _git("push")
    if pushr.returncode != 0:
        print(
            f"publish_web: PUSH HATASI (kimlik/ağ?): {pushr.stderr.strip()[:200]}", file=sys.stderr
        )
        return 1
    print(f"publish_web: pushed → Vercel deploy tetiklendi ({msg})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
