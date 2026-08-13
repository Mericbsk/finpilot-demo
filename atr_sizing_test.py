#!/usr/bin/env python3
"""
atr_sizing_test.py — Deney #8: ATR-bazlı (ters-orantılı) position-sizing testi.

concentration_portfolio_test.py'nin genişletilmiş hali: eşit-ağırlık yerine
1/ATR ağırlıklandırma (yüksek-ATR isimlere daha küçük pozisyon), kısıtlı/kısıtsız
kombinasyonlarıyla.
"""

from __future__ import annotations

import csv
import statistics
import sys
from collections import Counter

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

N = 10
MAXK = 3


def main():
    sec = {
        r["symbol"]: r["etf"]
        for r in csv.DictReader(open("data/backtest_out/sector_map_full.csv"))
        if r["etf"]
    }
    rows = list(csv.DictReader(open("data/backtest_out/edge_recheck.csv")))
    for r in rows:
        try:
            r["_c2c"] = float(r["c2c5_net"])
            r["_sc"] = float(r["composite_score"])
            r["_atr"] = float(r["atr_pct"])
        except (ValueError, KeyError):
            r["_c2c"] = r["_sc"] = r["_atr"] = None
        r["_sec"] = sec.get(r["symbol"], "UNK")

    by_date = {}
    for r in rows:
        if r["_c2c"] is None or r["_sc"] is None or r["_atr"] is None or r["_atr"] <= 0:
            continue
        by_date.setdefault(r["scan_date"], []).append(r)

    variants = {
        "kısıtsız+eşit-ağırlık": [],
        "kısıtsız+ATR-ters-ağırlık": [],
        "kısıtlı+eşit-ağırlık": [],
        "kısıtlı+ATR-ters-ağırlık": [],
    }
    conc = {k: [] for k in variants}

    for d, grp in sorted(by_date.items()):
        if len(grp) < N:
            continue
        grp_sorted = sorted(grp, key=lambda r: r["_sc"], reverse=True)

        unc = grp_sorted[:N]
        con, sec_count = [], {}
        for r in grp_sorted:
            s = r["_sec"]
            if sec_count.get(s, 0) >= MAXK:
                continue
            con.append(r)
            sec_count[s] = sec_count.get(s, 0) + 1
            if len(con) >= N:
                break
        if len(con) < N:
            con = None

        def eq_ret(picks):
            return statistics.mean(r["_c2c"] for r in picks)

        def atr_ret(picks):
            w = [1.0 / r["_atr"] for r in picks]
            tw = sum(w)
            return sum(wi * r["_c2c"] for wi, r in zip(w, picks, strict=False)) / tw

        def conc_share(picks):
            cnt = Counter(r["_sec"] for r in picks)
            return max(cnt.values()) / len(picks)

        variants["kısıtsız+eşit-ağırlık"].append(eq_ret(unc))
        conc["kısıtsız+eşit-ağırlık"].append(conc_share(unc))
        variants["kısıtsız+ATR-ters-ağırlık"].append(atr_ret(unc))
        conc["kısıtsız+ATR-ters-ağırlık"].append(conc_share(unc))
        if con:
            variants["kısıtlı+eşit-ağırlık"].append(eq_ret(con))
            conc["kısıtlı+eşit-ağırlık"].append(conc_share(con))
            variants["kısıtlı+ATR-ters-ağırlık"].append(atr_ret(con))
            conc["kısıtlı+ATR-ters-ağırlık"].append(conc_share(con))

    def report(daily, cshare, label):
        n = len(daily)
        if n < 5:
            print(f"{label:32} n=yetersiz({n})")
            return
        mean = statistics.mean(daily)
        std = statistics.pstdev(daily) if n > 1 else 0
        sharpe = mean / std if std else float("nan")
        srt = sorted(daily)
        cvar5 = statistics.mean(srt[: max(1, int(n * 0.05))])
        cum = peak = maxdd = 0.0
        for v in daily:
            cum += v
            peak = max(peak, cum)
            maxdd = min(maxdd, cum - peak)
        avgc = statistics.mean(cshare) if cshare else float("nan")
        print(
            f"{label:32} n={n:4d}  ort={mean:+.4f}  std={std:.4f}  sharpe~={sharpe:+.3f}  "
            f"CVaR5%={cvar5:+.4f}  maxDD={maxdd:+.3f}  konsantrasyon={avgc:.1%}"
        )

    print(f"=== ATR-bazlı sizing testi (top-{N}, kısıt max {MAXK}/sektör) ===")
    for k in [
        "kısıtsız+eşit-ağırlık",
        "kısıtsız+ATR-ters-ağırlık",
        "kısıtlı+eşit-ağırlık",
        "kısıtlı+ATR-ters-ağırlık",
    ]:
        report(variants[k], conc[k], k)


if __name__ == "__main__":
    main()
