"""Kalıcı Telegram bot süpervizörü (çökme→yeniden başlat). Bot kökte:
telegram_bot_runner.py (telegram_config'i kökten import eder). Bu süpervizör
cwd=REPO KÖKÜ ile çalıştırır → import çözülür. logs/bot.log'a yazar.
Kullanım: python scripts/run_bot.py   (Ctrl+C ile dur)
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOT = ROOT / "telegram_bot_runner.py"  # kökte
LOG = ROOT / "logs" / "bot.log"
BACKOFF, MAXB = 3, 60


def _log(m: str) -> None:
    line = f"{datetime.now().isoformat(timespec='seconds')} [supervisor] {m}"
    print(line, flush=True)
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        LOG.open("a", encoding="utf-8").write(line + "\n")
    except Exception:
        pass


def main() -> int:
    if not BOT.exists():
        _log(f"HATA: bot bulunamadı: {BOT}")
        return 1
    _log(f"süpervizör başladı → {BOT.name} (cwd={ROOT})")
    backoff = BACKOFF
    while True:
        t0 = time.time()
        try:
            env = dict(os.environ)
            env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
            code = subprocess.run([sys.executable, str(BOT)], cwd=str(ROOT), env=env).returncode
        except KeyboardInterrupt:
            _log("Ctrl+C — kapanıyor")
            return 0
        except Exception as exc:
            _log(f"başlatma hatası: {exc}")
            code = 1
        ran = time.time() - t0
        _log(f"bot çıktı (code={code}, {ran:.0f}s) — yeniden başlatılıyor")
        backoff = BACKOFF if ran > 120 else min(backoff * 2, MAXB)
        try:
            time.sleep(backoff)
        except KeyboardInterrupt:
            _log("Ctrl+C — kapanıyor")
            return 0


if __name__ == "__main__":
    raise SystemExit(main())
