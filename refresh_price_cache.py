#!/usr/bin/env python3
"""
refresh_price_cache.py — FAZ 0: price_cache'i EODHD ile bugüne güncelle.

Neden ayrı script: sandbox'ta ağ yok; bu LOCAL çalışır (EODHD_API_KEY .env'de olmalı).
Gölge defterindeki (data/shadow/scan_shadow.jsonl) uygun sinyaller + benchmark ETF'leri
(+ opsiyonel reddedilen kontrol grubu) için EODHD /eod barlarını çeker ve
data/price_cache/<SYM>.json dosyalarına ARTIMLI (incremental) birleştirir.

Kabul kriteri (Faz 0): eligible + benchmark sembollerinin ≥%90'ı, sinyal günü +
5 işlem günü ileri bar taşımalı. Script sonunda bu kapsama raporunu basar.

Kullanım (repo kökünden):
  python refresh_price_cache.py                  # eligible + benchmark (küçük, hızlı)
  python refresh_price_cache.py --control 3000   # + 3000 kontrol sembolü (kota tüketir)
  python refresh_price_cache.py --report-only    # fetch YOK, yalnız kapsama raporu
  python refresh_price_cache.py --from 2026-05-01 --sleep 0.15

Ağ yoksa/anahtar yoksa fetch atlanır; --report-only her zaman çalışır.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import date, datetime, timedelta

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

LEDGER = "data/shadow/scan_shadow.jsonl"
PRICE_DIR = "data/price_cache"
DEFAULT_FROM = "2026-05-01"  # ATR-14 lookback + Temmuz sinyalleri için yeterli taban
HORIZON = 5

# Benchmark + sektör ETF'leri (göreli/excess-return ve rejim mercekleri için)
BENCHMARKS = [
    "SPY",
    "QQQ",
    "IWM",
    "DIA",
    "XLK",
    "XLF",
    "XLE",
    "XLV",
    "XLY",
    "XLI",
    "XLP",
    "XLU",
    "XLB",
]


# ---------------------------------------------------------------- .env
def load_env(path: str = ".env") -> dict:
    env = {}
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


# ---------------------------------------------------------------- semboller
def gather_symbols(include_control: bool, control_limit: int | None):
    """Gölge defterinden (eligible sinyaller, tüm sembol seti) döndür."""
    eligible: list[tuple[str, str]] = []  # (symbol, signal_date)
    symbols: set[str] = set()
    control_syms: set[str] = set()
    with open(LEDGER, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            sym = r.get("symbol")
            d = (r.get("timestamp") or "")[:10]
            if not sym or not d:
                continue
            if r.get("selection_eligible") or r.get("entry_ok"):
                eligible.append((sym, d))
                symbols.add(sym)
            elif include_control:
                control_syms.add(sym)
    if include_control:
        extra = sorted(control_syms)
        if control_limit:
            extra = extra[:control_limit]
        symbols.update(extra)
    symbols.update(BENCHMARKS)
    # dedup eligible (symbol, gün)
    eligible = sorted(set(eligible))
    return eligible, sorted(symbols)


# ---------------------------------------------------------------- cache I/O
def load_cache(sym: str) -> list[dict]:
    p = os.path.join(PRICE_DIR, f"{sym}.json")
    if not os.path.exists(p):
        return []
    try:
        d = json.load(open(p, encoding="utf-8"))
        return d if isinstance(d, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def last_date(bars: list[dict]) -> str | None:
    return max((b["date"] for b in bars if b.get("date")), default=None)


def merge_cache(sym: str, new_bars: list[dict]) -> int:
    """Var olan + yeni barları tarih bazında birleştir, yaz. Eklenen bar sayısını döndür."""
    existing = load_cache(sym)
    by_date = {b["date"]: b for b in existing if b.get("date")}
    added = 0
    for b in new_bars:
        if not b.get("date"):
            continue
        if b["date"] not in by_date:
            added += 1
        by_date[b["date"]] = b  # yeni veri eskiyi günceller
    merged = [by_date[k] for k in sorted(by_date)]
    os.makedirs(PRICE_DIR, exist_ok=True)
    tmp = os.path.join(PRICE_DIR, f".{sym}.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(merged, f)
    os.replace(tmp, os.path.join(PRICE_DIR, f"{sym}.json"))  # atomik
    return added


# ---------------------------------------------------------------- EODHD fetch
def fetch_eod(sym: str, key: str, start: str, end: str) -> list[dict] | None:
    """EODHD /eod → price_cache formatı. None = hata (istek başarısız)."""
    import requests  # local bağımlılık; sandbox'ta ağ yok

    # EODHD nokta içeren tickerları '-' ile bekler (BRK.B -> BRK-B)
    eod_sym = sym.replace(".", "-")
    url = f"https://eodhd.com/api/eod/{eod_sym}.US"
    try:
        r = requests.get(
            url,
            params={"api_token": key, "fmt": "json", "from": start, "to": end, "period": "d"},
            timeout=30,
        )
    except Exception:
        return None
    if r.status_code == 429:
        return None  # rate limit — çağıran retry eder
    if r.status_code != 200:
        return []  # sembol yok/veri yok → boş (hata değil)
    try:
        raw = r.json()
    except ValueError:
        return None
    out = []
    for b in raw:
        if not b.get("date"):
            continue
        out.append(
            {
                "date": b["date"],
                "open": b.get("open"),
                "high": b.get("high"),
                "low": b.get("low"),
                "close": b.get("close"),
                "volume": b.get("volume"),
            }
        )
    return out


# ---------------------------------------------------------------- kapsama raporu
def coverage_report(eligible: list[tuple[str, str]], horizon: int = HORIZON) -> dict:
    resolvable = pending = no_cache = 0
    for sym, d in eligible:
        bars = load_cache(sym)
        if not bars:
            no_cache += 1
            continue
        dates = [b["date"] for b in bars]
        entry_idx = next((i for i, x in enumerate(dates) if x > d), None)
        if entry_idx is None or (len(dates) - entry_idx) < horizon:
            pending += 1
        else:
            resolvable += 1
    total = len(eligible)
    pct = round(100 * resolvable / total, 1) if total else 0.0
    return {
        "total": total,
        "resolvable": resolvable,
        "pending": pending,
        "no_cache": no_cache,
        "pct": pct,
    }


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--control",
        type=int,
        default=0,
        help="Bu kadar reddedilen kontrol sembolü de çek (0=kapalı)",
    )
    ap.add_argument("--report-only", action="store_true", help="Fetch yok; yalnız kapsama raporu")
    ap.add_argument(
        "--from", dest="from_date", default=DEFAULT_FROM, help="Cache yoksa başlangıç tarihi"
    )
    ap.add_argument("--sleep", type=float, default=0.12, help="İstekler arası bekleme (rate-limit)")
    ap.add_argument("--force", action="store_true", help="Güncel olsa bile yeniden çek")
    args = ap.parse_args()

    include_control = args.control > 0
    eligible, symbols = gather_symbols(include_control, args.control or None)
    print(
        f"Eligible sinyal: {len(eligible)} | çekilecek benzersiz sembol: {len(symbols)} "
        f"(benchmark {len(BENCHMARKS)}{' + kontrol' if include_control else ''})"
    )

    print("\n=== ÖNCE: kapsama ===")
    before = coverage_report(eligible)
    print(
        f"  çözülebilir {before['resolvable']}/{before['total']} (%{before['pct']}) | "
        f"pending {before['pending']} | cache yok {before['no_cache']}"
    )

    if args.report_only:
        print("\n(--report-only: fetch atlandı)")
        _verdict(before)
        return

    key = load_env().get("EODHD_API_KEY", "")
    if not key:
        print(
            "\nHATA: EODHD_API_KEY .env'de yok. Anahtarı ekleyip tekrar çalıştır "
            "(veya --report-only kullan)."
        )
        return

    today = date.today().isoformat()
    ok = fail = skip = added_total = 0
    for i, sym in enumerate(symbols, 1):
        bars = load_cache(sym)
        ld = last_date(bars)
        if ld and ld >= today and not args.force:
            skip += 1
            continue
        start = (
            (datetime.fromisoformat(ld).date() + timedelta(days=1)).isoformat()
            if ld
            else args.from_date
        )
        # retry (rate-limit / geçici hata)
        new = None
        for attempt in range(3):
            new = fetch_eod(sym, key, start, today)
            if new is not None:
                break
            time.sleep(1.5 * (attempt + 1))
        if new is None:
            fail += 1
        else:
            added_total += merge_cache(sym, new)
            ok += 1
        if i % 50 == 0:
            print(f"  ... {i}/{len(symbols)} (ok={ok} fail={fail} skip={skip})")
        time.sleep(args.sleep)

    print(f"\nFetch bitti: ok={ok} fail={fail} skip={skip} | eklenen bar={added_total}")

    print("\n=== SONRA: kapsama ===")
    after = coverage_report(eligible)
    print(
        f"  çözülebilir {after['resolvable']}/{after['total']} (%{after['pct']}) | "
        f"pending {after['pending']} | cache yok {after['no_cache']}"
    )
    _verdict(after)


def _verdict(cov: dict):
    if cov["pct"] >= 90:
        print(
            f"\n✅ FAZ 0 KABUL: kapsama %{cov['pct']} ≥ %90. shadow_scorecard.py artık gerçek sonuç üretir."
        )
    else:
        pend = cov["pending"]
        print(
            f"\n⏳ Kapsama %{cov['pct']} (<%90). Kalan {pend} sinyal muhtemelen son 5 günün "
            f"(henüz olgunlaşmamış) sinyalleri — birkaç işlem günü sonra tekrar çalıştır."
        )


if __name__ == "__main__":
    main()
