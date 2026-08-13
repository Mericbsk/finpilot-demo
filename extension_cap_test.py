#!/usr/bin/env python3
"""
extension_cap_test.py — Extension/exhaustion teşhisini aksiyon-alınabilir teste çevir.

Önceki tur (extension_exhaustion_test.py) yalnız entry_ok-ORANININ extension-decile'a göre
arttığını gösterdi (dolaylı kanıt). Bu script üç doğrudan testi ekliyor:

  A) Extension decile → GERÇEKLEŞEN forward-getiri (c2c5_net), gün-kümeli.
     "Yüksek extension -> düşük getiri" nedensel yönü doğrudan mı?
  B) entry_ok=True vs entry_ok=False: ortalama extension farkı, gün-kümeli SE/t ile.
     (Önceki decile-rate bulgusunun istatistiksel teyidi.)
  C) EXTENSION-CAP SİMÜLASYONU (aksiyon-adayı): entry_ok=True kümesine extension-tavanı
     uygulanınca "capped-eligible" kümesinin gerçekleşen getirisi/win-rate'i
     (a) orijinal eligible, (b) rejected kümesine göre nasıl değişiyor + kapsam-maliyeti (n kaybı).

Metodoloji: dedup (en-erken-scan_ts), gün-kümeli mean/median/SE/t (reverse_ranking_closure.py
dersleriyle tutarlı — satır-bazlı test yapılmıyor).
"""

from __future__ import annotations

import bisect
import csv
import json
import math
import os
import statistics
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PD = "data/price_cache"
_bcache = {}


def bars(sym):
    if sym not in _bcache:
        p = f"{PD}/{sym}.json"
        if os.path.exists(p):
            try:
                b = json.load(open(p))
                _bcache[sym] = (
                    sorted(b, key=lambda x: x["date"]) if isinstance(b, list) and b else None
                )
            except Exception:
                _bcache[sym] = None
        else:
            _bcache[sym] = None
    return _bcache[sym]


def atr_ext(sym, scan_date, p=14, lookback=20):
    b = bars(sym)
    if not b:
        return None
    dates = [x["date"] for x in b]
    ei = bisect.bisect_right(dates, scan_date) - 1
    if ei < max(p, lookback) + 1:
        return None
    trs = [
        max(
            b[j]["high"] - b[j]["low"],
            abs(b[j]["high"] - b[j - 1]["close"]),
            abs(b[j]["low"] - b[j - 1]["close"]),
        )
        for j in range(ei - p, ei)
    ]
    atr = sum(trs) / len(trs)
    if atr <= 0:
        return None
    ret20 = (b[ei]["close"] / b[ei - lookback]["close"] - 1) if b[ei - lookback]["close"] else None
    return (ret20 * b[ei]["close"] / atr) if ret20 is not None else None


def dedup_enriched():
    """(symbol,scan_date) -> en-erken-scan_ts satırının entry_ok/conviction_tier."""
    best = {}
    for r in csv.DictReader(open("data/backtest_out/full_universe_enriched.csv")):
        s, d, ts = r["symbol"], str(r["scan_date"]), r.get("scan_ts", "")
        k = (s, d)
        if k not in best or ts < best[k][0]:
            best[k] = (ts, r.get("entry_ok"), r.get("conviction_tier"))
    return best


def load_outcomes():
    out = {}
    for r in csv.DictReader(open("data/backtest_out/edge_recheck.csv")):
        k = (r["symbol"], r["scan_date"])
        if k in out:
            continue
        try:
            out[k] = float(r["c2c5_net"])
        except (ValueError, KeyError):
            continue
    return out


def cluster_report(daily_vals, label):
    """daily_vals: {date: [values]} -> gün-başına ortalama al, sonra gün-kümeli SE/t (H0: mean=0)."""
    day_means = {d: statistics.mean(v) for d, v in daily_vals.items() if v}
    n = len(day_means)
    if n < 5:
        print(f"    {label:30} n_gün={n} yetersiz")
        return None, n
    vals = list(day_means.values())
    m = statistics.mean(vals)
    med = statistics.median(vals)
    winrate = (
        100
        * sum(1 for d, v in daily_vals.items() for x in v if x > 0)
        / sum(len(v) for v in daily_vals.values())
    )
    sd = statistics.pstdev(vals) if n > 1 else 0
    se = sd / math.sqrt(n) if n else float("nan")
    t = m / se if se else float("nan")
    n_obs = sum(len(v) for v in daily_vals.values())
    print(
        f"    {label:30} n_gün={n:4d} n_obs={n_obs:6d}  ort={m:+7.3f}  medyan={med:+7.3f}  win%={winrate:5.1f}  SE={se:6.3f}  t~={t:+.2f}"
    )
    return m, n


def paired_report(a, b, label):
    common = set(a) & set(b)
    diffs = []
    for d in common:
        if a[d] and b[d]:
            diffs.append(statistics.mean(a[d]) - statistics.mean(b[d]))
    if len(diffs) < 5:
        print(f"    {label:30} n=yetersiz")
        return
    m = statistics.mean(diffs)
    sd = statistics.pstdev(diffs) if len(diffs) > 1 else 0
    se = sd / math.sqrt(len(diffs)) if diffs else float("nan")
    t = m / se if se else float("nan")
    verdict = "anlamli" if abs(t) > 2 else "anlamsiz"
    print(
        f"    {label:30} n_gün={len(diffs):4d}  ort-fark={m:+.3f}  SE={se:.3f}  t~={t:+.2f}  [{verdict}]"
    )


def main():
    print(
        "Dedup + outcome-join + extension hesaplaniyor (price_cache okumasi agir, biraz surer)..."
    )
    enr = dedup_enriched()
    outc = load_outcomes()

    rows = []
    for (s, d), (ts, entry_ok, conv) in enr.items():
        if entry_ok not in ("True", "False"):
            continue
        if (s, d) not in outc:
            continue
        rows.append(
            {
                "symbol": s,
                "date": d,
                "entry_ok": entry_ok == "True",
                "conv": conv,
                "ret": outc[(s, d)],
            }
        )

    print(f"Dedup+outcome-birlesmis satir: {len(rows)}")

    # zaman-butcesi icin orneklem (price_cache IO agir) — entry_ok True/False dengeli
    import random

    random.Random(23).shuffle(rows)
    SAMPLE = len(
        rows
    )  # tam populasyon -- eligible(entry_ok=True) sadece 801 satir, orneklemenin gucu kesmesin
    rows = rows[:SAMPLE]
    print(f"Ornek n={len(rows)} (extension hesabi icin)")

    for r in rows:
        r["ext"] = atr_ext(r["symbol"], r["date"])

    valid = [r for r in rows if r["ext"] is not None]
    print(f"Extension hesaplanabilen: {len(valid)}/{len(rows)}")

    # ============ TEST A: extension decile -> gercek forward-getiri ============
    print("\n" + "=" * 78)
    print("TEST A: ATR-extension decile -> gun-kumeli gercek c2c5_net (nedensellik yonu)")
    print("=" * 78)
    valid_sorted = sorted(valid, key=lambda r: r["ext"])
    n = len(valid_sorted)
    for i in range(10):
        lo, hi = i * n // 10, (i + 1) * n // 10
        chunk = valid_sorted[lo:hi]
        daily = {}
        for r in chunk:
            daily.setdefault(r["date"], []).append(r["ret"])
        ext_range = f"[{chunk[0]['ext']:+.2f}, {chunk[-1]['ext']:+.2f}]" if chunk else "-"
        cluster_report(daily, f"decile {i} ext={ext_range}")

    # ============ TEST B: entry_ok True vs False - ortalama extension farki ============
    print("\n" + "=" * 78)
    print("TEST B: entry_ok=True vs False -- ortalama ATR-extension (gun-kumeli)")
    print("=" * 78)
    daily_true = {}
    daily_false = {}
    for r in valid:
        tgt = daily_true if r["entry_ok"] else daily_false
        tgt.setdefault(r["date"], []).append(r["ext"])
    cluster_report(daily_true, "entry_ok=True (eligible)")
    cluster_report(daily_false, "entry_ok=False (rejected)")
    paired_report(daily_true, daily_false, "eligible - rejected (ext farki)")

    # ============ TEST C: extension-cap simulasyonu ============
    print("\n" + "=" * 78)
    print("TEST C: extension-cap simulasyonu -- capped-eligible vs orijinal-eligible vs rejected")
    print("=" * 78)
    elig_ext = sorted(r["ext"] for r in valid if r["entry_ok"])
    if elig_ext:
        med_cap = statistics.median(elig_ext)
        p70_cap = elig_ext[int(0.70 * len(elig_ext))]
        print(
            f"  eligible-kumesi extension: medyan={med_cap:+.2f}  p70={p70_cap:+.2f}  (n={len(elig_ext)})"
        )

        for cap_name, cap_val in [("medyan-tavan", med_cap), ("p70-tavan", p70_cap)]:
            daily_orig = {}
            daily_capped = {}
            for r in valid:
                if r["entry_ok"]:
                    daily_orig.setdefault(r["date"], []).append(r["ret"])
                    if r["ext"] <= cap_val:
                        daily_capped.setdefault(r["date"], []).append(r["ret"])
            n_orig = sum(len(v) for v in daily_orig.values())
            n_capped = sum(len(v) for v in daily_capped.values())
            cut_pct = 100 * (1 - n_capped / n_orig) if n_orig else 0
            print(
                f"\n  -- cap={cap_name} ({cap_val:+.2f}) -- kesilen pay: %{cut_pct:.1f} (n {n_orig}->{n_capped}) --"
            )
            cluster_report(daily_orig, "orijinal eligible (tum)")
            cluster_report(daily_capped, "capped-eligible (ext<=tavan)")
            cluster_report(daily_false, "rejected (referans)")
            paired_report(daily_capped, daily_orig, "capped - orijinal-eligible (fark)")
            paired_report(daily_capped, daily_false, "capped - rejected (fark)")

    # ============ TEST D: conviction tier icinde ext siralamasi ============
    print("\n" + "=" * 78)
    print("TEST D (ek): conviction_tier A/B/C -- ortalama extension (gun-kumeli)")
    print("=" * 78)
    for tier in ["A", "B", "C"]:
        daily = {}
        for r in valid:
            if r["conv"] == tier:
                daily.setdefault(r["date"], []).append(r["ext"])
        cluster_report(daily, f"tier {tier}")


if __name__ == "__main__":
    main()
