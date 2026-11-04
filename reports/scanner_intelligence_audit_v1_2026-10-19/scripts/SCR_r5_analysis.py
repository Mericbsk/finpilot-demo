# -*- coding: ascii -*-
"""SCR (R5) read-only analysis, scanner_intelligence_audit_v1_2026-10-19.

Usage: python -B SCR_r5_analysis.py main|prior
Reads repository files read-only. Writes only SCR_* files in the audit data folder.
No network, no database, no scanner imports.
"""
import ast
import glob
import hashlib
import json
import math
import os
import re
import sys
import time
from collections import Counter

import pandas as pd

sys.stdout.reconfigure(encoding="ascii", errors="backslashreplace")

ROOT = r"C:\Users\meric\Borsa"
AUD = os.path.join(ROOT, "reports", "scanner_intelligence_audit_v1_2026-10-19")
OUTD = os.path.join(AUD, "data")
SKIP = {"__pycache__", "node_modules", "site-packages"}
TR = {
    "\u00e7": "c", "\u011f": "g", "\u0131": "i", "\u00f6": "o", "\u015f": "s", "\u00fc": "u",
    "\u00c7": "C", "\u011e": "G", "\u0130": "I", "\u00d6": "O", "\u015e": "S", "\u00dc": "U",
    "\u2014": "-", "\u2013": "-", "\u2192": "->", "\u00d7": "x", "\u2265": ">=", "\u2264": "<=",
    "\u03c1": "rho", "\u2248": "~", "\u2212": "-", "\u00b1": "+/-", "\u2026": "...",
    "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"', "\u0394": "D", "\u03b1": "a",
}


def asc(s, n=200):
    s = "".join(TR.get(ch, ch) for ch in str(s))
    s = s.encode("ascii", "replace").decode("ascii")
    return s if len(s) <= n else s[: n - 3] + "..."


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def rel(p):
    return os.path.relpath(p, ROOT).replace("\\", "/")


def read_lines(p):
    with open(p, encoding="utf-8", errors="replace") as f:
        return f.read().splitlines()


def iter_py(dirs, skip_extra=()):
    skip = SKIP | set(skip_extra)
    for d in dirs:
        base = os.path.join(ROOT, d) if d else ROOT
        if not os.path.isdir(base):
            continue
        for dp, dns, fns in os.walk(base):
            dns[:] = [
                x for x in dns
                if x not in skip and not x.startswith(".") and "venv" not in x.lower()
            ]
            for fn in fns:
                if fn.endswith(".py"):
                    yield os.path.join(dp, fn)


# ---------------------------------------------------------------- flag registry
FLAG_RE = re.compile(r"FINPILOT_ENABLE_[A-Z0-9_]+")
DEF_RE = re.compile(
    r"(?:environ\.get|getenv)\(\s*[\"'](FINPILOT_ENABLE_[A-Z0-9_]+)[\"']\s*(?:,\s*[\"']([^\"']*)[\"'])?"
)


def flag_registry():
    occ, defaults, tests = {}, {}, {}
    for p in iter_py(["scanner", "api", "core", "distribution", "agents"]):
        for i, line in enumerate(read_lines(p), 1):
            for m in FLAG_RE.finditer(line):
                occ.setdefault(m.group(0), []).append("%s:%d" % (rel(p), i))
            for m in DEF_RE.finditer(line):
                defaults.setdefault(m.group(1), set()).add(
                    m.group(2) if m.group(2) is not None else "-"
                )
    for p in iter_py(["tests"]):
        for f in set(FLAG_RE.findall("\n".join(read_lines(p)))):
            tests.setdefault(f, set()).add(os.path.basename(p))
    rows = []
    for f in sorted(occ):
        rows.append({
            "flag": f,
            "n_code_refs": len(occ[f]),
            "defaults": sorted(defaults.get(f, set())),
            "locs": occ[f],
            "n_test_files": len(tests.get(f, ())),
            "test_files": sorted(tests.get(f, ())),
        })
    with open(os.path.join(OUTD, "SCR_flag_registry.json"), "w", encoding="ascii") as fh:
        json.dump(rows, fh, indent=1)
    print("== FLAG REGISTRY n_flags=%d (scanner,api,core,distribution,agents; tests separate)" % len(rows))
    for r in rows:
        print(asc("%s refs=%d def=%s tests=%d %s" % (
            r["flag"], r["n_code_refs"], "/".join(r["defaults"]) or "?", r["n_test_files"],
            " ".join(r["locs"][:2])), 175))


# ---------------------------------------------------------------- code excerpts
def excerpt(relpath, pat, maxn):
    rx = re.compile(pat)
    print("== EXCERPT %s" % relpath)
    n = 0
    for i, line in enumerate(read_lines(os.path.join(ROOT, relpath)), 1):
        if rx.search(line):
            print(asc("%d: %s" % (i, line.strip()), 165))
            n += 1
            if n >= maxn:
                print("  (capped)")
                break


def line_range(relpath, a, b):
    lines = read_lines(os.path.join(ROOT, relpath))
    print("== RANGE %s:%d-%d" % (relpath, a, b))
    for i in range(a, min(b, len(lines)) + 1):
        print(asc("%d: %s" % (i, lines[i - 1].rstrip()), 165))


def repo_grep(token, maxn):
    print("== REPO GREP %r (*.py; excl reports,web,data,docs,site,hidden,venv)" % token)
    n = 0
    for p in iter_py([""], ("reports", "web", "data", "docs", "site", "archive", "notebooks")):
        for i, line in enumerate(read_lines(p), 1):
            if token in line:
                print(asc("%s:%d: %s" % (rel(p), i, line.strip()), 165))
                n += 1
                if n >= maxn:
                    print("  (capped)")
                    return


def code_excerpts():
    excerpt("scanner/execution_policy.py",
            r"def |Tier [012]|execution_feasible|reject_reason\b|_enabled\(\)", 26)
    line_range("scanner/features.py", 410, 419)
    excerpt("scanner/evaluate.py",
            r"kelly|risk_data = |position_cap\(|\"atr_pct\"|sentiment_score = |\"tier\":", 20)
    excerpt("core/scheduler.py", r"kelly_fraction|_cycle_count", 22)
    repo_grep("scanner_config", 22)


# ---------------------------------------------------------------- composite / ties
OBS = {"squeeze_factor": True, "edgar_catalyst": True, "lottery_fade": True, "overnight_gap": False}
MAXR = 16.5
VRW = {0: 2.5, 1: 2.0, 2: 1.5}
GRADE_ORDER = {"A": 0, "B": 1, "C": 2}
EXEC_ORDER = {"Tier 2": 0, "Tier 1": 1, "Tier 0": 2}
NAN_RX = re.compile(r"\bnan\b|\binf\b")


def isnull(v):
    if v is None:
        return True
    return isinstance(v, float) and math.isnan(v)


def tb(v):
    if isnull(v):
        return False
    if isinstance(v, str):
        return v.strip().lower() in ("true", "1", "yes")
    return bool(v)


def is_true(v):
    return v is True or str(v).strip().lower() in {"true", "1", "yes"}


def fnum(v, d=0.0):
    try:
        x = float(v)
    except (TypeError, ValueError):
        return d
    return d if math.isnan(x) else x


def clamp(x, lo, hi):
    return max(lo, min(hi, x))


def pdict(v):
    if isinstance(v, dict):
        return v
    if not isinstance(v, str) or not v.strip().startswith("{"):
        return None
    try:
        return ast.literal_eval(v)
    except Exception:
        try:
            return ast.literal_eval(NAN_RX.sub("None", v))
        except Exception:
            return None


def raw_score(si, flags, macro, sent_delta):
    """Mirror of scanner/score_engine.py:compute_recommendation_score (HEAD 93ae83c)."""
    s = 0.0
    s += 2.0 if tb(si.get("regime", False)) else 0.0
    s += 2.0 if tb(si.get("direction", False)) else 0.0
    s += fnum(si.get("score", 0)) * 0.5
    s += fnum(si.get("filter_score", 0)) * 1.5
    s += fnum(si.get("alignment_ratio", 0.0)) * 2.0
    vr = si.get("vol_regime")
    vr = int(fnum(vr, 1.0)) if vr is not None else 1
    s += fnum(si.get("momentum_ratio", 0.0)) * VRW.get(vr, 2.0)
    s += 0.5 if tb(si.get("volume_spike", False)) else 0.0
    s += 0.5 if tb(si.get("price_momentum", False)) else 0.0
    s += 0.5 if tb(si.get("trend_strength", False)) else 0.0
    s += sent_delta
    if flags.get("squeeze_factor") or flags.get("edgar_catalyst"):
        if flags.get("squeeze_factor"):
            s += clamp(fnum(si.get("squeeze_factor")), 0.0, 1.0) * 1.5 * macro
        if flags.get("edgar_catalyst"):
            s += clamp(fnum(si.get("catalyst_factor")), -1.0, 1.0) * 1.5 * macro
    if flags.get("lottery_fade"):
        pen = clamp(fnum(si.get("lottery_factor")), 0.0, 1.0) * 2.0
        if flags.get("edgar_catalyst"):
            c = fnum(si.get("catalyst_factor"))
            if c > 0.3:
                pen *= 1.0 - min(0.5, (c - 0.3) / 0.8)
        s -= pen
    if flags.get("overnight_gap"):
        s -= clamp(fnum(si.get("overnight_gap_factor")), 0.0, 1.0) * 1.0
    return round(s, 3)


def strength(raw):
    return int(round(max(0.0, min(100.0, (raw / MAXR) * 100.0))))


def infer_macro(si, bd, flags):
    if not bd:
        return None
    if flags.get("squeeze_factor"):
        sq = clamp(fnum(si.get("squeeze_factor")), 0.0, 1.0)
        if sq > 0 and "squeeze" in bd:
            return fnum(bd["squeeze"]) / (sq * 1.5)
    if flags.get("edgar_catalyst"):
        c = clamp(fnum(si.get("catalyst_factor")), -1.0, 1.0)
        if c != 0 and "catalyst" in bd:
            return fnum(bd["catalyst"]) / (c * 1.5)
    return None


def legacy(si, atr_pct):
    """Mirror of scanner/score_engine.py:compute_legacy_quality_score (HEAD 93ae83c)."""
    def nz(v, sc):
        return 0.0 if v is None else clamp(float(v) / sc, 0.0, 1.0)
    rv = fnum(si.get("rvol_factor"))
    rvol = (1.0 + rv * 2.0) if rv else None
    base = (2.0 * float(tb(si.get("regime"))) + 2.0 * float(tb(si.get("direction")))
            + 1.5 * nz(fnum(si.get("score")), 3.0))
    atr = nz(atr_pct, 6.0)
    relv = nz((rvol - 1.0) if rvol is not None else None, 2.0)
    sq = clamp(fnum(si.get("squeeze_factor")), 0.0, 1.0)
    lot = clamp(fnum(si.get("lottery_factor")), 0.0, 1.0)
    ov = clamp(fnum(si.get("overnight_gap_factor")), 0.0, 1.0)
    return round((base + 1.5 * atr + 1.5 * relv + 0.5 * sq - 1.5 * lot - ov) / 10.0 * 100.0, 3)


def grade_of(row):
    c = row.get("conviction_tier")
    conv = "" if isnull(c) else str(c).strip().upper()
    if conv in ("A", "B", "C"):
        return conv
    t = row.get("tier")
    tier = "" if isnull(t) else str(t).strip().upper()
    if tier == "CONFIRM":
        return "B"
    if tier == "TRIGGER":
        return "C"
    return None


def public(row, cols):
    """Mirror of distribution/snapshot_builder.py:_public_candidate."""
    if not grade_of(row):
        return False
    if "selection_eligible" in cols and not is_true(row.get("selection_eligible")):
        return False
    if "execution_feasible" in cols and not is_true(row.get("execution_feasible")):
        return False
    pc = row.get("position_cap_reject_reason")
    return isnull(pc) or not pc


def first_truthy(row, keys):
    for k in keys:
        v = row.get(k)
        if isnull(v):
            continue
        fv = fnum(v, 0.0)
        if fv:
            return fv
    return 0.0


def sort_key(row):
    """Mirror of distribution/snapshot_builder.py:_sort_key."""
    g = grade_of(row) or "Z"
    ex = row.get("execution_confidence")
    ex = "Tier 0" if isnull(ex) or not ex else str(ex)
    prob = fnum(row.get("conviction_prob"))
    sc = first_truthy(row, ("ranking_score", "legacy_quality_score", "composite_score", "score"))
    return (GRADE_ORDER.get(g, 9), EXEC_ORDER.get(ex, 3), -prob, -sc)


def tie_share(series, k):
    s = pd.to_numeric(series, errors="coerce").dropna().round(6)
    if s.empty:
        return None
    s = s.sort_values(ascending=False, kind="mergesort")
    cnt = s.value_counts()
    top = s.iloc[:k]
    return round(sum(1 for v in top if cnt.get(v, 0) > 1) / float(len(top)), 4)


def key_tie_share(keys, k):
    if not keys:
        return None
    ks = sorted(keys)
    cnt = Counter(ks)
    top = ks[:k]
    return round(sum(1 for x in top if cnt[x] > 1) / float(len(top)), 4)


def topk_overlap(df, a, b, k):
    if a not in df.columns or b not in df.columns or "symbol" not in df.columns:
        return None
    sa = df.assign(_v=pd.to_numeric(df[a], errors="coerce")).sort_values(
        "_v", ascending=False, kind="mergesort")
    sb = df.assign(_v=pd.to_numeric(df[b], errors="coerce")).sort_values(
        "_v", ascending=False, kind="mergesort")
    sa_set, sb_set = set(sa["symbol"].iloc[:k]), set(sb["symbol"].iloc[:k])
    return round(len(sa_set & sb_set) / float(k), 4) if sa_set else None


def shortlist_analysis():
    files = sorted(glob.glob(os.path.join(ROOT, "data", "shortlists", "shortlist_202610*.csv")))
    print("== SHORTLISTS n_files=%d" % len(files))
    if not files:
        return
    if len(files) > 120:
        files = files[-120:]
        print("  capped to most recent 120 files")
    manifest, per = [], []
    agg, reasons, combos, rmethod = Counter(), Counter(), Counter(), Counter()
    conv, execc, tiercol, macro_vals = Counter(), Counter(), Counter(), Counter()
    pooled_c, pooled_r, atr_cols_seen = [], [], set()
    for path in files:
        df = pd.read_csv(path, low_memory=False)
        cols = list(df.columns)
        cs = set(cols)
        manifest.append({"file": rel(path), "sha256": sha256(path), "rows": len(df),
                         "ncols": len(cols),
                         "schema": hashlib.sha1(",".join(cols).encode()).hexdigest()[:10]})
        atr_col = "atr_pct" if "atr_pct" in cs else None
        atr_cols_seen.update(c for c in cols if "atr" in c.lower())
        recs = df.to_dict("records")
        st = Counter()
        for r in recs:
            st["rows"] += 1
            comp_v = r.get("composite_score")
            if isnull(comp_v):
                st["no_comp"] += 1
                continue
            comp = int(round(float(comp_v)))
            rmethod[str(r.get("ranking_method"))] += 1
            conv[str(r.get("conviction_tier"))] += 1
            execc[str(r.get("execution_confidence"))] += 1
            if "tier" in cs:
                tiercol[str(r.get("tier"))] += 1
            st["sel"] += is_true(r.get("selection_eligible"))
            st["entry"] += is_true(r.get("entry_ok"))
            rk, lq = r.get("ranking_score"), r.get("legacy_quality_score")
            if not isnull(rk) and not isnull(lq):
                st["eq_n"] += 1
                st["eq_rl"] += abs(float(rk) - float(lq)) < 1e-9
                st["eq_rc"] += abs(float(rk) - comp) < 1e-9
            rec = r.get("recommendation_score")
            if not isnull(rec):
                st["v0n"] += 1
                st["v0m"] += strength(float(rec)) == comp
            si = pdict(r.get("score_input"))
            if not si:
                st["no_si"] += 1
                continue
            bd = pdict(r.get("score_component_breakdown")) or {}
            ff = pdict(r.get("score_feature_flags"))
            frow = {k: bool(ff.get(k)) for k in OBS} if ff else None
            combos[json.dumps(frow, sort_keys=True) if frow else "missing"] += 1
            sent = sum(fnum(v) for kk, v in bd.items() if "sent" in str(kk).lower())
            macro = infer_macro(si, bd, frow or OBS)
            if macro is not None:
                macro_vals[round(macro, 2)] += 1
            raw1 = raw_score(si, OBS, 1.0, 0.0)
            ok1 = strength(raw1) == comp
            st["v1n"] += 1
            st["v1m"] += ok1
            if not ok1:
                rs = []
                if frow is not None and frow != OBS:
                    rs.append("flags_differ")
                if abs(sent) > 1e-9:
                    rs.append("sentiment_component")
                if macro is not None and abs(macro - 1.0) > 0.01:
                    rs.append("macro_ne_1")
                for x in (rs or ["unexplained"]):
                    reasons[x] += 1
            raw2 = raw_score(si, frow or OBS, macro if macro is not None else 1.0, sent)
            st["v2n"] += 1
            st["v2m"] += strength(raw2) == comp
            if not isnull(rec):
                st["v2rawn"] += 1
                st["v2rawm"] += abs(raw2 - float(rec)) <= 0.0015
            if atr_col and not isnull(r.get(atr_col)) and not isnull(lq):
                st["lgn"] += 1
                st["lgm"] += abs(legacy(si, float(r[atr_col])) - float(lq)) <= 0.0015
        pub = [r for r in recs if public(r, cs)]
        keys = [sort_key(r) for r in pub]
        rcol = "ranking_score" if "ranking_score" in cs else None
        hasc = "composite_score" in cs
        per.append({
            "file": os.path.basename(path), "rows": st["rows"], "ncols": len(cols),
            "n_public": len(pub),
            "uniq_comp": int(df["composite_score"].nunique()) if hasc else None,
            "uniq_rank": int(df[rcol].nunique()) if rcol else None,
            "tie10_rank": tie_share(df[rcol], 10) if rcol else None,
            "tie50_rank": tie_share(df[rcol], 50) if rcol else None,
            "tie10_comp": tie_share(df["composite_score"], 10) if hasc else None,
            "tie50_comp": tie_share(df["composite_score"], 50) if hasc else None,
            "tie10_pubkey": key_tie_share(keys, 10),
            "tie50_pubkey": key_tie_share(keys, 50),
            "ovl50_comp_vs_rank": topk_overlap(df, "composite_score", rcol, 50) if rcol else None,
            "pub_rank_zero": sum(1 for r in pub if not isnull(r.get("ranking_score"))
                                 and float(r["ranking_score"]) == 0.0),
            "v0": "%d/%d" % (st["v0m"], st["v0n"]), "v1": "%d/%d" % (st["v1m"], st["v1n"]),
            "v2": "%d/%d" % (st["v2m"], st["v2n"]), "legacy": "%d/%d" % (st["lgm"], st["lgn"]),
            "eq_rank_legacy": "%d/%d" % (st["eq_rl"], st["eq_n"]),
            "eq_rank_comp": "%d/%d" % (st["eq_rc"], st["eq_n"]),
            "sel": st["sel"], "entry": st["entry"], "no_si": st["no_si"],
        })
        for k2 in ("v0m", "v0n", "v1m", "v1n", "v2m", "v2n", "v2rawm", "v2rawn", "lgm", "lgn",
                   "eq_rl", "eq_rc", "eq_n", "rows", "no_si", "no_comp", "sel", "entry"):
            agg[k2] += st[k2]
        agg["public"] += len(pub)
        if hasc:
            pooled_c.extend(pd.to_numeric(df["composite_score"], errors="coerce").dropna().tolist())
        if rcol:
            pooled_r.extend(pd.to_numeric(df[rcol], errors="coerce").dropna().tolist())
    pd.DataFrame(per).to_csv(os.path.join(OUTD, "SCR_shortlist_per_file.csv"), index=False)
    mpath = os.path.join(OUTD, "SCR_shortlist_manifest.csv")
    pd.DataFrame(manifest).to_csv(mpath, index=False)
    print("files_used=%d first=%s last=%s" % (len(files), os.path.basename(files[0]),
                                              os.path.basename(files[-1])))
    print("ncols_by_file=%s schemas=%d" % (dict(Counter(m["ncols"] for m in manifest)),
                                          len(set(m["schema"] for m in manifest))))
    print("agg=%s" % dict(agg))
    print("V1 mismatch reasons=%s" % dict(reasons))
    print("row-recorded score_feature_flags combos=%s" % dict(combos.most_common(6)))
    print("macro inferred (0.01) top=%s" % dict(macro_vals.most_common(8)))
    print("ranking_method=%s" % dict(rmethod.most_common(5)))
    print("conviction_tier=%s" % dict(conv.most_common(6)))
    print("execution_confidence=%s" % dict(execc.most_common(5)))
    print("tier col=%s" % dict(tiercol.most_common(6)))
    print("atr-like cols=%s" % sorted(atr_cols_seen))
    for name, vals in (("composite_score", pooled_c), ("ranking_score", pooled_r)):
        if vals:
            s = pd.Series(vals)
            q = s.quantile([0, 0.1, 0.25, 0.5, 0.75, 0.9, 0.99, 1.0]).round(3).tolist()
            print("%s pooled n=%d uniq=%d q[0,10,25,50,75,90,99,100]=%s"
                  % (name, len(s), s.nunique(), q))
    pf = pd.DataFrame(per)
    for c in ("tie10_rank", "tie50_rank", "tie10_comp", "tie50_comp", "tie10_pubkey",
              "tie50_pubkey", "ovl50_comp_vs_rank", "uniq_comp", "uniq_rank", "n_public",
              "pub_rank_zero", "rows"):
        v = pd.to_numeric(pf[c], errors="coerce").dropna()
        if len(v):
            print("%s: n=%d min=%s med=%s max=%s" % (c, len(v), round(v.min(), 4),
                                                     round(v.median(), 4), round(v.max(), 4)))
    print("-- last 8 files:")
    for row in per[-8:]:
        print(asc("%s rows=%s pub=%s uC=%s uR=%s t10R=%s t50R=%s t10C=%s t50C=%s t10K=%s "
                  "t50K=%s v0=%s v1=%s v2=%s eqRL=%s" % (
                      row["file"], row["rows"], row["n_public"], row["uniq_comp"],
                      row["uniq_rank"], row["tie10_rank"], row["tie50_rank"], row["tie10_comp"],
                      row["tie50_comp"], row["tie10_pubkey"], row["tie50_pubkey"], row["v0"],
                      row["v1"], row["v2"], row["eq_rank_legacy"]), 230))
    print("manifest sha256=%s" % sha256(mpath))


def kelly_keys():
    p = os.path.join(ROOT, "data", "scanner_config.json")
    print("== KELLY scanner_config.json sha256=%s" % sha256(p))
    with open(p, encoding="utf-8") as fh:
        cfg = json.load(fh)
    print("keys=%s" % sorted(cfg.keys()))
    for k in ("kelly_fraction", "_kelly_reduced_cycle", "_updated_cycle"):
        print("%s=%r" % (k, cfg.get(k)))


# ---------------------------------------------------------------- PRIOR excerpts
PRIOR = [
    "reports/baseline_score_buckets_2026-09-09.csv",
    "reports/research_x_h2_score_direction_2026-09-21.md",
    "reports/research_x_h4a_resolution_compression_2026-09-21.md",
    "reports/research_x_h4b_ranking_mapping_2026-09-21.md",
    "reports/research_x_h4c_information_loss_2026-09-22.md",
    "reports/research_x_h4d_measure_2026-09-22.md",
    "reports/walk_forward_scoring_validation_2026-09-08.md",
    "reports/scoring_ablation_audit_2026-09-08.md",
    "reports/feature_flag_evidence_summary_2026-09-08.md",
    "reports/b2_0_flag_user_facing_impact_report_2026-09-23.md",
]
HEAD_RX = re.compile(
    r"^#+.*(summary|ozet|sonuc|verdict|conclusion|tl;?dr|executive|karar|bulgu|result)", re.I)
KEY_RX = re.compile(
    r"(spearman|\brho\b|monoton|verdict|\bIC\b|decile|bucket|lift|p.?value|\bp\s*[=<]|SUPPORTED|"
    r"CONTRADICTED|HYPOTHESIS|MEASURED|NOT_MEASURABLE|inconclusive|kendall|AUC|hit.?rate|win.?rate)",
    re.I)


def prior():
    fi = sorted(glob.glob(os.path.join(ROOT, "reports", "flag_impact", "*")))
    print("== reports/flag_impact files: %d" % len(fi))
    for p in fi[:12]:
        print("  " + asc(rel(p), 150))
    paths = [os.path.join(ROOT, p) for p in PRIOR]
    paths += [p for p in fi if p.lower().endswith(".md")][:3]
    for p in paths:
        rp = rel(p)
        if not os.path.exists(p):
            print("== MISSING %s" % rp)
            continue
        lines = read_lines(p)
        print("== %s sha256=%s lines=%d" % (rp, sha256(p)[:16], len(lines)))
        if p.endswith(".csv"):
            for i, ln in enumerate(lines[:22], 1):
                print(asc("%d: %s" % (i, ln), 200))
            continue
        shown = set()
        hi = next((i for i, ln in enumerate(lines) if HEAD_RX.search(asc(ln, 400))), None)
        if hi is not None:
            n = 0
            for j in range(hi, min(len(lines), hi + 30)):
                if lines[j].strip():
                    print(asc("%d: %s" % (j + 1, lines[j].strip()), 150))
                    shown.add(j)
                    n += 1
                    if n >= 6:
                        break
        n = 0
        for j, ln in enumerate(lines):
            if j in shown:
                continue
            t = asc(ln, 400)
            if KEY_RX.search(t) and re.search(r"\d", t):
                print(asc("%d: %s" % (j + 1, ln.strip()), 150))
                n += 1
                if n >= 3:
                    break


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "main"
    t0 = time.time()
    os.makedirs(OUTD, exist_ok=True)
    if mode == "main":
        flag_registry()
        code_excerpts()
        shortlist_analysis()
        kelly_keys()
    elif mode == "prior":
        prior()
    print("elapsed_s=%.1f" % (time.time() - t0))
