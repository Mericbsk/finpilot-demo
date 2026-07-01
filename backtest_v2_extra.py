"""Guncel veri forward-test (watchlist_signals) + yeni kombinasyon aramasi."""

import itertools
import json
import os
import sqlite3
from math import erf, sqrt

import numpy as np

DB = "/sessions/stoic-practical-tesla/mnt/Borsa/data/finpilot.db"
OUT = "/sessions/stoic-practical-tesla/mnt/Borsa/data/backtest_out"
os.makedirs(OUT, exist_ok=True)


def ncdf(x):
    return 0.5 * (1 + erf(x / sqrt(2)))


def zp(sa, na, sb, nb):
    if na == 0 or nb == 0:
        return None
    p1, p2 = sa / na, sb / nb
    pp = (sa + sb) / (na + nb)
    se = (pp * (1 - pp) * (1 / na + 1 / nb)) ** 0.5
    if se == 0:
        return 1.0
    return 2 * (1 - ncdf(abs((p1 - p2) / se)))


c = sqlite3.connect(DB)

# ---------- ARCHIVE (precise resolved_pct_t5) ----------
arch = []
for sc, pj, rp, rp5, ts in c.execute(
    "select score,payload_json,resolved_pct,resolved_pct_t5,ts from signals_archive"
):
    if rp5 is None and rp is None:
        continue
    try:
        d = json.loads(pj)
    except:
        d = {}
    e = d.get("entry_price")
    s = d.get("stop_loss")
    rr = d.get("risk_reward")
    rg = str(d.get("regime"))
    if e is not None and e < 1:
        continue
    sd = abs(e - s) / e * 100 if (e and s and e > 0) else None
    reg = 1 if rg in ("True", "1", "Trend") else (0 if rg in ("False", "0", "Range") else None)
    y = 1 if (rp5 is not None and rp5 >= 5) else 0
    arch.append(dict(score=sc, rr=rr, sd=sd, reg=reg, y=y, ts=ts))
A = arch
ybase = np.mean([r["y"] for r in A])

# ---------- WATCHLIST (newest cohort, win/loss) ----------
wl = []
for sym, e, s, tp, sc, rr, rg, stat, sd_ in c.execute(
    "select symbol,entry_price,stop_loss,take_profit,score,risk_reward,regime,status_lifecycle,signal_date from watchlist_signals"
):
    if stat not in ("resolved_win", "resolved_loss"):
        continue
    sd = abs(e - s) / e * 100 if (e and s and e > 0) else None
    tpd = (tp - e) / e * 100 if (e and tp and e > 0) else None
    reg = (
        1
        if str(rg) in ("True", "1", "Trend")
        else (0 if str(rg) in ("False", "0", "Range") else None)
    )
    win = 1 if stat == "resolved_win" else 0
    cap5 = 1 if (win and tpd is not None and tpd >= 5) else 0
    wl.append(dict(score=sc, rr=rr, sd=sd, reg=reg, win=win, cap5=cap5, tpd=tpd, date=sd_))
W = wl
winbase = np.mean([r["win"] for r in W])
cap5base = np.mean([r["cap5"] for r in W])

# ---------- filter library ----------
F = {
    "score>=3": lambda r: r["score"] is not None and r["score"] >= 3,
    "rr>=2.6": lambda r: r["rr"] is not None and r["rr"] >= 2.6,
    "rr>=3.0": lambda r: r["rr"] is not None and r["rr"] >= 3.0,
    "stop_dist 2-5%": lambda r: r["sd"] is not None and 2 <= r["sd"] < 5,
    "stop_dist>=2%": lambda r: r["sd"] is not None and r["sd"] >= 2,
    "stop_dist>=5%": lambda r: r["sd"] is not None and r["sd"] >= 5,
    "regime=Range": lambda r: r["reg"] == 0,
}


def metr(recs, fl, ykey, base):
    sub = [r for r in recs if fl(r)]
    if not sub:
        return None
    n = len(sub)
    h = np.mean([r[ykey] for r in sub])
    ctrl = [r for r in recs if not fl(r)]
    p = (
        zp(int(sum(r[ykey] for r in sub)), n, int(sum(r[ykey] for r in ctrl)), len(ctrl))
        if ctrl
        else None
    )
    return dict(
        n=n, hit=round(float(h), 4), lift=round(float(h / base), 3) if base > 0 else None, p=p
    )


# ===== 1) WATCHLIST forward-test of derived single rules =====
print("########## GUNCEL FORWARD-TEST (watchlist 12May-30Haz 2026) ##########")
print(f"N_resolved={len(W)}  base win-rate={winbase:.3f}  base 5%-capture={cap5base:.3f}")
print(f"{'kural':18s}{'n':>5}{'win%':>7}{'wLift':>7}{'cap5%':>7}{'c5Lift':>7}{'win_p':>8}")
wl_rows = []
for name, fl in F.items():
    mw = metr(W, fl, "win", winbase)
    mc = metr(W, fl, "cap5", cap5base)
    if mw:
        print(
            f"{name:18s}{mw['n']:>5}{mw['hit']*100:>7.1f}{(mw['lift'] or 0):>7.2f}{(mc['hit']*100 if mc else 0):>7.1f}{(mc['lift'] if mc else 0) or 0:>7.2f}{(mw['p'] if mw['p'] is not None else 0):>8.3f}"
        )
        wl_rows.append(
            dict(
                rule=name,
                **{f"win_{k}": v for k, v in mw.items()},
                cap5_hit=mc["hit"] if mc else None,
                cap5_lift=mc["lift"] if mc else None,
            )
        )

# ===== 2) NEW COMBINATIONS on archive (pairwise) =====
print("\n########## YENI KOMBINASYONLAR (arsiv, Y_5pct_5d, baz=%.3f) ##########" % ybase)
combo_rows = []
keys = list(F.keys())
# singles + all pairs
cands = [(k,) for k in keys] + list(itertools.combinations(keys, 2))
for combo in cands:
    fl = lambda r, cs=combo: all(F[k](r) for k in cs)
    m = metr(A, fl, "y", ybase)
    if m and m["n"] >= 50:
        combo_rows.append(dict(combo=" + ".join(combo), **m))
combo_rows.sort(key=lambda x: -(x["lift"] or 0))
print(f"{'kombinasyon':40s}{'n':>6}{'hit%':>7}{'lift':>6}{'p':>9}")
for r in combo_rows[:14]:
    print(f"{r['combo']:40s}{r['n']:>6}{r['hit']*100:>7.1f}{r['lift']:>6.2f}{(r['p'] or 0):>9.4f}")

# ===== 3) REGIME-AWARE composite (best 2-var, applied per regime) =====
print("\n########## REJIM-FARKINDA KURAL ##########")


# In Range regime: use volatility band; in Trend: require high rr
def rule_regime_aware(r):
    if r["reg"] == 0:  # Range -> volatility band
        return r["sd"] is not None and r["sd"] >= 2
    else:  # Trend/other -> need high rr
        return r["rr"] is not None and r["rr"] >= 3.0


m = metr(A, rule_regime_aware, "y", ybase)
print("Range->vol(sd>=2%), else->rr>=3.0 :", m)
# vs simple best
best_simple = combo_rows[0]
print(
    "En iyi sabit kombinasyon:",
    best_simple["combo"],
    best_simple["n"],
    f"hit={best_simple['hit']*100:.1f}% lift={best_simple['lift']}",
)

json.dump(
    dict(
        archive_base=round(float(ybase), 4),
        watchlist_winbase=round(float(winbase), 4),
        watchlist_cap5base=round(float(cap5base), 4),
        n_watchlist=len(W),
        watchlist_rules=wl_rows,
        new_combos=combo_rows[:14],
        regime_aware=m,
        best_combo=best_simple,
    ),
    open(f"{OUT}/backtest_v2_results.json", "w"),
    indent=2,
    default=str,
)
print("\nSAVED", f"{OUT}/backtest_v2_results.json")
