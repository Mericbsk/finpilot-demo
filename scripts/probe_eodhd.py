"""EODHD plan capability probe — data-source authority decision support (2026-07-31).

Answers the ONE open question in the Data-Source Authority Map: what does OUR
EODHD key actually grant? Tests each endpoint we might consolidate onto and
reports OK / FAIL(status) — WITHOUT ever printing the API key.

Endpoints probed:
  * eod (daily OHLCV, one symbol)      — base-plan expectation
  * eod-bulk-last-day (ALL US in 1 call) — the "one call for the universe" claim
  * intraday 1h (one symbol)           — needed for the scanner's 1h timeframe
  * intraday 5m (one symbol)           — possible 15m substitute (EODHD has NO 15m)

Run:  python scripts/probe_eodhd.py           # uses EODHD_API_KEY from env/.env
      python scripts/probe_eodhd.py AAPL      # probe a specific symbol

Read-only GETs. Note: intraday endpoints cost ~5 API credits each.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

BASE = "https://eodhd.com/api"


def _load_key() -> str:
    key = os.getenv("EODHD_API_KEY", "").strip()
    if not key:  # fall back to reading .env without importing anything heavy
        env = _ROOT / ".env"
        if env.exists():
            for line in env.read_text(encoding="utf-8").splitlines():
                if line.startswith("EODHD_API_KEY="):
                    key = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break
    return key


def _get(key: str, path: str, params: dict) -> tuple[bool, str, object]:
    """Return (ok, status_text, parsed_or_len). Never prints the key."""
    try:
        import requests
    except ImportError:
        return False, "requests-yok", None
    p = {"api_token": key, "fmt": "json", **params}
    try:
        r = requests.get(f"{BASE}/{path}", params=p, timeout=20)
    except Exception as exc:  # noqa: BLE001
        return False, f"istek-hatası:{type(exc).__name__}", None
    if r.status_code != 200:
        # Show status only — 401/402/403 typically = plan doesn't include it.
        return False, f"HTTP {r.status_code}", None
    try:
        data = r.json()
    except Exception:
        return False, "json-değil", None
    n = len(data) if isinstance(data, (list, dict)) else 1
    return True, "OK", n


def main(argv: list[str]) -> int:
    sym = (argv[1] if len(argv) > 1 else "AAPL").upper()
    key = _load_key()
    if not key:
        print("HATA: EODHD_API_KEY bulunamadı (env veya .env).")
        return 2
    print(f"EODHD plan probu — sembol={sym}  (anahtar GİZLİ, basılmıyor)\n")

    probes = [
        ("eod (günlük OHLCV)", f"eod/{sym}.US", {"period": "d"}),
        ("eod-bulk-last-day (TÜM US tek çağrı)", "eod-bulk-last-day/US", {}),
        ("intraday 1h", f"intraday/{sym}.US", {"interval": "1h"}),
        ("intraday 5m", f"intraday/{sym}.US", {"interval": "5m"}),
    ]
    results = {}
    for label, path, params in probes:
        ok, status, n = _get(key, path, params)
        results[label] = ok
        detail = f"{n} kayıt" if ok else status
        print(f"  {'✓' if ok else '✗'} {label:38s} → {detail}")

    print("\nÖzet:")
    print(f"  Günlük (eod)        : {'VAR' if results.get('eod (günlük OHLCV)') else 'YOK'}")
    print(
        f"  Bulk-EOD (tüm US)   : {'VAR' if results.get('eod-bulk-last-day (TÜM US tek çağrı)') else 'YOK'}"
    )
    intraday = results.get("intraday 1h") or results.get("intraday 5m")
    print(
        f"  Intraday (1h/5m)    : {'VAR — plan intraday içeriyor' if intraday else 'YOK — plan intraday içermiyor'}"
    )
    print("\nNot: EODHD 15m sunmuyor (yalnız 1m/5m/1h). 15m kararı ayrı (bkz. otorite haritası).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
