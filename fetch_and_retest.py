#!/usr/bin/env python3
"""
FinPilot — Yerel Veri Cekme + Yeniden Backtest
==============================================
Bu script SENIN MAKINENDE calistirilir (ag erisimi + gercek API anahtarlari gerekir).
Claude'un calistigi sandbox tum dis baglantilari engelledigi icin oradan cekilemedi.

Ne yapar:
  1) .env'den anahtarlari okur (EODHD birincil, Alpaca yedek).
  2) Cozulmemis/yeni sinyaller icin gunluk OHLCV ceker (on-disk cache ile).
  3) Sonuclari hesaplar: resolved_pct_t5 (T+1..T+5 maks hareket), resolved_pct_1d.
  4) Fiyattan TUREYEN eksik ozellikleri ekler: gap%, RVOL, ATR%, 52h-yukseğe yakinlik.
  5) (Opsiyonel) EODHD fundamentals: float, short interest.
  6) Zenginlestirilmis veriyle tek-sinyal + kombinasyon backtest'i kosar, sonuc yazar.

Kullanim:
  pip install requests
  # .env icine EODHD_API_KEY=... ekle (yoksa Alpaca kullanir)
  python fetch_and_retest.py --provider eodhd --with-fundamentals
  python fetch_and_retest.py --provider alpaca           # Alpaca ile
"""

import argparse
import glob
import json
import os
import sqlite3
import time
from datetime import datetime, timedelta

try:
    import requests
except ImportError:
    raise SystemExit("Once: pip install requests")
import numpy as np

ROOT = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(ROOT, "data", "finpilot.db")
CACHE = os.path.join(ROOT, "data", "price_cache")
OUT = os.path.join(ROOT, "data", "backtest_out")
os.makedirs(CACHE, exist_ok=True)
os.makedirs(OUT, exist_ok=True)


# ---------------------------------------------------------------- env
def load_env():
    env = {}
    p = os.path.join(ROOT, ".env")
    if os.path.exists(p):
        for line in open(p):
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    return env


ENV = load_env()


# ---------------------------------------------------------------- providers
def fetch_eodhd(sym, start, end):
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
            dict(
                date=b["date"],
                open=b.get("open"),
                high=b.get("high"),
                low=b.get("low"),
                close=b.get("close"),
                volume=b.get("volume"),
            )
        )
    return out


def fetch_alpaca(sym, start, end):
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
                dict(
                    date=b["t"][:10],
                    open=b["o"],
                    high=b["h"],
                    low=b["l"],
                    close=b["c"],
                    volume=b["v"],
                )
            )
        page = j.get("next_page_token")
        if not page:
            break
    return out


def fetch_fundamentals_eodhd(sym):
    key = ENV.get("EODHD_API_KEY", "")
    if not key:
        return {}
    try:
        r = requests.get(
            f"https://eodhd.com/api/fundamentals/{sym}.US", params={"api_token": key}, timeout=30
        )
        if r.status_code != 200:
            return {}
        j = r.json()
        ss = j.get("SharesStats", {}) or {}
        return dict(
            float_shares=ss.get("SharesFloat"),
            short_pct=ss.get("ShortPercentFloat") or ss.get("ShortPercent"),
        )
    except Exception:
        return {}


# ---------------------------------------------------------------- bars cache
def get_bars(sym, provider):
    """Tum gerekli araligi tek seferde cek, cache'le."""
    cf = os.path.join(CACHE, f"{sym}.json")
    if os.path.exists(cf):
        try:
            return json.load(open(cf))
        except Exception:
            pass
    end = (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d")
    start = "2024-09-01"  # 52-hafta + RVOL lookback icin genis
    fn = fetch_eodhd if provider == "eodhd" else fetch_alpaca
    bars = fn(sym, start, end)
    bars.sort(key=lambda b: b["date"])
    json.dump(bars, open(cf, "w"))
    time.sleep(0.12)  # nazik rate-limit
    return bars


# ---------------------------------------------------------------- resolve + features
def resolve_and_features(entry, sig_date, bars):
    """bars: tarih sirali. sig_date sonrasi T+1..T+5 maks hareket + fiyat ozellikleri."""
    idx = {b["date"]: i for i, b in enumerate(bars)}
    # signal gununun bar index'i (yoksa ilk >= sig_date)
    di = idx.get(sig_date)
    if di is None:
        for i, b in enumerate(bars):
            if b["date"] >= sig_date:
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
    # features
    prev = bars[di - 1]["close"] if di >= 1 else None
    gap = (bars[di]["open"] - prev) / prev * 100 if (prev and bars[di].get("open")) else None
    vols = [b["volume"] for b in bars[max(0, di - 20) : di] if b.get("volume")]
    rvol = (
        (bars[di]["volume"] / (sum(vols) / len(vols)))
        if (vols and bars[di].get("volume"))
        else None
    )
    # ATR14
    trs = []
    for j in range(max(1, di - 13), di + 1):
        h, l, pc = bars[j]["high"], bars[j]["low"], bars[j - 1]["close"]
        trs.append(max(h - l, abs(h - pc), abs(l - pc)))
    atr_pct = (
        (sum(trs) / len(trs)) / bars[di]["close"] * 100 if (trs and bars[di].get("close")) else None
    )
    hh = [b["high"] for b in bars[max(0, di - 252) : di + 1] if b.get("high")]
    dist52 = bars[di]["close"] / max(hh) if hh else None
    return dict(
        resolved_pct_t5=t5_max,
        resolved_pct_1d=r1,
        gap_pct=gap,
        rvol=rvol,
        atr_pct=atr_pct,
        dist_52w_high=dist52,
    )


# ---------------------------------------------------------------- collect signals
def collect_signals():
    c = sqlite3.connect(DB)
    recs = []
    # archive (oncelik: cozulmemisler; cozulmusler zaten var ama hepsini yeniden zenginlestir)
    for sid, sym, ts, sc, pj in c.execute(
        "select id,symbol,ts,score,payload_json from signals_archive"
    ):
        try:
            d = json.loads(pj)
        except Exception:
            d = {}
        recs.append(
            dict(
                src="archive",
                id=sid,
                symbol=sym,
                signal_date=(ts or "")[:10],
                entry=d.get("entry_price"),
                score=sc,
                rr=d.get("risk_reward"),
                regime=str(d.get("regime")),
            )
        )
    for sid, sym, sd, e, sc, rr, rg in c.execute(
        "select id,symbol,signal_date,entry_price,score,risk_reward,regime from watchlist_signals"
    ):
        recs.append(
            dict(
                src="watchlist",
                id=sid,
                symbol=sym,
                signal_date=sd,
                entry=e,
                score=sc,
                rr=rr,
                regime=str(rg),
            )
        )
    for f in glob.glob(os.path.join(ROOT, "data", "daily_reports", "2026-0[56]*.json")):
        d = json.load(open(f))
        for t in d.get("top_signals", []):
            recs.append(
                dict(
                    src="daily",
                    id=f"{d['date']}_{t['ticker']}",
                    symbol=t["ticker"],
                    signal_date=d["date"],
                    entry=t.get("entry") or t.get("tp"),
                    score=t.get("score"),
                    rr=t.get("rr"),
                    regime="",
                )
            )
    c.close()
    return recs


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--provider", choices=["eodhd", "alpaca"], default="eodhd")
    ap.add_argument(
        "--with-fundamentals",
        action="store_true",
        help="EODHD fundamentals'tan float + short interest cek (yavas)",
    )
    ap.add_argument("--limit", type=int, default=0, help="test icin sembol sayisini sinirla")
    args = ap.parse_args()

    recs = collect_signals()
    syms = sorted({r["symbol"] for r in recs})
    if args.limit:
        syms = syms[: args.limit]
    print(f"{len(recs)} sinyal, {len(syms)} sembol. Saglayici: {args.provider}")

    funda = {}
    bars_cache = {}
    for i, s in enumerate(syms, 1):
        try:
            bars_cache[s] = get_bars(s, args.provider)
        except SystemExit:
            raise
        except Exception:
            bars_cache[s] = []
        if args.with_fundamentals and args.provider == "eodhd":
            funda[s] = fetch_fundamentals_eodhd(s)
            time.sleep(0.1)
        if i % 25 == 0:
            print(f"  {i}/{len(syms)} sembol cekildi...")

    enriched = []
    for r in recs:
        bars = bars_cache.get(r["symbol"], [])
        if not bars:
            continue
        rf = resolve_and_features(r["entry"], r["signal_date"], bars)
        if not rf:
            continue
        row = dict(r)
        row.update(rf)
        if r["symbol"] in funda:
            row.update(funda[r["symbol"]])
        enriched.append(row)
    print(f"Cozulen + zenginlestirilen: {len(enriched)}")

    # kaydet
    import csv

    keys = [
        "src",
        "id",
        "symbol",
        "signal_date",
        "entry",
        "score",
        "rr",
        "regime",
        "resolved_pct_t5",
        "resolved_pct_1d",
        "gap_pct",
        "rvol",
        "atr_pct",
        "dist_52w_high",
        "float_shares",
        "short_pct",
    ]
    with open(os.path.join(OUT, "enriched_signals.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for r in enriched:
            w.writerow({k: r.get(k) for k in keys})

    # --- backtest: tek sinyal (yeni ozellikler dahil) ---
    Y = np.array(
        [
            1 if (r.get("resolved_pct_t5") is not None and r["resolved_pct_t5"] >= 5) else 0
            for r in enriched
            if r.get("resolved_pct_t5") is not None
        ]
    )
    valid = [r for r in enriched if r.get("resolved_pct_t5") is not None]
    base = Y.mean() if len(Y) else float("nan")
    print(f"\nBaz oran (T+5 maks >=5%): {base:.3f}  (n={len(valid)})")

    def lift(mask_fn, label):
        sub = [r for r in valid if mask_fn(r)]
        if len(sub) < 30:
            return None
        h = np.mean([1 if r["resolved_pct_t5"] >= 5 else 0 for r in sub])
        return dict(
            label=label,
            n=len(sub),
            hit=round(float(h), 4),
            lift=round(float(h / base), 3) if base > 0 else None,
        )

    tests = [
        ("RVOL >= 2x", lambda r: (r.get("rvol") or 0) >= 2),
        ("RVOL >= 3x", lambda r: (r.get("rvol") or 0) >= 3),
        ("gap > 5%", lambda r: (r.get("gap_pct") or -99) > 5),
        ("ATR% >= 4", lambda r: (r.get("atr_pct") or 0) >= 4),
        ("52w-high yakin (>0.9)", lambda r: (r.get("dist_52w_high") or 0) > 0.9),
        ("RVOL>=2 + ATR%>=4", lambda r: (r.get("rvol") or 0) >= 2 and (r.get("atr_pct") or 0) >= 4),
        ("gap>5 + RVOL>=3", lambda r: (r.get("gap_pct") or -99) > 5 and (r.get("rvol") or 0) >= 3),
    ]
    results = [x for x in (lift(fn, lab) for lab, fn in tests) if x]
    print("\n=== YENI OZELLIKLERLE TEK-SINYAL + KOMBINASYON ===")
    for x in sorted(results, key=lambda d: -(d["lift"] or 0)):
        print(f"  {x['label']:24s} n={x['n']:>5} hit={x['hit']*100:>5.1f}% lift={x['lift']}")

    json.dump(
        dict(
            base_rate=round(float(base), 4), n=len(valid), results=results, provider=args.provider
        ),
        open(os.path.join(OUT, "fetch_retest_results.json"), "w"),
        indent=2,
    )
    print(f"\nYazildi: {OUT}/enriched_signals.csv ve fetch_retest_results.json")
    print("Sonraki adim: python backtest_signals.py  (ya da bu sonuclari skor motoruna besle)")


if __name__ == "__main__":
    main()
