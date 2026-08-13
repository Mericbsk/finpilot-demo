#!/usr/bin/env python3
"""
lottery_gap_reweight_test.py — Item 2: lottery_factor + overnight_gap_factor'u
gercek bir alternatif-score'a cevirip, ayni rigor-suzgecinden (dedup, gun-kumeli,
blok-bootstrap CI, matched-random kontrol) gecir.

Semantik dogrulama (kaynak kod, scanner/features.py):
  compute_lottery_factor: "Higher score = more lottery-like = stronger FADE
  expectation" -> yuksek deger = beklenen ZAYIF ileri-getiri.
  compute_overnight_gap_factor: "overnight-gap REVERSAL PRESSURE" -> yuksek
  deger = beklenen reversal (fade) basinci.
Bu yuzden alt_score, bu iki alani NEGATIF agirlikla kullanir (yuksek
lottery/gap = daha kotu sira).

Test tasarimi:
  1. full_universe_enriched.csv dedup (en-erken scan_ts).
  2. lottery_factor, overnight_gap_factor, composite_score, c2c_5d hepsi
     dolu olan satirlar (n_gun, n_satir raporlanir).
  3. Fama-MacBeth tarzi: her gun ayri ayri Spearman-benzeri rank-korelasyon
     (lottery_factor vs c2c_5d, overnight_gap_factor vs c2c_5d), sonra
     gunler-arasi ortalama + blok-bootstrap CI + NULL kontrolu (o gun icinde
     c2c_5d'yi karistir, korelasyonu yeniden hesapla -- gercek korelasyon
     null dagilimin disinda mi?).
  4. Portfoy testi: her gun top-N SEC (a) orijinal composite_score ile,
     (b) alt_score = zscore(composite_score) - w*zscore(lottery_factor) -
     w*zscore(overnight_gap_factor) ile, (c) matched-random N ile.
     Gunluk ortalama c2c_5d, gun-kumeli + blok-bootstrap CI + ortusmeyen-
     alt-orneklem karsilastirmasi.
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

N = 10
BLOCK = 5
BOOT_B = 5000
RAND_DRAWS = 200
RNG = random.Random(2026)


def _f(x):
    try:
        return float(x)
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
    """Basit Spearman: rank(x) ile rank(y) arasi Pearson."""
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
    return means[int(0.025 * B)], means[int(0.975 * B)], statistics.mean(means)


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
    for r in rows:
        lot, gap, sc, c5 = (
            _f(r.get("lottery_factor")),
            _f(r.get("overnight_gap_factor")),
            _f(r.get("composite_score")),
            _f(r.get("c2c_5d")),
        )
        if None in (lot, gap, sc, c5):
            continue
        valid.append(
            {
                "symbol": r["symbol"],
                "date": r["scan_date"],
                "lot": lot,
                "gap": gap,
                "sc": sc,
                "c5": c5,
            }
        )

    by_date = defaultdict(list)
    for r in valid:
        by_date[r["date"]].append(r)
    print(
        f"[VERI] dedup + tum-alanlar-dolu satir={len(valid)}  gun={len(by_date)}  "
        f"tarih={min(by_date) if by_date else '-'}..{max(by_date) if by_date else '-'}"
    )

    print("\n" + "=" * 90)
    print("ADIM 1 -- FAMA-MACBETH: gun-ici rank-korelasyon(lottery/gap, c2c_5d), NULL-kontrollu")
    print("=" * 90)
    for feat in ["lot", "gap"]:
        daily_corr, daily_null = [], []
        for d, grp in sorted(by_date.items()):
            if len(grp) < 8:
                continue
            xs = [r[feat] for r in grp]
            ys = [r["c5"] for r in grp]
            c = rank_corr(xs, ys)
            if c is not None:
                daily_corr.append(c)
            ys_shuf = ys[:]
            RNG.shuffle(ys_shuf)
            cn = rank_corr(xs, ys_shuf)
            if cn is not None:
                daily_null.append(cn)
        m, t, n = naive_t(daily_corr)
        ci = block_bootstrap_ci(daily_corr)
        mn, tn, nn = naive_t(daily_null)
        ci_str = f"[{ci[0]:+.3f}, {ci[1]:+.3f}]" if ci else "n/a"
        verdict = "ANLAMLI (0'i icermiyor)" if (ci and (ci[0] > 0 or ci[1] < 0)) else "anlamsiz"
        print(
            f"  {feat:5} gercek: n_gun={n:3d} ort-rho={m:+.4f} t~={t:+.2f} boot-CI={ci_str} [{verdict}]"
        )
        print(
            f"  {feat:5} null(karistirilmis-c5): n_gun={nn:3d} ort-rho={mn:+.4f} t~={tn:+.2f}  (referans: 0 civari beklenir)"
        )

    print("\n" + "=" * 90)
    print("ADIM 2 -- PORTFOY TESTI: composite_score vs alt_score(lottery+gap-cezali) vs rastgele")
    print("=" * 90)

    # z-score gunluk (cross-sectional) -- gun-ici standardize, boylece gunler-arasi olcek farki karismasin
    def zscore_day(grp, key):
        vals = [r[key] for r in grp]
        m = statistics.mean(vals)
        sd = statistics.pstdev(vals) if len(vals) > 1 else 1.0
        sd = sd or 1.0
        return {id(r): (r[key] - m) / sd for r in grp}

    W = 1.0
    series = {"orig": {}, "alt": {}, "rand": {}}
    for d, grp in sorted(by_date.items()):
        if len(grp) < N:
            continue
        z_sc = zscore_day(grp, "sc")
        z_lot = zscore_day(grp, "lot")
        z_gap = zscore_day(grp, "gap")
        for r in grp:
            r["_alt"] = z_sc[id(r)] - W * z_lot[id(r)] - W * z_gap[id(r)]

        top_orig = sorted(grp, key=lambda r: r["sc"], reverse=True)[:N]
        top_alt = sorted(grp, key=lambda r: r["_alt"], reverse=True)[:N]
        series["orig"][d] = statistics.mean(r["c5"] for r in top_orig)
        series["alt"][d] = statistics.mean(r["c5"] for r in top_alt)
        rand_vals = [
            statistics.mean(r["c5"] for r in RNG.sample(grp, N)) for _ in range(RAND_DRAWS)
        ]
        series["rand"][d] = statistics.mean(rand_vals)

    for k in ["orig", "alt", "rand"]:
        vals = list(series[k].values())
        n = len(vals)
        m = statistics.mean(vals)
        sd = statistics.pstdev(vals) if n > 1 else 0
        print(f"  top-{N} by {k:6} n_gun={n:4d}  ort-c2c_5d={m:+.4f}  std={sd:.4f}")

    def report_pair(label, base_key, other_key):
        common = sorted(set(series[base_key]) & set(series[other_key]))
        diffs = [series[other_key][d] - series[base_key][d] for d in common]
        if len(diffs) < 5:
            print(f"  {label:30} n=yetersiz")
            return
        m, t, n = naive_t(diffs)
        ci = block_bootstrap_ci(diffs)
        ci_str = f"[{ci[0]:+.4f}, {ci[1]:+.4f}]" if ci else "n/a"
        verdict = "ANLAMLI" if (ci and (ci[0] > 0 or ci[1] < 0)) else "anlamsiz(CI 0'i iceriyor)"
        idx = list(range(0, len(diffs), BLOCK))
        sub = [diffs[i] for i in idx]
        ms, ts, ns = naive_t(sub)
        print(
            f"  {label:30} n_gun={n:4d}  fark-ort={m:+.4f}  naive-t~={t:+.2f}  boot-CI={ci_str}  [{verdict}]  "
            f"| ortusmeyen-alt-orneklem n={ns} fark={ms:+.4f} t~={ts:+.2f}"
        )

    print()
    report_pair("alt - orig (lottery/gap katkisi)", "orig", "alt")
    report_pair("alt - rand (alt_score bilgi mi?)", "rand", "alt")
    report_pair("orig - rand (composite bilgi mi?)", "rand", "orig")


if __name__ == "__main__":
    main()
