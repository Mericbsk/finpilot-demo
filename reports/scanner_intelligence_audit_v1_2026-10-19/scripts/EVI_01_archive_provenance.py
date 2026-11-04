# EVI_01: read-only provenance checks for signals_archive and related inputs.
# Writes only reports/scanner_intelligence_audit_v1_2026-10-19/data/EVI_01_archive_provenance.json
import collections
import csv
import datetime
import hashlib
import json
import math
import os
import sqlite3
import statistics

ROOT = r"C:\Users\meric\Borsa"
AUDIT = os.path.join(ROOT, "reports", "scanner_intelligence_audit_v1_2026-10-19")
OUT = os.path.join(AUDIT, "data", "EVI_01_archive_provenance.json")
DB = os.path.join(ROOT, "data", "finpilot.db")

HASH_FILES = [
    "data/finpilot.db",
    "data/signals_archive_recovered_20260703.csv",
    "web/public/stock_presets.json",
    "distribution/karne.py",
    "distribution/archive_bridge.py",
    "scripts/resolve_open_signals.py",
    "scripts/migrate_signal_archive_to_sqlite.py",
    "data/backtest_out/fundamentals_sentiment_protocol.json",
    "data/backtest_out/fundamentals_sentiment_holdout.json",
]


def sha256_file(rel):
    p = os.path.join(ROOT, rel)
    if not os.path.exists(p):
        return {"path": rel, "exists": False}
    h = hashlib.sha256()
    try:
        with open(p, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        st = os.stat(p)
        return {
            "path": rel,
            "exists": True,
            "sha256": h.hexdigest(),
            "bytes": st.st_size,
            "mtime_local": datetime.datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds"),
        }
    except Exception as exc:  # locked or unreadable
        return {"path": rel, "exists": True, "sha256": None, "error": type(exc).__name__}


def fnum(x):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


def stats(vals):
    vals = [v for v in vals if v is not None]
    if not vals:
        return {"n": 0}
    return {
        "n": len(vals),
        "mean": round(statistics.fmean(vals), 6),
        "median": round(statistics.median(vals), 6),
        "min": round(min(vals), 6),
        "max": round(max(vals), 6),
    }


def main():
    res = {"generated_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")}
    res["hashes"] = [sha256_file(r) for r in HASH_FILES]
    res["db_sidecars"] = {s: os.path.exists(DB + s) for s in ("-wal", "-shm", "-journal")}

    con = sqlite3.connect("file:" + DB.replace("\\", "/") + "?mode=ro", uri=True)
    con.execute("PRAGMA query_only=ON")
    tables = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
    counts = {}
    for t in tables:
        try:
            counts[t] = con.execute('SELECT COUNT(*) FROM "%s"' % t.replace('"', '""')).fetchone()[0]
        except sqlite3.Error as exc:
            counts[t] = "ERROR:" + type(exc).__name__
    res["db_tables"] = counts
    res["signals_archive_columns"] = [r[1] for r in con.execute("PRAGMA table_info(signals_archive)")]

    rows = con.execute(
        "SELECT id, symbol, ts, score, finpilot_score, payload_json, resolved_status, resolved_pct, "
        "resolved_pct_t5, resolved_pct_barrier, resolved_status_barrier FROM signals_archive"
    ).fetchall()
    con.close()

    sa = {"n_total": len(rows)}
    sa["resolved_status_counts"] = dict(collections.Counter(str(r[6]) for r in rows))
    sa["resolved_status_barrier_counts"] = dict(collections.Counter(str(r[10]) for r in rows))
    all_dates = sorted(str(r[2])[:10] for r in rows if r[2])
    sa["ts_date_range_all"] = [all_dates[0], all_dates[-1]] if all_dates else None

    decided = []
    for r in rows:
        if r[10] in ("resolved_win", "resolved_loss") and fnum(r[9]) is not None:
            decided.append(r)
    sa["n_decided"] = len(decided)
    dd = sorted(str(r[2])[:10] for r in decided)
    sa["ts_date_range_decided"] = [dd[0], dd[-1]] if dd else None

    # provenance of decided rows
    src_counter = collections.Counter()
    month_counter = collections.Counter()
    weekday_counter = collections.Counter()
    tod_counter = collections.Counter()
    month_tod = collections.defaultdict(collections.Counter)
    ts_format = collections.Counter()
    sigdate_vs_ts = collections.Counter()
    key_counter = collections.Counter()
    barrier_formula_ok = 0
    barrier_formula_checked = 0
    status_agree = 0
    pct_equal = 0
    pct_null = 0
    for r in decided:
        ts = str(r[2])
        d = ts[:10]
        month_counter[d[:7]] += 1
        try:
            weekday_counter[datetime.date.fromisoformat(d).strftime("%a")] += 1
        except ValueError:
            weekday_counter["unparsed"] += 1
        tod = ts[11:16] if len(ts) >= 16 else "date_only"
        tod_counter[tod] += 1
        bucket = tod if tod in ("09:00", "21:45", "date_only") else "other"
        month_tod[d[:7]][bucket] += 1
        ts_format["has_T" if "T" in ts else ("space" if " " in ts else "date_only")] += 1
        try:
            p = json.loads(r[5]) if r[5] else {}
        except Exception:
            p = {}
        src_counter[str(p.get("source"))] += 1
        for k in p.keys():
            key_counter[k] += 1
        sd = str(p.get("signal_date") or "")[:10]
        if not sd:
            sigdate_vs_ts["payload_signal_date_missing"] += 1
        elif sd == d:
            sigdate_vs_ts["equal"] += 1
        else:
            sigdate_vs_ts["different"] += 1
        e, tp, sl = fnum(p.get("entry_price")), fnum(p.get("take_profit")), fnum(p.get("stop_loss"))
        v = fnum(r[9])
        if e and e > 0:
            ref = (tp / e - 1) * 100 if r[10] == "resolved_win" and tp else ((sl / e - 1) * 100 if sl else None)
            if ref is not None:
                barrier_formula_checked += 1
                if abs(ref - v) <= 0.05:
                    barrier_formula_ok += 1
        if str(r[6]) == str(r[10]):
            status_agree += 1
        rp = fnum(r[7])
        if rp is None:
            pct_null += 1
        elif abs(rp - v) < 1e-9:
            pct_equal += 1
    sa["decided_payload_source_counts"] = dict(src_counter)
    sa["decided_month_counts"] = dict(sorted(month_counter.items()))
    sa["decided_weekday_counts"] = dict(weekday_counter)
    sa["decided_time_of_day_top10"] = tod_counter.most_common(10)
    sa["decided_month_by_tod_bucket"] = {k: dict(v) for k, v in sorted(month_tod.items())}
    sa["decided_ts_format"] = dict(ts_format)
    sa["decided_payload_signal_date_vs_ts_date"] = dict(sigdate_vs_ts)
    sa["decided_payload_keys_top40"] = key_counter.most_common(40)
    sa["decided_barrier_formula_check"] = {"checked": barrier_formula_checked, "within_0p05pp": barrier_formula_ok}
    sa["decided_resolved_status_equals_barrier_status"] = status_agree
    sa["decided_resolved_pct_equals_barrier_pct"] = pct_equal
    sa["decided_resolved_pct_null"] = pct_null

    # provenance reproduction of headline figures (gross stored labels; not an expectancy)
    vals = [fnum(r[9]) for r in decided]
    wins = [fnum(r[9]) for r in decided if r[10] == "resolved_win"]
    losses = [fnum(r[9]) for r in decided if r[10] == "resolved_loss"]
    head = stats(vals)
    head["hit_rate"] = round(len(wins) / len(vals), 6) if vals else None
    head["avg_win"] = round(statistics.fmean(wins), 6) if wins else None
    head["avg_loss"] = round(statistics.fmean(losses), 6) if losses else None
    head["sum_pp"] = round(sum(vals), 4)
    sa["headline_resolved_pct_barrier"] = head

    order = sorted(decided, key=lambda r: (-fnum(r[9]), str(r[0])))
    n = len(order)
    out_trim = {}
    for frac, label in ((0.01, "top1"), (0.05, "top5")):
        k = int(math.floor(frac * n))
        cut = fnum(order[k - 1][9])
        ties_at_cut = sum(1 for r in decided if abs(fnum(r[9]) - cut) < 1e-12)
        rest = [fnum(r[9]) for r in order[k:]]
        top = order[:k]
        top_dates = collections.Counter(str(r[2])[:10] for r in top)
        out_trim[label] = {
            "k_removed": k,
            "cut_value": cut,
            "rows_equal_to_cut_value": ties_at_cut,
            "remaining": stats(rest),
            "removed_all_wins": all(r[10] == "resolved_win" for r in top),
            "removed_top_dates": top_dates.most_common(5),
        }
    sa["trimmed"] = out_trim

    two = {"2026-03-01", "2026-03-03"}
    sa["two_dates_rows"] = sum(1 for r in decided if str(r[2])[:10] in two)

    # alternative return fields on the same decided rows (definitional sensitivity only)
    sa["alt_field_resolved_pct_on_decided"] = stats([fnum(r[7]) for r in decided])
    sa["alt_field_resolved_pct_t5_on_decided"] = stats([fnum(r[8]) for r in decided])
    sa["alt_field_resolved_pct_t5_all_nonnull"] = stats([fnum(r[8]) for r in rows])

    sym_dec = set(str(r[1]).upper() for r in decided)
    sa["decided_distinct_symbols"] = len(sym_dec)
    symday = collections.Counter((str(r[1]).upper(), str(r[2])[:10]) for r in decided)
    sa["decided_distinct_symbol_days"] = len(symday)
    sa["decided_rows_in_duplicated_symbol_days"] = sum(c for c in symday.values() if c > 1)
    allsymday = set((str(r[1]).upper(), str(r[2])[:10]) for r in rows)
    sa["all_distinct_symbol_days"] = len(allsymday)

    # universe check against the current preset file (current universe, not point-in-time)
    try:
        with open(os.path.join(ROOT, "web", "public", "stock_presets.json"), encoding="utf-8") as f:
            presets = json.load(f)
        uni = set()
        preset_sizes = {}

        def walk(x, acc):
            if isinstance(x, list):
                for it in x:
                    if isinstance(it, str):
                        acc.add(it.strip().upper())
                    else:
                        walk(it, acc)
            elif isinstance(x, dict):
                for v in x.values():
                    walk(v, acc)

        for key, val in presets.items():
            acc = set()
            walk(val, acc)
            preset_sizes[key] = len(acc)
            uni |= acc
        uni = set(s for s in uni if s and s.isascii())
        sa["preset_union_size_including_labels"] = len(uni)
        sa["preset_sizes"] = preset_sizes
        sa["decided_symbols_in_preset_union"] = len(sym_dec & uni)
        sa["decided_rows_symbol_in_preset_union"] = sum(1 for r in decided if str(r[1]).upper() in uni)
    except Exception as exc:
        sa["preset_error"] = type(exc).__name__
    res["signals_archive"] = sa

    # recovered CSV consistency (stored labels only)
    rc = {}
    p = os.path.join(ROOT, "data", "signals_archive_recovered_20260703.csv")
    if os.path.exists(p):
        with open(p, encoding="utf-8", newline="") as f:
            rd = csv.reader(f)
            header = next(rd)
            recs = list(rd)
        rc["header"] = header
        rc["n_rows"] = len(recs)
        idx = {h: i for i, h in enumerate(header)}
        db_by_id = {str(r[0]): r for r in rows}
        overlap = [x for x in recs if x and x[idx.get("id", 0)] in db_by_id]
        rc["ids_also_in_db"] = len(overlap)
        if "ts" in idx:
            tds = sorted(x[idx["ts"]][:10] for x in recs if len(x) > idx["ts"] and x[idx["ts"]])
            rc["ts_date_range"] = [tds[0], tds[-1]] if tds else None
        same_status = same_pct = compared = 0
        if "resolved_status_barrier" in idx and "resolved_pct_barrier" in idx:
            for x in overlap:
                dbr = db_by_id[x[idx["id"]]]
                cs = x[idx["resolved_status_barrier"]]
                if cs in ("resolved_win", "resolved_loss"):
                    compared += 1
                    if cs == dbr[10]:
                        same_status += 1
                    a, b = fnum(x[idx["resolved_pct_barrier"]]), fnum(dbr[9])
                    if a is not None and b is not None and abs(a - b) < 1e-6:
                        same_pct += 1
        rc["decided_in_csv_compared"] = compared
        rc["same_barrier_status_in_db"] = same_status
        rc["same_barrier_pct_in_db"] = same_pct
        rc["csv_barrier_status_counts"] = (
            dict(collections.Counter(x[idx["resolved_status_barrier"]] for x in recs))
            if "resolved_status_barrier" in idx
            else None
        )
    res["recovered_csv"] = rc

    # legacy JSON archive folder (migration source)
    ja = {}
    jdir = os.path.join(ROOT, "data", "signal_archive")
    if os.path.isdir(jdir):
        files = sorted(fn for fn in os.listdir(jdir) if fn.endswith(".json"))
        ja["n_files"] = len(files)
        ja["first_last"] = [files[0], files[-1]] if files else None
        mt = collections.Counter()
        n_rec = 0
        ids = set()
        for fn in files:
            fp = os.path.join(jdir, fn)
            mt[datetime.datetime.fromtimestamp(os.stat(fp).st_mtime).date().isoformat()] += 1
            try:
                with open(fp, encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                continue
            if isinstance(data, list):
                for rec in data:
                    if isinstance(rec, dict):
                        n_rec += 1
                        sid = str(rec.get("id") or "%s_%s" % (rec.get("symbol", "?"), rec.get("signal_date") or fn[:-5]))
                        ids.add(sid)
        ja["mtime_date_counts"] = dict(sorted(mt.items()))
        ja["n_records"] = n_rec
        db_ids = set(str(r[0]) for r in rows)
        dec_ids = set(str(r[0]) for r in decided)
        ja["record_ids_in_db"] = len(ids & db_ids)
        ja["decided_ids_from_json_folder"] = len(ids & dec_ids)
    res["legacy_json_archive"] = ja

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=1, sort_keys=False, default=str)
    print(json.dumps(res, indent=1, default=str)[:20000])


if __name__ == "__main__":
    main()
