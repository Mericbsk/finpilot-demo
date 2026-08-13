#!/usr/bin/env python3
"""
ranking_score_backfill_test.py — canlı urunun GERCEKTE kullandigi alanin
(`ranking_score`, su anki .env konfigurasyonuyla = `legacy_quality_score`)
geriye-donuk backfill'i + composite_score ile ayni rigor testleri.

`scanner/score_engine.py::compute_legacy_quality_score`'un TAM AYNI formulu
(satir-satir kopyalandi, kaynak degistirilmedi) mevcut export kolonlariyla
(regime, direction, score, atr_pct_real, rvol, squeeze_factor, lottery_factor,
overnight_gap_factor) her satir icin yeniden hesaplaniyor. YENI VERI GEREKMEDI.

Uc test:
  A) legacy_quality_score (proxy) vs composite_score: ne kadar farkli siralama
     uretiyorlar (Spearman, gun-ici)? Eger yuksek-korele iseler, "yanlis alani
     test ettik" kaygisi pratikte kucuk kalir.
  B) legacy_quality_score'un gun-ici rank-korelasyonu c2c_5d ile (composite_score
     icin zaten yapilan test, ayni metodoloji: null-shuffle + blok-bootstrap CI).
  C) Top-N (legacy_quality_score) portfoy testi vs Top-N (composite_score) vs
     rastgele -- gun-kumeli, blok-bootstrap CI.
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
N = 10


def _f(x):
    try:
        v = float(x)
        return None if v != v else v
    except (TypeError, ValueError):
        return None


def _bool(x):
    return str(x).strip().lower() == "true"


def compute_legacy_quality_score(
    regime,
    direction,
    raw_score,
    atr_pct,
    rvol,
    squeeze_factor=None,
    lottery_factor=None,
    overnight_gap_factor=None,
):
    """scanner/score_engine.py:193-222 ile BIREBIR AYNI (kaynak degistirilmedi)."""

    def normalized(value, scale):
        if value is None:
            return 0.0
        return max(0.0, min(1.0, float(value) / scale))

    base = 2.0 * float(regime) + 2.0 * float(direction) + 1.5 * normalized(raw_score, 3.0)
    atr = normalized(atr_pct, 6.0)
    relative_volume = normalized((float(rvol) - 1.0) if rvol is not None else None, 2.0)
    squeeze = max(0.0, min(1.0, float(squeeze_factor or 0.0)))
    lottery = max(0.0, min(1.0, float(lottery_factor or 0.0)))
    overnight = max(0.0, min(1.0, float(overnight_gap_factor or 0.0)))
    return round(
        (base + 1.5 * atr + 1.5 * relative_volume + 0.5 * squeeze - 1.5 * lottery - overnight)
        / 10.0
        * 100.0,
        3,
    )


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
    return num / (dx * dy) if dx and dy else None


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
    valid = []
    n_missing_composite = 0
    for r in rows:
        atr_pct = _f(r.get("atr_pct_real"))
        rvol = _f(r.get("rvol"))
        raw_score = _f(r.get("score"))
        c5 = _f(r.get("c2c_5d"))
        if atr_pct is None or rvol is None or raw_score is None or c5 is None:
            continue
        lqs = compute_legacy_quality_score(
            regime=_bool(r.get("regime")),
            direction=_bool(r.get("direction")),
            raw_score=raw_score,
            atr_pct=atr_pct,
            rvol=rvol,
            squeeze_factor=_f(r.get("squeeze_factor")),
            lottery_factor=_f(r.get("lottery_factor")),
            overnight_gap_factor=_f(r.get("overnight_gap_factor")),
        )
        cs = _f(r.get("composite_score"))
        if cs is None:
            n_missing_composite += 1
        valid.append(
            {"symbol": r["symbol"], "date": r["scan_date"], "lqs": lqs, "cs": cs, "c5": c5}
        )

    print(
        f"[VERI] legacy_quality_score hesaplanabilen satir={len(valid)}  "
        f"bunlarin composite_score'u eksik olan={n_missing_composite} "
        f"({100*n_missing_composite/len(valid):.1f}%)"
    )

    by_date = defaultdict(list)
    for r in valid:
        by_date[r["date"]].append(r)
    print(f"[VERI] gun sayisi={len(by_date)}\n")

    # ---- Test A: legacy_quality_score vs composite_score gun-ici rank-korelasyonu ----
    print("=" * 90)
    print("TEST A: legacy_quality_score (proxy) ile composite_score AYNI SIRALAMAYI mi uretiyor?")
    print("=" * 90)
    both = [r for r in valid if r["cs"] is not None]
    by_date_both = defaultdict(list)
    for r in both:
        by_date_both[r["date"]].append(r)
    daily_agree = []
    for d, grp in sorted(by_date_both.items()):
        if len(grp) < 8:
            continue
        c = rank_corr([r["lqs"] for r in grp], [r["cs"] for r in grp])
        if c is not None:
            daily_agree.append(c)
    if daily_agree:
        m, t, n = naive_t(daily_agree)
        print(
            f"  gun-ici Spearman(legacy_quality_score, composite_score): n_gun={n}  ort-rho={m:+.3f}  t~={t:+.2f}"
        )
        print(
            f"  (composite_score dolu olan {len(both)}/{len(valid)} satirda; digerlerinde composite_score YOK)"
        )

    # ---- Test B: legacy_quality_score gun-ici rank-korelasyonu ile c2c_5d ----
    print("\n" + "=" * 90)
    print(
        "TEST B: legacy_quality_score gun-ici rank-korelasyonu c2c_5d ile (composite_score ile AYNI test)"
    )
    print("=" * 90)
    for label, key in [
        ("legacy_quality_score (proxy=ranking_score)", "lqs"),
        ("composite_score (eski test, referans)", "cs"),
    ]:
        daily_rho, daily_null = [], []
        pool = by_date_both if key == "cs" else by_date
        for d, grp in sorted(pool.items()):
            xs = [r[key] for r in grp if r[key] is not None]
            ys = [r["c5"] for r in grp if r[key] is not None]
            if len(xs) < 8 or len(set(xs)) < 2:
                continue
            c = rank_corr(xs, ys)
            if c is not None:
                daily_rho.append(c)
            ys_s = ys[:]
            RNG.shuffle(ys_s)
            cn = rank_corr(xs, ys_s)
            if cn is not None:
                daily_null.append(cn)
        if len(daily_rho) < 8:
            print(f"  {label:42} YETERSİZ VERİ")
            continue
        m, t, n = naive_t(daily_rho)
        ci = block_bootstrap_ci(daily_rho)
        mn, _, _ = naive_t(daily_null)
        ci_str = f"[{ci[0]:+.4f}, {ci[1]:+.4f}]" if ci else "n/a"
        bonf = abs(t) > 4.56
        print(
            f"  {label:42} n_gün={n:4d}  ort-rho={m:+.4f}  t~={t:+.2f}  boot-CI={ci_str}  null-ort={mn:+.4f}  "
            f"[{'BONFERRONI-HAYATTA' if bonf else ('konvansiyonel|t|>2' if abs(t) > 2 else 'ölü')}]"
        )

    # ---- Test C: top-N portfoy testi ----
    print("\n" + "=" * 90)
    print(
        "TEST C: top-10 gunluk secim -- legacy_quality_score vs composite_score vs rastgele (c2c_5d ort)"
    )
    print("=" * 90)
    series = {"lqs": {}, "cs": {}, "rand": {}}
    for d, grp in sorted(by_date.items()):
        if len(grp) < N:
            continue
        top_lqs = sorted(grp, key=lambda r: r["lqs"], reverse=True)[:N]
        series["lqs"][d] = statistics.mean(r["c5"] for r in top_lqs)
        grp_cs = [r for r in grp if r["cs"] is not None]
        if len(grp_cs) >= N:
            top_cs = sorted(grp_cs, key=lambda r: r["cs"], reverse=True)[:N]
            series["cs"][d] = statistics.mean(r["c5"] for r in top_cs)
        series["rand"][d] = statistics.mean(
            statistics.mean(r["c5"] for r in RNG.sample(grp, N)) for _ in range(1)
        )

    for k, label in [
        ("lqs", "top-10 legacy_quality_score"),
        ("cs", "top-10 composite_score"),
        ("rand", "top-10 rastgele (1-cekilis)"),
    ]:
        vals = list(series[k].values())
        if len(vals) < 5:
            print(f"  {label:32} YETERSİZ")
            continue
        m, t, n = naive_t(vals)
        print(f"  {label:32} n_gün={n:4d}  ort-c2c_5d={m:+.4f}  t~(H0=0)={t:+.2f}")

    def paired(a_key, b_key, label):
        common = sorted(set(series[a_key]) & set(series[b_key]))
        diffs = [series[b_key][d] - series[a_key][d] for d in common]
        if len(diffs) < 5:
            print(f"  {label:42} n=yetersiz")
            return
        m, t, n = naive_t(diffs)
        ci = block_bootstrap_ci(diffs)
        ci_str = f"[{ci[0]:+.4f}, {ci[1]:+.4f}]" if ci else "n/a"
        verdict = "ANLAMLI" if (ci and (ci[0] > 0 or ci[1] < 0)) else "anlamsız"
        print(
            f"  {label:42} n_gün={n:4d}  fark-ort={m:+.4f}  t~={t:+.2f}  boot-CI={ci_str}  [{verdict}]"
        )

    print()
    paired("rand", "lqs", "legacy_quality_score - rastgele")
    paired("rand", "cs", "composite_score - rastgele (referans)")
    paired("cs", "lqs", "legacy_quality_score - composite_score")


if __name__ == "__main__":
    main()
