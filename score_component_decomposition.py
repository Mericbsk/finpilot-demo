#!/usr/bin/env python3
"""
score_component_decomposition.py — Soru 7 (red-team raporu): composite score'un tek
sayida karistirdigi bilesenlerden HANGISI gercekten ileri-bilgi tasiyor?

lottery_gap_reweight_test.py'deki ayni metodoloji (Fama-MacBeth gun-ici rank-korelasyon
+ null-shuffle kontrol + blok-bootstrap CI), full_universe_enriched.csv'deki TUM
numerik score-bilesenlerine tek-tek uygulanir. Ek veri gerektirmez (mevcut export).

Bilesenler: score, composite_score, finpilot_score, squeeze_factor, catalyst_factor,
lottery_factor (referans-tekrar), overnight_gap_factor (referans-tekrar), sentiment,
atr, atr_pct_real, rvol, gap_pct, dist_52w_high, risk_reward, tier_score.
"""

from __future__ import annotations

import csv
import math
import random
import statistics
import sys
from collections import defaultdict

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BLOCK = 5
BOOT_B = 5000
RNG = random.Random(2026)

COMPONENTS = [
    "score",
    "composite_score",
    "finpilot_score",
    "squeeze_factor",
    "catalyst_factor",
    "lottery_factor",
    "overnight_gap_factor",
    "sentiment",
    "atr",
    "atr_pct_real",
    "rvol",
    "gap_pct",
    "dist_52w_high",
    "risk_reward",
    "tier_score",
]


def _f(x):
    try:
        v = float(x)
        if v != v:  # NaN
            return None
        return v
    except (TypeError, ValueError):
        return None


def load_dedup_rows():
    best = {}
    with open("data/backtest_out/full_universe_enriched.csv") as f:
        for r in csv.DictReader(f):
            k = (r["symbol"], r["scan_date"])
            ts = r.get("scan_ts", "")
            if k not in best or ts < best[k][0]:
                best[k] = (ts, r)
    return [r for _, r in best.values()]


def rank_corr(xs, ys):
    n = len(xs)
    if n < 4:
        return None

    def ranks(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                j += 1
            avg_rank = (i + j) / 2.0 + 1
            for k in range(i, j + 1):
                r[order[k]] = avg_rank
            i = j + 1
        return r

    rx, ry = ranks(xs), ranks(ys)
    mx, my = statistics.mean(rx), statistics.mean(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry, strict=False))
    dx = math.sqrt(sum((a - mx) ** 2 for a in rx))
    dy = math.sqrt(sum((b - my) ** 2 for b in ry))
    if dx == 0 or dy == 0:
        return None
    return num / (dx * dy)


def block_bootstrap_ci(vals, block=BLOCK, B=BOOT_B, rng=None):
    rng = rng or RNG
    n = len(vals)
    if n < block + 1:
        return None
    nb = math.ceil(n / block)
    means = []
    for _ in range(B):
        s = []
        for _ in range(nb):
            start = rng.randrange(0, n - block + 1)
            s.extend(vals[start : start + block])
        means.append(statistics.mean(s[:n]))
    means.sort()
    return means[int(0.025 * B)], means[int(0.975 * B)]


def naive_t(vals):
    n = len(vals)
    if n < 2:
        return float("nan"), float("nan"), n
    m = statistics.mean(vals)
    sd = statistics.pstdev(vals)
    se = sd / math.sqrt(n) if sd else 0.0
    return m, (m / se if se else float("nan")), n


def main():
    rows = load_dedup_rows()
    by_date = defaultdict(list)
    c5_ok = 0
    for r in rows:
        c5 = _f(r.get("c2c_5d"))
        if c5 is None:
            continue
        c5_ok += 1
        by_date[r["scan_date"]].append(r)
    print(f"[VERI] dedup satir (c2c_5d dolu)={c5_ok}  gun={len(by_date)}")
    print("[ESIK] Bonferroni m~9754: |t|>4.56 (rapor Soru-10 ile aynı global esik)\n")

    print(
        f"{'bileşen':22} {'n_gün':>6} {'ort-rho':>9} {'naive-t':>9} {'boot-CI':>22} {'null-ort':>9}  {'sonuç'}"
    )
    print("-" * 100)

    results = []
    for comp in COMPONENTS:
        daily_rho, daily_null = [], []
        for d, grp in sorted(by_date.items()):
            xs, ys = [], []
            for r in grp:
                cv = _f(r.get(comp))
                c5 = _f(r.get("c2c_5d"))
                if cv is None or c5 is None:
                    continue
                xs.append(cv)
                ys.append(c5)
            if len(xs) < 8 or len(set(xs)) < 2:
                continue
            c = rank_corr(xs, ys)
            if c is not None:
                daily_rho.append(c)
            ys_shuf = ys[:]
            RNG.shuffle(ys_shuf)
            cn = rank_corr(xs, ys_shuf)
            if cn is not None:
                daily_null.append(cn)

        if len(daily_rho) < 8:
            print(f"{comp:22} {'—':>6} {'YETERSİZ VERİ (n_gün<8)':>45}")
            continue

        m, t, n = naive_t(daily_rho)
        ci = block_bootstrap_ci(daily_rho)
        mn, _, _ = naive_t(daily_null)
        ci_str = f"[{ci[0]:+.4f}, {ci[1]:+.4f}]" if ci else "n/a"
        survives_conv = ci is not None and (ci[0] > 0 or ci[1] < 0)
        survives_bonf = abs(t) > 4.56
        verdict = (
            "HAYATTA (Bonferroni)"
            if survives_bonf
            else "hayatta (konvansiyonel |t|>2 ama Bonferroni'de DEĞİL"
            if abs(t) > 2
            else "ölü"
        )
        print(f"{comp:22} {n:>6} {m:>+9.4f} {t:>+9.2f} {ci_str:>22} {mn:>+9.4f}  {verdict}")
        results.append((comp, n, m, t, ci, survives_conv, survives_bonf))

    print("\n" + "=" * 100)
    print("ÖZET (Soru 7 + Soru 10 kesişimi)")
    print("=" * 100)
    bonf_survivors = [r for r in results if r[6]]
    conv_survivors = [r for r in results if r[5] and not r[6]]
    dead = [r for r in results if not r[5]]
    print(f"Bonferroni-hayatta-kalan (|t|>4.56): {[r[0] for r in bonf_survivors]}")
    print(f"Sadece-konvansiyonel-hayatta (|t|>2 ama <4.56): {[r[0] for r in conv_survivors]}")
    print(f"Ölü/anlamsız (CI 0'ı içeriyor): {[r[0] for r in dead]}")


if __name__ == "__main__":
    main()
