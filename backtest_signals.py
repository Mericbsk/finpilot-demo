#!/usr/bin/env python3
"""
FinPilot Scanner Backtest & Signal Optimization
================================================
Gercek veriyle (data/finpilot.db -> signals_archive) durust backtest.
Master prompt Bolum 1-6'nin VERIDE KARSILIGI OLAN kismini kosar.
VERIDE OLMAYAN ozellikler (RVOL, float, short interest, gap%, ATR/ADR,
RSI/MACD, catalyst/earnings, IV, options) raporda 'VERI YOK' isaretlenir.
Kullanim: python backtest_signals.py [--db PATH] [--out DIR]
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sqlite3
from collections import Counter
from datetime import datetime

import numpy as np

try:
    from scipy.stats import chi2_contingency, fisher_exact

    HAVE_SCIPY = True
except Exception:
    HAVE_SCIPY = False

IS_END = "2026-01-01"
MIN_N = 30
MIN_N_RECO = 50
PENNY_PRICE = 1.0
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
        return None if x is None else float(x)
    except Exception:
        return None


def load_signals(db_path):
    con = sqlite3.connect(db_path)
    rows = con.execute("""
        SELECT id, symbol, ts, score, finpilot_score, payload_json,
               resolved_status, resolved_pct, resolved_pct_t5,
               resolved_pct_barrier, resolved_status_barrier
        FROM signals_archive""").fetchall()
    con.close()
    recs = []
    for sid, sym, ts, score, fps, pj, rstat, rpct, rpct5, rpctb, rstatb in rows:
        try:
            d = json.loads(pj) if pj else {}
        except Exception:
            d = {}
        entry = _f(d.get("entry_price"))
        stop = _f(d.get("stop_loss"))
        tp = _f(d.get("take_profit"))
        rr = _f(d.get("risk_reward"))
        regime_raw = str(d.get("regime"))
        if regime_raw in ("True", "1", "Trend"):
            regime = 1
        elif regime_raw in ("False", "0", "Range"):
            regime = 0
        else:
            regime = None
        stop_dist = (
            abs(entry - stop) / entry * 100.0
            if (entry and entry > 0 and stop and stop > 0)
            else None
        )
        tp_dist = (
            abs(tp - entry) / entry * 100.0 if (entry and entry > 0 and tp and tp > 0) else None
        )
        recs.append(
            dict(
                id=sid,
                symbol=sym,
                ts=ts,
                date=(ts or "")[:10],
                score=_f(score),
                rr=rr,
                regime=regime,
                regime_raw=regime_raw,
                entry=entry,
                stop=stop,
                tp=tp,
                stop_dist=stop_dist,
                tp_dist=tp_dist,
                resolved_status=rstat,
                rpct=_f(rpct),
                rpct5=_f(rpct5),
                rpct_barrier=_f(rpctb),
            )
        )
    return recs


def apply_quality_filters(recs):
    report = Counter()
    kept = []
    for r in recs:
        report["total"] += 1
        if r["rpct5"] is None and r["rpct"] is None:
            report["drop_unresolved"] += 1
            continue
        if r["entry"] is not None and r["entry"] < PENNY_PRICE:
            report["drop_penny"] += 1
            continue
        kept.append(r)
        report["kept"] += 1
    return kept, report


TARGETS = {
    "Y_5pct_5d": lambda r: (r["rpct5"] >= 5) if r["rpct5"] is not None else None,
    "Y_10pct_5d": lambda r: (r["rpct5"] >= 10) if r["rpct5"] is not None else None,
    "Y_5pct_res": lambda r: (r["rpct"] >= 5) if r["rpct"] is not None else None,
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
    rets_close = np.array([r["rpct"] for r in sub if r["rpct"] is not None], float)
    return dict(
        n=n,
        hit_rate=round(float(hit_rate), 4),
        base_rate=round(float(base), 4),
        lift=round(float(lift), 3) if lift == lift else None,
        control_hit=round(float(c_hits.mean()), 4) if len(c_hits) else None,
        p=pval,
        p_test=ptest,
        mean_ret5=round(float(rets.mean()), 3) if len(rets) else None,
        median_ret5=round(float(np.median(rets)), 3) if len(rets) else None,
        mean_ret_close=round(float(rets_close.mean()), 3) if len(rets_close) else None,
        pct_neg=round(float((rets_close < 0).mean()), 4) if len(rets_close) else None,
    )


def prec_recall(sub, universe, target):
    s_hits = hit_array(sub, target)
    u_hits = hit_array(universe, target)
    if len(s_hits) == 0 or u_hits.sum() == 0:
        return None
    precision = s_hits.mean()
    recall = s_hits.sum() / u_hits.sum()
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0
    return dict(
        precision=round(float(precision), 4), recall=round(float(recall), 4), f1=round(float(f1), 4)
    )


def filt_score(thr):
    return lambda r: r["score"] is not None and r["score"] >= thr


def filt_rr(thr):
    return lambda r: r["rr"] is not None and r["rr"] >= thr


def filt_regime_up():
    return lambda r: r["regime"] == 1


def filt_regime_rng():
    return lambda r: r["regime"] == 0


def filt_stopdist_lt(thr):
    return lambda r: r["stop_dist"] is not None and r["stop_dist"] < thr


def filt_stopdist_gt(thr):
    return lambda r: r["stop_dist"] is not None and r["stop_dist"] >= thr


def filt_stopdist_band(lo, hi):
    return lambda r: r["stop_dist"] is not None and lo <= r["stop_dist"] < hi


def subset(recs, *filters):
    out = recs
    for f in filters:
        out = [r for r in out if f(r)]
    return out


def analyze_single_signals(recs, target=PRIMARY):
    results = []
    for thr in [1, 2, 3, 5, 8, 10, 15, 20]:
        m = subset_metrics(subset(recs, filt_score(thr)), recs, target)
        if m:
            results.append(dict(signal=f"score >= {thr}", **m))
    for thr in [2.0, 2.6, 3.0, 3.33]:
        m = subset_metrics(subset(recs, filt_rr(thr)), recs, target)
        if m:
            results.append(dict(signal=f"risk_reward >= {thr}", **m))
    for name, f in [
        ("regime = Up/Trend", filt_regime_up()),
        ("regime = Range/False", filt_regime_rng()),
    ]:
        m = subset_metrics(subset(recs, f), recs, target)
        if m:
            results.append(dict(signal=name, **m))
    for label, f in [
        ("stop_dist < 2%", filt_stopdist_lt(2)),
        ("stop_dist 2-5%", filt_stopdist_band(2, 5)),
        ("stop_dist >= 5%", filt_stopdist_gt(5)),
    ]:
        m = subset_metrics(subset(recs, f), recs, target)
        if m:
            results.append(dict(signal=label, **m))
    return results


def analyze_combinations(recs, target=PRIMARY):
    layers = [dict(step="Baslangic evreni", **subset_metrics(recs, recs, target))]
    active = []
    for label, f in [
        ("+ score >= 2", filt_score(2)),
        ("+ risk_reward >= 2.0", filt_rr(2.0)),
        ("+ regime = Up/Trend", filt_regime_up()),
    ]:
        active.append(f)
        m = subset_metrics(subset(recs, *active), recs, target)
        if m:
            layers.append(dict(step=label, **m))
    alt = []
    alt_active = []
    for label, f in [
        ("score >= 3", filt_score(3)),
        ("+ risk_reward >= 2.6", filt_rr(2.6)),
        ("+ stop_dist 2-5%", filt_stopdist_band(2, 5)),
    ]:
        alt_active.append(f)
        m = subset_metrics(subset(recs, *alt_active), recs, target)
        if m:
            alt.append(dict(step=label, **m))
    return {"chain_primary": layers, "chain_highscore": alt}


def scoring_system(recs, target=PRIMARY):
    def pts(r):
        p = 0
        if r["score"] is not None and r["score"] >= 3:
            p += 2
        if r["rr"] is not None and r["rr"] >= 2.6:
            p += 3
        if r["rr"] is not None and r["rr"] >= 3.0:
            p += 1
        if r["stop_dist"] is not None and r["stop_dist"] >= 2:
            p += 2
        if r["regime"] == 0:
            p += 1
        return p

    out = []
    for thr in [2, 3, 4, 5, 6, 7, 8]:
        sub = [r for r in recs if pts(r) >= thr]
        m = subset_metrics(sub, recs, target)
        if m:
            pr = prec_recall(sub, recs, target)
            out.append(dict(min_points=thr, **m, **(pr or {})))
    return out


def walk_forward(recs, target=PRIMARY):
    IS = [r for r in recs if r["ts"] and r["ts"] < IS_END]
    OOS = [r for r in recs if r["ts"] and r["ts"] >= IS_END]
    candidates = []
    for thr in [1, 2, 3, 5, 8, 10]:
        m = subset_metrics(subset(IS, filt_score(thr)), IS, target)
        if m and m["n"] >= MIN_N:
            candidates.append((thr, m))
    sig = [(t, m) for t, m in candidates if m["p"] is not None and m["p"] < ALPHA]
    pool = sig if sig else candidates
    best_thr = max(pool, key=lambda x: (x[1]["lift"] or 0))[0] if pool else None
    result = {
        "IS_end": IS_END,
        "n_IS": len(IS),
        "n_OOS": len(OOS),
        "best_score_thr": best_thr,
        "IS_metrics": None,
        "OOS_metrics": None,
        "degradation": None,
        "lift_degradation": None,
        "verdict": None,
    }
    if best_thr is not None:
        is_m = subset_metrics(subset(IS, filt_score(best_thr)), IS, target)
        oos_m = subset_metrics(subset(OOS, filt_score(best_thr)), OOS, target)
        result["IS_metrics"] = is_m
        result["OOS_metrics"] = oos_m
        if is_m and oos_m and is_m["hit_rate"] > 0:
            result["degradation"] = round(1 - oos_m["hit_rate"] / is_m["hit_rate"], 3)
            if is_m["lift"] and oos_m["lift"] is not None:
                result["lift_degradation"] = round(1 - oos_m["lift"] / is_m["lift"], 3)
            ok = (
                oos_m["lift"] is not None
                and oos_m["lift"] > 1.5
                and oos_m["p"] is not None
                and oos_m["p"] < ALPHA
            )
            result["verdict"] = "GECTI" if ok else "ZAYIF/OVERFIT RISKI"
    return result


def walk_forward_multi(recs, target=PRIMARY):
    IS = [r for r in recs if r["ts"] and r["ts"] < IS_END]
    OOS = [r for r in recs if r["ts"] and r["ts"] >= IS_END]
    named = [
        ("score >= 2", filt_score(2)),
        ("score >= 3", filt_score(3)),
        ("risk_reward >= 2.6", filt_rr(2.6)),
        ("risk_reward >= 3.0", filt_rr(3.0)),
        ("stop_dist 2-5%", filt_stopdist_band(2, 5)),
        ("stop_dist >= 5%", filt_stopdist_gt(5)),
        ("regime = Range/False", filt_regime_rng()),
    ]
    rows = []
    for name, f in named:
        is_m = subset_metrics(subset(IS, f), IS, target)
        oos_m = subset_metrics(subset(OOS, f), OOS, target)
        row = {
            "signal": name,
            "IS_n": is_m["n"] if is_m else 0,
            "IS_hit": is_m["hit_rate"] if is_m else None,
            "IS_lift": is_m["lift"] if is_m else None,
            "OOS_n": oos_m["n"] if oos_m else 0,
            "OOS_hit": oos_m["hit_rate"] if oos_m else None,
            "OOS_lift": oos_m["lift"] if oos_m else None,
            "OOS_p": oos_m["p"] if oos_m else None,
        }
        if row["IS_lift"] and row["OOS_lift"] is not None:
            row["lift_degradation"] = round(1 - row["OOS_lift"] / row["IS_lift"], 3)
            ok = (
                row["OOS_lift"] > 1.3
                and row["OOS_p"] is not None
                and row["OOS_p"] < ALPHA
                and row["OOS_n"] >= MIN_N
            )
            row["verdict"] = "GECTI" if ok else "ZAYIF/OVERFIT"
        else:
            row["lift_degradation"] = None
            row["verdict"] = "YETERSIZ VERI"
        rows.append(row)
    return rows


def overfitting_checks(single, walk, wfm, recs, target=PRIMARY):
    flags = []
    for s in single:
        if s["hit_rate"] > 0.80 and s["n"] >= MIN_N:
            flags.append(
                f"{s['signal']}: hit rate %{s['hit_rate']*100:.0f} >80% (data leakage suphesi)"
            )
        if s["n"] < MIN_N:
            flags.append(f"{s['signal']}: n={s['n']} < {MIN_N} (yetersiz veri)")
    if walk.get("lift_degradation") is not None and walk["lift_degradation"] > 0.30:
        flags.append(
            f"Walk-forward (score): OOS lift IS'ten %{walk['lift_degradation']*100:.0f} dustu (>30% overfitting)"
        )
    for r in wfm:
        if (
            r["verdict"] == "ZAYIF/OVERFIT"
            and r["lift_degradation"] is not None
            and r["lift_degradation"] > 0.30
        ):
            flags.append(
                f"{r['signal']}: OOS lift %{r['lift_degradation']*100:.0f} dustu, OOS edge zayif"
            )
    base = subset_metrics(recs, recs, target)
    simplest = subset_metrics(subset(recs, filt_score(1)), recs, target)
    return dict(
        flags=flags,
        base_rate=base["hit_rate"],
        simplest_lift=simplest["lift"] if simplest else None,
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="data/finpilot.db")
    ap.add_argument("--out", default=".")
    args = ap.parse_args()
    recs_all = load_signals(args.db)
    recs, qrep = apply_quality_filters(recs_all)
    months = Counter(r["date"][:7] for r in recs)
    inventory = dict(
        total_archive=len(recs_all),
        after_filters=len(recs),
        quality_report=dict(qrep),
        ts_min=min((r["ts"] for r in recs if r["ts"]), default=None),
        ts_max=max((r["ts"] for r in recs if r["ts"]), default=None),
        per_month={k: months[k] for k in sorted(months)},
        n_symbols=len({r["symbol"] for r in recs}),
        scipy=HAVE_SCIPY,
    )
    out = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "primary_target": PRIMARY,
        "inventory": inventory,
    }
    out["base_rates"] = {t: round(float(hit_array(recs, t).mean()), 4) for t in TARGETS}
    out["single_primary"] = analyze_single_signals(recs, PRIMARY)
    out["single_10pct"] = analyze_single_signals(recs, "Y_10pct_5d")
    valid = [
        s
        for s in out["single_primary"]
        if s["n"] >= MIN_N_RECO
        and s["p"] is not None
        and s["p"] < ALPHA
        and s["lift"] is not None
        and s["lift"] > 1.0
    ]
    out["top5_signals"] = sorted(valid, key=lambda s: s["lift"], reverse=True)[:5]
    out["combinations"] = analyze_combinations(recs, PRIMARY)
    out["scoring_system"] = scoring_system(recs, PRIMARY)
    out["walk_forward"] = walk_forward(recs, PRIMARY)
    out["walk_forward_multi"] = walk_forward_multi(recs, PRIMARY)
    out["overfitting"] = overfitting_checks(
        out["single_primary"], out["walk_forward"], out["walk_forward_multi"], recs, PRIMARY
    )
    os.makedirs(args.out, exist_ok=True)
    jpath = os.path.join(args.out, "backtest_results.json")
    with open(jpath, "w") as f:
        json.dump(out, f, indent=2, default=str)
    cpath = os.path.join(args.out, "backtest_single_signals.csv")
    with open(cpath, "w", newline="") as f:
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
            "mean_ret_close",
            "pct_neg",
        ]
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for s in out["single_primary"]:
            w.writerow({k: s.get(k) for k in cols})
    print("OK ->", jpath)
    print("OK ->", cpath)
    print("scipy:", HAVE_SCIPY, " n:", len(recs), " base_rate:", out["base_rates"][PRIMARY])
    print("Top5:", [s["signal"] for s in out["top5_signals"]])
    print(
        "WF(score) verdict:",
        out["walk_forward"]["verdict"],
        " best_thr:",
        out["walk_forward"]["best_score_thr"],
    )
    return out


if __name__ == "__main__":
    main()
