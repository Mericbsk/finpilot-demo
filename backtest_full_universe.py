#!/usr/bin/env python3
"""
FinPilot Full-Universe Backtest — entry_ok=True/False kontrol grubu dahil
==========================================================================
Girdi: data/backtest_out/full_universe_enriched.csv
       (fetch_full_universe_and_retest.py --provider ... tarafindan uretilir)

backtest_signals.py ile AYNI metodoloji (hit rate, lift, iki-oran z-testi,
walk-forward IS/OOS, overfitting kontrolu) ama YENI olarak:
  - Gercek taban orani: TUM taranan evren (entry_ok True/False farketmeksizin)
  - entry_ok=True vs False lift — scanner'in kendi AL-gate'inin GERCEK degeri
  - score/composite_score TAM aralikta (0-100) esik taramasi
  - tier / squeeze_factor / sentiment full-evren edge'i
  - Dedup sanity-check: (symbol, scan_date) basina TEK gozlem alindiginda
    sonuclar nasil degisiyor (kullanici karariyla ana analiz dedup YAPMIYOR,
    gun ici tekrar taramalarin hepsini ayri gozlem sayiyor — bu ikincil
    kontrol o kararin etkisini gosterir).

Kullanim:
  python backtest_full_universe.py
  python backtest_full_universe.py --csv data/backtest_out/full_universe_enriched.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
from collections import Counter
from datetime import datetime

import numpy as np

try:
    from scipy.stats import chi2_contingency, fisher_exact

    HAVE_SCIPY = True
except Exception:
    HAVE_SCIPY = False

ROOT = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CSV = os.path.join(ROOT, "data", "backtest_out", "full_universe_enriched.csv")
OUT_DIR = os.path.join(ROOT, "data", "backtest_out")

IS_END = "2026-01-01"  # backtest_signals.py ile TUTARLI split — raporlar karsilastirilabilir
MIN_N = 30
MIN_N_RECO = 50
ALPHA = 0.05


def _norm_cdf(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def two_prop_pvalue(succ_a, n_a, succ_b, n_b):
    if n_a == 0 or n_b == 0:
        return None, None
    table = [[succ_a, n_a - succ_a], [succ_b, n_b - succ_b]]
    if HAVE_SCIPY:
        if min(succ_a, n_a - succ_a, succ_b, n_b - succ_b) < 5:
            try:
                _, p = fisher_exact(table)
                return p, "fisher"
            except Exception:
                pass
        try:
            chi2, p, _, _ = chi2_contingency(table, correction=True)
            return p, "chi2"
        except Exception:
            pass
    p1 = succ_a / n_a
    p2 = succ_b / n_b
    pp = (succ_a + succ_b) / (n_a + n_b)
    se = math.sqrt(pp * (1 - pp) * (1 / n_a + 1 / n_b))
    if se == 0:
        return 1.0, "ztest"
    z = (p1 - p2) / se
    return 2 * (1 - _norm_cdf(abs(z))), "ztest"


def _f(x):
    try:
        return None if x in (None, "") else float(x)
    except Exception:
        return None


def _b(x):
    return str(x).strip().lower() in ("true", "1", "yes")


# ---------------------------------------------------------------- load
def load_rows(csv_path):
    recs = []
    with open(csv_path, encoding="utf-8", newline="") as f:
        for i, d in enumerate(csv.DictReader(f)):
            recs.append(
                {
                    "id": f"{d.get('symbol')}_{d.get('scan_ts')}_{i}",
                    "symbol": d.get("symbol"),
                    "scan_date": d.get("scan_date"),
                    "score": _f(d.get("score")),
                    "composite_score": _f(d.get("composite_score")),
                    "entry_ok": _b(d.get("entry_ok")),
                    "rr": _f(d.get("risk_reward")),
                    "regime": d.get("regime"),
                    "tier": (d.get("tier") or "").strip() or None,
                    "squeeze_factor": _f(d.get("squeeze_factor")),
                    "catalyst_factor": _f(d.get("catalyst_factor")),
                    "sentiment": _f(d.get("sentiment")),
                    "vol_regime": d.get("vol_regime"),
                    "rpct5": _f(d.get("resolved_pct_t5")),
                    "rpct1": _f(d.get("resolved_pct_1d")),
                    "gap_pct": _f(d.get("gap_pct")),
                    "rvol": _f(d.get("rvol")),
                    "atr_pct": _f(d.get("atr_pct_real")),
                    "dist52": _f(d.get("dist_52w_high")),
                }
            )
    return recs


TARGETS = {
    "Y_5pct_5d": lambda r: (r["rpct5"] >= 5) if r["rpct5"] is not None else None,
    "Y_10pct_5d": lambda r: (r["rpct5"] >= 10) if r["rpct5"] is not None else None,
}
PRIMARY = "Y_5pct_5d"


def hit_array(recs, target):
    fn = TARGETS[target]
    out = []
    for r in recs:
        v = fn(r)
        if v is not None:
            out.append(1 if v else 0)
    return np.array(out, dtype=int)


def subset_metrics(sub, universe, target):
    s_hits = hit_array(sub, target)
    u_hits = hit_array(universe, target)
    n = len(s_hits)
    if n == 0:
        return None
    hit_rate = s_hits.mean()
    base = u_hits.mean() if len(u_hits) else float("nan")
    lift = (hit_rate / base) if base > 0 else float("nan")
    sids = {r["id"] for r in sub}
    control = [r for r in universe if r["id"] not in sids]
    c_hits = hit_array(control, target)
    pval, ptest = two_prop_pvalue(int(s_hits.sum()), len(s_hits), int(c_hits.sum()), len(c_hits))
    rets = np.array([r["rpct5"] for r in sub if r["rpct5"] is not None], float)
    return {
        "n": n,
        "hit_rate": round(float(hit_rate), 4),
        "base_rate": round(float(base), 4),
        "lift": round(float(lift), 3) if lift == lift else None,
        "control_hit": round(float(c_hits.mean()), 4) if len(c_hits) else None,
        "p": pval,
        "p_test": ptest,
        "mean_ret5": round(float(rets.mean()), 3) if len(rets) else None,
        "median_ret5": round(float(np.median(rets)), 3) if len(rets) else None,
    }


def subset(recs, *filters):
    out = recs
    for f in filters:
        out = [r for r in out if f(r)]
    return out


# ---------------------------------------------------------------- filters
def filt_score(thr):
    return lambda r: r["score"] is not None and r["score"] >= thr


def filt_composite(thr):
    return lambda r: r["composite_score"] is not None and r["composite_score"] >= thr


def filt_entry_ok(val):
    return lambda r: r["entry_ok"] is val


def filt_tier(t):
    return lambda r: r["tier"] == t


def filt_squeeze(thr):
    return lambda r: r["squeeze_factor"] is not None and r["squeeze_factor"] >= thr


def filt_sentiment_band(lo, hi):
    return lambda r: r["sentiment"] is not None and lo <= r["sentiment"] < hi


def filt_atr(thr):
    return lambda r: r["atr_pct"] is not None and r["atr_pct"] >= thr


def filt_gap(thr):
    return lambda r: r["gap_pct"] is not None and r["gap_pct"] > thr


def filt_rvol(thr):
    return lambda r: r["rvol"] is not None and r["rvol"] >= thr


# ---------------------------------------------------------------- analyses
def analyze_entry_gate(recs, target=PRIMARY):
    """Star finding: scanner'in kendi entry_ok=True gate'i, entry_ok=False
    (kontrol grubu) ile kiyaslandiginda GERCEKTEN edge katiyor mu?"""
    out = {}
    for label, f in [
        ("entry_ok=True (AL sinyali)", filt_entry_ok(True)),
        ("entry_ok=False (kontrol grubu)", filt_entry_ok(False)),
    ]:
        m = subset_metrics(subset(recs, f), recs, target)
        if m:
            out[label] = m
    return out


def analyze_single_signals(recs, target=PRIMARY):
    results = []
    for thr in [1, 2, 3, 5, 8, 10, 15, 20]:
        m = subset_metrics(subset(recs, filt_score(thr)), recs, target)
        if m:
            results.append(dict(signal=f"score >= {thr}", **m))
    for thr in [10, 20, 30, 40, 50, 60, 70, 80]:
        m = subset_metrics(subset(recs, filt_composite(thr)), recs, target)
        if m:
            results.append(dict(signal=f"composite_score >= {thr}", **m))
    for t in ["A", "B", "C"]:
        m = subset_metrics(subset(recs, filt_tier(t)), recs, target)
        if m:
            results.append(dict(signal=f"conviction tier = {t}", **m))
    for thr in [0.3, 0.5, 0.7]:
        m = subset_metrics(subset(recs, filt_squeeze(thr)), recs, target)
        if m:
            results.append(dict(signal=f"squeeze_factor >= {thr}", **m))
    for lo, hi, label in [
        (0.0, 0.4, "sentiment < 0.4 (negatif)"),
        (0.6, 1.01, "sentiment >= 0.6 (pozitif)"),
    ]:
        m = subset_metrics(subset(recs, filt_sentiment_band(lo, hi)), recs, target)
        if m:
            results.append(dict(signal=label, **m))
    for thr in [4, 6]:
        m = subset_metrics(subset(recs, filt_atr(thr)), recs, target)
        if m:
            results.append(dict(signal=f"ATR% >= {thr}", **m))
    for thr in [3, 5]:
        m = subset_metrics(subset(recs, filt_gap(thr)), recs, target)
        if m:
            results.append(dict(signal=f"gap% > {thr}", **m))
    for thr in [2, 5]:
        m = subset_metrics(subset(recs, filt_rvol(thr)), recs, target)
        if m:
            results.append(dict(signal=f"RVOL >= {thr}", **m))
    return results


def walk_forward_entry_gate(recs, target=PRIMARY):
    IS = [r for r in recs if r["scan_date"] and r["scan_date"] < IS_END]
    OOS = [r for r in recs if r["scan_date"] and r["scan_date"] >= IS_END]
    rows = []
    for label, f in [
        ("entry_ok=True", filt_entry_ok(True)),
        ("entry_ok=False", filt_entry_ok(False)),
    ]:
        is_m = subset_metrics(subset(IS, f), IS, target)
        oos_m = subset_metrics(subset(OOS, f), OOS, target)
        row = {
            "signal": label,
            "IS_n": is_m["n"] if is_m else 0,
            "IS_lift": is_m["lift"] if is_m else None,
            "OOS_n": oos_m["n"] if oos_m else 0,
            "OOS_lift": oos_m["lift"] if oos_m else None,
            "OOS_p": oos_m["p"] if oos_m else None,
        }
        rows.append(row)
    return {"IS_end": IS_END, "n_IS": len(IS), "n_OOS": len(OOS), "rows": rows}


def dedup_sanity_check(recs, target=PRIMARY):
    """(symbol, scan_date) basina TEK gozlem alinsaydi ana bulgular nasil
    degisirdi? Kullanici dedup YAPMAMAYI sectigi icin bu SADECE bir kontrol —
    ana rapor dedup-siz (tum intraday tekrarlar dahil) sonuclari kullanir."""
    seen = {}
    for r in recs:
        key = (r["symbol"], r["scan_date"])
        if key not in seen:
            seen[key] = r
    deduped = list(seen.values())
    full_m = subset_metrics(recs, recs, target)
    dedup_m = subset_metrics(deduped, deduped, target)
    gate_full = analyze_entry_gate(recs, target)
    gate_dedup = analyze_entry_gate(deduped, target)
    return {
        "n_full": len(recs),
        "n_dedup": len(deduped),
        "base_rate_full": full_m["hit_rate"] if full_m else None,
        "base_rate_dedup": dedup_m["hit_rate"] if dedup_m else None,
        "entry_gate_full": gate_full,
        "entry_gate_dedup": gate_dedup,
    }


def overfitting_checks(single, recs, target=PRIMARY):
    flags = []
    for s in single:
        if s["n"] < MIN_N:
            flags.append(f"{s['signal']}: n={s['n']} < {MIN_N} (yetersiz veri)")
        if s["hit_rate"] > 0.80 and s["n"] >= MIN_N:
            flags.append(f"{s['signal']}: hit rate %{s['hit_rate'] * 100:.0f} >80% (supheli)")
    base = subset_metrics(recs, recs, target)
    return {"flags": flags, "base_rate": base["hit_rate"] if base else None}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default=DEFAULT_CSV)
    ap.add_argument("--out", default=OUT_DIR)
    args = ap.parse_args()

    if not os.path.exists(args.csv):
        raise SystemExit(
            f"Bulunamadi: {args.csv}\n"
            "Once calistir: python fetch_full_universe_and_retest.py --provider alpaca"
        )

    recs = load_rows(args.csv)
    recs = [r for r in recs if r["rpct5"] is not None]  # cozulmemisleri at
    months = Counter((r["scan_date"] or "")[:7] for r in recs)
    n_symbols = len({r["symbol"] for r in recs})

    out = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "primary_target": PRIMARY,
        "inventory": {
            "n_rows": len(recs),
            "n_symbols": n_symbols,
            "per_month": dict(sorted(months.items())),
            "scipy": HAVE_SCIPY,
        },
    }
    out["base_rates"] = {t: round(float(hit_array(recs, t).mean()), 4) for t in TARGETS}
    out["entry_gate"] = analyze_entry_gate(recs, PRIMARY)
    out["entry_gate_walk_forward"] = walk_forward_entry_gate(recs, PRIMARY)
    out["single_primary"] = analyze_single_signals(recs, PRIMARY)
    valid = [
        s
        for s in out["single_primary"]
        if s["n"] >= MIN_N_RECO
        and s["p"] is not None
        and s["p"] < ALPHA
        and s["lift"]
        and s["lift"] > 1.0
    ]
    out["top_signals"] = sorted(valid, key=lambda s: s["lift"], reverse=True)[:10]
    out["dedup_sanity_check"] = dedup_sanity_check(recs, PRIMARY)
    out["overfitting"] = overfitting_checks(out["single_primary"], recs, PRIMARY)

    os.makedirs(args.out, exist_ok=True)
    jpath = os.path.join(args.out, "full_universe_backtest_results.json")
    with open(jpath, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, default=str)

    cpath = os.path.join(args.out, "full_universe_single_signals.csv")
    with open(cpath, "w", newline="", encoding="utf-8") as f:
        cols = [
            "signal",
            "n",
            "hit_rate",
            "base_rate",
            "lift",
            "control_hit",
            "p",
            "p_test",
            "mean_ret5",
            "median_ret5",
        ]
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for s in out["single_primary"]:
            w.writerow({k: s.get(k) for k in cols})

    print("OK ->", jpath)
    print("OK ->", cpath)
    print(
        f"\nn={len(recs)} satir, {n_symbols} sembol, taban oran (T+5 >=5%): "
        f"{out['base_rates'][PRIMARY] * 100:.1f}%"
    )
    print("\n=== ENTRY_OK GATE (star finding) ===")
    for label, m in out["entry_gate"].items():
        print(f"  {label:35s} n={m['n']:>6} hit={m['hit_rate'] * 100:>5.1f}% lift={m['lift']}")
    print("\n=== TOP SIGNALS (full universe) ===")
    for s in out["top_signals"][:10]:
        print(
            f"  {s['signal']:32s} n={s['n']:>6} hit={s['hit_rate'] * 100:>5.1f}% lift={s['lift']} p={s['p']}"
        )
    dsc = out["dedup_sanity_check"]
    print("\n=== DEDUP SANITY CHECK === (ana rapor dedup YAPMIYOR — bu sadece kontrol)")
    print(f"  Tum satirlar (dedup yok): n={dsc['n_full']}  base_rate={dsc['base_rate_full']}")
    print(f"  (symbol,tarih) basina tek: n={dsc['n_dedup']}  base_rate={dsc['base_rate_dedup']}")
    if out["overfitting"]["flags"]:
        print("\n=== UYARILAR ===")
        for fl in out["overfitting"]["flags"][:15]:
            print(f"  - {fl}")
    return out


if __name__ == "__main__":
    main()
