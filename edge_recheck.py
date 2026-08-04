#!/usr/bin/env python3
"""
edge_recheck.py — Metrik düzeltme + edge tekrar-koşu.

SORUN: full_universe_enriched.csv'deki `resolved_pct_t5` MFE-yanlı (en-iyi-durum),
gerçekleşen getiri değil → sahte ATR/skor edge'i üretiyor (bkz. 0.0 raporu).

BU SCRIPT: her (symbol, scan_date) için price_cache'ten DÜRÜST sonuç üretir:
  - c2c5      : gerçekleşen kapanış-kapanış 5g getiri (giriş = ertesi bar açılışı)
  - c2c5_net  : c2c5 - round-trip cost
  - tb_ret    : triple-barrier (TP=tp*ATR, SL=sl*ATR, bar-içi önce STOP), net cost
  - mfe5/mae5 : referans (en-iyi/en-kötü)
Ayrıca SPY 50-SMA rejimi ve skorları taşır.

RESUMABLE: her koşu en fazla --limit YENİ sembol işler, çıktıya EKLER. Bitene kadar
tekrar çalıştır. Tümü bitince (yeni sembol kalmayınca) analizi de basar.

Kullanım:
  python edge_recheck.py            # bir chunk işle (400 sembol)
  python edge_recheck.py --limit 300
  python edge_recheck.py --analyze  # sadece analiz (çıktı hazırsa)
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import statistics

ENRICHED = "data/backtest_out/full_universe_enriched.csv"
PD = "data/price_cache"
OUT = "data/backtest_out/edge_recheck.csv"
H = 5  # horizon (işlem günü)
TP_ATR = 2.0  # take-profit ATR çarpanı
SL_ATR = 1.0  # stop ATR çarpanı
COST = 0.5  # round-trip % (muhafazakâr; yüksek-ATR'de gerçekte daha yüksek)

_spy_reg = None


def spy_regime():
    global _spy_reg
    if _spy_reg is not None:
        return _spy_reg
    b = sorted(json.load(open(f"{PD}/SPY.json")), key=lambda x: x["date"])
    c = [x["close"] for x in b]
    d = [x["date"] for x in b]
    reg = {}
    for i in range(len(b)):
        if i < 50:
            continue
        reg[d[i]] = "bull" if c[i] >= statistics.mean(c[i - 50 : i]) else "bear"
    _spy_reg = reg
    return reg


def bars(sym):
    p = f"{PD}/{sym}.json"
    if not os.path.exists(p):
        return None
    try:
        b = json.load(open(p))
        return sorted(b, key=lambda x: x["date"]) if isinstance(b, list) and b else None
    except Exception:
        return None


def atr_pct(b, ei, p=14):
    if ei < p + 1:
        return None
    trs = [
        max(
            b[j]["high"] - b[j]["low"],
            abs(b[j]["high"] - b[j - 1]["close"]),
            abs(b[j]["low"] - b[j - 1]["close"]),
        )
        for j in range(ei - p, ei)
    ]
    atr = sum(trs) / len(trs)
    ref = b[ei]["open"] or b[ei - 1]["close"]
    return atr / ref if ref else None


def outcomes(b, ei, atrp):
    entry = b[ei]["open"] or b[ei]["close"]
    if not entry:
        return None
    c2c = (b[ei + H - 1]["close"] / entry - 1) * 100
    win = b[ei : ei + H]
    mfe = max((x["high"] / entry - 1) * 100 for x in win)
    mae = min((x["low"] / entry - 1) * 100 for x in win)
    tp = entry * (1 + TP_ATR * atrp)
    sl = entry * (1 - SL_ATR * atrp)
    tb = None
    for x in win:
        if x["low"] <= sl:
            tb = (sl / entry - 1) * 100
            break
        if x["high"] >= tp:
            tb = (tp / entry - 1) * 100
            break
    if tb is None:
        tb = (win[-1]["close"] / entry - 1) * 100
    return round(c2c, 3), round(c2c - COST, 3), round(tb - COST, 3), round(mfe, 3), round(mae, 3)


def build(limit):
    import pandas as pd

    df = pd.read_csv(ENRICHED, low_memory=False).dropna(subset=["symbol", "scan_date"])
    reg = spy_regime()
    done = set()
    exists = os.path.exists(OUT)
    if exists:
        for r in csv.DictReader(open(OUT)):
            done.add(r["symbol"])
    todo = [s for s in df.symbol.unique() if s not in done]
    print(f"toplam sembol {df.symbol.nunique()} | bitmiş {len(done)} | kalan {len(todo)}")
    batch = todo[:limit]
    cols = [
        "symbol",
        "scan_date",
        "regime",
        "score",
        "composite_score",
        "finpilot_score",
        "atr_pct",
        "c2c5",
        "c2c5_net",
        "tb_ret",
        "mfe5",
        "mae5",
    ]
    fh = open(OUT, "a", newline="")
    w = csv.DictWriter(fh, fieldnames=cols)
    if not exists:
        w.writeheader()
    n = 0
    for sym in batch:
        b = bars(sym)
        if not b:
            continue
        sub = df[df.symbol == sym]
        for _, r in sub.iterrows():
            d = str(r["scan_date"])
            ei = next((i for i, x in enumerate(b) if x["date"] > d), None)
            if ei is None or ei < 15 or ei + H - 1 >= len(b):
                continue
            a = atr_pct(b, ei)
            if not a:
                continue
            o = outcomes(b, ei, a)
            if not o:
                continue
            c2c, c2cnet, tb, mfe, mae = o
            w.writerow(
                {
                    "symbol": sym,
                    "scan_date": d,
                    "regime": reg.get(d, ""),
                    "score": r.get("score"),
                    "composite_score": r.get("composite_score"),
                    "finpilot_score": r.get("finpilot_score"),
                    "atr_pct": round(a * 100, 3),
                    "c2c5": c2c,
                    "c2c5_net": c2cnet,
                    "tb_ret": tb,
                    "mfe5": mfe,
                    "mae5": mae,
                }
            )
            n += 1
    fh.close()
    print(f"bu koşuda {len(batch)} sembol işlendi, {n} satır eklendi → {OUT}")
    print("kalan sembol:", len(todo) - len(batch), "(0 ise --analyze çalıştır)")


def analyze():
    import pandas as pd

    d = pd.read_csv(OUT)
    print(f"\n=== EDGE TEKRAR-KOŞU — DÜRÜST METRİKLER (n={len(d)}) ===")
    print(
        f"metrik medyanları: c2c5 {d.c2c5.median():.2f} | "
        f"c2c5_net {d.c2c5_net.median():.2f} | tb_ret {d.tb_ret.median():.2f} | "
        f"mfe5 {d.mfe5.median():.2f}"
    )

    def ic(a, b):
        m = a.notna() & b.notna()
        return (
            (a[m].rank().corr(b[m].rank()), int(m.sum()))
            if m.sum() >= 30
            else (float("nan"), int(m.sum()))
        )

    feats = ["score", "composite_score", "finpilot_score", "atr_pct"]
    for target in ["c2c5", "c2c5_net", "tb_ret", "mfe5"]:
        print(f"\n-- hedef: {target} — rank-IC --")
        for f in feats:
            v, n = ic(d[f], d[target])
            print(f"   {f:16} IC={v:+.3f} (n={n})")
    print("\n=== REJİM: skor/atr → c2c5 (dürüst) ===")
    for f in ["finpilot_score", "score", "atr_pct"]:
        parts = []
        for rg, sub in d.groupby("regime"):
            if rg == "":
                continue
            v, n = ic(sub[f], sub.c2c5)
            parts.append(f"{rg}:{v:+.3f}(n={n})")
        print(f"   {f:16} " + " | ".join(parts))
    print("\n=== atr decile → c2c5 medyan (dürüst) ===")
    dd = d.dropna(subset=["atr_pct", "c2c5"]).copy()
    dd["dec"] = (dd.atr_pct.rank(pct=True) * 10).clip(upper=9.999).astype(int)
    print("  ", dd.groupby("dec").c2c5.median().round(2).tolist())


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=400)
    ap.add_argument("--analyze", action="store_true")
    a = ap.parse_args()
    if a.analyze:
        analyze()
    else:
        build(a.limit)
