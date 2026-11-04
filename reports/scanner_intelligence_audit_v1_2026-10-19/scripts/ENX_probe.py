# ENX_probe.py - R6 entry/exit audit: read-only code/DB/file probe (ASCII only).
# Writes UTF-8 output to ../data/ENX_probe_out.txt and ends with DONE_ENX.
import ast
import datetime as dt
import hashlib
import json
import os
import re
import sqlite3
import sys
import traceback
from collections import Counter, defaultdict

ROOT = r"C:\Users\meric\Borsa"
AUDIT = os.path.join(ROOT, "reports", "scanner_intelligence_audit_v1_2026-10-19")
OUT = os.path.join(AUDIT, "data", "ENX_probe_out.txt")
os.makedirs(os.path.dirname(OUT), exist_ok=True)
_fh = open(OUT, "w", encoding="utf-8", errors="replace")
sys.stdout = _fh
sys.stderr = _fh

PROD_DIRS = ["scanner", "core", "api", "distribution"]
PRIOR = [
    "reports/entry_quality_experiment_2026-08-06.md",
    "reports/c2c_5d_label_entry_basis_2026-09-03.md",
    "reports/pre_rise_path_battery_2026-08-11.md",
    "docs/2026-08-13-winner-anatomy-exp05-real-first-touch-path.md",
    "reports/high_rvol_raw_ohlc_exit_gate_2026-08-12.md",
    "docs/2026-07-15-p0-execution-replay-full-universe-report.md",
    "reports/research_x_capture_1_2026-09-22.md",
]


def t(s, n=170):
    s = str(s).rstrip("\n").replace("\t", " ")
    return s if len(s) <= n else s[:n] + "...[trunc]"


def rel(path):
    return os.path.relpath(path, ROOT).replace("\\", "/")


def read_lines(path):
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        return fh.read().splitlines()


def section(title):
    print("")
    print("======== " + title + " ========")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def py_files(dirs):
    out = []
    for d in dirs:
        base = os.path.join(ROOT, d)
        for dp, dn, fn in os.walk(base):
            dn[:] = [x for x in dn if x not in ("__pycache__", "node_modules", ".git")]
            for f in fn:
                if f.endswith(".py"):
                    out.append(os.path.join(dp, f))
    return sorted(out)


PATTERNS = [
    ("RESOLVE", r"resolved_pct_barrier|resolved_status_barrier", 30),
    ("ENTRY_OK", r"entry_ok", 45),
    ("PRICE", r"signal_price|entry_price|entry_basis|reference_price|ref_price|fill_price|filled_avg_price|avg_fill", 35),
    ("EXIT", r"take_profit|stop_loss|risk_reward|trailing|time_exit|max_hold|hold_days|horizon_days|tp_mult|sl_mult|atr_mult|TP_MULT|SL_MULT", 45),
    ("COST", r"slippage|commission|spread_bps|bid_ask|bidask|\bspread\b|borrow|market_impact|partial_fill|cost_bps|fee_bps|\bfees?\b", 40),
    ("EXEC", r"EXECUTION_MODE|dry_run|auto_approve|autoapprove|paper_", 35),
    ("DEDUP", r"cooldown|dedup|duplicate|already_", 20),
    ("TF", r"timeframe|interval=|\"1h\"|'1h'|\"4h\"|'4h'|\"15m\"|'15m'|\"1d\"|'1d'|iloc\[-1\]|iloc\[-2\]", 45),
]

cache = {}
hits_by = defaultdict(list)


def func_index(path):
    try:
        tree = ast.parse("\n".join(cache[path]))
    except SyntaxError as exc:
        print("  AST_FAIL %s %s" % (rel(path), exc))
        return []
    out = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out.append((node.name, node.lineno, node.end_lineno))
    out.sort(key=lambda x: x[1])
    return out


def innermost(lineno, idx):
    best = None
    for name, a, b in idx:
        if a <= lineno <= b and (best is None or (b - a) < (best[2] - best[1])):
            best = (name, a, b)
    return best


def run_a():
    files = py_files(PROD_DIRS)
    for f in files:
        cache[f] = read_lines(f)
    section("A. GREP prod dirs %s (%d py files)" % (",".join(PROD_DIRS), len(files)))
    for name, pat, cap in PATTERNS:
        rx = re.compile(pat)
        hits = []
        for f in files:
            for i, line in enumerate(cache[f], 1):
                if rx.search(line):
                    hits.append((f, i, line))
                    hits_by[name].append((f, i))
        per_file = Counter(rel(h[0]) for h in hits)
        print("--- %s total_hits=%d files=%d" % (name, len(hits), len(per_file)))
        for fp, c in per_file.most_common(12):
            print("  FILECOUNT %s %d" % (fp, c))
        for f, i, line in hits[:cap]:
            print("  %s:%d: %s" % (rel(f), i, t(line.strip(), 160)))
        if len(hits) > cap:
            print("  ...[%d more hits not shown]" % (len(hits) - cap))


BUDGET = [950]


def windows(group, name, ffilter, before, after, cap_lines):
    sel = [(f, i) for (f, i) in hits_by[name] if ffilter(rel(f))]
    byfile = defaultdict(list)
    for f, i in sel:
        byfile[f].append(i)
    print("--- WINDOWS %s (%s): %d hits in %d files" % (group, name, len(sel), len(byfile)))
    used = 0
    for f in sorted(byfile):
        lines = cache[f]
        idx = func_index(f)
        ranges = []
        for i in sorted(byfile[f]):
            a = max(1, i - before)
            b = min(len(lines), i + after)
            if ranges and a <= ranges[-1][1] + 1:
                ranges[-1][1] = max(ranges[-1][1], b)
            else:
                ranges.append([a, b, i])
        for a, b, first in ranges:
            n = b - a + 1
            if used + n > cap_lines or BUDGET[0] < n:
                print("  [CAP] skip %s %d-%d" % (rel(f), a, b))
                continue
            print("  >> %s %d-%d func=%s" % (rel(f), a, b, innermost(first, idx)))
            for k in range(a, b + 1):
                print("%5d| %s" % (k, t(lines[k - 1], 160)))
            used += n
            BUDGET[0] -= n


def run_b():
    section("B. FUNCTION INDEX + SOURCE WINDOWS")
    key_files = set()
    for f, _i in hits_by["RESOLVE"]:
        if rel(f).startswith("core/"):
            key_files.add(f)
    for r in ("scanner/evaluate.py", "scanner/features.py", "core/scheduler.py"):
        key_files.add(os.path.join(ROOT, r.replace("/", os.sep)))
    for f in sorted(key_files):
        if f not in cache:
            print("  MISSING " + rel(f))
            continue
        idx = func_index(f)
        print("--- FUNCS %s (%d lines, %d funcs)" % (rel(f), len(cache[f]), len(idx)))
        print("  " + "; ".join("%s %d-%d" % x for x in idx))
    windows("resolver", "RESOLVE", lambda r: r.startswith("core/"), 20, 22, 320)
    windows("entry", "ENTRY_OK", lambda r: r in ("scanner/evaluate.py", "scanner/features.py"), 10, 10, 260)
    windows("exec", "EXEC", lambda r: r == "core/scheduler.py", 6, 10, 150)
    windows("exit", "EXIT", lambda r: r.startswith("scanner/"), 4, 4, 200)


def run_c():
    section("C. DB metadata (read-only)")
    dbp = os.path.join(ROOT, "data", "finpilot.db")
    print("db bytes=%d sha256=%s" % (os.path.getsize(dbp), sha256_file(dbp)))
    for extra in ("finpilot.db-wal", "finpilot.db-shm", "finpilot.db-journal"):
        print("  %s exists=%s" % (extra, os.path.exists(os.path.join(ROOT, "data", extra))))
    con = sqlite3.connect("file:C:/Users/meric/Borsa/data/finpilot.db?mode=ro", uri=True)
    con.execute("PRAGMA query_only=ON")
    tables = [r[0] for r in con.execute("select name from sqlite_master where type='table' order by name")]
    for tb in tables:
        q = tb.replace('"', '""')
        try:
            n = con.execute('select count(*) from "%s"' % q).fetchone()[0]
        except Exception as exc:
            n = "ERR:%s" % exc
        print("  TABLE %s rows=%s" % (tb, n))
        if re.search(r"paper|order|fill|position|trade|execut|watch|approv|outcome|resolv|archive", tb, re.I):
            cc = [r[1] for r in con.execute('PRAGMA table_info("%s")' % q)]
            print("    COLS %s" % cc)
            for c in cc:
                if c.lower() in ("status", "mode", "state", "side", "source", "execution_mode", "kind"):
                    vc = con.execute('select "%s", count(*) from "%s" group by 1 order by 2 desc limit 8' % (c, q)).fetchall()
                    print("    VC %s.%s %s" % (tb, c, vc))
    cols = [r[1] for r in con.execute("PRAGMA table_info(signals_archive)")]
    ci = {c: k for k, c in enumerate(cols)}
    rows = con.execute("select * from signals_archive").fetchall()
    print("signals_archive n_rows=%d cols=%s" % (len(rows), cols))
    for c in cols:
        if "status" in c.lower():
            print("  VC %s %s" % (c, Counter(r[ci[c]] for r in rows).most_common(10)))
    tsv = [str(r[ci["ts"]]) for r in rows]
    print("ts min=%s max=%s samples=%s" % (min(tsv), max(tsv), tsv[:3]))
    print("ts time-of-day top: %s" % Counter(x[11:16] for x in tsv).most_common(8))
    wd = Counter()
    for x in tsv:
        try:
            wd[dt.date.fromisoformat(x[:10]).weekday()] += 1
        except Exception:
            wd[-1] += 1
    print("ts weekday (0=Mon,-1=bad): %s" % sorted(wd.items()))
    payloads = []
    keyfreq = Counter()
    for r in rows:
        raw = r[ci["payload_json"]] if "payload_json" in ci else None
        try:
            pj = json.loads(raw) if raw else None
        except Exception:
            pj = None
        payloads.append(pj)
        if isinstance(pj, dict):
            keyfreq.update(pj.keys())
    print("payload dicts=%d" % sum(isinstance(p, dict) for p in payloads))
    print("payload key freq: %s" % keyfreq.most_common(150))
    for k in sorted(keyfreq):
        if re.search(r"date|time|_ts$|^ts$|as_?of|scan|bar", k, re.I):
            eq = ne = 0
            ex = []
            for x, p in zip(tsv, payloads):
                if isinstance(p, dict) and p.get(k) is not None:
                    if str(p[k])[:10] == x[:10]:
                        eq += 1
                    else:
                        ne += 1
                        if len(ex) < 4:
                            ex.append((x[:19], t(p[k], 40)))
            print("  DATEKEY %s eq_ts_date=%d ne=%d ex=%s" % (k, eq, ne, ex))
    for k in sorted(keyfreq):
        if re.search(r"price|entry|^tp|_tp|^sl|_sl|stop|target|take|close|atr|rr|risk|reward|exit|level|horizon", k, re.I):
            nn = [p[k] for p in payloads if isinstance(p, dict) and p.get(k) is not None]
            print("  PRICEKEY %s nonnull=%d sample=%s" % (k, len(nn), [t(v, 60) for v in nn[:3]]))
    st_col = "resolved_status_barrier" if "resolved_status_barrier" in ci else None
    shown = 0
    for r, p in zip(rows, payloads):
        if st_col and r[ci[st_col]] in ("win", "loss") and shown < 2:
            meta = {c: r[ci[c]] for c in cols if c != "payload_json"}
            print("  EXAMPLE meta: %s" % t(meta, 700))
            print("  EXAMPLE payload: %s" % t(json.dumps(p, default=str), 1600))
            shown += 1
    sym = "symbol" if "symbol" in ci else ("ticker" if "ticker" in ci else None)
    if sym:
        per = defaultdict(list)
        for r, x in zip(rows, tsv):
            per[r[ci[sym]]].append(x[:10])
        cnt = Counter(len(v) for v in per.values())
        same_day = sum(len(v) - len(set(v)) for v in per.values())
        print("symbols=%d rows-per-symbol dist=%s same-symbol-same-tsdate extra rows=%d"
              % (len(per), sorted(cnt.items())[:15], same_day))


def run_d():
    section("D. data/ top-level listing (names only)")
    dd = os.path.join(ROOT, "data")
    for name in sorted(os.listdir(dd)):
        low = name.lower()
        if low.startswith(".env") or any(s in low for s in ("token", "secret", "credential", "password", "apikey", "api_key")):
            print("  [skipped sensitive-looking name]")
            continue
        full = os.path.join(dd, name)
        if os.path.isdir(full):
            try:
                n = len(os.listdir(full))
            except Exception:
                n = -1
            print("  DIR  %s (%d entries)" % (name, n))
        else:
            print("  FILE %s (%d bytes)" % (name, os.path.getsize(full)))


def run_e():
    section("E. lock/holdout discovery (names + decision-log lines)")
    skip = {".git", "node_modules", ".next", ".venv", "venv", "__pycache__", "price_cache", "intraday_cache",
            "site", ".mypy_cache", ".pytest_cache", ".ruff_cache", "scanner_intelligence_audit_v1_2026-10-19"}
    rxn = re.compile(r"holdout|sealed|locked|lock_manifest|quarantine|_oos|oos_", re.I)
    found = []
    for dp, dn, fn in os.walk(ROOT):
        dn[:] = [x for x in dn if x not in skip]
        for f in fn:
            lf = f.lower()
            if lf.startswith(".env"):
                continue
            if rxn.search(f) and not lf.endswith(".lock") and lf != "package-lock.json":
                found.append(rel(os.path.join(dp, f)))
    print("  n=%d" % len(found))
    for x in sorted(found)[:80]:
        print("  LOCKFILE " + x)
    dl = os.path.join(ROOT, "docs", "governance", "decision-log.md")
    if os.path.exists(dl):
        lines = read_lines(dl)
        rx2 = re.compile(r"holdout|sealed|locked|kilitli|\bD7\b|out-of-sample", re.I)
        hh = [(i, l) for i, l in enumerate(lines, 1) if rx2.search(l)]
        print("  decision-log lines=%d matches=%d" % (len(lines), len(hh)))
        for i, l in hh[:45]:
            print("  DLOG:%d: %s" % (i, t(l.strip(), 300)))


def run_f():
    section("F. PRIOR report extraction (read-only)")
    rx_lock = re.compile(r"lock|holdout|sealed|\bOOS\b|out-of-sample", re.I)
    rx_head = re.compile(r"^#+.*(ozet|zet|summary|sonu|verdict|conclusion|tl;dr|karar|result|bulgu)", re.I)
    for pth in PRIOR:
        full = os.path.join(ROOT, pth.replace("/", os.sep))
        if not os.path.exists(full):
            print("--- MISSING " + pth)
            continue
        lines = read_lines(full)
        print("--- PRIOR %s lines=%d" % (pth, len(lines)))
        for i in range(min(8, len(lines))):
            print("  %d: %s" % (i + 1, t(lines[i], 220)))
        lk = [(i, l) for i, l in enumerate(lines, 1) if rx_lock.search(l)]
        print("  lock-matches=%d" % len(lk))
        for i, l in lk[:8]:
            print("  L%d: %s" % (i, t(l.strip(), 220)))
        hd = [i for i, l in enumerate(lines, 1) if rx_head.search(l)]
        if hd:
            s = hd[0]
            print("  summary-heading at %d" % s)
            for i in range(s, min(len(lines), s + 24) + 1):
                print("  %d: %s" % (i, t(lines[i - 1], 220)))


def run_g():
    section("G. price cache structure")
    pc = os.path.join(ROOT, "data", "price_cache")
    if not os.path.isdir(pc):
        print("  no data/price_cache")
        return
    allf = os.listdir(pc)
    fs = sorted(x for x in allf if x.endswith(".json"))
    print("  n_json=%d other=%d" % (len(fs), len(allf) - len(fs)))
    firsts, lasts, nb = [], [], []
    keysets, types = Counter(), Counter()
    bad = 0
    for x in fs:
        try:
            with open(os.path.join(pc, x), "r", encoding="utf-8") as fh:
                d = json.load(fh)
        except Exception:
            bad += 1
            continue
        types[type(d).__name__] += 1
        bars = d if isinstance(d, list) else (d.get("bars") or d.get("data") or [])
        if not bars or not isinstance(bars[0], dict):
            continue
        nb.append(len(bars))
        keysets[tuple(sorted(bars[0].keys()))] += 1
        ds = [str(b.get("date")) for b in bars if isinstance(b, dict) and b.get("date")]
        if ds:
            firsts.append(min(ds))
            lasts.append(max(ds))
    nb.sort()
    print("  bad=%d types=%s" % (bad, dict(types)))
    print("  keysets top=%s" % keysets.most_common(3))
    if nb:
        print("  bars/file min=%d median=%d max=%d" % (nb[0], nb[len(nb) // 2], nb[-1]))
    if firsts:
        print("  first-date min=%s max=%s; last-date min=%s max=%s" % (min(firsts), max(firsts), min(lasts), max(lasts)))
        print("  last-date month dist=%s" % Counter(x[:7] for x in lasts).most_common(8))


def run_h():
    section("H. research exit/cost pattern counts (research/ + root *.py)")
    files = py_files(["research"])
    files += sorted(os.path.join(ROOT, x) for x in os.listdir(ROOT) if x.endswith(".py"))
    pats = [("TRAIL", r"trailing|trail_"), ("TIME", r"time_exit|max_hold|hold_days|horizon"),
            ("COSTR", r"slippage|commission|cost_bps|round.trip|spread_bps|\bspread\b|fee_bps")]
    lines_by = {}
    for f in files:
        try:
            lines_by[f] = read_lines(f)
        except Exception:
            lines_by[f] = []
    for name, pat in pats:
        rx = re.compile(pat, re.I)
        cnt = Counter()
        for f, lines in lines_by.items():
            k = sum(1 for l in lines if rx.search(l))
            if k:
                cnt[rel(f)] = k
        print("--- %s files=%d top=%s" % (name, len(cnt), cnt.most_common(12)))
    rx = re.compile(r"trailing|trail_|time_exit|max_hold|hold_days|horizon|slippage|commission|cost_bps|round.trip|tp_mult|sl_mult|atr_mult|same.bar|both", re.I)
    for r in ("research/score_lab_2_exits.py", "research/full_universe_barrier_backtest.py", "full_universe_barrier_backtest.py"):
        f = os.path.join(ROOT, r.replace("/", os.sep))
        if f not in lines_by:
            print("--- NOTFOUND " + r)
            continue
        hh = [(i, l) for i, l in enumerate(lines_by[f], 1) if rx.search(l)]
        print("--- %s lines=%d matches=%d" % (r, len(lines_by[f]), len(hh)))
        for i, l in hh[:30]:
            print("  %s:%d: %s" % (r, i, t(l.strip(), 160)))


for fn in (run_a, run_b, run_c, run_d, run_e, run_f, run_g, run_h):
    try:
        fn()
    except Exception:
        print("SECTION_FAIL %s" % fn.__name__)
        traceback.print_exc()
print("DONE_ENX")
_fh.flush()
_fh.close()
