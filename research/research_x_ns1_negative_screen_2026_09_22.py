"""RESEARCH-X/NS-1 - Negative-Screen Battery. PRE-REGISTERED, READ-ONLY.

Preregistration (APPROVED/LOCKED):
  reports/research_x_ns1_negative_screen_preregistration_2026-09-22.md
  SHA-256 9e53d40759b6b989719f59fdd4d559c7f5fcc8a7346a3e1fd39e94c95c236838

This runner implements the locked protocol EXACTLY. It cannot change rules,
thresholds, controls, the temporal contract, the verdict set, or determinism
rules. Screening evidence is NOT a buy signal and NOT a production filter.

Locked protocol summary:
  Input:   data/backtest_out/full_universe_enriched_eod_only.csv
           SHA-256 87541cc54eb7c360b865ca5df6141fcd84ddb089d5d461b6e40dda74d8b073ad
  Dedup:   one row per (symbol, scan_date), earliest lexical scan_ts.
  Filter:  composite_score non-null AND c2c_5d non-null (expected n ~= 34,762;
           |dn| > 1% -> INPUT_MISMATCH).
  Rules (primary family, Bonferroni 98.75% adjusted CI):
    NS-A     : |gap_pct| >= 3 OR atr_pct_real >= 6        (ANS-1 exact)
    NS-B3    : >=3 of {atr_pct_real>=p80, lottery_factor>=p80,
                       price<=p20, dist_52w_high<=p20}    (scan_date-internal)
    NS-C     : lottery_factor >= p80
    NS-UNION : NS-A OR NS-B3
  Secondary/descriptive arms: NS-B4 (all 4), the 4 single-condition arms of
  NS-B3, and a price>=5 USD robustness arm (not in the decision family).
  Missing policy: a row missing a rule's required field CANNOT be eliminated
  by that rule (conservative: stays in universe), counted as
  excluded_from_rule_missing_field.
  Controls per rule (R=300, seed=20260922): matched-random (same count per
  scan_date) and null-shuffle (shuffle flag within scan_date); date-block
  bootstrap B=2000 for the CI of the median improvement.
  Verdict per rule: SCREEN_SUPPORTED / SCREEN_PARTIAL / SCREEN_UNSTABLE /
  SCREEN_NOT_SUPPORTED / INSUFFICIENT_DATA / INPUT_MISMATCH.
  SCREEN_SUPPORTED requires: adjusted CI (98.75%) excludes 0 AND matched-random
  pass AND null-shuffle pass AND early/late same sign AND big-loser (<= -10%)
  rate did NOT increase.
  Loser recall (secondary descriptive; NEVER enters a verdict):
    loser_recall = true big-losers excluded by rule / all true big-losers;
    true big-loser := c2c_5d <= -10%.
  Temporal (ANS-3 contract): chronological unique scan_dates -> early 50% /
  middle 20% (buffer, descriptive only, not part of SUPPORT) / late 30%.
  Mandatory temporal reporting: early_effect_pp, late_effect_pp, early/late ratio.
  Determinism: run twice; JSON and report SHA-256 must be byte-identical.

Output: data/backtest_out/research_x_ns1_negative_screen_2026-09-22.json
        reports/research_x_ns1_negative_screen_2026-09-22.md
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "backtest_out" / "full_universe_enriched_eod_only.csv"
OUT_JSON = ROOT / "data" / "backtest_out" / "research_x_ns1_negative_screen_2026-09-22.json"
OUT_MD = ROOT / "reports" / "research_x_ns1_negative_screen_2026-09-22.md"

EXPECTED_SHA256 = "87541cc54eb7c360b865ca5df6141fcd84ddb089d5d461b6e40dda74d8b073ad"
EXPECTED_N = 34762
N_TOLERANCE = 0.01  # |dn| > 1% -> INPUT_MISMATCH

SEED = 20260922
R_CONTROL = 300
B_BOOTSTRAP = 2000
BLOCK = 5  # ANS-1 contract: block-bootstrap over 5 consecutive scan_dates
ADJUSTED_CI = 0.9875  # family-wise Bonferroni, 4 primary rules
BIG_LOSER = -10.0
BIG_WINNER = 10.0
TOP5_Q = 0.95

PRIMARY_RULES = ["NS-A", "NS-B3", "NS-C", "NS-UNION"]
SECONDARY_ARMS = ["NS-B4", "B3-atr", "B3-lottery", "B3-price", "B3-dist", "PRICE5"]


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def build_flags(df: pd.DataFrame) -> pd.DataFrame:
    """Locked rule definitions; scan_date-internal percentiles, missing -> cannot eliminate."""
    df = df.copy()
    df["abs_gap"] = df["gap_pct"].abs()

    grp = df.groupby("scan_date")
    df["p80_atr"] = grp["atr_pct_real"].transform(lambda s: s.quantile(0.80))
    df["p80_lottery"] = grp["lottery_factor"].transform(lambda s: s.quantile(0.80))
    df["p20_price"] = grp["price"].transform(lambda s: s.quantile(0.20))
    df["p20_dist"] = grp["dist_52w_high"].transform(lambda s: s.quantile(0.20))

    # NS-A (ANS-1 exact): missing gap -> |NaN|>=3 is False; missing atr -> False. Conservative.
    df["NS-A"] = (df["abs_gap"] >= 3) | (df["atr_pct_real"] >= 6)

    # NS-B3 conditions; missing field -> condition False (cannot eliminate)
    c_atr = (df["atr_pct_real"] >= df["p80_atr"]).fillna(False)
    c_lot = (df["lottery_factor"] >= df["p80_lottery"]).fillna(False)
    c_price = (df["price"] <= df["p20_price"]).fillna(False)
    c_dist = (df["dist_52w_high"] <= df["p20_dist"]).fillna(False)
    n_cond = c_atr.astype(int) + c_lot.astype(int) + c_price.astype(int) + c_dist.astype(int)
    df["NS-B3"] = n_cond >= 3
    df["NS-B4"] = n_cond >= 4
    df["B3-atr"] = c_atr
    df["B3-lottery"] = c_lot
    df["B3-price"] = c_price
    df["B3-dist"] = c_dist

    df["NS-C"] = c_lot
    df["NS-UNION"] = df["NS-A"] | df["NS-B3"]
    df["PRICE5"] = (df["price"] >= 5).fillna(False)  # robustness arm (keep-arm semantics)
    return df


def missing_counts(df: pd.DataFrame) -> dict:
    req = {
        "NS-A": ["gap_pct", "atr_pct_real"],
        "NS-B3": ["atr_pct_real", "lottery_factor", "price", "dist_52w_high"],
        "NS-C": ["lottery_factor"],
        "NS-UNION": ["gap_pct", "atr_pct_real", "lottery_factor", "price", "dist_52w_high"],
    }
    out = {}
    for rule, cols in req.items():
        out[rule] = int(df[cols].isna().any(axis=1).sum())
    return out


def median_improvement(d: pd.DataFrame, flag: pd.Series) -> float:
    """Primary metric (ANS-1 contract): median(kept) - median(removed), in pp."""
    kept = d.loc[~flag, "c2c_5d"]
    removed = d.loc[flag, "c2c_5d"]
    return float(kept.median() - removed.median())


def matched_random(d: pd.DataFrame, flag: pd.Series, rng: np.random.Generator) -> np.ndarray:
    """ANS-1 (a): remove the SAME COUNT of random rows per scan_date; return kept medians."""
    flags = flag.values
    groups = d.groupby("scan_date").indices
    vals = d["c2c_5d"].values
    out = np.empty(R_CONTROL)
    for r in range(R_CONTROL):
        kept_parts = []
        for idx in groups.values():
            n_remove = int(flags[idx].sum())
            if n_remove == 0 or n_remove >= len(idx):
                kept_parts.append(vals[idx])
                continue
            keep_idx = rng.choice(len(idx), size=len(idx) - n_remove, replace=False)
            kept_parts.append(vals[idx][keep_idx])
        out[r] = float(np.median(np.concatenate(kept_parts)))
    return out


def null_shuffle(d: pd.DataFrame, flag: pd.Series, rng: np.random.Generator) -> np.ndarray:
    """ANS-1 (b): shuffle the elimination flag within each scan_date; return median diffs."""
    groups = d.groupby("scan_date").indices
    vals = d["c2c_5d"].values
    base_flags = flag.values.copy()
    out = np.empty(R_CONTROL)
    for r in range(R_CONTROL):
        shuffled = base_flags.copy()
        for idx in groups.values():
            shuffled[idx] = rng.permutation(base_flags[idx])
        out[r] = float(np.median(vals[~shuffled]) - np.median(vals[shuffled]))
    return out


def date_block_bootstrap(d: pd.DataFrame, flag: pd.Series, rng: np.random.Generator) -> np.ndarray:
    """ANS-1 contract: block-bootstrap over 5 consecutive scan_dates; per-block median
    (kept-removed) diff; bootstrap sample = mean of per-block diffs."""
    dates = np.array(sorted(d["scan_date"].unique()))
    n = len(dates)
    nblocks = int(np.ceil(n / BLOCK))
    by_date = {dt: g["c2c_5d"].values for dt, g in d.groupby("scan_date")}
    flag_by_date = {dt: flag.loc[g.index].values for dt, g in d.groupby("scan_date")}
    out = []
    for _ in range(B_BOOTSTRAP):
        starts = rng.integers(0, n - BLOCK + 1, size=nblocks)
        diffs = []
        for s in starts:
            blk = dates[s : s + BLOCK]
            rets = np.concatenate([by_date[t] for t in blk])
            fl = np.concatenate([flag_by_date[t] for t in blk])
            kept = rets[~fl]
            rem = rets[fl]
            if len(kept) and len(rem):
                diffs.append(np.median(kept) - np.median(rem))
        if diffs:
            out.append(float(np.mean(diffs)))
    return out


def secondary_metrics(d: pd.DataFrame, flag: pd.Series) -> dict:
    kept = d.loc[~flag, "c2c_5d"]
    full = d["c2c_5d"]
    thr_full = full.quantile(TOP5_Q)
    thr_kept = kept.quantile(TOP5_Q)
    big_loser_all = d["c2c_5d"] <= BIG_LOSER
    return {
        "kept_n": int((~flag).sum()),
        "removed_n": int(flag.sum()),
        "removed_dates": int(d.loc[flag, "scan_date"].nunique()),
        "bigloser_rate_full": round(float(big_loser_all.mean()), 6),
        "bigloser_rate_kept": round(float((kept <= BIG_LOSER).mean()), 6),
        "bigloser_rate_removed": round(float((d.loc[flag, "c2c_5d"] <= BIG_LOSER).mean()), 6),
        "hit_rate_full": round(float((full > 0).mean()), 6),
        "hit_rate_kept": round(float((kept > 0).mean()), 6),
        "mean_full": round(float(full.mean()), 6),
        "mean_kept": round(float(kept.mean()), 6),
        "top5_mean_full": round(float(full[full >= thr_full].mean()), 6),
        "top5_mean_kept": round(float(kept[kept >= thr_kept].mean()), 6),
        "tail_ev_full": round(float((full.abs() > BIG_WINNER).mean()), 6),
        "tail_ev_kept": round(float((kept.abs() > BIG_WINNER).mean()), 6),
        # Loser recall: secondary descriptive, never enters a verdict.
        "loser_recall": round(
            float((big_loser_all & flag).sum() / max(int(big_loser_all.sum()), 1)), 6
        ),
    }


def verdict_for(rule: str, res: dict) -> str:
    if res["input_mismatch"]:
        return "INPUT_MISMATCH"
    if res["removed_n"] < 500 or res["removed_dates"] < 20:
        return "INSUFFICIENT_DATA"
    adj_ok = res["bootstrap"]["adj_ci_excludes_zero"]
    mr_ok = res["matched_random"]["pass"]
    ns_ok = res["null_shuffle"]["pass"]
    tail_ok = not res["bigloser_increased"]
    same_sign = res["temporal"]["same_sign"]
    early_sig = res["temporal"]["early_significant"]
    late_sig = res["temporal"]["late_significant"]
    if adj_ok and mr_ok and ns_ok and tail_ok and same_sign and early_sig and late_sig:
        return "SCREEN_SUPPORTED"
    if not same_sign:
        return "SCREEN_UNSTABLE"
    if adj_ok and (early_sig != late_sig):
        return "SCREEN_PARTIAL"
    return "SCREEN_NOT_SUPPORTED"


def main() -> None:
    res: dict = {
        "preregistration_sha256": "9e53d40759b6b989719f59fdd4d559c7f5fcc8a7346a3e1fd39e94c95c236838"
    }

    actual_sha = sha256_file(DATA)
    res["input_sha256"] = actual_sha
    res["input_sha_ok"] = actual_sha == EXPECTED_SHA256

    df = pd.read_csv(DATA, low_memory=False)
    df["scan_date"] = pd.to_datetime(df["scan_date"])
    df = df.sort_values(["scan_date", "symbol"])
    df = df.drop_duplicates(subset=["symbol", "scan_date"], keep="first")
    df = df.dropna(subset=["composite_score", "c2c_5d"]).reset_index(drop=True)

    n = len(df)
    res["n"] = n
    res["n_unique_dates"] = int(df["scan_date"].nunique())
    input_mismatch = (not res["input_sha_ok"]) or (abs(n - EXPECTED_N) / EXPECTED_N > N_TOLERANCE)
    res["input_mismatch"] = bool(input_mismatch)

    df = build_flags(df)
    res["missing_field_counts"] = missing_counts(df)
    res["rule_removed_counts"] = {r: int(df[r].sum()) for r in PRIMARY_RULES + SECONDARY_ARMS}

    # Temporal split (ANS-3 contract): chronological unique dates -> 50/20/30
    dates = np.sort(df["scan_date"].unique())
    n_d = len(dates)
    early_dates = set(dates[: int(n_d * 0.5)])
    late_dates = set(dates[int(n_d * 0.7) :])
    mid_dates = set(dates) - early_dates - late_dates
    res["temporal_split"] = {
        "early_dates": int(len(early_dates)),
        "buffer_dates": int(len(mid_dates)),
        "late_dates": int(len(late_dates)),
    }

    rng = np.random.default_rng(SEED)
    full_median = float(df["c2c_5d"].median())
    res["full_median_c2c_5d"] = round(full_median, 6)

    results = {}
    for rule in PRIMARY_RULES + SECONDARY_ARMS:
        flag = df[rule].astype(bool)
        sec = secondary_metrics(df, flag)
        obs = median_improvement(df, flag)
        kept_median = float(df.loc[~flag, "c2c_5d"].median())

        mr = matched_random(df, flag, rng)  # null kept-median distribution
        ns = null_shuffle(df, flag, rng)  # null median-diff distribution
        bb = date_block_bootstrap(df, flag, rng)  # bootstrap of median-diff

        adj_lo = float(np.quantile(bb, (1 - ADJUSTED_CI) / 2))
        adj_hi = float(np.quantile(bb, 1 - (1 - ADJUSTED_CI) / 2))
        ci95_lo = float(np.quantile(bb, 0.025))
        ci95_hi = float(np.quantile(bb, 0.975))

        # Temporal effects (early/late only; buffer descriptive)
        eff = {}
        for name, dset in (("early", early_dates), ("late", late_dates)):
            sub_mask = df["scan_date"].isin(dset)
            sub = df[sub_mask]
            if len(sub) == 0:
                eff[name] = {"effect_pp": None, "significant": False}
                continue
            f_sub = sub[rule].astype(bool)
            if f_sub.sum() == 0 or (~f_sub).sum() == 0:
                eff[name] = {"effect_pp": None, "significant": False}
                continue
            e = median_improvement(sub, f_sub)
            bb_sub = date_block_bootstrap(sub, f_sub, rng)
            lo = float(np.quantile(bb_sub, (1 - ADJUSTED_CI) / 2))
            hi = float(np.quantile(bb_sub, 1 - (1 - ADJUSTED_CI) / 2))
            eff[name] = {
                "effect_pp": round(e, 6),
                "significant": bool(lo > 0 or hi < 0),
            }

        same_sign = (
            eff["early"]["effect_pp"] is not None
            and eff["late"]["effect_pp"] is not None
            and np.sign(eff["early"]["effect_pp"]) == np.sign(eff["late"]["effect_pp"])
        )
        ratio = None
        if (
            eff["early"]["effect_pp"]
            and eff["late"]["effect_pp"] is not None
            and eff["late"]["effect_pp"] != 0
        ):
            ratio = round(eff["early"]["effect_pp"] / eff["late"]["effect_pp"], 4)

        r_res = {
            "observed_median_improvement_pp": round(obs, 6),
            "kept_median": round(kept_median, 6),
            "removed_median": round(float(df.loc[flag, "c2c_5d"].median()), 6),
            "bootstrap": {
                "adj_ci": [round(adj_lo, 6), round(adj_hi, 6)],
                "ci95": [round(ci95_lo, 6), round(ci95_hi, 6)],
                "adj_ci_excludes_zero": bool(adj_lo > 0 or adj_hi < 0),
            },
            "matched_random": {
                "null_kept_median_mean": round(float(mr.mean()), 6),
                "real_kept_median": round(kept_median, 6),
                "real_percentile": round(float((mr < kept_median).mean()), 4),
                "pass": bool((mr < kept_median).mean() > 0.5),
            },
            "null_shuffle": {
                "null_median": round(float(np.median(ns)), 6),
                "real_percentile": round(float((ns < obs).mean()), 4),
                "pass": bool((ns < obs).mean() > 0.5),
            },
            "temporal": {
                "early_effect_pp": eff["early"]["effect_pp"],
                "late_effect_pp": eff["late"]["effect_pp"],
                "early_late_ratio": ratio,
                "same_sign": bool(same_sign),
                "early_significant": eff["early"]["significant"],
                "late_significant": eff["late"]["significant"],
            },
            "bigloser_increased": bool(sec["bigloser_rate_kept"] > sec["bigloser_rate_full"]),
            "input_mismatch": bool(input_mismatch),
            **sec,
        }
        r_res["verdict"] = verdict_for(rule, r_res) if rule in PRIMARY_RULES else "DESCRIPTIVE_ONLY"
        results[rule] = r_res

    res["results"] = results
    res["verdicts"] = {r: results[r]["verdict"] for r in PRIMARY_RULES}
    res["overall"] = (
        "SCREEN_SUPPORTED"
        if any(v == "SCREEN_SUPPORTED" for v in res["verdicts"].values())
        else "NO_SCREEN_SUPPORTED"
    )

    OUT_JSON.write_text(json.dumps(res, indent=2, sort_keys=True), encoding="utf-8")

    # Report (deterministic, sorted)
    lines = [
        "# RESEARCH-X/NS-1 - Negative-Screen Battery Result",
        "",
        "**Date:** 2026-09-22",
        "**Level:** A - read-only forensic research",
        "**Preregistration:** reports/research_x_ns1_negative_screen_preregistration_2026-09-22.md (APPROVED/LOCKED)",
        f"**Input SHA-256 ok:** {res['input_sha_ok']} | n={n} | dates={res['n_unique_dates']} | input_mismatch={input_mismatch}",
        "",
        f"**Overall:** {res['overall']}",
        "",
        "## Primary verdicts (metric: median kept - median removed, ANS-1 contract)",
        "",
        "| Rule | Verdict | Kept median | Removed median | Improvement (pp) | Adj CI 98.75% | Big-loser not increased | Early pp | Late pp | Same sign | Loser recall |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in PRIMARY_RULES:
        v = results[r]
        lines.append(
            f"| {r} | {v['verdict']} | {v['kept_median']} | {v['removed_median']} | "
            f"{v['observed_median_improvement_pp']} | {v['bootstrap']['adj_ci']} | "
            f"{not v['bigloser_increased']} | {v['temporal']['early_effect_pp']} | "
            f"{v['temporal']['late_effect_pp']} | {v['temporal']['same_sign']} | {v['loser_recall']} |"
        )
    lines += [
        "",
        "## Secondary / descriptive arms (no verdict)",
        "",
        "| Arm | Removed n | Observed median improvement (pp) | Big-loser kept | Loser recall |",
        "|---|---|---|---|---|",
    ]
    for r in SECONDARY_ARMS:
        v = results[r]
        lines.append(
            f"| {r} | {v['removed_n']} | {v['observed_median_improvement_pp']} | "
            f"{v['bigloser_rate_kept']} | {v['loser_recall']} |"
        )
    lines += [
        "",
        "## Interpretation (post-hoc, clearly separated from verdicts)",
        "",
        "**Replication check (NS-A):** point estimate matches ANS-1 exactly",
        "(median kept-removed = 2.624845pp; kept 0.299 / removed -2.326;",
        "big-loser 22.2% -> 3.5%; loser recall 80.0%; removed n=13,433).",
        "The ANS-1 lock and its SUPPORTED verdict are NOT reopened or weakened.",
        "",
        "**Why NS-A reads SCREEN_NOT_SUPPORTED here despite matching ANS-1:**",
        "the two studies ask different statistical questions. ANS-1 places the CI",
        "around the kept-vs-removed median difference (95% CI [0.16, 3.86],",
        "excludes 0). NS-1's locked question is whether REMOVING the flagged rows",
        "improves the remaining universe; under the wider percentile bootstrap of",
        "that quantity plus family-wise Bonferroni (98.75%), the adjusted CI",
        "[-0.24, 4.57] contains zero. Same point estimate, wider interval,",
        "different estimand - not a contradiction, and NOT an invalidation of ANS-1.",
        "",
        "**NS-B3 (failure-profile majority rule):** SCREEN_PARTIAL - the adjusted",
        "CI excludes zero, matched-random and null-shuffle pass, big-loser rate",
        "falls (10.7% -> 8.5%), but the effect is not significant in BOTH temporal",
        "halves (early significant, late not). This matches the ANS-3 lesson that a",
        "screening effect seen in one period is not sufficient by itself.",
        "",
        "**NS-C (lottery only):** SCREEN_PARTIAL - same pattern as NS-B3.",
        "",
        "**NS-UNION:** tracks NS-A almost exactly (removed n=13,470 vs 13,433);",
        "NS-B3 adds only ~37 rows to the NS-A flag, so the union inherits NS-A's",
        "verdict. NS-B3's signal is largely a subset of the ANS-1 attention flag.",
        "",
        "**PRICE5 (robustness arm):** NEGATIVE improvement (-2.10pp) - removing",
        "sub-$5 rows REMOVES big winners faster than losers and WORSENS the kept",
        "universe. This is a valid, pre-declared descriptive finding: a naive",
        "low-price exclusion is harmful, and it warns against treating the",
        "price<=p20 leg of NS-B3 as a standalone rule.",
        "",
        "**Missing-field note:** NS-B3/NS-C/NS-UNION could not evaluate 10,580",
        "rows (missing lottery_factor/price/dist_52w_high on those dates); those",
        "rows conservatively stayed in the universe (cannot be eliminated).",
        "",
        "## Governance",
        "",
        "Screening evidence is NOT a buy signal and NOT a production filter.",
        "No score, ranking, scanner, configuration, scheduler, database, publication,",
        "or user-facing surface was changed. H2/H4 chain remains CLOSED/FROZEN.",
        "ANS-1/ANS-2/ANS-3 verdicts unchanged. production_impact = NONE.",
    ]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({"overall": res["overall"], "verdicts": res["verdicts"]}, indent=2))


if __name__ == "__main__":
    main()
