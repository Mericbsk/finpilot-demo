# ENX_paths.py - R6: signal metadata, level geometry and daily-bar path statistics (read-only).
# Outcome/path statistics only for payload signal_date <= 2026-05-21 (C1 locked-OOS boundary);
# later rows are counted only. Output: ../data/ENX_paths_out.txt (ends with DONE_ENX).
import bisect
import csv
import datetime as dt
import hashlib
import json
import os
import re
import sqlite3
import sys
import traceback
from collections import Counter, defaultdict

import numpy as np

ROOT = r"C:\Users\meric\Borsa"
AUDIT = os.path.join(ROOT, "reports", "scanner_intelligence_audit_v1_2026-10-19")
DATA = os.path.join(AUDIT, "data")
OUT = os.path.join(DATA, "ENX_paths_out.txt")
ROWS_CSV = os.path.join(DATA, "ENX_paths_rows.csv")
MANIFEST = os.path.join(DATA, "ENX_price_cache_manifest.csv")
LOCK_CUTOFF = "2026-05-21"
PIT = ("2026-06-09", "2026-06-30")
os.makedirs(DATA, exist_ok=True)
_fh = open(OUT, "w", encoding="utf-8", errors="replace")
sys.stdout = _fh
sys.stderr = _fh

FMTS = ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M")


def parse_ts(ts):
    # replica of scripts/resolve_open_signals.py:_parse_ts
    if not ts:
        return None
    for fmt in FMTS:
        try:
            return dt.datetime.strptime(ts[:26], fmt).date()
        except ValueError:
            continue
    return None


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def q(arr, scale=1.0):
    a = np.asarray([x for x in arr if x is not None and np.isfinite(x)], dtype=float) * scale
    if a.size == 0:
        return "n=0"
    p = np.percentile(a, [10, 25, 50, 75, 90])
    return "n=%d mean=%.3f p10=%.3f p25=%.3f p50=%.3f p75=%.3f p90=%.3f" % ((a.size, a.mean()) + tuple(p))


def share(flags):
    f = [x for x in flags if x is not None]
    return "%d/%d=%.1f%%" % (sum(f), len(f), 100.0 * sum(f) / len(f)) if f else "0/0"


def show(relpath, pattern=None, ranges=None, cap=60, ctx=0):
    path = os.path.join(ROOT, relpath.replace("/", os.sep))
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        lines = fh.read().splitlines()
    print("--- SRC %s (%d lines)" % (relpath, len(lines)))
    idx = set()
    if pattern:
        rx = re.compile(pattern)
        for i, line in enumerate(lines, 1):
            if rx.search(line):
                idx.update(range(max(1, i - ctx), min(len(lines), i + ctx) + 1))
    for a, b in ranges or []:
        idx.update(range(a, min(b, len(lines)) + 1))
    for n, k in enumerate(sorted(idx)):
        if n >= cap:
            print("  ...[cap]")
            break
        print("%5d| %s" % (k, lines[k - 1].rstrip()[:170]))


def code_checks():
    print("======== K. CODE VERIFICATION ========")
    show("scanner/evaluate.py", r"calculate_risk_management\(|^_COST_FLAT_PCT|^_THIN_EDGE_THRESH|^_DECAY_EV_THRESH", ctx=2, cap=30)
    show("scanner/data_fetcher.py", r"\[:-1\]|incomplete|partial|forming|is_closed|completed|drop_last|last_bar|in.progress|still open", cap=30)
    show("core/slippage_tracker.py", r"def |class |commission|lambda|_bps|BPS|spread|gap|round_trip|_PCT\b", cap=70)
    show("scanner/execution_policy.py", r"spread|adv|feasib|[Tt]ier|threshold|max_|min_", cap=40)
    show("core/paper_portfolio.py", r"bps|cost|slippage|commission|fee|_COST", cap=20)
    show("core/outcome_reconciler.py", ranges=[(60, 90), (120, 142)], cap=60)


def load_bars(sym, cache, used):
    if sym in cache:
        return cache[sym]
    pc = os.path.join(ROOT, "data", "price_cache")
    path = None
    for c in (sym, sym.replace(".", "-"), sym.replace("/", "-"), sym.replace("-", ".")):
        pth = os.path.join(pc, c + ".json")
        if os.path.exists(pth):
            path = pth
            break
    if path is None:
        cache[sym] = None
        return None
    with open(path, "r", encoding="utf-8") as fh:
        raw = json.load(fh)
    byd, bad = {}, 0
    for bar in raw if isinstance(raw, list) else []:
        try:
            d = str(bar["date"])[:10]
            o, h, lo, c = float(bar["open"]), float(bar["high"]), float(bar["low"]), float(bar["close"])
        except Exception:
            bad += 1
            continue
        if not np.all(np.isfinite([o, h, lo, c])) or min(o, h, lo, c) <= 0:
            bad += 1
            continue
        byd[d] = (o, h, lo, c)
    ds = sorted(byd)
    b = {"d": ds, "o": [byd[x][0] for x in ds], "h": [byd[x][1] for x in ds],
         "l": [byd[x][2] for x in ds], "c": [byd[x][3] for x in ds], "bad": bad}
    cache[sym] = b
    used[os.path.basename(path)] = path
    return b


def replay(b, start, e, tp, sl):
    n = len(b["d"])
    if start >= n:
        return ("nodata", None, False, False, False, None)
    end = min(n, start + 21)
    for i in range(start, end):
        hi, lo, op = b["h"][i], b["l"][i], b["o"][i]
        tp_hit = tp > 0 and hi >= tp
        sl_hit = sl > 0 and lo <= sl
        if tp_hit:
            return ("resolved_win", i - start + 1, sl_hit, op >= tp, False, None)
        if sl_hit:
            return ("resolved_loss", i - start + 1, False, False, op <= sl,
                    (op / e - 1.0) * 100.0 if op <= sl else None)
    if end - start == 21:
        return ("expired_win" if b["c"][end - 1] >= e else "expired_loss", 21, False, False, False, None)
    return ("incomplete", None, False, False, False, None)


def main():
    dbp = os.path.join(ROOT, "data", "finpilot.db")
    print("db sha256=%s bytes=%d" % (sha256_file(dbp), os.path.getsize(dbp)))
    con = sqlite3.connect("file:C:/Users/meric/Borsa/data/finpilot.db?mode=ro", uri=True)
    con.execute("PRAGMA query_only=ON")
    print("======== X. EXECUTION TABLES ========")
    print("alpaca_orders n,filled_price_nonnull,filled_qty_nonnull,filled_at_nonnull,min/max created,min/max submitted:",
          con.execute("select count(*), sum(filled_price is not null), sum(filled_qty is not null), "
                      "sum(filled_at is not null), min(created_at), max(created_at), min(submitted_at), "
                      "max(submitted_at) from alpaca_orders").fetchone())
    print("alpaca_orders by type/tif (n, limit_nonnull, stop_nonnull):",
          con.execute("select order_type, time_in_force, count(*), sum(limit_price is not null), "
                      "sum(stop_price is not null) from alpaca_orders group by 1, 2").fetchall())
    print("watchlist_signals n,min/max signal_date,min/max added_at:",
          con.execute("select count(*), min(signal_date), max(signal_date), min(added_at), max(added_at) "
                      "from watchlist_signals").fetchone())
    lc = Counter()
    for (s,) in con.execute("select status_lifecycle from watchlist_signals"):
        try:
            d = json.loads(s) if s else None
            lc[str(d.get("status")) if isinstance(d, dict) else str(s)[:30]] += 1
        except Exception:
            lc[str(s)[:30]] += 1
    print("watchlist_signals status_lifecycle.status top:", lc.most_common(10))

    rows = con.execute("select id, symbol, ts, payload_json, resolved_status, resolved_pct_barrier, "
                       "resolved_status_barrier from signals_archive").fetchall()
    recs = []
    for rid, sym, ts, pj, rs, rpb, rsb in rows:
        try:
            p = json.loads(pj) if pj else {}
        except Exception:
            p = {}
        sd = parse_ts(str(p.get("signal_date"))) if p.get("signal_date") else None
        ts_d = parse_ts(str(ts)) if ts else None
        cohort = "A_entry_ok_key" if "entry_ok" in p else ("B_grade_key" if "grade" in p else "C_other")
        recs.append({
            "id": rid, "sym": str(sym or "").strip().upper(), "ts": str(ts), "sd": sd, "ts_d": ts_d,
            "anchor_res": ts_d or sd, "e": float(p.get("entry_price") or 0), "tp": float(p.get("take_profit") or 0),
            "sl": float(p.get("stop_loss") or 0), "rr_payload": p.get("risk_reward"), "cohort": cohort,
            "eok": p.get("entry_ok"), "rsb": rsb, "rpb": rpb})
    print("======== M. METADATA (all rows; no outcomes) ========")
    print("n_rows=%d cohorts=%s" % (len(recs), Counter(r["cohort"] for r in recs).most_common()))
    print("cohort A entry_ok values:", Counter(str(r["eok"]) for r in recs if r["cohort"] == "A_entry_ok_key").most_common())
    print("signal_date parse fail=%d ts parse fail=%d" % (sum(r["sd"] is None for r in recs), sum(r["ts_d"] is None for r in recs)))
    print("signal_date month counts:", sorted(Counter(str(r["sd"])[:7] for r in recs).items()))
    lockd = [r for r in recs if r["sd"] is None or str(r["sd"]) > LOCK_CUTOFF]
    free = [r for r in recs if r["sd"] is not None and str(r["sd"]) <= LOCK_CUTOFF]
    print("partition: nonlocked(sd<=%s)=%d metadata_only(sd>%s or None)=%d PIT-window rows=%d" % (
        LOCK_CUTOFF, len(free), LOCK_CUTOFF, len(lockd),
        sum(1 for r in recs if r["sd"] and PIT[0] <= str(r["sd"]) <= PIT[1])))
    print("stored barrier status (all):", Counter(r["rsb"] for r in recs).most_common())
    print("stored barrier status nonlocked:", Counter(r["rsb"] for r in free).most_common())
    print("stored barrier status metadata_only partition:", Counter(r["rsb"] for r in lockd).most_common())
    for label, sub in (("ALL", recs), ("DECIDED", [r for r in recs if r["rsb"]])):
        diffs = [(r["anchor_res"] - r["sd"]).days for r in sub if r["anchor_res"] and r["sd"]]
        b = Counter()
        for x in diffs:
            b["<0" if x < 0 else "0" if x == 0 else "1-3" if x <= 3 else "4-7" if x <= 7 else "8-14" if x <= 14 else ">14"] += 1
        print("resolver anchor (ts date first) minus signal_date, %s: buckets=%s %s" % (label, sorted(b.items()), q(diffs)))
    by_key = defaultdict(list)
    for r in recs:
        by_key[(r["sym"], r["sd"])].append(r)
    dup = [v for v in by_key.values() if len(v) > 1]
    same_lv = sum(1 for v in dup if len({(x["e"], x["tp"], x["sl"]) for x in v}) == 1)
    print("same (symbol, signal_date) groups with >1 row=%d extra_rows=%d groups_identical_levels=%d" % (
        len(dup), sum(len(v) - 1 for v in dup), same_lv))
    per_sym = defaultdict(set)
    for r in recs:
        if r["sd"]:
            per_sym[r["sym"]].add(r["sd"])
    gaps = []
    for s, ds in per_sym.items():
        ds = sorted(ds)
        gaps += [(ds[i] - ds[i - 1]).days for i in range(1, len(ds))]
    print("consecutive distinct signal_date gap per symbol (calendar days): <=1 %s, <=7 %s, <=14 %s" % (
        share([g <= 1 for g in gaps]), share([g <= 7 for g in gaps]), share([g <= 14 for g in gaps])))

    print("======== G. LEVEL GEOMETRY (payload levels; no outcomes) ========")
    inval = Counter()
    for r in recs:
        if r["e"] <= 0:
            inval["entry<=0"] += 1
        elif r["tp"] <= r["e"]:
            inval["tp<=entry"] += 1
        elif r["sl"] <= 0 or r["sl"] >= r["e"]:
            inval["sl<=0_or_sl>=entry"] += 1
        else:
            inval["valid"] += 1
    print("level validity:", inval.most_common())
    val = [r for r in recs if r["e"] > 0 and r["tp"] > r["e"] and 0 < r["sl"] < r["e"]]
    for r in val:
        r["stop_pct"] = (r["e"] - r["sl"]) / r["e"] * 100.0
        r["tp_pct"] = (r["tp"] - r["e"]) / r["e"] * 100.0
        r["rr"] = r["tp_pct"] / r["stop_pct"]
        r["ticks"] = (r["e"] - r["sl"]) / 0.01
    for label, sub in (("ALL_VALID", val), ("NONLOCKED_VALID", [r for r in val if r in free])):
        print("%s stop_pct: %s" % (label, q([r["stop_pct"] for r in sub])))
        print("%s tp_pct:   %s" % (label, q([r["tp_pct"] for r in sub])))
        print("%s rr:       %s" % (label, q([r["rr"] for r in sub])))
        print("%s rr round2 top: %s" % (label, Counter(round(r["rr"], 2) for r in sub).most_common(12)))
        print("%s rr round1 top: %s" % (label, Counter(round(r["rr"], 1) for r in sub).most_common(8)))
    print("payload risk_reward==0 share:", share([float(r["rr_payload"] or 0) == 0.0 for r in recs if r["rr_payload"] is not None]))
    edges = [(0, 1), (1, 2), (2, 5), (5, 10), (10, 50), (50, 1e9)]
    for lo, hi in edges:
        sub = [r for r in val if lo <= r["e"] < hi]
        if not sub:
            print("price[%g,%g): n=0" % (lo, hi))
            continue
        print("price[%g,%g): n=%d median_stop_pct=%.3f median_stop_ticks=%.1f stop<10ticks=%s one_tick_pct_median=%.3f one_tick/stop_median=%.3f" % (
            lo, hi, len(sub), np.median([r["stop_pct"] for r in sub]), np.median([r["ticks"] for r in sub]),
            share([r["ticks"] < 10 for r in sub]), np.median([0.01 / r["e"] * 100 for r in sub]),
            np.median([0.01 / (r["e"] - r["sl"]) for r in sub])))
    print("entry<2.0 by cohort:", {c: share([r["e"] < 2.0 for r in val if r["cohort"] == c]) for c in ("A_entry_ok_key", "B_grade_key", "C_other")})

    print("======== P. DAILY-BAR PATH STATISTICS (nonlocked only; approximations) ========")
    cache, used = {}, {}
    stage = Counter()
    out_rows = []
    for r in val:
        if r not in free:
            continue
        stage["nonlocked_valid"] += 1
        b = load_bars(r["sym"], cache, used)
        if b is None:
            stage["no_cache_file"] += 1
            continue
        sds = str(r["sd"])
        st = bisect.bisect_right(b["d"], sds)
        d0 = st - 1
        if d0 < 20 or st >= len(b["d"]):
            stage["no_d0_or_no_future"] += 1
            continue
        stage["computed"] += 1
        c0 = b["c"][d0]
        x = {"id": r["id"], "sym": r["sym"], "sd": sds, "d0": b["d"][d0], "d0_exact": b["d"][d0] == sds,
             "cohort": r["cohort"], "eok": r["eok"], "e": r["e"], "tp": r["tp"], "sl": r["sl"],
             "stop_pct": r["stop_pct"], "tp_pct": r["tp_pct"], "rr": r["rr"], "rsb": r["rsb"]}
        x["e_vs_c0"] = (r["e"] / c0 - 1) * 100
        x["gap_e"] = (b["o"][st] / r["e"] - 1) * 100
        x["gap_c0"] = (b["o"][st] / c0 - 1) * 100
        for k in (1, 5, 10):
            if d0 + k < len(b["d"]):
                x["mfe%d" % k] = (max(b["h"][st:st + k]) / r["e"] - 1) * 100
                x["mae%d" % k] = (min(b["l"][st:st + k]) / r["e"] - 1) * 100
            else:
                x["mfe%d" % k] = x["mae%d" % k] = None
        x["run5"] = (c0 / b["c"][d0 - 5] - 1) * 100
        x["run20"] = (c0 / b["c"][d0 - 20] - 1) * 100
        trs = [max(b["h"][k] - b["l"][k], abs(b["h"][k] - b["c"][k - 1]), abs(b["l"][k] - b["c"][k - 1]))
               for k in range(d0 - 13, d0 + 1)]
        atr = float(np.mean(trs))
        x["atr_pct"] = atr / c0 * 100
        x["stop_atr"] = (r["e"] - r["sl"]) / atr if atr > 0 else None
        x["tp_atr"] = (r["tp"] - r["e"]) / atr if atr > 0 else None
        x["d1_both"] = b["h"][st] >= r["tp"] and b["l"][st] <= r["sl"]
        x["d1_sl"] = b["l"][st] <= r["sl"]
        x["d1_tp"] = b["h"][st] >= r["tp"]
        s1 = replay(b, st, r["e"], r["tp"], r["sl"])
        x["rp_sd"], x["rp_sd_bar"], x["amb_sd"], x["gaptp_sd"], x["gapsl_sd"], x["gapsl_open_pct"] = s1
        if r["anchor_res"]:
            s2 = replay(b, bisect.bisect_right(b["d"], str(r["anchor_res"])), r["e"], r["tp"], r["sl"])
            x["rp_res"], x["amb_res"] = s2[0], s2[2]
            x["anchor_diff"] = (r["anchor_res"] - r["sd"]).days
        else:
            x["rp_res"], x["amb_res"], x["anchor_diff"] = None, None, None
        out_rows.append(x)
    print("stages:", stage.most_common())
    groups = (("ALL", out_rows), ("PAYLOAD_ENTRY_OK_TRUE", [x for x in out_rows if x["eok"] is True]))
    for label, sub in groups:
        print("--- group %s n=%d" % (label, len(sub)))
        print("  d0 exact trading-day match: %s" % share([x["d0_exact"] for x in sub]))
        print("  entry_price vs close(d0) %%: %s" % q([x["e_vs_c0"] for x in sub]))
        print("  |entry/close(d0)-1|<=0.1%%: %s  <=1%%: %s" % (share([abs(x["e_vs_c0"]) <= 0.1 for x in sub]),
                                                         share([abs(x["e_vs_c0"]) <= 1.0 for x in sub])))
        print("  gap next open vs entry %%: %s" % q([x["gap_e"] for x in sub]))
        print("  gap next open vs close(d0) %%: %s" % q([x["gap_c0"] for x in sub]))
        print("  next open above entry by >2%%: %s; below by >2%%: %s" % (
            share([x["gap_e"] > 2 for x in sub]), share([x["gap_e"] < -2 for x in sub])))
        for k in (1, 5, 10):
            print("  MFE%d %%: %s" % (k, q([x["mfe%d" % k] for x in sub])))
            print("  MAE%d %%: %s" % (k, q([x["mae%d" % k] for x in sub])))
        print("  runup5 %%: %s" % q([x["run5"] for x in sub]))
        print("  runup20 %%: %s" % q([x["run20"] for x in sub]))
        print("  daily ATR14 %% of close: %s" % q([x["atr_pct"] for x in sub]))
        print("  stop distance in daily ATR: %s" % q([x["stop_atr"] for x in sub]))
        print("  TP distance in daily ATR: %s" % q([x["tp_atr"] for x in sub]))
        print("  stop<0.5 dailyATR: %s stop<1.0 dailyATR: %s" % (
            share([x["stop_atr"] is not None and x["stop_atr"] < 0.5 for x in sub]),
            share([x["stop_atr"] is not None and x["stop_atr"] < 1.0 for x in sub])))
        print("  d1 low<=SL: %s d1 high>=TP: %s d1 both inside: %s" % (
            share([x["d1_sl"] for x in sub]), share([x["d1_tp"] for x in sub]), share([x["d1_both"] for x in sub])))
        print("  replay(signal_date anchor) status: %s" % Counter(x["rp_sd"] for x in sub).most_common())
        dec = [x for x in sub if x["rp_sd"] in ("resolved_win", "resolved_loss")]
        print("  first touch on bar 1 (decided): %s" % share([x["rp_sd_bar"] == 1 for x in dec]))
        wins = [x for x in sub if x["rp_sd"] == "resolved_win"]
        losses = [x for x in sub if x["rp_sd"] == "resolved_loss"]
        print("  ambiguous (TP and SL both in hit bar) among replay wins: %s; among decided: %s" % (
            share([x["amb_sd"] for x in wins]), share([x["amb_sd"] for x in dec])))
        print("  gap-through-stop among replay losses: %s; open-based minus SL-based pct: %s" % (
            share([x["gapsl_sd"] for x in losses]),
            q([x["gapsl_open_pct"] - (x["sl"] / x["e"] - 1) * 100 for x in losses if x["gapsl_open_pct"] is not None])))
        print("  gap-through-TP among replay wins: %s" % share([x["gaptp_sd"] for x in wins]))
        stored = [x for x in sub if x["rsb"] in ("resolved_win", "resolved_loss", "expired_win", "expired_loss")]
        for an in ("rp_sd", "rp_res"):
            comp = [x for x in stored if x[an] not in (None, "nodata", "incomplete")]
            print("  stored status == replay(%s): %s" % (an, share([x[an] == x["rsb"] for x in comp])))
        diffa = [x for x in stored if x["anchor_diff"] not in (None, 0)]
        for an in ("rp_sd", "rp_res"):
            comp = [x for x in diffa if x[an] not in (None, "nodata", "incomplete")]
            print("  [anchor differs] stored == replay(%s): %s" % (an, share([x[an] == x["rsb"] for x in comp])))
        same = [x for x in stored if x["anchor_diff"] == 0]
        comp = [x for x in same if x["rp_sd"] not in (None, "nodata", "incomplete")]
        print("  [anchor same] stored == replay(rp_sd): %s" % share([x["rp_sd"] == x["rsb"] for x in comp]))
        sw = [x for x in stored if x["rsb"] == "resolved_win" and x["rp_sd"] == "resolved_win"]
        print("  stored wins also replay wins (sd anchor) that are ambiguous: %s" % share([x["amb_sd"] for x in sw]))
    cols = ["id", "sym", "sd", "d0", "d0_exact", "cohort", "eok", "e", "tp", "sl", "stop_pct", "tp_pct", "rr",
            "e_vs_c0", "gap_e", "gap_c0", "mfe1", "mae1", "mfe5", "mae5", "mfe10", "mae10", "run5", "run20",
            "atr_pct", "stop_atr", "tp_atr", "d1_sl", "d1_tp", "d1_both", "rp_sd", "rp_sd_bar", "amb_sd",
            "gaptp_sd", "gapsl_sd", "rp_res", "anchor_diff", "rsb"]
    with open(ROWS_CSV, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(cols)
        for x in out_rows:
            w.writerow([x.get(c) for c in cols])
    man = []
    for name in sorted(used):
        man.append((name, sha256_file(used[name]), len(cache[name[:-5]]["d"]) if cache.get(name[:-5]) else ""))
    with open(MANIFEST, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["file", "sha256", "valid_bars"])
        w.writerows(man)
    agg = hashlib.sha256("".join("%s,%s\n" % (m[0], m[1]) for m in man).encode("ascii")).hexdigest()
    print("price_cache files used=%d aggregate_sha256(name,sha lines)=%s malformed_bars_in_used=%d" % (
        len(man), agg, sum(v["bad"] for v in cache.values() if v)))
    print("rows csv=%s manifest=%s" % (os.path.basename(ROWS_CSV), os.path.basename(MANIFEST)))


for fn in (main, code_checks):
    try:
        fn()
    except Exception:
        print("SECTION_FAIL %s" % fn.__name__)
        traceback.print_exc()
print("DONE_ENX")
_fh.flush()
_fh.close()
