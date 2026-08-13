#!/usr/bin/env python3
"""
concentration_portfolio_test.py — Concentration-kısıtlı vs kısıtsız portföy (yaklaşık).

Basitleştirme (açıkça etiketli): her scan_date için top-N adayın c2c5_net'inin
eşit-ağırlıklı ortalaması o günün "portföy günlük getirisi" sayılır (pozisyon
üst-üste-binmesi/gerçek-equity-eğrisi modellenmiyor — tam backtest motoru değil,
concentration'ın GÖRECELİ etkisini görmek için yeterli bir yaklaşıklama).

Kısıtsız: top-N composite_score.
Kısıtlı: top-N composite_score, max K/sektör (fazlaysa bir sonraki-en-iyi farklı-sektör
sembolüyle değiştirilir).
"""

from __future__ import annotations

import csv
import statistics
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

N = 10  # günlük top-N
MAXK = 3  # sektör başına maksimum


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
        except (ValueError, KeyError):
            r["_c2c"] = None
            r["_sc"] = None
        r["_sec"] = sec.get(r["symbol"], "UNK")

    by_date = {}
    for r in rows:
        if r["_c2c"] is None or r["_sc"] is None:
            continue
        by_date.setdefault(r["scan_date"], []).append(r)

    unconstrained_daily, constrained_daily = [], []
    unc_conc, con_conc = [], []  # en-yoğun-sektörün-payı, gün başına

    for d, grp in sorted(by_date.items()):
        if len(grp) < N:
            continue
        grp_sorted = sorted(grp, key=lambda r: r["_sc"], reverse=True)

        # Kısıtsız top-N
        unc = grp_sorted[:N]
        unc_ret = statistics.mean(r["_c2c"] for r in unc)
        unconstrained_daily.append(unc_ret)
        from collections import Counter

        cnt = Counter(r["_sec"] for r in unc)
        unc_conc.append(max(cnt.values()) / N)

        # Kısıtlı: max MAXK/sektör
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
            continue
        con_ret = statistics.mean(r["_c2c"] for r in con)
        constrained_daily.append(con_ret)
        cnt2 = Counter(r["_sec"] for r in con)
        con_conc.append(max(cnt2.values()) / N)

    def report(daily, conc, label):
        n = len(daily)
        mean = statistics.mean(daily)
        std = statistics.pstdev(daily) if n > 1 else 0
        sharpe_like = mean / std if std else float("nan")
        srt = sorted(daily)
        cvar5 = statistics.mean(srt[: max(1, int(n * 0.05))])
        cum = 0.0
        peak = 0.0
        maxdd = 0.0
        for v in daily:
            cum += v
            peak = max(peak, cum)
            maxdd = min(maxdd, cum - peak)
        avg_conc = statistics.mean(conc) if conc else float("nan")
        print(
            f"{label:28} n_gün={n:5d}  günlük-ort={mean:+.4f}  std={std:.4f}  "
            f"sharpe~={sharpe_like:+.3f}  CVaR5%={cvar5:+.4f}  maxDD(kümülatif)={maxdd:+.3f}  "
            f"ort-en-yoğun-sektör-payı={avg_conc:.2%}"
        )

    print(
        f"=== Portföy karşılaştırması (top-{N}, kısıt: max {MAXK}/sektör) — yaklaşık, günlük-eşit-ağırlık ==="
    )
    report(unconstrained_daily, unc_conc, "KISITSIZ (top-N composite)")
    report(constrained_daily, con_conc, "KISITLI (max/sektör)")


if __name__ == "__main__":
    main()
