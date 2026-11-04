"""B2-0 — FLAG USER-FACING IMPACT & FLAG-CONFIGURATION PROVENANCE GATE (runner).

Implements the LOCKED v2 preregistration
  reports/b2_0_flag_user_facing_impact_preregistration_2026-09-23.md
  (SHA-256 fe4ceab1294a2799f034e4d4cc1c0f27b55ef1378d8ff577960c181f7a2133c0).

Level A, read-only. No production/flag/.env/DB/ranking change, no network call,
no new scan, no new data. The ff9658a code is extracted with `git archive` into a
temporary directory (repo untouched); distribution.db is read from a read-only copy.

Runtime note: this sandbox runs CPython 3.10; ff9658a targets 3.11+ only for
`datetime.UTC`. A one-line alias (datetime.UTC = timezone.utc) is installed before
importing ff9658a modules. It does not change any computation; Q3A fidelity checks
the resulting reconstruction against the published snapshot.

Verdict vocabulary and precedence: prereg §9/§13. Output JSON path: prereg §11.
"""

from __future__ import annotations

import copy
import datetime as _dt
import hashlib
import inspect
import itertools
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREREG = ROOT / "reports" / "b2_0_flag_user_facing_impact_preregistration_2026-09-23.md"
PREREG_SHA = "fe4ceab1294a2799f034e4d4cc1c0f27b55ef1378d8ff577960c181f7a2133c0"
TRACE = ROOT / "data" / "backtest_out" / "b2_0_flag_scope_trace_2026-09-23.json"
TRACE_SHA = "838ab9dea2641cc6e36e1c419ab541c4706c041ab4c15cf9f91121746aee63b7"
OUT = ROOT / "data" / "backtest_out" / "b2_0_flag_user_facing_impact_2026-09-23.json"

SNAP_COMMIT = "ff9658a"
PRIMARY_DATE = "2026-09-09"
EXEC_DATE = _dt.date(2026, 9, 23)
DIST = ROOT / "data" / "distribution"

# prereg §2.7 input manifest (locked)
MANIFEST = {
    "data/distribution/scan_export_2026-09-09_published.json": "454dd92835201b5c019067ffd9945f6de531d07776a94b8b65164798312b2074",
    "data/distribution/snapshot_2026-09-09.json": "e1f26abaa1aa066a5d80818bfb2c8e729498ca062dd460346e9c9eaf8f7d0a34",
    "git:ff9658a:distribution/snapshot_builder.py": "47b92eaa8115b500b13f4023f0cc27afbc60a206610f5f86a2cb8268ca292552",
    "data/distribution.db": "97fe4dd0c66920c921a67a15cadbe53f5069351907cf0253f9edc8d4a5023a10",
    "flag_extract:.env": "e6a840f275b954488d45c5ee6694efc9e6ef21e63c954e175a0a8914304a2c93",
    "data/distribution/scan_export_2026-07-29_published.json": "020da1f07fba1112ae9809ac01c2cea4ea1474c6d589e0107e49b058eee032a3",
    "data/distribution/snapshot_2026-07-29.json": "c350ab9df56353f94ef918cbb2bbc7806ca2a9623f09e14d19daeab95ed7e251",
    "data/distribution/scan_export_2026-07-30_published.json": "7e32c1480cf19c9ae7da54f575a1c944e89bb0db99453aee5c9c390edbc2c08b",
    "data/distribution/snapshot_2026-07-30.json": "c6ae0bf93374c127691942c67294b2d301ffa7a824c3ea4c07e69dbaaba7ea5a",
    "data/distribution/scan_export_2026-08-03_published.json": "309430725f9bedf97271521c1240e9af1899cc2fb9aae1bfffd982ef94688d21",
    "data/distribution/snapshot_2026-08-03.json": "a6670b546600a2468d993142b5f0d00d160944e1b73127e0e19c9d304e79ba5d",
    "data/distribution/scan_export_2026-08-11_published.json": "33976ba897e52bb0b628fe52312695d90a05a217e92dd3f115618609cd6b578c",
    "data/distribution/snapshot_2026-08-11.json": "70d32522aeec71d49d861021c090868202028fb6ad1cf056d80a1f7136223a56",
    "data/distribution/scan_export_2026-08-14_published.json": "ba0679eefc96b9de86a8e2b406f06bb2a318495951b2b9e390d566612605be7b",
    "data/distribution/snapshot_2026-08-14.json": "92ad0b89a8531a7cc8ac5bfba50674af9f2138313fcf61794e1660efabd08875",
    "data/distribution/scan_export_2026-08-24_published.json": "559efe9c4b59039c0b297c22040ac0be8ad07fa3b77ae4c20a83545f4c3d682b",
    "data/distribution/snapshot_2026-08-24.json": "dc131e29e74d61babbbef183481bc82e3203b4f21a411cfc3b65a310aebd7bb4",
    "data/distribution/scan_export_2026-08-27_published.json": "8d5f39d0998c8b12bb2cbb111367a7bf7359f23dd462491554e950c0e7093b8a",
    "data/distribution/snapshot_2026-08-27.json": "45d11a72910ac7f559e0f661bb284a1c42dc53ec163b0d5267d2bb46d0a5b774",
}
HIST_DATES = ["2026-07-29", "2026-07-30", "2026-08-03", "2026-08-11", "2026-08-14", "2026-08-24", "2026-08-27"]
COMPOSITE_FLAGS = ["SQUEEZE_FACTOR", "LOTTERY_FADE", "OVERNIGHT_GAP", "EDGAR_CATALYST", "FRED_MACRO"]
SCORE_TOL = 0.01


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def git(*args: str) -> bytes:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=True).stdout


def flag_extract() -> tuple[bytes, list[str]]:
    """prereg §2.7 extract rule (FINPILOT_ENABLE* lines only; secrets never read out)."""
    lines = []
    for raw in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
        if re.match(r"^\s*FINPILOT_ENABLE[A-Z0-9_]*\s*=", raw):
            lines.append(re.sub(r"\s*=\s*", "=", raw.strip().rstrip("\r"), count=1))
    lines.sort()
    return ("\n".join(lines) + "\n").encode(), lines


def config_sha_independent(pairs: list[str], git_short: str) -> str:
    base = ";".join(sorted(pairs))
    return sha256_bytes(f"{git_short}|{base}".encode())[:12] + (f"@{git_short}" if git_short else "")


# ─────────────────────────────────────────────────────────────────────────────
def main() -> None:
    res: dict = {"prereg": str(PREREG.relative_to(ROOT)), "prereg_sha256": PREREG_SHA,
                 "trace": str(TRACE.relative_to(ROOT)), "trace_sha256": TRACE_SHA,
                 "snapshot_commit": SNAP_COMMIT, "primary_date": PRIMARY_DATE,
                 "runtime": {"python": sys.version.split()[0],
                             "compat_shim": "datetime.UTC = datetime.timezone.utc (py3.10 alias only)"}}
    conflicts: list[str] = []

    # ── Q0 integrity (hard gate) ─────────────────────────────────────────────
    integrity = {}
    extract_bytes, extract_lines = flag_extract()
    for key, expected in MANIFEST.items():
        try:
            if key.startswith("git:"):
                _, commit, path = key.split(":", 2)
                actual = sha256_bytes(git("show", f"{commit}:{path}"))
            elif key.startswith("flag_extract:"):
                actual = sha256_bytes(extract_bytes)
            else:
                p = ROOT / key
                actual = sha256_bytes(p.read_bytes()) if p.exists() else None
        except Exception:  # noqa: BLE001
            actual = None
        status = "SHA_MISSING" if (actual is None or not expected) else ("SHA_MATCH" if actual == expected else "SHA_MISMATCH")
        integrity[key] = {"expected": expected, "actual": actual, "status": status}
    for key, path, expected in (("prereg", PREREG, PREREG_SHA), ("trace", TRACE, TRACE_SHA)):
        actual = sha256_bytes(path.read_bytes()) if path.exists() else None
        integrity[key] = {"expected": expected, "actual": actual,
                          "status": "SHA_MISSING" if actual is None else ("SHA_MATCH" if actual == expected else "SHA_MISMATCH")}
    res["integrity"] = integrity
    q0_ok = all(v["status"] == "SHA_MATCH" for v in integrity.values())
    res["q0"] = "PASS" if q0_ok else "FAIL"
    if not q0_ok:
        conflicts.append("Q0 integrity failure: " + ", ".join(k for k, v in integrity.items() if v["status"] != "SHA_MATCH"))

    # ── workspace: ff9658a extraction + DB read-only copy ────────────────────
    work = Path(tempfile.mkdtemp(prefix="b2_0_"))
    code_dir = work / "code"
    code_dir.mkdir()
    tar = subprocess.run(["git", "archive", SNAP_COMMIT], cwd=ROOT, capture_output=True, check=True).stdout
    subprocess.run(["tar", "-x", "-C", str(code_dir)], input=tar, check=True)
    db_copy = work / "distribution_copy.db"
    shutil.copyfile(ROOT / "data" / "distribution.db", db_copy)
    os.chmod(db_copy, 0o444)
    db_copy_sha = sha256_bytes(db_copy.read_bytes())
    res["db_copy_sha256"] = db_copy_sha
    if db_copy_sha != MANIFEST["data/distribution.db"]:
        conflicts.append("distribution.db copy SHA != manifest")

    _dt.UTC = _dt.timezone.utc  # type: ignore[attr-defined]  # py3.10 alias, see docstring
    sys.path.insert(0, str(code_dir))
    for k in list(os.environ):
        if k.startswith("FINPILOT_ENABLE"):
            del os.environ[k]
    import distribution.snapshot_builder as sb  # noqa: E402
    import scanner.score_engine as se  # noqa: E402
    se._macro_mult = lambda: 1.0  # FRED multiplier fixed (no network); validated by Q3B precondition

    export = json.loads((DIST / f"scan_export_{PRIMARY_DATE}_published.json").read_text(encoding="utf-8"))
    snap = json.loads((DIST / f"snapshot_{PRIMARY_DATE}.json").read_text(encoding="utf-8"))
    rows = export["results"]

    # ── §2 fact re-verification ──────────────────────────────────────────────
    facts = {}
    facts["2.1_constants"] = (sb.FREE_CANDIDATES, sb.WEB_CONTEXT_CANDIDATES, sb.MAX_CANDIDATES) == (2, 10, 50)
    src = inspect.getsource(sb.config_sha)
    facts["2.2_config_sha_definition"] = ('startswith("FINPILOT_ENABLE")' in src and "rev-parse" in src and "[:12]" in src)
    con = sqlite3.connect(f"file:{db_copy}?mode=ro", uri=True)
    bq_cols = [r[1] for r in con.execute("pragma table_info(broadcast_queue)")]
    facts["2.3_broadcast_queue_has_no_config_sha"] = "config_sha" not in bq_cols
    facts["2.4_primary_snapshot_fields"] = (snap.get("config_sha") == "a5e0d8b7c9d5@ff9658a" and snap.get("universe") == 1812
                                           and snap.get("scan_result_count") == 1801 and snap.get("eligible_candidate_count") == 10
                                           and str(snap.get("generated_at", "")).startswith("2026-09-09T11:42:17"))
    names = [p.name for p in DIST.glob("scan_export_*.json")]
    full_dates = sorted({m.group(1) for n in names if (m := re.fullmatch(r"scan_export_(\d{4}-\d{2}-\d{2})(_published)?\.json", n))})
    pub_dates = sorted({m.group(1) for n in names if (m := re.fullmatch(r"scan_export_(\d{4}-\d{2}-\d{2})_published\.json", n))})
    snap_dates = sorted({m.group(1) for p in DIST.glob("snapshot_*.json") if (m := re.fullmatch(r"snapshot_(\d{4}-\d{2}-\d{2})\.json", p.name))})
    pairs = sorted(set(pub_dates) & set(snap_dates))
    facts["2.5_export_inventory"] = (full_dates[-1] == PRIMARY_DATE and pub_dates[-1] == PRIMARY_DATE
                                     and pairs == HIST_DATES + [PRIMARY_DATE])
    py_changed = [f for f in git("diff", "--name-only", "ff9658a", "a242b06").decode().split() if f.endswith(".py")]
    facts["2.6_no_py_change_ff9658a_a242b06"] = py_changed == []
    mtime = _dt.datetime.fromtimestamp((ROOT / "data" / "distribution.db").stat().st_mtime, tz=_dt.timezone.utc)
    facts["2.8_db_mtime_observation"] = mtime.strftime("%Y-%m-%dT%H:%M") == "2026-09-09T11:42"
    res["facts"] = {"checks": facts, "inventory": {"latest_full_export": full_dates[-1], "latest_published_export": pub_dates[-1],
                    "published_snapshot_pairs": pairs, "db_mtime_utc": mtime.isoformat()}}
    for k, ok in facts.items():
        if not ok:
            conflicts.append(f"§2 fact not reproduced: {k}")
    res["configuration_provenance_discrepancy"] = {
        "a_meta_validation_audit_2026-09-08": "'9+ flags ON' (count claim, lower bound)",
        "b_flag_impact_report_2026-09-10": "5 score flags measured on composite ranking (commit a242b06)",
        "c_snapshot_2026-09-09_config_sha": snap.get("config_sha"),
        "d_local_env_extract_2026-09-23": {"on": sorted(l.split("=")[0] for l in extract_lines if l.endswith("=1")),
                                            "off": sorted(l.split("=")[0] for l in extract_lines if l.endswith("=0"))},
        "rule": "objects are not equated; Q2 addresses (c) only"}
    res["provenance_gap"] = "broadcast_queue does not persist config_sha (columns: " + ", ".join(bq_cols) + ") -> B4 provenance debt; not resolved here"

    # ── Q1 publication activity (context only) ───────────────────────────────
    last_sent = con.execute("select kind, max(brief_date), max(sent_at) from broadcast_queue where status='sent' group by kind").fetchall()
    tg = con.execute("select max(ts), count(*) from tg_delivery_log where ok=1").fetchone()
    web_snap = ROOT / "web" / "public" / "demo_snapshot.json"
    web_date = None
    if web_snap.exists():
        try:
            web_date = json.loads(web_snap.read_text(encoding="utf-8")).get("date")
        except Exception:  # noqa: BLE001
            web_date = "UNREADABLE"
    last_dates = [d for _, d, _ in last_sent if d]
    last_pub = max(last_dates) if last_dates else None
    window, d = [], EXEC_DATE
    while len(window) < 5:
        if d.weekday() < 5:
            window.append(d)
        d -= _dt.timedelta(days=1)
    tg_last = _dt.datetime.fromtimestamp(tg[0], tz=_dt.timezone.utc).isoformat() if tg and tg[0] else None
    q1_status = "UNKNOWN" if last_pub is None else ("ACTIVE" if _dt.date.fromisoformat(last_pub) >= min(window) else "DORMANT")
    res["q1"] = {"status": q1_status, "broadcast_queue_last_sent_by_kind": [{"kind": k, "brief_date": d_, "sent_at": s} for k, d_, s in last_sent],
                 "tg_delivery_last_ok_utc": tg_last, "tg_delivery_ok_count": tg[1] if tg else None,
                 "web_public_snapshot_date": web_date, "active_window_weekdays": [w.isoformat() for w in sorted(window)],
                 "note": "contextual metadata only; does not alter Q2/Q3/Q4 eligibility or the total verdict"}

    # ── Q2 FINPILOT_ENABLE* + commit provenance ──────────────────────────────
    keys = [l.split("=")[0] for l in extract_lines]
    local_pairs = list(extract_lines)

    def repo_config_sha(pairs_: list[str], git_short: str) -> str:
        saved = {k: v for k, v in os.environ.items() if k.startswith("FINPILOT_ENABLE")}
        for k in saved:
            del os.environ[k]
        for p in pairs_:
            k, v = p.split("=", 1)
            os.environ[k] = v
        real_run = sb.subprocess.run
        sb.subprocess.run = lambda *a, **kw: subprocess.CompletedProcess(a, 0, stdout=git_short + "\n", stderr="")  # controlled git
        try:
            return sb.config_sha()
        finally:
            sb.subprocess.run = real_run
            for p in pairs_:
                os.environ.pop(p.split("=", 1)[0], None)
            os.environ.update(saved)

    q2 = {"per_snapshot": {}}
    for date in HIST_DATES + [PRIMARY_DATE]:
        s = json.loads((DIST / f"snapshot_{date}.json").read_text(encoding="utf-8"))
        stamp = s.get("config_sha")
        entry = {"config_sha": stamp}
        if not stamp or "@" not in stamp:
            entry.update(status="NO_MATCH", reason="no config_sha or no git suffix in snapshot")
            q2["per_snapshot"][date] = entry
            continue
        git_short = stamp.split("@", 1)[1]
        ind = config_sha_independent(local_pairs, git_short)
        rep = repo_config_sha(local_pairs, git_short)
        entry.update(git=git_short, local_hash_independent=ind, local_hash_repo_fn=rep, impl_agree=(ind == rep))
        if ind != rep:
            conflicts.append(f"Q2 {date}: independent vs repo config_sha disagree")
        if ind == stamp:
            entry["status"] = "CONFIG_HASH_MATCH_LOCAL"
            entry["config"] = local_pairs
        else:
            target = stamp.split("@", 1)[0]
            matches = []
            for vals in itertools.product("01", repeat=len(keys)):
                cand = [f"{k}={v}" for k, v in zip(keys, vals)]
                if sha256_bytes(f"{git_short}|{';'.join(sorted(cand))}".encode())[:12] == target:
                    matches.append(cand)
            if len(matches) == 1:
                diff = {c.split("=")[0]: {"local": l.split("=")[1], "snapshot": c.split("=")[1]}
                        for c, l in zip(matches[0], local_pairs) if c != l}
                entry.update(status="CONFIG_HASH_MATCH_BY_ENUMERATION", config=matches[0], diff_vs_local=diff)
            elif len(matches) > 1:
                entry.update(status="NO_MATCH", reason=f"{len(matches)} enumeration matches (ambiguous)")
                conflicts.append(f"Q2 {date}: ambiguous enumeration")
            else:
                entry.update(status="NO_MATCH", reason="no match within locked key set x {0,1}")
        q2["per_snapshot"][date] = entry
    prim = q2["per_snapshot"][PRIMARY_DATE]
    q2["primary_status"] = prim["status"]
    q2["interpretation_boundary"] = ("A hash match establishes a FINPILOT_ENABLE* configuration consistent with the snapshot stamp under the "
                                     "locked hash function and candidate value space. It does not independently prove the physical/runtime origin "
                                     "of the snapshot, the state of non-FINPILOT_ENABLE* configuration, or the absence of uncommitted code changes.")
    a242 = git("log", "-1", "--format=%cI %s", "a242b06").decode().strip()
    q2["location_evidence"] = {
        "snapshot_generated_at": snap.get("generated_at"), "db_mtime_utc": mtime.isoformat(),
        "a242b06_commit": a242, "git_suffix_present": "@" in (snap.get("config_sha") or ""),
        "runtime_files_at_ff9658a": [f for f in ("finpilot.bat", "docker-compose.yml", "render.yaml", ".devcontainer/devcontainer.json") if (code_dir / f).exists()],
        "determination": "UNKNOWN",
        "note": "Evidence is consistent with generation in an environment writing to this repository's data/ directory (snapshot, DB write and snapshot commit within ~2 min), but this does not prove the runtime host."}
    sff = {}
    for r in rows:
        key = json.dumps(r.get("score_feature_flags"), sort_keys=True)
        sff[key] = sff.get(key, 0) + 1
    q2["supplementary_row_level_score_feature_flags"] = {"counts": sff, "note": "descriptive supplementary evidence from the export (4 score flags only); not a Q2 verdict input"}
    res["q2"] = q2
    if prim["status"] in ("CONFIG_HASH_MATCH_LOCAL", "CONFIG_HASH_MATCH_BY_ENUMERATION"):
        config_pairs, q2_verified = prim["config"], True
    else:
        config_pairs, q2_verified = local_pairs, False
    config = dict(p.split("=", 1) for p in config_pairs)

    # ── F finalization (trace ∩ ON) — before Q3B/Q4 ──────────────────────────
    trace = json.loads(TRACE.read_text(encoding="utf-8"))
    reachable = [f for f, v in trace["flags"].items() if v.get("reachable")]
    F = [f for f in reachable if config.get(f"FINPILOT_ENABLE_{f}") == "1"]
    res["F"] = {"reachable_from_trace": reachable, "on_in_q2_config": sorted(k.replace("FINPILOT_ENABLE_", "") for k, v in config.items() if v == "1"),
                "F": F, "conditional_on_local_config": not q2_verified}

    def set_env(cfg: dict[str, str]) -> None:
        for k in [k for k in os.environ if k.startswith("FINPILOT_ENABLE")]:
            del os.environ[k]
        os.environ.update(cfg)

    # ── object builders (repo functions) ─────────────────────────────────────
    def ticker(r: dict) -> str:
        return str(r.get("symbol") or r.get("ticker") or "").upper()

    def build_objects(rs: list[dict]) -> dict:
        graded_all = [r for r in rs if sb._public_candidate(r)]
        graded_all.sort(key=sb._sort_key)
        o1_rows = [r for r in graded_all[: sb.MAX_CANDIDATES] if ticker(r)]
        o1 = [ticker(r) for r in o1_rows]
        web = sb._build_web_context(rs, graded_tickers=set(o1))
        o3 = [str(w.get("ticker")).upper() for w in web]
        measurable = [r for r in rs if ticker(r) not in set(o1) and r.get("price") is not None
                      and any(r.get(k) is not None for k in ("ranking_score", "legacy_quality_score", "score"))]
        measurable.sort(key=sb._sort_key)
        return {"O1": o1, "O2": o1[: sb.FREE_CANDIDATES], "O3": o3,
                "graded_rank": {ticker(r): i + 1 for i, r in enumerate(graded_all)},
                "web_rank": {ticker(r): i + 1 for i, r in enumerate(measurable)},
                "keys_graded": [sb._sort_key(r) for r in graded_all],
                "keys_web": [sb._sort_key(r) for r in measurable],
                "grade": {ticker(r): sb._grade_of(r) for r in rs},
                "public": {ticker(r): sb._public_candidate(r) for r in rs},
                "row_order_sha": sha256_bytes("|".join(ticker(r) for r in rs).encode())}

    # ── Q0 hard gate: Q3A/Q3B/Q4 not executed on integrity failure ───────────
    if not q0_ok:
        res.update(q3a={"status": "NOT_EXECUTED"}, q3b={}, q4={"status": "NOT_EXECUTED"},
                   flags_class={}, conflicts=conflicts, total_verdict="CONFLICT", production_impact="NONE")
        OUT.write_text(json.dumps(res, indent=2, ensure_ascii=False, sort_keys=True, default=str) + "\n", encoding="utf-8")
        shutil.rmtree(work, ignore_errors=True)
        print(json.dumps({"total_verdict": "CONFLICT", "conflicts": conflicts}, indent=2))
        return

    # ── Q3A snapshot fidelity ────────────────────────────────────────────────
    set_env(dict(config))
    full = build_objects(rows)
    cand_hash = sha256_bytes("|".join(sorted(full["O1"])).encode())
    snap_id = sha256_bytes(f"{PRIMARY_DATE}|{int(export['universe'])}|{cand_hash}".encode())[:24]
    published_o1 = [c["ticker"] for c in snap["candidates"]]
    published_o3 = [str(w.get("ticker")).upper() for w in snap.get("web_context", [])]
    q3a = {"candidate_hash_match": cand_hash == snap["candidate_hash"], "snapshot_id_match": snap_id == snap["snapshot_id"],
           "o1_ordered_match": full["O1"] == published_o1, "o2_match": full["O2"] == published_o1[:2],
           "o3_match": full["O3"] == published_o3, "reconstructed_o1": full["O1"], "published_o1": published_o1,
           "reconstructed_o3": full["O3"], "published_o3": published_o3}
    q3a["status"] = "PASS" if all(q3a[k] for k in ("candidate_hash_match", "snapshot_id_match", "o1_ordered_match", "o2_match", "o3_match")) else "FAIL"
    res["q3a"] = q3a

    # ── Q3B reconstructibility per flag ──────────────────────────────────────
    def recompute_scores(cfg: dict[str, str]) -> dict[int, tuple[float, int]]:
        set_env(cfg)
        out = {}
        for i, r in enumerate(rows):
            si = r.get("score_input")
            if isinstance(si, dict):
                out[i] = (float(se.compute_recommendation_score(si, sentiment_score=None)),
                          int(se.compute_recommendation_strength(si, sentiment_score=None)))
        return out

    full_cfg = {k: v for k, v in config.items()}
    q3b: dict = {}
    transforms = {}

    # composite flags
    base_scores = recompute_scores(full_cfg)
    mism = [i for i, (rs_, cs) in base_scores.items()
            if abs(rs_ - float(rows[i].get("recommendation_score"))) > SCORE_TOL or cs != int(rows[i].get("composite_score"))]
    comp_pre = {"rows_with_score_input": len(base_scores), "rows_without_score_input": len(rows) - len(base_scores),
                "mismatches": len(mism), "fred_multiplier_assumed": 1.0,
                "rows_without_score_input_note": "held fixed: no price and no conviction tier -> cannot enter O1 or O3 under any evaluated configuration"}
    no_si_can_enter = [ticker(r) for r in rows if not isinstance(r.get("score_input"), dict) and (r.get("price") is not None or r.get("conviction_tier"))]
    comp_pre["rows_without_score_input_that_could_enter_objects"] = no_si_can_enter
    comp_ok = len(mism) == 0 and not no_si_can_enter
    for f in COMPOSITE_FLAGS:
        if f not in F:
            continue
        q3b[f] = {"status": "PASS" if comp_ok else "FAIL", "precondition": comp_pre}
        if comp_ok:
            def _t(rs, f=f):
                cfg = dict(full_cfg)
                cfg[f"FINPILOT_ENABLE_{f}"] = "0"
                sc = recompute_scores(cfg)
                out = copy.deepcopy(rs)
                for i, (rscore, comp) in sc.items():
                    out[i]["recommendation_score"] = round(rscore, 3)
                    out[i]["composite_score"] = comp
                return out
            transforms[f] = _t

    # CONVICTION_TIERS
    if "CONVICTION_TIERS" in F:
        def tier_of(sq, gap, rvol, atr_present):
            short_strong, gap_strong, gap_present, rvol_present = sq >= 0.5, gap >= 0.6, gap >= 0.2, rvol >= 0.25
            nfac = sum([short_strong, atr_present, gap_present, rvol_present])
            if short_strong and gap_strong:
                return "A"
            if (short_strong and atr_present) or nfac >= 3:
                return "B"
            if nfac >= 2:
                return "C"
            return ""
        uniquely, ambiguous_consistent, mismatch, not_evaluable = 0, 0, 0, 0
        amb_tickers = []
        for r in rows:
            stored = r.get("conviction_tier") or ""
            si = r.get("score_input")
            if not r.get("entry_ok"):
                uniquely += stored == ""
                mismatch += stored != ""
                continue
            if not isinstance(si, dict):
                not_evaluable += 1
                continue
            t1 = tier_of(float(si.get("squeeze_factor") or 0), float(si.get("gap_factor") or 0), float(si.get("rvol_factor") or 0), True)
            t0 = tier_of(float(si.get("squeeze_factor") or 0), float(si.get("gap_factor") or 0), float(si.get("rvol_factor") or 0), False)
            if t1 == t0 == stored:
                uniquely += 1
            elif stored in (t1, t0):
                ambiguous_consistent += 1
                amb_tickers.append(ticker(r))
            else:
                mismatch += 1
        ok = ambiguous_consistent == 0 and mismatch == 0 and not_evaluable == 0
        q3b["CONVICTION_TIERS"] = {"status": "PASS" if ok else "FAIL",
                                   "precondition": {"uniquely_reproduced": uniquely, "consistent_but_atr_dependent": ambiguous_consistent,
                                                    "atr_dependent_tickers": amb_tickers, "mismatch": mismatch, "not_evaluable": not_evaluable,
                                                    "note": "atr_pct_daily is not stored in the export; strict rule: every row must be uniquely reproduced"},
                                   "off_state_note": "OFF state is input-independent by code (features.py:221 returns ('',0.0)); export has no `tier` field (0/1801)"}
        if ok:
            def _t(rs):
                out = copy.deepcopy(rs)
                for r in out:
                    r["conviction_tier"], r["conviction_prob"] = "", 0.0
                return out
            transforms["CONVICTION_TIERS"] = _t

    # Error-template rows (evaluate.py:70-103 hard-coded result; never pass through
    # execution_contract()/position_cap()) are held fixed for the execution flags.
    # IMPLEMENTATION CORRECTION (documented): the first run applied the
    # position_cap() formula to these rows as well, producing 293 spurious
    # precondition mismatches; the locked rule (reproduce stored values under the
    # full configuration) is unchanged.
    template_idx = {i for i, r in enumerate(rows) if "scan_status" in r}
    no_si_idx = {i for i, r in enumerate(rows) if not isinstance(r.get("score_input"), dict)}
    template_can_enter = [ticker(rows[i]) for i in template_idx
                          if rows[i].get("entry_ok") or rows[i].get("conviction_tier") or rows[i].get("price") is not None]
    res["template_rows"] = {"count": len(template_idx), "equals_rows_without_score_input": template_idx == no_si_idx,
                            "could_enter_objects": template_can_enter}
    if template_idx != no_si_idx or template_can_enter:
        conflicts.append("error-template row set inconsistent or template rows could enter user-facing objects")
    res["implementation_corrections"] = [
        "Execution-flag Q3B preconditions/transforms restricted to main-path rows; 293 error-template rows (scan_status present, "
        "no score_input, entry_ok False, no conviction tier, price None) held fixed. First run had applied position_cap() to them "
        "(293 spurious mismatches, PORTFOLIO_ADV_LIMIT Q3B FAIL). Correction made after that run, determined by code provenance "
        "(evaluate.py error template), locked rule unchanged."]

    # EXECUTION_POLICY
    if "EXECUTION_POLICY" in F:
        mm = 0
        for i, r in enumerate(rows):
            if i in template_idx:
                continue
            adv = bool(((r.get("data_quality") or {}).get("available") or {}).get("dollar_adv", False))
            if bool(r.get("execution_feasible")) != adv or bool(r.get("selection_eligible")) != bool(r.get("entry_ok") and adv):
                mm += 1
        q3b["EXECUTION_POLICY"] = {"status": "PASS" if mm == 0 else "FAIL",
                                   "precondition": {"mismatches": mm, "main_path_rows": len(rows) - len(template_idx), "template_rows_held_fixed": len(template_idx)}}
        if mm == 0:
            def _t(rs):
                out = copy.deepcopy(rs)
                for i, r in enumerate(out):
                    if i in template_idx:
                        continue
                    r["execution_feasible"] = True
                    r["selection_eligible"] = bool(r.get("entry_ok"))
                return out
            transforms["EXECUTION_POLICY"] = _t

    # PORTFOLIO_ADV_LIMIT
    if "PORTFOLIO_ADV_LIMIT" in F:
        mm = 0
        for i, r in enumerate(rows):
            if i in template_idx:
                continue
            cap = r.get("position_cap_notional")
            exp_on = "adv_position_cap" if r.get("position_cap_applied") else ("portfolio_capacity_unknown" if cap is None else None)
            if r.get("position_cap_reject_reason") != exp_on:
                mm += 1
        q3b["PORTFOLIO_ADV_LIMIT"] = {"status": "PASS" if mm == 0 else "FAIL",
                                      "precondition": {"mismatches": mm, "main_path_rows": len(rows) - len(template_idx), "template_rows_held_fixed": len(template_idx)}}
        if mm == 0:
            def _t(rs):
                out = copy.deepcopy(rs)
                for i, r in enumerate(out):
                    if i in template_idx:
                        continue
                    r["position_cap_reject_reason"] = "portfolio_capacity_unknown" if r.get("position_cap_notional") is None else None
                return out
            transforms["PORTFOLIO_ADV_LIMIT"] = _t

    # ALPHA_V2
    if "ALPHA_V2" in F:
        raw_fields = [k for k in ("short_interest_pct", "short_percent", "float_shares", "shares_float", "short_comp", "float_comp") if any(k in r for r in rows)]
        q3b["ALPHA_V2"] = {"status": "FAIL" if not raw_fields else "REVIEW",
                           "precondition": {"raw_squeeze_inputs_in_export": raw_fields,
                                            "note": "squeeze_factor weights (features.py:151) and risk_engine stop/TP (risk_engine.py:204) require raw short/float and ATR-bar inputs not stored in the export"}}
    for f in F:
        q3b.setdefault(f, {"status": "FAIL", "precondition": {"note": "no reconstruction path"}})
    res["q3b"] = q3b

    # ── Q4 leave-one-out ─────────────────────────────────────────────────────
    def compare(full_o: dict, alt: dict) -> dict:
        out = {"row_order_integrity": full_o["row_order_sha"] == alt["row_order_sha"]}
        scope, mag, tie_only = {}, {}, {}
        for obj, n in (("O1", len(full_o["O1"])), ("O2", 2), ("O3", 10)):
            a, b = full_o[obj], alt[obj]
            inter = len(set(a) & set(b))
            changed_membership = set(a) != set(b)
            keys_src = "keys_web" if obj == "O3" else "keys_graded"
            ta, tb = full_o[keys_src][: len(a)], alt[keys_src][: len(b)]
            scope[f"{obj}_membership"] = changed_membership
            tie_only[f"{obj}_membership"] = changed_membership and ta == tb
            mag[obj] = {"N": n, "L_full": len(a), "L_without": len(b), "overlap": (inter / n if n else None),
                        "changed_count": n - inter if n else len(b), "entered": sorted(set(b) - set(a)), "exited": sorted(set(a) - set(b))}
            if obj == "O2":
                order_changed = a != b and not changed_membership
                scope["O2_order"] = order_changed
                tie_only["O2_order"] = order_changed and ta == tb
            # boundary tie group at N
            keys = full_o[keys_src]
            if n and len(keys) > n:
                bt = keys[n - 1]
                mag[obj]["boundary_tie_group_size"] = sum(1 for k in keys if k == bt) if keys[n] == bt else 1
            else:
                mag[obj]["boundary_tie_group_size"] = None
        union = sorted(set(full_o["O1"] + full_o["O3"] + alt["O1"] + alt["O3"]))
        table, disp = [], []
        for t in union:
            rf, rw = full_o["graded_rank"].get(t), alt["graded_rank"].get(t)
            wf, ww = full_o["web_rank"].get(t), alt["web_rank"].get(t)
            d = (rw - rf) if (rf is not None and rw is not None) else None
            if d is not None:
                disp.append(abs(d))
            table.append({"ticker": t, "rank_full": rf, "rank_without_f": rw, "delta_rank": d,
                          "web_rank_full": wf, "web_rank_without_f": ww,
                          "entered": t not in (full_o["O1"] + full_o["O3"]) and t in (alt["O1"] + alt["O3"]),
                          "exited": t in (full_o["O1"] + full_o["O3"]) and t not in (alt["O1"] + alt["O3"]),
                          "grade_full": full_o["grade"].get(t), "grade_without_f": alt["grade"].get(t),
                          "public_full": full_o["public"].get(t), "public_without_f": alt["public"].get(t)})
        mag["max_rank_displacement"] = max(disp) if disp else 0
        mag["public_status_changed_rows"] = sum(1 for t in full_o["public"] if full_o["public"][t] != alt["public"].get(t))
        any_change = any(scope.values())
        non_tie = any(v and not tie_only.get(k, False) for k, v in scope.items())
        cls = "USER_FACING_IMPACT" if non_tie else ("TIE_ONLY" if any_change else "NO_OBSERVED_USER_FACING_IMPACT")
        out.update(impact_scope=scope, tie_only=tie_only, impact_magnitude=mag, ticker_table=table, class_=cls)
        return out

    q4 = {"design": "C_full vs C_full - {f}; other conditions fixed", "per_flag": {}, "all_off_secondary": None}
    blocked = (not q0_ok) or q3a["status"] != "PASS"
    if blocked:
        q4["status"] = "NOT_EXECUTED" if not q0_ok else "BLOCKED_Q3A_FAIL"
    else:
        for f in F:
            if f not in transforms:
                q4["per_flag"][f] = {"class": "NOT_RECONSTRUCTIBLE"}
                continue
            alt_rows = transforms[f](rows)
            set_env(full_cfg)
            cmp_ = compare(full, build_objects(alt_rows))
            if not cmp_["row_order_integrity"]:
                conflicts.append(f"ROW_ORDER_INTEGRITY violated for {f}")
            cmp_["class"] = cmp_.pop("class_")
            q4["per_flag"][f] = cmp_
        recon = [f for f in F if f in transforms]
        alt_rows = rows
        for f in recon:
            alt_rows = transforms[f](alt_rows)
        set_env(full_cfg)
        ao = compare(full, build_objects(alt_rows))
        ao["class"] = ao.pop("class_")
        q4["all_off_secondary"] = {"flags_turned_off": recon, "not_computable_flags": [f for f in F if f not in transforms],
                                   "label": "descriptive; all-OFF over the reconstructible subset only" if len(recon) < len(F) else "descriptive",
                                   **{k: ao[k] for k in ("impact_scope", "impact_magnitude", "class")}}
        q4["status"] = "EXECUTED"
    res["q4"] = q4

    # ── total verdict (precedence) ───────────────────────────────────────────
    flag_classes = {f: q4["per_flag"].get(f, {}).get("class", "NOT_EXECUTED") for f in F}
    if q2["primary_status"] == "CONFIG_HASH_MATCH_LOCAL" and q3a["status"] != "PASS":
        conflicts.append("Q2 local hash match but Q3A FAIL")
    if conflicts:
        total = "CONFLICT"
    elif q3a["status"] != "PASS":
        total = "NOT_RECONSTRUCTIBLE"
    elif not q2_verified:
        total = "PRODUCTION_ENV_NOT_VERIFIABLE"
    elif any(c == "USER_FACING_IMPACT" for c in flag_classes.values()):
        total = "USER_FACING_IMPACT"
    elif any(c == "NOT_RECONSTRUCTIBLE" for c in flag_classes.values()):
        total = "INCOMPLETE"
    else:
        total = "NO_OBSERVED_USER_FACING_IMPACT"
    res["flags_class"] = flag_classes
    res["conflicts"] = conflicts
    res["total_verdict"] = total
    res["boundary"] = ("Behavioral difference under counterfactual flag removal only. Not predictive, economic, usefulness, harm or "
                       "authorization evidence. Does not imply any flag should be enabled or disabled.")
    res["production_impact"] = "NONE"
    OUT.write_text(json.dumps(res, indent=2, ensure_ascii=False, sort_keys=True, default=str) + "\n", encoding="utf-8")
    shutil.rmtree(work, ignore_errors=True)
    print(json.dumps({"total_verdict": total, "q0": res["q0"], "q1": q1_status, "q2": q2["primary_status"], "q3a": q3a["status"],
                      "q3b": {f: v["status"] for f, v in q3b.items()}, "flags": flag_classes, "conflicts": conflicts}, indent=2))


if __name__ == "__main__":
    main()
