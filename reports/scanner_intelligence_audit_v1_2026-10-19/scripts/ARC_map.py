"""ARC_map.py - read-only architecture extraction for audit role ARC (R2).

Usage:
  python -B ARC_map.py SECTION [SECTION ...]
  python -B ARC_map.py show "relpath:START-END" ["relpath:START-END" ...]
Sections: funcs calls greps flags db files

Read-only: parses repository source with ast (never imports repo modules),
opens data/finpilot.db with mode=ro + PRAGMA query_only=ON (schema and row
counts only), lists file names under data/. Derived outputs are written only
to <audit folder>/data/ARC_*.csv|json.
"""
import ast
import csv
import datetime as dt
import glob
import hashlib
import json
import os
import re
import sqlite3
import sys

REPO = r"C:\Users\meric\Borsa"
AUDIT = os.path.join(REPO, "reports", "scanner_intelligence_audit_v1_2026-10-19")
OUT = os.path.join(AUDIT, "data")
DB_URI = "file:C:/Users/meric/Borsa/data/finpilot.db?mode=ro"
DB_PATH = os.path.join(REPO, "data", "finpilot.db")

MAIN_PY = [
    "api/routers/scan.py",
    "scanner/evaluate.py",
    "scanner/data_fetcher.py",
    "scanner/features.py",
    "scanner/score_engine.py",
    "core/scheduler.py",
    "distribution/jobs.py",
    "distribution/scan_contract.py",
]
ALT_PY = [
    "agents/scanner_agent.py",
    "scanner.py",
    "research/score_replay.py",
    "research/score_bridge.py",
]
INTEREST = re.compile(
    r"scan|evaluat|cycle|resolv|persist|score|composite|rank|shortlist|archive|"
    r"summar|daily|fetch|prefetch|repair|feature|gate|full|contract|watchlist|"
    r"export|enrich|signal|select|filter|replay|bridge|verif",
    re.I,
)
SKIP_CALL_BASE = {
    "len", "str", "int", "float", "bool", "dict", "list", "set", "tuple",
    "print", "isinstance", "getattr", "setattr", "hasattr", "range", "min",
    "max", "sum", "sorted", "enumerate", "zip", "round", "abs", "any", "all",
    "repr", "type", "super", "iter", "next", "debug", "info", "warning",
    "error", "exception", "append", "items", "keys", "values", "format",
    "join", "strip", "lower", "upper", "split", "replace", "startswith",
    "endswith", "update", "pop", "setdefault", "extend", "isoformat",
}
GREPS = [
    ("web/src/app/dashboard/scanner/page.tsx",
     r"BATCH|FULL_UNIVERSE|summar|daily|/scan|for \(|while \(|apiFetch|timeout|Abort|Promise\.all"),
    ("web/src/app/py-api/[...path]/route.ts",
     r"timeout|Timeout|Abort|maxDuration|isScan|http\.request|statusCode|export "),
    ("api/routers/scan.py",
     r"@router\.|run_in_executor|Executor|wait_for|TIMEOUT|timeout|evaluate_symbols|_persist_|"
     r"_auto_add_watchlist|shortlist_|strftime|signals_archive|add_task|create_task|scan_export"),
    ("scanner/evaluate.py",
     r"Executor|max_workers|as_completed|timeout|except|return None|import|compute_|score"),
    ("scanner/score_engine.py",
     r"volume_spike|filter_score|composite_score|weight|getenv|environ"),
    ("scanner/features.py", r"volume_spike|vol_ratio|avg_vol"),
    ("core/scheduler.py",
     r"run_cycle_once|resolv|signals_archive|\[:8\]|add_job|Trigger|AUTOSTART|evaluate|score"),
    ("distribution/jobs.py", r"scan_contract|full|FULL|gate|coverage|raise|import"),
    ("distribution/scan_contract.py",
     r"FULL|full|coverage|min_|threshold|universe|ratio|raise|return"),
    ("docker-compose.yml", r"volumes|/data|finpilot\.db|PY_API|API_URL|timeout"),
]
CODE_DIRS = ["api", "core", "scanner", "distribution", "agents", "scripts"]
GLOBAL_GREPS = [
    ("signals_archive refs", CODE_DIRS,
     r"INSERT\s+(OR\s+\w+\s+)?INTO\s+signals_archive|signals_archive"),
    ("shortlist naming", CODE_DIRS + ["ROOT"], r"shortlist_|%Y%m%d_%H%M"),
    ("production scoring entry points", ["agents", "core", "api", "distribution", "scripts",
                                         "research", "ROOT"],
     r"evaluate_symbols_parallel|from scanner\.score_engine|from scanner\.evaluate|"
     r"import score_engine|compute_composite|def .*composite"),
]
FLAG_RE = re.compile(r"^FINPILOT_[A-Z0-9_]+$")
SHOW_RE = re.compile(r"ENABLE|SUMMARY|EXECUTION_MODE|DISTRIBUTION|LEGACY|AUTOSTART|SHADOW|"
                     r"SQUEEZE|LOTTERY|NEWS|FRED|EDGAR|FUNDAMENTAL|SCAN|BATCH|UNIVERSE|"
                     r"WORKER|TIMEOUT|LLM")
SKIP_DIRS = {"__pycache__", "tests", "node_modules", ".git", ".next", ".venv", "venv",
             ".mypy_cache", ".pytest_cache", ".ruff_cache"}


def out(text):
    sys.stdout.write(str(text).encode("ascii", "replace").decode("ascii") + "\n")


def rel(path):
    return os.path.relpath(path, REPO).replace("\\", "/")


def utc(ts):
    return dt.datetime.fromtimestamp(ts, dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_csv(name, rows, fields):
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, name), "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    out("wrote data/%s rows=%d" % (name, len(rows)))


def write_json(name, obj):
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=1, sort_keys=True)
    out("wrote data/%s" % name)


def all_py_targets():
    paths = [os.path.join(REPO, p) for p in MAIN_PY + ALT_PY]
    paths += sorted(glob.glob(os.path.join(REPO, "research", "*verification*.py")))
    return paths


def parse(path):
    with open(path, "rb") as fh:
        return ast.parse(fh.read(), filename=path)


def collect_defs(tree):
    found = []

    def visit(node, prefix):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                name = prefix + child.name
                if isinstance(child, ast.ClassDef):
                    kind = "class"
                elif isinstance(child, ast.AsyncFunctionDef):
                    kind = "async"
                else:
                    kind = "def"
                decos = []
                for deco in child.decorator_list:
                    try:
                        decos.append(ast.unparse(deco))
                    except Exception:  # noqa: BLE001
                        decos.append("?")
                found.append({"name": name, "kind": kind, "start": child.lineno,
                              "end": child.end_lineno, "decorators": decos, "node": child})
                visit(child, name + ".")
            else:
                visit(child, prefix)

    visit(tree, "")
    return found


def call_name(node):
    func = node.func
    parts = []
    while isinstance(func, ast.Attribute):
        parts.append(func.attr)
        func = func.value
    if isinstance(func, ast.Name):
        parts.append(func.id)
    elif isinstance(func, ast.Call):
        parts.append(call_name(func) + "()")
    else:
        parts.append("?")
    return ".".join(reversed(parts))


def enclosing(defs, line):
    best = None
    for d in defs:
        if d["kind"] == "class" or not (d["start"] <= line <= d["end"]):
            continue
        if best is None or (d["end"] - d["start"]) < (best["end"] - best["start"]):
            best = d
    return best["name"] if best else "<module>"


def iter_code(dirs, exts=(".py",)):
    for d in dirs:
        if d == "ROOT":
            for path in sorted(glob.glob(os.path.join(REPO, "*.py"))):
                yield path
            continue
        base = os.path.join(REPO, d)
        for root, subdirs, files in os.walk(base):
            subdirs[:] = sorted(s for s in subdirs if s not in SKIP_DIRS)
            for name in sorted(files):
                if name.endswith(exts) and not name.startswith("test_"):
                    yield os.path.join(root, name)


def grep_file(path, pattern, cap):
    rx = re.compile(pattern)
    hits = []
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        for i, line in enumerate(fh, 1):
            if rx.search(line):
                hits.append((i, line.rstrip()))
    return hits[:cap], len(hits)


def sec_funcs():
    rows = []
    main = set(os.path.join(REPO, p) for p in MAIN_PY)
    for path in all_py_targets():
        r = rel(path)
        if not os.path.exists(path):
            out("MISSING %s" % r)
            continue
        try:
            tree = parse(path)
        except SyntaxError as exc:
            out("SYNTAX_ERROR %s %s" % (r, exc))
            continue
        defs = collect_defs(tree)
        with open(path, "rb") as fh:
            nlines = fh.read().count(b"\n")
        out("== %s lines=%d defs=%d sha256=%s" % (r, nlines, len(defs), sha256_file(path)[:16]))
        for d in defs:
            rows.append({"file": r, "name": d["name"], "kind": d["kind"], "start": d["start"],
                         "end": d["end"], "decorators": " | ".join(d["decorators"])})
            if path not in main and not INTEREST.search(d["name"]):
                continue
            deco = (" @" + " @".join(d["decorators"]))[:110] if d["decorators"] else ""
            out("  L%d-%d %s %s%s" % (d["start"], d["end"], d["kind"], d["name"], deco))
    write_csv("ARC_function_map.csv", rows, ["file", "name", "kind", "start", "end", "decorators"])


def sec_calls():
    rows = []
    for path in all_py_targets():
        if not os.path.exists(path):
            continue
        r = rel(path)
        try:
            tree = parse(path)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and re.match(
                    r"(scanner|api|core|distribution|agents|research)\b", node.module):
                out("IMPORT %s:%d from %s import %s" % (r, node.lineno, node.module,
                                                        ",".join(a.name for a in node.names)))
        for d in collect_defs(tree):
            if d["kind"] == "class" or not INTEREST.search(d["name"]):
                continue
            seen = {}
            for node in ast.walk(d["node"]):
                if isinstance(node, ast.Call):
                    name = call_name(node)
                    if name.split(".")[-1] in SKIP_CALL_BASE:
                        continue
                    if name not in seen or node.lineno < seen[name]:
                        seen[name] = node.lineno
            calls = sorted(seen.items(), key=lambda kv: kv[1])
            for name, line in calls:
                rows.append({"file": r, "func": d["name"], "callee": name, "line": line})
            out("%s:%s L%d-%d -> %s" % (r, d["name"], d["start"], d["end"],
                                         ", ".join("%s@%d" % kv for kv in calls)))
    write_csv("ARC_calls.csv", rows, ["file", "func", "callee", "line"])


def sec_greps():
    for relpath, pattern in GREPS:
        path = os.path.join(REPO, relpath)
        if not os.path.exists(path):
            out("MISSING %s" % relpath)
            continue
        hits, total = grep_file(path, pattern, 90)
        out("== %s hits=%d sha256=%s" % (relpath, total, sha256_file(path)[:16]))
        for i, line in hits:
            out("  %d: %s" % (i, line.strip()[:170]))
    for label, dirs, pattern in GLOBAL_GREPS:
        out("== GLOBAL %s" % label)
        for path in iter_code(dirs):
            hits, total = grep_file(path, pattern, 5)
            if not total:
                continue
            out("  -- %s hits=%d" % (rel(path), total))
            for i, line in hits:
                out("    %d: %s" % (i, line.strip()[:150]))


def sec_flags():
    rows = []
    paths = list(iter_code(["api", "scanner", "core", "distribution", "agents"]))
    paths.append(os.path.join(REPO, "scanner.py"))
    for path in paths:
        if not os.path.exists(path):
            continue
        try:
            tree = parse(path)
        except SyntaxError:
            continue
        defs = collect_defs(tree)
        hit_keys = set()
        for node in ast.walk(tree):
            flag, callee, extra = None, "", ""
            if isinstance(node, ast.Call):
                for i, arg in enumerate(node.args):
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, str) \
                            and FLAG_RE.match(arg.value):
                        flag, callee = arg.value, call_name(node)
                        extra = ", ".join(ast.unparse(x) for x in node.args[i + 1:])
                        kws = ", ".join("%s=%s" % (k.arg, ast.unparse(k.value))
                                        for k in node.keywords)
                        if kws:
                            extra = (extra + "; " + kws) if extra else kws
                        break
            elif isinstance(node, ast.Subscript):
                sl = node.slice
                if isinstance(sl, ast.Constant) and isinstance(sl.value, str) \
                        and FLAG_RE.match(sl.value):
                    flag, callee = sl.value, "subscript:" + ast.unparse(node.value)
            if flag:
                hit_keys.add((node.lineno, flag))
                rows.append({"flag": flag, "file": rel(path), "line": node.lineno,
                             "enclosing": enclosing(defs, node.lineno), "callee": callee,
                             "args": extra[:120]})
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str) \
                    and FLAG_RE.match(node.value) and (node.lineno, node.value) not in hit_keys:
                rows.append({"flag": node.value, "file": rel(path), "line": node.lineno,
                             "enclosing": enclosing(defs, node.lineno), "callee": "const-ref",
                             "args": ""})
    write_csv("ARC_flag_reads.csv", rows, ["flag", "file", "line", "enclosing", "callee", "args"])
    grouped = {}
    for row in rows:
        grouped.setdefault(row["flag"], []).append(row)
    out("flags_total=%d refs_total=%d" % (len(grouped), len(rows)))
    for flag in sorted(grouped):
        if not SHOW_RE.search(flag):
            continue
        locs = grouped[flag]
        shown = "; ".join("%s:%d[%s|%s|%s]" % (x["file"], x["line"], x["enclosing"],
                                                 x["callee"], x["args"]) for x in locs[:3])
        out("%s n=%d %s%s" % (flag, len(locs), shown, " ..." if len(locs) > 3 else ""))


def sec_db():
    st = os.stat(DB_PATH)
    out("db=data/finpilot.db size=%d mtime_utc=%s" % (st.st_size, utc(st.st_mtime)))
    for suffix in ("-wal", "-shm"):
        out("exists%s=%s" % (suffix, os.path.exists(DB_PATH + suffix)))
    digest = sha256_file(DB_PATH)
    out("db_sha256=%s" % digest)
    con = sqlite3.connect(DB_URI, uri=True)
    try:
        con.execute("PRAGMA query_only=ON")
        tables = [r[0] for r in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
        schema = {}
        for table in tables:
            quoted = '"%s"' % table.replace('"', '""')
            cols = [r[1] for r in con.execute("PRAGMA table_info(%s)" % quoted)]
            count = con.execute("SELECT COUNT(*) FROM %s" % quoted).fetchone()[0]
            schema[table] = {"rows": count, "columns": cols}
            out("%s rows=%d cols=%s" % (table, count, ",".join(cols)))
    finally:
        con.close()
    write_json("ARC_db_schema.json", {"db": "data/finpilot.db", "sha256": digest,
                                      "size": st.st_size, "mtime_utc": utc(st.st_mtime),
                                      "tables": schema})


def sec_files():
    rows = []
    for root, subdirs, files in os.walk(os.path.join(REPO, "data")):
        subdirs[:] = sorted(subdirs)
        for name in files:
            if name.startswith("shortlist_") and name.endswith(".csv"):
                rows.append(os.path.join(root, name))
    out("shortlist_files=%d dirs=%s" % (len(rows), sorted(set(rel(os.path.dirname(p))
                                                               for p in rows))))
    shapes, per_day, records = {}, {}, []
    for path in rows:
        name = os.path.basename(path)
        shape = re.sub(r"\d", "9", name)
        shapes[shape] = shapes.get(shape, 0) + 1
        m = re.match(r"shortlist_(\d{8})_(\d{4})\.csv$", name)
        if m:
            per_day[m.group(1)] = per_day.get(m.group(1), 0) + 1
    out("name_shapes=%s" % shapes)
    out("per_day_last15=%s" % sorted(per_day.items())[-15:])
    for path in sorted(rows):
        name = os.path.basename(path)
        if "20261016" not in name:
            continue
        st = os.stat(path)
        with open(path, "rb") as fh:
            data = fh.read()
        header = data.split(b"\n", 1)[0].decode("utf-8", "replace")
        rec = {"file": rel(path), "mtime_utc": utc(st.st_mtime), "size": st.st_size,
               "data_rows": max(data.count(b"\n") - 1, 0), "sha256": sha256_file(path),
               "header": header[:400]}
        records.append(rec)
        out("SL %s mtime_utc=%s size=%d rows~%d sha256=%s" % (
            rec["file"], rec["mtime_utc"], rec["size"], rec["data_rows"], rec["sha256"]))
    if records:
        out("SL header(first 20161016 file)=%s" % records[0]["header"])
    write_json("ARC_shortlist_files_20261016.json", records)
    out("research verification=%s" % [rel(p) for p in sorted(glob.glob(
        os.path.join(REPO, "research", "*verification*.py")))])
    legacy, archive_ext, rescore = [], {}, []
    for root, subdirs, files in os.walk(REPO):
        subdirs[:] = sorted(s for s in subdirs if s not in SKIP_DIRS
                            and not (root == REPO and s in ("data", "reports", "site")))
        for name in files:
            path = os.path.join(root, name)
            r = rel(path)
            if "_legacy" in name.lower():
                legacy.append(r)
            if r.startswith("archive/"):
                ext = os.path.splitext(name)[1] or "<none>"
                archive_ext[ext] = archive_ext.get(ext, 0) + 1
            if name.endswith(".py") and re.search(r"rescor|replay|recompute|backfill|rescan",
                                                  name, re.I):
                rescore.append(r)
    out("legacy_named=%s" % legacy[:40])
    out("archive_ext_counts=%s" % archive_ext)
    out("rescore_like_py=%s" % rescore[:40])


def show(specs):
    for spec in specs:
        relpath, _, span = spec.rpartition(":")
        start, _, end = span.partition("-")
        path = os.path.join(REPO, relpath)
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            lines = fh.readlines()
        out("== %s:%s-%s" % (relpath, start, end))
        for i in range(int(start), min(int(end), len(lines)) + 1):
            out("%5d| %s" % (i, lines[i - 1].rstrip()[:180]))


SECTIONS = {"funcs": sec_funcs, "calls": sec_calls, "greps": sec_greps,
            "flags": sec_flags, "db": sec_db, "files": sec_files}

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "show":
        show(sys.argv[2:])
    else:
        for section in sys.argv[1:]:
            out("##### SECTION %s" % section)
            SECTIONS[section]()
