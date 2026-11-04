# PERF_code_scan.py - read-only grep of selected FinPilot source files.
# Does not import project code; prints matches with line numbers and enclosing def.
import os
import re
import sys

ROOT = r"C:\Users\meric\Borsa"

KEY_FILES = [
    os.path.join("scanner", "data_fetcher.py"),
    os.path.join("core", "rate_limiter.py"),
    os.path.join("api", "routers", "scan.py"),
]

PAT_KEY = re.compile(
    r"ThreadPoolExecutor|ProcessPoolExecutor|max_workers|run_in_executor|wait_for|"
    r"_SCAN_TIMEOUT|timeout|lru_cache|maxsize|OrderedDict|_CACHE|"
    r"feed|StockBarsRequest|TimeFrame|timeframe|chunk|_BATCH|batch_size|"
    r"yf\.download|Ticker\(|\.history\(|RateLimiter|TokenBucket|rate_limit|acquire|burst|"
    r"capacity|per_second|retry|retries|backoff|sleep\(|scan_timing|active_jobs|peak_active|"
    r"counters_unreliable|caller|yf_fallback|yf_bulk|alpaca_miss|total_s|parquet|pickle|"
    r"read_csv|sqlite|price_cache|intraday|Semaphore|Lock\(|getenv|environ",
    re.I,
)

PAT_POOL = re.compile(
    r"ThreadPoolExecutor\(|ProcessPoolExecutor\(|max_workers|run_in_executor|BoundedSemaphore\(|Semaphore\(",
)
PAT_TIMING_WRITER = re.compile(r"scan_timing|peak_active_jobs|counters_unreliable|active_jobs_at_")
PAT_WEB = re.compile(r"timeout|Timeout|_000|isScan|scan")
PAT_DEF = re.compile(r"^\s*(async\s+def|def|class)\s+([A-Za-z_][A-Za-z0-9_]*)")


def safe(s, n=190):
    s = s.rstrip("\r\n")
    if len(s) > n:
        s = s[:n] + "..."
    return s.encode("ascii", "backslashreplace").decode("ascii")


def read_lines(path):
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        return fh.readlines()


def scan_file(rel, pat, show_outline=False):
    path = os.path.join(ROOT, rel)
    if not os.path.exists(path):
        print("MISSING", rel)
        return
    lines = read_lines(path)
    print("=" * 100)
    print("FILE", rel, "lines=%d" % len(lines))
    cur = "<module>"
    outline = []
    for i, line in enumerate(lines, 1):
        m = PAT_DEF.match(line)
        if m:
            cur = m.group(2)
            outline.append((i, safe(line.strip(), 120)))
        if pat.search(line):
            print("%s:%d [%s] %s" % (rel, i, cur, safe(line.strip())))
    if show_outline:
        print("-- OUTLINE", rel)
        for i, s in outline:
            print("  %d: %s" % (i, s))


def walk(dirs, exts):
    for d in dirs:
        base = os.path.join(ROOT, d)
        for dp, dn, fn in os.walk(base):
            dn[:] = [x for x in dn if x not in ("__pycache__", "node_modules", ".next")]
            for f in sorted(fn):
                if os.path.splitext(f)[1] in exts:
                    yield os.path.relpath(os.path.join(dp, f), ROOT)


def main():
    print("## SECTION 1: key files (pattern matches + outline)")
    for rel in KEY_FILES:
        scan_file(rel, PAT_KEY, show_outline=True)
    print("## SECTION 2: thread/process pools across scanner, core, api")
    for rel in walk(["scanner", "core", "api"], {".py"}):
        lines = read_lines(os.path.join(ROOT, rel))
        cur = "<module>"
        for i, line in enumerate(lines, 1):
            m = PAT_DEF.match(line)
            if m:
                cur = m.group(2)
            if PAT_POOL.search(line):
                print("%s:%d [%s] %s" % (rel, i, cur, safe(line.strip())))
    print("## SECTION 3: timing-log writers")
    for rel in walk(["scanner", "core", "api"], {".py"}):
        lines = read_lines(os.path.join(ROOT, rel))
        for i, line in enumerate(lines, 1):
            if PAT_TIMING_WRITER.search(line):
                print("%s:%d %s" % (rel, i, safe(line.strip())))
    print("## SECTION 4: web py-api proxy timeouts")
    for rel in walk([os.path.join("web", "src", "app", "py-api")], {".ts", ".tsx"}):
        lines = read_lines(os.path.join(ROOT, rel))
        for i, line in enumerate(lines, 1):
            if PAT_WEB.search(line) and ("imeout" in line or "_000" in line or "isScan" in line):
                print("%s:%d %s" % (rel, i, safe(line.strip())))


if __name__ == "__main__":
    sys.exit(main())
