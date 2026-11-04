"""PRF_02_analysis.py - R7 gross barrier-return analysis of signals_archive (read-only).

Writes only <audit>/data/PRF_analysis.json and <audit>/data/PRF_daily_cohorts.csv.
All returns are gross simulated barrier outcomes (percent); nothing here is net or expectancy.
"""
import json
import os
import sqlite3

import numpy as np
import pandas as pd
from scipy import stats

ROOT = r"C:\Users\meric\Borsa"
DB_URI = "file:C:/Users/meric/Borsa/data/finpilot.db?mode=ro"
AUD = os.path.join(ROOT, "reports", "scanner_intelligence_audit_v1_2026-10-19", "data")
SECTOR_MAP = os.path.join(ROOT, "data", "backtest_out", "sector_map_full.csv")
SEED = 20261019
B_MAIN = 5000
B_SUB = 2000
COSTS = [0.10, 0.25, 0.55, 1.00]
C1 = "2026-05-21"
DECIDED = ("resolved_win", "resolved_loss")


def r4(x):
    if x is None:
        return None
    x = float(x)
    return None if np.isnan(x) else round(x, 4)


def summ(r):
    r = np.asarray(r, float)
    pos, neg = r[r > 0], r[r < 0]
    return {
        "n": int(r.size), "mean": r4(r.mean()), "median": r4(np.median(r)), "sum": r4(r.sum()),
        "std": r4(r.std(ddof=1)), "win_rate_pct": r4(100 * (r > 0).mean()),
        "avg_win": r4(pos.mean()) if pos.size else None, "avg_loss": r4(neg.mean()) if neg.size else None,
        "pf": r4(pos.sum() / abs(neg.sum())) if neg.size else None,
        "skew": r4(stats.skew(r, bias=False)), "exkurt": r4(stats.kurtosis(r, bias=False)),
    }


def groups_of(r, keys):
    codes, uniq = pd.factorize(pd.Series(keys), sort=True)
    order = np.argsort(codes, kind="mergesort")
    rs, cs = r[order], codes[order]
    starts = np.searchsorted(cs, np.arange(len(uniq)))
    ends = np.r_[starts[1:], rs.size]
    return uniq, [rs[s:e] for s, e in zip(starts, ends)]


def cluster_boot(r, keys, B, seed, median=True):
    r = np.asarray(r, float)
    _, grp = groups_of(r, keys)
    sums = np.array([g.sum() for g in grp])
    cnts = np.array([g.size for g in grp])
    G = len(grp)
    rng = np.random.default_rng(seed)
    means = np.empty(B)
    meds = np.empty(B)
    for b in range(B):
        idx = rng.integers(0, G, G)
        means[b] = sums[idx].sum() / cnts[idx].sum()
        if median:
            meds[b] = np.median(np.concatenate([grp[i] for i in idx]))
    out = {"clusters": int(G), "B": B, "seed": seed,
           "mean_ci95": [r4(np.percentile(means, 2.5)), r4(np.percentile(means, 97.5))],
           "mean_boot_se": r4(means.std(ddof=1)), "share_boot_mean_le_0": r4((means <= 0).mean())}
    if median:
        out["median_ci95"] = [r4(np.percentile(meds, 2.5)), r4(np.percentile(meds, 97.5))]
        out["share_boot_median_ge_0"] = r4((meds >= 0).mean())
    return out


def loo_days(r, keys):
    d = pd.DataFrame({"r": r, "k": keys})
    g = d.groupby("k")["r"].agg(["sum", "count"])
    S, N = d["r"].sum(), len(d)
    base = S / N
    loo = (S - g["sum"]) / (N - g["count"])
    infl = (base - loo).sort_values(ascending=False)
    out = {"days": int(len(g)), "base_mean": r4(base),
           "loo_min": [str(loo.idxmin()), r4(loo.min()), int(g.loc[loo.idxmin(), "count"])],
           "loo_max": [str(loo.idxmax()), r4(loo.max()), int(g.loc[loo.idxmax(), "count"])],
           "days_flip_sign": int((np.sign(loo) != np.sign(base)).sum()),
           "rows_per_day_min_median_max": [int(g["count"].min()), float(g["count"].median()), int(g["count"].max())]}
    seq = {}
    for k in (1, 2, 3, 5, 10):
        drop = infl.index[:k].tolist()
        m = d.loc[~d["k"].isin(drop), "r"]
        seq[str(k)] = {"dropped_first3": [str(x) for x in drop[:3]], "n": int(m.size), "mean": r4(m.mean()),
                       "median": r4(m.median())}
    out["drop_top_k_influential_days"] = seq
    top = g.sort_values("count", ascending=False).head(5)
    out["largest_days_n_mean"] = [[str(i), int(row["count"]), r4(row["sum"] / row["count"])] for i, row in top.iterrows()]
    out["top2_days_share_rows"] = r4(top["count"].head(2).sum() / N)
    return out


def split_table(dec, col, min_n=30):
    rows = []
    for v, g in dec.groupby(col, dropna=False):
        if len(g) < min_n:
            rows.append([str(v), int(len(g)), "n<30"])
            continue
        s = summ(g["r"].values)
        cb = cluster_boot(g["r"].values, g["signal_date"].values, B_SUB, SEED, median=False)
        rows.append([str(v), s["n"], cb["clusters"], s["mean"], s["median"], s["win_rate_pct"], s["pf"],
                     cb["mean_ci95"][0], cb["mean_ci95"][1]])
    return rows


def portfolio(dec, key):
    g = dec.groupby(key)["r"].agg(["mean", "count"]).sort_index()
    coh = g["mean"].values
    cum = np.r_[0.0, np.cumsum(coh)]
    res = {"cohorts": int(len(g)), "cohort_mean_of_means": r4(coh.mean()), "cohort_median": r4(np.median(coh)),
           "share_cohorts_positive": r4((coh > 0).mean()),
           "worst": [str(g["mean"].idxmin()), r4(coh.min()), int(g.loc[g["mean"].idxmin(), "count"])],
           "best": [str(g["mean"].idxmax()), r4(coh.max()), int(g.loc[g["mean"].idxmax(), "count"])],
           "cum_sum_pp": r4(cum[-1]), "mdd_additive_pp": r4((np.maximum.accumulate(cum) - cum).max())}
    for f in (1.0, 0.2, 0.1):
        eq = np.r_[1.0, np.cumprod(1 + f * coh / 100.0)]
        peak = np.maximum.accumulate(eq)
        res["compound_f_%.1f" % f] = {"final_multiple": r4(eq[-1]), "mdd_pct": r4(((peak - eq) / peak).max() * 100)}
    cnt = g["count"].values
    sh = cnt / cnt.sum()
    res["rows_per_cohort_min_med_max"] = [int(cnt.min()), float(np.median(cnt)), int(cnt.max())]
    res["top5_cohorts_share_rows"] = r4(np.sort(sh)[::-1][:5].sum())
    res["hhi_cohorts"] = r4((sh ** 2).sum())
    res["effective_cohorts"] = r4(1 / (sh ** 2).sum())
    return res, g


def sector_map():
    if not os.path.exists(SECTOR_MAP):
        return None
    sm = pd.read_csv(SECTOR_MAP)
    cols = {c.lower(): c for c in sm.columns}
    sym = cols.get("symbol")
    sec = next((cols[c] for c in ("etf", "sector_etf", "sector") if c in cols), None)
    if not sym or not sec:
        return None
    return dict(zip(sm[sym].astype(str), sm[sec].astype(str)))


def main():
    con = sqlite3.connect(DB_URI, uri=True)
    con.execute("PRAGMA query_only=ON")
    df = pd.read_sql_query(
        "SELECT id, symbol, ts, resolved_status_barrier, resolved_pct_barrier, payload_json FROM signals_archive", con)
    con.close()
    pl = df["payload_json"].apply(lambda s: json.loads(s) if s else {})
    df["signal_date"] = pl.apply(lambda d: str(d.get("signal_date") or "")[:10])
    df["added_date"] = pl.apply(lambda d: str(d.get("added_at") or "")[:10])
    df["ts_date"] = df["ts"].astype(str).str.slice(0, 10)
    df["source_model"] = pl.apply(lambda d: str(d.get("source_model")))
    df["regime_raw"] = pl.apply(lambda d: str(d.get("regime")) if "regime" in d else "MISSING")
    df["signal_label"] = pl.apply(lambda d: str(d.get("signal")))
    df["entry_price"] = pd.to_numeric(pl.apply(lambda d: d.get("entry_price")), errors="coerce")
    dec = df[df["resolved_status_barrier"].isin(DECIDED) & df["resolved_pct_barrier"].notna()].copy()
    dec["r"] = dec["resolved_pct_barrier"].astype(float)
    sd = pd.to_datetime(dec["signal_date"], errors="coerce")
    dec["lag_days"] = (pd.to_datetime(dec["ts_date"], errors="coerce") - sd).dt.days
    dec["entry_session"] = pd.Series([(t + pd.offsets.BDay(1)).strftime("%Y-%m-%d") for t in sd], index=dec.index)
    dec["month"] = dec["signal_date"].str.slice(0, 7)
    dec["weekday"] = sd.dt.day_name()
    dec["lag_bucket"] = np.select([dec["lag_days"].between(-1, 1), dec["lag_days"].between(2, 4), dec["lag_days"] >= 5],
                                  ["lag_-1_to_1", "lag_2_to_4", "lag_ge_5"], "lag_other")
    dec["price_band"] = np.select([dec["entry_price"] < 1, dec["entry_price"] < 5, dec["entry_price"] >= 5],
                                  ["lt_1", "1_to_5", "ge_5"], "missing")
    smap = sector_map()
    dec["sector_etf"] = dec["symbol"].map(smap).fillna("UNMAPPED") if smap else "NO_MAP"
    r = dec["r"].values
    n = r.size
    res = {"n_decided": int(n), "seed": SEED, "B_main": B_MAIN, "B_sub": B_SUB, "sector_map_used": bool(smap)}
    res["baseline"] = summ(r)
    res["distinct"] = {"signal_date": int(dec["signal_date"].nunique()), "ts_date": int(dec["ts_date"].nunique()),
                       "entry_session": int(dec["entry_session"].nunique()), "symbols": int(dec["symbol"].nunique())}
    res["signal_date_min_max"] = [dec["signal_date"].min(), dec["signal_date"].max()]
    res["lag_days_counts"] = {str(k): int(v) for k, v in dec["lag_days"].value_counts().sort_index().items()}
    res["lag_bucket_by_source"] = {k: {kk: int(vv) for kk, vv in v.items()}
                                   for k, v in pd.crosstab(dec["source_model"], dec["lag_bucket"]).to_dict().items()}
    res["weekday_signal_date"] = dec["weekday"].value_counts().to_dict()
    res["weekday_ts_date"] = pd.to_datetime(dec["ts_date"]).dt.day_name().value_counts().to_dict()

    order = np.argsort(-r, kind="mergesort")
    tails = {}
    for pct in (1, 5, 10):
        k = int(np.floor(pct / 100 * n))
        top, bot = r[order[:k]], r[order[n - k:]]
        tails["top_%d" % pct] = {"k": k, "cut": r4(top.min()), "share_net_sum": r4(top.sum() / r.sum()),
                                 "share_gross_pos": r4(top.sum() / r[r > 0].sum())}
        tails["bottom_%d" % pct] = {"k": k, "cut": r4(bot.max()), "share_net_sum": r4(bot.sum() / r.sum()),
                                    "share_gross_neg": r4(bot.sum() / r[r < 0].sum())}
    res["tails"] = tails
    rem = {}
    for pct in (1, 5):
        k = int(np.floor(pct / 100 * n))
        keep = np.sort(order[k:])
        s = summ(r[keep])
        s["cluster_signal_date"] = cluster_boot(r[keep], dec["signal_date"].values[keep], B_SUB, SEED)
        rem["excl_top_%d" % pct] = s
    res["removal"] = rem

    res["cluster_signal_date"] = cluster_boot(r, dec["signal_date"].values, B_MAIN, SEED)
    res["cluster_entry_session"] = cluster_boot(r, dec["entry_session"].values, B_MAIN, SEED)
    res["cluster_ts_date"] = cluster_boot(r, dec["ts_date"].values, B_MAIN, SEED)
    res["prior_repro_ts_date_B2000_seed20261014"] = cluster_boot(r, dec["ts_date"].values, 2000, 20261014, median=False)
    iid_se = r.std(ddof=1) / np.sqrt(n)
    res["iid_se_mean"] = r4(iid_se)
    res["design_effect_signal_date"] = r4((res["cluster_signal_date"]["mean_boot_se"] / iid_se) ** 2)
    res["design_effect_entry_session"] = r4((res["cluster_entry_session"]["mean_boot_se"] / iid_se) ** 2)

    res["loo_signal_date"] = loo_days(r, dec["signal_date"].values)
    res["loo_entry_session"] = loo_days(r, dec["entry_session"].values)
    res["loo_ts_date"] = loo_days(r, dec["ts_date"].values)

    cb = res["cluster_signal_date"]
    cost = []
    for c in COSTS:
        rc = r - c
        pos, neg = rc[rc > 0], rc[rc < 0]
        cost.append({"cost_pp": c, "mean_minus_cost": r4(rc.mean()), "median_minus_cost": r4(np.median(rc)),
                     "mean_ci95_minus_cost": [r4(cb["mean_ci95"][0] - c), r4(cb["mean_ci95"][1] - c)],
                     "share_r_gt_cost_pct": r4(100 * (r > c).mean()), "pf_after_cost": r4(pos.sum() / abs(neg.sum()))})
    res["cost_sensitivity"] = cost

    sub = {}
    for name, mask in (("lag_-1_to_1", dec["lag_bucket"].eq("lag_-1_to_1").values),
                       ("lag_ge_2", (dec["lag_days"] >= 2).values)):
        rr = r[mask]
        s = summ(rr)
        s["cluster_signal_date"] = cluster_boot(rr, dec["signal_date"].values[mask], B_SUB, SEED)
        s["mean_minus_cost"] = {str(c): r4(rr.mean() - c) for c in COSTS}
        s["days"] = int(dec["signal_date"].values[mask].size and pd.Series(dec["signal_date"].values[mask]).nunique())
        sub[name] = s
    res["lag_subsets"] = sub

    c1mask = np.array([max(a, b, c) > C1 for a, b, c in zip(dec["ts_date"], dec["signal_date"], dec["added_date"])])
    rr = r[~c1mask]
    s = summ(rr)
    s["cluster_signal_date"] = cluster_boot(rr, dec["signal_date"].values[~c1mask], B_SUB, SEED, median=False)
    s["excluded_rows"] = int(c1mask.sum())
    res["excl_c1_calendar_rows"] = s

    two = dec[dec["ts_date"].isin(["2026-03-01", "2026-03-03"])]
    res["prior_two_ts_dates"] = {"rows": int(len(two)), "distinct_signal_dates": int(two["signal_date"].nunique()),
                                 "signal_date_min_max": [two["signal_date"].min(), two["signal_date"].max()],
                                 "lag_counts": {str(k): int(v) for k, v in two["lag_days"].value_counts().sort_index().items()}}
    res["month_ts_date_n_mean"] = {m: [int(len(g)), r4(g["r"].mean())] for m, g in dec.groupby(dec["ts_date"].str.slice(0, 7))}
    res["month_signal_date_n_mean"] = {m: [int(len(g)), r4(g["r"].mean())] for m, g in dec.groupby("month")}

    res["splits_cols"] = ["group", "n", "days", "mean", "median", "win_rate_pct", "pf", "ci_lo", "ci_hi"]
    res["splits"] = {col: split_table(dec, col) for col in
                     ("source_model", "regime_raw", "signal_label", "month", "weekday", "price_band", "lag_bucket", "sector_etf")}

    res["dup_symbol_signal_date"] = int(dec.duplicated(["symbol", "signal_date"]).sum())
    ds = dec.sort_values(["symbol", "signal_date"])
    gap = pd.to_datetime(ds["signal_date"]).groupby(ds["symbol"]).diff().dt.days
    res["rows_same_symbol_prior_signal_within_7d"] = int((gap <= 7).sum())
    sy = dec.groupby("symbol")["r"].agg(["sum", "count"])
    res["symbol_concentration"] = {"symbols": int(len(sy)),
                                   "top10_by_rows_share_rows": r4(sy["count"].nlargest(10).sum() / n),
                                   "top10_by_sum_share_net_sum": r4(sy["sum"].nlargest(10).sum() / r.sum()),
                                   "hhi_rows": r4(((sy["count"] / n) ** 2).sum())}

    pf_sd, g_sd = portfolio(dec, "signal_date")
    pf_es, _ = portfolio(dec, "entry_session")
    res["portfolio_signal_date"] = pf_sd
    res["portfolio_entry_session"] = pf_es
    out = g_sd.reset_index().rename(columns={"mean": "cohort_mean_pct", "count": "n_signals"})
    out["cum_sum_pp"] = out["cohort_mean_pct"].cumsum().round(4)
    out["cohort_mean_pct"] = out["cohort_mean_pct"].round(4)
    out.to_csv(os.path.join(AUD, "PRF_daily_cohorts.csv"), index=False)
    with open(os.path.join(AUD, "PRF_analysis.json"), "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1, default=str)
    print(json.dumps(res, default=str, separators=(",", ":")))


if __name__ == "__main__":
    main()
