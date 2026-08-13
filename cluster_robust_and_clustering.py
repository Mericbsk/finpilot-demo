#!/usr/bin/env python3
"""
cluster_robust_and_clustering.py — Deney #10 + #19:
(A) Reverse-ranking bulgusunu GÜN-SEVİYESİNDE kümeleyip (cluster-robust) yeniden test et
    — satır-bazlı naif CI yerine gün-bazlı ortalama + gün-sayısı üzerinden t-testi.
(B) Aynı-gün top-N seçimlerinin ne kadar "aynı hareketi" yakaladığını (within-day
    dispersion vs between-day dispersion) ölç — kümelenme riskinin doğrudan kanıtı.
"""

from __future__ import annotations

import csv
import math
import statistics
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def load():
    rows = list(csv.DictReader(open("data/backtest_out/edge_recheck.csv")))
    for r in rows:
        try:
            r["_c2c"] = float(r["c2c5_net"])
            r["_sc"] = float(r["composite_score"])
        except (ValueError, KeyError):
            r["_c2c"] = None
            r["_sc"] = None
    return [r for r in rows if r["_c2c"] is not None and r["_sc"] is not None]


def daily_topk(rows, frac, reverse):
    by_date = {}
    for r in rows:
        by_date.setdefault(r["scan_date"], []).append(r)
    daily_means = {}
    for d, grp in by_date.items():
        valid = sorted(grp, key=lambda r: r["_sc"], reverse=reverse)
        n = max(1, int(len(valid) * frac))
        sel = valid[:n]
        if len(sel) >= 2:
            daily_means[d] = (statistics.mean(r["_c2c"] for r in sel), len(sel))
    return daily_means


def cluster_ttest(daily_means, label):
    vals = [v for v, n in daily_means.values()]
    n_days = len(vals)
    if n_days < 5:
        print(f"  {label}: n_gün={n_days} yetersiz")
        return
    m = statistics.mean(vals)
    sd = statistics.pstdev(vals) if n_days > 1 else 0
    se = sd / math.sqrt(n_days) if n_days > 0 else float("nan")
    t = m / se if se else float("nan")
    print(
        f"  {label:30} n_gün={n_days:4d}  gün-ort-medRet={statistics.median(vals):+.3f}  gün-ort-meanRet={m:+.3f}  SE={se:.3f}  t~={t:+.2f}"
    )


def deney_a_cluster_robust():
    print("=" * 70)
    print("(A) CLUSTER-ROBUST: composite_score reverse-ranking, GÜN-SEVİYESİNDE")
    print("=" * 70)
    rows = load()
    dates = sorted({r["scan_date"] for r in rows})
    cut = dates[len(dates) // 2]

    for name, sub in [
        ("IS", [r for r in rows if r["scan_date"] < cut]),
        ("OOS", [r for r in rows if r["scan_date"] >= cut]),
    ]:
        print(f"\n-- {name} --")
        baseline_daily = daily_topk(sub, 1.0, False)  # tüm gün ortalaması (frac=1.0 -> hepsi)
        top20_daily = daily_topk(sub, 0.20, True)
        bot20_daily = daily_topk(sub, 0.20, False)
        cluster_ttest(baseline_daily, "baseline (gün-ort, tüm)")
        cluster_ttest(top20_daily, "ÜST-%20 (gün-ort)")
        cluster_ttest(bot20_daily, "ALT-%20 REVERSE (gün-ort)")

        # ALT-%20 vs ÜST-%20 farkının gün-bazlı paired t-testi
        common_dates = set(top20_daily) & set(bot20_daily)
        diffs = [bot20_daily[d][0] - top20_daily[d][0] for d in common_dates]
        if len(diffs) >= 5:
            m = statistics.mean(diffs)
            sd = statistics.pstdev(diffs) if len(diffs) > 1 else 0
            se = sd / math.sqrt(len(diffs)) if len(diffs) else float("nan")
            t = m / se if se else float("nan")
            print(
                f"  PAIRED (ALT-üst fark)         n_gün={len(diffs):4d}  ort-fark={m:+.3f}  SE={se:.3f}  t~={t:+.2f}"
            )


def deney_b_clustering():
    print("\n" + "=" * 70)
    print("(B) AYNI-GÜN KÜMELENME: within-day vs between-day dispersion")
    print("=" * 70)
    rows = load()
    by_date = {}
    for r in rows:
        by_date.setdefault(r["scan_date"], []).append(r["_c2c"])

    within_vars, day_means = [], []
    for d, vals in by_date.items():
        if len(vals) < 5:
            continue
        day_means.append(statistics.mean(vals))
        within_vars.append(statistics.pvariance(vals))

    between_var = statistics.pvariance(day_means) if len(day_means) > 1 else 0
    mean_within_var = statistics.mean(within_vars) if within_vars else float("nan")
    total_var = mean_within_var + between_var
    icc = between_var / total_var if total_var else float("nan")

    print(f"  gün sayısı (n>=5 sinyalli): {len(day_means)}")
    print(f"  between-day varyans (günler-arası): {between_var:.4f}")
    print(f"  ort within-day varyans (gün-içi):   {mean_within_var:.4f}")
    print(f"  ICC (intra-class correlation, günün payı): {icc:.3f}")
    print("  → ICC yüksekse (örn >0.1-0.2), aynı-gün sinyalleri BİRBİRİNE BENZER hareket ediyor")
    print("    (ortak gün-etkisi/piyasa-beta baskın) — bağımsız-N varsayımı ihlalli, CI'lar")
    print("    naif-satır-bazlı hesaplanırsa OLDUĞUNDAN DAR (yanlış-güvenli) çıkar.")

    # top-N seçimlerinde günlük en-yoğun-sektör-payı zaten concentration_portfolio_test.py'de
    # ölçülmüştü (~%62) — burada ayrıca teyit: kaç farklı sembol aynı günde tekrar seçiliyor mu?
    sym_by_date = {}
    for r in rows:
        sym_by_date.setdefault(r["scan_date"], set()).add(r["symbol"])
    avg_unique = statistics.mean(len(s) for s in sym_by_date.values())
    avg_total = statistics.mean(len(by_date[d]) for d in by_date if d in sym_by_date)
    print(
        f"\n  ort. günlük benzersiz-sembol: {avg_unique:.1f}  vs  ort. günlük toplam-satır: {avg_total:.1f}"
    )


if __name__ == "__main__":
    deney_a_cluster_robust()
    deney_b_clustering()
