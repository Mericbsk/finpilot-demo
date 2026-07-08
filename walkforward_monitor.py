#!/usr/bin/env python3
"""
WALK-FORWARD MONITOR — tier precision zaman icinde stabil mi?
============================================================
enriched_signals_v3.csv'yi zaman pencerelerine bolup her pencerede Tier A/B/C
precision + baz orani raporlar. Kalibrasyon/edge KAYMASINI tespit eder.
Tekrar calistirilabilir: veri buyudukce yeniden koş, drift'i izle.
Kullanim:  python walkforward_monitor.py   -> ciktiyi yapistir.
"""

import csv
import os
from collections import defaultdict

ROOT = os.path.dirname(os.path.abspath(__file__))
bd = os.path.join(ROOT, "data", "backtest_out")
CSVP = os.path.join(bd, "enriched_signals_v3.csv")
if not os.path.exists(CSVP):
    CSVP = os.path.join(bd, "enriched_signals_v2.csv")


def ff(x):
    try:
        return float(x)
    except Exception:
        return None


rows = [r for r in csv.DictReader(open(CSVP)) if ff(r.get("resolved_pct_t5")) is not None]


def sh(r):
    s = r.get("short_pit")
    s = ff(s) if s not in (None, "") else ff(r.get("short_pct"))
    return s if s is not None else 0.0


def atr(r):
    return ff(r.get("atr_pct")) or 0


def gap(r):
    return ff(r.get("gap_pct")) or -9


def rvol(r):
    return ff(r.get("rvol")) or 0


def nfac(r):
    return sum([sh(r) >= 15, atr(r) >= 4, gap(r) >= 1, rvol(r) >= 1.5])


def tier(r):
    if sh(r) >= 15 and gap(r) >= 3:
        return "A"
    if (sh(r) >= 15 and atr(r) >= 4) or nfac(r) >= 3:
        return "B"
    if nfac(r) >= 2:
        return "C"
    return ""


for r in rows:
    r["y5"] = 1 if ff(r["resolved_pct_t5"]) >= 5 else 0
    r["_m"] = r["signal_date"][:7]
    r["_t"] = tier(r)
bymon = defaultdict(list)
for r in rows:
    bymon[r["_m"]].append(r)


def P(sub):
    return sum(r["y5"] for r in sub) / len(sub) if sub else 0


print("=== AYLIK TIER PRECISION (>=%5) — drift izleme ===")
print(f"{'ay':>9}{'n':>6}{'baz':>7}{'TierA':>16}{'TierB':>16}{'TierC':>16}")
for m in sorted(bymon):
    rs = bymon[m]

    def cell(t, rs=rs):
        s = [r for r in rs if r["_t"] == t]
        return f"{P(s)*100:.0f}% (n{len(s)})" if len(s) >= 5 else f"- (n{len(s)})"

    print(f"{m:>9}{len(rs):>6}{P(rs)*100:>6.0f}%{cell('A'):>16}{cell('B'):>16}{cell('C'):>16}")
print(
    "\n>>> Tier A/B bir ayda aniden dusuyorsa (ör. <%50) -> edge kaymis olabilir, esikleri yeniden fit et."
)
print("Bu monitoru veri buyudukce periyodik koş (paper trading doneminde haftalik).")
print("Bu ciktinin TAMAMINI Claude'a yapistir.")
