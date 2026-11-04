"""PRF_03_universe.py - R7 selected-vs-universe comparison on non-locked dates only (read-only).

Outcome columns of the CSV are kept only for rows with scan_date <= 2025-12-31 (filtered per chunk);
later rows contribute metadata (dates, counts) only. Return definition: CSV c2c_5d for both groups
(NOT the barrier return). Writes only <audit>/data/PRF_universe_compare.json.
"""
import json
import os
import sqlite3

import numpy as np
import pandas as pd

ROOT = r"C:\Users\meric\Borsa"
CSV = os.path.join(ROOT, "data", "backtest_out", "full_universe_enriched_labeled.csv")
DB_URI = "file:C:/Users/meric/Borsa/data/finpilot.db?mode=ro"
OUT = os.path.join(ROOT, "reports", "scanner_intelligence_audit_v1_2026-10-19", "data", "PRF_universe_compare.json")
NONLOCKED_MAX = "2025-12-31"
SEED = 20261019
B = 5000


def r4(x):
    if x is None:
        return None
    x = float(x)
    return None if np.isnan(x) else round(x, 4)


def describe(x):
    x = pd.to_numeric(pd.Series(x), errors="coerce").dropna()
    q = x.quantile([0, 0.01, 0.5, 0.99, 1]).round(4).tolist()
    return {"n": int(x.size), "mean": r4(x.mean()), "q_0_1_50_99_100": q, "abs_gt_100": int((x.abs() > 100).sum())}


def day_cluster_ci(x, days):
    x = np.asarray(x, float)
    codes, uniq = pd.factorize(pd.Series(days), sort=True)
    G = len(uniq)
    sums = np.bincount(codes, weights=x, minlength=G)
    cnts = np.bincount(codes, minlength=G)
    rng = np.random.default_rng(SEED)
    bs = np.empty(B)
    for b in range(B):
        idx = rng.integers(0, G, G)
        bs[b] = sums[idx].sum() / cnts[idx].sum()
    return {"n": int(x.size), "days": int(G), "B": B, "seed": SEED, "mean": r4(x.mean()),
            "ci95": [r4(np.percentile(bs, 2.5)), r4(np.percentile(bs, 97.5))]}


def compare(ud, sel_keys, eod_only, liq_only, winsor):
    v = ud[ud["c2c_5d"].notna()].copy()
    if eod_only:
        v = v[v["eod"]]
    if winsor:
        lo, hi = v["c2c_5d"].quantile([0.01, 0.99])
        v["c2c_5d"] = v["c2c_5d"].clip(lo, hi)
    v["sel"] = [(s, d) in sel_keys for s, d in zip(v["symbol"], v["scan_date"])]
    s = v[v["sel"]]
    uni = v[~v["sel"]]
    if liq_only:
        uni = uni[uni["liq"]]
    rows = []
    for d, sg in s.groupby("scan_date"):
        ug = uni.loc[uni["scan_date"] == d, "c2c_5d"].values
        if ug.size < 20:
            continue
        sv = sg["c2c_5d"].values
        rows.append((d, sv.size, sv.mean(), np.median(sv), ug.size, ug.mean(), np.median(ug)))
    t = pd.DataFrame(rows, columns=["date", "n_sel", "sel_mean", "sel_med", "n_uni", "uni_mean", "uni_med"])
    if t.empty:
        return {"days": 0}
    s2 = s.merge(t[["date", "uni_mean", "uni_med"]], left_on="scan_date", right_on="date")
    ex_mean = (s2["c2c_5d"] - s2["uni_mean"]).values
    ex_med = (s2["c2c_5d"] - s2["uni_med"]).values
    return {
        "days": int(len(t)), "n_sel": int(len(s2)), "n_uni_rows": int(t["n_uni"].sum()),
        "sel_mean": r4(s2["c2c_5d"].mean()), "sel_median": r4(s2["c2c_5d"].median()),
        "uni_mean_weighted_by_sel": r4(np.average(t["uni_mean"], weights=t["n_sel"])),
        "uni_median_weighted_by_sel": r4(np.average(t["uni_med"], weights=t["n_sel"])),
        "excess_vs_same_day_uni_mean": day_cluster_ci(ex_mean, s2["scan_date"].values),
        "excess_vs_same_day_uni_median_median": r4(np.median(ex_med)),
        "share_excess_vs_same_day_uni_median_gt0_pct": r4(100 * (ex_med > 0).mean()),
        "per_day_mean_diff_equal_weight": day_cluster_ci((t["sel_mean"] - t["uni_mean"]).values, t["date"].values),
        "per_day_median_diff_median": r4(np.median(t["sel_med"] - t["uni_med"])),
        "days_sel_mean_gt_uni_mean": int((t["sel_mean"] > t["uni_mean"]).sum()),
        "largest_days_n_sel": t.sort_values("n_sel", ascending=False).head(3)[["date", "n_sel"]].values.tolist(),
    }


def main():
    info = {"csv": CSV, "nonlocked_max_scan_date": NONLOCKED_MAX, "return_definition": "CSV c2c_5d (not barrier)"}
    meta = pd.read_csv(CSV, usecols=["symbol", "scan_date", "scan_ts", "label_entry_basis"], dtype=str)
    meta["scan_date"] = meta["scan_date"].str.slice(0, 10)
    info["rows"] = int(len(meta))
    info["date_min_max"] = [meta["scan_date"].min(), meta["scan_date"].max()]
    info["rows_by_month"] = meta["scan_date"].str.slice(0, 7).value_counts().sort_index().to_dict()
    info["label_entry_basis_counts"] = meta["label_entry_basis"].fillna("NULL").value_counts().to_dict()
    info["rows_nonlocked"] = int((meta["scan_date"] <= NONLOCKED_MAX).sum())
    info["dates_nonlocked"] = int(meta.loc[meta["scan_date"] <= NONLOCKED_MAX, "scan_date"].nunique())

    keep = []
    cols = ["symbol", "scan_date", "scan_ts", "label_entry_basis", "liquidity_ok", "c2c_5d"]
    for ch in pd.read_csv(CSV, usecols=cols, dtype=str, chunksize=20000):
        ch["scan_date"] = ch["scan_date"].str.slice(0, 10)
        keep.append(ch[ch["scan_date"] <= NONLOCKED_MAX])
    u = pd.concat(keep, ignore_index=True)
    u["c2c_5d"] = pd.to_numeric(u["c2c_5d"], errors="coerce")
    u["eod"] = u["label_entry_basis"].fillna("") == "eod_close"
    u["liq"] = u["liquidity_ok"].astype(str).str.lower().isin(["true", "1", "1.0"])
    eod = u[u["eod"] & u["c2c_5d"].notna()]
    dup = eod.groupby(["symbol", "scan_date"])["c2c_5d"].agg(["count", "min", "max"])
    dup = dup[dup["count"] > 1]
    info["eod_dup_groups"] = int(len(dup))
    info["eod_dup_max_absdiff"] = r4((dup["max"] - dup["min"]).max()) if len(dup) else 0.0
    ud = u.sort_values(["symbol", "scan_date", "eod", "scan_ts"], ascending=[True, True, False, True])
    ud = ud.drop_duplicates(["symbol", "scan_date"])
    info["dedup_symbol_days"] = int(len(ud))
    info["dedup_eod_share"] = r4(ud["eod"].mean())
    info["c2c_5d_nonlocked_dedup"] = describe(ud["c2c_5d"])

    con = sqlite3.connect(DB_URI, uri=True)
    con.execute("PRAGMA query_only=ON")
    a = pd.read_sql_query(
        "SELECT symbol, resolved_status_barrier, resolved_pct_barrier, payload_json FROM signals_archive", con)
    con.close()
    a["signal_date"] = a["payload_json"].apply(lambda s: str(json.loads(s).get("signal_date") or "")[:10] if s else "")
    a = a[a["resolved_status_barrier"].isin(["resolved_win", "resolved_loss"]) & a["resolved_pct_barrier"].notna()]
    sel = a[(a["signal_date"] != "") & (a["signal_date"] <= NONLOCKED_MAX)]
    info["selected_decided_nonlocked_rows"] = int(len(sel))
    info["selected_unique_symbol_days"] = int(sel[["symbol", "signal_date"]].drop_duplicates().shape[0])
    info["selected_dates"] = int(sel["signal_date"].nunique())
    sel_keys = set(zip(sel["symbol"], sel["signal_date"]))
    ud_keys = set(zip(ud["symbol"], ud["scan_date"]))
    ud_eod_keys = set(zip(ud.loc[ud["eod"], "symbol"], ud.loc[ud["eod"], "scan_date"]))
    info["selected_keys_found_in_csv"] = len(sel_keys & ud_keys)
    info["selected_keys_found_in_csv_eod"] = len(sel_keys & ud_eod_keys)
    prev_bd = {(s, (pd.Timestamp(d) - pd.offsets.BDay(1)).strftime("%Y-%m-%d") if pd.Timestamp(d).weekday() >= 5 else d)
               for s, d in sel_keys}
    info["selected_keys_found_weekend_to_prev_bday"] = len(prev_bd & ud_keys)
    m = sel.drop_duplicates(["symbol", "signal_date"]).merge(
        ud[["symbol", "scan_date", "c2c_5d", "eod"]], left_on=["symbol", "signal_date"], right_on=["symbol", "scan_date"])
    m = m[m["eod"] & m["c2c_5d"].notna()]
    info["matched_eod_selected_barrier_vs_c2c5d"] = {"n": int(len(m)), "barrier_mean": r4(m["resolved_pct_barrier"].mean()),
                                                     "c2c_5d_mean": r4(m["c2c_5d"].mean()),
                                                     "c2c_5d_median": r4(m["c2c_5d"].median())}
    info["compare_primary_eod"] = compare(ud, sel_keys, True, False, False)
    info["compare_eod_liquidity_ok_universe"] = compare(ud, sel_keys, True, True, False)
    info["compare_eod_winsor_1_99"] = compare(ud, sel_keys, True, False, True)
    info["compare_all_basis"] = compare(ud, sel_keys, False, False, False)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(info, fh, indent=1, default=str)
    print(json.dumps(info, default=str, separators=(",", ":")))


if __name__ == "__main__":
    main()
