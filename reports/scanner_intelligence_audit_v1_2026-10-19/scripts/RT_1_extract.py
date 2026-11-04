# RT_1_extract.py - read-only, line-numbered extraction for R10 red-team review.
# ASCII only. No network, no writes except stdout. SQLite opened read-only.
import os
import re
import sys
import json
import sqlite3
import subprocess
import traceback
from collections import Counter, defaultdict

sys.stdout.reconfigure(encoding="ascii", errors="backslashreplace")
sys.stderr.reconfigure(encoding="ascii", errors="backslashreplace")

ROOT = r"C:\Users\meric\Borsa"
TOK = re.compile(r"\b(?=[A-Za-z0-9\-]*\d)(?=[A-Za-z0-9\-]*[A-Za-z])[A-Za-z0-9\-]{32,}\b")


def safe(s, n=260):
    s = str(s).rstrip("\r\n")
    s = TOK.sub("<MASKED>", s)
    if len(s) > n:
        s = s[:n] + " ..."
    return s.encode("ascii", "backslashreplace").decode("ascii")


def read_lines(rel):
    p = rel if os.path.isabs(rel) else os.path.join(ROOT, rel)
    with open(p, "r", encoding="utf-8", errors="replace") as f:
        return f.readlines()


def show(rel, start, end, n=260):
    print("=== SHOW %s %d-%d ===" % (rel, start, end))
    try:
        L = read_lines(rel)
        print("TOTAL_LINES %d" % len(L))
        for i in range(max(1, start), min(end, len(L)) + 1):
            print("%s:%d: %s" % (rel, i, safe(L[i - 1], n)))
    except Exception as e:
        print("ERR %s %r" % (rel, e))


def grep(rel, pattern, after=0, before=0, limit=60, n=260, flags=0):
    print("=== GREP %s /%s/ a=%d b=%d ===" % (rel, pattern, after, before))
    try:
        L = read_lines(rel)
        rx = re.compile(pattern, flags)
        shown = set()
        cnt = 0
        for i, line in enumerate(L, 1):
            if rx.search(line):
                cnt += 1
                if cnt > limit:
                    continue
                for j in range(max(1, i - before), min(len(L), i + after) + 1):
                    if j in shown:
                        continue
                    shown.add(j)
                    mark = ">" if j == i else " "
                    print("%s:%d:%s %s" % (rel, j, mark, safe(L[j - 1], n)))
                if after or before:
                    print("--")
        print("MATCHES %d" % cnt)
    except Exception as e:
        print("ERR %s %r" % (rel, e))


def dir_grep(reldir, pattern, limit=40, n=220):
    print("=== DIRGREP %s /%s/ ===" % (reldir, pattern))
    rx = re.compile(pattern)
    cnt = 0
    base = os.path.join(ROOT, reldir)
    for dp, dns, fns in os.walk(base):
        dns[:] = [d for d in dns if d != "__pycache__" and not d.startswith(".")]
        for fn in sorted(fns):
            if not fn.endswith(".py"):
                continue
            p = os.path.join(dp, fn)
            rel = os.path.relpath(p, ROOT).replace("\\", "/")
            try:
                L = read_lines(p)
            except Exception:
                continue
            for i, line in enumerate(L, 1):
                if rx.search(line):
                    cnt += 1
                    if cnt <= limit:
                        print("%s:%d: %s" % (rel, i, safe(line, n)))
    print("MATCHES %d" % cnt)


def doc(rel, head=120, tail=80, full_max=260, n=240, pat=None):
    print("=== DOC %s ===" % rel)
    try:
        L = read_lines(rel)
    except Exception as e:
        print("ERR %r" % e)
        return
    N = len(L)
    print("TOTAL_LINES %d" % N)
    if N <= full_max:
        idx = list(range(1, N + 1))
    else:
        idx = list(range(1, head + 1))
        if pat:
            rx = re.compile(pat, re.I)
            idx += [i for i in range(head + 1, N - tail + 1) if rx.search(L[i - 1])][:60]
        idx += list(range(N - tail + 1, N + 1))
    for i in idx:
        t = L[i - 1]
        if t.strip() == "":
            continue
        print("%s:%d: %s" % (rel, i, safe(t, n)))


def git(args, limit=80, n=200):
    print("=== GIT %s ===" % " ".join(args))
    try:
        r = subprocess.run(["git", "-C", ROOT] + args, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=900)
        L = r.stdout.splitlines()
        print("RC %d N_LINES %d" % (r.returncode, len(L)))
        for line in L[:limit]:
            print(safe(line, n))
        if r.stderr.strip():
            print("STDERR " + safe(r.stderr.strip().splitlines()[0], 300))
        return L
    except Exception as e:
        print("ERR %r" % e)
        return []


def repo_scan():
    print("=== REPO SCAN (code/docs, excludes top-level data/ reports/, hidden dirs, env/secret names) ===")
    pats = {
        "KELLY": re.compile(r"_kelly_reduced_cycle"),
        "INSERT_SA": re.compile(r"INSERT\s+(?:OR\s+\w+\s+)?INTO\s+[\"'`]?signals_archive", re.I),
        "SA": re.compile(r"signals_archive"),
        "CRS": re.compile(r"compute_recommendation_strength"),
        "RANKING": re.compile(r"ranking_score"),
        "DAILY_REPORT": re.compile(r"daily[-_]report"),
    }
    printlines = {"KELLY": 80, "INSERT_SA": 60, "CRS": 40, "RANKING": 40, "DAILY_REPORT": 30}
    exts = (".py", ".ts", ".tsx", ".js", ".mjs", ".cjs", ".json", ".yml", ".yaml", ".toml",
            ".ini", ".sh", ".ps1", ".bat", ".sql", ".md")
    skip = {"node_modules", "venv", "env", "__pycache__", "htmlcov", "site"}
    top_skip = {"data", "reports"}
    files_hit = defaultdict(Counter)
    out = defaultdict(list)
    for dp, dns, fns in os.walk(ROOT):
        top = os.path.normcase(dp) == os.path.normcase(ROOT)
        dns[:] = [d for d in dns if d not in skip and not (d.startswith(".") and d != ".github")
                  and not (top and d in top_skip)]
        for fn in fns:
            low = fn.lower()
            if (low.startswith(".env") or "secret" in low or "token" in low or "credential" in low
                    or "claude_desktop_config" in low or low.endswith((".key", ".pem"))):
                continue
            if not low.endswith(exts):
                continue
            p = os.path.join(dp, fn)
            try:
                if os.path.getsize(p) > 3000000:
                    continue
                L = read_lines(p)
            except Exception:
                continue
            rel = os.path.relpath(p, ROOT).replace("\\", "/")
            for i, line in enumerate(L, 1):
                for k, rx in pats.items():
                    if rx.search(line):
                        files_hit[k][rel] += 1
                        if k in printlines and len(out[k]) < printlines[k]:
                            out[k].append("%s:%d: %s" % (rel, i, safe(line, 220)))
    for k in pats:
        print("--- %s files=%d hits=%d" % (k, len(files_hit[k]), sum(files_hit[k].values())))
        if k == "SA":
            for rel, c in sorted(files_hit[k].items()):
                print("SA_FILE %s %d" % (rel, c))
        for line in out.get(k, []):
            print(line)


def db_survey():
    print("=== DB SURVEY (schema and payload keys only; no outcome statistics) ===")
    con = sqlite3.connect("file:C:/Users/meric/Borsa/data/finpilot.db?mode=ro", uri=True)
    con.execute("PRAGMA query_only=ON")
    tabs = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
    print("TABLES", tabs)
    print("COLS", con.execute("PRAGMA table_info(signals_archive)").fetchall())
    print("IDX", con.execute("PRAGMA index_list(signals_archive)").fetchall())
    print("N_MIN_MAX_TS", con.execute("SELECT COUNT(*), MIN(ts), MAX(ts) FROM signals_archive").fetchone())
    kc = Counter()
    ex = defaultdict(list)
    for (pj,) in con.execute("SELECT payload_json FROM signals_archive ORDER BY rowid"):
        try:
            d = json.loads(pj)
        except Exception:
            kc["<bad_json>"] += 1
            continue
        if not isinstance(d, dict):
            kc["<nondict>"] += 1
            continue
        for k, v in d.items():
            kc[k] += 1
            kl = k.lower()
            if ("date" in kl or "time" in kl or kl.endswith("_at") or "as_of" in kl or kl in ("ts", "asof")) \
                    and len(ex[k]) < 3:
                ex[k].append(safe(v, 40))
    print("PAYLOAD_KEYS", kc.most_common(90))
    for k, v in ex.items():
        print("DATEKEY", k, v)
    con.close()


def config_keys():
    print("=== data/scanner_config.json keys (values not printed except target key) ===")
    p = os.path.join(ROOT, "data", "scanner_config.json")
    with open(p, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    print("TOP_KEYS", sorted(cfg.keys()) if isinstance(cfg, dict) else type(cfg))
    if isinstance(cfg, dict) and "_kelly_reduced_cycle" in cfg:
        print("_kelly_reduced_cycle =", safe(json.dumps(cfg["_kelly_reduced_cycle"]), 200))
    else:
        print("_kelly_reduced_cycle ABSENT at top level")
    pc = os.path.join(ROOT, "data", "price_cache")
    print("PRICE_CACHE_FILES", len([x for x in os.listdir(pc) if x.endswith(".json")]) if os.path.isdir(pc) else "NO_DIR")


def yf_info():
    print("=== YFINANCE LOCAL METADATA (no import of yfinance) ===")
    import importlib.metadata as md
    import importlib.util as iu
    print("yfinance_version", md.version("yfinance"))
    spec = iu.find_spec("yfinance")
    pkg = os.path.dirname(spec.origin)
    print("pkg_dir", safe(pkg, 200))
    q = os.path.join(pkg, "scrapers", "quote.py")
    grep(q, r"def last_price|def _get_1y_prices|def _get_exchange_metadata", after=28, limit=4, n=200)


def run(name, fn):
    try:
        fn()
    except Exception:
        print("SECTION_ERR " + name)
        print(safe(traceback.format_exc(), 3000))


def phase_a():
    doc("data/backtest_out/fixed_target_full_universe_2026-08-11.md", full_max=200, n=330)
    pat = r"median|medyan|mean|ortalama|54|export|artefact|artifact|target|hedef|cost|maliyet|verdict|karar|PBO|SPA|oos|holdout|locked|day|gun|concentr"
    for rel in ["reports/research_x_capture_1_2026-09-22.md",
                "reports/research_x_capture_1_econ_2026-09-23.md",
                "reports/ans1_attention_negative_screen_2026-09-18.md",
                "reports/research_x_ns1_negative_screen_2026-09-22.md"]:
        doc(rel, head=110, tail=60, full_max=230, n=240, pat=pat)
    dl = "docs/governance/decision-log.md"
    for a, b in [(50, 58), (66, 70), (76, 80), (88, 92), (100, 104), (112, 117), (3282, 3288)]:
        show(dl, a, b, n=650)
    grep(dl, r"RX-CAPTURE|ANS-1|\bNS-1\b|ECON", limit=50, n=320)
    grep(dl, r"2026-05-21", limit=50, n=320)
    grep(dl, r"5,206|5\.206|138[.,]5|NOT_OPENED|MEDIAN DEGENERACY|LockedHoldoutGuard|5,748|common_buy_accuracy", limit=60, n=320)
    show("docs/pitch_deck_finpilot_2026-09-07.html", 94, 98, n=300)
    show("docs/pitch_deck_finpilot_2026-09-07.html", 115, 118, n=300)
    show("docs/pitch_deck_slides_2026-09-07.md", 105, 112, n=300)
    show("distribution/glossary.py", 22, 26, n=300)
    show("distribution/glossary.py", 150, 154, n=300)


def phase_b_code():
    # B3
    show("distribution/snapshot_builder.py", 85, 130)
    grep("distribution/snapshot_builder.py", r"sort|key=|composite_score|ranking_score|execution_confidence|conviction_prob", limit=40)
    show("scanner/evaluate.py", 585, 620)
    grep("scanner/evaluate.py", r"ranking_score|legacy_quality_score", limit=30)
    # B9
    show("scanner/evaluate.py", 270, 330)
    grep("scanner/score_engine.py", r"def |filter_score|volume_spike|price_momentum|trend_strength", limit=90)
    grep("scanner/score_engine.py", r"def score_component_breakdown", after=95, limit=1)
    # B5
    grep("scanner/score_engine.py", r"def compute_recommendation_strength", after=45, limit=1)
    show("scanner/features.py", 170, 240)
    grep("scanner/features.py", r"atr_pct|isnan|isna|fillna|dropna|nan\b", limit=40)
    grep("scanner/evaluate.py", r"atr_pct|isnan|isna|fillna|dropna|len\(df|min_bars|MIN_BARS|compute_recommendation_strength", limit=40)
    # B4
    show("scanner/data_fetcher.py", 850, 890)
    grep("scanner/data_fetcher.py", r"feed|iex|\bsip\b", limit=30)
    grep("scanner/data_fetcher.py", r"^\s*def |^class ", limit=140, n=160)
    dir_grep("scanner", r"avg_volume|dollar_vol|min_volume|MIN_AVG_VOLUME|liquidity|min_dollar", limit=40)
    # B8
    grep("scanner/data_fetcher.py", r"fast_info|last_price", before=8, after=8, limit=8)
    grep("scanner/data_fetcher.py", r"repair", limit=40)
    grep("scanner/data_fetcher.py", r"def \w*repair\w*", after=60, limit=4)
    grep("scanner/data_fetcher.py", r"rate_limit|limiter|acquire|RateLimiter", limit=40)
    grep("core/rate_limiter.py", r"class |def |yfinance|yf\.|alpaca|acquire", limit=80)
    # B6 / B7
    grep("api/routers/scan.py", r"@router\.|^async def |^def |Depends\(|wait_for|timeout|run_in_executor|executor|ThreadPool|daily.report|BaseModel|persist|insert|save_|to_sql|write_text|open\(", limit=220, n=200)
    show("api/routers/scan.py", 890, 940)
    grep("api/routers/scan.py", r"wait_for", before=45, after=40, limit=3, n=200)
    for main in ["api/main.py", "api/app.py"]:
        grep(main, r"include_router|dependencies|Depends|middleware|auth|api_key|APIKey|verify", limit=60)
    dir_grep("api", r"def verify_|APIKeyHeader|HTTPBearer|def require_|def get_current", limit=40)
    # B10
    grep("core/scheduler.py", r"_kelly_reduced_cycle", before=15, after=15, limit=5)
    # B11
    grep("scripts/resolve_open_signals.py", r"^\s*def |_parse_ts|signal_date|entry_price|horizon|HORIZON|max_bars|MAX_BARS|barrier", limit=140, n=200)
    show("scripts/resolve_open_signals.py", 290, 430, n=200)


def git_part():
    git(["rev-parse", "HEAD"])
    git(["log", "--all", "-S", "INSERT INTO signals_archive", "--date=short", "--format=%h %ad %s"], limit=60)
    git(["log", "--all", "-S", "signals_archive", "--date=short", "--format=%h %ad %s"], limit=90)
    git(["log", "--all", "-S", "_kelly_reduced_cycle", "--date=short", "--format=%h %ad %s"], limit=30)
    git(["log", "-n", "25", "--date=short", "--format=%h %ad %s", "--", "scripts/resolve_open_signals.py"], limit=25)
    L = git(["ls-files"], limit=0)
    print("=== ls-files filtered (backfill|archive) ===")
    for line in L:
        low = line.lower()
        if ("backfill" in low or "archive" in low) and not low.startswith("reports/scanner_intelligence_audit"):
            print(safe(line, 200))


if __name__ == "__main__":
    run("phase_a", phase_a)
    run("phase_b_code", phase_b_code)
    run("db_survey", db_survey)
    run("config_keys", config_keys)
    run("yf_info", yf_info)
    run("repo_scan", repo_scan)
    run("git_part", git_part)
    print("DONE_RT")
