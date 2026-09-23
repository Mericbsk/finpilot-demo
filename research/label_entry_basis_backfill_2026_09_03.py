#!/usr/bin/env python3
"""
label_entry_basis geriye-donuk backfill -- Meric onayli, Arastirma Portfoyu
Kurulu #1 kalemi.

reports/data_repair_diagnosis_2026-09-03.md'nin kok-neden bulgusu: scan_ts >= 15:30
olan taramalarda entry fiyati gun kapanisina yakin (rho=0.9829 gercek 5g getiriyle),
< 15:30 olanlarda intraday bir fiyat olabiliyor (rho=0.9173, >5pp sapma oranı %5.70,
sapmalarin %79'u 13:30-14:30 saatlerinde). Bu script:

  1. Mevcut full_universe_enriched.csv'yi (48.188+ satir) YENIDEN CEKMEDEN
     (aga erisim gerektirmez -- scan_ts zaten CSV'de var) label_entry_basis
     alanini geriye-donuk hesaplar.
  2. c2c_5d/c2c_1d/mae_t5 gibi MEVCUT DEGERLERE DOKUNMAZ -- yalnizca provenance
     etiketi ekler.
  3. Yeni bir "clean" (yalnizca eod_close) arastirma export'u yazar --
     production/canli scanner'a hicbir etkisi yok, yalnizca research/backtest_out.
  4. Kalite raporu: n, oran, hangi saat dilimlerinin en cok intraday oldugu.

Fetch script'inin kendisi (fetch_full_universe_and_retest.py) da ayni esikle
label_entry_basis'i ARTIK BASTAN hesapliyor (bu turda eklendi) -- bu script
yalnizca ONCEDEN uretilmis CSV'yi geriye-donuk etiketlemek icin.
"""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

SRC = Path("data/backtest_out/full_universe_enriched.csv")
OUT_LABELED = Path("data/backtest_out/full_universe_enriched_labeled.csv")
OUT_CLEAN = Path("data/backtest_out/full_universe_enriched_eod_only.csv")
EOD_THRESHOLD = "15:30"


def label_entry_basis(scan_ts: str) -> str:
    if not scan_ts or " " not in scan_ts:
        return "unknown"
    hhmm = scan_ts.split(" ", 1)[1][:5]
    if len(hhmm) != 5 or hhmm[2] != ":":
        return "unknown"
    return "eod_close" if hhmm >= EOD_THRESHOLD else "intraday"


def main():
    with open(SRC, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    if "label_entry_basis" not in fieldnames:
        fieldnames = fieldnames + ["label_entry_basis"]

    basis_counts = Counter()
    hour_counts = Counter()
    for r in rows:
        basis = label_entry_basis(r.get("scan_ts", ""))
        r["label_entry_basis"] = basis
        basis_counts[basis] += 1
        ts = r.get("scan_ts", "")
        if " " in ts:
            hour_counts[(ts.split(" ", 1)[1][:5], basis)] += 1

    with open(OUT_LABELED, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)

    clean_rows = [r for r in rows if r["label_entry_basis"] == "eod_close"]
    with open(OUT_CLEAN, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(clean_rows)

    total = len(rows)
    print(f"[VERI] toplam satir={total}")
    for k, v in basis_counts.most_common():
        print(f"  {k}: {v} ({100*v/total:.1f}%)")
    print(
        f"\n[CIKTI] {OUT_LABELED} -- tum satirlar + label_entry_basis (mevcut degerler DEGISMEDI)"
    )
    print(
        f"[CIKTI] {OUT_CLEAN} -- yalnizca eod_close satirlar (n={len(clean_rows)}, "
        f"%{100*len(clean_rows)/total:.1f}) -- diagnostik raporun onerdigi 'temiz' alt-kume"
    )

    print("\n[KALITE] en cok intraday-etiketli saat dilimleri (top 10):")
    intraday_hours = Counter()
    for (hhmm, basis), n in hour_counts.items():
        if basis == "intraday":
            intraday_hours[hhmm] += n
    for hhmm, n in intraday_hours.most_common(10):
        print(f"  {hhmm}: {n} intraday-etiketli satir")


if __name__ == "__main__":
    main()
