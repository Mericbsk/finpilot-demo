# EVI_02: read-only payload/date/universe provenance details for signals_archive.
# Writes only reports/scanner_intelligence_audit_v1_2026-10-19/data/EVI_02_payload_universe.json
import collections
import datetime
import json
import math
import os
import sqlite3

ROOT = r"C:\Users\meric\Borsa"
OUT = os.path.join(ROOT, "reports", "scanner_intelligence_audit_v1_2026-10-19", "data", "EVI_02_payload_universe.json")
DB = os.path.join(ROOT, "data", "finpilot.db")


def fnum(x):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


def pdate(s):
    try:
        return datetime.date.fromisoformat(str(s)[:10])
    except ValueError:
        return None


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


def main():
    con = sqlite3.connect("file:" + DB.replace("\\", "/") + "?mode=ro", uri=True)
    con.execute("PRAGMA query_only=ON")
    rows = con.execute(
        "SELECT id, symbol, ts, payload_json, resolved_pct_barrier, resolved_status_barrier, resolved_status "
        "FROM signals_archive"
    ).fetchall()
    sym_ex = {str(t).upper(): (e, s) for t, e, s in con.execute("SELECT ticker, exchange, status FROM symbols")}
    lists = collections.Counter(r[0] for r in con.execute("SELECT list_name FROM symbol_lists"))
    wl = con.execute("SELECT MIN(signal_date), MAX(signal_date), COUNT(*) FROM watchlist_signals").fetchone()
    ao = con.execute(
        "SELECT status, COUNT(*), SUM(CASE WHEN filled_at IS NOT NULL THEN 1 ELSE 0 END) FROM alpaca_orders GROUP BY status"
    ).fetchall()
    con.close()

    res = {"generated_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")}
    res["symbol_lists_counts"] = dict(lists)
    res["watchlist_signals_signal_date_min_max_n"] = list(wl)
    res["alpaca_orders_status_n_filled"] = [list(x) for x in ao]

    decided = [r for r in rows if r[5] in ("resolved_win", "resolved_loss") and fnum(r[4]) is not None]
    src_model = collections.Counter()
    signal_val = collections.Counter()
    lifecycle_keys = collections.Counter()
    added_eq_ts = 0
    daydiff = collections.Counter()
    daydiff_by_month = collections.defaultdict(collections.Counter)
    sd_weekday = collections.Counter()
    entry_ok_vals = collections.Counter()
    for r in decided:
        p = json.loads(r[3]) if r[3] else {}
        src_model[str(p.get("source_model"))] += 1
        signal_val[str(p.get("signal"))] += 1
        sl = p.get("status_lifecycle")
        if isinstance(sl, dict):
            for k in sl.keys():
                lifecycle_keys[k] += 1
        if str(p.get("added_at")) == str(r[2]):
            added_eq_ts += 1
        a, b = pdate(r[2]), pdate(p.get("signal_date"))
        if a and b:
            dd = (a - b).days
            daydiff[dd] += 1
            daydiff_by_month[str(r[2])[:7]][dd] += 1
            sd_weekday[b.strftime("%a")] += 1
        if "entry_ok" in p:
            entry_ok_vals[str(p.get("entry_ok"))] += 1
    res["decided_source_model_counts"] = dict(src_model)
    res["decided_signal_field_counts"] = dict(signal_val)
    res["decided_status_lifecycle_keys"] = dict(lifecycle_keys)
    res["decided_added_at_equals_ts"] = added_eq_ts
    res["decided_ts_date_minus_payload_signal_date_days"] = dict(sorted(daydiff.items()))
    res["decided_daydiff_by_ts_month"] = {k: dict(sorted(v.items())) for k, v in sorted(daydiff_by_month.items())}
    res["decided_payload_signal_date_weekday"] = dict(sd_weekday)
    res["decided_entry_ok_values"] = dict(entry_ok_vals)

    # top 1 % rows: ts date vs payload signal_date
    order = sorted(decided, key=lambda r: (-fnum(r[4]), str(r[0])))
    k = int(math.floor(0.01 * len(order)))
    top = order[:k]
    res["top1_k"] = k
    res["top1_ts_dates"] = collections.Counter(str(r[2])[:10] for r in top).most_common()
    res["top1_payload_signal_dates"] = collections.Counter(
        str((json.loads(r[3]) if r[3] else {}).get("signal_date"))[:10] for r in top
    ).most_common()

    # exchange membership (symbols table snapshot; not point-in-time)
    with open(os.path.join(ROOT, "web", "public", "stock_presets.json"), encoding="utf-8") as f:
        presets = json.load(f)
    uni = set()
    walk(presets, uni)
    uni = set(s for s in uni if s and s.isascii())
    pres_tick = set()
    for key, val in presets.items():
        if isinstance(val, dict):
            for kk, vv in val.items():
                if isinstance(vv, list):
                    walk(vv, pres_tick)
        else:
            walk(val, pres_tick)
    res["preset_union_all_strings"] = len(uni)
    res["preset_union_list_values_only"] = len(pres_tick)
    res["preset_exchange_counts"] = dict(collections.Counter(str(sym_ex.get(s, ("NOT_IN_SYMBOLS", None))[0]) for s in pres_tick))
    dsym = set(str(r[1]).upper() for r in decided)
    res["decided_symbol_exchange_counts"] = dict(collections.Counter(str(sym_ex.get(s, ("NOT_IN_SYMBOLS", None))[0]) for s in dsym))
    res["decided_row_exchange_counts"] = dict(
        collections.Counter(str(sym_ex.get(str(r[1]).upper(), ("NOT_IN_SYMBOLS", None))[0]) for r in decided)
    )
    res["decided_symbols_in_preset_list_values"] = len(dsym & pres_tick)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=1, default=str)
    print(json.dumps(res, indent=1, default=str))


if __name__ == "__main__":
    main()
