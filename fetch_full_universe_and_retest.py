#!/usr/bin/env python3
"""
FinPilot — Tam-Evren (Full Universe) Backtest: konsolidasyon + zenginlestirme
==============================================================================
Mevcut backtest raporlari (backtest_signals.py, fetch_and_retest.py) SADECE
entry_ok=True (AL sinyali uretmis) sembolleri test etti. Bu script, scanner'in
HER taramada tum evren icin (entry_ok True/False farketmeksizin) yazdigi
data/shortlists/*.csv dosyalarini (2025-09-12 -> bugun, ~600+ dosya) kaynak
alarak GERCEK bir kontrol grubu (sinyal-olmayan semboller) ile backtest yapmayi
mumkun kilar.

IKI ASAMA:
  1) KONSOLIDASYON — data/shortlists/*.csv glob + parse. AG ERISIMI GEREKMEZ,
     herhangi bir makinede (bu sandbox dahil) calisir. --consolidate-only ile
     sadece bu adimi calistir.
  2) ZENGINLESTIRME — Alpaca/EODHD'den gunluk OHLCV cek, T+1..T+5 forward
     getiri + gap%/RVOL/ATR%/52h-yakinlik turet. AG ERISIMI + API ANAHTARI
     GEREKIR — SENIN MAKINENDE calistirilmali (fetch_and_retest.py ile ayni
     kisit: bu sandbox tum dis baglantilari engelliyor).

Dedup YOK: gun ici tekrar taramalarin HER BIRI ayri gozlem olarak tutulur
(kullanici karari). Fiyat cekme/forward-return hesaplama yine de sembol+tarih
basina BIR KEZ yapilir (cache) — sonuc tum kopya satirlara join'lenir, API
cagirisi israf edilmez.

Kullanim:
  python fetch_full_universe_and_retest.py --consolidate-only
  python fetch_full_universe_and_retest.py --provider alpaca
  python fetch_full_universe_and_retest.py --provider eodhd --with-fundamentals
  python fetch_full_universe_and_retest.py --provider alpaca --limit 200   # test
"""

from __future__ import annotations

import argparse
import csv
import glob
import json
import os
import time
from datetime import datetime, timedelta

ROOT = os.path.dirname(os.path.abspath(__file__))
SHORTLIST_DIR = os.path.join(ROOT, "data", "shortlists")
CACHE = os.path.join(ROOT, "data", "price_cache")  # fetch_and_retest.py ile PAYLASILAN cache
OUT = os.path.join(ROOT, "data", "backtest_out")
os.makedirs(CACHE, exist_ok=True)
os.makedirs(OUT, exist_ok=True)

RAW_CSV = os.path.join(OUT, "full_universe_raw.csv")
ENRICHED_CSV = os.path.join(OUT, "full_universe_enriched.csv")

RAW_KEYS = [
    "source_file",
    "symbol",
    "scan_ts",
    "scan_date",
    "price",
    "score",
    "composite_score",
    "regime",
    "direction",
    "entry_ok",
    "liquidity_ok",
    "risk_reward",
    "tier",
    "tier_score",
    "conviction_tier",
    "squeeze_factor",
    "catalyst_factor",
    "lottery_factor",
    "overnight_gap_factor",
    "sentiment",
    "vol_regime",
    "atr",
    "finpilot_score",
]

ENRICHED_KEYS = RAW_KEYS + [
    "resolved_pct_t5",
    "resolved_pct_1d",
    "gap_pct",
    "rvol",
    "atr_pct_real",
    "dist_52w_high",
]


# ---------------------------------------------------------------- env
def load_env():
    env = {}
    p = os.path.join(ROOT, ".env")
    if os.path.exists(p):
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    return env


ENV = load_env()


def _b(x):
    return str(x).strip().lower() in ("true", "1", "yes")


def _f(x):
    try:
        return None if x in (None, "") else float(x)
    except Exception:
        return None


# ---------------------------------------------------------------- stage 1: consolidate
def collect_universe_rows():
    """data/shortlists/*.csv -> tum satirlar, DEDUP YOK. Eksik kolonlar None olur
    (schema 10 ay icinde evrildi; DictReader eksik anahtar icin None dondurur)."""
    files = sorted(glob.glob(os.path.join(SHORTLIST_DIR, "*.csv")))
    rows = []
    for fp in files:
        fname = os.path.basename(fp)
        try:
            with open(fp, encoding="utf-8", errors="replace", newline="") as f:
                reader = csv.DictReader(f)
                for d in reader:
                    ts = (d.get("timestamp") or "").strip()
                    rows.append(
                        {
                            "source_file": fname,
                            "symbol": (d.get("symbol") or "").strip(),
                            "scan_ts": ts,
                            "scan_date": ts[:10] if ts else "",
                            "price": _f(d.get("price")),
                            "score": _f(d.get("score")),
                            "composite_score": _f(d.get("composite_score")),
                            "regime": d.get("regime"),
                            "direction": d.get("direction"),
                            "entry_ok": _b(d.get("entry_ok")),
                            "liquidity_ok": _b(d.get("liquidity_ok")),
                            "risk_reward": _f(d.get("risk_reward")),
                            "tier": d.get("tier") or None,
                            "tier_score": _f(d.get("tier_score")),
                            "conviction_tier": d.get("conviction_tier") or None,
                            "squeeze_factor": _f(d.get("squeeze_factor")),
                            "catalyst_factor": _f(d.get("catalyst_factor")),
                            "lottery_factor": _f(d.get("lottery_factor")),
                            "overnight_gap_factor": _f(d.get("overnight_gap_factor")),
                            "sentiment": _f(d.get("sentiment")),
                            "vol_regime": d.get("vol_regime"),
                            "atr": _f(d.get("atr")),
                            "finpilot_score": _f(d.get("finpilot_score")),
                        }
                    )
        except Exception as exc:
            print(f"[warn] {fname}: okunamadi ({exc})")
    return rows, files


def write_raw_csv(rows):
    with open(RAW_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=RAW_KEYS)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k) for k in RAW_KEYS})


# ---------------------------------------------------------------- stage 2: price fetch
def fetch_eodhd(sym, start, end):
    import requests

    key = ENV.get("EODHD_API_KEY", "")
    if not key:
        raise SystemExit("EODHD_API_KEY .env'de yok. --provider alpaca dene ya da anahtar ekle.")
    url = f"https://eodhd.com/api/eod/{sym}.US"
    r = requests.get(
        url,
        params={"api_token": key, "fmt": "json", "from": start, "to": end, "period": "d"},
        timeout=30,
    )
    if r.status_code != 200:
        return []
    out = []
    for b in r.json():
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


def fetch_alpaca(sym, start, end):
    import requests

    kid = ENV.get("ALPACA_API_KEY", "")
    sec = ENV.get("ALPACA_SECRET_KEY", "")
    if not (kid and sec):
        raise SystemExit("ALPACA_API_KEY/SECRET .env'de yok.")
    url = f"https://data.alpaca.markets/v2/stocks/{sym}/bars"
    hdr = {"APCA-API-KEY-ID": kid, "APCA-API-SECRET-KEY": sec}
    out, page = [], None
    while True:
        params = {
            "timeframe": "1Day",
            "start": start + "T00:00:00Z",
            "end": end + "T00:00:00Z",
            "limit": 10000,
            "adjustment": "raw",
            "feed": "iex",
        }
        if page:
            params["page_token"] = page
        r = requests.get(url, headers=hdr, params=params, timeout=30)
        if r.status_code != 200:
            break
        j = r.json()
        for b in j.get("bars", []) or []:
            out.append(
                {
                    "date": b["t"][:10],
                    "open": b["o"],
                    "high": b["h"],
                    "low": b["l"],
                    "close": b["c"],
                    "volume": b["v"],
                }
            )
        page = j.get("next_page_token")
        if not page:
            break
    return out


def get_bars(sym, provider):
    """Tum gerekli araligi tek seferde cek, cache'le (fetch_and_retest.py ile PAYLASILAN
    cache dizini — ayni sembol daha once cekilmisse tekrar cekilmez)."""
    cf = os.path.join(CACHE, f"{sym}.json")
    if os.path.exists(cf):
        try:
            return json.load(open(cf, encoding="utf-8"))
        except Exception:
            pass
    end = (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d")
    start = "2024-09-01"  # 52-hafta + RVOL lookback icin genis
    fn = fetch_eodhd if provider == "eodhd" else fetch_alpaca
    bars = fn(sym, start, end)
    bars.sort(key=lambda b: b["date"])
    json.dump(bars, open(cf, "w", encoding="utf-8"))
    time.sleep(0.12)  # nazik rate-limit
    return bars


def resolve_and_features(entry, scan_date, bars):
    """bars: tarih sirali. scan_date sonrasi T+1..T+5 maks hareket + fiyat ozellikleri.
    Ayni mantik fetch_and_retest.py::resolve_and_features ile — sembol+tarih basina
    BIR KEZ cagrilir (cagiran taraf memoize eder)."""
    if not scan_date:
        return None
    idx = {b["date"]: i for i, b in enumerate(bars)}
    di = idx.get(scan_date)
    if di is None:
        for i, b in enumerate(bars):
            if b["date"] >= scan_date:
                di = i
                break
    if di is None or di + 1 >= len(bars):
        return None
    e = entry or bars[di].get("close")
    if not e or e <= 0:
        return None
    fwd = bars[di + 1 : di + 6]
    if not fwd:
        return None
    highs = [b["high"] for b in fwd if b.get("high")]
    t5_max = (max(highs) - e) / e * 100 if highs else None
    c1 = fwd[0].get("close")
    r1 = (c1 - e) / e * 100 if c1 else None
    prev = bars[di - 1]["close"] if di >= 1 else None
    gap = (bars[di]["open"] - prev) / prev * 100 if (prev and bars[di].get("open")) else None
    vols = [b["volume"] for b in bars[max(0, di - 20) : di] if b.get("volume")]
    rvol = (
        (bars[di]["volume"] / (sum(vols) / len(vols)))
        if (vols and bars[di].get("volume"))
        else None
    )
    trs = []
    for j in range(max(1, di - 13), di + 1):
        h, low, pc = bars[j]["high"], bars[j]["low"], bars[j - 1]["close"]
        trs.append(max(h - low, abs(h - pc), abs(low - pc)))
    atr_pct = (
        (sum(trs) / len(trs)) / bars[di]["close"] * 100 if (trs and bars[di].get("close")) else None
    )
    hh = [b["high"] for b in bars[max(0, di - 252) : di + 1] if b.get("high")]
    dist52 = bars[di]["close"] / max(hh) if hh else None
    return {
        "resolved_pct_t5": t5_max,
        "resolved_pct_1d": r1,
        "gap_pct": gap,
        "rvol": rvol,
        "atr_pct_real": atr_pct,
        "dist_52w_high": dist52,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--consolidate-only",
        action="store_true",
        help="Sadece shortlist konsolidasyonu (ag erisimi YOK).",
    )
    ap.add_argument("--provider", choices=["eodhd", "alpaca"], default="alpaca")
    ap.add_argument(
        "--with-fundamentals",
        action="store_true",
        help="EODHD fundamentals'tan float + short interest cek (yavas, opsiyonel).",
    )
    ap.add_argument("--limit", type=int, default=0, help="test icin sembol sayisini sinirla")
    args = ap.parse_args()

    rows, files = collect_universe_rows()
    syms_all = sorted({r["symbol"] for r in rows if r["symbol"]})
    dates = sorted({r["scan_date"] for r in rows if r["scan_date"]})
    print(
        f"{len(files)} shortlist dosyasi -> {len(rows)} satir (dedup YOK), {len(syms_all)} sembol"
    )
    if dates:
        print(f"Tarih araligi: {dates[0]} -> {dates[-1]}")
    entry_ok_n = sum(1 for r in rows if r["entry_ok"])
    print(
        f"entry_ok=True: {entry_ok_n} satir ({entry_ok_n / len(rows) * 100:.1f}%)  |  "
        f"entry_ok=False (kontrol grubu): {len(rows) - entry_ok_n} satir"
    )

    write_raw_csv(rows)
    print(f"Yazildi: {RAW_CSV}")

    if args.consolidate_only:
        print("\n--consolidate-only: fiyat zenginlestirme atlandi (ag erisimi yok).")
        print("Devam etmek icin (SENIN MAKINENDE, ag + API anahtari gerekir):")
        print(f"  python fetch_full_universe_and_retest.py --provider {args.provider}")
        return

    syms = syms_all[: args.limit] if args.limit else syms_all
    print(f"\nFiyat cekiliyor: {len(syms)} sembol, saglayici={args.provider} ...")
    bars_cache = {}
    for i, s in enumerate(syms, 1):
        try:
            bars_cache[s] = get_bars(s, args.provider)
        except SystemExit:
            raise
        except Exception as exc:
            print(f"[warn] {s}: bar cekilemedi ({exc})")
            bars_cache[s] = []
        if i % 50 == 0:
            print(f"  {i}/{len(syms)} sembol cekildi...")

    # (symbol, scan_date) basina BIR KEZ resolve et, tum kopya satirlara join'le
    resolved_cache: dict[tuple[str, str], dict | None] = {}
    enriched = []
    skipped_no_bars = 0
    for r in rows:
        sym, sd = r["symbol"], r["scan_date"]
        if args.limit and sym not in bars_cache:
            continue  # limit ile sinirlandiysa kapsam disi sembolleri atla
        key = (sym, sd)
        if key not in resolved_cache:
            bars = bars_cache.get(sym, [])
            resolved_cache[key] = resolve_and_features(r["price"], sd, bars) if bars else None
        rf = resolved_cache[key]
        if rf is None:
            skipped_no_bars += 1
            continue
        row = dict(r)
        row.update(rf)
        enriched.append(row)

    print(f"\nCozulen + zenginlestirilen satir: {len(enriched)} (cozulemeyen: {skipped_no_bars})")
    with open(ENRICHED_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=ENRICHED_KEYS)
        w.writeheader()
        for r in enriched:
            w.writerow({k: r.get(k) for k in ENRICHED_KEYS})
    print(f"Yazildi: {ENRICHED_CSV}")
    print("\nSonraki adim: python backtest_full_universe.py")


if __name__ == "__main__":
    main()
