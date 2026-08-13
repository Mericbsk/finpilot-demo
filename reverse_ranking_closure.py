#!/usr/bin/env python3
"""
reverse_ranking_closure.py — Reverse-ranking bulgusunu KAPAT.

Düzeltmeler (önceki turların eksikleri):
  1) DEDUP: full_universe_enriched.csv'de aynı (symbol,scan_date) için EN ERKEN
     scan_ts satırı tutulur (composite_score/finpilot_score oradan alınır) —
     scanner saatlik ateşlendiği için aynı gün 2-17 tekrar vardı (%48 çift).
  2) MATCHED-RANDOM KONTROL: her gün o günün adaylarından gerçek rastgele-%20
     (birkaç seed), ALT/ÜST-%20 ile aynı ölçekte kıyaslanır.
  3) ÇEYREKLİK PENCERELER: tek IS/OOS ayrımı yerine 4 zaman-bloğu, her biri
     gün-kümeli (cluster-robust) test edilir — tek-OOS-penceresi kırılganlığını azaltır.

Karar: her çeyrekte VE toplamda ALT-%20 tutarlı+anlamlı üstünlük göstermezse
bulgu resmi olarak ARTEFAKT sayılır ve kapatılır.
"""

from __future__ import annotations

import csv
import math
import random
import statistics
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def dedup_scores():
    """(symbol, scan_date) -> en-erken-scan_ts satırının composite_score, finpilot_score."""
    best = {}
    for r in csv.DictReader(open("data/backtest_out/full_universe_enriched.csv")):
        s, d, ts = r["symbol"], str(r["scan_date"]), r.get("scan_ts", "")
        k = (s, d)
        if k not in best or ts < best[k][0]:
            try:
                sc = float(r["composite_score"])
            except (ValueError, KeyError, TypeError):
                sc = None
            best[k] = (ts, sc)
    return {k: v[1] for k, v in best.items() if v[1] is not None}


def load_dedup():
    scores = dedup_scores()
    outcomes = {}
    for r in csv.DictReader(open("data/backtest_out/edge_recheck.csv")):
        k = (r["symbol"], r["scan_date"])
        if k in outcomes:
            continue  # ilk-görülen yeterli (outcome dup'lar arası aynı)
        try:
            c2c = float(r["c2c5_net"])
        except (ValueError, KeyError):
            continue
        outcomes[k] = c2c

    rows = []
    for k, sc in scores.items():
        if k in outcomes:
            rows.append({"symbol": k[0], "scan_date": k[1], "_sc": sc, "_c2c": outcomes[k]})
    return rows


def daily_groups(rows):
    by_date = {}
    for r in rows:
        by_date.setdefault(r["scan_date"], []).append(r)
    return by_date


def day_selection_means(by_date, frac, mode, seed=0):
    """mode: 'top' | 'bottom' | 'random'. Gün başına (ortalama, n) döndürür."""
    rnd = random.Random(seed)
    out = {}
    for d, grp in by_date.items():
        if len(grp) < 10:
            continue
        n = max(1, int(len(grp) * frac))
        if mode == "top":
            sel = sorted(grp, key=lambda r: r["_sc"], reverse=True)[:n]
        elif mode == "bottom":
            sel = sorted(grp, key=lambda r: r["_sc"])[:n]
        else:
            sel = rnd.sample(grp, n)
        out[d] = (statistics.mean(r["_c2c"] for r in sel), n)
    return out


def cluster_stats(daily, label):
    vals = [v for v, n in daily.values()]
    n = len(vals)
    if n < 5:
        print(f"    {label:26} n_gün={n} yetersiz")
        return None
    m = statistics.mean(vals)
    med = statistics.median(vals)
    sd = statistics.pstdev(vals) if n > 1 else 0
    se = sd / math.sqrt(n) if n else float("nan")
    t = m / se if se else float("nan")
    print(
        f"    {label:26} n_gün={n:4d}  ort={m:+7.3f}  medyan={med:+7.3f}  SE={se:6.3f}  t~={t:+.2f}"
    )
    return m


def paired_stats(a, b, label):
    common = set(a) & set(b)
    diffs = [a[d][0] - b[d][0] for d in common]
    if len(diffs) < 5:
        print(f"    {label:26} n=yetersiz")
        return
    m = statistics.mean(diffs)
    sd = statistics.pstdev(diffs) if len(diffs) > 1 else 0
    se = sd / math.sqrt(len(diffs)) if diffs else float("nan")
    t = m / se if se else float("nan")
    verdict = "✅ anlamlı" if abs(t) > 2 else "✗ anlamsız"
    print(
        f"    {label:26} n_gün={len(diffs):4d}  ort-fark={m:+.3f}  SE={se:.3f}  t~={t:+.2f}  {verdict}"
    )


def main():
    rows = load_dedup()
    print(
        f"DEDUP SONRASI: {len(rows)} benzersiz (symbol,scan_date) satırı (önceki: 53.754 ham satır)"
    )
    dates = sorted({r["scan_date"] for r in rows})
    print(f"tarih aralığı: {dates[0]} .. {dates[-1]}  ({len(dates)} işlem-günü)")

    # 4 çeyreklik blok
    q = len(dates) // 4
    blocks = {
        "Q1": dates[:q],
        "Q2": dates[q : 2 * q],
        "Q3": dates[2 * q : 3 * q],
        "Q4": dates[3 * q :],
    }

    print("\n" + "=" * 78)
    print("ÇEYREKLİK-PENCERE + MATCHED-RANDOM KONTROL (dedup'lu, gün-kümeli)")
    print("=" * 78)
    verdicts = []
    for name, dblock in blocks.items():
        sub = [r for r in rows if r["scan_date"] in set(dblock)]
        by_date = daily_groups(sub)
        print(
            f"\n-- {name} ({dblock[0] if dblock else '-'}..{dblock[-1] if dblock else '-'}, {len(dblock)} gün) --"
        )
        top = day_selection_means(by_date, 0.20, "top")
        bot = day_selection_means(by_date, 0.20, "bottom")
        rnd1 = day_selection_means(by_date, 0.20, "random", seed=1)
        rnd2 = day_selection_means(by_date, 0.20, "random", seed=2)
        cluster_stats(top, "ÜST-%20")
        cluster_stats(bot, "ALT-%20 (reverse)")
        cluster_stats(rnd1, "RANDOM-%20 (seed1)")
        cluster_stats(rnd2, "RANDOM-%20 (seed2)")
        paired_stats(bot, top, "ALT vs ÜST (fark)")
        paired_stats(bot, rnd1, "ALT vs RANDOM1 (fark)")
        paired_stats(bot, rnd2, "ALT vs RANDOM2 (fark)")

    print("\n" + "=" * 78)
    print("TAM DÖNEM (dedup'lu, gün-kümeli)")
    print("=" * 78)
    by_date_all = daily_groups(rows)
    top = day_selection_means(by_date_all, 0.20, "top")
    bot = day_selection_means(by_date_all, 0.20, "bottom")
    rnd1 = day_selection_means(by_date_all, 0.20, "random", seed=1)
    rnd2 = day_selection_means(by_date_all, 0.20, "random", seed=2)
    rnd3 = day_selection_means(by_date_all, 0.20, "random", seed=3)
    cluster_stats(top, "ÜST-%20")
    cluster_stats(bot, "ALT-%20 (reverse)")
    cluster_stats(rnd1, "RANDOM-%20 (seed1)")
    cluster_stats(rnd2, "RANDOM-%20 (seed2)")
    cluster_stats(rnd3, "RANDOM-%20 (seed3)")
    paired_stats(bot, top, "ALT vs ÜST (fark)")
    paired_stats(bot, rnd1, "ALT vs RANDOM1 (fark)")
    paired_stats(bot, rnd2, "ALT vs RANDOM2 (fark)")
    paired_stats(bot, rnd3, "ALT vs RANDOM3 (fark)")


if __name__ == "__main__":
    main()
