# PERF_analysis.py - R8 scanner performance audit (read-only).
# Reads data/distribution/scan_timing.jsonl ONCE into memory, analyses it, greps code,
# and writes only PERF_* files into the audit data folder.
import collections
import csv
import datetime as dt
import glob
import hashlib
import json
import os
import re
import subprocess
import sysconfig
import traceback

import math

import numpy as np

ROOT = r"C:\Users\meric\Borsa"
SRC = os.path.join(ROOT, "data", "distribution", "scan_timing.jsonl")
AUD = os.path.join(ROOT, "reports", "scanner_intelligence_audit_v1_2026-10-19")
OUT = os.path.join(AUD, "data")
CUT = dt.datetime(2026, 10, 16, 13, 57, 32, tzinfo=dt.timezone.utc)
RATE, BURST = 4.0, 8.0  # code defaults in scanner/data_fetcher.py fetch(); env override unknown
SEED = 20261019
NAIVE = [0]
S = collections.OrderedDict()
UTC = dt.timezone.utc


def num(x):
    if isinstance(x, bool) or x is None:
        return None
    if isinstance(x, (int, float)):
        return float(x)
    return None


def r3(v):
    return None if v is None else round(float(v), 3)


def desc(vals):
    a = np.asarray([v for v in vals if v is not None], dtype=float)
    if a.size == 0:
        return {"n": 0}
    return {
        "n": int(a.size),
        "median": r3(np.median(a)),
        "p25": r3(np.percentile(a, 25)),
        "p75": r3(np.percentile(a, 75)),
        "p90": r3(np.percentile(a, 90)),
        "mean": r3(a.mean()),
        "min": r3(a.min()),
        "max": r3(a.max()),
    }


def rankdata(a):
    a = np.asarray(a, dtype=float)
    order = np.argsort(a, kind="mergesort")
    sa = a[order]
    ranks = np.empty(a.size, dtype=float)
    i = 0
    while i < a.size:
        j = i
        while j + 1 < a.size and sa[j + 1] == sa[i]:
            j += 1
        ranks[order[i:j + 1]] = (i + j) / 2.0 + 1.0
        i = j + 1
    return ranks


def mwu_p(x, y):
    # two-sided Mann-Whitney U, normal approximation with tie and continuity correction
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    n1, n2 = x.size, y.size
    allv = np.concatenate([x, y])
    rk = rankdata(allv)
    u1 = rk[:n1].sum() - n1 * (n1 + 1) / 2.0
    n = n1 + n2
    _, t = np.unique(allv, return_counts=True)
    tie = float((t.astype(float) ** 3 - t).sum()) / (n * (n - 1))
    sd = math.sqrt(n1 * n2 / 12.0 * ((n + 1) - tie))
    if sd == 0:
        return 1.0
    z = max(abs(u1 - n1 * n2 / 2.0) - 0.5, 0.0) / sd
    return math.erfc(z / math.sqrt(2.0))


def spearman(x, y, perms=2000):
    rx = rankdata(x)
    ry = rankdata(y)
    rho = float(np.corrcoef(rx, ry)[0, 1])
    rng = np.random.default_rng(SEED)
    hits = sum(1 for _ in range(perms) if abs(np.corrcoef(rx, rng.permutation(ry))[0, 1]) >= abs(rho) - 1e-12)
    return rho, (hits + 1) / (perms + 1)


def parse_ts(s):
    if not isinstance(s, str):
        return None
    try:
        t = dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None
    if t.tzinfo is None:
        NAIVE[0] += 1
        t = t.replace(tzinfo=UTC)
    return t.astimezone(UTC)


def session(t):
    if t is None:
        return None
    m = t.hour * 60 + t.minute
    return "market" if (t.weekday() < 5 and 13 * 60 + 30 <= m <= 20 * 60) else "off"


def safe(s, n=170):
    s = str(s).rstrip("\r\n")
    if len(s) > n:
        s = s[:n] + "..."
    return s.encode("ascii", "backslashreplace").decode("ascii")


def pj(tag, obj):
    print(tag, json.dumps(obj, separators=(",", ":"), default=str))


# ---------------------------------------------------------------- load
def load():
    with open(SRC, "rb") as fh:
        raw = fh.read()
    info = {
        "path": "data/distribution/scan_timing.jsonl",
        "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "ends_with_newline": raw.endswith(b"\n"),
        "read_utc": dt.datetime.now(UTC).isoformat(),
    }
    recs, bad, nonempty = [], 0, 0
    for i, ln in enumerate(raw.split(b"\n"), 1):
        if not ln.strip():
            continue
        nonempty += 1
        try:
            o = json.loads(ln.decode("utf-8"))
        except Exception:
            bad += 1
            continue
        if not isinstance(o, dict):
            bad += 1
            continue
        o["_line"] = i
        o["_t"] = parse_ts(o.get("ts"))
        recs.append(o)
    ts = [r["_t"] for r in recs if r["_t"] is not None]
    info.update(
        nonempty_lines=nonempty,
        parsed=len(recs),
        bad=bad,
        naive_ts=NAIVE[0],
        first_ts=min(ts).isoformat() if ts else None,
        last_ts=max(ts).isoformat() if ts else None,
    )
    return recs, info


def schema(recs):
    kc = collections.Counter()
    for r in recs:
        kc.update(k for k in r if not k.startswith("_"))
    evr = [r for r in recs if "event" in r]
    pids = {}
    for r in evr:
        if r["_t"] is None:
            continue
        d = pids.setdefault(str(r.get("process_id")), [r["_t"], r["_t"], 0])
        d[0] = min(d[0], r["_t"])
        d[1] = max(d[1], r["_t"])
        d[2] += 1
    return {
        "keys": dict(kc.most_common()),
        "n_event_records": len(evr),
        "n_legacy_records": len(recs) - len(evr),
        "first_event_ts": min((r["_t"] for r in evr if r["_t"]), default=None),
        "events": dict(collections.Counter(str(r.get("event")) for r in evr)),
        "callers": dict(collections.Counter(str(r.get("caller")) for r in evr)),
        "event_outcome": dict(
            collections.Counter("%s|%s" % (r.get("event"), r.get("outcome")) for r in evr)
        ),
        "coordinator_version": dict(collections.Counter(str(r.get("coordinator_version")) for r in evr)),
        "process_ids": {k: [v[0].isoformat(), v[1].isoformat(), v[2]] for k, v in pids.items()},
    }


# ---------------------------------------------------------------- jobs / batches
def build_jobs(recs):
    jobs = collections.OrderedDict()
    for r in recs:
        ev = r.get("event")
        if not ev or not r.get("job_id"):
            continue
        j = jobs.setdefault(r["job_id"], {"started": None, "ends": [], "reqs": [], "disc": 0, "all": []})
        j["all"].append(r)
        if ev == "job_started":
            if j["started"] is None:
                j["started"] = r
        elif ev.startswith("job_"):
            j["ends"].append(r)
        elif ev == "request_disconnected":
            j["disc"] += 1
        elif ev.startswith("request_"):
            j["reqs"].append(r)
    return jobs


def am(r, tf):
    m = r.get("alpaca_miss")
    return num(m.get(tf)) if isinstance(m, dict) else None


def batch_row(r, kind, j=None):
    t = r["_t"]
    e = j["ends"][0] if (j and j["ends"]) else None
    q = j["reqs"][0] if (j and j["reqs"]) else None
    st = r.get("stage_timing")
    return {
        "line": r["_line"],
        "ts": t.isoformat() if t else None,
        "kind": kind,
        "event": r.get("event"),
        "job_id": r.get("job_id"),
        "caller": r.get("caller"),
        "process_id": r.get("process_id"),
        "coordinator_version": r.get("coordinator_version"),
        "universe": num(r.get("universe")),
        "result_symbols": num(r.get("result_symbols")),
        "total_s": num(r.get("total_s")),
        "eval_s": num(r.get("eval_s")),
        "persist_s": num(r.get("persist_s")),
        "yf_fallback": num(r.get("yf_fallback")),
        "yf_bulk_requests": num(r.get("yf_bulk_requests")),
        "yf_bulk_symbols": num(r.get("yf_bulk_symbols")),
        "am_15m": am(r, "15m"),
        "am_1h": am(r, "1h"),
        "am_1d": am(r, "1d"),
        "alpaca_total_failure": r.get("alpaca_total_failure"),
        "experiment_arm": r.get("experiment_arm"),
        "counters_unreliable": r.get("counters_unreliable") if kind == "obs" else None,
        "peak_active_jobs": num(r.get("peak_active_jobs")),
        "active_jobs_at_start": num(r.get("active_jobs_at_start")),
        "active_jobs_at_end": num(r.get("active_jobs_at_end")),
        "request_s": num(q.get("request_s")) if q else num(r.get("request_s")),
        "job_s": num(e.get("job_s")) if e else None,
        "stage_timing_n": len(st) if isinstance(st, list) else 0,
        "session": session(t),
        "period": None if t is None else ("post" if t >= CUT else "pre"),
    }


def build_batches(recs, jobs):
    out = []
    for r in recs:
        if "event" not in r and num(r.get("total_s")) is not None:
            out.append(batch_row(r, "legacy"))
    for jid, j in jobs.items():
        tot = [r for r in j["all"] if num(r.get("total_s")) is not None]
        if not tot:
            continue
        pref = [r for r in tot if str(r.get("event", "")).startswith("request_")] or tot
        out.append(batch_row(pref[0], "obs", j))
    out.sort(key=lambda b: b["line"])
    return out


# ---------------------------------------------------------------- Q1
def group_stats(g):
    pos = lambda k: [b[k] for b in g if b[k] is not None and b[k] >= 0]
    rel = [b for b in g if b["counters_unreliable"] is False]
    ts = [b["ts"] for b in g if b["ts"]]
    return {
        "n": len(g),
        "kinds": dict(collections.Counter(b["kind"] for b in g)),
        "first_ts": min(ts) if ts else None,
        "last_ts": max(ts) if ts else None,
        "total_s": desc([b["total_s"] for b in g]),
        "total_s_market": desc([b["total_s"] for b in g if b["session"] == "market"]),
        "total_s_off": desc([b["total_s"] for b in g if b["session"] == "off"]),
        "yf_fallback": desc(pos("yf_fallback")),
        "yf_bulk_symbols": desc(pos("yf_bulk_symbols")),
        "yf_bulk_requests": desc(pos("yf_bulk_requests")),
        "am_15m": desc(pos("am_15m")),
        "am_1h": desc(pos("am_1h")),
        "am_1d": desc(pos("am_1d")),
        "result_symbols": desc(pos("result_symbols")),
        "counters_unreliable": dict(collections.Counter(str(b["counters_unreliable"]) for b in g)),
        "alpaca_total_failure": dict(collections.Counter(str(b["alpaca_total_failure"]) for b in g)),
        "coordinator_version": dict(collections.Counter(str(b["coordinator_version"]) for b in g)),
        "reliable_n": len(rel),
        "reliable_total_s": desc([b["total_s"] for b in rel]),
        "reliable_yf_fallback": desc([b["yf_fallback"] for b in rel if b["yf_fallback"] is not None and b["yf_fallback"] >= 0]),
        "reliable_yf_bulk_symbols": desc([b["yf_bulk_symbols"] for b in rel if b["yf_bulk_symbols"] is not None and b["yf_bulk_symbols"] >= 0]),
        "reliable_am_1h": desc([b["am_1h"] for b in rel if b["am_1h"] is not None]),
    }


def q1(batches):
    rng = np.random.default_rng(SEED)
    b200 = [b for b in batches if b["universe"] == 200 and b["total_s"] is not None and b["period"]]
    pre = [b for b in b200 if b["period"] == "pre"]
    post = [b for b in b200 if b["period"] == "post"]
    lim30 = (CUT - dt.timedelta(days=30)).isoformat()
    groups = collections.OrderedDict(
        pre_all=pre,
        pre_30d=[b for b in pre if b["ts"] >= lim30],
        pre_obs_era=[b for b in pre if b["kind"] == "obs"],
        post=post,
    )
    res = {"groups": {k: group_stats(v) for k, v in groups.items()}, "tests": {}}
    pv = np.array([b["total_s"] for b in post], dtype=float)
    for name in ("pre_all", "pre_30d", "pre_obs_era"):
        g = groups[name]
        if len(g) < 3 or pv.size < 3:
            res["tests"][name] = {"skipped": True, "n_pre": len(g), "n_post": int(pv.size)}
            continue
        pr = np.array([b["total_s"] for b in g], dtype=float)
        up = mwu_p(pv, pr)
        hl = float(np.median((pv[:, None] - pr[None, :]).ravel()))
        boots = [np.median(rng.choice(pv, pv.size)) - np.median(rng.choice(pr, pr.size)) for _ in range(4000)]
        lo, hi = np.percentile(boots, [2.5, 97.5])
        res["tests"][name] = {
            "n_pre": len(g),
            "n_post": int(pv.size),
            "mwu_p": r3(up) if up >= 0.001 else float("%.2e" % up),
            "hl_post_minus_pre_s": r3(hl),
            "median_diff_s": r3(np.median(pv) - np.median(pr)),
            "median_diff_boot95": [r3(lo), r3(hi)],
        }
    # OLS total_s ~ 1 + yf_fallback + post ; stratified bootstrap on the post coefficient
    rows = [b for b in b200 if b["yf_fallback"] is not None and b["yf_fallback"] >= 0 and b["counters_unreliable"] is not True]
    for label, sub in (("all_known", rows), ("pre30_and_post", [b for b in rows if b["period"] == "post" or b["ts"] >= lim30])):
        pre_i = [b for b in sub if b["period"] == "pre"]
        post_i = [b for b in sub if b["period"] == "post"]
        if len(post_i) < 3 or len(pre_i) < 3:
            res["ols_" + label] = {"skipped": True, "n_pre": len(pre_i), "n_post": len(post_i)}
            continue

        def fit(pp, qq):
            X = np.array([[1.0, b["yf_fallback"], 0.0] for b in pp] + [[1.0, b["yf_fallback"], 1.0] for b in qq])
            y = np.array([b["total_s"] for b in pp] + [b["total_s"] for b in qq])
            return np.linalg.lstsq(X, y, rcond=None)[0]

        beta = fit(pre_i, post_i)
        bs = []
        for _ in range(2000):
            a = [pre_i[k] for k in rng.integers(0, len(pre_i), len(pre_i))]
            c = [post_i[k] for k in rng.integers(0, len(post_i), len(post_i))]
            bs.append(fit(a, c)[2])
        lo, hi = np.percentile(bs, [2.5, 97.5])
        res["ols_" + label] = {
            "n_pre": len(pre_i),
            "n_post": len(post_i),
            "intercept": r3(beta[0]),
            "per_yf_fallback_s": r3(beta[1]),
            "post_shift_s": r3(beta[2]),
            "post_shift_boot95": [r3(lo), r3(hi)],
        }
    days = collections.defaultdict(list)
    for b in post:
        days[b["ts"][:10]].append(b)
    res["post_by_day"] = {
        d: {
            "n": len(v),
            "median_total_s": r3(np.median([b["total_s"] for b in v])),
            "median_yf_fallback": r3(np.median([b["yf_fallback"] for b in v if b["yf_fallback"] is not None and b["yf_fallback"] >= 0] or [np.nan])),
            "sessions": dict(collections.Counter(b["session"] for b in v)),
            "unreliable": dict(collections.Counter(str(b["counters_unreliable"]) for b in v)),
        }
        for d, v in sorted(days.items())
    }
    # rate-limit lower bound (ESTIMATED) and yf_fallback multiple-of-3 pattern
    lb = {}
    for name, g in (("pre_all", pre), ("pre_30d", groups["pre_30d"]), ("post", post)):
        ok = [b for b in g if b["yf_fallback"] is not None and b["yf_fallback"] >= 0 and b["counters_unreliable"] is not True]
        lbs = [max(0.0, b["yf_fallback"] - BURST) / RATE for b in ok]
        lb[name] = {
            "n": len(ok),
            "lb_s": desc(lbs),
            "lb_over_total": desc([x / b["total_s"] for x, b in zip(lbs, ok) if b["total_s"] > 0]),
        }
    res["rate_limit_lower_bound"] = lb
    m3 = {}
    for name, g in (("legacy", [b for b in b200 if b["kind"] == "legacy"]), ("obs_reliable", [b for b in b200 if b["counters_unreliable"] is False]), ("obs_unreliable", [b for b in b200 if b["counters_unreliable"] is True])):
        v = [int(b["yf_fallback"]) for b in g if b["yf_fallback"] is not None and b["yf_fallback"] > 0]
        m3[name] = {"n_pos": len(v), "share_mod3_eq0": r3(sum(1 for x in v if x % 3 == 0) / len(v)) if v else None}
    res["yf_fallback_mod3"] = m3
    zero = [b for b in b200 if b["result_symbols"] == 0]
    res["zero_result_batches_200"] = {
        "n": len(zero),
        "alpaca_total_failure": dict(collections.Counter(str(b["alpaca_total_failure"]) for b in zero)),
        "lines": [b["line"] for b in zero][:20],
    }
    res["total_failure_batches_200"] = dict(collections.Counter(str(b["alpaca_total_failure"]) for b in b200))
    return res, b200


# ---------------------------------------------------------------- Q2 / Q3
def job_rows(jobs):
    rows = []
    for jid, j in jobs.items():
        s = j["started"]
        e = j["ends"][0] if j["ends"] else None
        q = j["reqs"][0] if j["reqs"] else None
        base = e or q or s or j["all"][0]
        tot = next((num(r.get("total_s")) for r in j["all"] if num(r.get("total_s")) is not None), None)
        rows.append({
            "job_id": jid,
            "caller": base.get("caller"),
            "universe": num(base.get("universe")),
            "process_id": base.get("process_id"),
            "coordinator_version": base.get("coordinator_version"),
            "t_start": s["_t"] if s else None,
            "t_end": e["_t"] if e else None,
            "job_s": num(e.get("job_s")) if e else None,
            "end_event": e.get("event") if e else None,
            "job_outcome": e.get("outcome") if e else None,
            "error_type": e.get("error_type") if e else None,
            "active_jobs_at_start": num((e or s or base).get("active_jobs_at_start")),
            "active_jobs_at_end": num(e.get("active_jobs_at_end")) if e else None,
            "peak_active_jobs": num((e or base).get("peak_active_jobs")),
            "counters_unreliable_end": e.get("counters_unreliable") if e else None,
            "n_requests": len(j["reqs"]),
            "request_outcome": q.get("outcome") if q else None,
            "request_s": num(q.get("request_s")) if q else None,
            "request_error_type": q.get("error_type") if q else None,
            "t_req_end": q["_t"] if q else None,
            "counters_unreliable_req": q.get("counters_unreliable") if q else None,
            "worker_started_req": q.get("worker_started") if q else None,
            "total_s": tot,
            "disconnects": j["disc"],
        })
    iv = [r for r in rows if r["t_start"] is not None and r["t_end"] is not None]
    st = np.array([r["t_start"].timestamp() for r in iv])
    en = np.array([r["t_end"].timestamp() for r in iv])
    pid = [str(r["process_id"]) for r in iv]
    for r in rows:
        r.update(n_overlap=None, overlap_s=None, same_proc_overlap=None, cross_proc_overlap=None)
    for i, r in enumerate(iv):
        inter = np.minimum(en[i], en) - np.maximum(st[i], st)
        m = inter > 0
        m[i] = False
        idx = np.nonzero(m)[0]
        r["n_overlap"] = int(idx.size)
        r["overlap_s"] = r3(inter[m].sum()) if idx.size else 0.0
        r["same_proc_overlap"] = any(pid[k] == pid[i] for k in idx)
        r["cross_proc_overlap"] = any(pid[k] != pid[i] for k in idx)
    ev = sorted([(a, 1) for a in st] + [(b, -1) for b in en])
    act, last, t1, t2 = 0, None, 0.0, 0.0
    for t, d in ev:
        if last is not None:
            if act >= 1:
                t1 += t - last
            if act >= 2:
                t2 += t - last
        act += d
        last = t
    return rows, {"jobs_with_interval": len(iv), "busy_s": r3(t1), "busy_ge2_s": r3(t2), "share_busy_time_ge2": r3(t2 / t1) if t1 else None}


def q2(rows, sweep):
    fin = [r for r in rows if r["end_event"]]
    res = {"sweep_all_jobs": sweep}
    res["n_jobs"] = len(rows)
    res["n_jobs_finished"] = len(fin)
    res["callers"] = dict(collections.Counter(str(r["caller"]) for r in rows))
    res["coordinator_version"] = dict(collections.Counter(str(r["coordinator_version"]) for r in rows))
    for k in ("active_jobs_at_start", "active_jobs_at_end", "peak_active_jobs"):
        res[k] = dict(sorted(collections.Counter(str(None if r[k] is None else int(r[k])) for r in fin).items()))
    res["counters_unreliable_end"] = dict(collections.Counter(str(r["counters_unreliable_end"]) for r in fin))
    res["counters_unreliable_req"] = dict(collections.Counter(str(r["counters_unreliable_req"]) for r in rows if r["n_requests"]))
    res["overlap_any"] = dict(collections.Counter(str(None if r["n_overlap"] is None else r["n_overlap"] > 0) for r in rows))
    res["overlap_cross_proc"] = dict(collections.Counter(str(r["cross_proc_overlap"]) for r in rows if r["n_overlap"] is not None))
    res["xtab_interval_vs_peak"] = dict(collections.Counter(
        "interval_same_proc=%s|peak>1=%s" % (r["same_proc_overlap"], None if r["peak_active_jobs"] is None else r["peak_active_jobs"] > 1)
        for r in rows if r["n_overlap"] is not None
    ))
    by_caller = {}
    for c in sorted(set(str(r["caller"]) for r in fin)):
        g = [r for r in fin if str(r["caller"]) == c]
        by_caller[c] = {
            "n": len(g),
            "universe": dict(collections.Counter(str(r["universe"]) for r in g).most_common(6)),
            "overlap_share": r3(sum(1 for r in g if r["n_overlap"]) / len(g)),
            "peak_gt1_share": r3(sum(1 for r in g if (r["peak_active_jobs"] or 0) > 1) / len(g)),
            "job_s": desc([r["job_s"] for r in g]),
        }
    res["by_caller"] = by_caller
    g = [r for r in fin if r["universe"] == 200 and r["job_s"] is not None and r["n_overlap"] is not None]
    a = [r["job_s"] for r in g if r["n_overlap"] == 0]
    b = [r["job_s"] for r in g if r["n_overlap"] > 0]
    out = {"n": len(g), "job_s_no_overlap": desc(a), "job_s_overlap": desc(b)}
    if len(a) >= 3 and len(b) >= 3:
        out["mwu_p"] = r3(mwu_p(b, a))
        out["hl_overlap_minus_none_s"] = r3(np.median((np.array(b)[:, None] - np.array(a)[None, :]).ravel()))
    if len(g) >= 5:
        rho, p = spearman([r["n_overlap"] for r in g], [r["job_s"] for r in g])
        out["spearman_noverlap_jobs"] = [r3(rho), r3(p)]
        pk = [r for r in g if r["peak_active_jobs"] is not None]
        if len(pk) >= 5:
            rho2, p2 = spearman([r["peak_active_jobs"] for r in pk], [r["job_s"] for r in pk])
            out["spearman_peak_jobs"] = [r3(rho2), r3(p2), len(pk)]
    res["u200_overlap_vs_job_s"] = out
    t = [r for r in rows if r["universe"] == 200 and r["total_s"] is not None]
    res["u200_total_s_by_req_unreliable"] = {
        str(k): desc([r["total_s"] for r in t if r["counters_unreliable_req"] == k]) for k in (True, False, None)
    }
    return res


def legacy_overlap(batches):
    g = [b for b in batches if b["kind"] == "legacy" and b["universe"] == 200 and b["ts"]]
    iv = []
    for b in g:
        t = dt.datetime.fromisoformat(b["ts"]).timestamp()
        iv.append((t - b["total_s"] - (b["persist_s"] or 0.0), t))
    n_ov = 0
    for i, (s0, e0) in enumerate(iv):
        if any(min(e0, e1) - max(s0, s1) > 0 for k, (s1, e1) in enumerate(iv) if k != i):
            n_ov += 1
    return {"n": len(iv), "n_overlapping_approx": n_ov, "share": r3(n_ov / len(iv)) if iv else None}


def q3(rows):
    req = [r for r in rows if r["n_requests"]]
    res = {"n_jobs_with_request": len(req)}
    res["request_outcome"] = dict(collections.Counter(str(r["request_outcome"]) for r in req))
    res["request_outcome_by_universe"] = dict(collections.Counter("%s|%s" % (r["universe"], r["request_outcome"]) for r in req).most_common(12))
    res["request_error_type"] = dict(collections.Counter(str(r["request_error_type"]) for r in req if r["request_outcome"] != "ok"))
    res["request_s_by_outcome"] = {o: desc([r["request_s"] for r in req if r["request_outcome"] == o]) for o in sorted(set(str(r["request_outcome"]) for r in req))}
    fin = [r for r in rows if r["end_event"]]
    res["job_outcome"] = dict(collections.Counter("%s|%s|%s" % (r["end_event"], r["job_outcome"], r["error_type"]) for r in fin))
    tmo = [r for r in req if r["request_outcome"] == "timeout"]
    late = []
    for r in tmo:
        if r["t_end"] is not None and r["t_req_end"] is not None:
            late.append({
                "job_id": r["job_id"][:12],
                "universe": r["universe"],
                "request_s": r3(r["request_s"]),
                "job_s": r3(r["job_s"]),
                "finished_after_request_s": r3((r["t_end"] - r["t_req_end"]).total_seconds()),
                "job_outcome": r["job_outcome"],
                "req_end": r["t_req_end"].isoformat()[:19],
            })
    res["timeouts"] = {
        "n": len(tmo),
        "with_job_end": len(late),
        "without_job_end": len(tmo) - len(late),
        "finished_after_request": sum(1 for x in late if (x["finished_after_request_s"] or 0) > 0),
        "finished_after_request_s": desc([x["finished_after_request_s"] for x in late]),
        "job_s": desc([x["job_s"] for x in late]),
        "rows": late[:25],
    }
    ok = [r for r in req if r["request_outcome"] == "ok" and r["job_s"] is not None and r["request_s"] is not None]
    res["ok_request_minus_job_s"] = desc([r["request_s"] - r["job_s"] for r in ok])
    qw = []
    for r in ok:
        if r["t_start"] is not None and r["t_req_end"] is not None:
            qw.append((r["t_start"] - (r["t_req_end"] - dt.timedelta(seconds=r["request_s"]))).total_seconds())
    res["ok_queue_wait_approx_s"] = desc(qw)
    orph = [r for r in rows if r["t_start"] is not None and r["end_event"] is None]
    res["orphan_job_started_no_end"] = {
        "n": len(orph),
        "by_caller_universe": dict(collections.Counter("%s|%s" % (r["caller"], r["universe"]) for r in orph).most_common(8)),
        "by_date": dict(collections.Counter(r["t_start"].isoformat()[:10] for r in orph).most_common(12)),
    }
    res["requests_worker_not_started"] = sum(1 for r in req if r["worker_started_req"] is False)
    res["jobs_with_disconnect"] = sum(1 for r in rows if r["disconnects"])
    return res


# ---------------------------------------------------------------- code greps
SECRET_HINT = re.compile(r"KEY|SECRET|TOKEN|PASSW|://", re.I)


def grep(path, pattern, limit=15, mask=False, label=None):
    full = path if os.path.isabs(path) else os.path.join(ROOT, path)
    lab = label or path
    if not os.path.exists(full):
        print("  [missing]", lab)
        return
    rx = re.compile(pattern)
    n = 0
    with open(full, "r", encoding="utf-8", errors="replace") as fh:
        for i, line in enumerate(fh, 1):
            if rx.search(line):
                txt = line.strip()
                if mask and SECRET_HINT.search(txt):
                    txt = "<masked>"
                print("  %s:%d %s" % (lab, i, safe(txt)))
                n += 1
                if n >= limit:
                    print("  ... limit")
                    break
    if n == 0:
        print("  [no match]", lab)


def code_checks():
    print("C.1 data_fetcher counters / cancellation / persistent cache patterns")
    grep("scanner/data_fetcher.py", r"_YF_FETCH_COUNT|def _note_yf_fetch|def yf_fetch_count|def reset_yf_fetch_count|note_counter_reset|check_cancelled", 20)
    grep("scanner/data_fetcher.py", r"parquet|pickle|feather|joblib|read_csv|to_csv|sqlite|\.h5\b|cache_dir|CACHE_DIR|np\.load|open\(", 15)
    print("C.2 evaluate.py cancellation / observe_scan / file reads")
    grep("scanner/evaluate.py", r"check_cancelled|observe_scan|def evaluate_symbols_parallel", 20)
    grep("scanner/evaluate.py", r"read_parquet|read_csv|json\.load|open\(|sqlite", 12)
    print("C.3 scanner/performance.py event store")
    grep("scanner/performance.py", r"_EVENTS|deque|maxlen|\.append\(|\.clear\(|def snapshot|def timer|def enabled|STAGE_TIMING|_MAX", 20)
    print("C.4 core/cache.py MemoryCache / CacheManager bounds")
    grep("core/cache.py", r"class MemoryCache|class CacheManager|max_size|popitem|OrderedDict|evict|def cleanup|maxsize|redis|REDIS|getenv", 30, mask=True)
    print("C.5 scan_coordinator config / cleanup / prepare")
    grep("core/scan_coordinator.py", r"def submit_scan|prepare|reset_yf_fetch_count|note_counter_reset|getenv|\.pop\(|del self|ScanCoordinator\(", 30)
    grep("api/routers/scan.py", r"prepare=|reset_yf_fetch_count|submit_scan|note_counter_reset", 10)
    print("C.6 deployment config (non-secret keys only; secret-like lines masked)")
    for p in sorted(glob.glob(os.path.join(ROOT, "docker-compose*.yml")) + glob.glob(os.path.join(ROOT, "Dockerfile*")) + glob.glob(os.path.join(ROOT, "api", "Dockerfile*"))):
        grep(p, r"YFINANCE_RATE|YFINANCE_BURST|FINPILOT_SCAN_[A-Z_]+|FINPILOT_ENABLE_EODHD_BARS|FINPILOT_DISABLE_ALPACA|uvicorn|gunicorn|--workers|WEB_CONCURRENCY|mem_limit|cpus|python:3", 12, mask=True, label=os.path.relpath(p, ROOT))
    for p in sorted(glob.glob(os.path.join(ROOT, "requirements*.txt")) + glob.glob(os.path.join(ROOT, "api", "requirements*.txt"))):
        grep(p, r"(?i)alpaca|yfinance", 6, label=os.path.relpath(p, ROOT))
    print("C.7 local site-packages (may differ from API image)")
    sp = sysconfig.get_paths()["purelib"]
    for pat in ("yfinance-*.dist-info", "alpaca_py-*.dist-info"):
        print("  dist:", [os.path.basename(x) for x in glob.glob(os.path.join(sp, pat))])
    grep(os.path.join(sp, "alpaca", "common", "rest.py"), r"limit|page_token|page_size", 20, label="site:alpaca/common/rest.py")
    grep(os.path.join(sp, "yfinance", "multi.py"), r"threads|cpu_count|max_workers|timeout", 12, label="site:yfinance/multi.py")
    grep(os.path.join(sp, "yfinance", "scrapers", "quote.py"), r"def last_price|_get_1y_prices|def _get_1y|\.history\(", 12, label="site:yfinance/scrapers/quote.py")
    print("C.8 git show 93ae83c repair hunk")
    try:
        cp = subprocess.run(["git", "-C", ROOT, "--no-pager", "show", "--format=", "93ae83c", "--", "scanner/data_fetcher.py"], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
        txt = cp.stdout.splitlines()
        k = next((i for i, l in enumerate(txt) if l.startswith("@@ -1210")), None)
        for l in (txt[k:k + 22] if k is not None else ["[hunk not found]"]):
            print("  |", safe(l))
    except Exception as exc:
        print("  git show failed:", type(exc).__name__)


# ---------------------------------------------------------------- main
def write_csv(path, rows, cols):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({c: (r[c].isoformat() if isinstance(r.get(c), dt.datetime) else r.get(c)) for c in cols})


def main():
    recs, info = load()
    S["snapshot"] = info
    pj("SNAPSHOT", info)
    try:
        sc = schema(recs)
        S["schema"] = sc
        pj("SCHEMA_KEYS", sc["keys"])
        pj("SCHEMA_MISC", {k: v for k, v in sc.items() if k != "keys"})
    except Exception:
        traceback.print_exc()
    jobs = build_jobs(recs)
    batches = build_batches(recs, jobs)
    S["batches"] = {"n": len(batches), "kinds": dict(collections.Counter(b["kind"] for b in batches)), "universe_top": dict(collections.Counter(str(b["universe"]) for b in batches).most_common(8))}
    pj("BATCHES", S["batches"])
    # PRIOR reproduction on the first 820 non-empty records (10-18 snapshot size)
    try:
        first820 = recs[:820]
        rows820 = [r for r in first820 if num(r.get("universe")) == 200 and num(r.get("total_s")) is not None]
        S["prior_check_first820"] = {"rows_u200_total": len(rows820), "median_total_s": r3(np.median([num(r["total_s"]) for r in rows820])) if rows820 else None, "last_line": first820[-1]["_line"] if first820 else None}
        pj("PRIOR_CHECK", S["prior_check_first820"])
    except Exception:
        traceback.print_exc()
    try:
        res1, b200 = q1(batches)
        S["q1"] = res1
        for k, v in res1["groups"].items():
            pj("Q1_GROUP_" + k, v)
        for k in ("tests", "ols_all_known", "ols_pre30_and_post", "post_by_day", "rate_limit_lower_bound", "yf_fallback_mod3", "zero_result_batches_200", "total_failure_batches_200"):
            pj("Q1_" + k, res1.get(k))
    except Exception:
        traceback.print_exc()
    try:
        rows, sweep = job_rows(jobs)
        S["q2"] = q2(rows, sweep)
        S["q2"]["legacy_u200_overlap_approx"] = legacy_overlap(batches)
        for k, v in S["q2"].items():
            pj("Q2_" + k, v)
        S["q3"] = q3(rows)
        for k, v in S["q3"].items():
            pj("Q3_" + k, v)
        write_csv(os.path.join(OUT, "PERF_jobs.csv"), rows, list(rows[0].keys()) if rows else ["job_id"])
    except Exception:
        traceback.print_exc()
    write_csv(os.path.join(OUT, "PERF_batches.csv"), batches, list(batches[0].keys()) if batches else ["line"])
    with open(os.path.join(OUT, "PERF_summary.json"), "w", encoding="utf-8") as fh:
        json.dump(S, fh, indent=1, default=str)
    print("WROTE", [os.path.basename(p) for p in glob.glob(os.path.join(OUT, "PERF_*"))])
    try:
        code_checks()
    except Exception:
        traceback.print_exc()


if __name__ == "__main__":
    main()
