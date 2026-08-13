#!/usr/bin/env python3
"""regime_layers_full.py — TAM EVREN (1926 sembol) sektör-trend replikasyonu + mekanizma.

(1) Doğrulama: korelasyon-atamalı sektör, sector_cache'teki 143 gerçek sektörle uyuşuyor mu?
(2) Sektör-trend koşullaması tüm evrende tutuyor mu (IS/OOS)?
(3) Mekanizma: sektör-nötr residual (sembol getirisi − sektör ETF getirisi) üzerinde de
    S_off kötü mü? Evetse gerçek sektör-seçimi; hayırsa yalnız beta/selection.
"""

from __future__ import annotations

import csv
import json
import statistics
import sys

from regime_layers_test import ETF, SEC_MAP

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# ETF serileri (fwd getirisi için de gerekli)
etf_syms = ["XLK", "XLV", "XLF", "XLY", "XLP", "XLI", "XLE", "XLB", "XLRE", "XLU", "XLC"]
etfs = {e: ETF(e) for e in etf_syms}


def etf_fwd5(e, d):
    """Sektör ETF'inin scan_date'ten 5 gün ileri close-to-close getirisi (%)."""
    et = etfs[e]
    i = et.asof(d)
    if i is None or i + 5 >= len(et.close):
        return None
    return (et.close[i + 5] / et.close[i] - 1) * 100


# tam-evren korelasyon-atamalı harita
full = {
    r["symbol"]: r["etf"]
    for r in csv.DictReader(open("data/backtest_out/sector_map_full.csv"))
    if r["etf"]
}

# (1) DOĞRULAMA — 143 gerçek sektöre karşı
real = json.load(open("data/sector_cache.json"))
agree = tot = 0
for s, sname in real.items():
    metf = SEC_MAP.get(sname)
    if metf and s in full:
        tot += 1
        if full[s] == metf:
            agree += 1
print(f"=== (1) DOĞRULAMA: korelasyon-atama vs gerçek sektör (n={tot}) ===")
print(f"  tam uyum: {agree}/{tot} = {100*agree/tot:.0f}%  (11 sınıf; şans ~9%)")

# Y (sembol regime)
yreg = {}
for r in csv.DictReader(open("data/backtest_out/full_universe_enriched.csv")):
    yreg[(r["symbol"], str(r["scan_date"]))] = r.get("regime") == "True"

rows = []
for r in csv.DictReader(open("data/backtest_out/edge_recheck.csv")):
    s = r["symbol"]
    if s not in full:
        continue
    d = str(r["scan_date"])
    try:
        c2c = float(r["c2c5_net"])
    except (ValueError, KeyError):
        continue
    ssig = etfs[full[s]].signals(d)
    if ssig is None:
        continue
    y = yreg.get((s, d))
    if y is None:
        continue
    sf = etf_fwd5(full[s], d)
    rows.append(
        {
            "date": d,
            "S": ssig["close"] >= ssig["s200"],
            "Y": y,
            "c2c": c2c,
            "win": c2c > 0,
            "resid": (c2c - sf) if sf is not None else None,
        }
    )

dates = sorted({x["date"] for x in rows})
cut = dates[len(dates) // 2]
print(f"\ntam-evren eşleşen satır: n={len(rows)}")


def st(sub, lbl, key="c2c"):
    v = [x[key] for x in sub if x[key] is not None]
    if len(v) < 20:
        return f"{lbl:32} n={len(v)}"
    w = 100 * sum(1 for x in v if x > 0) / len(v)
    return f"{lbl:32} n={len(v):5d}  win%={w:5.1f}  med={statistics.median(v):+6.2f}"


print("\n=== (2) SEKTÖR-TREND koşullaması, Y_on (sembol bullish), TAM EVREN — honest c2c5_net ===")
for nm, f in [("IS", lambda x: x["date"] < cut), ("OOS", lambda x: x["date"] >= cut)]:
    sub = [x for x in rows if f(x) and x["Y"]]
    print(f"-- {nm} --")
    print("  " + st([x for x in sub if x["S"]], "sektör YÜKSELIŞ (S_on)"))
    print("  " + st([x for x in sub if not x["S"]], "sektör DÜŞÜŞ  (S_off)"))

print("\n=== (3) MEKANİZMA: sektör-NÖTR residual (sembol − sektör ETF, 5g) ===")
print("    S_off residual'de de kötüyse → gerçek; nötrleşiyorsa → sadece beta.")
for nm, f in [("IS", lambda x: x["date"] < cut), ("OOS", lambda x: x["date"] >= cut)]:
    sub = [x for x in rows if f(x) and x["Y"] and x["resid"] is not None]
    print(f"-- {nm} (residual) --")
    print("  " + st([x for x in sub if x["S"]], "S_on residual", "resid"))
    print("  " + st([x for x in sub if not x["S"]], "S_off residual", "resid"))
