# RT_3_followup.py - read-only follow-up checks for R10 (B2 mechanism, B8, B10, B11 within-cache means).
# ASCII only. No network. SQLite read-only. Outcome statistics only for signal_date <= 2026-05-20.
import os
import re
import sys
import csv
import json
import math
import sqlite3
import subprocess
import datetime as dt
from collections import Counter

import numpy as np

sys.stdout.reconfigure(encoding="ascii", errors="backslashreplace")
ROOT = r"C:\Users\meric\Borsa"
AUD = os.path.join(ROOT, "reports", "scanner_intelligence_audit_v1_2026-10-19")
CUTOFF = dt.date(2026, 5, 20)


def safe(s, n=220):
    s = str(s).rstrip("\r\n")
    return (s[:n] + " ...") if len(s) > n else s


def pdate(s):
    try:
        return dt.date.fromisoformat(str(s)[:10])
    except Exception:
        return None


def section(name, fn):
    try:
        fn()
    except Exception as e:
        print("SECTION_ERR %s %r" % (name, e))


def legacy_dir():
    d = os.path.join(ROOT, "data", "signal_archive")
    print("=== LEGACY data/signal_archive exists=%s ===" % os.path.isdir(d))
    if not os.path.isdir(d):
        return
    files = sorted(f for f in os.listdir(d) if f.endswith(".json"))
    print("N_FILES", len(files))
    tot = Counter()
    for f in files:
        p = os.path.join(d, f)
        try:
            data = json.load(open(p, "r", encoding="utf-8"))
        except Exception as e:
            print("FILE %s ERR %r" % (f, e))
            continue
        if not isinstance(data, list):
            print("FILE %s nonlist" % f)
            continue
        added = Counter(str(r.get("added_at") or "")[:16] for r in data if isinstance(r, dict))
        sigs = sorted({str(r.get("signal_date")) for r in data if isinstance(r, dict)})
        batch = added.get("2026-03-01T21:45", 0)
        tot["rows"] += len(data)
        tot["batch_0301_2145"] += batch
        mt = dt.datetime.fromtimestamp(os.path.getmtime(p), dt.timezone.utc).strftime("%Y-%m-%dT%H:%M")
        if batch or len(files) <= 60:
            print("FILE %s rows=%d batch0301=%d sig=%s..%s n_sig=%d mtime_utc=%s top_added=%s" % (
                f, len(data), batch, sigs[0] if sigs else None, sigs[-1] if sigs else None, len(sigs), mt,
                added.most_common(2)))
    print("TOTALS", dict(tot))


def code_checks():
    print("=== CODE ===")
    L = open(os.path.join(ROOT, "scanner", "data_fetcher.py"), encoding="utf-8", errors="replace").readlines()
    for i in range(554, 591):
        if L[i - 1].strip():
            print("scanner/data_fetcher.py:%d: %s" % (i, safe(L[i - 1].encode("ascii", "backslashreplace").decode())))
    rx = re.compile(r"scanner_config\.json|signal_archive[\"'/ ]|/archive\"")
    hits = 0
    for top in ("api", "core", "scanner", "distribution", "scripts", "agents"):
        for dp, dns, fns in os.walk(os.path.join(ROOT, top)):
            dns[:] = [x for x in dns if x != "__pycache__"]
            for fn in fns:
                if not fn.endswith(".py"):
                    continue
                p = os.path.join(dp, fn)
                rel = os.path.relpath(p, ROOT).replace("\\", "/")
                for i, line in enumerate(open(p, encoding="utf-8", errors="replace"), 1):
                    if rx.search(line):
                        hits += 1
                        if hits <= 40:
                            print("%s:%d: %s" % (rel, i, safe(line.strip().encode("ascii", "backslashreplace").decode())))
    print("CODE_HITS", hits)
    r = subprocess.run(["git", "-C", ROOT, "log", "--all", "-S", "signal_archive", "--date=iso",
                        "--format=%h %ad %s", "--reverse"], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=900)
    out = r.stdout.splitlines()
    print("GIT_PICKAXE_signal_archive n=%d first=%s" % (len(out), [safe(x, 120) for x in out[:4]]))


_cache = {}


def bars(sym):
    if sym in _cache:
        return _cache[sym]
    out = None
    try:
        d = json.load(open(os.path.join(ROOT, "data", "price_cache", sym + ".json"), encoding="utf-8"))
        if isinstance(d, list):
            tmp = {}
            for b in d:
                try:
                    k = pdate(b["date"])
                    c = float(b["close"])
                    if k and math.isfinite(c):
                        tmp[k] = c
                except Exception:
                    continue
            out = sorted(tmp.items())
    except Exception:
        out = None
    _cache[sym] = out
    return out


def close_on_or_before(b, day):
    prev = None
    for k, c in b:
        if k > day:
            break
        prev = (k, c)
    return prev


def b11_followup():
    print("=== B11 within-cache means (late decided rows, W) ===")
    rows = list(csv.DictReader(open(os.path.join(AUD, "data", "RT_b11_replay.csv"), encoding="ascii")))
    ts_p = [float(r["replay_ts_pct"]) for r in rows if r["replay_ts_pct"] not in ("", "None")]
    sg_p = [float(r["replay_sig_pct"]) for r in rows if r["replay_sig_pct"] not in ("", "None")]
    st_p = [float(r["stored_pct"]) for r in rows]
    print("n=%d stored_mean=%.4f replay_ts_mean=%.4f (n=%d) replay_sig_mean=%.4f (n=%d) diff_ts_minus_sig=%.4f" % (
        len(rows), np.mean(st_p), np.mean(ts_p), len(ts_p), np.mean(sg_p), len(sg_p), np.mean(ts_p) - np.mean(sg_p)))
    print("replay_ts_hit=%.4f replay_sig_hit=%.4f" % (
        np.mean([r["replay_ts_status"] == "win" for r in rows]), np.mean([r["replay_sig_status"] == "win" for r in rows])))
    con = sqlite3.connect("file:C:/Users/meric/Borsa/data/finpilot.db?mode=ro", uri=True)
    con.execute("PRAGMA query_only=ON")
    ids = {r["id"] for r in rows}
    d_sig = []
    d_ts = []
    for rid, sym, ts, pj in con.execute("SELECT id, symbol, ts, payload_json FROM signals_archive"):
        if rid not in ids:
            continue
        p = json.loads(pj)
        sig = pdate(p.get("signal_date"))
        if sig is None or sig > CUTOFF:
            continue
        e = float(p.get("entry_price") or 0)
        b = bars((sym or "").upper())
        if not b or e <= 0:
            continue
        a = close_on_or_before(b, sig)
        z = close_on_or_before(b, pdate(ts))
        if a and z:
            d_sig.append(abs(e / a[1] - 1))
            d_ts.append(abs(e / z[1] - 1))
    con.close()
    print("ENTRY_VS_CLOSE late rows n=%d median_abs_dev_vs_signal_close=%.4f median_abs_dev_vs_ts_close=%.4f "
          "share_within_1pct_signal=%.4f share_within_1pct_ts=%.4f" % (
              len(d_sig), np.median(d_sig), np.median(d_ts), np.mean(np.array(d_sig) <= 0.01),
              np.mean(np.array(d_ts) <= 0.01)))


def months():
    print("=== ROWS BY SIGNAL MONTH x LAG (all rows, status-agnostic) ===")
    con = sqlite3.connect("file:C:/Users/meric/Borsa/data/finpilot.db?mode=ro", uri=True)
    con.execute("PRAGMA query_only=ON")
    c = Counter()
    for ts, pj in con.execute("SELECT ts, payload_json FROM signals_archive"):
        p = json.loads(pj) if pj else {}
        sig = pdate(p.get("signal_date"))
        t = pdate(ts)
        if not sig or not t:
            continue
        lag = (t - sig).days
        c[(str(sig)[:7], "late" if lag >= 5 else ("ontime" if lag == 0 else "other"))] += 1
    con.close()
    for k in sorted(c):
        print(k, c[k])


if __name__ == "__main__":
    section("legacy_dir", legacy_dir)
    section("code_checks", code_checks)
    section("b11_followup", b11_followup)
    section("months", months)
    print("DONE_RT")
