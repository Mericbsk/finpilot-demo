#!/usr/bin/env python3
"""
Full Baseline Reconstruction + Ranking Compression Forensics -- PART B.

Agirlik denemesi YOK, yeni feature YOK. Sadece mevcut composite_score'un
neden bu kadar tie/sikismis oldugunu olcuyor -- EOD-only (temiz) veri
uzerinde, dedup sonrasi.
"""

from __future__ import annotations

import csv
import statistics
from collections import Counter, defaultdict

SRC = "data/backtest_out/full_universe_enriched_eod_only.csv"


def load_dedup_rows():
    best = {}
    with open(SRC, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            k = (r["symbol"], r["scan_date"])
            ts = r.get("scan_ts", "")
            if k not in best or ts < best[k][0]:
                best[k] = (ts, r)
    return [r for _, r in best.values()]


def f(x):
    try:
        v = float(x)
        return None if v != v else v
    except (TypeError, ValueError):
        return None


def main():
    rows = load_dedup_rows()
    cs = [(r["scan_date"], f(r.get("composite_score"))) for r in rows]
    cs = [(d, v) for d, v in cs if v is not None]
    print(f"[VERI] EOD-only dedup satir (composite_score dolu) = {len(cs)}")

    # B.1a -- global tekillik/tie
    vals = [v for _, v in cs]
    uniq = len(set(vals))
    print(
        f"\n[B.1a] Benzersiz composite_score degeri: {uniq} / {len(vals)} satir "
        f"(tie orani = {100*(1 - uniq/len(vals)):.2f}%)"
    )
    cnt = Counter(vals)
    top5 = cnt.most_common(5)
    print(f"  En sik 5 deger: {top5}")

    # B.1b -- gun-ici etkin rank cozunurlugu
    by_day = defaultdict(list)
    for d, v in cs:
        by_day[d].append(v)
    day_ratios = []
    for _d, vs in by_day.items():
        if len(vs) < 5:
            continue
        u = len(set(vs))
        day_ratios.append(u / len(vs))
    if day_ratios:
        print(f"\n[B.1b] Gun-ici etkin rank cozunurlugu (n_gun={len(day_ratios)}):")
        print(
            f"  ortalama = {statistics.mean(day_ratios)*100:.2f}%  "
            f"medyan = {statistics.median(day_ratios)*100:.2f}%  "
            f"min = {min(day_ratios)*100:.2f}%  max = {max(day_ratios)*100:.2f}%"
        )

    # B.1c -- deger histogrami (0-100 araliginda mi, hangi bolgede yogun)
    buckets = Counter()
    for v in vals:
        b = int(v // 2) * 2  # 2-birimlik kovalar
        buckets[b] += 1
    print("\n[B.1c] 2-birimlik kovalarda dagilim (en yogun 8):")
    for b, n in sorted(buckets.items(), key=lambda x: -x[1])[:8]:
        print(f"  [{b:>4},{b+2:>4}): {n:>6}  ({100*n/len(vals):.1f}%)")

    # B.1d -- "score" (raw, 0-3 beklenen) ve "tier_score" gibi diger mevcut
    # sikismaya-katkida-bulunabilecek kolonlarin kendi tekillikleri
    for col in ["score", "tier_score", "finpilot_score", "risk_reward"]:
        cvals = [f(r.get(col)) for r in rows]
        cvals = [v for v in cvals if v is not None]
        if not cvals:
            continue
        print(
            f"\n[B.1d] {col}: benzersiz={len(set(cvals))}/{len(cvals)} "
            f"(tie={100*(1-len(set(cvals))/len(cvals)):.2f}%)  "
            f"min={min(cvals):.2f} max={max(cvals):.2f}"
        )


if __name__ == "__main__":
    main()
