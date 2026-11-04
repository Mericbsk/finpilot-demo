# INT_discover.py - R9 (INT) read-only discovery helper. ASCII only.
# Usage: python -B INT_discover.py [all|code|docs|db] | lines relpath:start-end ...
import os, re, sys, json, sqlite3, hashlib, collections, datetime

try:
    sys.stdout.reconfigure(encoding="ascii", errors="backslashreplace")
except Exception:
    pass

ROOT = r"C:\Users\meric\Borsa"
AUD_REL = "reports/scanner_intelligence_audit_v1_2026-10-19"
DB_PATH = os.path.join(ROOT, "data", "finpilot.db")
DB_URI = "file:C:/Users/meric/Borsa/data/finpilot.db?mode=ro"
SKIP = {".git", "node_modules", ".venv", "venv", "__pycache__", ".next", "site",
        ".mypy_cache", ".pytest_cache", ".ruff_cache", "data", "dist", "build"}
OUTCOME_RX = re.compile(r"(?i)resolved|outcome|pnl|return|mfe|mae|win|loss|hit|label|c2c|fwd|forward")
_CACHE = {}


def out(*a):
    print(*a, flush=True)


def rl(path):
    if path not in _CACHE:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            _CACHE[path] = f.read().splitlines()
    return _CACHE[path]


def rel(p):
    return os.path.relpath(p, ROOT).replace("\\", "/")


def walk(base, exts, skip_rel=None, max_bytes=3_000_000):
    b = os.path.join(ROOT, base)
    if os.path.isfile(b):
        yield b
        return
    for dp, dns, fns in os.walk(b):
        dns[:] = [d for d in dns if d not in SKIP]
        if skip_rel and rel(dp).startswith(skip_rel):
            dns[:] = []
            continue
        for fn in fns:
            fp = os.path.join(dp, fn)
            if fn.endswith(exts) and os.path.getsize(fp) <= max_bytes:
                yield fp


def print_func(path, name, maxlines=700):
    lines = rl(os.path.join(ROOT, path))
    start = None
    for i, l in enumerate(lines):
        if re.match(r"\s*(async\s+)?def\s+" + re.escape(name) + r"\b", l):
            start = i
            break
    if start is None:
        out("NOTFOUND %s %s" % (path, name))
        return
    ind0 = len(lines[start]) - len(lines[start].lstrip())
    end = len(lines)
    for j in range(start + 1, len(lines)):
        s = lines[j]
        if not s.strip():
            continue
        ind = len(s) - len(s.lstrip())
        if ind <= ind0 and s.lstrip()[0] not in ")]}":
            end = j
            break
    out("FUNC %s:%s lines %d-%d" % (path, name, start + 1, end))
    for k in range(start, min(end, start + maxlines)):
        out("%5d| %s" % (k + 1, lines[k][:230]))


def mode_lines(specs):
    for sp in specs:
        path, rng = sp.rsplit(":", 1)
        a, b = [int(x) for x in rng.split("-")]
        lines = rl(os.path.join(ROOT, path))
        out("---- %s:%d-%d (file has %d lines)" % (path, a, b, len(lines)))
        for k in range(a - 1, min(b, len(lines))):
            out("%5d| %s" % (k + 1, lines[k][:240]))


def mode_batch(specs):
    # spec: L::relpath::a-b  or  G::relpath_or_dir::regex[::maxhits]
    for sp in specs:
        parts = sp.split("::")
        if parts[0] == "L":
            mode_lines([parts[1] + ":" + parts[2]])
            continue
        path, pat = parts[1], parts[2]
        mx = int(parts[3]) if len(parts) > 3 else 60
        rx = re.compile(pat)
        fp = os.path.join(ROOT, path)
        files = [fp] if os.path.isfile(fp) else list(walk(path, (".py", ".md", ".json", ".yaml", ".yml"), skip_rel=AUD_REL))
        out("==== GREP %s /%s/ files=%d" % (path, pat, len(files)))
        n = 0
        for f in files:
            for i, l in enumerate(rl(f)):
                if rx.search(l):
                    out("%s:%d| %s" % (rel(f), i + 1, l.strip()[:220]))
                    n += 1
                    if n >= mx:
                        break
            if n >= mx:
                break


CODE_PATS = [
    ("SCORE_ASSIGN", r"(finpilot_score|filter_score|composite_score|recommendation_score|final_score)[\"'\]\)]*\s*=[^=]|[\"'](finpilot_score|filter_score|composite_score|recommendation_score)[\"']\s*:"),
    ("ARCHIVE", r"signals_archive"),
    ("BARRIER", r"resolved_pct_barrier|resolved_status_barrier"),
    ("MFE_MAE", r"\bmfe\b|\bmae\b|max_favorable|max_adverse"),
    ("COST", r"(?i)slippage|commission|cost_bps|round_trip|spread_bps|\bfees?\b"),
    ("REGIME", r"vol_regime|market_regime|def \w*regime"),
    ("FRESH", r"(?i)\bstale|freshness|max_age|data_age|last_bar|cache_ttl|\bttl\b"),
    ("COMPLETE", r"(?i)completeness|missing_bars|min_bars|insufficient|data_quality"),
    ("PROVIDER", r"(?i)import yfinance|yf\.download|alpaca|eodhd|polygon|finnhub|tiingo|stooq"),
    ("ENTRY", r"(?i)entry_price|entry_basis|next_open|\bentry\s*="),
    ("FLAGS", r"volume_spike|gap_pct|squeeze|lottery|overnight_gap|catalyst_factor|big_gap|volatility_spike"),
    ("GRADE", r"(?i)\bgrade\b|\btier\b"),
    ("SPEED", r"ThreadPoolExecutor|max_workers|as_completed|asyncio\.gather"),
    ("RANKSORT", r"sort_values\(|sorted\(|\.sort\(|nlargest\("),
]


def mode_code():
    out("#### CODE MAP")
    for path in ["core/scheduler.py", "api/routers/scan.py"]:
        fp = os.path.join(ROOT, path)
        if not os.path.exists(fp):
            out("MISSING", path)
            continue
        out("-- defs/keylines", path, "nlines", len(rl(fp)))
        for i, l in enumerate(rl(fp)):
            if re.match(r"\s*(async\s+)?def\s+\w+", l) or re.search(
                    r"finpilot_score|filter_score|composite|recommendation_score|sort|rank|grade|regime|archive", l):
                out("%s:%d| %s" % (path, i + 1, l.strip()[:200]))
    print_func("core/scheduler.py", "run_cycle_once", 700)
    files = []
    for b in ["scanner", "core", "api", "distribution", "scripts"]:
        files += list(walk(b, (".py",)))
    out("-- py files scanned:", len(files))
    for b in ["scanner", "core", "api", "distribution"]:
        fl = sorted(f for f in files if rel(f).startswith(b + "/"))
        out("DIR", b, "files:", ", ".join("%s(%d)" % (rel(f)[len(b) + 1:], len(rl(f))) for f in fl)[:3000])
    for name, pat in CODE_PATS:
        rx = re.compile(pat)
        per = collections.Counter()
        hits = []
        for f in files:
            for i, l in enumerate(rl(f)):
                if rx.search(l):
                    per[rel(f)] += 1
                    hits.append("%s:%d| %s" % (rel(f), i + 1, l.strip()[:170]))
        out("## PAT", name, "total", len(hits), "files", len(per))
        out("   top files:", ", ".join("%s=%d" % kv for kv in per.most_common(14)))
        for h in [h for h in hits if not h.startswith("scripts/")][:30]:
            out("   " + h)


def mode_docs():
    out("#### DOCS")
    aud = os.path.join(ROOT, AUD_REL)
    names = sorted(os.listdir(aud)) if os.path.isdir(aud) else []
    out("audit folder top-level names:", names)
    brief = [n for n in names if re.search(r"(?i)brief|readme|^00", n) and os.path.isfile(os.path.join(aud, n))]
    rx = re.compile(r"(?i)WP-11|^#+.*\b15\.[123]\b|holdout|sealed|locked|lockbox|signals_archive|\bD7\b")
    for n in brief:
        ls = rl(os.path.join(aud, n))
        out("-- BRIEF CANDIDATE", n, "lines", len(ls))
        c = 0
        for i, l in enumerate(ls):
            if rx.search(l):
                out("%s:%d| %s" % (n, i + 1, l.strip()[:260]))
                c += 1
                if c > 90:
                    break
    md = []
    for b in ["docs", "research", "reports", "_instructions"]:
        md += list(walk(b, (".md", ".json", ".yaml", ".yml", ".txt"), skip_rel=AUD_REL))
    md += [os.path.join(ROOT, f) for f in os.listdir(ROOT) if f.endswith(".md")]
    out("-- doc files scanned:", len(md))
    rx_wp = re.compile(r"WP-11")
    rx_lock = re.compile(r"(?i)(holdout|sealed|locked|lockbox).{0,160}(signals_archive|finpilot\.db)|(signals_archive|finpilot\.db).{0,160}(holdout|sealed|locked|lockbox)")
    rx_d7 = re.compile(r"(?i)\bD7\b.{0,200}(out-of-sample|OOS)|(out-of-sample|\bOOS\b).{0,120}\bD7\b")
    wp, lk, d7 = [], [], []
    for f in md:
        try:
            ls = rl(f)
        except Exception:
            continue
        for i, l in enumerate(ls):
            if rx_wp.search(l):
                wp.append("%s:%d| %s" % (rel(f), i + 1, l.strip()[:200]))
            if rx_lock.search(l):
                lk.append("%s:%d| %s" % (rel(f), i + 1, l.strip()[:280]))
            if rx_d7.search(l):
                d7.append("%s:%d| %s" % (rel(f), i + 1, l.strip()[:280]))
    out("WP-11 hits:", len(wp))
    for h in wp[:20]:
        out("  " + h)
    out("LOCK hits:", len(lk))
    for h in lk[:60]:
        out("  " + h)
    out("D7 hits:", len(d7))
    for h in d7[:15]:
        out("  " + h)


def parse_dt(v):
    if v is None:
        return None
    if isinstance(v, (int, float)):
        x = float(v)
        if x > 1e12:
            x /= 1000.0
        if x < 1e8:
            return None
        return datetime.datetime.utcfromtimestamp(x)
    s = str(v).strip()
    m = re.match(r"(\d{4}-\d{2}-\d{2})(?:[T ](\d{2}):(\d{2}))?", s)
    if not m:
        return None
    d = datetime.datetime.fromisoformat(m.group(1))
    if m.group(2):
        d = d.replace(hour=int(m.group(2)), minute=int(m.group(3)))
    return d


def mode_db():
    out("#### DB")
    st = os.stat(DB_PATH)
    out("db_size_bytes", st.st_size, "mtime_utc", datetime.datetime.utcfromtimestamp(st.st_mtime).isoformat())
    for suf in ("-wal", "-shm", "-journal"):
        if os.path.exists(DB_PATH + suf):
            out("sidecar", suf, os.path.getsize(DB_PATH + suf))
    h = hashlib.sha256()
    with open(DB_PATH, "rb") as f:
        for ch in iter(lambda: f.read(1 << 20), b""):
            h.update(ch)
    out("db_sha256", h.hexdigest())
    con = sqlite3.connect(DB_URI, uri=True)
    con.execute("PRAGMA query_only=ON")
    cur = con.cursor()
    tabs = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
    lockish = re.compile(r"(?i)lock|holdout|seal|partition|split|oos|embargo|freeze|frozen")
    for t in tabs:
        cols = [r[1] for r in cur.execute('PRAGMA table_info("%s")' % t)]
        n = cur.execute('SELECT COUNT(*) FROM "%s"' % t).fetchone()[0]
        flag = " LOCKISH" if lockish.search(t) or any(lockish.search(c) for c in cols) else ""
        out("TABLE %s rows=%d%s cols=%s" % (t, n, flag, ",".join(cols)[:500]))
    sa = "signals_archive"
    info = list(cur.execute("PRAGMA table_info(%s)" % sa))
    for r in cur.execute("SELECT name, sql FROM sqlite_master WHERE tbl_name='signals_archive'"):
        out("  SA_DDL", r[0], (r[1] or "").replace("\n", " ")[:700])
    cols = [r[1] for r in info]
    for c in cols:
        if c == "payload_json":
            continue
        nd, nn = cur.execute('SELECT COUNT(DISTINCT "%s"), SUM("%s" IS NULL) FROM %s' % (c, c, sa)).fetchone()
        line = "  SA %s distinct=%s nulls=%s" % (c, nd, nn)
        if OUTCOME_RX.search(c):
            if nd <= 12:
                vals = [r[0] for r in cur.execute('SELECT DISTINCT "%s" FROM %s' % (c, sa))]
                line += " labelset=%r" % (vals,)
            line += " [outcome column: values not summarized]"
        elif nd <= 25:
            vals = cur.execute('SELECT "%s", COUNT(*) FROM %s GROUP BY 1 ORDER BY 2 DESC' % (c, sa)).fetchall()
            line += " vals=%s" % (repr(vals)[:700])
        else:
            mn, mx = cur.execute('SELECT MIN("%s"), MAX("%s") FROM %s' % (c, c, sa)).fetchone()
            line += " min=%s max=%s" % (str(mn)[:40], str(mx)[:40])
        out(line)
    rows = cur.execute("SELECT rowid, %s, payload_json FROM %s" % ("ts" if "ts" in cols else "NULL", sa)).fetchall()
    out("SA rows", len(rows), "ts examples", [r[1] for r in rows[:3]])
    kc = collections.Counter(); kt = {}; ke = {}; sub = collections.Counter()
    parsed = []
    for rid, ts, pj in rows:
        try:
            d = json.loads(pj) if pj else None
        except Exception:
            kc["<json_error>"] += 1
            continue
        if not isinstance(d, dict):
            kc["<non_dict>"] += 1
            continue
        parsed.append((rid, ts, d))
        for k, v in d.items():
            kc[k] += 1
            kt.setdefault(k, collections.Counter())[type(v).__name__] += 1
            if k not in ke and v is not None:
                ke[k] = "<masked>" if OUTCOME_RX.search(k) else repr(v)[:70]
            if isinstance(v, dict):
                for k2, v2 in v.items():
                    kk = k + "." + k2
                    sub[kk] += 1
                    if kk not in ke and v2 is not None:
                        ke[kk] = "<masked>" if OUTCOME_RX.search(kk) else repr(v2)[:60]
    out("PAYLOAD top-level keys:", len(kc))
    for k, n in sorted(kc.items(), key=lambda x: (-x[1], x[0])):
        out("  PK %-34s n=%6d types=%s ex=%s" % (k, n, dict(kt.get(k, {})), ke.get(k)))
    out("PAYLOAD nested keys:", len(sub))
    for k, n in sorted(sub.items(), key=lambda x: (-x[1], x[0]))[:160]:
        out("  NK %-44s n=%6d ex=%s" % (k, n, ke.get(k)))
    rx_date = re.compile(r"(?i)date|time|^ts$|_ts$|as_?of|scan|generated|created|day")
    cand = [k for k in kc if rx_date.search(k)] + [k for k in sub if rx_date.search(k.split(".")[-1])]
    hrs = collections.Counter(); wds = collections.Counter(); tdays = set()
    tsd = {}
    for rid, ts, d in parsed:
        t = parse_dt(ts)
        tsd[rid] = t
        if t is not None:
            hrs["%02d:%02d" % (t.hour, t.minute)] += 1
            wds[t.strftime("%a")] += 1
            tdays.add(t.date())
    out("ts HH:MM top:", hrs.most_common(12))
    out("ts weekday:", sorted(wds.items()))
    out("ts distinct days:", len(tdays), "min", min(tdays) if tdays else None, "max", max(tdays) if tdays else None)
    for k in cand:
        cnt = collections.Counter(); ex = []; days = set()
        for rid, ts, d in parsed:
            if "." in k:
                a, b = k.split(".", 1)
                v = d.get(a).get(b) if isinstance(d.get(a), dict) else None
            else:
                v = d.get(k)
            pv = parse_dt(v)
            if pv is None:
                cnt["unparsed_or_null"] += 1
                continue
            days.add(pv.date())
            if len(ex) < 3:
                ex.append(repr(v)[:40])
            t = tsd.get(rid)
            if t is None:
                cnt["ts_null"] += 1
                continue
            dd = (t.date() - pv.date()).days
            if dd == 0:
                b = "same"
            elif dd == 1:
                b = "ts_later_1"
            elif 2 <= dd <= 3:
                b = "ts_later_2_3"
            elif 4 <= dd <= 7:
                b = "ts_later_4_7"
            elif dd > 7:
                b = "ts_later_gt7"
            else:
                b = "ts_earlier"
            cnt[b] += 1
        out("  DATECAND %-32s %s days=%d range=%s..%s ex=%s" % (
            k, dict(cnt), len(days), min(days) if days else None, max(days) if days else None, ex))
    con.close()


if __name__ == "__main__":
    args = sys.argv[1:]
    mode = args[0] if args else "all"
    if mode in ("all", "code"):
        mode_code()
    if mode in ("all", "docs"):
        mode_docs()
    if mode in ("all", "db"):
        mode_db()
    if mode == "lines":
        mode_lines(args[1:])
    if mode == "batch":
        mode_batch(args[1:])
    out("DONE_INT")
