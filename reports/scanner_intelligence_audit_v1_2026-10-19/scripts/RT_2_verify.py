# RT_2_verify.py - read-only verification for R10 Phase B (B1/B2/B11 analytics + code excerpts).
# ASCII only. No network. SQLite read-only. Outcome statistics only for signal_date <= 2026-05-20.
import os
import re
import sys
import csv
import ast
import json
import math
import sqlite3
import subprocess
import traceback
import datetime as dt
from collections import Counter, defaultdict

import numpy as np

sys.stdout.reconfigure(encoding="ascii", errors="backslashreplace")
sys.stderr.reconfigure(encoding="ascii", errors="backslashreplace")

ROOT = r"C:\Users\meric\Borsa"
AUD = os.path.join(ROOT, "reports", "scanner_intelligence_audit_v1_2026-10-19")
CUTOFF = dt.date(2026, 5, 20)
TOK = re.compile(r"\b(?=[A-Za-z0-9\-]*\d)(?=[A-Za-z0-9\-]*[A-Za-z])[A-Za-z0-9\-]{32,}\b")


def safe(s, n=240):
    s = str(s).rstrip("\r\n")
    s = TOK.sub("<MASKED>", s)
    if len(s) > n:
        s = s[:n] + " ..."
    return s.encode("ascii", "backslashreplace").decode("ascii")


def read_lines(rel):
    p = rel if os.path.isabs(rel) else os.path.join(ROOT, rel)
    with open(p, "r", encoding="utf-8", errors="replace") as f:
        return f.readlines()


def show(rel, a, b, n=240):
    print("=== SHOW %s %d-%d ===" % (rel, a, b))
    try:
        L = read_lines(rel)
        for i in range(max(1, a), min(b, len(L)) + 1):
            if L[i - 1].strip():
                print("%s:%d: %s" % (rel, i, safe(L[i - 1], n)))
    except Exception as e:
        print("ERR %s %r" % (rel, e))


def grep(rel, pattern, after=0, limit=40, n=240, flags=0):
    print("=== GREP %s /%s/ a=%d ===" % (rel, pattern, after))
    try:
        L = read_lines(rel)
        rx = re.compile(pattern, flags)
        cnt = 0
        shown = set()
        for i, line in enumerate(L, 1):
            if rx.search(line):
                cnt += 1
                if cnt > limit:
                    continue
                for j in range(i, min(len(L), i + after) + 1):
                    if j not in shown and L[j - 1].strip():
                        shown.add(j)
                        print("%s:%d: %s" % (rel, j, safe(L[j - 1], n)))
        print("MATCHES %d" % cnt)
    except Exception as e:
        print("ERR %s %r" % (rel, e))


def git(args, limit=20):
    print("=== GIT %s ===" % " ".join(args))
    try:
        r = subprocess.run(["git", "-C", ROOT] + args, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=900)
        L = r.stdout.splitlines()
        print("RC %d N_LINES %d" % (r.returncode, len(L)))
        for line in L[:limit]:
            print(safe(line, 200))
    except Exception as e:
        print("ERR %r" % e)


def run(name, fn):
    try:
        fn()
    except Exception:
        print("SECTION_ERR " + name)
        print(safe(traceback.format_exc(), 3000))


def code_part():
    s = "api/routers/scan.py"
    show(s, 28, 57)
    show(s, 318, 372)
    show(s, 945, 961)
    show(s, 1018, 1030)
    show("api/main.py", 300, 345)
    show("api/middleware/auth.py", 44, 75)
    cand = []
    for d in ("api", "core", "scanner"):
        for dp, dns, fns in os.walk(os.path.join(ROOT, d)):
            dns[:] = [x for x in dns if x != "__pycache__"]
            for fn in fns:
                if fn.endswith(".py") and "coordinator" in fn:
                    cand.append(os.path.relpath(os.path.join(dp, fn), ROOT).replace("\\", "/"))
    print("COORDINATOR_FILES", cand)
    for c in cand:
        grep(c, r"^\s*def |^class |budget|cancel", limit=60, n=180)
        grep(c, r"def check_cancelled|def detach|def submit_scan", after=22, limit=3, n=180)
    f = "scanner/data_fetcher.py"
    grep(f, r"^DEFAULT_TIMEFRAMES|^MIN_HISTORY_BARS|^CACHE_TTL_SECONDS", after=6, limit=3)
    show(f, 333, 440)
    show(f, 636, 700)
    show(f, 1208, 1222)
    grep(f, r"dropna|isna|notna", limit=20)
    show("core/rate_limiter.py", 1, 33)
    show("core/rate_limiter.py", 94, 108)
    e = "scanner/score_engine.py"
    show(e, 10, 32)
    show(e, 99, 252)
    show("scanner/evaluate.py", 360, 384)
    show("scanner/evaluate.py", 525, 575)
    show("core/scheduler.py", 885, 921)
    r = "scripts/resolve_open_signals.py"
    show(r, 30, 50)
    show(r, 71, 93)
    show(r, 134, 152)
    show(r, 166, 289)
    show("distribution/archive_bridge.py", 1, 140)
    show("scripts/migrate_signal_archive_to_sqlite.py", 1, 130)
    grep("distribution/karne.py", r"_overall_from_archive|resolved_status_barrier|resolved_pct_barrier|decided", limit=20)
    grep("research/label_entry_basis_backfill_2026_09_03.py", r"UPDATE|INSERT|signals_archive|commit\(|dry|mode=ro|query_only", limit=30)
    dl = "docs/governance/decision-log.md"
    show(dl, 57, 57, n=3200)
    show(dl, 93, 95, n=900)
    show(dl, 832, 840, n=400)
    show(dl, 1260, 1260, n=1400)
    show(dl, 3241, 3241, n=2200)
    grep(dl, r"econ", limit=15, n=500, flags=re.I)
    try:
        p = os.path.join(ROOT, "data", "signals_archive_recovered_20260703.csv")
        with open(p, "r", encoding="utf-8", errors="replace") as fh:
            hdr = fh.readline()
            n = sum(1 for _ in fh)
        print("RECOVERED_CSV header=%s rows=%d" % (safe(hdr, 400), n))
    except Exception as ex:
        print("RECOVERED_CSV ERR %r" % ex)


def fixed_target_lists():
    print("=== FIXED TARGET final-interpretation lists ===")
    L = read_lines("data/backtest_out/fixed_target_full_universe_2026-08-11.md")
    target = "ATR>=3|tp=10.00%|atr_stop=2|h=10"
    for ln in (57, 58):
        t = L[ln - 1]
        m = re.search(r"`(\[.*\])`", t)
        items = ast.literal_eval(m.group(1)) if m else []
        tp10 = [x for x in items if "tp=10.00%" in x]
        print("LINE %d n_items=%d target_in=%s tp10_items=%d first12=%s" % (
            ln, len(items), target in items, len(tp10), items[:12]))
        print("LINE %d tp10_items_list=%s" % (ln, tp10[:20]))
        print("LINE %d ATR>=3 items=%s" % (ln, [x for x in items if x.startswith("ATR>=3|")][:20]))
    j = os.path.join(ROOT, "data", "backtest_out", "fixed_target_full_universe_2026-08-11.json")
    print("JSON_EXISTS", os.path.exists(j), os.path.getsize(j) if os.path.exists(j) else -1)
    if os.path.exists(j) and os.path.getsize(j) < 80000000:
        with open(j, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        hits = []

        def walk(o, path):
            if len(hits) >= 3:
                return
            if isinstance(o, dict):
                if any(v == target for v in o.values() if isinstance(v, str)):
                    hits.append((path, o))
                    return
                for k, v in o.items():
                    walk(v, path + "/" + str(k))
            elif isinstance(o, list):
                for i, v in enumerate(o):
                    walk(v, path + "[%d]" % i)
        walk(data, "")
        print("JSON_TOP_KEYS", list(data.keys())[:30] if isinstance(data, dict) else type(data))
        for p_, o in hits:
            print("JSON_HIT", safe(p_, 120), safe(json.dumps(o, default=str), 900))


def git_part():
    git(["log", "--all", "-S", "INSERT OR IGNORE INTO signals_archive", "--date=iso", "--format=%h %ad %s"])
    for f in ["distribution/archive_bridge.py", "scripts/migrate_signal_archive_to_sqlite.py",
              "data/signals_archive_recovered_20260703.csv", "research/label_entry_basis_backfill_2026_09_03.py",
              "research/ans1_attention_negative_screen_2026_09_18.py",
              "reports/ans1_attention_negative_screen_2026-09-18.md",
              "data/backtest_out/ans1_attention_negative_screen_2026-09-18.json",
              "reports/research_x_ns1_negative_screen_preregistration_2026-09-22.md",
              "reports/research_x_ns1_negative_screen_2026-09-22.md",
              "reports/research_x_capture_1_preregistration_2026-09-22.md",
              "reports/research_x_capture_1_2026-09-22.md",
              "reports/research_x_capture_1_econ_2026-09-23.md",
              "data/backtest_out/fixed_target_full_universe_2026-08-11.md"]:
        git(["log", "--all", "--date=iso", "--format=%h %ad %s", "--", f], limit=6)


# ---------------------------------------------------------------- analytics
def pdate(s):
    try:
        return dt.date.fromisoformat(str(s)[:10])
    except Exception:
        return None


def fnum(v):
    try:
        x = float(v)
        return x if math.isfinite(x) else None
    except Exception:
        return None


def mapst(s):
    s = (s or "").lower()
    if "expired" in s:
        return "expired"
    if "win" in s:
        return "win"
    if "loss" in s:
        return "loss"
    return s or "none"


def bucket(lag):
    if lag is None:
        return "missing"
    if lag < 0:
        return "<0"
    if lag == 0:
        return "0"
    if lag <= 4:
        return "1-4"
    if lag <= 145:
        return "5-145"
    return ">145"


def load_archive():
    con = sqlite3.connect("file:C:/Users/meric/Borsa/data/finpilot.db?mode=ro", uri=True)
    con.execute("PRAGMA query_only=ON")
    rows = con.execute("SELECT id, symbol, ts, payload_json, resolved_status_barrier, resolved_pct_barrier "
                       "FROM signals_archive").fetchall()
    con.close()
    recs = []
    for rid, sym, ts, pj, st, pct in rows:
        try:
            p = json.loads(pj) if pj else {}
        except Exception:
            p = {}
        if not isinstance(p, dict):
            p = {}
        r = dict(id=rid, sym=(sym or "").strip().upper(), ts=str(ts or ""), ts_date=pdate(ts),
                 sig=pdate(p.get("signal_date")), added=str(p.get("added_at") or ""),
                 entry=fnum(p.get("entry_price")), tp=fnum(p.get("take_profit")), sl=fnum(p.get("stop_loss")),
                 st=st, pct=fnum(pct))
        r["lag"] = (r["ts_date"] - r["sig"]).days if (r["ts_date"] and r["sig"]) else None
        recs.append(r)
    return recs


def cluster_ci(x, g, B=4000, seed=20261019):
    x = np.asarray(x, float)
    if len(x) < 3:
        return None
    m = float(x.mean())
    keys = sorted(set(g))
    idx = {k: i for i, k in enumerate(keys)}
    gi = np.array([idx[k] for k in g])
    G = len(keys)
    S = np.bincount(gi, weights=x - m, minlength=G)
    se = math.sqrt(G / max(G - 1, 1) * float((S ** 2).sum())) / len(x)
    sums = np.bincount(gi, weights=x, minlength=G)
    cnts = np.bincount(gi, minlength=G).astype(float)
    rng = np.random.default_rng(seed)
    draw = rng.integers(0, G, size=(B, G))
    bm = sums[draw].sum(1) / cnts[draw].sum(1)
    lo, hi = np.percentile(bm, [2.5, 97.5])
    return dict(n=len(x), days=G, mean=m, median=float(np.median(x)), sum=float(x.sum()),
                cr_lo=m - 1.96 * se, cr_hi=m + 1.96 * se, bs_lo=float(lo), bs_hi=float(hi))


def fmt(d):
    if d is None:
        return "NA"
    return ("n=%d days=%d mean=%.4f median=%.4f sum=%.2f CR95=[%.4f,%.4f] BOOT95=[%.4f,%.4f]" % (
        d["n"], d["days"], d["mean"], d["median"], d["sum"], d["cr_lo"], d["cr_hi"], d["bs_lo"], d["bs_hi"]))


_cache = {}


def bars(sym):
    if sym in _cache:
        return _cache[sym]
    out = None
    p = os.path.join(ROOT, "data", "price_cache", sym + ".json")
    try:
        with open(p, "r", encoding="utf-8") as fh:
            d = json.load(fh)
        if isinstance(d, dict):
            for k in ("bars", "data", "prices"):
                if isinstance(d.get(k), list):
                    d = d[k]
                    break
        if isinstance(d, list):
            tmp = {}
            for b in d:
                try:
                    dd = pdate(b["date"])
                    h, lo, c = float(b["high"]), float(b["low"]), float(b["close"])
                    if dd is None or not all(math.isfinite(v) for v in (h, lo, c)):
                        continue
                    tmp[dd] = (h, lo, c)
                except Exception:
                    continue
            out = sorted((k,) + v for k, v in tmp.items())
    except Exception:
        out = None
    _cache[sym] = out
    return out


def replay(b, base, entry, tp, sl, cap):
    if not b or not entry or entry <= 0 or tp is None or sl is None:
        return ("noinput", None, None)
    lim = base + dt.timedelta(days=cap) if cap else None
    fut = [x for x in b if x[0] > base and (lim is None or x[0] <= lim)][:21]
    if not fut:
        return ("nodata", None, None)
    for d, h, lo, c in fut:
        if tp > 0 and h >= tp:
            return ("win", round((tp - entry) / entry * 100.0, 4), d)
        if sl > 0 and lo <= sl:
            return ("loss", round((sl - entry) / entry * 100.0, 4), d)
    return ("expired", round((fut[-1][3] - entry) / entry * 100.0, 4), fut[-1][0])


def analytics():
    recs = load_archive()
    N = len(recs)
    print("=== STRUCTURAL (all rows, status-agnostic) N=%d ===" % N)
    lb = Counter(bucket(r["lag"]) for r in recs)
    print("LAG_BUCKETS_ALL", sorted(lb.items()))
    late_all = [r["lag"] for r in recs if r["lag"] is not None and r["lag"] >= 5]
    print("LATE_ALL n=%d min=%s max=%s" % (len(late_all), min(late_all) if late_all else None,
                                           max(late_all) if late_all else None))
    same_added = sum(1 for r in recs if r["added"] and r["ts"][:16] == r["added"][:16])
    print("TS_EQ_ADDED_AT_MINUTE %d of %d with added_at=%d" % (
        same_added, N, sum(1 for r in recs if r["added"])))
    wd = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    print("TS_WEEKDAY", Counter(wd[r["ts_date"].weekday()] for r in recs if r["ts_date"]).most_common())
    print("SIG_WEEKDAY", Counter(wd[r["sig"].weekday()] for r in recs if r["sig"]).most_common())
    hm = Counter(r["ts"][11:16] for r in recs)
    print("TS_HHMM_TOP", hm.most_common(6))
    for t, _ in hm.most_common(3):
        print("HHMM %s x lag bucket %s" % (t, sorted(Counter(bucket(r["lag"]) for r in recs
                                                           if r["ts"][11:16] == t).items())))
    lt = defaultdict(list)
    for r in recs:
        if r["lag"] is not None and r["lag"] >= 5:
            lt[r["ts_date"]].append(r["sig"])
    print("TOP_TS_DATES_WITH_LATE_ROWS (ts_date n min_sig max_sig n_sig weekday)")
    for d, sigs in sorted(lt.items(), key=lambda kv: -len(kv[1]))[:12]:
        print("  %s n=%d sig=%s..%s n_sig=%d %s" % (d, len(sigs), min(sigs), max(sigs), len(set(sigs)),
                                                   wd[d.weekday()]))
    print("ROWS_SIG_AFTER_CUTOFF %d (excluded from all outcome statistics)" % sum(
        1 for r in recs if r["sig"] and r["sig"] > CUTOFF))

    W = [r for r in recs if r["sig"] is not None and r["sig"] <= CUTOFF]
    print("=== OUTCOME WINDOW W: signal_date <= %s, n=%d sig_range=%s..%s ===" % (
        CUTOFF, len(W), min(r["sig"] for r in W), max(r["sig"] for r in W)))
    print("STATUS_W", Counter(r["st"] for r in W).most_common())
    dec = [r for r in W if mapst(r["st"]) in ("win", "loss") and r["pct"] is not None]
    x = [r["pct"] for r in dec]
    print("DECIDED_W n=%d mean=%.4f median=%.4f hit=%.4f mean_abs=%.4f" % (
        len(dec), float(np.mean(x)), float(np.median(x)),
        sum(1 for r in dec if mapst(r["st"]) == "win") / len(dec), float(np.mean(np.abs(x)))))
    print("DECIDED_W lag buckets", sorted(Counter(bucket(r["lag"]) for r in dec).items()))
    print("DECIDED_W ALL ", fmt(cluster_ci(x, [r["sig"] for r in dec])))

    k = int(len(dec) * 0.01)
    top = sorted(dec, key=lambda r: -r["pct"])[:k]
    tsc = Counter(r["ts_date"] for r in top)
    sgc = Counter(r["sig"] for r in top)
    two = sum(c for _, c in tsc.most_common(2))
    print("=== B1 TOP1PCT (W) k=%d distinct_ts=%d distinct_sig=%d top2_ts_share=%d/%d ===" % (
        k, len(tsc), len(sgc), two, k))
    print("TOP_TS", [(str(d), c, wd[d.weekday()]) for d, c in tsc.most_common(6)])
    print("TOP_SIG", [(str(d), c) for d, c in sgc.most_common(15)])
    print("TOP_LAG_BUCKETS", sorted(Counter(bucket(r["lag"]) for r in top).items()))
    print("TOP_min_pct=%.4f max_pct=%.4f" % (min(r["pct"] for r in top), max(r["pct"] for r in top)))

    print("=== B2 GROUPS (W decided; clusters = signal_date) ===")
    tot = float(sum(x))
    rows_out = []
    for name, cond in [("on_time_lag0", lambda r: r["lag"] == 0),
                       ("lag1_4", lambda r: r["lag"] is not None and 1 <= r["lag"] <= 4),
                       ("lag0_4", lambda r: r["lag"] is not None and 0 <= r["lag"] <= 4),
                       ("late_lag5_145", lambda r: r["lag"] is not None and 5 <= r["lag"] <= 145),
                       ("lag_gt145", lambda r: r["lag"] is not None and r["lag"] > 145),
                       ("lag_neg", lambda r: r["lag"] is not None and r["lag"] < 0)]:
        g = [r for r in dec if cond(r)]
        if not g:
            print(name, "n=0")
            continue
        ci = cluster_ci([r["pct"] for r in g], [r["sig"] for r in g])
        share = (ci["sum"] / tot) if tot else float("nan")
        lagv = [r["lag"] for r in g]
        print("%s %s share_of_sum=%.4f lag_range=%d..%d" % (name, fmt(ci), share, min(lagv), max(lagv)))
        rows_out.append([name, ci["n"], ci["days"], round(ci["mean"], 4), round(ci["median"], 4),
                         round(ci["sum"], 4), round(share, 4), round(ci["cr_lo"], 4), round(ci["cr_hi"], 4),
                         round(ci["bs_lo"], 4), round(ci["bs_hi"], 4)])
    with open(os.path.join(AUD, "data", "RT_b2_groups.csv"), "w", newline="", encoding="ascii") as fh:
        w = csv.writer(fh)
        w.writerow(["group", "n", "signal_days", "mean_pct", "median_pct", "sum_pct", "share_of_sum",
                    "cr95_lo", "cr95_hi", "boot95_lo", "boot95_hi"])
        w.writerows(rows_out)
    print("TOTAL_SUM_W=%.4f" % tot)

    print("=== B11 REPLAY (approximation on cached daily bars; TP checked before SL; <=21 bars) ===")
    aff = [r for r in dec if r["lag"] is not None and r["lag"] >= 1]
    ctl = [r for r in dec if r["lag"] == 0]
    print("AFFECTED_DECIDED_W (lag>=1) n=%d ; lag>=5 n=%d ; all-rows lag>=1 (status-agnostic) n=%d" % (
        len(aff), sum(1 for r in aff if r["lag"] >= 5), sum(1 for r in recs if r["lag"] is not None and r["lag"] >= 1)))
    out_rows = []
    for label, group in (("affected", aff), ("control_lag0", ctl)):
        for cap in (30, None):
            agree_ts = agree_sig = usable = 0
            trans = Counter()
            known_before_ts = 0
            first_bar_ts = 0
            pct_sig = []
            pct_st = []
            for r in group:
                b = bars(r["sym"])
                a_ = replay(b, r["ts_date"], r["entry"], r["tp"], r["sl"], cap)
                s_ = replay(b, r["sig"], r["entry"], r["tp"], r["sl"], cap)
                if a_[0] in ("noinput", "nodata") or s_[0] in ("noinput", "nodata"):
                    continue
                usable += 1
                stored = mapst(r["st"])
                agree_ts += int(a_[0] == stored)
                agree_sig += int(s_[0] == stored)
                trans[(stored, s_[0])] += 1
                if s_[0] in ("win", "loss") and s_[2] is not None and s_[2] < r["ts_date"]:
                    known_before_ts += 1
                fut = [x_ for x_ in b if x_[0] > r["ts_date"]]
                if a_[0] in ("win", "loss") and fut and a_[2] == fut[0][0]:
                    first_bar_ts += 1
                pct_sig.append(s_[1])
                pct_st.append(r["pct"])
                if label == "affected" and cap == 30:
                    out_rows.append([r["id"], r["sym"], r["sig"], r["ts_date"], r["lag"], stored, r["pct"],
                                     a_[0], a_[1], s_[0], s_[1], s_[2]])
            if usable:
                print("%s cap=%s usable=%d/%d agree_ts_basis=%.4f agree_sig_basis=%.4f "
                      "resolved_before_ts_under_sig_basis=%.4f first_bar_after_ts_resolution=%.4f "
                      "mean_stored=%.4f mean_replay_sig_basis=%.4f" % (
                          label, cap, usable, len(group), agree_ts / usable, agree_sig / usable,
                          known_before_ts / usable, first_bar_ts / usable, float(np.mean(pct_st)),
                          float(np.mean(pct_sig))))
                print("   stored->sig_basis transitions", sorted(trans.items()))
    with open(os.path.join(AUD, "data", "RT_b11_replay.csv"), "w", newline="", encoding="ascii") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "symbol", "signal_date", "ts_date", "lag_days", "stored_status", "stored_pct",
                    "replay_ts_status", "replay_ts_pct", "replay_sig_status", "replay_sig_pct",
                    "replay_sig_resolution_date"])
        for row in out_rows:
            w.writerow([safe(v, 80) for v in row])
    print("REPLAY_CSV_ROWS %d ; price_cache symbols loaded=%d missing=%d" % (
        len(out_rows), len(_cache), sum(1 for v in _cache.values() if v is None)))


def nan_semantics():
    print("=== NAN SEMANTICS (pure Python, mirrors expressions only) ===")
    nan = float("nan")
    print("max(0,min(100,nan/16.5*100)) =", max(0.0, min(100.0, (nan / 16.5) * 100.0)))
    print("min(1,max(0,nan)) =", min(1.0, max(0.0, nan)), " max(0,min(1,nan)) =", max(0.0, min(1.0, nan)))
    print("round(nan,4) =", round(nan, 4), " nan>=4.0 =", nan >= 4.0, " nan>0 =", nan > 0)


if __name__ == "__main__":
    run("code_part", code_part)
    run("fixed_target_lists", fixed_target_lists)
    run("git_part", git_part)
    run("analytics", analytics)
    run("nan_semantics", nan_semantics)
    print("DONE_RT")
