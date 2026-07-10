"""M7 canlı test yardımcısı — SENİN makinede çalıştır.

Kullanım (repo kökünde):
    python scripts/dist_live_test.py draft     # taslak üret + telefonuna DM
    python scripts/dist_live_test.py status    # kuyruk durumu
    python scripts/dist_live_test.py publish   # ONAYLI taslakları kanala yayınla
    python scripts/dist_live_test.py sentinel  # 07:40 bekçisini elle test et
    python scripts/dist_live_test.py backup    # yedek job'ını elle test et

Onay adımı için ayrı pencerede bot çalışmalı:
    python telegram_bot_runner.py
    (bota DM'den: ONAYLA <id>)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# .env'i yükle (python-dotenv projede zaten var)
try:
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
except ImportError:
    print("UYARI: python-dotenv yok — env değişkenleri sistemden okunacak.")


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"

    if cmd == "draft":
        from distribution.jobs import job_draft

        print(json.dumps(job_draft(), ensure_ascii=False, indent=1, default=str))
        print("→ Telefonunu kontrol et: bot DM'inde taslak + ONAYLA <id> talimatı olmalı.")
    elif cmd == "publish":
        from distribution.jobs import job_publish

        print(json.dumps(job_publish(), ensure_ascii=False, indent=1, default=str))
        print(
            "→ Kanalı kontrol et: onaylı taslak yayınlanmış olmalı; web/public snapshot güncellendi."
        )
    elif cmd == "status":
        from distribution import broadcast

        print("Bekleyen:", json.dumps(broadcast.get_pending(), ensure_ascii=False, default=str))
        print(
            "Onaylı-gönderilmemiş:",
            json.dumps(broadcast.get_approved_unsent(), ensure_ascii=False, default=str),
        )
        last = broadcast.get_last_sent("daily")
        print("Son yayın:", (last or {}).get("brief_date"))
    elif cmd == "drop":
        from distribution import broadcast

        qid = int(sys.argv[2])
        print("düşürüldü" if broadcast.drop(qid) else "bulunamadı/zaten gönderilmiş", f"(#{qid})")
    elif cmd == "sentinel":
        from distribution.jobs import job_scan_sentinel

        print(json.dumps(job_scan_sentinel(), ensure_ascii=False, default=str))
    elif cmd == "backup":
        from distribution.maintenance import job_backup, verify_backup

        print(json.dumps(job_backup(), ensure_ascii=False, indent=1, default=str))
        print(
            "restore provası:", json.dumps(verify_backup(), ensure_ascii=False, default=str)[:400]
        )
    else:
        print(__doc__)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
