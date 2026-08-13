#!/usr/bin/env python3
"""Takip: S_trend (sektör trendi) katmanının (1) IS/OOS dayanıklılığı,
(2) ATR-risk boyutundan bağımsızlığı. regime_layers_test'in veri kurulumunu yeniden kurar."""

from __future__ import annotations

import csv
import json
import statistics
import sys

from regime_layers_test import ETF, SEC_MAP

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

spy = ETF("SPY")
etfs = {e: ETF(e) for e in set(SEC_MAP.values())}
sec = json.load(open("data/sector_cache.json"))
yreg = {}
for r in csv.DictReader(open("data/backtest_out/full_universe_enriched.csv")):
    yreg[(r["symbol"], str(r["scan_date"]))] = r.get("regime") == "True"

rows = []
for r in csv.DictReader(open("data/backtest_out/edge_recheck.csv")):
    s = r["symbol"]
    if s not in sec or sec[s] not in SEC_MAP:
        continue
    d = str(r["scan_date"])
    try:
        c2c = float(r["c2c5_net"])
        atr = float(r["atr_pct"])
        mae = float(r["mae5"])
    except (ValueError, KeyError):
        continue
    ssig = etfs[SEC_MAP[sec[s]]].signals(d)
    if ssig is None:
        continue
    y = yreg.get((s, d))
    if y is None:
        continue
    rows.append(
        {
            "date": d,
            "S": ssig["close"] >= ssig["s200"],
            "Y": y,
            "M": r.get("regime") == "bull",
            "c2c": c2c,
            "win": c2c > 0,
            "atr": atr,
        }
    )

dates = sorted({x["date"] for x in rows})
cut = dates[len(dates) // 2]


def st(sub, lbl):
    if len(sub) < 20:
        return f"{lbl:30} n={len(sub)}"
    w = 100 * sum(x["win"] for x in sub) / len(sub)
    return f"{lbl:30} n={len(sub):5d}  win%={w:5.1f}  medRet={statistics.median(x['c2c'] for x in sub):+6.2f}"


print("=== S_trend etkisi, SADECE Y_on (sembol bullish) — IS/OOS ===")
for nm, sub in [
    ("IS", [x for x in rows if x["date"] < cut and x["Y"]]),
    ("OOS", [x for x in rows if x["date"] >= cut and x["Y"]]),
]:
    print(f"-- {nm} --")
    print("  " + st([x for x in sub if x["S"]], "sektör YÜKSELIŞ (S_on)"))
    print("  " + st([x for x in sub if not x["S"]], "sektör DÜŞÜŞ  (S_off)"))

print("\n=== S_trend, ATR terzilinde kontrollü (risk-proxy değil mi?) ===")
atrs = sorted(x["atr"] for x in rows)
lo, hi = atrs[len(atrs) // 3], atrs[2 * len(atrs) // 3]
for band, f in [
    ("düşük-ATR", lambda x: x["atr"] <= lo),
    ("orta-ATR", lambda x: lo < x["atr"] <= hi),
    ("yüksek-ATR", lambda x: x["atr"] > hi),
]:
    b = [x for x in rows if f(x) and x["Y"]]
    print(f"-- {band} (Y_on) --")
    print("  " + st([x for x in b if x["S"]], "S_on"))
    print("  " + st([x for x in b if not x["S"]], "S_off"))
