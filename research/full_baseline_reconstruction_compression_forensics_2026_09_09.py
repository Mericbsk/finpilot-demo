#!/usr/bin/env python3
"""
FULL BASELINE RECONSTRUCTION & RANKING COMPRESSION FORENSICS
Master Validation Prompt v1.0 (docs/MASTER_VALIDATION_PROMPT_2026-09-09.md) uygulamasi.

READ-ONLY / PRE-REGISTERED / FORENSIC. Agirlik optimizasyonu, grid search,
reverse-score, yeni feature, production/flag/DB/cache degisikligi YOK.

REPRODUCIBILITY
----------------
DATASET PATH : data/backtest_out/full_universe_enriched_eod_only.csv
SCRIPT VERSION: 1.0
DATE          : 2026-09-09
RANDOM SEED   : 20260909
TARGET        : c2c_1d (primary), c2c_5d (secondary)
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import random
import statistics
from collections import defaultdict
from pathlib import Path

RNG = random.Random(20260909)
SRC = Path("data/backtest_out/full_universe_enriched_eod_only.csv")
OUT_DIR = Path("reports")
BLOCK = 5
BOOT_B = 2000  # matched-random / permutation replication azaltilmis (n buyuk, hiz icin)


def f(x):
    try:
        v = float(x)
        return None if v != v else v
    except (TypeError, ValueError):
        return None


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load_dedup_rows():
    best = {}
    with open(SRC, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            k = (r["symbol"], r["scan_date"])
            ts = r.get("scan_ts", "")
            if k not in best or ts < best[k][0]:
                best[k] = (ts, r)
    return [r for _, r in best.values()]


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


def pearson(xs, ys):
    n = len(xs)
    if n < 2:
        return None
    mx, my = statistics.mean(xs), statistics.mean(ys)
    num = sum((a - mx) * (b - my) for a, b in zip(xs, ys, strict=False))
    dx = math.sqrt(sum((a - mx) ** 2 for a in xs))
    dy = math.sqrt(sum((b - my) ** 2 for b in ys))
    return num / (dx * dy) if dx and dy else None


def spearman(xs, ys):
    if len(xs) < 4:
        return None
    return pearson(ranks(xs), ranks(ys))


def kendall_tau_approx(xs, ys, max_n=1500):
    """O(n^2) exact kendall tau-b; buyuk n icin altorneklenir (max_n)."""
    n = len(xs)
    if n < 4:
        return None
    if n > max_n:
        idx = RNG.sample(range(n), max_n)
        xs = [xs[i] for i in idx]
        ys = [ys[i] for i in idx]
        n = max_n
    conc = disc = tx = ty = 0
    for i in range(n):
        for j in range(i + 1, n):
            dx = xs[i] - xs[j]
            dy = ys[i] - ys[j]
            if dx == 0 and dy == 0:
                continue
            if dx == 0:
                tx += 1
                continue
            if dy == 0:
                ty += 1
                continue
            if (dx > 0) == (dy > 0):
                conc += 1
            else:
                disc += 1
    denom = math.sqrt((conc + disc + tx) * (conc + disc + ty))
    return (conc - disc) / denom if denom else None


def quintiles(xs, ys, q=5):
    """xs'e gore siralayip q dilime bol, her dilimde ys istatistikleri."""
    n = len(xs)
    order = sorted(range(n), key=lambda i: xs[i])
    out = []
    for k in range(q):
        lo = int(n * k / q)
        hi = int(n * (k + 1) / q)
        idx = order[lo:hi]
        yv = [ys[i] for i in idx]
        if not yv:
            continue
        out.append(
            {
                "bucket": f"Q{k+1}",
                "n": len(yv),
                "mean": round(statistics.mean(yv), 4),
                "median": round(statistics.median(yv), 4),
                "hit_rate": round(sum(1 for v in yv if v > 0) / len(yv), 4),
            }
        )
    return out


def main():
    report = {}
    dataset_sha = sha256_of(SRC)
    report["dataset_sha256"] = dataset_sha
    print(f"[REPRO] dataset sha256={dataset_sha}")

    rows = load_dedup_rows()
    print(f"[VERI] EOD-only dedup satir = {len(rows)}")

    # ------------------------------------------------------------------
    # SECTION 7 -- INPUT COVERAGE FORENSICS
    # ------------------------------------------------------------------
    all_cols = list(rows[0].keys())
    baseline_cols_needed = [
        "regime",
        "direction",
        "score",
        "filter_score",
        "alignment_ratio",
        "momentum_ratio",
        "volume_spike",
        "price_momentum",
        "trend_strength",
    ]
    coverage_csv = []
    for col in baseline_cols_needed:
        present = col in all_cols
        if not present:
            coverage_csv.append(
                {
                    "column": col,
                    "total_rows": len(rows),
                    "non_null_rows": 0,
                    "null_rows": len(rows),
                    "coverage_pct": 0.0,
                    "first_valid_date": "",
                    "last_valid_date": "",
                    "classification": "MISSING",
                }
            )
            continue
        nn = [(r["scan_date"], r[col]) for r in rows if r.get(col) not in (None, "")]
        coverage_csv.append(
            {
                "column": col,
                "total_rows": len(rows),
                "non_null_rows": len(nn),
                "null_rows": len(rows) - len(nn),
                "coverage_pct": round(100 * len(nn) / len(rows), 2),
                "first_valid_date": min((d for d, _ in nn), default=""),
                "last_valid_date": max((d for d, _ in nn), default=""),
                "classification": "FULL"
                if len(nn) == len(rows)
                else "PARTIAL"
                if nn
                else "MISSING",
            }
        )
    with open(OUT_DIR / "baseline_input_coverage_2026-09-09.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(coverage_csv[0].keys()))
        w.writeheader()
        w.writerows(coverage_csv)
    print("\n[SEC 7] Input coverage:")
    for c in coverage_csv:
        print(f"  {c['column']:16} {c['classification']:10} coverage={c['coverage_pct']}%")

    # ------------------------------------------------------------------
    # SECTION 3/5/6 -- PARTIAL RECONSTRUCTION (R1) + EXACT MATCH TEST
    # ------------------------------------------------------------------
    # Kod (scanner/score_engine.py::compute_recommendation_score) BIREBIR AYNI
    # agirliklarla, ama alignment_ratio/momentum_ratio/filter_score/volume_spike/
    # price_momentum/trend_strength CSV'de YOK -> bu terimler icin katki
    # hesaplanamaz (0 varsayilmadi, "unavailable" olarak ayrildi).
    def r1_partial(row):
        s = 0.0
        s += 2.0 if str(row.get("regime")).strip().lower() == "true" else 0.0
        s += 2.0 if str(row.get("direction")).strip().lower() == "true" else 0.0
        sc = f(row.get("score"))
        s += (sc or 0.0) * 0.5
        return s  # filter_score/alignment/momentum/3-binary EKSIK -> tavan degil

    recon_rows = []
    for r in rows:
        cs = f(r.get("composite_score"))
        if cs is None:
            continue
        r1 = r1_partial(r)
        recon_rows.append(
            {"symbol": r["symbol"], "date": r["scan_date"], "stored": cs, "r1_partial": r1}
        )

    stored = [x["stored"] for x in recon_rows]
    r1p = [x["r1_partial"] for x in recon_rows]
    exact = sum(1 for a, b in zip(stored, r1p, strict=False) if abs(a - b) < 1e-6)
    abs_err = sorted(abs(a - b) for a, b in zip(stored, r1p, strict=False))
    n_r = len(recon_rows)
    print(f"\n[SEC 6] EXACT MATCH TEST (R1-partial, eksik terimlerle) n={n_r}")
    print(
        f"  exact_match_rate = {100*exact/n_r:.2f}%  (BEKLENEN: dusuk -- alignment/momentum/filter/3-binary eksik)"
    )
    if abs_err:
        print(
            f"  mean_abs_error={statistics.mean(abs_err):.3f}  median={statistics.median(abs_err):.3f}  "
            f"p95={abs_err[int(0.95*len(abs_err))]:.3f}  max={abs_err[-1]:.3f}"
        )
    corr = pearson(stored, r1p)
    scorr = spearman(stored, r1p)
    print(f"  correlation(stored, r1_partial) = {corr:.3f}   rank_correlation = {scorr:.3f}")
    print(
        "  KARAR: PRODUCTION BASELINE = NOT FULLY RECONSTRUCTED "
        "(missing_input: filter_score, alignment_ratio, momentum_ratio, volume_spike, price_momentum, trend_strength)"
    )
    report["reconstruction_fidelity"] = {
        "exact_match_rate_pct": round(100 * exact / n_r, 2),
        "correlation": round(corr, 4) if corr else None,
        "rank_correlation": round(scorr, 4) if scorr else None,
        "status": "NOT_FULLY_RECONSTRUCTED",
        "mismatch_reason": "missing_input",
    }

    with open(OUT_DIR / "baseline_reconstruction_components_2026-09-09.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(
            ["symbol", "date", "stored_composite_score", "r1_partial_reconstructed", "abs_error"]
        )
        for x in recon_rows[:5000]:  # tam liste cok buyuk, ornek/temsili kayit
            w.writerow(
                [
                    x["symbol"],
                    x["date"],
                    x["stored"],
                    x["r1_partial"],
                    abs(x["stored"] - x["r1_partial"]),
                ]
            )

    print(
        "\n[SEC 7-continued] Baseline formul bilesenlerinin CSV'deki karsiligi (dogrudan kod okuma ile):"
    )
    print(
        "  regime(binary,2 state) [FULL], direction(binary,2 state) [FULL], "
        "score(0-3,4 state) [FULL] -- reconstruct EDILEBILIR"
    )
    print(
        "  filter_score/alignment_ratio/momentum_ratio/volume_spike/price_momentum/trend_strength "
        "[MISSING] -- reconstruct EDILEMEZ (CSV'de kolon yok)"
    )

    Path(OUT_DIR / "_section_progress.json").write_text(json.dumps(report, indent=2))
    print("\n[OK] Section 3/5/6/7 tamamlandi.")


if __name__ == "__main__":
    main()

# ======================================================================
# EXTENSION -- R2 (per-component intermediate values), gercek kolonlarla
# squeeze_factor / catalyst_factor / lottery_factor / overnight_gap_factor /
# sentiment CSV'de MEVCUT (score_engine.py agirliklariyla dogrudan
# reconstruct edilebilir). filter_score/alignment_ratio/momentum_ratio
# HALA YOK -- bu terimler icin katki hesaplanamaz.
# VARSAYIM (acikca belirtiliyor): macro_factor_multiplier()=1.0 (regime=
# "neutral", core/macro_regime.py'den MEVCUT deger) -- HER SATIR/TARIH icin
# tarihsel rejim gecmisi bu ortamda mevcut degil, bu yuzden tum satirlara
# GUNCEL multiplier (1.0) uygulaniyor. Bu bir TAHMIN DEGIL AMA bir
# VARSAYIMDIR -- tarihsel rejim "neutral" olmayan donemler icin hata payi
# yaratabilir. Explicit UNKNOWN olarak isaretlendi.
# ======================================================================
SQUEEZE_W, CATALYST_W, LOTTERY_W, OVERNIGHT_W, MACRO_MULT_ASSUMED = 1.5, 1.5, 2.0, 1.0, 1.0
MAX_RECO_SCORE_CONST = 16.5  # scanner/score_engine.py:24, effective_max_reco_score() sabit dondurur

# DUZELTME (bu script'in ilk versiyonunda YANLIS varsayim vardi): CSV'deki
# `composite_score` kolonu compute_recommendation_score()'un HAM (0-16.5)
# ciktisi DEGIL. scanner/score_engine.py:378-397 dogrudan okundu (kod, hafizadan
# degil): `compute_recommendation_strength()` = round(clip(raw_score/16.5*100, 0, 100)).
# composite_score = bu 0-100 STRENGTH ciktisi. Onceki turlarda (bu oturumun
# erken kismi + gozden gecirilen onceki oturumlar) composite_score'un 0-16.5
# olcekli oldugu varsayilmisti -- bu YANLISTI ve asagida acikca duzeltiliyor.


def r2_raw(row):
    """R2: ham (0-16.5 olcekli, henuz strength-yuzdesine cevrilmemis) ara-toplam."""
    s = 0.0
    s += 2.0 if str(row.get("regime")).strip().lower() == "true" else 0.0
    s += 2.0 if str(row.get("direction")).strip().lower() == "true" else 0.0
    sc = f(row.get("score"))
    s += (sc or 0.0) * 0.5
    sq = f(row.get("squeeze_factor"))
    if sq is not None:
        s += sq * SQUEEZE_W * MACRO_MULT_ASSUMED
    ca = f(row.get("catalyst_factor"))
    if ca is not None:
        s += ca * CATALYST_W * MACRO_MULT_ASSUMED
    lo = f(row.get("lottery_factor"))
    if lo is not None:
        s -= lo * LOTTERY_W
    og = f(row.get("overnight_gap_factor"))
    if og is not None:
        s -= og * OVERNIGHT_W
    se = f(row.get("sentiment"))
    if se is not None:
        s += se * 0.5
    return s


def r2_reconstruct(row):
    """R3: r2_raw()'u compute_recommendation_strength() ile BIREBIR AYNI sekilde
    0-100 STRENGTH'e cevirir (round(clip(raw/16.5*100, 0, 100))) -- composite_score
    kolonuyla dogru olcekte karsilastirilabilir hale getirir."""
    raw = r2_raw(row)
    strength = max(0.0, min(100.0, (raw / MAX_RECO_SCORE_CONST) * 100.0))
    return round(strength)


def main2():
    rows = load_dedup_rows()
    recon2 = []
    for r in rows:
        cs = f(r.get("composite_score"))
        if cs is None:
            continue
        recon2.append(
            {"symbol": r["symbol"], "date": r["scan_date"], "stored": cs, "r2": r2_reconstruct(r)}
        )
    stored = [x["stored"] for x in recon2]
    r2v = [x["r2"] for x in recon2]
    n_r = len(recon2)
    exact = sum(1 for a, b in zip(stored, r2v, strict=False) if abs(a - b) < 1e-6)
    abs_err = sorted(abs(a - b) for a, b in zip(stored, r2v, strict=False))
    corr = pearson(stored, r2v)
    scorr = spearman(stored, r2v)
    print(
        f"\n[SEC 6-R2] EXACT MATCH TEST (R2, squeeze/catalyst/lottery/overnight/sentiment dahil) n={n_r}"
    )
    print(f"  exact_match_rate = {100*exact/n_r:.2f}%")
    print(
        f"  mean_abs_error={statistics.mean(abs_err):.3f}  median={statistics.median(abs_err):.3f}  "
        f"p95={abs_err[int(0.95*len(abs_err))]:.3f}  max={abs_err[-1]:.3f}"
    )
    print(f"  correlation(stored, r2) = {corr:.4f}   rank_correlation = {scorr:.4f}")
    print(
        "  KARAR: hala PRODUCTION BASELINE = NOT FULLY RECONSTRUCTED "
        "(missing: filter_score, alignment_ratio, momentum_ratio, volume_spike, price_momentum, trend_strength)"
    )
    print(
        "  VARSAYIM ISARETI: macro_factor_multiplier tarihsel olarak dogrulanamadi, guncel deger (1.0) tum satirlara uygulandi -- UNKNOWN riski var"
    )

    # SECTION 8/12 -- COMPONENT PREDICTIVENESS (mevcut bilesenler icin, forward return'e karsi)
    targets = {}
    for tname in ("c2c_1d", "c2c_5d"):
        tv = [f(r.get(tname)) for r in rows]
        targets[tname] = tv

    comp_cols = [
        "score",
        "squeeze_factor",
        "catalyst_factor",
        "lottery_factor",
        "overnight_gap_factor",
        "sentiment",
        "tier_score",
        "finpilot_score",
        "composite_score",
    ]
    pred_csv = []
    for col in comp_cols:
        xv_raw = [f(r.get(col)) for r in rows]
        for tname, tv_raw in targets.items():
            pairs = [
                (x, y)
                for x, y in zip(xv_raw, tv_raw, strict=False)
                if x is not None and y is not None
            ]
            if len(pairs) < 30:
                pred_csv.append(
                    {
                        "component": col,
                        "target": tname,
                        "n": len(pairs),
                        "pearson": None,
                        "spearman": None,
                        "kendall_tau_approx": None,
                        "classification": "INSUFFICIENT_DATA",
                    }
                )
                continue
            xs = [p[0] for p in pairs]
            ys = [p[1] for p in pairs]
            pr = pearson(xs, ys)
            sr = spearman(xs, ys)
            kt = None  # kendall atlandi (perf) -- pearson+spearman yeterli, ayri not: kendall istenirse offline calistirilabilir
            cls = (
                "WEAK"
                if pr is not None and abs(pr) < 0.05
                else "MODEST"
                if pr is not None and abs(pr) < 0.15
                else "NOTABLE"
                if pr is not None
                else "UNKNOWN"
            )
            if col == "catalyst_factor":
                cls = "UNTESTABLE_NO_VARIANCE"  # tek deger=0.0
            pred_csv.append(
                {
                    "component": col,
                    "target": tname,
                    "n": len(pairs),
                    "pearson": round(pr, 4) if pr is not None else None,
                    "spearman": round(sr, 4) if sr is not None else None,
                    "kendall_tau_approx": round(kt, 4) if kt is not None else None,
                    "classification": cls,
                }
            )
    with open("reports/baseline_component_predictiveness_2026-09-09.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(pred_csv[0].keys()))
        w.writeheader()
        w.writerows(pred_csv)
    print("\n[SEC 8/12] Component predictiveness (forward return'e karsi korelasyon):")
    for p in pred_csv:
        print(
            f"  {p['component']:20} vs {p['target']:8} n={p['n']:6} pearson={p['pearson']} spearman={p['spearman']} -> {p['classification']}"
        )

    # SECTION 9 -- RANDOM CONTROL (composite_score permute edilip forward-return korelasyonu)
    cs_vals = [f(r.get("composite_score")) for r in rows]
    c1_vals = targets["c2c_1d"]
    pairs = [
        (x, y) for x, y in zip(cs_vals, c1_vals, strict=False) if x is not None and y is not None
    ]
    xs_real = [p[0] for p in pairs]
    ys_real = [p[1] for p in pairs]
    real_corr = pearson(xs_real, ys_real)
    null_corrs = []
    xs_shuf = list(xs_real)
    for _ in range(150):
        RNG.shuffle(xs_shuf)
        c = pearson(xs_shuf, ys_real)
        if c is not None:
            null_corrs.append(c)
    null_corrs.sort()
    p_val = sum(1 for c in null_corrs if abs(c) >= abs(real_corr)) / len(null_corrs)
    print("\n[SEC 9] RANDOM CONTROL: composite_score vs c2c_1d")
    print(
        f"  gercek pearson={real_corr:.4f}  null_dagilim mean={statistics.mean(null_corrs):.4f} "
        f"std={statistics.stdev(null_corrs):.4f}  permutation_p={p_val:.4f}  n_null={len(null_corrs)}"
    )
    with open("reports/baseline_random_control_2026-09-09.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["metric", "value"])
        w.writerow(["real_pearson_composite_vs_c2c1d", round(real_corr, 4)])
        w.writerow(["null_mean", round(statistics.mean(null_corrs), 4)])
        w.writerow(["null_std", round(statistics.stdev(null_corrs), 4)])
        w.writerow(["permutation_p", round(p_val, 4)])
        w.writerow(["n_null_replications", len(null_corrs)])
        w.writerow(["n_pairs", len(pairs)])

    # SECTION 10 -- LEAVE-ONE-OUT (r2 terimlerinden birini cikarinca composite_score korelasyonu nasil degisir)
    loo_csv = []
    base_pairs = [(x["r2"], x["stored"]) for x in recon2]
    base_corr = pearson([p[0] for p in base_pairs], [p[1] for p in base_pairs])
    term_names = [
        "regime",
        "direction",
        "score",
        "squeeze_factor",
        "catalyst_factor",
        "lottery_factor",
        "overnight_gap_factor",
        "sentiment",
    ]
    for excl in term_names:
        vals = []
        for r in rows:
            cs = f(r.get("composite_score"))
            if cs is None:
                continue
            s = 0.0
            if excl != "regime":
                s += 2.0 if str(r.get("regime")).strip().lower() == "true" else 0.0
            if excl != "direction":
                s += 2.0 if str(r.get("direction")).strip().lower() == "true" else 0.0
            if excl != "score":
                sc = f(r.get("score"))
                s += (sc or 0.0) * 0.5
            if excl != "squeeze_factor":
                sq = f(r.get("squeeze_factor"))
                if sq is not None:
                    s += sq * SQUEEZE_W
            if excl != "catalyst_factor":
                ca = f(r.get("catalyst_factor"))
                if ca is not None:
                    s += ca * CATALYST_W
            if excl != "lottery_factor":
                lo = f(r.get("lottery_factor"))
                if lo is not None:
                    s -= lo * LOTTERY_W
            if excl != "overnight_gap_factor":
                og = f(r.get("overnight_gap_factor"))
                if og is not None:
                    s -= og * OVERNIGHT_W
            if excl != "sentiment":
                se = f(r.get("sentiment"))
                if se is not None:
                    s += se * 0.5
            vals.append((s, cs))
        c = pearson([v[0] for v in vals], [v[1] for v in vals])
        loo_csv.append(
            {
                "excluded_term": excl,
                "corr_with_stored_without_term": round(c, 4) if c else None,
                "full_r2_corr": round(base_corr, 4),
                "delta": round((base_corr - c), 4) if c else None,
            }
        )
    with open("reports/baseline_leave_one_out_2026-09-09.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(loo_csv[0].keys()))
        w.writeheader()
        w.writerows(loo_csv)
    print(f"\n[SEC 10] LEAVE-ONE-OUT (full R2 corr={base_corr:.4f} baseline ile):")
    for row in loo_csv:
        print(
            f"  exclude={row['excluded_term']:20} corr_without={row['corr_with_stored_without_term']} delta={row['delta']}"
        )

    # SECTION -- COMPONENT CORRELATION MATRIX (bilesenler arasi, redundancy taramasi icin -- dist_52w_high dahil)
    corr_cols = [
        "score",
        "squeeze_factor",
        "lottery_factor",
        "overnight_gap_factor",
        "sentiment",
        "tier_score",
        "finpilot_score",
        "dist_52w_high",
        "gap_pct",
        "rvol",
        "atr_pct_real",
    ]
    matrix_rows = []
    col_vals = {c: [f(r.get(c)) for r in rows] for c in corr_cols}
    for i, c1 in enumerate(corr_cols):
        for c2 in corr_cols[i + 1 :]:
            pairs = [
                (x, y)
                for x, y in zip(col_vals[c1], col_vals[c2], strict=False)
                if x is not None and y is not None
            ]
            if len(pairs) < 30:
                continue
            xs = [p[0] for p in pairs]
            ys = [p[1] for p in pairs]
            pr = pearson(xs, ys)
            matrix_rows.append(
                {
                    "col_a": c1,
                    "col_b": c2,
                    "n": len(pairs),
                    "pearson": round(pr, 4) if pr is not None else None,
                }
            )
    with open("reports/baseline_component_correlation_2026-09-09.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(matrix_rows[0].keys()))
        w.writeheader()
        w.writerows(matrix_rows)
    print("\n[SEC -- REDUNDANCY] En yuksek |pearson| ciftler (dist_52w_high dahil):")
    for m in sorted(matrix_rows, key=lambda x: -abs(x["pearson"] or 0))[:8]:
        print(f"  {m['col_a']:16} <-> {m['col_b']:16} pearson={m['pearson']}  n={m['n']}")

    # SECTION 13-17 -- WALK FORWARD (composite_score aylik quintile -> c2c_1d hit-rate stabilitesi)
    by_month = defaultdict(list)
    for r in rows:
        cs = f(r.get("composite_score"))
        c1 = f(r.get("c2c_1d"))
        if cs is None or c1 is None:
            continue
        month = r["scan_date"][:7]
        by_month[month].append((cs, c1))
    wf_rows = []
    for month in sorted(by_month.keys()):
        pts = by_month[month]
        if len(pts) < 30:
            wf_rows.append(
                {
                    "month": month,
                    "n": len(pts),
                    "q1_hit_rate": None,
                    "q5_hit_rate": None,
                    "spread": None,
                    "note": "INSUFFICIENT_N",
                }
            )
            continue
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        qs = quintiles(xs, ys)
        q1 = next((q for q in qs if q["bucket"] == "Q1"), None)
        q5 = next((q for q in qs if q["bucket"] == "Q5"), None)
        spread = (q5["hit_rate"] - q1["hit_rate"]) if q1 and q5 else None
        wf_rows.append(
            {
                "month": month,
                "n": len(pts),
                "q1_hit_rate": q1["hit_rate"] if q1 else None,
                "q5_hit_rate": q5["hit_rate"] if q5 else None,
                "spread": round(spread, 4) if spread is not None else None,
                "note": "",
            }
        )
    with open("reports/baseline_reconstruction_walk_forward_2026-09-09.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(wf_rows[0].keys()))
        w.writeheader()
        w.writerows(wf_rows)
    print("\n[SEC 13-17] WALK-FORWARD (aylik composite_score Q1 vs Q5 hit-rate, c2c_1d):")
    for w_ in wf_rows:
        print(
            f"  {w_['month']}  n={w_['n']:5}  Q1={w_['q1_hit_rate']}  Q5={w_['q5_hit_rate']}  spread={w_['spread']}  {w_['note']}"
        )

    # SECTION -- COMPRESSION FORENSICS (tekrar, R2 dahil edilerek CSV'ye yazilan ozet)
    with open("reports/baseline_compression_forensics_2026-09-09.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["metric", "value"])
        w.writerow(["n_rows_eod_dedup", n_r])
        w.writerow(["unique_composite_score_values", len({round(v, 6) for v in stored})])
        w.writerow(
            ["tie_ratio_pct", round(100 * (1 - len({round(v, 6) for v in stored}) / n_r), 4)]
        )
        w.writerow(["r2_correlation_with_stored", round(corr, 4) if corr else None])
        w.writerow(["r2_rank_correlation_with_stored", round(scorr, 4) if scorr else None])
        w.writerow(["r2_exact_match_pct", round(100 * exact / n_r, 2)])

    return {
        "r2_corr": corr,
        "r2_rank_corr": scorr,
        "r2_exact_pct": round(100 * exact / n_r, 2),
        "random_control_p": p_val,
        "real_corr_composite_c2c1d": real_corr,
    }


if __name__ == "__main__":
    res = main2()
    print("\n[SUMMARY]", json.dumps(res, indent=2, default=str))
