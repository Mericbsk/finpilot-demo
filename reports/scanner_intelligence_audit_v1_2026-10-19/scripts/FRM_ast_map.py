# FRM_ast_map.py - R4 audit, read-only static map (no imports of repo modules).
# Prints def line ranges, module constants, sha256 and targeted grep hits.
import ast
import hashlib
import os
import re

ROOT = r"C:\Users\meric\Borsa"
DEF_FILES = [
    "scanner/evaluate.py", "scanner/signals.py", "scanner/features.py",
    "scanner/score_engine.py", "scanner/position_sizer.py", "scanner/risk_engine.py",
    "scanner/execution_policy.py",
]


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


for rel in DEF_FILES:
    p = os.path.join(ROOT, rel)
    if not os.path.exists(p):
        print("MISSING", rel)
        continue
    src = open(p, encoding="utf-8").read()
    tree = ast.parse(src)
    funcs = sorted((n.lineno, n.end_lineno, n.name) for n in ast.walk(tree)
                   if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)))
    consts = []
    for n in tree.body:
        if isinstance(n, (ast.Assign, ast.AnnAssign)):
            t = n.targets[0] if isinstance(n, ast.Assign) else n.target
            if isinstance(t, ast.Name) and (t.id.isupper() or t.id.startswith("_")):
                consts.append("%s@%d" % (t.id, n.lineno))
    imports = []
    for n in tree.body:
        if isinstance(n, ast.Import):
            imports += [a.name for a in n.names]
        elif isinstance(n, ast.ImportFrom):
            imports.append(("." * n.level) + (n.module or ""))
    print("FILE %s lines=%d sha256=%s" % (rel, src.count("\n") + 1, sha(p)))
    print("  imports:", ", ".join(imports))
    print("  defs:", "; ".join("%s:%d-%d" % (nm, a, b) for a, b, nm in funcs))
    print("  consts:", "; ".join(consts))

PATTERNS = {
    "indicator_assign": r"\[[\"'](vol_med20|vol_avg10|macd_hist|ema200|ema50|atr|rsi)[\"']\]\s*=",
    "incomplete_bar": r"incomplete|partial bar|in_progress|iloc\[:-1\]|\[:-1\]|drop_last|today_bar",
    "conviction": r"_CONV_PROB|conviction_tier|conviction_prob",
    "ranking": r"ranking_score\s*=|legacy_quality_score\s*=|position_size\s*=|regime_gate_mult\(|_regime_scale\(",
    "momentum_cfg": r"momentum_z_threshold|momentum_baseline_window|dynamic_threshold|z_threshold_segment",
}
SCAN_DIRS = ["scanner", "core"]
for key, pat in PATTERNS.items():
    rx = re.compile(pat)
    hits = []
    for d in SCAN_DIRS:
        for dp, _, fns in os.walk(os.path.join(ROOT, d)):
            if "__pycache__" in dp:
                continue
            for fn in fns:
                if not fn.endswith(".py"):
                    continue
                fp = os.path.join(dp, fn)
                try:
                    lines = open(fp, encoding="utf-8").read().splitlines()
                except Exception:
                    continue
                for i, line in enumerate(lines, 1):
                    if rx.search(line):
                        hits.append("%s:%d: %s" % (os.path.relpath(fp, ROOT).replace("\\", "/"), i, line.strip()[:140]))
    print("GREP", key, "n=%d" % len(hits))
    for h in hits[:30]:
        print("   ", h)

TEST_NAMES = [
    "check_volume_spike", "analyze_price_momentum", "check_trend_strength",
    "check_timeframe_alignment", "check_momentum_confluence", "compute_recommendation_score",
    "score_component_breakdown", "compute_recommendation_strength", "regime_gate_mult",
    "compute_legacy_quality_score", "calculate_dynamic_position", "_regime_scale",
    "calculate_risk_management_yz", "compute_lottery_factor", "compute_squeeze_factor",
    "compute_overnight_gap_factor", "conviction_tier", "_CONV_PROB", "get_alpha_features",
    "compute_rvol_factor", "compute_gap_factor", "compute_extension_factor", "position_cap",
]
tdir = os.path.join(ROOT, "tests")
tfiles = []
for dp, _, fns in os.walk(tdir):
    if "__pycache__" in dp:
        continue
    for fn in fns:
        if fn.endswith(".py"):
            fp = os.path.join(dp, fn)
            try:
                tfiles.append((os.path.relpath(fp, ROOT).replace("\\", "/"), open(fp, encoding="utf-8").read()))
            except Exception:
                pass
print("TESTS scanned files=%d" % len(tfiles))
for name in TEST_NAMES:
    hit = [f for f, txt in tfiles if re.search(r"\b%s\b" % re.escape(name), txt)]
    print("  %s: %d -> %s" % (name, len(hit), ", ".join(hit[:6])))
