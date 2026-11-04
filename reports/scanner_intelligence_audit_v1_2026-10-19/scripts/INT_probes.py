# INT_probes.py - R9 (INT) descriptive interaction probes on signals_archive. ASCII only.
# Read-only DB. Outcomes are loaded ONLY for rows with payload signal_date < CUTOFF.
import collections
import csv
import datetime
import json
import os
import re
import sqlite3
import sys

import numpy as np

try:
    sys.stdout.reconfigure(encoding="ascii", errors="backslashreplace")
except Exception:
    pass

AUD = r"C:\Users\meric\Borsa\reports\scanner_intelligence_audit_v1_2026-10-19"
DB_URI = "file:C:/Users/meric/Borsa/data/finpilot.db?mode=ro"
CUTOFF = "2026-08-01"
SEED = 20261019
B = 2000
DECIDED = ("resolved_win", "resolved_loss", "expired_win", "expired_loss")
N_CELLS = 0
N_CONTRASTS = 0
CSV_ROWS = []


def out(*a):
    print(*a, flush=True)


def day(s):
    m = re.match(r"(\d{4}-\d{2}-\d{2})", str(s or ""))
    return m.group(1) if m else None


def fnum(v):
    try:
        x = float(v)
        return x if np.isfinite(x) else None
    except (TypeError, ValueError):
        return None


def scale(v):
    x = fnum(v)
    if x is None:
        return "null_or_nonnum"
    if x in (0.0, 1.0, 2.0, 3.0):
        return "int0_3"
    if 0.0 < x < 1.0:
        return "frac0_1"
    if x > 3.0:
        return "gt3"
    return "other"


def bull_of(v):
    s = str(v).strip().lower()
    if s in ("true", "bull", "1"):
        return 1
    if s in ("false", "bear", "0"):
        return 0
    return None


con = sqlite3.connect(DB_URI, uri=True)
con.execute("PRAGMA query_only=ON")
meta_rows = con.execute("SELECT id, symbol, ts, score, payload_json FROM signals_archive").fetchall()
lab_rows = con.execute(
    "SELECT id, resolved_status_barrier, resolved_pct_barrier FROM signals_archive "
    "WHERE substr(json_extract(payload_json, '$.signal_date'), 1, 10) < ?", (CUTOFF,)).fetchall()
post = con.execute(
    "SELECT COUNT(*), SUM(resolved_pct_barrier IS NOT NULL) FROM signals_archive "
    "WHERE NOT (substr(json_extract(payload_json, '$.signal_date'), 1, 10) < ?)", (CUTOFF,)).fetchone()
con.close()

recs = {}
daycount = collections.Counter()
for rid, sym, ts, tscore, pj in meta_rows:
    d = json.loads(pj) if pj else {}
    sd, td = day(d.get("signal_date")), day(ts)
    if sd and td:
        lag = (datetime.date.fromisoformat(td) - datetime.date.fromisoformat(sd)).days
        grp = "same" if lag == 0 else ("late" if lag > 0 else "early")
    else:
        lag, grp = None, "unknown"
    rr = fnum(d.get("risk_reward"))
    comp = sum([bool(rr and rr > 0), bool(str(d.get("explanation") or "").strip()),
                bool(str(d.get("reason") or "").strip()), fnum(d.get("sentiment")) is not None])
    recs[rid] = dict(sd=sd, lag=lag, grp=grp, tod=(str(ts)[11:16] if ts else "?"), tscore=fnum(tscore),
                     pscore=fnum(d.get("score")), tscale=scale(tscore), pscale=scale(d.get("score")),
                     bull=bull_of(d.get("regime")), regime_raw=str(d.get("regime")),
                     price=fnum(d.get("entry_price")), tp=fnum(d.get("take_profit")), sl=fnum(d.get("stop_loss")),
                     comp=comp, src=str(d.get("source") or d.get("source_model") or "?"),
                     signal=str(d.get("signal")), has_entry_ok=("entry_ok" in d))
    if sd:
        daycount[sd] += 1

out("#### METADATA (all rows; no outcomes)")
out("rows", len(recs), "groups", dict(collections.Counter(r["grp"] for r in recs.values())))
lb = collections.Counter()
for r in recs.values():
    L = r["lag"]
    lb["none" if L is None else "<0" if L < 0 else "0" if L == 0 else "1-3" if L <= 3 else "4-7" if L <= 7
       else "8-14" if L <= 14 else "15-29" if L <= 29 else "30+"] += 1
out("lag_days(ts_date - signal_date):", dict(lb))
pre = sum(1 for r in recs.values() if r["sd"] and r["sd"] < CUTOFF)
out("signal_date < %s: %d rows; >= cutoff: %d rows (labels present, count only: %s)" % (CUTOFF, pre, post[0], post[1]))
coh = collections.Counter()
for r in recs.values():
    t = r["tod"] if r["tod"] in ("09:00", "21:45") else "other"
    coh[(t, r["grp"], r["has_entry_ok"])] += 1
out("cohort (ts HH:MM, group, has_entry_ok):", sorted(coh.items()))
out("table score scale:", dict(collections.Counter(r["tscale"] for r in recs.values())))
out("payload score scale:", dict(collections.Counter(r["pscale"] for r in recs.values())))
eq = collections.Counter()
for r in recs.values():
    if r["tscore"] is None or r["pscore"] is None:
        eq["one_missing"] += 1
    else:
        eq["equal" if abs(r["tscore"] - r["pscore"]) < 1e-9 else "different"] += 1
out("table vs payload score:", dict(eq))
for sc in ("int0_3", "frac0_1", "gt3"):
    ds = sorted(r["sd"] for r in recs.values() if r["tscale"] == sc and r["sd"])
    tv = collections.Counter(r["tscore"] for r in recs.values() if r["tscale"] == sc)
    out("table scale %s: n=%d signal_date %s..%s top values %s" % (
        sc, len(ds), ds[0] if ds else None, ds[-1] if ds else None, tv.most_common(8)))
out("table scale x group:", sorted(collections.Counter((r["tscale"], r["grp"]) for r in recs.values()).items()))
out("regime raw:", dict(collections.Counter(r["regime_raw"] for r in recs.values())))
out("signal:", dict(collections.Counter(r["signal"] for r in recs.values())))
out("source:", dict(collections.Counter(r["src"] for r in recs.values())))
out("completeness count:", dict(collections.Counter(r["comp"] for r in recs.values())))
dc = np.array([daycount[k] for k in sorted(daycount) if k < CUTOFF], dtype=float)
q1, q2 = np.quantile(dc, [1 / 3, 2 / 3])
out("pre-cutoff signal days:", len(dc), "rows/day min/median/max", dc.min(), np.median(dc), dc.max(),
    "tercile cuts", q1, q2)

lab = {}
for rid, st, pct in lab_rows:
    if st in DECIDED and pct is not None:
        lab[rid] = (float(pct), 1.0 if st.endswith("_win") else 0.0)
out("#### OUTCOME PROBES (gross resolved_pct_barrier, %; signal_date < cutoff; decided rows)")
out("decided rows by group:", dict(collections.Counter(recs[k]["grp"] for k in lab)))


def boot(dlist, cells, ys, ws, ncell, seedkey):
    days, dinv = np.unique(np.array(dlist), return_inverse=True)
    D = len(days)
    c = np.array(cells)
    S = np.zeros((D, ncell)); N = np.zeros((D, ncell)); W = np.zeros((D, ncell))
    np.add.at(S, (dinv, c), np.array(ys))
    np.add.at(N, (dinv, c), 1.0)
    np.add.at(W, (dinv, c), np.array(ws))
    rng = np.random.default_rng([SEED] + list(seedkey))
    rm = np.full((B, ncell), np.nan); rw = np.full((B, ncell), np.nan)
    with np.errstate(invalid="ignore", divide="ignore"):
        for b in range(B):
            w = np.bincount(rng.integers(0, D, D), minlength=D).astype(float)
            nb = w @ N
            rm[b] = (w @ S) / nb
            rw[b] = (w @ W) / nb
        n = N.sum(0)
        return n, (N > 0).sum(0), S.sum(0) / n, W.sum(0) / n, rm, rw


def ci(a):
    a = a[np.isfinite(a)]
    if len(a) < 50:
        return (float("nan"), float("nan"))
    lo, hi = np.percentile(a, [2.5, 97.5])
    return (float(lo), float(hi))


def run_probe(pno, name, cell_fn, labels, contrasts, groups=("same", "late"), group_fn=None):
    global N_CELLS, N_CONTRASTS
    for gno, g in enumerate(groups):
        dl, cl, yl, wl, tpl, sll = [], [], [], [], [], []
        for rid, (y, w) in lab.items():
            r = recs[rid]
            if group_fn is None and r["grp"] != g:
                continue
            c = cell_fn(r) if group_fn is None else group_fn(r)
            if c is None:
                continue
            dl.append(r["sd"]); cl.append(c); yl.append(y); wl.append(w)
            ok = r["price"] and r["price"] > 0
            tpl.append((r["tp"] / r["price"] - 1) * 100 if ok and r["tp"] else np.nan)
            sll.append((r["sl"] / r["price"] - 1) * 100 if ok and r["sl"] else np.nan)
        if not dl:
            out("%s [%s]: no rows" % (name, g)); continue
        nc = len(labels)
        n, nd, m, wr, rm, rw = boot(dl, cl, yl, wl, nc, (pno, gno))
        ca, ya, ta, sa = np.array(cl), np.array(yl), np.array(tpl), np.array(sll)
        out("-- %s [%s] days=%d" % (name, g if group_fn is None else "all", len(set(dl))))
        for k in range(nc):
            N_CELLS += 1
            sel = ca == k
            med = float(np.median(ya[sel])) if sel.any() else float("nan")
            tpm = float(np.nanmedian(ta[sel])) if sel.any() else float("nan")
            slm = float(np.nanmedian(sa[sel])) if sel.any() else float("nan")
            mc, wc = ci(rm[:, k]), ci(rw[:, k])
            out("  cell %-16s n=%5d days=%3d mean=%7.3f CI[%7.3f,%7.3f] win=%.3f CI[%.3f,%.3f] median=%7.3f tp_med=%6.2f sl_med=%6.2f" % (
                labels[k], n[k], nd[k], m[k], mc[0], mc[1], wr[k], wc[0], wc[1], med, tpm, slm))
            CSV_ROWS.append([name, g if group_fn is None else "all", labels[k], int(n[k]), int(nd[k]),
                             round(float(m[k]), 4), round(mc[0], 4), round(mc[1], 4), round(float(wr[k]), 4),
                             round(wc[0], 4), round(wc[1], 4), round(med, 4), round(tpm, 3), round(slm, 3)])
        for cname, fn in contrasts:
            N_CONTRASTS += 1
            pt = fn(m); pw = fn(wr)
            dm, dw = fn(rm.T), fn(rw.T)
            out("  contrast %-26s mean_diff=%7.3f CI[%7.3f,%7.3f] win_diff=%.3f CI[%.3f,%.3f] nan_frac=%.3f" % (
                cname, pt, *ci(dm), pw, *ci(dw), float(np.mean(~np.isfinite(dm)))))
            CSV_ROWS.append([name, g if group_fn is None else "all", "contrast:" + cname, "", "", round(float(pt), 4),
                             round(ci(dm)[0], 4), round(ci(dm)[1], 4), round(float(pw), 4), round(ci(dw)[0], 4),
                             round(ci(dw)[1], 4), "", "", ""])
        if group_fn is not None:
            break


run_probe(0, "P0_archive_timing", None, ["same", "late"], [("late_minus_same", lambda a: a[1] - a[0])],
          groups=("all",), group_fn=lambda r: {"same": 0, "late": 1}.get(r["grp"]))
run_probe(4, "P4_same_day_count", lambda r: 0 if daycount[r["sd"]] <= q1 else (1 if daycount[r["sd"]] <= q2 else 2),
          ["tercile_low", "tercile_mid", "tercile_high"], [("high_minus_low", lambda a: a[2] - a[0])])
run_probe(5, "P5_price_lt5", lambda r: None if not r["price"] or r["price"] <= 0 else (1 if r["price"] < 5 else 0),
          ["price_ge5", "price_lt5"], [("lt5_minus_ge5", lambda a: a[1] - a[0])])
run_probe(6, "P6_completeness", lambda r: 1 if r["comp"] >= 2 else 0,
          ["comp_le1", "comp_ge2"], [("ge2_minus_le1", lambda a: a[1] - a[0])])
run_probe(7, "P7_score_x_regime",
          lambda r: None if r["pscale"] != "int0_3" or r["bull"] is None else int(r["pscore"] >= 2) * 2 + r["bull"],
          ["lowscore_bear", "lowscore_bull", "highscore_bear", "highscore_bull"],
          [("hi_minus_lo_in_bull", lambda a: a[3] - a[1]), ("hi_minus_lo_in_bear", lambda a: a[2] - a[0]),
           ("interaction", lambda a: (a[3] - a[1]) - (a[2] - a[0]))])
out("MULTIPLE_TESTING cells=%d contrasts=%d (95%% CIs, no adjustment; expected ~%.1f contrast CIs excluding 0 by chance)" % (
    N_CELLS, N_CONTRASTS, 0.05 * N_CONTRASTS))
with open(os.path.join(AUD, "data", "INT_probe_cells.csv"), "w", newline="", encoding="ascii") as f:
    wtr = csv.writer(f)
    wtr.writerow(["probe", "group", "cell", "n", "days", "mean_pct", "mean_lo", "mean_hi", "win", "win_lo", "win_hi",
                  "median_pct", "tp_med_pct", "sl_med_pct"])
    wtr.writerows(CSV_ROWS)
out("DONE_INT_PROBES")
