#!/usr/bin/env python3
"""B2-0 independent verifier (read-only, Level A).

Independent re-implementation of the locked B2-0 protocol
(reports/b2_0_flag_user_facing_impact_preregistration_2026-09-23.md, SHA-256 fe4ceab1...).
Written from the prereg + raw inputs + code at ff9658a only; the original B2-0
implementation and its outputs were not read.

Repo code is executed only where the prereg requires it (Q2b repo-function path,
Q3A "repo functions are called"), always from a `git archive ff9658a` extract in a
temp dir, inside a subprocess. Everything else is stdlib re-implementation.

Side effects: writes ONLY data/backtest_out/b2_0_independent_verification_2026-09-23.json.
No network, no new data, no git state changes (read-only git commands only).
The .env file is read only to apply the prereg §2.7 extract rule; no other .env
line is kept, printed or written.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import io
import itertools
import json
import os
import re
import shutil
import sqlite3
import stat
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
COMMIT = "ff9658a"
PREREG = REPO / "reports/b2_0_flag_user_facing_impact_preregistration_2026-09-23.md"
PREREG_SHA = "fe4ceab1294a2799f034e4d4cc1c0f27b55ef1378d8ff577960c181f7a2133c0"
TRACE = REPO / "data/backtest_out/b2_0_independent_scope_trace_2026-09-23.json"
TRACE_SHA_RECORDED = "7cb986e075afd2a41c0b8052b0b40ba8fc8dcbf800613953c858dc218e111991"  # recorded 2026-09-23T14:48:30Z, before Q3B/Q4
OUT = REPO / "data/backtest_out/b2_0_independent_verification_2026-09-23.json"
DIST = REPO / "data/distribution"
PRIMARY = "2026-09-09"
HIST_DAYS = ["2026-07-29", "2026-07-30", "2026-08-03", "2026-08-11", "2026-08-14", "2026-08-24", "2026-08-27"]
AS_OF = _dt.date(2026, 9, 23)

MANIFEST = [
    ("data/distribution/scan_export_2026-09-09_published.json", "454dd92835201b5c019067ffd9945f6de531d07776a94b8b65164798312b2074"),
    ("data/distribution/snapshot_2026-09-09.json", "e1f26abaa1aa066a5d80818bfb2c8e729498ca062dd460346e9c9eaf8f7d0a34"),
    ("git show ff9658a:distribution/snapshot_builder.py", "47b92eaa8115b500b13f4023f0cc27afbc60a206610f5f86a2cb8268ca292552"),
    ("data/distribution.db", "97fe4dd0c66920c921a67a15cadbe53f5069351907cf0253f9edc8d4a5023a10"),
    ("local flag extract", "e6a840f275b954488d45c5ee6694efc9e6ef21e63c954e175a0a8914304a2c93"),
    ("data/distribution/scan_export_2026-07-29_published.json", "020da1f07fba1112ae9809ac01c2cea4ea1474c6d589e0107e49b058eee032a3"),
    ("data/distribution/snapshot_2026-07-29.json", "c350ab9df56353f94ef918cbb2bbc7806ca2a9623f09e14d19daeab95ed7e251"),
    ("data/distribution/scan_export_2026-07-30_published.json", "7e32c1480cf19c9ae7da54f575a1c944e89bb0db99453aee5c9c390edbc2c08b"),
    ("data/distribution/snapshot_2026-07-30.json", "c6ae0bf93374c127691942c67294b2d301ffa7a824c3ea4c07e69dbaaba7ea5a"),
    ("data/distribution/scan_export_2026-08-03_published.json", "309430725f9bedf97271521c1240e9af1899cc2fb9aae1bfffd982ef94688d21"),
    ("data/distribution/snapshot_2026-08-03.json", "a6670b546600a2468d993142b5f0d00d160944e1b73127e0e19c9d304e79ba5d"),
    ("data/distribution/scan_export_2026-08-11_published.json", "33976ba897e52bb0b628fe52312695d90a05a217e92dd3f115618609cd6b578c"),
    ("data/distribution/snapshot_2026-08-11.json", "70d32522aeec71d49d861021c090868202028fb6ad1cf056d80a1f7136223a56"),
    ("data/distribution/scan_export_2026-08-14_published.json", "ba0679eefc96b9de86a8e2b406f06bb2a318495951b2b9e390d566612605be7b"),
    ("data/distribution/snapshot_2026-08-14.json", "92ad0b89a8531a7cc8ac5bfba50674af9f2138313fcf61794e1660efabd08875"),
    ("data/distribution/scan_export_2026-08-24_published.json", "559efe9c4b59039c0b297c22040ac0be8ad07fa3b77ae4c20a83545f4c3d682b"),
    ("data/distribution/snapshot_2026-08-24.json", "dc131e29e74d61babbbef183481bc82e3203b4f21a411cfc3b65a310aebd7bb4"),
    ("data/distribution/scan_export_2026-08-27_published.json", "8d5f39d0998c8b12bb2cbb111367a7bf7359f23dd462491554e950c0e7093b8a"),
    ("data/distribution/snapshot_2026-08-27.json", "45d11a72910ac7f559e0f661bb284a1c42dc53ec163b0d5267d2bb46d0a5b774"),
]

INTERPRETATION_LIMIT = (
    "A hash match establishes a `FINPILOT_ENABLE*` configuration consistent with the snapshot stamp under the "
    "locked hash function and candidate value space. It does not independently prove the physical/runtime origin "
    "of the snapshot, the state of non-`FINPILOT_ENABLE*` configuration, or the absence of uncommitted code changes."
)

# Judgment calls: fixed before Q3B/Q4 results were computed.
JUDGMENT_CALLS = [
    {"id": "J1", "topic": "rows that never pass a flag's code path",
     "decision": "Rows with scan_status='unavailable' (built by scanner/evaluate.py:69 _unavailable_result, defaults re-applied by api/routers/scan.py:818-832) keep their stored values in every counterfactual and are excluded from Q3B precondition coverage.",
     "justification": "Their sink fields are hard-coded literals; no FINPILOT_ENABLE reader is on that path, so no flag state can change them."},
    {"id": "J2", "topic": "Q3B precondition row coverage",
     "decision": "Precondition is checked on ALL evaluated rows (scan_status != 'unavailable'), not only on current candidates or O1/O3 members.",
     "justification": "Any evaluated row can enter O1/O3 under a counterfactual; restricting coverage to current members would be result-dependent."},
    {"id": "J3", "topic": "meaning of C_full - {f}",
     "decision": "f is set to '0' (not unset).",
     "justification": "Prereg says 'flag kapalı'; FINPILOT_ENABLE_PORTFOLIO_ADV_LIMIT defaults to '1' when unset (scanner/execution_policy.py:36), so unsetting would be a no-op for it."},
    {"id": "J4", "topic": "C_full baseline for Q4",
     "decision": "C_full = stored export rows. Counterfactual = stored rows with only the fields f reaches replaced by the f-OFF recomputation.",
     "justification": "Q3B precondition shows full-config recomputation == stored values for those fields; unaffected fields are flag-independent."},
    {"id": "J5", "topic": "atr_pct (input of compute_conviction) is not stored in the export",
     "decision": "For the CONVICTION_TIERS precondition, atr_pct is recovered by inverting the stored legacy_quality_score (scanner/score_engine.py:193-222) with every other term taken from score_input. Rows whose recovered atr_pct lies inside the rounding-error band of the 4.0 threshold, or whose recovered normalized ATR is outside [0,1], count as precondition failures.",
     "justification": "Derived only from stored fields; ambiguity is counted against reconstructibility, not guessed. The CONVICTION_TIERS-OFF counterfactual itself is input-independent (features.py:221 returns ('', 0.0))."},
    {"id": "J6", "topic": "FRED macro multiplier is a runtime input (data/macro_regime.json + FRED_API_KEY), not stored as a scalar",
     "decision": "Infer one global macro_mult from the stored score_component_breakdown squeeze/catalyst components, restricted to the values the code can produce {1.0, 0.5} (core/macro_regime.py:43). If no single value reproduces all evaluated rows, composite-path flags fail Q3B.",
     "justification": "Stored-derived, finite candidate set from code; no guessing."},
    {"id": "J7", "topic": "PORTFOLIO_ADV_LIMIT inputs",
     "decision": "cap = stored position_cap_notional (cross-checked vs round(dollar_adv*0.005,2)); requested notional = 1000 * stored price (risk_engine.py:217 position_size=1000). Rows with |requested-cap| <= 0.05 (price stored at 4 dp) are ambiguous and count as precondition failures.",
     "justification": "Only stored inputs; rounding uncertainty counted against reconstructibility."},
    {"id": "J8", "topic": "ALPHA_V2 counterfactual",
     "decision": "NOT_RECONSTRUCTIBLE without evaluating the precondition.",
     "justification": "ALPHA_V2 changes squeeze_factor weights 0.7/0.3 -> 0.5/0.5 (features.py:151-155); the short%/float components are not stored (only their weighted sum), so the OFF value needs new data (yfinance .info)."},
    {"id": "J9", "topic": "Q4 secondary all-OFF",
     "decision": "Executed only if every flag in F passes Q3B; otherwise NOT_EXECUTED. No substitute subset combination is computed.",
     "justification": "Prereg §8: 'Pairwise veya başka kombinasyon yok'."},
    {"id": "J10", "topic": "worktree vs extract; repo calls",
     "decision": "ff9658a is used via `git archive` into a temp dir (no worktree, per task constraint). Repo functions (config_sha, build_snapshot, _public_candidate, _sort_key, _build_web_context) run in a subprocess with a controlled env; config_sha's git call is served by a PATH shim that answers `git rev-parse --short HEAD` with 'ff9658a'.",
     "justification": "The extract has no .git and repo HEAD != ff9658a; the shim reproduces the stamp's git component without touching git state."},
    {"id": "J11", "topic": "Q1 ACTIVE window",
     "decision": "ACTIVE iff a publication falls in the last 5 weekdays up to 2026-09-23 (2026-09-17..2026-09-23; no NYSE holiday in that window).",
     "justification": "Prereg: 'son 5 işlem günü'."},
    {"id": "J12", "topic": "tie attribution",
     "decision": "A change is tie-only iff every changed ticker is inside the tuple-equal group crossing the N boundary in BOTH configurations (O2 order: iff the two O2 keys are equal in both).",
     "justification": "Prereg §8 tie rule; with identical row order (ROW_ORDER_INTEGRITY) any other change stems from a key change."},
    {"id": "J13", "topic": "ticker table entered/exited",
     "decision": "entered/exited are relative to the union O1∪O2∪O3; per-object membership columns are added.",
     "justification": "Prereg lists a single entered/exited column over the union."},
    {"id": "J14", "topic": "historical days",
     "decision": "Historical Q3A (own implementation) and Q2 context are informational and do not enter the total verdict; code at those dates may differ from ff9658a.",
     "justification": "Prereg §3.1: historical days are Q0, Q2 context and optional Q3A only."},
    {"id": "J15", "topic": "which process the stamp describes",
     "decision": "Q2 identifies the FINPILOT_ENABLE env of the snapshot-building process. It is used as the F basis (prereg §3.2(i)); scan-process agreement is corroborated only where the export records it (score_feature_flags).",
     "justification": "Export generated_at 11:15:31Z vs snapshot 11:42:17Z: different processes; scripts/publish_now.py:15-23 loads .env then forces DISTRIBUTION=1."},
]


# ----------------------------------------------------------------------------- helpers
def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git(*args: str) -> bytes:
    allowed = {"archive", "show", "log", "diff", "rev-parse", "cat-file"}
    assert args[0] in allowed, args
    return subprocess.run(["git", "-C", str(REPO), *args], capture_output=True, check=True).stdout


def load_json(p: Path):
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def iso_utc(ts: float) -> str:
    return _dt.datetime.fromtimestamp(ts, tz=_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def local_flag_extract() -> tuple[bytes, dict[str, str]]:
    """Prereg §2.7 rule. Only FINPILOT_ENABLE* lines are retained in memory."""
    pat = re.compile(r"^\s*FINPILOT_ENABLE[A-Z0-9_]*\s*=")
    kept = []
    with open(REPO / ".env", "rb") as fh:
        for raw in fh.read().decode("utf-8").split("\n"):
            if pat.match(raw):
                line = raw.replace("\r", "")
                k, v = line.split("=", 1)
                kept.append(f"{k.strip()}={v.strip()}")
    kept.sort()
    blob = ("\n".join(kept) + "\n").encode("utf-8")
    return blob, dict(x.split("=", 1) for x in kept)


def config_sha_indep(flags: dict[str, str], git_short: str) -> str:
    base = ";".join(sorted(f"{k}={v}" for k, v in flags.items() if k.startswith("FINPILOT_ENABLE")))
    return hashlib.sha256(f"{git_short}|{base}".encode()).hexdigest()[:12] + (f"@{git_short}" if git_short else "")


# ----------------------------------------------------------------------------- snapshot contract (own implementation)
GRADE_ORDER = {"A": 0, "B": 1, "C": 2}
EXEC_ORDER = {"Tier 2": 0, "Tier 1": 1, "Tier 0": 2}
N_O1, N_O2, N_O3 = 50, 2, 10


def v_ticker(r) -> str:
    return str(r.get("symbol") or r.get("ticker") or "").upper()


def v_grade(r):
    conv = str(r.get("conviction_tier") or "").strip().upper()
    if conv in ("A", "B", "C"):
        return conv
    tier = str(r.get("tier") or "").strip().upper()
    return "B" if tier == "CONFIRM" else "C" if tier == "TRIGGER" else None


def v_key(r) -> tuple:
    grade = v_grade(r) or "Z"
    execution = str(r.get("execution_confidence") or "Tier 0")
    try:
        prob = float(r.get("conviction_prob") or 0.0)
    except (TypeError, ValueError):
        prob = 0.0
    try:
        score = float(r.get("ranking_score") or r.get("legacy_quality_score") or r.get("composite_score") or r.get("score") or 0.0)
    except (TypeError, ValueError):
        score = 0.0
    return (GRADE_ORDER.get(grade, 9), EXEC_ORDER.get(execution, 3), -prob, -score)


def v_true(v) -> bool:
    return v is True or str(v).strip().lower() in {"true", "1", "yes"}


def v_public(r) -> bool:
    if not v_grade(r):
        return False
    if "selection_eligible" in r and not v_true(r.get("selection_eligible")):
        return False
    if "execution_feasible" in r and not v_true(r.get("execution_feasible")):
        return False
    return not r.get("position_cap_reject_reason")


def build_objects(rows: list[dict]) -> dict:
    graded = sorted((r for r in rows if v_public(r)), key=v_key)  # stable
    o1_rows = graded[:N_O1]
    o1 = [v_ticker(r) for r in o1_rows if v_ticker(r)]
    cand_hash = sha256_bytes("|".join(sorted(v_ticker(r) for r in o1_rows if r.get("symbol") or r.get("ticker"))).encode())
    o1set = set(o1)
    meas = sorted(
        (r for r in rows if v_ticker(r) not in o1set and r.get("price") is not None
         and any(r.get(k) is not None for k in ("ranking_score", "legacy_quality_score", "score"))),
        key=v_key,
    )
    return {
        "graded_order": [v_ticker(r) for r in graded], "graded_keys": [v_key(r) for r in graded],
        "o1": o1, "o2": o1[:N_O2], "o3": [v_ticker(r) for r in meas[:N_O3]],
        "meas_order": [v_ticker(r) for r in meas], "meas_keys": [v_key(r) for r in meas],
        "candidate_hash": cand_hash, "L": len(o1_rows),
    }


def boundary_group(order: list[str], keys: list[tuple], n: int) -> dict:
    if len(keys) > n and keys[n - 1] == keys[n]:
        k = keys[n - 1]
        members = [t for t, kk in zip(order, keys) if kk == k]
        return {"size": len(members), "members": members}
    return {"size": 0, "members": []}


# ----------------------------------------------------------------------------- upstream recomputation (own implementation of ff9658a formulas)
SQUEEZE_W, CATALYST_W, LOTTERY_W, OVERNIGHT_W, MAX_RECO = 1.5, 1.5, 2.0, 1.0, 16.5
VOL_W = {0: 2.5, 1: 2.0, 2: 1.5}
CONV_PROB = {"A": 0.73, "B": 0.59, "C": 0.52}


def clip(x, lo, hi):
    return max(lo, min(hi, x))


def rec_score(si: dict, fl: dict, mult: float) -> float:
    """scanner/score_engine.py:99-190, sentiment_score=None (SENTIMENT unset => OFF)."""
    s = 0.0
    s += 2.0 if bool(si.get("regime", False)) else 0.0
    s += 2.0 if bool(si.get("direction", False)) else 0.0
    s += float(si.get("score", 0)) * 0.5
    s += float(si.get("filter_score", 0)) * 1.5
    s += float(si.get("alignment_ratio", 0.0)) * 2.0
    vr = si.get("vol_regime")
    s += float(si.get("momentum_ratio", 0.0)) * VOL_W.get(int(vr) if vr is not None else 1, 2.0)
    s += 0.5 if bool(si.get("volume_spike", False)) else 0.0
    s += 0.5 if bool(si.get("price_momentum", False)) else 0.0
    s += 0.5 if bool(si.get("trend_strength", False)) else 0.0
    sq_on, cat_on = fl["SQUEEZE_FACTOR"], fl["EDGAR_CATALYST"]
    if sq_on or cat_on:
        m = mult if fl["FRED_MACRO"] else 1.0
        if sq_on:
            s += clip(float(si.get("squeeze_factor", 0.0) or 0.0), 0.0, 1.0) * SQUEEZE_W * m
        if cat_on:
            s += clip(float(si.get("catalyst_factor", 0.0) or 0.0), -1.0, 1.0) * CATALYST_W * m
    if fl["LOTTERY_FADE"]:
        pen = clip(float(si.get("lottery_factor", 0.0) or 0.0), 0.0, 1.0) * LOTTERY_W
        if cat_on:
            c = float(si.get("catalyst_factor", 0.0) or 0.0)
            if c > 0.3:
                pen *= 1.0 - min(0.5, (c - 0.3) / 0.8)
        s -= pen
    if fl["OVERNIGHT_GAP"]:
        s -= clip(float(si.get("overnight_gap_factor", 0.0) or 0.0), 0.0, 1.0) * OVERNIGHT_W
    return round(s, 3)


def composite(si: dict, fl: dict, mult: float) -> int:
    return int(round(clip((rec_score(si, fl, mult) / MAX_RECO) * 100.0, 0.0, 100.0)))


def conviction(sq, gap, rvol, atr_present: bool):
    short_strong, gap_strong, gap_present, rvol_present = sq >= 0.5, gap >= 0.6, gap >= 0.2, rvol >= 0.25
    nfac = sum([short_strong, atr_present, gap_present, rvol_present])
    if short_strong and gap_strong:
        t = "A"
    elif (short_strong and atr_present) or nfac >= 3:
        t = "B"
    elif nfac >= 2:
        t = "C"
    else:
        t = ""
    return t, CONV_PROB.get(t, 0.0)


def is_evaluated(r) -> bool:
    return r.get("scan_status") != "unavailable"


# ----------------------------------------------------------------------------- main
def main() -> dict:
    out: dict = {"artifact": "b2_0_independent_verification", "date": "2026-09-23", "commit_under_test": COMMIT,
                 "judgment_calls": JUDGMENT_CALLS, "implementation_corrections": [],
                 "repo_function_calls": ["distribution.snapshot_builder.config_sha (Q2b, subprocess)",
                                         "distribution.snapshot_builder.load_scan_export/build_snapshot (Q3A, subprocess)",
                                         "distribution.snapshot_builder._public_candidate/_sort_key/_build_web_context (Q4 cross-check, subprocess)"]}
    conflicts: list[str] = []

    # --- prereg lock
    pr_sha = sha256_file(PREREG)
    out["prereg"] = {"path": str(PREREG.relative_to(REPO)), "sha256": pr_sha, "expected": PREREG_SHA, "match": pr_sha == PREREG_SHA}
    if pr_sha != PREREG_SHA:
        out["total_verdict"] = "CONFLICT"
        out["stop_reason"] = "prereg SHA mismatch"
        return out

    tmp = Path(tempfile.mkdtemp(prefix="b2v_"))
    try:
        return _run(out, conflicts, tmp)
    finally:
        for p in tmp.rglob("*"):
            try:
                os.chmod(p, stat.S_IWUSR | stat.S_IRUSR | (stat.S_IXUSR if p.is_dir() else 0))
            except OSError:
                pass
        shutil.rmtree(tmp, ignore_errors=True)


def _run(out: dict, conflicts: list[str], tmp: Path) -> dict:
    ff = tmp / "ff"
    ff.mkdir()
    with tarfile.open(fileobj=io.BytesIO(git("archive", COMMIT)), mode="r:") as tf:
        tf.extractall(ff)
    shim = tmp / "shim"
    shim.mkdir()
    (shim / "git").write_text('#!/bin/sh\nif [ "$1 $2 $3" = "rev-parse --short HEAD" ]; then echo ff9658a; exit 0; fi\nexit 1\n')
    os.chmod(shim / "git", 0o755)
    base_env = {"PATH": f"{shim}:/usr/bin:/bin", "FINPILOT_DB": str(tmp / "no_such.db"), "FINPILOT_DIST_DIR": str(tmp / "dist"), "PYTHONHASHSEED": "0"}

    # ------------------------------------------------------------------ Q0
    db_copy = tmp / "db" / "distribution.db"
    db_copy.parent.mkdir()
    shutil.copyfile(REPO / "data/distribution.db", db_copy)  # original never opened by sqlite
    os.chmod(db_copy, 0o444)
    extract_blob, local_flags = local_flag_extract()
    integrity = []
    for name, expected in MANIFEST:
        if not expected:
            status, got = "SHA_MISSING", None
        elif name.startswith("git show "):
            try:
                got = sha256_bytes(git("show", name.split(" ", 2)[2]))
                status = "SHA_MATCH" if got == expected else "SHA_MISMATCH"
            except subprocess.CalledProcessError:
                status, got = "SHA_MISSING", None
        elif name == "local flag extract":
            got = sha256_bytes(extract_blob)
            status = "SHA_MATCH" if got == expected else "SHA_MISMATCH"
        elif name == "data/distribution.db":
            got = sha256_file(db_copy)
            status = "SHA_MATCH" if got == expected else "SHA_MISMATCH"
        else:
            p = REPO / name
            if not p.exists():
                status, got = "SHA_MISSING", None
            else:
                got = sha256_file(p)
                status = "SHA_MATCH" if got == expected else "SHA_MISMATCH"
        integrity.append({"artifact": name, "expected": expected, "observed": got, "status": status})
    q0_pass = all(x["status"] == "SHA_MATCH" for x in integrity)
    out["integrity"] = {"entries": integrity, "count": len(integrity), "all_match": q0_pass,
                        "local_extract_lines": len(local_flags), "db_copy": "temp copy, chmod 0444, opened with sqlite URI mode=ro"}
    if not q0_pass:
        conflicts.append("Q0: SHA != MATCH")

    export = load_json(DIST / f"scan_export_{PRIMARY}_published.json")
    snap = load_json(DIST / f"snapshot_{PRIMARY}.json")
    rows = export["results"]

    # ------------------------------------------------------------------ §2 fact re-checks
    facts = []

    def fact(fid, desc, expected, observed, holds):
        facts.append({"id": fid, "fact": desc, "expected": expected, "observed": observed, "holds": bool(holds)})

    sb_lines = (ff / "distribution/snapshot_builder.py").read_text(encoding="utf-8").split("\n")
    L = lambda n: sb_lines[n - 1]  # noqa: E731
    fact("2.1a", "constants at snapshot_builder.py:33-35", ["FREE_CANDIDATES = 2", "MAX_CANDIDATES = 50", "WEB_CONTEXT_CANDIDATES = 10"],
         [L(33).split("#")[0].strip(), L(34).strip(), L(35).strip()],
         L(33).startswith("FREE_CANDIDATES = 2") and L(34).strip() == "MAX_CANDIDATES = 50" and L(35).strip() == "WEB_CONTEXT_CANDIDATES = 10")
    fact("2.1b", "_public_candidate at 123-131", "def at 123, return at 131", [L(123).strip(), L(131).strip()],
         L(123).startswith("def _public_candidate") and "return not row.get(\"position_cap_reject_reason\")" in L(131))
    fact("2.1c", "_sort_key at 99-116, score is 4th key", "def at 99; return (grade, execution, -prob, -score) at 116", [L(99).strip(), L(116).strip()],
         L(99).startswith("def _sort_key") and L(116).strip() == "return (_GRADE_ORDER.get(grade, 9), _EXECUTION_ORDER.get(execution, 3), -prob, -score)")
    fact("2.1d", "web context excludes graded names (166-180)", "not in graded_tickers inside _build_web_context", L(173).strip(),
         L(166).startswith("def _build_web_context") and "not in graded_tickers" in L(173))
    body = "\n".join(sb_lines[85:131])
    fact("2.1e", "_grade_of/_sort_key/_is_true/_public_candidate read only row fields (no env/os/import/IO)", "no os./environ/import/open(",
         [tok for tok in ("os.", "environ", "import", "open(") if tok in body], not any(tok in body for tok in ("os.", "environ", "import", "open(")))
    fact("2.2a", "config_sha at 38-52 (sorted FINPILOT_ENABLE pairs, git short, [:12]+@git)", "def at 38, return at 52", [L(38).strip(), L(52).strip()[:60]],
         L(38).startswith("def config_sha") and "hexdigest()[:12]" in L(52) and 'startswith("FINPILOT_ENABLE")' in L(40))
    fact("2.2b", "snapshot JSON gets config_sha at line 523", '"config_sha": config_sha(),', L(523).strip(), L(523).strip() == '"config_sha": config_sha(),')
    con = sqlite3.connect(f"file:{db_copy}?mode=ro", uri=True)
    bq_cols = [r[1] for r in con.execute("PRAGMA table_info(broadcast_queue)")]
    fact("2.3", "PROVENANCE_GAP: broadcast_queue has no config_sha; has snapshot_id, candidate_hash, scan_id", "no config_sha col",
         bq_cols, "config_sha" not in bq_cols and all(c in bq_cols for c in ("snapshot_id", "candidate_hash", "scan_id")))
    latest_sha = sha256_file(DIST / "snapshot_latest.json")
    fact("2.4", "primary snapshot facts", {"config_sha": "a5e0d8b7c9d5@ff9658a", "universe": 1812, "scan_result_count": 1801, "eligible_candidate_count": 10,
                                           "generated_at": "2026-09-09T11:42:17Z", "equals_snapshot_latest": True},
         {"config_sha": snap["config_sha"], "universe": snap["universe"], "scan_result_count": snap["scan_result_count"],
          "eligible_candidate_count": snap["eligible_candidate_count"], "generated_at": snap["generated_at"],
          "equals_snapshot_latest": latest_sha == sha256_file(DIST / f"snapshot_{PRIMARY}.json")},
         snap["config_sha"] == "a5e0d8b7c9d5@ff9658a" and snap["universe"] == 1812 and snap["scan_result_count"] == 1801
         and snap["eligible_candidate_count"] == 10 and snap["generated_at"].startswith("2026-09-09T11:42:17")
         and latest_sha == sha256_file(DIST / f"snapshot_{PRIMARY}.json"))
    names = sorted(os.listdir(DIST))
    full_exports = sorted(n[12:22] for n in names if re.fullmatch(r"scan_export_\d{4}-\d{2}-\d{2}\.json", n))
    published = sorted(n[12:22] for n in names if re.fullmatch(r"scan_export_\d{4}-\d{2}-\d{2}_published\.json", n))
    snaps = sorted(n[9:19] for n in names if re.fullmatch(r"snapshot_\d{4}-\d{2}-\d{2}\.json", n))
    late = [n for n in names if n.startswith("scan_export_") and re.match(r"scan_export_(\d{4}-\d{2}-\d{2})", n)
            and "2026-09-10" <= re.match(r"scan_export_(\d{4}-\d{2}-\d{2})", n).group(1) <= "2026-09-23"]
    pairs = sorted(set(published) & set(snaps))
    exp_pairs = ["2026-07-29", "2026-07-30", "2026-08-03", "2026-08-11", "2026-08-14", "2026-08-24", "2026-08-27", "2026-09-09"]
    fact("2.5", "export inventory", {"last_full_export": PRIMARY, "last_published": PRIMARY, "09-10..09-23 only _partial_": True, "published+snapshot days": exp_pairs},
         {"last_full_export": full_exports[-1] if full_exports else None, "last_published": published[-1] if published else None,
          "09-10..09-23 only _partial_": all("_partial_" in n for n in late), "n_files_09-10..09-23": len(late), "published+snapshot days": pairs},
         (full_exports and full_exports[-1] == PRIMARY) and published and published[-1] == PRIMARY and all("_partial_" in n for n in late) and pairs == exp_pairs)
    primary_rule_day = pairs[-1] if pairs else None
    ff_log = git("log", "-1", "--format=%cI|%s", COMMIT).decode().strip()
    a2_log = git("log", "-1", "--format=%cI|%s", "a242b06").decode().strip()
    a2_utc = _dt.datetime.fromisoformat(a2_log.split("|")[0]).astimezone(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    diff_names = git("diff", "--name-only", COMMIT, "a242b06").decode().split()
    sb_ff_sha = sha256_bytes(git("show", f"{COMMIT}:distribution/snapshot_builder.py"))
    sb_wt_sha = sha256_file(REPO / "distribution/snapshot_builder.py")
    fact("2.6", "commit relation", {"ff9658a": "2026-09-03 chore(web): daily snapshot 2026-09-03", "a242b06": "2026-09-09T11:44:05Z chore(web): daily snapshot 2026-09-09",
                                    "diff": ["web/public/demo_snapshot.json"], "snapshot_builder ff9658a == worktree": True},
         {"ff9658a": ff_log, "a242b06": f"{a2_utc} {a2_log.split('|', 1)[1]}", "diff": diff_names, "py_changed": [d for d in diff_names if d.endswith(".py")],
          "snapshot_builder ff9658a == worktree": sb_ff_sha == sb_wt_sha},
         ff_log.startswith("2026-09-03") and ff_log.endswith("chore(web): daily snapshot 2026-09-03") and a2_utc == "2026-09-09T11:44:05Z"
         and a2_log.endswith("chore(web): daily snapshot 2026-09-09") and diff_names == ["web/public/demo_snapshot.json"] and sb_ff_sha == sb_wt_sha)
    meta_txt = (REPO / "reports/meta_validation_audit_2026-09-08.md").read_text(encoding="utf-8")
    meta_on = sorted(set(re.findall(r"^\|\s*(FINPILOT_ENABLE_[A-Z0-9_]+)\s*\|\s*\**1\**\s*\|", meta_txt, flags=re.M)))
    fis = load_json(REPO / "reports/flag_impact/flag_impact_summary.json")
    fis_flags = fis.get("flags")
    fis_n = len(fis_flags) if isinstance(fis_flags, (list, dict)) else fis_flags
    n_on = sum(1 for v in local_flags.values() if v == "1")
    n_off = sum(1 for v in local_flags.values() if v == "0")
    fact("2.7", "configuration provenance objects (a)-(d)", {"a_meta_audit_flags_on": ">=9", "b_flag_impact_flags": 5, "b_commit": "a242b06", "c": "hash only", "d_local": "14 ON / 4 OFF"},
         {"a_meta_audit_flags_on": len(meta_on), "b_flag_impact_flags": fis_n, "b_commit": fis.get("git_commit"), "c": snap["config_sha"], "d_local": f"{n_on} ON / {n_off} OFF"},
         len(meta_on) >= 9 and fis_n == 5 and fis.get("git_commit") == "a242b06" and n_on == 14 and n_off == 4)
    db_mtime = iso_utc(os.stat(REPO / "data/distribution.db").st_mtime)
    fact("2.8", "distribution.db mtime 2026-09-09 13:42:18 +02:00 (=11:42Z, same minute as snapshot generated_at)", "2026-09-09T11:42:18Z",
         db_mtime, db_mtime == "2026-09-09T11:42:18Z" and snap["generated_at"][:16] == db_mtime[:16])
    fact("3.1", "primary-day rule (latest D with _published export and snapshot)", PRIMARY, primary_rule_day, primary_rule_day == PRIMARY)
    out["section2_facts"] = facts
    if not all(f["holds"] for f in facts):
        conflicts.append("§2 fact(s) do not hold: " + ",".join(f["id"] for f in facts if not f["holds"]))
    out["provenance_gap"] = {"label": "PROVENANCE_GAP", "broadcast_queue_columns": bq_cols, "config_sha_stored": "config_sha" in bq_cols,
                             "note": "recorded only; resolution belongs to B4"}
    out["configuration_provenance_discrepancy"] = {
        "label": "CONFIGURATION_PROVENANCE_DISCREPANCY",
        "objects": {"a_meta_validation_audit_2026-09-08": {"type": "count claim, lower bound", "flags_listed_ON": meta_on},
                    "b_flag_impact_report_2026-09-10": {"type": "measurement", "flags_measured": fis_n, "git_commit": fis.get("git_commit")},
                    "c_snapshot_2026-09-09_config_sha": {"type": "runtime stamp", "value": snap["config_sha"]},
                    "d_local_env_today": {"type": "file state today", "on": n_on, "off": n_off}},
        "note": "objects are not equated; no claim that '14 flags were ON in production' is made."}

    # ------------------------------------------------------------------ Q1
    q1 = {"as_of": AS_OF.isoformat()}
    window = []
    d = AS_OF
    while len(window) < 5:
        if d.weekday() < 5:
            window.append(d.isoformat())
        d -= _dt.timedelta(days=1)
    q1["active_window"] = [window[-1], window[0]]

    def status_for(last):
        if last is None:
            return "UNKNOWN"
        return "ACTIVE" if window[-1] <= last <= window[0] else "DORMANT"

    bq_sent = con.execute("SELECT max(brief_date), max(sent_at) FROM broadcast_queue WHERE status='sent'").fetchone()
    tg_ok = con.execute("SELECT max(ts) FROM tg_delivery_log WHERE ok=1").fetchone()[0]
    tg_by_ch = con.execute("SELECT coalesce(channel,'<null>'), max(ts), count(*) FROM tg_delivery_log WHERE ok=1 GROUP BY 1 ORDER BY 1").fetchall()
    con.close()
    tg_last = iso_utc(tg_ok)[:10] if tg_ok else None
    web = load_json(REPO / "web/public/demo_snapshot.json")
    web_commit = git("log", "-1", "--format=%cI", "--", "web/public/demo_snapshot.json").decode().strip()
    q1["channels"] = {
        "telegram_broadcast_queue": {"last_publication_date": bq_sent[0], "status": status_for(bq_sent[0]),
                                     "last_sent_at_utc": iso_utc(bq_sent[1]) if isinstance(bq_sent[1], (int, float)) else bq_sent[1]},
        "telegram_delivery_log": {"last_publication_date": tg_last, "status": status_for(tg_last),
                                  "by_channel_ok": [{"channel": c, "last_utc": iso_utc(t), "n_ok": n} for c, t, n in tg_by_ch]},
        "web_public_snapshot": {"last_publication_date": web.get("date"), "status": status_for(web.get("date")),
                                "snapshot_id": web.get("snapshot_id"), "last_commit": web_commit},
        "snapshot_archive": {"last_publication_date": snaps[-1] if snaps else None, "status": status_for(snaps[-1] if snaps else None)},
    }
    q1["note"] = "contextual only; does not affect Q2/Q3/Q4 eligibility or the total verdict"
    out["q1"] = q1

    # ------------------------------------------------------------------ Q2
    q2: dict = {}
    snap_shas = {}
    for day in HIST_DAYS + [PRIMARY]:
        s = load_json(DIST / f"snapshot_{day}.json")
        snap_shas[day] = s.get("config_sha")
    q2["2a_config_sha_by_snapshot"] = snap_shas
    target = snap["config_sha"]
    tgt_hash, git_short = target.split("@", 1)
    local_ind = config_sha_indep(local_flags, git_short)

    def repo_config_sha(flags: dict[str, str]) -> str:
        code = ("import datetime,sys; datetime.UTC=datetime.timezone.utc; sys.path.insert(0, sys.argv[1]);"
                "from distribution.snapshot_builder import config_sha; print(config_sha())")
        env = dict(base_env, **flags)
        return subprocess.run([sys.executable, "-c", code, str(ff)], env=env, cwd=str(tmp), capture_output=True, text=True, check=True).stdout.strip().splitlines()[-1]

    local_repo = repo_config_sha(local_flags)
    q2["2b"] = {"target": target, "local_independent": local_ind, "local_repo_function": local_repo,
                "independent_equals_repo": local_ind == local_repo, "local_match": local_ind == target,
                "runtime_env_loaders": ["api/main.py:17-26 (manual parser; does not override existing env)",
                                        "scripts/publish_now.py:15-17 load_dotenv(ROOT/.env) then :23 os.environ['FINPILOT_ENABLE_DISTRIBUTION']='1'",
                                        "core/config.py:303 pydantic env_file (settings object, not os.environ)"]}
    if local_ind != local_repo:
        conflicts.append("Q2b: independent config_sha != repo config_sha")
    keys = sorted(local_flags)
    matches = []
    enumerated = 0
    if local_ind != target:
        for vals in itertools.product("01", repeat=len(keys)):
            enumerated += 1
            cfg = dict(zip(keys, vals))
            if config_sha_indep(cfg, git_short) == target:
                matches.append(cfg)
    q2["2c"] = {"executed": local_ind != target, "key_set": keys, "value_space": ["0", "1"], "assignments_tried": enumerated,
                "n_matches": len(matches)}
    if local_ind == target:
        q2_status, q2_cfg = "CONFIG_HASH_MATCH_LOCAL", dict(local_flags)
    elif matches:
        q2_status, q2_cfg = "CONFIG_HASH_MATCH_BY_ENUMERATION", matches[0]
    else:
        q2_status, q2_cfg = "NO_MATCH", None
    if matches:
        q2["2c"]["matches"] = [{"diff_vs_local": {k: {"local": local_flags[k], "matched": m[k]} for k in keys if m[k] != local_flags[k]}} for m in matches]
        rep = repo_config_sha(matches[0])
        q2["2c"]["matched_config_repo_function"] = rep
        q2["2c"]["matched_config_repo_function_equals_target"] = rep == target
        if rep != target:
            conflicts.append("Q2c: repo config_sha disagrees with enumeration match")
    q2["status"] = q2_status
    q2["matched_config"] = q2_cfg
    q2["ambiguous"] = len(matches) > 1
    # historical context: which snapshots share the primary stamp / match local or enumeration
    hist = {}
    for day, cs in snap_shas.items():
        if not cs or "@" not in cs:
            hist[day] = {"config_sha": cs, "result": "UNPARSEABLE"}
            continue
        h, g = cs.split("@", 1)
        hit_local = config_sha_indep(local_flags, g) == cs
        hits = [] if hit_local else [dict(zip(keys, v)) for v in itertools.product("01", repeat=len(keys)) if config_sha_indep(dict(zip(keys, v)), g) == cs]
        hist[day] = {"config_sha": cs, "local_match": hit_local, "n_enumeration_matches": len(hits),
                     "diff_vs_local": [{k: m[k] for k in keys if m[k] != local_flags[k]} for m in hits]}
    q2["historical_context"] = hist
    q2["2d_origin_evidence"] = {
        "snapshot_generated_at": snap["generated_at"], "export_generated_at": export.get("generated_at"),
        "snapshot_file_mtime_utc": iso_utc(os.stat(DIST / f"snapshot_{PRIMARY}.json").st_mtime),
        "export_file_mtime_utc": iso_utc(os.stat(DIST / f"scan_export_{PRIMARY}_published.json").st_mtime),
        "distribution_db_mtime_utc": db_mtime, "a242b06_commit_utc": a2_utc,
        "publish_path": "scripts/publish_now.py writes _published copy (:99-104) and forces DISTRIBUTION=1 (:23) — consistent with the only diff vs local (DISTRIBUTION)",
        "physical_runtime_origin": "UNKNOWN"}
    q2["interpretation_limit"] = INTERPRETATION_LIMIT
    q2["forbidden_inference"] = "Yerel .env X diyor -> production X'ti (not made)"
    out["q2"] = q2

    # ------------------------------------------------------------------ trace (written before Q3B/Q4)
    trace_sha = sha256_file(TRACE)
    trace = load_json(TRACE)
    F = list(trace["F"])
    cfg_basis = q2_cfg if q2_cfg is not None else local_flags
    f_check = {n: (cfg_basis.get("FINPILOT_ENABLE_" + n) == "1") == trace["candidates"][n]["on_in_q2_config"] for n in trace["candidates"]}
    out["scope"] = {"trace_path": str(TRACE.relative_to(REPO)), "trace_sha256": trace_sha, "trace_sha256_recorded_before_q3b_q4": TRACE_SHA_RECORDED,
                    "trace_unchanged": trace_sha == TRACE_SHA_RECORDED, "F": F, "F_basis": q2_status if q2_cfg else "local extract (CONDITIONAL)",
                    "excluded": {n: c.get("note") for n, c in trace["candidates"].items() if not c["in_F"]},
                    "on_status_consistent_with_q2_config": all(f_check.values())}
    if trace_sha != TRACE_SHA_RECORDED or not all(f_check.values()):
        conflicts.append("trace SHA changed or F ON-status inconsistent with Q2 config")

    if not q0_pass:  # prereg §5 hard gate
        for k in ("q3a", "q3b", "q4_secondary_all_off"):
            out[k] = {"status": "NOT_EXECUTED", "reason": "Q0 hard gate"}
        out["flags"] = {f: {"class": None, "q4": "NOT_EXECUTED (Q0)"} for f in F}
        out["conflicts"] = conflicts
        out["total_verdict"] = "CONFLICT"
        return out

    # ------------------------------------------------------------------ Q3A
    full = build_objects(rows)
    snap_c = [c["ticker"] for c in snap["candidates"]]
    snap_o2 = [c["ticker"] for c in snap["candidates"] if not c.get("premium_only")]
    snap_wc = [c["ticker"] for c in snap.get("web_context", [])]
    own = {"candidate_hash": full["candidate_hash"] == snap["candidate_hash"], "candidates_ordered": full["o1"] == snap_c,
           "o2": full["o2"] == snap_o2, "web_context": full["o3"] == snap_wc, "eligible_count": full["L"] == snap["eligible_candidate_count"],
           "snapshot_id": sha256_bytes(f"{export['date']}|{int(export['universe'])}|{full['candidate_hash']}".encode())[:24] == snap["snapshot_id"]}

    # repo path (subprocess) — also used for Q4 cross-checks later
    helper = tmp / "repo_helper.py"
    helper.write_text(
        "import datetime, json, sys\n"
        "datetime.UTC = datetime.timezone.utc\n"
        "sys.path.insert(0, sys.argv[1])\n"
        "from pathlib import Path\n"
        "from distribution import snapshot_builder as sb\n"
        "req = json.load(open(sys.argv[2]))\n"
        "res = {}\n"
        "if req.get('export'):\n"
        "    rows, universe, date_str = sb.load_scan_export(Path(req['export']))\n"
        "    exp = json.load(open(req['export']))\n"
        "    s = sb.build_snapshot(rows, universe, date_str=date_str, scan_id=exp.get('scan_id'))\n"
        "    res['snap'] = {'candidate_hash': s['candidate_hash'], 'snapshot_id': s['snapshot_id'],\n"
        "                   'candidates': [c['ticker'] for c in s['candidates']],\n"
        "                   'o2': [c['ticker'] for c in s['candidates'] if not c['premium_only']],\n"
        "                   'web_context': [c['ticker'] for c in s['web_context']],\n"
        "                   'eligible_candidate_count': s['eligible_candidate_count']}\n"
        "for name, rs in req.get('sets', {}).items():\n"
        "    g = [r for r in rs if sb._public_candidate(r)]\n"
        "    g.sort(key=sb._sort_key)\n"
        "    g = g[:sb.MAX_CANDIDATES]\n"
        "    t = [str(r.get('symbol') or r.get('ticker') or '').upper() for r in g]\n"
        "    wc = sb._build_web_context(rs, graded_tickers=set(t))\n"
        "    res[name] = {'o1': t, 'o3': [c['ticker'] for c in wc]}\n"
        "print(json.dumps(res))\n", encoding="utf-8")

    def repo_call(req: dict) -> dict:
        rp = tmp / "req.json"
        rp.write_text(json.dumps(req), encoding="utf-8")
        cp = subprocess.run([sys.executable, str(helper), str(ff), str(rp)], env=base_env, cwd=str(ff), capture_output=True, text=True)
        if cp.returncode != 0:
            return {"error": cp.stderr.strip().splitlines()[-1] if cp.stderr.strip() else f"rc={cp.returncode}"}
        return json.loads(cp.stdout.strip().splitlines()[-1])

    rr = repo_call({"export": str(DIST / f"scan_export_{PRIMARY}_published.json")})
    if "snap" in rr:
        rs = rr["snap"]
        repo_cmp = {"candidate_hash": rs["candidate_hash"] == snap["candidate_hash"], "candidates_ordered": rs["candidates"] == snap_c,
                    "o2": rs["o2"] == snap_o2, "web_context": rs["web_context"] == snap_wc,
                    "eligible_count": rs["eligible_candidate_count"] == snap["eligible_candidate_count"], "snapshot_id": rs["snapshot_id"] == snap["snapshot_id"]}
    else:
        repo_cmp = {"error": rr.get("error")}
    q3a_pass = all(own.values()) and "error" not in repo_cmp and all(repo_cmp.values())
    out["q3a"] = {"status": "PASS" if q3a_pass else "FAIL", "own_implementation": own, "repo_functions": repo_cmp,
                  "candidates": snap_c, "o2": snap_o2, "web_context": snap_wc, "candidate_hash": snap["candidate_hash"],
                  "flag_config_independent": True}
    hist_q3a = {}
    for day in HIST_DAYS:
        e = load_json(DIST / f"scan_export_{day}_published.json")
        s = load_json(DIST / f"snapshot_{day}.json")
        ob = build_objects(e["results"])
        sc = [c["ticker"] for c in s.get("candidates", [])]
        hist_q3a[day] = {"candidate_hash": ob["candidate_hash"] == s.get("candidate_hash"), "candidates_ordered": ob["o1"] == sc,
                         "o2": ob["o2"] == [c["ticker"] for c in s.get("candidates", []) if not c.get("premium_only")],
                         "web_context": (ob["o3"] == [c["ticker"] for c in s["web_context"]]) if "web_context" in s else "n/a (no web_context in snapshot)"}
    out["q3a_historical_informational"] = hist_q3a

    # ------------------------------------------------------------------ Q3B
    ev_rows = [r for r in rows if is_evaluated(r)]
    full_flags = {n: True for n in ("SQUEEZE_FACTOR", "EDGAR_CATALYST", "LOTTERY_FADE", "OVERNIGHT_GAP", "FRED_MACRO")}
    for n in full_flags:
        full_flags[n] = cfg_basis.get("FINPILOT_ENABLE_" + n) == "1"

    # macro multiplier inference (J6)
    mult_fit = {}
    for m in (1.0, 0.5):
        bad = 0
        for r in ev_rows:
            si, bd = r["score_input"], r["score_component_breakdown"]
            exp_sq = round(clip(float(si.get("squeeze_factor", 0.0) or 0.0), 0.0, 1.0) * SQUEEZE_W * m, 3) if full_flags["SQUEEZE_FACTOR"] else 0.0
            exp_ca = round(clip(float(si.get("catalyst_factor", 0.0) or 0.0), -1.0, 1.0) * CATALYST_W * m, 3) if full_flags["EDGAR_CATALYST"] else 0.0
            if abs(exp_sq - float(bd.get("squeeze", 0.0))) > 1e-9 or abs(exp_ca - float(bd.get("catalyst", 0.0))) > 1e-9:
                bad += 1
        mult_fit[str(m)] = bad
    fitting = [float(m) for m, b in mult_fit.items() if b == 0]
    macro_mult = fitting[0] if len(fitting) == 1 else None

    def composite_precondition():
        if macro_mult is None:
            return {"pass": False, "reason": f"macro_mult not uniquely inferable (mismatch counts {mult_fit})"}
        bad_c, bad_r = [], []
        for r in ev_rows:
            si = r["score_input"]
            if abs(composite(si, full_flags, macro_mult) - float(r["composite_score"])) > 0.01:
                bad_c.append(r["symbol"])
            if abs(rec_score(si, full_flags, macro_mult) - float(r["recommendation_score"])) > 0.01:
                bad_r.append(r["symbol"])
        return {"pass": not bad_c, "rows_checked": len(ev_rows), "composite_score_mismatch": len(bad_c), "composite_mismatch_examples": bad_c[:10],
                "recommendation_score_mismatch_info": len(bad_r), "macro_mult": macro_mult, "macro_mult_fit_mismatches": mult_fit}

    def conviction_precondition():
        eps_norm = 0.0005 / 10.0 / 1.5 + 1e-9
        bad, amb, out_of_range, checked_entry = [], [], [], 0
        for r in ev_rows:
            si = r["score_input"]
            if not r.get("entry_ok"):
                exp_t, exp_p = "", 0.0
            else:
                checked_entry += 1
                base = 2.0 * float(bool(si["regime"])) + 2.0 * float(bool(si["direction"])) + 1.5 * clip(float(si["score"]) / 3.0, 0.0, 1.0)
                rvf = float(si.get("rvol_factor") or 0.0)
                rv = clip(((1.0 + rvf * 2.0) - 1.0) / 2.0, 0.0, 1.0) if rvf else 0.0
                sq = clip(float(si.get("squeeze_factor") or 0.0), 0.0, 1.0)
                lo = clip(float(si.get("lottery_factor") or 0.0), 0.0, 1.0)
                ov = clip(float(si.get("overnight_gap_factor") or 0.0), 0.0, 1.0)
                atr_norm = (float(r["legacy_quality_score"]) / 10.0 - base - 1.5 * rv - 0.5 * sq + 1.5 * lo + ov) / 1.5
                if atr_norm < -eps_norm or atr_norm > 1.0 + eps_norm:
                    out_of_range.append(r["symbol"])
                    continue
                if abs(atr_norm - 4.0 / 6.0) <= eps_norm:
                    amb.append(r["symbol"])
                    continue
                exp_t, exp_p = conviction(float(si.get("squeeze_factor") or 0.0), float(si.get("gap_factor") or 0.0), rvf, atr_norm * 6.0 >= 4.0)
            if str(r.get("conviction_tier") or "") != exp_t or abs(float(r.get("conviction_prob") or 0.0) - round(exp_p, 3)) > 1e-9:
                bad.append(r["symbol"])
        return {"pass": not bad and not amb and not out_of_range, "rows_checked": len(ev_rows), "entry_ok_rows": checked_entry,
                "mismatch": bad, "ambiguous_atr_threshold": amb, "legacy_inversion_out_of_range": out_of_range,
                "method": "atr_pct recovered from stored legacy_quality_score (J5)"}

    def execpolicy_precondition():
        bad = []
        for r in ev_rows:
            adv = bool((r.get("data_quality") or {}).get("available", {}).get("dollar_adv", False))
            feas = adv  # policy ON
            if (r.get("execution_feasible") is not feas or list(r.get("execution_reject_reason") or []) != ([] if feas else ["missing_dollar_adv"])
                    or r.get("selection_eligible") is not bool(r.get("entry_ok") and feas)):
                bad.append(r["symbol"])
        return {"pass": not bad, "rows_checked": len(ev_rows), "mismatch": bad[:20], "n_mismatch": len(bad)}

    def advlimit_precondition():
        bad, amb, cap_formula_mismatch = [], [], 0
        for r in ev_rows:
            cap = r.get("position_cap_notional")
            try:
                adv = float(r.get("dollar_adv"))
                cap_f = round(adv * 0.005, 2) if adv > 0 else None
            except (TypeError, ValueError):
                cap_f = None
            if cap_f != cap:
                cap_formula_mismatch += 1
            req = 1000.0 * float(r.get("price") or 0.0)
            if cap is None:
                exp_reason, exp_applied = "portfolio_capacity_unknown", False
            else:
                if abs(req - float(cap)) <= 0.05:
                    amb.append(r["symbol"])
                    continue
                exp_applied = req > float(cap)
                exp_reason = "adv_position_cap" if exp_applied else None
            if r.get("position_cap_reject_reason") != exp_reason or bool(r.get("position_cap_applied")) != exp_applied:
                bad.append(r["symbol"])
        return {"pass": not bad and not amb, "rows_checked": len(ev_rows), "n_mismatch": len(bad), "mismatch": bad[:20], "ambiguous": amb,
                "cap_vs_default_fraction_mismatch": cap_formula_mismatch}

    pre = {}
    q3b = {}
    for f in F:
        if f == "ALPHA_V2":
            q3b[f] = {"status": "FAIL", "class_if_fail": "NOT_RECONSTRUCTIBLE",
                      "reason": "needs new data: short%/float components of squeeze_factor not stored (J8)", "precondition": "NOT_EVALUATED"}
            continue
        if f == "CONVICTION_TIERS":
            pre[f] = pre.get(f) or conviction_precondition()
        elif f == "EXECUTION_POLICY":
            pre[f] = execpolicy_precondition()
        elif f == "PORTFOLIO_ADV_LIMIT":
            pre[f] = advlimit_precondition()
        elif f in full_flags:
            pre[f] = composite_precondition()
        else:
            pre[f] = {"pass": False, "reason": "no recomputation model"}
        q3b[f] = {"status": "PASS" if pre[f]["pass"] else "FAIL", "precondition": pre[f], "tolerance": {"score": 0.01, "categorical": "exact"},
                  "rows_excluded_from_coverage": len(rows) - len(ev_rows), "new_data_required": False}
    out["q3b"] = q3b

    # ------------------------------------------------------------------ counterfactual construction
    def cf_rows(off: set[str]) -> list[dict]:
        fl = dict(full_flags)
        for n in off:
            if n in fl:
                fl[n] = False
        new = []
        for r in rows:
            r2 = dict(r)
            if is_evaluated(r):
                if "CONVICTION_TIERS" in off:
                    r2["conviction_tier"], r2["conviction_prob"] = "", 0.0
                if "EXECUTION_POLICY" in off:
                    r2["execution_feasible"] = True
                    r2["execution_reject_reason"] = []
                    r2["selection_eligible"] = bool(r.get("entry_ok"))
                if "PORTFOLIO_ADV_LIMIT" in off:
                    cap = r.get("position_cap_notional")
                    r2["position_cap_reject_reason"] = "portfolio_capacity_unknown" if cap is None else None
                    r2["position_cap_applied"] = False
                    r2["position_notional"] = 1000.0 * float(r.get("price") or 0.0)
                if off & set(full_flags):
                    r2["composite_score"] = composite(r["score_input"], fl, macro_mult if macro_mult is not None else 1.0)
            new.append(r2)
        return new

    def row_order_sha(rs):
        return sha256_bytes("\n".join(v_ticker(r) for r in rs).encode())

    full_order_sha = row_order_sha(rows)
    dup = len(rows) - len({v_ticker(r) for r in rows})

    def compare(cf: list[dict]) -> dict:
        c = build_objects(cf)
        roi = row_order_sha(cf) == full_order_sha and dup == 0
        by_full = {v_ticker(r): r for r in rows}
        by_cf = {v_ticker(r): r for r in cf}
        gf = {t: i + 1 for i, t in enumerate(full["graded_order"])}
        gc = {t: i + 1 for i, t in enumerate(c["graded_order"])}
        mf = {t: i + 1 for i, t in enumerate(full["meas_order"])}
        mc = {t: i + 1 for i, t in enumerate(c["meas_order"])}
        bg = {"O1": (boundary_group(full["graded_order"], full["graded_keys"], N_O1), boundary_group(c["graded_order"], c["graded_keys"], N_O1)),
              "O2": (boundary_group(full["graded_order"], full["graded_keys"], N_O2), boundary_group(c["graded_order"], c["graded_keys"], N_O2)),
              "O3": (boundary_group(full["meas_order"], full["meas_keys"], N_O3), boundary_group(c["meas_order"], c["meas_keys"], N_O3))}
        changes = []
        scope = {}
        mag = {}
        for obj, lf, lc, pf, pc in (("O1", full["o1"], c["o1"], gf, gc), ("O2", full["o2"], c["o2"], gf, gc), ("O3", full["o3"], c["o3"], mf, mc)):
            sf, sc = set(lf), set(lc)
            entered, exited = sorted(sc - sf), sorted(sf - sc)
            common = sf & sc
            scope[f"{obj}_membership"] = bool(entered or exited)
            if entered or exited:
                g0, g1 = set(bg[obj][0]["members"]), set(bg[obj][1]["members"])
                tie = all(t in g0 and t in g1 for t in entered + exited)
                changes.append({"object": obj, "kind": "membership", "entered": entered, "exited": exited, "tie_only": tie})
            mag[obj] = {"changed_count": len(sf ^ sc), "entered": len(entered), "exited": len(exited), "overlap_N": len(common),
                        "max_rank_displacement": max((abs(pf[t] - pc[t]) for t in common if t in pf and t in pc), default=0),
                        "boundary_tie_group_size_full": bg[obj][0]["size"], "boundary_tie_group_size_without_f": bg[obj][1]["size"]}
        o2_common = [t for t in full["o2"] if t in c["o2"]]
        o2_order = any(full["o2"].index(t) != c["o2"].index(t) for t in o2_common)
        scope["O2_order"] = o2_order
        if o2_order:
            kf = [v_key(by_full[t]) for t in full["o2"]]
            kc = [v_key(by_cf[t]) for t in c["o2"]]
            changes.append({"object": "O2", "kind": "order", "full": full["o2"], "without_f": c["o2"],
                            "tie_only": len(kf) == 2 and len(kc) == 2 and kf[0] == kf[1] and kc[0] == kc[1]})
        mag["L_full"], mag["L_f"] = full["L"], c["L"]
        uf = set(full["o1"]) | set(full["o3"])
        uc = set(c["o1"]) | set(c["o3"])
        table = []
        for t in sorted(uf | uc):
            rf, rc = gf.get(t), gc.get(t)
            table.append({"ticker": t, "rank_full": rf, "rank_without_f": rc, "delta_rank": (rc - rf) if rf and rc else None,
                          "entered": t in uc and t not in uf, "exited": t in uf and t not in uc,
                          "grade_full": v_grade(by_full[t]), "grade_without_f": v_grade(by_cf[t]),
                          "public_full": v_public(by_full[t]), "public_without_f": v_public(by_cf[t]),
                          "in_O1_full": t in full["o1"], "in_O1_without_f": t in c["o1"], "in_O2_full": t in full["o2"], "in_O2_without_f": t in c["o2"],
                          "in_O3_full": t in full["o3"], "in_O3_without_f": t in c["o3"],
                          "o3_rank_full": mf.get(t), "o3_rank_without_f": mc.get(t)})
        pub_changed = sum(1 for a, b in zip(rows, cf) if v_public(a) != v_public(b))
        if not changes:
            cls = "NO_OBSERVED_USER_FACING_IMPACT"
        elif all(ch["tie_only"] for ch in changes):
            cls = "TIE_ONLY"
        else:
            cls = "USER_FACING_IMPACT"
        return {"class": cls, "row_order_integrity": roi, "impact_scope": scope, "impact_magnitude": mag, "changes": changes,
                "public_candidate_status_changed_rows": pub_changed, "ticker_table": table,
                "O1_without_f": c["o1"], "O2_without_f": c["o2"], "O3_without_f": c["o3"], "_objects": c}

    # ------------------------------------------------------------------ Q4
    flags_out = {}
    cross_sets = {}
    q3a_ok = q3a_pass
    for f in F:
        if not q3a_ok:
            flags_out[f] = {"class": "NOT_RECONSTRUCTIBLE", "q4": "BLOCKED (Q3A FAIL)"}
            continue
        if q3b[f]["status"] != "PASS":
            flags_out[f] = {"class": "NOT_RECONSTRUCTIBLE", "q4": "NOT_EXECUTED (Q3B FAIL)", "q3b_reason": q3b[f].get("reason") or "precondition failed"}
            continue
        cf = cf_rows({f})
        res = compare(cf)
        objs = res.pop("_objects")
        if not res["row_order_integrity"]:
            conflicts.append(f"ROW_ORDER_INTEGRITY violated for {f}")
        keep = ("symbol", "ticker", "conviction_tier", "tier", "selection_eligible", "execution_feasible", "position_cap_reject_reason",
                "execution_confidence", "conviction_prob", "ranking_score", "legacy_quality_score", "composite_score", "score", "price")
        cross_sets[f] = [{k: r[k] for k in keep if k in r} for r in cf]
        res["_own"] = {"o1": objs["o1"], "o3": objs["o3"]}
        res["conditional_label"] = None if q2_status != "NO_MATCH" else "CONDITIONAL (local extract)"
        flags_out[f] = res
    # repo cross-check of every executed counterfactual
    if cross_sets:
        cross_sets["C_full"] = [{k: r[k] for k in ("symbol", "ticker", "conviction_tier", "tier", "selection_eligible", "execution_feasible",
                                                    "position_cap_reject_reason", "execution_confidence", "conviction_prob", "ranking_score",
                                                    "legacy_quality_score", "composite_score", "score", "price") if k in r} for r in rows]
        rc = repo_call({"sets": cross_sets})
        cross = {}
        for name in cross_sets:
            if "error" in rc:
                cross[name] = {"error": rc["error"]}
                continue
            own_o = flags_out[name]["_own"] if name in flags_out else {"o1": full["o1"], "o3": full["o3"]}
            cross[name] = {"o1_equal": rc[name]["o1"] == own_o["o1"], "o3_equal": rc[name]["o3"] == own_o["o3"]}
        out["q4_repo_cross_check"] = cross
        if any("error" in v or not (v["o1_equal"] and v["o3_equal"]) for v in cross.values()):
            conflicts.append("Q4: own implementation disagrees with repo snapshot functions")
    for v in flags_out.values():
        v.pop("_own", None)
    all_recon = q3a_ok and all(q3b[f]["status"] == "PASS" for f in F)
    if all_recon:
        sec = compare(cf_rows(set(F)))
        sec.pop("_objects")
        out["q4_secondary_all_off"] = {"status": "EXECUTED", "descriptive_only": True, **sec}
    else:
        out["q4_secondary_all_off"] = {"status": "NOT_EXECUTED", "reason": "not every flag in F is reconstructible (J9): "
                                       + ",".join(f for f in F if q3b[f]["status"] != "PASS")}
    out["q4_baseline"] = {"O1_full": full["o1"], "O2_full": full["o2"], "O3_full": full["o3"], "L_full": full["L"],
                          "row_order_sha256": full_order_sha, "duplicate_symbols": dup,
                          "boundary_groups_full": {"O1": boundary_group(full["graded_order"], full["graded_keys"], N_O1)["size"],
                                                   "O2": boundary_group(full["graded_order"], full["graded_keys"], N_O2)["size"],
                                                   "O3": boundary_group(full["meas_order"], full["meas_keys"], N_O3)["size"]}}
    out["flags"] = flags_out

    # ------------------------------------------------------------------ verdict
    if q2_status == "CONFIG_HASH_MATCH_LOCAL" and not q3a_pass:
        conflicts.append("evidence contradiction: Q2 local match but Q3A FAIL")
    classes = [flags_out[f]["class"] for f in F]
    if conflicts:
        verdict = "CONFLICT"
    elif not q3a_pass:
        verdict = "NOT_RECONSTRUCTIBLE"
    elif q2_status == "NO_MATCH":
        verdict = "PRODUCTION_ENV_NOT_VERIFIABLE"
    elif "USER_FACING_IMPACT" in classes:
        verdict = "USER_FACING_IMPACT"
    elif "NOT_RECONSTRUCTIBLE" in classes:
        verdict = "INCOMPLETE"
    else:
        verdict = "NO_OBSERVED_USER_FACING_IMPACT"
    out["conflicts"] = conflicts
    out["flag_classes"] = {f: flags_out[f]["class"] for f in F}
    out["total_verdict"] = verdict
    return out


if __name__ == "__main__":
    result = main()
    text = json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    print("total_verdict:", result.get("total_verdict"))
    print("sha256:", sha256_bytes(text.encode("utf-8")))
