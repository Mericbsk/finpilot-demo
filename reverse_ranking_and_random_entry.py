#!/usr/bin/env python3
"""
reverse_ranking_and_random_entry.py — İki deney tek scriptte:

DENEY A (Reverse-Ranking): composite/finpilot skorunun ALT-%20'si (ters-sıralama,
fade-adayı) günlük kesitte seçilip üst-%20 ve baseline'la IS/OOS kıyaslanır.

DENEY B (Random-Entry vs Mevcut-Exit): edge_recheck'in gerçek sinyalleri
(entry_ok cohort'unu temsilen tüm sinyaller) ile AYNI exit-mekaniğiyle (TP=2xATR,
SL=1xATR, H=5) rastgele (symbol,date) kontrolünün tb_ret dağılımı kıyaslanır.
Amaç: edge entry-seçiminde mi, yoksa yalnız exit-mekaniğinde mi (ikisi de aynıysa
entry seçim-değeri katmıyor demektir).
"""

from __future__ import annotations

import csv
import random
import statistics
import sys

sys.path.insert(0, ".")
from edge_recheck import atr_pct, bars, outcomes  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def deney_a():
    print("=" * 70)
    print("DENEY A — REVERSE-RANKING (alt-%20 vs üst-%20 vs baseline)")
    print("=" * 70)
    rows = list(csv.DictReader(open("data/backtest_out/edge_recheck.csv")))
    for r in rows:
        try:
            r["_c2c"] = float(r["c2c5_net"])
        except (ValueError, KeyError):
            r["_c2c"] = None
    dates = sorted({r["scan_date"] for r in rows})
    cut = dates[len(dates) // 2]

    def topk(sub, key, frac, reverse):
        by_date = {}
        for r in sub:
            by_date.setdefault(r["scan_date"], []).append(r)
        out = []
        for d, grp in by_date.items():
            valid = [r for r in grp if r.get(key) not in (None, "") and r["_c2c"] is not None]
            if len(valid) < 5:
                continue
            valid.sort(key=lambda r: float(r[key]), reverse=reverse)
            n = max(1, int(len(valid) * frac))
            out.extend(valid[:n])
        return out

    def stats(sub, label):
        vals = [r["_c2c"] for r in sub if r["_c2c"] is not None]
        if not vals:
            return f"{label:32} n=0"
        w = 100 * sum(1 for v in vals if v > 0) / len(vals)
        return f"{label:32} n={len(vals):6d}  win%={w:5.1f}  medRet={statistics.median(vals):+6.3f}  meanRet={statistics.mean(vals):+6.3f}"

    for key in ["composite_score", "finpilot_score"]:
        print(f"\n--- {key} ---")
        for name, sub in [
            ("IS", [r for r in rows if r["scan_date"] < cut]),
            ("OOS", [r for r in rows if r["scan_date"] >= cut]),
        ]:
            baseline = [r for r in sub if r["_c2c"] is not None]
            top20 = topk(sub, key, 0.20, reverse=True)
            bot20 = topk(sub, key, 0.20, reverse=False)
            print(f"  [{name}]")
            print("   " + stats(baseline, "baseline (tüm)"))
            print("   " + stats(top20, "ÜST-%20 (normal ranking)"))
            print("   " + stats(bot20, "ALT-%20 (REVERSE/fade-adayı)"))


def deney_b(n_control=3000, seed=7):
    print("\n" + "=" * 70)
    print("DENEY B — RANDOM-ENTRY vs GERÇEK-SİNYAL (aynı exit-mekaniği)")
    print("=" * 70)
    sig_rows = list(csv.DictReader(open("data/backtest_out/edge_recheck.csv")))
    actual_tb = [float(r["tb_ret"]) for r in sig_rows if r.get("tb_ret") not in (None, "")]
    actual_c2c = [float(r["c2c5_net"]) for r in sig_rows if r.get("c2c5_net") not in (None, "")]

    syms = sorted({r["symbol"] for r in sig_rows})
    sig_dates_by_sym = {}
    for r in sig_rows:
        sig_dates_by_sym.setdefault(r["symbol"], set()).add(r["scan_date"])

    rnd = random.Random(seed)
    control_tb, control_c2c = [], []
    tries = 0
    bars_cache = {}
    while len(control_tb) < n_control and tries < n_control * 8:
        tries += 1
        s = rnd.choice(syms)
        if s not in bars_cache:
            bars_cache[s] = bars(s)
        b = bars_cache[s]
        if not b or len(b) < 40:
            continue
        ei = rnd.randint(20, len(b) - 10)
        d = b[ei - 1]["date"] if ei > 0 else None
        # Gerçek bir sinyal gününe denk gelmesin diye kabaca ele — tam engelleme değil ama azaltır.
        if d in sig_dates_by_sym.get(s, set()):
            continue
        a = atr_pct(b, ei)
        if not a:
            continue
        o = outcomes(b, ei, a)
        if not o:
            continue
        c2c, c2cnet, tb, mfe, mae = o
        control_tb.append(tb)
        control_c2c.append(c2cnet)

    def stats(vals, label):
        if not vals:
            return f"{label:32} n=0"
        w = 100 * sum(1 for v in vals if v > 0) / len(vals)
        return f"{label:32} n={len(vals):6d}  win%={w:5.1f}  medRet={statistics.median(vals):+6.3f}  meanRet={statistics.mean(vals):+6.3f}"

    print("\n-- tb_ret (triple-barrier, TP=2xATR/SL=1xATR/H=5) --")
    print(stats(actual_tb, "GERÇEK sinyaller"))
    print(stats(control_tb, "RANDOM-entry kontrol"))
    print("\n-- c2c5_net (close-to-close, aynı maliyet) --")
    print(stats(actual_c2c, "GERÇEK sinyaller"))
    print(stats(control_c2c, "RANDOM-entry kontrol"))
    print(f"\n(kontrol denemesi: {tries}, hedef: {n_control})")


if __name__ == "__main__":
    deney_a()
    deney_b()
