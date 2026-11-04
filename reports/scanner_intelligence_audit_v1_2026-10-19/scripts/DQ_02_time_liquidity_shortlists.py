"""DQ_02 (R3 Data Quality Auditor): read-only time/staleness, liquidity cross-check,
skeleton-row instrument classes, 2026-10-16 shortlists, catalyst cache structure.

Reads local files only (no network, no SQLite). Writes only reports/.../data/DQ_02_*.
Run: python.exe -B DQ_02_time_liquidity_shortlists.py
"""
import collections
import csv
import glob
import hashlib
import json
import math
import os

import pandas as pd

ROOT = r"C:\Users\meric\Borsa"
OUT = os.path.join(ROOT, "reports", "scanner_intelligence_audit_v1_2026-10-19", "data")
EXPORT = os.path.join(ROOT, "data", "distribution", "scan_export_latest.json")
CLASSES = os.path.join(OUT, "DQ_01_universe_classes.csv")
WATCH = ["ANNAW", "NUAIW", "GSRFU", "HAVAU", "HCACU"]
MEGA = ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "AMD", "INTC", "LRCX"]
DERIV = ("warrant", "unit", "right")
SUMMARY = collections.OrderedDict()


def P(key, value):
    SUMMARY[key] = value
    print(key, json.dumps(value, default=str)[:3000])


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fnum(v):
    try:
        if v is None or isinstance(v, bool):
            return None
        x = float(v)
        return None if math.isnan(x) or math.isinf(x) else x
    except (TypeError, ValueError):
        return None


def dist(vals):
    v = sorted(x for x in vals if x is not None)
    if not v:
        return {"n": 0}

    def q(p):
        k = (len(v) - 1) * p
        lo, hi = int(math.floor(k)), int(math.ceil(k))
        return v[lo] + (v[hi] - v[lo]) * (k - lo)

    return {"n": len(v), "min": round(v[0], 2), "p25": round(q(0.25), 2), "med": round(q(0.5), 2),
            "p75": round(q(0.75), 2), "p90": round(q(0.9), 2), "max": round(v[-1], 2)}


def rank_key(r):
    rs, cs = fnum(r.get("ranking_score")), fnum(r.get("composite_score"))
    return (-(rs if rs is not None else -1e9), -(cs if cs is not None else -1e9), str(r.get("symbol")))


def time_analysis(rows, classes):
    full = [r for r in rows if "scan_status" not in r]
    skel = [r for r in rows if "scan_status" in r]
    rank = {r.get("symbol"): i for i, r in enumerate(sorted(rows, key=rank_key), 1)}
    ts = [str(r.get("timestamp")) for r in full]
    P("TS_date_counts", collections.Counter(t[:10] for t in ts).most_common())
    P("TS_time_counts_1016", collections.Counter(t[11:16] for t in ts if t.startswith("2026-10-16")).most_common(12))
    out = []
    for r in full:
        t = str(r.get("timestamp"))
        kind = "stale" if not t.startswith("2026-10-16") else ("post_1945" if t[11:16] > "19:45" else "")
        if kind:
            s = r.get("symbol")
            out.append({"symbol": s, "kind": kind, "timestamp": t, "rank": rank[s],
                        "ranking_score": r.get("ranking_score"), "eligible": r.get("selection_eligible"),
                        "name_class": classes.get(s), "fts_15m": (r.get("feature_timestamps") or {}).get("15m"),
                        "fts_1d": (r.get("feature_timestamps") or {}).get("1d")})
    for kind in ("stale", "post_1945"):
        sub = sorted((x for x in out if x["kind"] == kind), key=lambda x: x["rank"])
        P("LASTBAR_%s" % kind, {"n": len(sub), "in_top100": sum(1 for x in sub if x["rank"] <= 100),
                                "eligible": sum(1 for x in sub if x["eligible"]),
                                "classes": collections.Counter(x["name_class"] for x in sub).most_common(),
                                "best": sub[:8]})
    if out:
        with open(os.path.join(OUT, "DQ_02_lastbar_flags.csv"), "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(out[0].keys()))
            w.writeheader()
            w.writerows(out)
    agree = collections.Counter()
    for r in full:
        a = str(r.get("timestamp"))[:16].replace(" ", "T")
        b = str((r.get("feature_timestamps") or {}).get("15m"))[:16]
        agree["same" if a == b else "diff"] += 1
    P("TS_vs_fts15m", agree.most_common())
    for tf in ("15m", "1h", "4h", "1d"):
        P("FTS_%s" % tf, collections.Counter(str((r.get("feature_timestamps") or {}).get(tf)) for r in full).most_common(5))
    P("AGE_keys", collections.Counter(tuple(sorted((r.get("feature_age_minutes") or {}).keys())) for r in full).most_common(3))
    keys = set()
    for r in full:
        keys.update((r.get("feature_age_minutes") or {}).keys())
    for k in sorted(keys):
        P("AGE_%s" % k, dist([fnum((r.get("feature_age_minutes") or {}).get(k)) for r in full]))
    P("SKEL_classes", collections.Counter(classes.get(r.get("symbol")) for r in skel).most_common())
    P("FULL_classes", collections.Counter(classes.get(r.get("symbol")) for r in full).most_common())
    P("DOLLAR_ADV_full", dist([fnum(r.get("dollar_adv")) for r in full]))
    P("LIQ_OK_by_adv", {str(k): dist([fnum(r.get("dollar_adv")) for r in full if r.get("liquidity_ok") is k])
                        for k in (True, False)})
    return {r.get("symbol"): r for r in full}


def liquidity_crosscheck(by_sym):
    pc = os.path.join(ROOT, "data", "price_cache")
    exts = collections.Counter(os.path.splitext(n)[1] for n in os.listdir(pc)) if os.path.isdir(pc) else {}
    P("PRICE_CACHE_exts", dict(exts))
    res = []
    for s in MEGA:
        r = by_sym.get(s) or {}
        item = {"symbol": s, "export_dollar_adv": r.get("dollar_adv"), "export_price": r.get("price"),
                "adv_source": r.get("adv_source"), "liquidity_ok": r.get("liquidity_ok")}
        for f in sorted(glob.glob(os.path.join(pc, s + ".*")) + glob.glob(os.path.join(pc, s + "_*.*")))[:1]:
            item["cache_file"] = os.path.basename(f)
            try:
                if f.endswith(".parquet"):
                    df = pd.read_parquet(f)
                elif f.endswith(".csv"):
                    df = pd.read_csv(f)
                else:
                    continue
                cols = {c.lower(): c for c in df.columns}
                if "date" in cols:
                    df = df.sort_values(cols["date"])
                    item["cache_last_date"] = str(df[cols["date"]].iloc[-1])[:10]
                elif not isinstance(df.index, pd.RangeIndex):
                    df = df.sort_index()
                    item["cache_last_date"] = str(df.index[-1])[:10]
                tail = df.tail(20)
                item["cache_dollar_adv20"] = round(float((tail[cols["close"]] * tail[cols["volume"]]).mean()), 0)
            except Exception as exc:  # noqa: BLE001
                item["cache_error"] = str(exc)[:120]
        if fnum(item.get("export_dollar_adv")) and fnum(item.get("cache_dollar_adv20")):
            item["ratio_export_to_cache"] = round(fnum(item["export_dollar_adv"]) / item["cache_dollar_adv20"], 4)
        res.append(item)
    P("MEGA_liquidity", res)


def shortlists_1016(classes):
    files = sorted(glob.glob(os.path.join(ROOT, "data", "shortlists", "shortlist_20261016*.csv")))
    P("SL1016_files", [os.path.basename(f) for f in files])
    first_header, per_file = None, []
    watch, top20 = collections.defaultdict(list), collections.Counter()
    for f in files:
        with open(f, newline="", encoding="utf-8") as fh:
            rdr = csv.DictReader(fh)
            header = rdr.fieldnames or []
            data = list(rdr)
        first_header = first_header or header
        symcol = "symbol" if "symbol" in header else ("ticker" if "ticker" in header else header[0])
        rec = {"file": os.path.basename(f), "sha256": sha256(f)[:16], "ncols": len(header), "nrows": len(data)}
        for k in ("data_quality_status", "scan_status", "selection_eligible", "liquidity_ok", "spread_source"):
            if k in header:
                rec[k] = collections.Counter(row.get(k) for row in data).most_common(3)
        if "composite_score" in header:
            rec["composite"] = dist([fnum(row.get("composite_score")) for row in data])
        per_file.append(rec)
        for pos, row in enumerate(data, 1):
            s = row.get(symcol)
            c = classes.get(s, "not_in_universe")
            if pos <= 20:
                top20[c] += 1
            if s in WATCH or (c in DERIV and pos <= 20):
                watch[s].append({"file": rec["file"], "pos": pos, "n": len(data),
                                 "composite": row.get("composite_score"), "ranking": row.get("ranking_score"),
                                 "dq": row.get("data_quality_status"), "dollar_adv": row.get("dollar_adv"),
                                 "price": row.get("price"), "eligible": row.get("selection_eligible"),
                                 "ts": row.get("timestamp")})
    P("SL1016_header_first", first_header)
    P("SL1016_per_file", per_file)
    P("SL1016_top20_classes", top20.most_common())
    P("SL1016_watch", {k: v[:4] for k, v in watch.items()})
    P("SL1016_watch_counts", {k: len(v) for k, v in watch.items()})


def catalyst_structure():
    p = os.path.join(ROOT, "data", "catalyst_cache.json")
    if not os.path.exists(p):
        P("CATALYST_structure", "MISSING")
        return
    with open(p, encoding="utf-8") as fh:
        d = json.load(fh)
    P("CATALYST_structure", {k: (type(v).__name__, len(v) if isinstance(v, (dict, list)) else None)
                             for k, v in d.items()} if isinstance(d, dict) else type(d).__name__)


def main():
    with open(EXPORT, encoding="utf-8") as fh:
        d = json.load(fh)
    P("EXPORT_sha256", sha256(EXPORT))
    rows = d.get("results") or []
    with open(CLASSES, newline="", encoding="utf-8") as fh:
        classes = {r["symbol"]: r["name_class"] for r in csv.DictReader(fh)}
    by_sym = time_analysis(rows, classes)
    liquidity_crosscheck(by_sym)
    shortlists_1016(classes)
    catalyst_structure()
    with open(os.path.join(OUT, "DQ_02_summary.json"), "w", encoding="utf-8") as fh:
        json.dump(SUMMARY, fh, indent=1, default=str)


if __name__ == "__main__":
    main()
