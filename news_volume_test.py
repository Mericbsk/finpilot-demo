#!/usr/bin/env python3
"""
HABER AKISI + VOLUME KOMBINASYON TESTI
======================================
Soru: haber akisi (news spike/sentiment) + volume (RVOL) BIRLIKTE anlamli
hareketi (>=%5/%10) her birinden daha iyi yakaliyor mu (interaction)?

Haber kaynagi: EODHD news API (tarih + sentiment polarity). RVOL: enriched CSV.
Her sinyal icin sinyal oncesi 3 gunde haber sayisi + ort sentiment.

Kullanim:  pip install requests ; python news_volume_test.py [--limit 0]
Ciktinin TAMAMINI Claude'a yapistir.
"""

import argparse
import csv
import datetime as dt
import json
import os
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
bd = os.path.join(ROOT, "data", "backtest_out")
CSVP = os.path.join(bd, "enriched_signals_v3.csv")
if not os.path.exists(CSVP):
    CSVP = os.path.join(bd, "enriched_signals_v2.csv")
CACHE = os.path.join(ROOT, "data", "news_cache")
os.makedirs(CACHE, exist_ok=True)
try:
    import requests
except ImportError:
    raise SystemExit("pip install requests") from None


def env():
    e = {}
    for line in open(os.path.join(ROOT, ".env")):
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip()] = v.strip().strip('"').strip("'")
    return e


KEY = env().get("EODHD_API_KEY", "")


def ff(x):
    try:
        return float(x)
    except Exception:
        return None


def fetch_news(sym):
    cf = os.path.join(CACHE, f"{sym}.json")
    if os.path.exists(cf):
        try:
            return json.load(open(cf))
        except Exception:
            return []
    out = []
    try:
        r = requests.get(
            "https://eodhd.com/api/news",
            params={
                "api_token": KEY,
                "s": f"{sym}.US",
                "from": "2025-08-01",
                "to": "2026-07-01",
                "limit": 1000,
            },
            timeout=30,
        )
        if r.status_code == 200:
            for a in r.json():
                d = (a.get("date") or "")[:10]
                pol = None
                sent = a.get("sentiment") or {}
                if isinstance(sent, dict):
                    pol = ff(sent.get("polarity"))
                if d:
                    out.append((d, pol))
    except Exception:
        pass
    json.dump(out, open(cf, "w"))
    time.sleep(0.09)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()
    rows = [r for r in csv.DictReader(open(CSVP)) if ff(r.get("resolved_pct_t5")) is not None]
    if a.limit > 0:
        rows = rows[: a.limit]
    for r in rows:
        r["y5"] = 1 if ff(r["resolved_pct_t5"]) >= 5 else 0
        r["y10"] = 1 if ff(r["resolved_pct_t5"]) >= 10 else 0
    syms = sorted({r["symbol"] for r in rows})
    print(f"Sinyal: {len(rows)}  sembol: {len(syms)}  EODHD news cekiliyor...")
    news = {}
    for i, s in enumerate(syms, 1):
        news[s] = fetch_news(s)
        if i % 50 == 0:
            print(f"  {i}/{len(syms)}...")
    # her sinyale haber sayisi + ort sentiment (sinyal oncesi 3 gun)
    for r in rows:
        d = r["signal_date"][:10]
        d0 = dt.date.fromisoformat(d)
        lo = (d0 - dt.timedelta(days=3)).isoformat()
        arts = [(dd, pol) for dd, pol in news.get(r["symbol"], []) if lo <= dd <= d]
        r["ncount"] = len(arts)
        pols = [p for _, p in arts if p is not None]
        r["nsent"] = sum(pols) / len(pols) if pols else 0.0
    covsym = sum(1 for s in syms if news.get(s))
    print(f"Haber verisi olan sembol: {covsym}/{len(syms)}")

    def RV(r):
        return ff(r.get("rvol")) or 0

    def P(sub, k):
        return sum(r[k] for r in sub) / len(sub) if sub else 0

    N = len(rows)
    b5 = P(rows, "y5")
    b10 = P(rows, "y10")
    print(f"\nBAZ: >=5% {b5*100:.1f}%  >=10% {b10*100:.1f}%  (n={N})")

    def show(name, sub):
        if len(sub) < 25:
            print(f"  {name:34s} n={len(sub)} (yetersiz)")
            return
        print(
            f"  {name:34s} n={len(sub):>5} >=5% {P(sub,'y5')*100:5.1f}% (lift {P(sub,'y5')/b5:.2f})  >=10% {P(sub,'y10')*100:5.1f}% (lift {P(sub,'y10')/b10:.2f})"
        )

    print("\n=== TEK BASINA ===")
    show("haber>=1 (son 3g)", [r for r in rows if r["ncount"] >= 1])
    show("haber>=3 (spike)", [r for r in rows if r["ncount"] >= 3])
    show("pozitif sentiment (>0.1)", [r for r in rows if r["nsent"] > 0.1])
    show("RVOL>=2", [r for r in rows if RV(r) >= 2])
    show("RVOL>=3", [r for r in rows if RV(r) >= 3])
    print("\n=== HABER + VOLUME KOMBINASYONU (interaction) ===")
    show("haber>=1 & RVOL>=2", [r for r in rows if r["ncount"] >= 1 and RV(r) >= 2])
    show("haber>=3 & RVOL>=2", [r for r in rows if r["ncount"] >= 3 and RV(r) >= 2])
    show("haber>=3 & RVOL>=3", [r for r in rows if r["ncount"] >= 3 and RV(r) >= 3])
    show("poz.sent & RVOL>=2", [r for r in rows if r["nsent"] > 0.1 and RV(r) >= 2])
    show(
        "haber>=1 & RVOL<1.2 (haber var,hacim yok)",
        [r for r in rows if r["ncount"] >= 1 and RV(r) < 1.2],
    )
    print(
        "\n>>> Kombinasyon lift'i, haber-tek ve RVOL-tek lift'lerinin ikisinden de BELIRGIN yuksekse"
    )
    print("    haber+volume gercek bir etkilesim/anlamli sinyaldir. Degilse sadece toplamsaldir.")
    print("Bu ciktinin TAMAMINI Claude'a yapistir.")


if __name__ == "__main__":
    main()
