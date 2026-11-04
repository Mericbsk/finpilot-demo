"""PRF_01_profile.py - R7 read-only profile of signals_archive.

Writes only reports/scanner_intelligence_audit_v1_2026-10-19/data/PRF_profile.json.
Outcome statistics are computed only on rows outside the conservative C1 calendar
window (any candidate signal date > 2026-05-21); window rows get metadata counts only.
"""
import datetime as dt
import hashlib
import json
import os
import re
import sqlite3
from collections import Counter

import pandas as pd

ROOT = r"C:\Users\meric\Borsa"
DB = os.path.join(ROOT, "data", "finpilot.db")
DB_URI = "file:C:/Users/meric/Borsa/data/finpilot.db?mode=ro"
OUT = os.path.join(ROOT, "reports", "scanner_intelligence_audit_v1_2026-10-19", "data", "PRF_profile.json")
C1_BOUNDARY = "2026-05-21"
DATE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})")
RET_FIELDS = ["resolved_pct", "resolved_pct_t5", "resolved_pct_barrier"]
DECIDED = {"resolved_win", "resolved_loss"}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def describe(x):
    x = pd.to_numeric(pd.Series(x), errors="coerce").dropna()
    if x.empty:
        return {"n": 0}
    q = x.quantile([0, 0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99, 1]).round(4).tolist()
    return {"n": int(x.size), "mean": round(float(x.mean()), 4), "q_0_1_5_25_50_75_95_99_100": q,
            "abs_gt_50": int((x.abs() > 50).sum()), "abs_gt_100": int((x.abs() > 100).sum()),
            "share_abs_lt_1": round(float((x.abs() < 1).mean()), 4)}


def brief(x):
    x = pd.to_numeric(pd.Series(x), errors="coerce").dropna()
    if x.empty:
        return [0]
    return [int(x.size), round(float(x.min()), 4), round(float(x.median()), 4), round(float(x.max()), 4)]


def flatten(p):
    out = {}
    if not isinstance(p, dict):
        return out
    for k, v in p.items():
        if isinstance(v, dict):
            for k2, v2 in v.items():
                if not isinstance(v2, (dict, list)):
                    out[k + "." + k2] = v2
        elif not isinstance(v, list):
            out[k] = v
    return out


def first_key(keys, names):
    for name in names:
        if name in keys:
            return name
    return None


def main():
    info = {"started_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}
    files = {}
    for suf in ("", "-wal", "-shm", "-journal"):
        p = DB + suf
        if os.path.exists(p):
            st = os.stat(p)
            files["finpilot.db" + suf] = [st.st_size, dt.datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds")]
    info["db_files"] = files
    try:
        info["db_sha256_start"] = sha256(DB)
    except OSError as exc:
        info["db_sha256_start"] = "ERROR " + str(exc)

    con = sqlite3.connect(DB_URI, uri=True)
    con.execute("PRAGMA query_only=ON")
    tables = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
    info["n_tables"] = len(tables)
    info["tables_lock_like"] = [t for t in tables if re.search(r"hold|lock|seal|partition|oos|embargo", t, re.I)]
    info["schema"] = [[r[1], r[2]] for r in con.execute("PRAGMA table_info(signals_archive)")]
    df = pd.read_sql_query("SELECT * FROM signals_archive", con)
    con.close()
    try:
        info["db_sha256_end"] = sha256(DB)
    except OSError as exc:
        info["db_sha256_end"] = "ERROR " + str(exc)
    n = len(df)
    info["rows"] = n
    info["id_samples"] = df["id"].astype(str).head(2).tolist()
    info["id_unique"] = int(df["id"].nunique())

    ts = df["ts"].astype(str)
    info["ts_samples"] = ts.head(2).tolist() + ts.tail(2).tolist()
    info["ts_has_T"] = int(ts.str.contains("T").sum())
    info["ts_has_tz"] = int(ts.str.contains(r"(?:[+-]\d\d:?\d\d|Z)$").sum())
    df["ts_date"] = ts.str.slice(0, 10)
    hours = pd.to_numeric(ts.str.extract(r"[T ](\d\d):")[0], errors="coerce")
    info["ts_hour_as_stored_counts"] = {int(k): int(v) for k, v in hours.value_counts().sort_index().items()}
    tsd = pd.to_datetime(df["ts_date"], errors="coerce")
    info["ts_date_weekday_counts_all"] = tsd.dt.day_name().value_counts().to_dict()
    info["ts_date_min_max"] = [df["ts_date"].min(), df["ts_date"].max()]

    flat, bad = [], 0
    for s in df["payload_json"].tolist():
        try:
            p = json.loads(s) if s else {}
        except (TypeError, ValueError):
            p, bad = {}, bad + 1
        flat.append(flatten(p))
    info["payload_parse_fail"] = bad
    key_cov = Counter(k for f in flat for k in f)
    info["payload_keys_cov"] = {k: round(v / n, 3) for k, v in key_cov.most_common()}

    ts_dates = df["ts_date"].tolist()
    cand, date_report = {}, {}
    for k in key_cov:
        vals = [f.get(k) for f in flat]
        strs = [v for v in vals if isinstance(v, str)]
        m = sum(1 for v in strs if DATE_RE.match(v))
        if not strs or m < 0.5 * len(strs) or m < 0.01 * n:
            continue
        ds = [DATE_RE.match(v).group(1) if isinstance(v, str) and DATE_RE.match(v) else None for v in vals]
        pairs = [(a, b) for a, b in zip(ds, ts_dates) if a]
        diffs = [(pd.Timestamp(a) - pd.Timestamp(b)).days for a, b in pairs]
        med = float(pd.Series(diffs).median())
        date_report[k] = {
            "coverage": round(len(pairs) / n, 4),
            "share_eq_ts_date": round(sum(a == b for a, b in pairs) / len(pairs), 4),
            "median_diff_days_vs_ts": med,
            "diff_days_top": Counter(diffs).most_common(8),
            "weekday": dict(Counter(pd.Timestamp(a).day_name() for a, _ in pairs)),
            "samples": [v for v in vals if isinstance(v, str)][:2],
            "min_max": [min(a for a, _ in pairs), max(a for a, _ in pairs)],
        }
        if -4 <= med <= 1:
            cand[k] = ds
    info["payload_date_fields"] = date_report
    info["union_date_keys"] = ["ts_date"] + sorted(cand)

    maxdate = []
    for i in range(n):
        ds = [ts_dates[i]] + [cand[k][i] for k in cand if cand[k][i]]
        maxdate.append(max(ds))
    df["max_cand_date"] = maxdate
    df["c1_window"] = df["max_cand_date"] > C1_BOUNDARY
    decided = df["resolved_status_barrier"].isin(DECIDED) & df["resolved_pct_barrier"].notna()
    info["counts"] = {
        "all": n,
        "c1_window_rows": int(df["c1_window"].sum()),
        "decided_total": int(decided.sum()),
        "decided_in_c1_window": int((decided & df["c1_window"]).sum()),
        "decided_analysable": int((decided & ~df["c1_window"]).sum()),
        "rows_max_cand_date_after_2026-06-08": int((df["max_cand_date"] > "2026-06-08").sum()),
        "dup_symbol_tsdate_all": int(df.duplicated(["symbol", "ts_date"]).sum()),
    }

    # signals_archive has no declared partition; the C1 calendar flag is kept as metadata only.
    ana = df.copy()
    info["analysable_ts_date_min_max"] = [ana["ts_date"].min(), ana["ts_date"].max()]
    info["status_barrier_counts_analysable"] = ana["resolved_status_barrier"].fillna("NULL").value_counts().to_dict()
    info["status_counts_analysable"] = ana["resolved_status"].fillna("NULL").value_counts().to_dict()
    info["return_fields_analysable"] = {f: describe(ana[f]) for f in RET_FIELDS}
    info["by_status_barrier_n_min_med_max"] = {
        s: {f: brief(g[f]) for f in RET_FIELDS}
        for s, g in ana.groupby(ana["resolved_status_barrier"].fillna("NULL"))
    }
    info["by_status_n_min_med_max"] = {
        s: {f: brief(g[f]) for f in RET_FIELDS} for s, g in ana.groupby(ana["resolved_status"].fillna("NULL"))
    }
    dec = ana[ana["resolved_status_barrier"].isin(DECIDED) & ana["resolved_pct_barrier"].notna()]
    comp = {}
    for f in ("resolved_pct", "resolved_pct_t5"):
        both = dec[[f, "resolved_pct_barrier"]].dropna()
        if len(both) > 2:
            comp[f] = {"n": int(len(both)), "pearson": round(float(both.corr().iloc[0, 1]), 4),
                       "share_absdiff_lt_0.01": round(float(((both[f] - both["resolved_pct_barrier"]).abs() < 0.01).mean()), 4)}
    info["decided_field_vs_barrier"] = comp

    aflat = [flat[i] for i in ana.index]
    akeys = set(k for f in aflat for k in f)
    entry_k = first_key(akeys, ["entry", "entry_price", "price", "close", "last_price"])
    tgt_k = first_key(akeys, ["target", "target_price", "take_profit", "tp", "tp_price"])
    stop_k = first_key(akeys, ["stop", "stop_loss", "stop_price", "sl", "sl_price"])
    info["barrier_keys"] = [entry_k, tgt_k, stop_k]
    if entry_k and tgt_k and stop_k:
        chk = []
        for idx, f in zip(ana.index, aflat):
            try:
                e, t, s = float(f[entry_k]), float(f[tgt_k]), float(f[stop_k])
            except (KeyError, TypeError, ValueError):
                continue
            if e > 0:
                chk.append((idx, (t / e - 1) * 100, (s / e - 1) * 100))
        c = pd.DataFrame(chk, columns=["idx", "tp_pct", "sl_pct"]).set_index("idx")
        j = dec.join(c, how="inner")
        win = j["resolved_status_barrier"] == "resolved_win"
        exp = j["tp_pct"].where(win, j["sl_pct"])
        info["barrier_implied_check"] = {
            "n": int(len(j)),
            "share_absdiff_le_0.05pp": round(float(((j["resolved_pct_barrier"] - exp).abs() <= 0.05).mean()), 4),
            "tp_pct_median": round(float(c["tp_pct"].median()), 4),
            "sl_pct_median": round(float(c["sl_pct"].median()), 4),
        }

    cats = {}
    for k in sorted(akeys):
        vals = [f.get(k) for f in aflat]
        vv = [v for v in vals if v is not None and not isinstance(v, float)]
        if len(vv) < 0.5 * len(aflat):
            continue
        u = Counter(map(str, vv))
        if 2 <= len(u) <= 15:
            cats[k] = dict(u.most_common(15))
    info["payload_categorical_analysable"] = cats
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(info, fh, indent=1, default=str)

    show = dict(info)
    show["payload_keys_cov"] = {k: v for k, v in info["payload_keys_cov"].items() if v >= 0.05}
    print(json.dumps(show, default=str))


if __name__ == "__main__":
    main()
