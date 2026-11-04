"""DQ_01 (R3 Data Quality Auditor): read-only profiling of scan export, universe, shortlists.

Reads only local files; SQLite opened mode=ro + PRAGMA query_only=ON. No network.
Writes only to reports/scanner_intelligence_audit_v1_2026-10-19/data/DQ_01_*.
Run: python.exe -B DQ_01_export_universe_shortlists.py
"""
import collections
import csv
import datetime as dt
import glob
import hashlib
import json
import math
import os
import re
import sqlite3

ROOT = r"C:\Users\meric\Borsa"
OUT = os.path.join(ROOT, "reports", "scanner_intelligence_audit_v1_2026-10-19", "data")
EXPORT = os.path.join(ROOT, "data", "distribution", "scan_export_latest.json")
DB_FILE = os.path.join(ROOT, "data", "finpilot.db")
DB_URI = "file:C:/Users/meric/Borsa/data/finpilot.db?mode=ro"
WATCH = ["ANNAW", "NUAIW", "GSRFU", "HAVAU", "HCACU"]
MISSING_TOKENS = ("", "nan", "NaN", "None", "null", "[]", "{}")
SUMMARY = collections.OrderedDict()

SEC_RULES = {
    "warrant": r"\bwarrants?\b",
    "right": r"\brights?\b",
    "unit": r"\bunits?\b",
    "preferred": r"\bpreferred\b|\bpfd\b|\bperpetual\b",
    "debt_note": r"\bnotes? due\b|\bsenior notes?\b|\bdebentures?\b",
}


def P(key, value):
    SUMMARY[key] = value
    print(key, json.dumps(value, default=str)[:1800])


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

    return {"n": len(v), "min": round(v[0], 3), "p25": round(q(0.25), 3), "med": round(q(0.5), 3),
            "p75": round(q(0.75), 3), "p90": round(q(0.9), 3), "max": round(v[-1], 3),
            "mean": round(sum(v) / len(v), 3), "n_zero": sum(1 for x in v if x == 0)}


def name_class(name):
    if not name:
        return "no_name"
    if re.search(r"common units|limited partner|partnership units|beneficial interest", name, re.I):
        return "lp_trust_units"
    best = None
    for cls, pat in SEC_RULES.items():
        m = re.search(pat, name, re.I)
        if m and (best is None or m.start() < best[0]):
            best = (m.start(), cls)
    if best:
        return best[1]
    if re.search(r"\betf\b|\bfund\b|ishares|spdr|proshares|direxion|\bleveraged\b", name, re.I):
        return "etf_fund"
    if re.search(r"depositary receipt|american depositary|\badr\b|\bads\b", name, re.I):
        return "adr"
    return "common_other"


def suffix_class(t):
    t = t or ""
    if re.search(r"\.WS(\.[A-Z])?$|\.W$", t):
        return "warrant_sfx"
    if re.search(r"\.U$", t):
        return "unit_sfx"
    if re.search(r"\.RT?$", t):
        return "right_sfx"
    if re.search(r"\.P[A-Z]?$|\.PR[A-Z]?$|-P[A-Z]?$", t):
        return "pref_sfx"
    if len(t) == 5 and t.isalpha() and t[-1] in "WUR":
        return {"W": "warrant_sfx5", "U": "unit_sfx5", "R": "right_sfx5"}[t[-1]]
    return ""


def grp(r):
    if "scan_status" in r:
        return "skeleton"
    return "full_partial" if (r.get("missing_fields") or []) else "full_complete"


def rank_key(r):
    rs, cs = fnum(r.get("ranking_score")), fnum(r.get("composite_score"))
    return (-(rs if rs is not None else -1e9), -(cs if cs is not None else -1e9), str(r.get("symbol")))


def load_meta():
    con = sqlite3.connect(DB_URI, uri=True)
    con.execute("PRAGMA query_only=ON")
    meta = {}
    for t, name, exch, trad in con.execute("SELECT ticker, name, exchange, tradable FROM symbols"):
        meta[t] = (name or "", exch, trad)
    lists = collections.defaultdict(list)
    for ln, t in con.execute("SELECT list_name, ticker FROM symbol_lists"):
        lists[ln].append(t)
    con.close()
    return meta, lists


def export_analysis(meta):
    with open(EXPORT, encoding="utf-8") as fh:
        d = json.load(fh)
    rows = d.get("results") or []
    P("EXPORT_META", {"sha256": sha256(EXPORT), "run_id": d.get("run_id"), "generated_at": d.get("generated_at"),
                      "universe": d.get("universe"), "result_count": d.get("result_count"), "n_rows": len(rows)})
    skel = [r for r in rows if "scan_status" in r]
    full = [r for r in rows if "scan_status" not in r]
    P("EXPORT_PARTITION", {"skeleton": len(skel), "full": len(full),
                           "both_scan_status_and_price": sum(1 for r in skel if "price" in r),
                           "neither": sum(1 for r in full if "price" not in r)})
    P("SKEL_scan_status", collections.Counter(r.get("scan_status") for r in skel).most_common())
    P("SKEL_reject_reason", collections.Counter(tuple(r.get("reject_reason") or []) for r in skel).most_common(8))
    P("ALL_dq_status", collections.Counter(r.get("data_quality_status") for r in rows).most_common())
    P("FULL_dq_status", collections.Counter(r.get("data_quality_status") for r in full).most_common())
    P("FULL_dq_tier", collections.Counter(r.get("data_quality_tier") for r in full).most_common())
    mf, nmiss, avail_false = collections.Counter(), [], collections.Counter()
    for r in full:
        m = r.get("missing_fields") or []
        m = [m] if isinstance(m, str) else list(m)
        nmiss.append(len(m))
        mf.update(m)
        dq = r.get("data_quality") or {}
        av = dq.get("available") if isinstance(dq, dict) else None
        if isinstance(av, dict):
            avail_false.update(k for k, v in av.items() if not v)
    P("FULL_n_missing_hist", sorted(collections.Counter(nmiss).items()))
    P("FULL_missing_fields_freq", mf.most_common(25))
    P("FULL_available_false", avail_false.most_common(25))
    si_none, si_zero, si_keys = collections.Counter(), collections.Counter(), None
    for r in full:
        si = r.get("score_input")
        if isinstance(si, dict):
            si_keys = si_keys or sorted(si.keys())
            for k, v in si.items():
                if v is None or (isinstance(v, float) and math.isnan(v)):
                    si_none[k] += 1
                elif fnum(v) == 0:
                    si_zero[k] += 1
    P("SCORE_INPUT_keys", si_keys)
    P("SCORE_INPUT_none", si_none.most_common())
    P("SCORE_INPUT_zero", si_zero.most_common())
    groups = collections.defaultdict(list)
    for r in rows:
        groups[grp(r)].append(r)
    for g, rs in sorted(groups.items()):
        P("DIST_%s" % g, {"composite": dist([fnum(r.get("composite_score")) for r in rs]),
                          "ranking": dist([fnum(r.get("ranking_score")) for r in rs]),
                          "eligible": sum(1 for r in rs if r.get("selection_eligible"))})
    for st in sorted(set(str(r.get("data_quality_status")) for r in full)):
        rs = [r for r in full if str(r.get("data_quality_status")) == st]
        P("DIST_FULL_dqstatus_%s" % st, {"composite": dist([fnum(r.get("composite_score")) for r in rs]),
                                         "eligible": sum(1 for r in rs if r.get("selection_eligible"))})
    ranked = sorted(rows, key=rank_key)
    top_rows = []
    for pos, r in enumerate(ranked, 1):
        s = r.get("symbol")
        nm = meta.get(s, ("", None, None))
        top_rows.append({"rank": pos, "symbol": s, "ranking_score": r.get("ranking_score"),
                         "composite_score": r.get("composite_score"), "group": grp(r),
                         "dq_status": r.get("data_quality_status"),
                         "missing_fields": "|".join(map(str, r.get("missing_fields") or [])),
                         "selection_eligible": r.get("selection_eligible"), "name_class": name_class(nm[0]),
                         "suffix_class": suffix_class(s), "exchange": nm[1], "dollar_adv": r.get("dollar_adv"),
                         "spread_bps": r.get("spread_bps"), "price": r.get("price")})
    for n in (20, 50, 100):
        top = top_rows[:n]
        P("TOP%d" % n, {"group": collections.Counter(x["group"] for x in top).most_common(),
                        "dq": collections.Counter(x["dq_status"] for x in top).most_common(),
                        "name_class": collections.Counter(x["name_class"] for x in top).most_common(),
                        "suffix_nonempty": sum(1 for x in top if x["suffix_class"])})
    elig = [x for x in top_rows if x["selection_eligible"]]
    P("ELIGIBLE", {"n": len(elig), "group": collections.Counter(x["group"] for x in elig).most_common(),
                   "name_class": collections.Counter(x["name_class"] for x in elig).most_common(),
                   "suffix_nonempty": sum(1 for x in elig if x["suffix_class"])})
    P("EXPORT_name_class", collections.Counter(x["name_class"] for x in top_rows).most_common())
    P("EXPORT_suffix_class", collections.Counter(x["suffix_class"] for x in top_rows).most_common())
    P("EXPORT_noncommon_top100", [(x["rank"], x["symbol"], x["name_class"], x["suffix_class"], x["ranking_score"],
                                    x["dq_status"]) for x in top_rows[:100]
                                   if x["name_class"] in ("warrant", "unit", "right", "preferred", "debt_note")
                                   or x["suffix_class"]])
    P("WATCH_in_export", [x for x in top_rows if x["symbol"] in WATCH])
    with open(os.path.join(OUT, "DQ_01_export_ranked.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(top_rows[0].keys()))
        w.writeheader()
        w.writerows(top_rows)
    flags = collections.Counter(json.dumps(r.get("score_feature_flags"), sort_keys=True) for r in full)
    P("FLAGS", flags.most_common(4))
    P("SENTIMENT_BAND", collections.Counter(str(r.get("sentiment_band")) for r in full).most_common(6))
    P("SENTIMENT_VALUE", collections.Counter(str(r.get("sentiment")) for r in full).most_common(4))
    P("MARKET_STATUS", collections.Counter(str(r.get("market_status")) for r in full).most_common())
    P("POINT_IN_TIME", collections.Counter(str(r.get("point_in_time"))[:60] for r in full).most_common(4))
    P("FEATURE_AGE_MIN", dist([fnum(r.get("feature_age_minutes")) for r in full]))
    ts = sorted(str(r.get("timestamp")) for r in full if r.get("timestamp"))
    P("TIMESTAMP_RANGE", [ts[0], ts[-1]] if ts else None)
    P("FEATURE_TS_SAMPLE", [full[0].get("symbol"), full[0].get("feature_timestamps")] if full else None)
    for k in ("adv_source", "spread_source", "risk_data_quality", "regime", "vol_regime", "earnings_proximity",
              "earnings_blackout", "telemetry_version", "liquidity_ok", "execution_warning"):
        P("CNT_%s" % k, collections.Counter(str(r.get(k))[:50] for r in full).most_common(6))
    P("SHORT_INT_TS", collections.Counter("none" if r.get("short_interest_timestamp") in (None, "") else "set"
                                          for r in full).most_common())
    return rows


def universe_analysis(meta, lists, rows):
    for ln, ts in sorted(lists.items()):
        u = set(ts)
        P("LIST_%s" % ln, {"rows": len(ts), "unique": len(u), "not_in_symbols": sum(1 for t in u if t not in meta),
                           "tradable0": sum(1 for t in u if t in meta and meta[t][2] != 1)})
    p, i = set(lists.get("preset_1500", [])), set(lists.get("iwm_300m", []))
    union = p | i
    exp = set(r.get("symbol") for r in rows)
    P("UNION", {"union": len(union), "overlap": len(p & i),
                "union_tradable": sum(1 for t in union if t in meta and meta[t][2] == 1),
                "export_symbols": len(exp), "export_in_union": len(exp & union),
                "export_not_in_union": sorted(exp - union)[:25], "n_export_not_in_union": len(exp - union),
                "union_not_in_export": sorted(union - exp)[:25], "n_union_not_in_export": len(union - exp)})
    cls = collections.Counter()
    agree = collections.Counter()
    out = []
    for t in sorted(union | exp):
        nm = meta.get(t, ("", None, None))
        nc, sc = name_class(nm[0]), suffix_class(t)
        cls[nc] += 1
        agree[(nc, sc)] += 1
        out.append({"symbol": t, "in_export": t in exp, "in_preset_1500": t in p, "in_iwm_300m": t in i,
                    "tradable": nm[2], "exchange": nm[1], "name_class": nc, "suffix_class": sc, "name": nm[0][:120]})
    P("UNIVERSE_name_class", cls.most_common())
    P("UNIVERSE_name_vs_suffix", sorted(([a, b, c] for (a, b), c in agree.items() if a not in ("common_other", "adr", "etf_fund") or b), key=lambda x: -x[2]))
    with open(os.path.join(OUT, "DQ_01_universe_classes.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0].keys()))
        w.writeheader()
        w.writerows(out)
    P("WATCH_meta", {t: [meta.get(t, ("", None, None))[0][:110], meta.get(t, ("", None, None))[1],
                         t in p, t in i] for t in WATCH})


def shortlist_analysis(meta):
    files = sorted(glob.glob(os.path.join(ROOT, "data", "shortlists", "shortlist_202610*.csv")))
    recs, agg_missing, agg_rows = [], collections.Counter(), 0
    comp = collections.defaultdict(list)
    cls_counts, watch_pos, header74 = collections.Counter(), collections.defaultdict(list), None
    for f in files:
        with open(f, newline="", encoding="utf-8") as fh:
            rdr = csv.reader(fh)
            header = next(rdr, [])
            data = list(rdr)
        recs.append({"file": os.path.basename(f), "ncols": len(header), "nrows": len(data), "sha256": sha256(f)})
        if len(header) != 74:
            continue
        header74 = header
        idx = {h: j for j, h in enumerate(header)}
        for pos, row in enumerate(data, 1):
            agg_rows += 1
            for h, j in idx.items():
                if j >= len(row) or row[j].strip() in MISSING_TOKENS:
                    agg_missing[h] += 1
            sym = row[idx.get("symbol", 0)]
            mfv = row[idx["missing_fields"]].strip() if "missing_fields" in idx else ""
            dqs = row[idx["data_quality_status"]].strip() if "data_quality_status" in idx else ""
            partial = (mfv not in MISSING_TOKENS) or (dqs not in ("", "complete"))
            comp["partial" if partial else "complete"].append(fnum(row[idx["composite_score"]]) if "composite_score" in idx else None)
            cls_counts[name_class(meta.get(sym, ("",))[0])] += 1
            if sym in WATCH:
                watch_pos[sym].append((os.path.basename(f), pos))
    P("SHORTLIST_files", {"n": len(files), "ncols_hist": collections.Counter(r["ncols"] for r in recs).most_common(),
                          "rows_74col": agg_rows})
    P("SHORTLIST_last_files", recs[-6:])
    P("SHORTLIST_header74", header74)
    P("SHORTLIST_missing_cols_top", [(h, c, round(c / agg_rows, 3)) for h, c in agg_missing.most_common(30)] if agg_rows else None)
    P("SHORTLIST_composite", {k: dist(v) for k, v in comp.items()})
    P("SHORTLIST_name_class", cls_counts.most_common())
    P("SHORTLIST_watch_positions", {k: v[-6:] for k, v in watch_pos.items()})
    P("SHORTLIST_watch_counts", {k: len(v) for k, v in watch_pos.items()})
    with open(os.path.join(OUT, "DQ_01_shortlist_files.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["file", "ncols", "nrows", "sha256"])
        w.writeheader()
        w.writerows(recs)


def prior_and_caches():
    for p in sorted(glob.glob(os.path.join(ROOT, "data", "backtest_out", "price_cache*integrity*audit*.json"))):
        with open(p, encoding="utf-8") as fh:
            d = json.load(fh)
        info = {"sha256": sha256(p), "bytes": os.path.getsize(p), "scalars": {}, "containers": {}}

        def walk(o, prefix, depth):
            if not isinstance(o, dict):
                return
            for k, v in o.items():
                key = prefix + str(k)
                if isinstance(v, dict):
                    info["containers"][key] = "dict[%d]" % len(v)
                    if depth < 2 and len(v) <= 40:
                        walk(v, key + ".", depth + 1)
                elif isinstance(v, list):
                    info["containers"][key] = "list[%d]" % len(v)
                    if v and isinstance(v[0], dict) and len(v) <= 12 and depth < 2:
                        for n, item in enumerate(v):
                            walk(item, "%s[%d]." % (key, n), depth + 1)
                else:
                    info["scalars"][key] = repr(v)[:100]

        walk(d, "", 0)
        P("PRIOR_%s" % os.path.basename(p), info)
    for name in ("catalyst_cache.json", "macro_regime.json", "sentiment_cache.json"):
        p = os.path.join(ROOT, "data", name)
        if not os.path.exists(p):
            P("CACHE_%s" % name, "MISSING")
            continue
        mtime = dt.datetime.fromtimestamp(os.path.getmtime(p), dt.timezone.utc).isoformat()
        info = {"bytes": os.path.getsize(p), "mtime_utc": mtime, "sha256": sha256(p)}
        try:
            with open(p, encoding="utf-8") as fh:
                d = json.load(fh)
            if isinstance(d, dict):
                info["n_keys"] = len(d)
                info["ts_fields"] = {k: repr(v)[:60] for k, v in d.items()
                                     if re.search(r"generat|updat|as_?of|fetch|time|date|regime", str(k), re.I)
                                     and not isinstance(v, (dict, list))}
                sub = [v for v in d.values() if isinstance(v, dict)]
                info["n_dict_values"] = len(sub)
                tsv = []
                for v in sub:
                    for k2, v2 in v.items():
                        if re.search(r"fetch|updat|time|as_?of|date", str(k2), re.I) and isinstance(v2, str):
                            tsv.append(v2)
                if tsv:
                    tsv.sort()
                    info["inner_ts_min_max"] = [tsv[0], tsv[-1], len(tsv)]
            elif isinstance(d, list):
                info["n_items"] = len(d)
        except (ValueError, OSError) as exc:
            info["error"] = str(exc)[:100]
        P("CACHE_%s" % name, info)


def main():
    P("RUN_UTC", dt.datetime.now(dt.timezone.utc).isoformat())
    P("DB_SHA256", sha256(DB_FILE))
    meta, lists = load_meta()
    rows = export_analysis(meta)
    universe_analysis(meta, lists, rows)
    shortlist_analysis(meta)
    prior_and_caches()
    with open(os.path.join(OUT, "DQ_01_summary.json"), "w", encoding="utf-8") as fh:
        json.dump(SUMMARY, fh, indent=1, default=str)


if __name__ == "__main__":
    main()
