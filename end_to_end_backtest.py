#!/usr/bin/env python3
"""
UCTAN-UCA URETIM-CONFIG BACKTEST + TAVAN TARAMASI
=================================================
Canlidaki TAM kurali (siki giris kapisi -> konviksiyon tier -> gunluk top-N tavan)
gun-gun tarihsel veride koşar. "Bu config'le her gun kac sinyal / ne isabet olurdu?"
enriched_signals_v3.csv (nokta-zamanli short). Yeni veri gerekmez.

Kullanim:  python end_to_end_backtest.py   -> ciktinin TAMAMINI yapistir.
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


def d52(r):
    return ff(r.get("dist_52w_high")) or 0


for r in rows:
    r["y5"] = 1 if ff(r["resolved_pct_t5"]) >= 5 else 0
    r["y10"] = 1 if ff(r["resolved_pct_t5"]) >= 10 else 0
    r["_d"] = r["signal_date"][:10]


# --- canli kural bilesenleri ---
def strict_gate(r):  # yeni entry_ok proxy
    return atr(r) >= 4 or gap(r) >= 3 or rvol(r) >= 2


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


_PROB = {"A": 0.73, "B": 0.63, "C": 0.56}
_ORD = {"A": 0, "B": 1, "C": 2}


def comp(r):
    return (
        4 * min(sh(r) / 20, 1)
        + 3 * min(atr(r) / 6, 1)
        + 3 * min(max(gap(r), 0) / 5, 1)
        + 2 * min(max(rvol(r) - 1, 0) / 2, 1)
        - 1.5 * min(max(d52(r) - 0.9, 0) / 0.1, 1)
    )


for r in rows:
    r["_tier"] = tier(r)
    r["_c"] = comp(r)

N = len(rows)
ndays = len({r["_d"] for r in rows})


def P(sub, k):
    return sum(r[k] for r in sub) / len(sub) if sub else 0


b5 = P(rows, "y5")
b10 = P(rows, "y10")
print(f"n={N} gun={ndays} (~{N/ndays:.0f}/gun ham)  baz >=5% {b5*100:.1f}% >=10% {b10*100:.1f}%")

print("\n=== KATMAN KATMAN (tum donem) ===")


def show(name, sub):
    print(
        f"  {name:30s} n={len(sub):>5} ~{len(sub)/ndays:5.1f}/gun  >=5% {P(sub,'y5')*100:5.1f}% (lift {P(sub,'y5')/b5:.2f})  >=10% {P(sub,'y10')*100:5.1f}%"
    )


show("0) ham (tum sinyaller)", rows)
gated = [r for r in rows if strict_gate(r)]
show("1) siki kapi", gated)
tiered = [r for r in gated if r["_tier"] in ("A", "B", "C")]
show("2) + tier (A/B/C)", tiered)
show("   ...bunlardan Tier A", [r for r in tiered if r["_tier"] == "A"])
show("   ...Tier B", [r for r in tiered if r["_tier"] == "B"])
show("   ...Tier C", [r for r in tiered if r["_tier"] == "C"])

# --- gunluk top-N tavan simulasyonu ---
byday = defaultdict(list)
for r in tiered:
    byday[r["_d"]].append(r)


def daily_topN(nn):
    picks = []
    for _d, rs in byday.items():
        rs2 = sorted(rs, key=lambda r: (_ORD[r["_tier"]], -_PROB[r["_tier"]], -r["_c"]))
        picks += rs2[:nn]
    return picks


print("\n=== 3) GUNLUK TAVAN TARAMASI (tier'li adaylardan top-N/gun) ===")
print(
    f"{'N/gun':>6}{'toplam':>8}{'gercek/gun':>11}{'>=5%':>8}{'lift':>6}{'>=10%':>8}{'recall5':>9}"
)
total5 = sum(r["y5"] for r in rows)
for nn in [1, 2, 3, 5, 8, 10, 15]:
    picks = daily_topN(nn)
    if not picks:
        continue
    rec = sum(r["y5"] for r in picks) / total5 if total5 else 0
    print(
        f"{nn:>6}{len(picks):>8}{len(picks)/ndays:>11.1f}{P(picks,'y5')*100:>7.1f}%{P(picks,'y5')/b5:>6.2f}{P(picks,'y10')*100:>7.1f}%{rec*100:>8.1f}%"
    )

# --- IS vs OOS: onerilen config (top-5/gun) ---
print("\n=== 4) ONERILEN CONFIG (top-5/gun) IS vs OOS ===")
picks5 = daily_topN(5)
for lab, cond in [
    ("TUM", lambda r: True),
    ("IS 2025", lambda r: r["_d"] < "2026-01-01"),
    ("OOS 2026", lambda r: r["_d"] >= "2026-01-01"),
]:
    seg = [r for r in picks5 if cond(r)]
    allseg = [r for r in rows if cond(r)]
    if len(seg) >= 15:
        bb = P(allseg, "y5")
        print(
            f"  {lab:10s} n={len(seg):>4} ~{len(seg)/len({r['_d'] for r in allseg}):.1f}/gun  >=5% {P(seg,'y5')*100:5.1f}% (baz {bb*100:.1f}%, lift {P(seg,'y5')/bb:.2f})  >=10% {P(seg,'y10')*100:5.1f}%"
        )
print(
    "\n>>> Karar: precision platoya girdigi + gunluk sayinin makul oldugu N. lift IS/OOS'ta >1.5 kalmali."
)
print("Bu ciktinin TAMAMINI Claude'a yapistir.")
