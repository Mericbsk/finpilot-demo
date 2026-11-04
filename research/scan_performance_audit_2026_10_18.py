"""Offline, read-only analysis of the scanner timing JSONL."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import statistics
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "distribution" / "scan_timing.jsonl"
REPORTS = ROOT / "reports"
ARTIFACT_DATE = "2026-10-18"
COLD_RUN_TS = "2026-09-22T16:25:11.261907+00:00"

REPORT_PATH = REPORTS / f"scan_performance_audit_{ARTIFACT_DATE}.md"
STAGE_PATH = REPORTS / f"scan_stage_breakdown_{ARTIFACT_DATE}.csv"
VARIANCE_PATH = REPORTS / f"scan_variance_analysis_{ARTIFACT_DATE}.csv"
GAPS_PATH = REPORTS / f"scan_instrumentation_gaps_{ARTIFACT_DATE}.csv"

TOP_LEVEL_TIMERS = {
    "prefetch.alpaca",
    "prefetch.bulk_yfinance",
    "prefetch.repair",
}

STAGE_TYPES = {
    "evaluation.window": "UNKNOWN: scanner evaluation window mixes fetch and compute",
    "enrichment.window": "UNKNOWN: no process CPU profile",
    "persistence.window": "UNKNOWN: combined write/persist timer",
    "prefetch.alpaca": "UNKNOWN: provider wrapper does not isolate network from client work",
    "prefetch.repair": "UNKNOWN: repair wrapper mixes provider and fallback work",
    "prefetch.bulk_yfinance": "UNKNOWN: provider wrapper does not isolate network from client work",
    "fetch.request": "UNKNOWN: provider-call elapsed, network/client split absent",
    "fetch.parse": "UNKNOWN: parse timer, CPU not separately sampled",
    "retry.attempt": "UNKNOWN: provider-call time, not backoff-only time",
    "retry.backoff": "retry sleep timer; no process-level resource profile",
    "rate_limit.wait": "rate-limit wait timer; concurrent event sum is not wall time",
    "indicator.compute": "UNKNOWN: elapsed timer, process CPU not sampled",
    "evaluation.symbol": "UNKNOWN: per-symbol elapsed in a parallel worker pool",
    "prefetch.resample_4h": "UNKNOWN: processing elapsed, CPU not sampled",
    "prefetch.symbol_repair": "UNKNOWN: parallel symbol-repair elapsed",
    "prefetch.symbol_yfinance": "UNKNOWN: parallel symbol-fetch elapsed",
}

PER_SYMBOL_NOTES = {
    "evaluation.symbol": "Per-symbol event; linear scaling was not tested",
    "indicator.compute": "DataFrame-row count; not a per-symbol scaling test",
    "fetch.request": "Batch/provider-call event; scaling was not tested",
}


def as_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def percentile(values: list[float], fraction: float) -> float | None:
    clean = [value for value in values if math.isfinite(value)]
    if not clean:
        return None
    if len(clean) == 1:
        return clean[0]
    index = int(fraction * 100) - 1
    return statistics.quantiles(clean, n=100, method="inclusive")[index]


def metric(value: float | None, digits: int = 2) -> str:
    return "UNKNOWN" if value is None else f"{value:.{digits}f}"


def load_snapshot() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    before = SOURCE.stat()
    raw = SOURCE.read_bytes()
    after = SOURCE.stat()
    if (
        before.st_size != after.st_size
        or before.st_mtime_ns != after.st_mtime_ns
        or len(raw) != after.st_size
    ):
        raise RuntimeError("Timing JSONL changed during the read; rerun against a stable snapshot.")

    rows: list[dict[str, Any]] = []
    parse_error_lines: list[int] = []
    non_object_lines: list[int] = []
    text = raw.decode("utf-8")
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            parse_error_lines.append(line_number)
            continue
        if not isinstance(value, dict):
            non_object_lines.append(line_number)
            continue
        value["_source_line"] = line_number
        rows.append(value)

    return rows, {
        "sha256": hashlib.sha256(raw).hexdigest(),
        "bytes": len(raw),
        "nonempty_lines": sum(bool(line.strip()) for line in text.splitlines()),
        "parse_error_lines": parse_error_lines,
        "non_object_lines": non_object_lines,
        "mtime_utc": datetime.fromtimestamp(after.st_mtime, UTC).isoformat(),
    }


def stage_events(row: dict[str, Any]) -> list[dict[str, Any]]:
    events = row.get("stage_timing")
    if not isinstance(events, list):
        return []
    return [event for event in events if isinstance(event, dict)]


def stage_names(rows: list[dict[str, Any]]) -> set[str]:
    return {
        str(event["stage"])
        for row in rows
        for event in stage_events(row)
        if isinstance(event.get("stage"), str)
    }


def event_total(row: dict[str, Any], stage: str) -> tuple[int, float]:
    matching = [event for event in stage_events(row) if event.get("stage") == stage]
    elapsed = [as_number(event.get("elapsed_s")) for event in matching]
    return len(matching), sum(value for value in elapsed if value is not None)


def line_list(rows: list[dict[str, Any]], limit: int = 20) -> str:
    if len(rows) > limit:
        return f"{len(rows)} selected JSONL rows"
    return ";".join(str(row["_source_line"]) for row in rows)


def source_stats(rows: list[dict[str, Any]], key: str) -> list[float]:
    values = [as_number(row.get(key)) for row in rows]
    return [value for value in values if value is not None]


def ratio_values(
    rows: list[dict[str, Any]],
    numerator: str,
    denominator: str,
) -> list[float]:
    ratios: list[float] = []
    for row in rows:
        top = as_number(row.get(numerator))
        bottom = as_number(row.get(denominator))
        if top is not None and bottom is not None and bottom > 0:
            ratios.append(top / bottom * 100)
    return ratios


def paired_share_values(
    rows: list[dict[str, Any]],
    numerator: str,
    denominator: str,
    second_denominator: str | None = None,
) -> list[float]:
    shares: list[float] = []
    for row in rows:
        top = as_number(row.get(numerator))
        bottom = as_number(row.get(denominator))
        if second_denominator is not None:
            extra = as_number(row.get(second_denominator))
            if extra is None:
                continue
            bottom = (bottom or 0.0) + extra
        if top is not None and bottom is not None and bottom > 0:
            shares.append(top / bottom * 100)
    return shares


def pearson(pairs: list[tuple[float, float]]) -> float | None:
    if len(pairs) < 2:
        return None
    x_values = [pair[0] for pair in pairs]
    y_values = [pair[1] for pair in pairs]
    x_mean = statistics.mean(x_values)
    y_mean = statistics.mean(y_values)
    numerator = sum((x - x_mean) * (y - y_mean) for x, y in pairs)
    denominator = math.sqrt(
        sum((x - x_mean) ** 2 for x in x_values)
        * sum((y - y_mean) ** 2 for y in y_values)
    )
    return numerator / denominator if denominator else None


def is_universe_200(row: dict[str, Any]) -> bool:
    return as_number(row.get("universe")) == 200


def is_completed(row: dict[str, Any]) -> bool:
    return as_number(row.get("total_s")) is not None


def is_timed(row: dict[str, Any]) -> bool:
    return bool(stage_events(row))


def campaign_rows(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    sep21_failure = [
        row
        for row in rows
        if row.get("date") == "2026-09-21"
        and is_universe_200(row)
        and is_timed(row)
        and row.get("alpaca_total_failure") is True
    ]
    sep22_candidates = [
        row
        for row in rows
        if row.get("date") == "2026-09-22"
        and is_universe_200(row)
        and is_timed(row)
        and row.get("experiment_arm") == "A_baseline"
        and row.get("alpaca_total_failure") is False
        and row.get("alpaca_disabled") is False
        and as_number(row.get("result_symbols")) == 200
        and is_completed(row)
    ]
    cold = [row for row in sep22_candidates if row.get("ts") == COLD_RUN_TS]
    selected = [row for row in sep22_candidates if row.get("ts") != COLD_RUN_TS]
    return sep21_failure, sep22_candidates, selected if len(cold) == 1 else []


def stage_row(
    sample: str,
    stage: str,
    sample_rows: list[dict[str, Any]],
    *,
    top_level: bool = False,
    zero_when_absent: bool = False,
    custom_durations: list[float] | None = None,
    custom_shares: list[float] | None = None,
    custom_event_count: int | None = None,
    custom_lines: str | None = None,
    scope: str,
) -> dict[str, str]:
    durations: list[float] = []
    shares: list[float] = []
    selected_lines: list[dict[str, Any]] = []
    event_count = 0
    runs_with_event = 0

    if custom_durations is None:
        for row in sample_rows:
            count, elapsed = event_total(row, stage)
            event_count += count
            if count:
                runs_with_event += 1
                durations.append(elapsed)
                selected_lines.append(row)
                if top_level:
                    total = as_number(row.get("total_s"))
                    if total is not None and total > 0:
                        shares.append(elapsed / total * 100)
            elif zero_when_absent:
                durations.append(0.0)
                if top_level:
                    total = as_number(row.get("total_s"))
                    if total is not None and total > 0:
                        shares.append(0.0)
    else:
        durations = custom_durations
        shares = custom_shares or []
        event_count = custom_event_count or 0
        runs_with_event = len(durations)
        selected_lines = sample_rows

    median = statistics.median(durations) if durations else None
    p95 = percentile(durations, 0.95)
    share_median = statistics.median(shares) if shares else None
    share_p95 = percentile(shares, 0.95)
    duration_label = "DERIVED" if event_count else ("LOGGED" if zero_when_absent else "UNKNOWN")
    if not durations:
        duration_label = "UNKNOWN"
    share_label = "DERIVED" if shares else "UNKNOWN"
    ceiling = share_median if top_level else None
    ceiling_label = "DERIVED" if ceiling is not None else "UNKNOWN"
    return {
        "sample": sample,
        "stage": stage,
        "source_label": "LOGGED" if event_count else ("LOGGED" if zero_when_absent else "UNKNOWN"),
        "summary_label": duration_label,
        "runs_in_sample": str(len(sample_rows)),
        "runs_with_event": str(runs_with_event),
        "event_count": str(event_count),
        "median_s": metric(median, 6),
        "p95_s": metric(p95, 6),
        "share_label": share_label,
        "median_run_share_percent": metric(share_median, 2),
        "p95_run_share_percent": metric(share_p95, 2),
        "share_basis": "paired run stage seconds / total_s; median and inclusive p95"
        if shares
        else "UNKNOWN; event sums are nested or parallel work, not wall-clock share",
        "bottleneck_type": STAGE_TYPES.get(stage, "UNKNOWN"),
        "per_symbol_scaling": PER_SYMBOL_NOTES.get(
            stage, "UNKNOWN; fixed-size sample does not establish scaling"
        ),
        "ceiling_label": ceiling_label,
        "theoretical_max_gain_percent": metric(ceiling, 2),
        "measurement_scope": scope,
        "source_lines": custom_lines or line_list(selected_lines),
    }


def window_row(
    sample: str,
    stage: str,
    rows: list[dict[str, Any]],
    field: str,
    *,
    denominator: str,
    second_denominator: str | None = None,
    scope: str,
    bottleneck_type: str,
    per_symbol: str,
) -> dict[str, str]:
    durations = source_stats(rows, field)
    shares = paired_share_values(rows, field, denominator, second_denominator)
    median = statistics.median(durations) if durations else None
    p95 = percentile(durations, 0.95)
    share_median = statistics.median(shares) if shares else None
    share_p95 = percentile(shares, 0.95)
    ceiling = share_median
    denominator_text = f"{denominator} + {second_denominator}" if second_denominator else denominator
    return {
        "sample": sample,
        "stage": stage,
        "source_label": "LOGGED" if durations else "UNKNOWN",
        "summary_label": "DERIVED" if durations else "UNKNOWN",
        "runs_in_sample": str(len(rows)),
        "runs_with_event": str(len(durations)),
        "event_count": "n/a",
        "median_s": metric(median, 3),
        "p95_s": metric(p95, 3),
        "share_label": "DERIVED" if shares else "UNKNOWN",
        "median_run_share_percent": metric(share_median, 2),
        "p95_run_share_percent": metric(share_p95, 2),
        "share_basis": f"paired run {field} / {denominator_text}; median and inclusive p95"
        if shares
        else "UNKNOWN",
        "bottleneck_type": bottleneck_type,
        "per_symbol_scaling": per_symbol,
        "ceiling_label": "DERIVED" if ceiling is not None else "UNKNOWN",
        "theoretical_max_gain_percent": metric(ceiling, 2),
        "measurement_scope": scope,
        "source_lines": line_list(rows, limit=0),
    }


def combined_prefetch_row(rows: list[dict[str, Any]]) -> dict[str, str] | None:
    durations: list[float] = []
    shares: list[float] = []
    selected: list[dict[str, Any]] = []
    events = 0
    for row in rows:
        alpaca_count, alpaca_s = event_total(row, "prefetch.alpaca")
        repair_count, repair_s = event_total(row, "prefetch.repair")
        total = as_number(row.get("total_s"))
        if not alpaca_count or not repair_count or total is None or total <= 0:
            continue
        elapsed = alpaca_s + repair_s
        durations.append(elapsed)
        shares.append(elapsed / total * 100)
        events += alpaca_count + repair_count
        selected.append(row)
    if not durations:
        return None
    median = statistics.median(durations)
    share_median = statistics.median(shares)
    return {
        "sample": "2026-09-22 API stage cohort; first cold run excluded",
        "stage": "prefetch.alpaca + prefetch.repair (sequential timers)",
        "source_label": "LOGGED",
        "summary_label": "DERIVED",
        "runs_in_sample": str(len(rows)),
        "runs_with_event": str(len(durations)),
        "event_count": str(events),
        "median_s": metric(median, 3),
        "p95_s": metric(percentile(durations, 0.95), 3),
        "share_label": "DERIVED",
        "median_run_share_percent": metric(share_median, 2),
        "p95_run_share_percent": metric(percentile(shares, 0.95), 2),
        "share_basis": "paired sum of sequential top-level timers / total_s",
        "bottleneck_type": "UNKNOWN: provider and repair work are not resource-profiled",
        "per_symbol_scaling": "UNKNOWN; fixed 200-symbol sample",
        "ceiling_label": "DERIVED",
        "theoretical_max_gain_percent": metric(share_median, 2),
        "measurement_scope": "200-symbol campaign only; not a full-universe ceiling",
        "source_lines": line_list(selected),
    }


def build_stage_rows(
    completed_200: list[dict[str, Any]],
    persisted_200: list[dict[str, Any]],
    sep21_failure: list[dict[str, Any]],
    sep22_selected: list[dict[str, Any]],
) -> list[dict[str, str]]:
    rows = [
        window_row(
            "All completed 200-symbol requests",
            "evaluation.window (eval_s)",
            completed_200,
            "eval_s",
            denominator="total_s",
            scope="LOGGED 200-symbol requests; eval_s/total_s is not a full-universe share",
            bottleneck_type="UNKNOWN: eval_s includes prefetch and evaluation; no CPU/network split",
            per_symbol="UNKNOWN; mixed scanner window",
        ),
        window_row(
            "All completed 200-symbol requests",
            "enrichment.window (enrich_s)",
            completed_200,
            "enrich_s",
            denominator="total_s",
            scope="LOGGED 200-symbol requests; share is within total_s only",
            bottleneck_type="UNKNOWN: no process CPU or I/O profile",
            per_symbol="UNKNOWN; mixed result enrichment",
        ),
        window_row(
            "Completed 200-symbol requests with persist_s",
            "persistence.window (persist_s)",
            persisted_200,
            "persist_s",
            denominator="total_s",
            second_denominator="persist_s",
            scope="130 paired records; denominator total_s + persist_s excludes outer request/log overhead",
            bottleneck_type="UNKNOWN: combined persistence timer, no per-operation split",
            per_symbol="UNKNOWN; combined persistence phase",
        ),
    ]

    cohorts = (
        (
            "2026-09-21 Alpaca-total-failure cohort (not comparable)",
            sep21_failure,
            "200-symbol runs with alpaca_total_failure=true; excluded from production-path conclusions",
        ),
        (
            "2026-09-22 API stage cohort; first cold run excluded",
            sep22_selected,
            "Same 200 symbols; A_baseline and Alpaca active per decision log; remaining cache state UNKNOWN",
        ),
    )
    for sample, records, scope in cohorts:
        names = stage_names(records)
        if sample.startswith("2026-09-22"):
            names.add("retry.backoff")
        for name in sorted(names):
            rows.append(
                stage_row(
                    sample,
                    name,
                    records,
                    top_level=name in TOP_LEVEL_TIMERS,
                    zero_when_absent=name == "retry.backoff",
                    scope=scope,
                )
            )
        if sample.startswith("2026-09-22"):
            combined = combined_prefetch_row(records)
            if combined is not None:
                rows.append(combined)

    rows.append(
        {
            "sample": "Requested full universe",
            "stage": "full_universe.end_to_end",
            "source_label": "UNKNOWN",
            "summary_label": "UNKNOWN",
            "runs_in_sample": "0",
            "runs_with_event": "0",
            "event_count": "UNKNOWN",
            "median_s": "UNKNOWN",
            "p95_s": "UNKNOWN",
            "share_label": "UNKNOWN",
            "median_run_share_percent": "UNKNOWN",
            "p95_run_share_percent": "UNKNOWN",
            "share_basis": "UNKNOWN; no full-universe timing row",
            "bottleneck_type": "UNKNOWN",
            "per_symbol_scaling": "UNKNOWN",
            "ceiling_label": "UNKNOWN",
            "theoretical_max_gain_percent": "UNKNOWN",
            "measurement_scope": "No single timing-log row exceeds universe=200",
            "source_lines": "",
        }
    )
    return rows


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def build_variance_rows(
    rows: list[dict[str, Any]],
    sep21_failure: list[dict[str, Any]],
    sep22_candidates: list[dict[str, Any]],
    sep22_selected: list[dict[str, Any]],
) -> list[dict[str, str]]:
    sep21_lines = {row["_source_line"] for row in sep21_failure}
    sep22_candidate_lines = {row["_source_line"] for row in sep22_candidates}
    sep22_selected_lines = {row["_source_line"] for row in sep22_selected}
    variance: list[dict[str, str]] = []
    for row in rows:
        if not is_universe_200(row):
            continue
        line = row["_source_line"]
        timestamp = str(row.get("ts") or "UNKNOWN")
        total = as_number(row.get("total_s"))
        persisted = as_number(row.get("persist_s"))
        if line in sep21_lines:
            campaign = "2026-09-21 Alpaca-total-failure; not comparable"
        elif line in sep22_selected_lines:
            campaign = "2026-09-22 API stage cohort; selected run"
        elif line in sep22_candidate_lines and timestamp == COLD_RUN_TS:
            campaign = "2026-09-22 API stage cohort; first cold run excluded"
        else:
            campaign = "Other historical 200-symbol record"
        if timestamp == COLD_RUN_TS:
            cache_state = "COLD per decision log; cache field absent from JSONL"
        else:
            cache_state = "UNKNOWN"
        paired_share = None
        if total is not None and persisted is not None and total + persisted > 0:
            paired_share = persisted / (total + persisted) * 100
        events = stage_events(row)
        variance.append(
            {
                "source_line": str(line),
                "record_label": "LOGGED",
                "date": str(row.get("date") or "UNKNOWN"),
                "timestamp": timestamp,
                "universe": metric(as_number(row.get("universe")), 0),
                "symbols": metric(as_number(row.get("symbols")), 0),
                "total_s": metric(total, 3),
                "eval_s": metric(as_number(row.get("eval_s")), 3),
                "enrich_s": metric(as_number(row.get("enrich_s")), 3),
                "persist_s": metric(persisted, 3),
                "persist_share_label": "DERIVED" if paired_share is not None else "UNKNOWN",
                "persist_share_of_recorded_windows_percent": metric(paired_share, 3),
                "yf_fallback": metric(as_number(row.get("yf_fallback")), 0),
                "yf_bulk_requests": metric(as_number(row.get("yf_bulk_requests")), 0),
                "yf_bulk_symbols": metric(as_number(row.get("yf_bulk_symbols")), 0),
                "experiment_arm": str(row.get("experiment_arm") or "UNKNOWN"),
                "alpaca_total_failure": str(row.get("alpaca_total_failure", "UNKNOWN")),
                "alpaca_disabled": str(row.get("alpaca_disabled", "UNKNOWN")),
                "result_symbols": metric(as_number(row.get("result_symbols")), 0),
                "stage_timing_events": str(len(events)),
                "stage_timing_label": "LOGGED" if events else "UNKNOWN",
                "campaign_classification": campaign,
                "cache_state": cache_state,
                "market_session": "UNKNOWN",
            }
        )
    return variance


def build_gap_rows(max_universe: float | None, full200: int, completed200: int) -> list[dict[str, str]]:
    return [
        {
            "gap_or_stage": "Full-universe end-to-end wall clock",
            "status_label": "UNKNOWN",
            "evidence_label": "DERIVED",
            "current_evidence": f"max logged universe={metric(max_universe, 0)}; {full200} universe=200 rows, {completed200} with total_s",
            "why_unmeasured": "No single timing-log record represents the requested full universe; no batch-chain wall timer or campaign ID.",
            "how_to_measure": "Use an approved full-universe API campaign with an outer timer around the complete batch chain and final response.",
        },
        {
            "gap_or_stage": "End-to-end request overhead",
            "status_label": "UNKNOWN",
            "evidence_label": "UNKNOWN",
            "current_evidence": "total_s stops before persistence; persist_s is separate; timing-log append and analytics occur later.",
            "why_unmeasured": "No timer spans request queueing, all work, persistence, timing-log append, analytics, and response return.",
            "how_to_measure": "Add or externally capture one request-level wall timer without changing scanner outputs.",
        },
        {
            "gap_or_stage": "Persistence sub-operations",
            "status_label": "LOGGED",
            "evidence_label": "LOGGED",
            "current_evidence": "persist_s is present for 130 completed 200-symbol rows; it combines four persistence calls.",
            "why_unmeasured": "No per-call breakdown; timing-log append and analytics are outside persist_s.",
            "how_to_measure": "Record the four existing persistence calls separately and retain an outer persistence timer.",
        },
        {
            "gap_or_stage": "Network versus CPU versus disk I/O",
            "status_label": "UNKNOWN",
            "evidence_label": "UNKNOWN",
            "current_evidence": "Stage elapsed values exist in historical rows, but no process CPU, disk, or network profile was captured.",
            "why_unmeasured": "Wall timers do not identify the physical resource consuming time.",
            "how_to_measure": "Collect process/resource profiles during the approved same-path campaign; do not infer from stage names.",
        },
        {
            "gap_or_stage": "Cache state and cold-versus-hot effect",
            "status_label": "UNKNOWN",
            "evidence_label": "UNKNOWN",
            "current_evidence": "Cache state is absent from JSONL; only the first Sep 22 run is tagged cold in the decision log.",
            "why_unmeasured": "No repeated, controlled cold/hot cohorts; remaining Sep 22 cache state is not recorded.",
            "how_to_measure": "Declare and record cache state for each repeated run in one environment.",
        },
        {
            "gap_or_stage": "Market session and provider conditions",
            "status_label": "UNKNOWN",
            "evidence_label": "UNKNOWN",
            "current_evidence": "No market-session, provider-latency baseline, or resource-contention fields in the timing record.",
            "why_unmeasured": "Historical runs are not a controlled time-of-day or provider experiment.",
            "how_to_measure": "Capture market session and provider/resource context alongside the approved repeated runs.",
        },
        {
            "gap_or_stage": "Per-timeframe repair wall time",
            "status_label": "UNKNOWN",
            "evidence_label": "LOGGED",
            "current_evidence": "Some inner fetch events include timeframe; prefetch.repair is an outer aggregate timer.",
            "why_unmeasured": "No outer repair timer split by timeframe; nested request times cannot substitute for it.",
            "how_to_measure": "Add per-timeframe outer spans while preserving the existing aggregate timer.",
        },
        {
            "gap_or_stage": "Rate-limit and retry totals for the full universe",
            "status_label": "UNKNOWN",
            "evidence_label": "LOGGED",
            "current_evidence": "rate_limit.wait and retry.attempt events exist in the five-run 200-symbol cohort; no retry.backoff event was logged there.",
            "why_unmeasured": "The event cohort is not a full-universe run; event sums are not total request wall time.",
            "how_to_measure": "Retain per-event timers and summarize them for the full approved campaign, including explicit backoff events.",
        },
        {
            "gap_or_stage": "Batch gaps and run grouping",
            "status_label": "UNKNOWN",
            "evidence_label": "UNKNOWN",
            "current_evidence": "Rows have timestamps but no shared full-scan/campaign identifier or measured inter-batch interval.",
            "why_unmeasured": "Timestamp deltas can include unrelated API activity and are not a controlled batch-gap measurement.",
            "how_to_measure": "Attach a campaign identifier and capture the full scheduler/API cycle wall clock.",
        },
        {
            "gap_or_stage": "Linear scale model",
            "status_label": "UNKNOWN",
            "evidence_label": "UNKNOWN",
            "current_evidence": "Instrumented runs use a fixed 200-symbol request size; no larger sample establishes scaling.",
            "why_unmeasured": "Fixed costs, fallback mix, cache, and non-linear effects are not separated.",
            "how_to_measure": "Measure multiple controlled universe sizes on the same path before fitting the requested model.",
        },
        {
            "gap_or_stage": "Stage timer label mapping",
            "status_label": "UNKNOWN",
            "evidence_label": "UNKNOWN",
            "current_evidence": "The prompt lists prefetch.symbol_yfinance; current code also has prefetch.symbol_repair, with distinct timer sites.",
            "why_unmeasured": "Historical aliases must not be merged without a verified semantic mapping.",
            "how_to_measure": "Keep exact event labels and document any mapping before aggregating across versions.",
        },
    ]


def find_stage_row(rows: list[dict[str, str]], sample: str, stage: str) -> dict[str, str] | None:
    return next(
        (row for row in rows if row["sample"] == sample and row["stage"] == stage),
        None,
    )


def build_report(
    rows: list[dict[str, Any]],
    snapshot: dict[str, Any],
    completed_200: list[dict[str, Any]],
    persisted_200: list[dict[str, Any]],
    stage_rows: list[dict[str, str]],
    sep21_failure: list[dict[str, Any]],
    sep22_candidates: list[dict[str, Any]],
    sep22_selected: list[dict[str, Any]],
) -> str:
    total_values = source_stats(completed_200, "total_s")
    fallback_values = source_stats(completed_200, "yf_fallback")
    persist_values = source_stats(persisted_200, "persist_s")
    persist_shares = paired_share_values(
        persisted_200,
        "persist_s",
        "total_s",
        "persist_s",
    )
    correlation_pairs = [
        (fallback, total)
        for row in completed_200
        if (fallback := as_number(row.get("yf_fallback"))) is not None
        and (total := as_number(row.get("total_s"))) is not None
    ]
    correlation = pearson(correlation_pairs)
    universes = [as_number(row.get("universe")) for row in rows]
    max_universe = max((value for value in universes if value is not None), default=None)
    all_200 = [row for row in rows if is_universe_200(row)]
    timed = [row for row in rows if is_timed(row)]
    timed_200 = [row for row in all_200 if is_timed(row)]
    persist_share_median = statistics.median(persist_shares) if persist_shares else None
    persist_share_p95 = percentile(persist_shares, 0.95)

    repair_durations = [
        event_total(row, "prefetch.repair")[1]
        for row in sep22_selected
        if event_total(row, "prefetch.repair")[0]
    ]
    repair_shares = [
        event_total(row, "prefetch.repair")[1] / as_number(row["total_s"]) * 100
        for row in sep22_selected
        if event_total(row, "prefetch.repair")[0]
        and as_number(row.get("total_s")) is not None
        and as_number(row["total_s"]) > 0
    ]
    repair_median = statistics.median(repair_durations) if repair_durations else None
    repair_mean = statistics.mean(repair_durations) if repair_durations else None
    campaign_totals = source_stats(sep22_selected, "total_s")
    campaign_total_median = statistics.median(campaign_totals) if campaign_totals else None
    repair_share_median = statistics.median(repair_shares) if repair_shares else None
    repair_ratio_of_medians = (
        repair_median / campaign_total_median * 100
        if repair_median is not None and campaign_total_median
        else None
    )
    mean_over_median = (
        repair_mean / campaign_total_median * 100
        if repair_mean is not None and campaign_total_median
        else None
    )
    repair_share_min = min(repair_shares) if repair_shares else None
    repair_share_max = max(repair_shares) if repair_shares else None

    completed_stats = {
        "median": statistics.median(total_values) if total_values else None,
        "p95": percentile(total_values, 0.95),
        "minimum": min(total_values) if total_values else None,
        "maximum": max(total_values) if total_values else None,
    }
    fallback_stats = {
        "median": statistics.median(fallback_values) if fallback_values else None,
        "p95": percentile(fallback_values, 0.95),
        "minimum": min(fallback_values) if fallback_values else None,
        "maximum": max(fallback_values) if fallback_values else None,
    }
    p95_to_median = (
        completed_stats["p95"] / completed_stats["median"]
        if completed_stats["p95"] is not None
        and completed_stats["median"]
        else None
    )
    max_to_min = (
        completed_stats["maximum"] / completed_stats["minimum"]
        if completed_stats["maximum"] is not None
        and completed_stats["minimum"]
        and completed_stats["minimum"] > 0
        else None
    )
    stage_coverage_all = len(timed) / len(rows) * 100 if rows else None
    stage_coverage_200 = len(timed_200) / len(all_200) * 100 if all_200 else None
    stage_coverage_completed = (
        len([row for row in completed_200 if is_timed(row)]) / len(completed_200) * 100
        if completed_200
        else None
    )
    mismatch_count = sum(
        as_number(row.get("symbols")) != 200 for row in completed_200
    )

    report_table = [
        "| Sample | Stage/window | n | p50 seconds | p95 seconds | p50 run share | p95 run share | Amdahl ceiling |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    requested_rows = [
        ("All completed 200-symbol requests", "evaluation.window (eval_s)"),
        ("All completed 200-symbol requests", "enrichment.window (enrich_s)"),
        ("Completed 200-symbol requests with persist_s", "persistence.window (persist_s)"),
        ("2026-09-22 API stage cohort; first cold run excluded", "prefetch.alpaca"),
        ("2026-09-22 API stage cohort; first cold run excluded", "prefetch.repair"),
        (
            "2026-09-22 API stage cohort; first cold run excluded",
            "prefetch.alpaca + prefetch.repair (sequential timers)",
        ),
        (
            "2026-09-21 Alpaca-total-failure cohort (not comparable)",
            "prefetch.bulk_yfinance",
        ),
    ]
    for sample, stage in requested_rows:
        item = find_stage_row(stage_rows, sample, stage)
        if item is None:
            continue
        report_table.append(
            "| {sample} | {stage} | {n} | {median} | {p95} | {share} | {share_p95} | {ceiling} |".format(
                sample=sample,
                stage=stage,
                n=item["runs_with_event"],
                median=item["median_s"],
                p95=item["p95_s"],
                share=item["median_run_share_percent"],
                share_p95=item["p95_run_share_percent"],
                ceiling=item["theoretical_max_gain_percent"],
            )
        )

    full200_lines = [row["_source_line"] for row in completed_200]
    sep21_lines = [row["_source_line"] for row in sep21_failure]
    sep22_lines = [row["_source_line"] for row in sep22_selected]
    parse_count = len(snapshot["parse_error_lines"])
    object_count = len(rows)
    now = datetime.now(UTC).isoformat()
    current_date_rows = [row for row in rows if row.get("date") == ARTIFACT_DATE]
    current_date_no_total = [row for row in current_date_rows if as_number(row.get("total_s")) is None]
    source_growth_note = (
        "The source was observed growing from 817 to 820 non-empty records during this audit; "
        "the three appended tail records have universe=8 and no total_s, so they do not change "
        "the completed 200-symbol population."
    )

    return f"""# Scan Performance Audit - {ARTIFACT_DATE}

**PRIMARY STATUS = NOT MEASURED.** The requested full-universe, end-to-end stage allocation cannot be stated from these records. This is an offline audit: no live scan, provider request, API request, flag change, `.env` read/write, production change, publication, commit, or push was performed.

## 1. Executive Summary

- **DERIVED from LOGGED JSONL:** {object_count} JSON objects parsed; {parse_count} JSON parse errors and {len(snapshot['non_object_lines'])} non-object JSON lines; SHA-256 snapshot `{snapshot['sha256']}`.
- **DERIVED from LOGGED rows:** {len(all_200)} records have `universe=200`; {len(completed_200)} have `total_s`; maximum logged `universe` is {metric(max_universe, 0)}. A 200-symbol request is not the full universe.
- **DERIVED from LOGGED `total_s`:** median {metric(completed_stats['median'])} s; p95 {metric(completed_stats['p95'])} s; range {metric(completed_stats['minimum'])}-{metric(completed_stats['maximum'])} s, n={len(total_values)}.
- **DERIVED from LOGGED stage events:** only {len(timed)} of {object_count} records have nonempty `stage_timing`; the comparable Sep 22 stage cohort is {len(sep22_selected)} runs after excluding its documented first cold run.
- **DERIVED, Sep 22 200-symbol cohort only:** `prefetch.repair` median {metric(repair_median, 3)} s; median paired run share {metric(repair_share_median)}% (range {metric(repair_share_min)}-{metric(repair_share_max)}%). Not a full-universe result.
- **DERIVED from LOGGED persistence fields:** `persist_s` is available for {len(persist_values)} completed 200-symbol rows; median {metric(statistics.median(persist_values) if persist_values else None)} s, p95 {metric(percentile(persist_values, 0.95))} s.
- The 81.6% historical repair-share label conflicts with raw-row statistics; this report exposes both definitions and does not edit the historical documents.
- **No full-universe bottleneck, share, or Amdahl ceiling is asserted.**

## 2. Feasibility Gate

| Capability | Status | Consequence |
|---|---|---|
| Python runtime | Available; used for offline parsing and artifact generation | Offline analysis is reproducible; no scanner ran. |
| `time.perf_counter` | Present in scanner/API code | Historical timers exist; no new scanner timing was taken. |
| `cProfile` | Available in the selected Python runtime; not run | CPU profile remains absent. |
| `psutil` | Installed in the selected Python runtime; not used | No process CPU/RAM sample was collected. |
| Workspace disk write | Available; analyzer wrote only the new dated artifacts; a separate Level A receipt was appended to the decision log | Runtime data and application state were not written. |
| Local API | Not tested | No API request was issued. |
| External provider network | Not tested | No provider request or credential use occurred. |
| Live `FINPILOT_SCAN_STAGE_TIMING` state | UNKNOWN; not inspected or changed | Historical event rows show prior opt-in runs only. |

## 3. Instrumentation Status

**DERIVED from LOGGED rows:** `stage_timing` is nonempty in {len(timed)}/{object_count} records ({metric(stage_coverage_all)}%), {len(timed_200)}/{len(all_200)} `universe=200` records ({metric(stage_coverage_200)}%), and {len([row for row in completed_200 if is_timed(row)])}/{len(completed_200)} completed 200-symbol records ({metric(stage_coverage_completed)}%). The timed population separates into {len(sep21_failure)} Sep 21 rows with `alpaca_total_failure=true` and {len(sep22_candidates)} Sep 22 API-campaign rows; the first Sep 22 run is excluded from the five-run comparison per the decision log.

**DERIVED from LOGGED fields:** `persist_s` is present on {len(persist_values)}/{len(completed_200)} completed 200-symbol rows. It is a combined persistence timer, not an operation-level breakdown. The current live flag value is not known from this audit.

## 4. Measurement Window

**CODE-VERIFIED:** in `api/routers/scan.py`, `total_s` is captured from `_t_start` to `_t_scoring_done`, after scanner evaluation and `_enrich_results`. It ends before the four persistence calls. `persist_s` separately times `_persist_shortlist`, `_persist_shadow_ledger`, `_auto_add_watchlist`, and `_persist_distribution_export`. The timing-log append and analytics increment occur after `persist_s`; request queueing before `_t_start` and response completion are also outside these fields. Therefore neither `total_s` nor `total_s + persist_s` is a proven end-to-end request duration.

## 5. Stage Breakdown and Amdahl Ceiling

The table statistics are **DERIVED from LOGGED** timer values. p50/p95 are calculated over per-run values using `statistics.quantiles(method="inclusive")`; run shares are paired per-run ratios, not ratios of unrelated medians. Event-level sums for parallel or nested timers are not treated as wall-clock shares.

{chr(10).join(report_table)}

For the valid Sep 22 sample (JSONL source lines {sep22_lines[0] if sep22_lines else 'UNKNOWN'}-{sep22_lines[-1] if sep22_lines else 'UNKNOWN'}), the raw `prefetch.repair` values have mean {metric(repair_mean, 3)} s and median {metric(repair_median, 3)} s. The total median is {metric(campaign_total_median, 3)} s. Therefore:

- **DERIVED:** median of paired `repair_s / total_s` ratios = {metric(repair_share_median)}% (run range {metric(repair_share_min)}-{metric(repair_share_max)}%); this is the sample-specific Amdahl ceiling for that measured 200-symbol window.
- **DERIVED:** ratio of medians = `median(repair_s) / median(total_s)` = {metric(repair_ratio_of_medians)}%.
- **DERIVED:** `mean(repair_s) / median(total_s)` = {metric(mean_over_median)}%; this reproduces the historical 81.6% value, but it is not a ratio of medians.

The `prefetch.alpaca` and `prefetch.repair` timers are sequential top-level blocks in `scanner/data_fetcher.py`. `evaluation.symbol`, `indicator.compute`, `fetch.request`, `fetch.parse`, `rate_limit.wait`, and retry timers are inner or parallel events. Their per-run event sums are retained in the stage CSV, but their end-to-end shares and Amdahl ceilings are UNKNOWN. Six Sep 21 stage rows ({';'.join(map(str, sep21_lines)) if sep21_lines else 'none'}) belong to the separate Alpaca-total-failure regime and are not merged into the Sep 22 cohort.

## 6. Bottleneck Type

**UNKNOWN for the full universe.** The five-run Sep 22 `prefetch.repair` wall timer includes repair/provider/fallback work; the event data does not split network wait from client parsing or other processing. `rate_limit.wait` is explicitly timed in the sample, but summing concurrent event durations does not establish its wall-clock contribution. No CPU, disk-I/O, memory-pressure, or lock-wait profile was collected. No optimization conclusion follows from stage names alone.

## 7. Variance Analysis

**DERIVED from LOGGED completed 200-symbol rows (n={len(total_values)}):** `total_s` median {metric(completed_stats['median'])} s, p95 {metric(completed_stats['p95'])} s, minimum {metric(completed_stats['minimum'])} s, maximum {metric(completed_stats['maximum'])} s; p95/median={metric(p95_to_median, 3)} and max/min={metric(max_to_min, 3)}. `yf_fallback` median {metric(statistics.median(fallback_values) if fallback_values else None)} and p95 {metric(percentile(fallback_values, 0.95))}; Pearson r(total_s, yf_fallback)={metric(correlation, 3)} over n={len(correlation_pairs)} paired rows (**DERIVED, observational; not causal**).

**LOGGED Sep 22 sample:** the five selected runs span total_s {metric(min(campaign_totals) if campaign_totals else None)}-{metric(max(campaign_totals) if campaign_totals else None)} s and `yf_fallback` {metric(min(source_stats(sep22_selected, 'yf_fallback')) if sep22_selected else None, 0)}-{metric(max(source_stats(sep22_selected, 'yf_fallback')) if sep22_selected else None, 0)}. Cache state for these runs is UNKNOWN except the first run's cold label in the decision log; the remaining runs are not assumed warm. Market session is UNKNOWN. The variance CSV preserves each 200-symbol row and its source line.

**Snapshot note:** {source_growth_note}

## 8. Serialization Analysis

**LOGGED:** the five selected Sep 22 rows contain timed `rate_limit.wait` and `retry.attempt` events. The `retry.backoff` timer is present in code but has zero events in this cohort; no backoff duration is inferred for other runs. **UNKNOWN:** full-universe rate-limit/backoff totals, worker saturation, GIL contribution, lock contention, and batch-gap time. No parallelism change is recommended.

## 9. Scale Model

`total_s ≈ fixed_cost + symbols × per_symbol_cost + fallback_symbols × fallback_extra_cost`

All terms are **UNKNOWN** for the full universe. The largest `universe` value in this timing-log snapshot is {metric(max_universe, 0)}; all stage-instrumented runs use a 200-symbol request. No extrapolation or `ESTIMATED` value is supplied.

## 10. Instrumentation Gaps

See `{GAPS_PATH.relative_to(ROOT).as_posix()}` for the full gap register. Principal gaps: full-universe end-to-end wall time, persistence sub-operation timing, physical resource split, controlled cache/session metadata, per-timeframe outer repair timing, batch-chain identifiers, and validated scale behavior. The master prompt's `prefetch.symbol_yfinance` label is not merged with the distinct current-code timer `prefetch.symbol_repair`.

## 11. Decision Tree Result

**Status F: measurement incomplete.** Partial 200-symbol stage timings exist, but no full-universe end-to-end stage allocation exists. The master prompt's success sentence cannot be populated without extrapolation; no full-universe bottleneck or percentage is claimed.

## 12. Bottlenecks by Impact

1. **Full-universe bottleneck:** UNKNOWN; ranking and ceiling are UNKNOWN.
2. **Sep 22 200-symbol sample only:** `prefetch.repair` has a derived median paired share of {metric(repair_share_median)}%; its sample-specific ceiling is not transferable to the full universe or another cache/provider regime.
3. **Persistence in the paired logged windows only:** median `persist_s` is {metric(statistics.median(persist_values) if persist_values else None, 3)} s; median `persist_s/(total_s+persist_s)` is {metric(persist_share_median, 3)}% (p95 {metric(persist_share_p95, 3)}%). This excludes outer request/logging overhead and is not a full-request ceiling.

## 13. What We Measured

- **LOGGED:** source `data/distribution/scan_timing.jsonl`, SHA-256 `{snapshot['sha256']}`, {snapshot['bytes']} bytes, {snapshot['nonempty_lines']} nonempty lines; {len(rows)} JSON objects, {parse_count} JSON parse errors, and {len(snapshot['non_object_lines'])} non-object JSON lines.
- **DERIVED:** {len(all_200)} `universe=200` rows, {len(completed_200)} with `total_s`, max recorded universe {metric(max_universe, 0)}.
- **DERIVED from LOGGED:** completed 200-symbol `total_s` and `yf_fallback` distributions; `persist_s` distribution on {len(persist_values)} rows; stage-event distributions in separately classified cohorts.
- **LOGGED, Sep 22:** selected source lines {','.join(map(str, sep22_lines)) if sep22_lines else 'none'}; first cold run excluded as documented.
- **MEASURED in this audit:** no live scanner performance value. The only new runtime action was offline parsing and artifact generation.

## 14. What We Could Not Measure

Full-universe wall-clock duration and stage shares; end-to-end request duration; cold-versus-hot delta; market-session effect; provider-only network time; CPU/GIL and disk-I/O contributions; lock/serialization totals; complete retry/backoff behavior; full-run persistence split; and linear/nonlinear scaling. Missing quantities remain UNKNOWN, not estimated.

## 15. What the Measurement Contradicts

- The Oct 17 decision-log receipt records 411 completed 200-symbol batches; this source snapshot contains {len(completed_200)}. The five-row difference is not reconciled here; this report uses the pinned current snapshot and does not rewrite that receipt.
- The Sep 21 audit report's zero-stage-event claim was accurate for its dated snapshot, but is stale for the current JSONL, which contains {len(timed)} stage-timed records. Likewise, `persist_s` is now present in {len(persist_values)} completed 200-symbol rows, though it remains incomplete for end-to-end timing.
- **CORE-005 metric conflict:** the Sep 22 decision log computes {metric(repair_mean, 3)} s as the sum of five repair values divided by five (the mean); the Sep 23 note labels {metric(repair_mean, 3)} s a median and calls {metric(mean_over_median)}% a ratio of medians. Raw rows instead give median repair {metric(repair_median, 3)} s, median total {metric(campaign_total_median, 3)} s, ratio-of-medians {metric(repair_ratio_of_medians)}%, and median paired run share {metric(repair_share_median)}%. Historical documents are left untouched; these definitions remain visibly distinguished.
- **FAZ 1:** the Sep 21 stage rows are not a valid production baseline because Alpaca completely failed; the Sep 22 five-run cohort is 200-symbol stage evidence only and does not complete the full-universe measurement.
- **CORE-005 phase-status conflict:** the Sep 21 acceleration plan labels FAZ 2R pending, while the Sep 22 decision-log entry says FAZ 2R.3 closed. This audit does not choose between them. The Oct 17 receipt says the FAZ 3 live A/B was not run and FAZ 4 had not started.
- The Sep 21 timed rows have `alpaca_total_failure=true` and are not evidence for the production Alpaca path. They remain separate from the Sep 22 API cohort.

## 16. Single Next Step

After an operator-approved measurement window is available, run one same-path full-universe campaign with at least five repeated runs, an explicitly recorded cache/session state, `FINPILOT_SCAN_STAGE_TIMING` enabled by the operator, and an outer wall timer spanning the complete batch chain through persistence and response. This audit did not enable the flag or run that campaign.

## 17. Proposed Governance Action

**None applied.** This Level A offline audit changes no scanner behavior, provider selection, signal, flag, cache, database, scheduler, API, or publication state. The two historical documentation conflicts above are reported but not edited; no performance optimization is proposed without a full-universe measurement.

## Reproducibility

- Source: `data/distribution/scan_timing.jsonl`
- Source SHA-256: `{snapshot['sha256']}`
- Source file modified UTC: `{snapshot['mtime_utc']}`
- Analyzer: `research/scan_performance_audit_{ARTIFACT_DATE.replace('-', '_')}.py`
- Generated UTC: `{now}`
- Percentile method: `statistics.quantiles(..., method="inclusive")`
- Output CSVs: `{STAGE_PATH.relative_to(ROOT).as_posix()}`, `{VARIANCE_PATH.relative_to(ROOT).as_posix()}`, `{GAPS_PATH.relative_to(ROOT).as_posix()}`
- Stage cohort source lines: Sep 21 {','.join(map(str, sep21_lines)) if sep21_lines else 'none'}; Sep 22 selected {','.join(map(str, sep22_lines)) if sep22_lines else 'none'}.
"""


def main() -> int:
    rows, snapshot = load_snapshot()
    all_200 = [row for row in rows if is_universe_200(row)]
    completed_200 = [row for row in all_200 if is_completed(row)]
    persisted_200 = [
        row for row in completed_200 if as_number(row.get("persist_s")) is not None
    ]
    sep21_failure, sep22_candidates, sep22_selected = campaign_rows(rows)

    stage_rows = build_stage_rows(
        completed_200,
        persisted_200,
        sep21_failure,
        sep22_selected,
    )
    variance_rows = build_variance_rows(
        rows,
        sep21_failure,
        sep22_candidates,
        sep22_selected,
    )
    universes = [as_number(row.get("universe")) for row in rows]
    max_universe = max((value for value in universes if value is not None), default=None)
    gap_rows = build_gap_rows(max_universe, len(all_200), len(completed_200))

    REPORTS.mkdir(parents=True, exist_ok=True)
    write_csv(STAGE_PATH, list(stage_rows[0]), stage_rows)
    write_csv(
        VARIANCE_PATH,
        list(variance_rows[0]) if variance_rows else ["source_line"],
        variance_rows,
    )
    write_csv(GAPS_PATH, list(gap_rows[0]), gap_rows)
    report = build_report(
        rows,
        snapshot,
        completed_200,
        persisted_200,
        stage_rows,
        sep21_failure,
        sep22_candidates,
        sep22_selected,
    )
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(
        json.dumps(
            {
                "source_sha256": snapshot["sha256"],
                "source_records": len(rows),
                "parse_errors": len(snapshot["parse_error_lines"]),
                "universe_200_rows": len(all_200),
                "completed_200_rows": len(completed_200),
                "persist_s_completed_200_rows": len(persisted_200),
                "stage_timed_rows": sum(is_timed(row) for row in rows),
                "sep21_alpaca_failure_stage_rows": len(sep21_failure),
                "sep22_candidates": len(sep22_candidates),
                "sep22_selected_runs": len(sep22_selected),
                "stage_csv_rows": len(stage_rows),
                "variance_csv_rows": len(variance_rows),
                "gap_csv_rows": len(gap_rows),
                "primary_status": "NOT MEASURED",
                "outputs": [
                    str(REPORT_PATH.relative_to(ROOT)),
                    str(STAGE_PATH.relative_to(ROOT)),
                    str(VARIANCE_PATH.relative_to(ROOT)),
                    str(GAPS_PATH.relative_to(ROOT)),
                ],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())