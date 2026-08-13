#!/usr/bin/env python3
"""
catastrophe_subset_test.py — Item 4: eligible (entry_ok=True) kohortunun negatif
medyani TUM eligible isimlerde homojen mi, yoksa kucuk bir "felaket alt-kumesi"
(148 price-integrity-flagged sembol ve/veya penny-stock <$5) tarafindan mi
suruklenıyor?

Onem: eger felaket-alt-kumesi cikartilinca eligible-negatif-medyan bulgusu
kaybolursa/kucuk kalirsa -> "secim kirik" sonucu "secim riskli-bir-dilime
asiri-maruz" sonucuna donusur (daha ucuz, daha aksiyon-alinabilir bir duzeltme:
felaket-alt-kumesini scanner cikisinda filtrele).

Metodoloji: dedup (en-erken scan_ts), gun-kumeli mean/median/SE/t (H0: fark=0),
blok-bootstrap CI (otokorelasyon icin, c2c_5d 5-gunluk ileri getiri oldugundan).
"""

from __future__ import annotations

import csv
import json
import math
import random
import statistics
import sys
from collections import defaultdict

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BLOCK = 5
BOOT_B = 5000
RNG = random.Random(2026)


def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def load_dedup_rows():
    best = {}
    with open("data/backtest_out/full_universe_enriched.csv") as f:
        for r in csv.DictReader(f):
            k = (r["symbol"], r["scan_date"])
            ts = r.get("scan_ts", "")
            if k not in best or ts < best[k][0]:
                best[k] = (ts, r)
    return [r for _, r in best.values()]


def load_flagged():
    data = json.load(open("data/backtest_out/price_cache_adjusted_integrity_audit_2026-08-07.json"))
    return set(x["symbol"] for x in data["flagged_symbols"])


def block_bootstrap_ci(vals, block=BLOCK, B=BOOT_B, rng=None):
    rng = rng or RNG
    n = len(vals)
    if n < block + 1:
        return None
    nb = math.ceil(n / block)
    means = []
    for _ in range(B):
        s = []
        for _ in range(nb):
            start = rng.randrange(0, n - block + 1)
            s.extend(vals[start : start + block])
        means.append(statistics.mean(s[:n]))
    means.sort()
    return means[int(0.025 * B)], means[int(0.975 * B)], statistics.mean(means)


def day_cluster(rows, val_key):
    """rows -> gun-basina deger listesi -> gun-basina ortalama -> gun-kumeli istatistik."""
    by_day = defaultdict(list)
    for r in rows:
        by_day[r["scan_date"]].append(r[val_key])
    day_means = {d: statistics.mean(v) for d, v in by_day.items() if v}
    day_medians = {d: statistics.median(v) for d, v in by_day.items() if v}
    return by_day, day_means, day_medians


def report(label, rows, val_key):
    by_day, day_means, day_medians = day_cluster(rows, val_key)
    n_days = len(day_means)
    if n_days < 3:
        print(f"  {label:38} n_gun={n_days} yetersiz  n_satir={len(rows)}")
        return None
    vals = list(day_means.values())
    m = statistics.mean(vals)
    med_of_medians = statistics.median(list(day_medians.values()))
    sd = statistics.pstdev(vals) if n_days > 1 else 0
    se = sd / math.sqrt(n_days) if sd else 0
    t = m / se if se else float("nan")
    n_rows = sum(len(v) for v in by_day.values())
    print(
        f"  {label:38} n_gun={n_days:4d} n_satir={n_rows:6d}  gun-kumeli-ort={m:+7.3f}  "
        f"gun-medyanlarinin-medyani={med_of_medians:+7.3f}  t~(H0=0)={t:+.2f}"
    )
    return day_means


def paired_diff_report(label, day_means_a, day_means_b):
    common = sorted(set(day_means_a) & set(day_means_b))
    if len(common) < 5:
        print(f"  {label:38} n=yetersiz")
        return
    diffs = [day_means_b[d] - day_means_a[d] for d in common]
    n = len(diffs)
    m = statistics.mean(diffs)
    sd = statistics.pstdev(diffs) if n > 1 else 0
    se = sd / math.sqrt(n) if sd else 0
    t = m / se if se else float("nan")
    ci = block_bootstrap_ci(diffs)
    ci_str = f"[{ci[0]:+.3f}, {ci[1]:+.3f}]" if ci else "n/a"
    verdict = "ANLAMLI FARK" if (ci and (ci[0] > 0 or ci[1] < 0)) else "anlamsiz (CI 0'i iceriyor)"
    print(
        f"  {label:38} n_gun={n:4d}  fark-ort={m:+.3f}  naive-t~={t:+.2f}  boot-CI={ci_str}  [{verdict}]"
    )


def main():
    rows = load_dedup_rows()
    flagged = load_flagged()

    data = []
    for r in rows:
        c5 = _f(r.get("c2c_5d"))
        px = _f(r.get("price"))
        eo = r.get("entry_ok")
        if c5 is None or eo not in ("True", "False"):
            continue
        data.append(
            {
                "symbol": r["symbol"],
                "scan_date": r["scan_date"],
                "c5": c5,
                "eligible": eo == "True",
                "flagged": r["symbol"] in flagged,
                "penny": (px is not None and px < 5.0),
            }
        )
    print(
        f"[VERI] dedup + c2c_5d+entry_ok dolu satir={len(data)}  "
        f"gun={len({r['scan_date'] for r in data})}  "
        f"flagged-sembol-oranı={sum(1 for r in data if r['flagged'])}/{len(data)}={100*sum(1 for r in data if r['flagged'])/len(data):.1f}%"
    )

    eligible = [r for r in data if r["eligible"]]
    rejected = [r for r in data if not r["eligible"]]

    print("\n" + "=" * 92)
    print("ADIM 1 -- TUM eligible vs rejected (referans, felaket-filtresi YOK)")
    print("=" * 92)
    dm_elig_all = report("eligible (TUMU, filtresiz)", eligible, "c5")
    dm_rej_all = report("rejected (TUMU, filtresiz)", rejected, "c5")
    if dm_elig_all and dm_rej_all:
        paired_diff_report("eligible - rejected (filtresiz)", dm_rej_all, dm_elig_all)

    print("\n" + "=" * 92)
    print("ADIM 2 -- eligible kohortu ICINDE: flagged (148 price-integrity) vs non-flagged")
    print("=" * 92)
    elig_flagged = [r for r in eligible if r["flagged"]]
    elig_nonflagged = [r for r in eligible if not r["flagged"]]
    print(
        f"  eligible-icinde flagged-satir-sayisi={len(elig_flagged)}/{len(eligible)}="
        f"{100*len(elig_flagged)/len(eligible) if eligible else 0:.1f}%"
    )
    dm_ef = report("eligible + flagged (felaket-alt-kumesi)", elig_flagged, "c5")
    dm_enf = report("eligible + non-flagged (temiz)", elig_nonflagged, "c5")
    if dm_ef and dm_enf:
        paired_diff_report("flagged - non-flagged (eligible icinde)", dm_enf, dm_ef)

    print("\n" + "=" * 92)
    print("ADIM 3 -- eligible vs rejected, FELAKET-ALT-KUMESI CIKARILDIKTAN SONRA")
    print("=" * 92)
    eligible_clean = elig_nonflagged
    rejected_clean = [r for r in rejected if not r["flagged"]]
    print(
        f"  rejected-icinde flagged-satir-sayisi={sum(1 for r in rejected if r['flagged'])}/{len(rejected)}="
        f"{100*sum(1 for r in rejected if r['flagged'])/len(rejected) if rejected else 0:.1f}%"
    )
    dm_ec = report("eligible (flagged-CIKARILMIS)", eligible_clean, "c5")
    dm_rc = report("rejected (flagged-CIKARILMIS)", rejected_clean, "c5")
    if dm_ec and dm_rc:
        paired_diff_report("eligible - rejected (flagged-cikarilmis)", dm_rc, dm_ec)

    print("\n" + "=" * 92)
    print("ADIM 4 -- ALTERNATIF FELAKET-TANIMI: penny-stock (price<$5) alt-kumesi")
    print("=" * 92)
    elig_penny = [r for r in eligible if r["penny"]]
    elig_nonpenny = [r for r in eligible if not r["penny"]]
    print(
        f"  eligible-icinde penny(<$5)-satir-sayisi={len(elig_penny)}/{len(eligible)}="
        f"{100*len(elig_penny)/len(eligible) if eligible else 0:.1f}%"
    )
    dm_ep = report("eligible + penny(<$5)", elig_penny, "c5")
    dm_enp = report("eligible + non-penny(>=$5)", elig_nonpenny, "c5")
    if dm_ep and dm_enp:
        paired_diff_report("penny - non-penny (eligible icinde)", dm_enp, dm_ep)

    print("\n" + "=" * 92)
    print(
        "ADIM 5 -- eligible vs rejected, HEM flagged HEM penny CIKARILDIKTAN SONRA (en-temiz kohort)"
    )
    print("=" * 92)
    eligible_vclean = [r for r in eligible if not r["flagged"] and not r["penny"]]
    rejected_vclean = [r for r in rejected if not r["flagged"] and not r["penny"]]
    dm_evc = report("eligible (cift-temiz)", eligible_vclean, "c5")
    dm_rvc = report("rejected (cift-temiz)", rejected_vclean, "c5")
    if dm_evc and dm_rvc:
        paired_diff_report("eligible - rejected (cift-temiz)", dm_rvc, dm_evc)


if __name__ == "__main__":
    main()
