"""EVI_03 - read-only re-verification of brief section 2.1 aggregates.

Recomputes only already-published aggregates plus metadata counts; no new outcome splits.
"""
import collections
import datetime
import hashlib
import json
import math
import os
import sqlite3
import statistics

ROOT = r"C:\Users\meric\Borsa"
DB_PATH = os.path.join(ROOT, "data", "finpilot.db")
DB_URI = "file:C:/Users/meric/Borsa/data/finpilot.db?mode=ro"
OUT_PATH = os.path.join(
    ROOT, "reports", "scanner_intelligence_audit_v1_2026-10-19", "data", "EVI_03_verify.json"
)
TWO_TS_DATES = ("2026-03-01", "2026-03-03")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def summary(values):
    return {
        "n": len(values),
        "mean": round(statistics.fmean(values), 6),
        "median": round(statistics.median(values), 6),
    }


def weekday(day):
    try:
        return datetime.date.fromisoformat(day).strftime("%a")
    except ValueError:
        return "NA"


def payload(raw):
    try:
        return json.loads(raw) if raw else {}
    except ValueError:
        return {}


def value_profile(values):
    present = [v for v in values if v is not None]
    counts = collections.Counter(present)
    numeric = [float(v) for v in present if isinstance(v, (int, float)) and math.isfinite(float(v))]
    return {
        "n_null": len(values) - len(present),
        "n_distinct": len(counts),
        "top5_values": [[v, n] for v, n in counts.most_common(5)],
        "rows_sharing_value_globally": sum(n for n in counts.values() if n > 1),
        "share_integer_valued": round(sum(1 for v in numeric if v == int(v)) / len(numeric), 4)
        if numeric
        else None,
        "min": min(numeric) if numeric else None,
        "max": max(numeric) if numeric else None,
    }


def within_day_ties(rows, idx):
    by_day = collections.defaultdict(list)
    for r in rows:
        if r[idx] is not None:
            by_day[str(r[2])[:10]].append(r[idx])
    tied = 0
    total = 0
    for vals in by_day.values():
        counts = collections.Counter(vals)
        total += len(vals)
        tied += sum(n for n in counts.values() if n > 1)
    return {"rows_with_value": total, "rows_tied_within_same_ts_day": tied, "n_ts_days": len(by_day)}


def main():
    st = os.stat(DB_PATH)
    out = {
        "generated_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "db": {
            "sha256": sha256(DB_PATH),
            "bytes": st.st_size,
            "mtime_local": datetime.datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds"),
        },
    }
    con = sqlite3.connect(DB_URI, uri=True)
    con.execute("PRAGMA query_only=ON")
    rows = con.execute(
        "SELECT id, symbol, ts, score, finpilot_score, payload_json, resolved_status, "
        "resolved_pct_barrier, resolved_status_barrier FROM signals_archive"
    ).fetchall()
    con.close()
    out["n_total"] = len(rows)
    out["n_resolved_status_win_loss"] = sum(1 for r in rows if r[6] in ("resolved_win", "resolved_loss"))
    decided = [r for r in rows if r[8] in ("resolved_win", "resolved_loss") and r[7] is not None]
    out["n_decided_barrier"] = len(decided)
    out["full"] = summary([float(r[7]) for r in decided])
    ranked = sorted(decided, key=lambda r: float(r[7]), reverse=True)
    for label, frac in (("top1", 0.01), ("top5", 0.05)):
        k = int(math.floor(frac * len(ranked)))
        out["excluding_" + label] = dict(summary([float(r[7]) for r in ranked[k:]]), k_removed=k)
    top1 = ranked[: int(math.floor(0.01 * len(ranked)))]
    ts_days = collections.Counter(str(r[2])[:10] for r in top1)
    signal_days = collections.Counter(str(payload(r[5]).get("signal_date"))[:10] for r in top1)
    out["top1_ts_dates"] = [[d, n, weekday(d)] for d, n in ts_days.most_common()]
    out["top1_signal_dates"] = [[d, n, weekday(d)] for d, n in signal_days.most_common()]
    out["top1_source_model"] = dict(collections.Counter(str(payload(r[5]).get("source_model")) for r in top1))
    out["top1_rows_on_two_ts_dates"] = sum(1 for r in top1 if str(r[2])[:10] in TWO_TS_DATES)
    out["decided_rows_on_two_ts_dates"] = sum(1 for r in decided if str(r[2])[:10] in TWO_TS_DATES)
    out["share_top1_on_two_ts_dates"] = round(out["top1_rows_on_two_ts_dates"] / len(top1), 4)
    out["share_decided_on_two_ts_dates"] = round(out["decided_rows_on_two_ts_dates"] / len(decided), 4)
    month_model = collections.Counter(
        (str(r[2])[:7], str(payload(r[5]).get("source_model"))) for r in decided
    )
    out["decided_ts_month_x_source_model"] = {a + "|" + b: n for (a, b), n in sorted(month_model.items())}
    out["decided_score_profile"] = value_profile([r[3] for r in decided])
    out["decided_finpilot_score_profile"] = value_profile([r[4] for r in decided])
    out["decided_score_within_day_ties"] = within_day_ties(decided, 3)
    out["decided_finpilot_score_within_day_ties"] = within_day_ties(decided, 4)
    with open(OUT_PATH, "w", encoding="ascii") as f:
        json.dump(out, f, indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
