#!/usr/bin/env python3
"""
extension_exhaustion_test.py — Persona-1 Deney #3: entry_ok/conviction inversiyonu
extension/exhaustion kaynaklı mı?

Extension proxy'leri (mevcut enriched-kolonlar + price_cache'ten hesaplanan):
  dist_52w_high : enriched'te var (0=zirvede, negatif=zirveden uzak; işaret kontrol edilecek)
  gap_pct       : enriched'te var (sinyal-günü gap büyüklüğü)
  rvol          : enriched'te var (hacim-çarpanı)
  atr_ext20     : price_cache'ten — son 20g getiri / ATR (ne kadar "uzamış")
  close_loc     : sinyal-günü (close-low)/(high-low) — 1=güne güçlü kapanmış, 0=zayıf kapanmış

Test: her proxy'yi decile'lara böl, entry_ok eligible/rejected VE conviction_tier
A/B/C alt-kümelerinde win-rate/medRet ile kıyasla — monoton "extension yüksek → kötü" var mı?
"""

from __future__ import annotations

import csv
import json
import os
import statistics
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PD = "data/price_cache"
_bcache = {}


def bars(sym):
    if sym not in _bcache:
        p = f"{PD}/{sym}.json"
        if os.path.exists(p):
            try:
                b = json.load(open(p))
                _bcache[sym] = (
                    sorted(b, key=lambda x: x["date"]) if isinstance(b, list) and b else None
                )
            except Exception:
                _bcache[sym] = None
        else:
            _bcache[sym] = None
    return _bcache[sym]


def atr_ext_and_closeloc(sym, scan_date, p=14, lookback=20):
    b = bars(sym)
    if not b:
        return None, None
    dates = [x["date"] for x in b]
    import bisect

    ei = bisect.bisect_right(dates, scan_date) - 1
    if ei < max(p, lookback) + 1:
        return None, None
    trs = [
        max(
            b[j]["high"] - b[j]["low"],
            abs(b[j]["high"] - b[j - 1]["close"]),
            abs(b[j]["low"] - b[j - 1]["close"]),
        )
        for j in range(ei - p, ei)
    ]
    atr = sum(trs) / len(trs)
    if atr <= 0:
        return None, None
    ret20 = (b[ei]["close"] / b[ei - lookback]["close"] - 1) if b[ei - lookback]["close"] else None
    ext = (
        (ret20 * b[ei]["close"] / atr) if ret20 is not None else None
    )  # ATR-birim cinsinden 20g hareket
    hi, lo, cl = b[ei]["high"], b[ei]["low"], b[ei]["close"]
    closeloc = (cl - lo) / (hi - lo) if hi > lo else None
    return ext, closeloc


def main():
    rows = list(csv.DictReader(open("data/backtest_out/full_universe_enriched.csv")))
    print(f"toplam satır: {len(rows)}")

    # Sample: extension hesaplaması ağır (price_cache okuma) — yönetilebilir alt-küme al
    # entry_ok True/False + conviction_tier dolu olan satırları önceliklendir.
    sub = [r for r in rows if r.get("entry_ok") in ("True", "False")]
    print(f"entry_ok dolu satır: {len(sub)}")

    import random

    random.Random(11).shuffle(sub)
    sub = sub[:6000]  # zaman-bütçesi için örneklem

    enriched_data = []
    for r in sub:
        s, d = r["symbol"], str(r["scan_date"])
        ext, closeloc = atr_ext_and_closeloc(s, d)
        try:
            dist52 = float(r.get("dist_52w_high", "") or "nan")
        except ValueError:
            dist52 = float("nan")
        try:
            gap = float(r.get("gap_pct", "") or "nan")
        except ValueError:
            gap = float("nan")
        try:
            rvol = float(r.get("rvol", "") or "nan")
        except ValueError:
            rvol = float("nan")
        try:
            resolved = float(r.get("resolved_pct_1d", "") or "nan")
        except ValueError:
            resolved = None
        enriched_data.append(
            {
                "entry_ok": r["entry_ok"] == "True",
                "conviction": r.get("conviction_tier", ""),
                "ext": ext,
                "closeloc": closeloc,
                "dist52": dist52,
                "gap": gap,
                "rvol": rvol,
            }
        )

    n_ext = sum(1 for x in enriched_data if x["ext"] is not None)
    print(f"ATR-extension hesaplanabilen satır: {n_ext}/{len(enriched_data)}")

    def decile_report(data, key, label):
        vals = [
            (x[key], x["entry_ok"])
            for x in data
            if x.get(key) is not None and not (isinstance(x[key], float) and x[key] != x[key])
        ]
        if len(vals) < 50:
            print(f"  {label}: yetersiz veri (n={len(vals)})")
            return
        vals.sort(key=lambda t: t[0])
        n = len(vals)
        print(f"  {label} (n={n}) — decile → entry_ok-oranı:")
        dec_rates = []
        for i in range(10):
            lo = i * n // 10
            hi = (i + 1) * n // 10
            chunk = vals[lo:hi]
            if not chunk:
                continue
            rate = 100 * sum(1 for _, ok in chunk if ok) / len(chunk)
            dec_rates.append(rate)
        print("   ", [round(x, 1) for x in dec_rates])

    print("\n=== extension-proxy → entry_ok(eligible)-oranı monoton mu? ===")
    decile_report(enriched_data, "ext", "ATR-extension (20g-getiri/ATR)")
    decile_report(enriched_data, "dist52", "dist_52w_high")
    decile_report(enriched_data, "gap", "gap_pct")
    decile_report(enriched_data, "rvol", "rvol")
    decile_report(enriched_data, "closeloc", "close-location (gün-içi)")

    print("\n=== conviction_tier bazında extension ortalaması ===")
    for tier in ["A", "B", "C"]:
        vals = [x["ext"] for x in enriched_data if x["conviction"] == tier and x["ext"] is not None]
        if vals:
            print(
                f"  tier {tier}: n={len(vals)}  ort-extension={statistics.mean(vals):+.3f}  medyan={statistics.median(vals):+.3f}"
            )
        else:
            print(f"  tier {tier}: n=0")


if __name__ == "__main__":
    main()
