#!/usr/bin/env python3
"""
Hipotez Uretimi Master Prompt v1.0 - H3 (opening-range fade) uzerinde uygulama.

Mumkun bulan sinyal: direction_threshold_matrix_2026_09_03.py'nin H3 testi,
gap>=3% gunlerinde "ilk 30dk yonunun tersini al, kapanista cik" kuralinin
brut win_rate ve mean/median'ini olcuyordu (n=698, 59 gun, sembol kimligi
YOKTU - h3_fade() sembolu atip sadece agregat donuyordu).

Bu script AYNI kaynak veriyi (data/intraday_cache/*.json) sembol kimligiyle
yeniden insa eder, sector_map_full.csv ve full_universe_enriched.csv ile
zenginlestirir, ve docs/2026-09-03-hipotez-uretimi-master-prompt.md'nin
tam surecini (Bolum 0-7) uygular: ONCEDEN arama butcesini tanimla -> tum
adaylari (kazanan/kaybeden) logla -> 5 sartli suzgecten gecir -> sadece
gececek olani (varsa) on-kayit formatinda kilitle.

Hicbir sayi bu script'in ciktisinda "dogrulandi" olarak sunulmaz.
"""

from __future__ import annotations

import json
import math
import statistics
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

RNG = np.random.default_rng(20260903)
INTRADAY = Path("data/intraday_cache")
CSV = Path("data/backtest_out/full_universe_enriched.csv")
SECTOR_MAP = Path("data/backtest_out/sector_map_full.csv")
BLOCK = 5
BOOT_B = 5000
COST_PCT = 0.55  # round-trip diagnostic cost, ayni onceki high-RVOL exit raporuyla tutarli

# ---------------------------------------------------------------------------
# BOLUM 0 -- ARAMA BUTCESI (sonuclari gormeden ONCE tanimlanir)
# ---------------------------------------------------------------------------
SEARCH_BUDGET = [
    (
        "gap_direction",
        2,
        "Asimetrik reaksiyon hipotezi: dusus-gap'leri panik/asiri-tepki "
        "tasiyabilir (mean-reversion literaturu), yukselis-gap'leri ise devam egilimli "
        "olabilir (momentum) -- ikisi ayni fade kuralina ayni tepki vermeyebilir.",
    ),
    (
        "price_tertile",
        3,
        "Fiyat, likidite/mikroyapi icin kaba bir proxy (dolar-hacim veride "
        "yok). Dusuk fiyatli hisselerde spread/slippage nispeten daha buyuk oldugundan brut "
        "fade edge'i orada daha kirilgan olabilir.",
    ),
    (
        "gap_size_tertile",
        3,
        "Gap ne kadar buyukse ilk-30dk hareketi o kadar 'asiri' olabilir "
        "-- asiri-tepki hipotezine gore en buyuk gap'lerde fade daha guclu calismasi beklenir.",
    ),
    (
        "rvol_tertile",
        3,
        "Yuksek RVOL, guclu yeni bilgi/haber akisini isaret edebilir (devam "
        "egilimli); dusuk RVOL'de hareket likidite/mikroyapi kaynakli olabilir (fade'e daha "
        "uygun) -- iki yonlu bir a priori beklenti var, bu yuzden test edilmeye deger.",
    ),
    (
        "sector_etf",
        11,
        "Sektorler arasinda likidite/haber-akis hizi farkli olabilir; "
        "XLK/XLE gibi yuksek-beta sektorlerde asiri-tepki farkli buyuklukte olabilir.",
    ),
    (
        "day_of_week",
        5,
        "Pazartesi/Cuma etkisi literaturde bilinen (haftasonu bilgi birikimi, "
        "likidite farkliligi) -- kaba ama ucuz bir kontrol degiskeni.",
    ),
]
M_GENERATION = sum(n for _, n, _ in SEARCH_BUDGET)
M_EXISTING = 9754  # score_component_decomposition.py / red-team raporundan tasinan mevcut butce
M_TOTAL = M_EXISTING + M_GENERATION


def bonferroni_t(m: int, alpha: float = 0.05) -> float:
    """Iki-yonlu Bonferroni-duzeltilmis t esigi (normal yaklasimla)."""
    from math import erf

    # normal ppf icin ikili arama (scipy yoksa bagimsiz calisir)
    p_target = 1 - alpha / (2 * m)

    def norm_cdf(x):
        return 0.5 * (1 + erf(x / math.sqrt(2)))

    lo, hi = 0.0, 10.0
    for _ in range(200):
        mid = (lo + hi) / 2
        if norm_cdf(mid) < p_target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


T_THRESHOLD = bonferroni_t(M_TOTAL)

# ---------------------------------------------------------------------------
# BOLUM 1 -- VERI KARANTINASI
# ---------------------------------------------------------------------------
# direction_threshold_matrix_2026_09_03.py'nin H3'u zaten "muhurlenmis kesif"tir:
# data/intraday_cache/*.json (880 dosya). Bu script o veriyi YENIDEN KESFETMIYOR --
# aynı 698 gozlemi sembol kimligiyle yeniden kuruyor ve ARADIGI TEK SEY "bu desenin
# hangi mekanistik kosulda goruldugu" (Bolum 1'in izin verdigi tek analiz turu).
# Bagimsiz/kilitli set: intraday_cache'e YENI eklenecek gunler (henuz mevcut degil) --
# bu script'in urettigi HER ADAY, ancak o yeni veri geldiginde tek-atislik test edilebilir.
DISCOVERY_NOTE = (
    "data/intraday_cache/*.json (880 dosya, mevcut anlik goruntu) -- "
    "MUHURLENMIS KESIF. Bagimsiz dogrulama seti: bu tarihten SONRA "
    "intraday_cache'e eklenecek yeni gunler (henuz mevcut degil)."
)


def _f(x):
    try:
        v = float(x)
        return None if v != v else v
    except (TypeError, ValueError):
        return None


def iter_gap_days_with_symbol():
    for f in sorted(INTRADAY.glob("*.json")):
        symbol = f.name.split("_")[0]
        try:
            bars = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(bars, list) or len(bars) < 10:
            continue
        by_day: dict[str, list] = defaultdict(list)
        for b in bars:
            try:
                by_day[str(b[0])[:10]].append(b)
            except (IndexError, TypeError):
                continue
        days = sorted(by_day)
        for i, day in enumerate(days):
            if i == 0:
                continue
            today, prev = by_day[day], by_day[days[i - 1]]
            try:
                day_open, prev_close, day_close = (
                    float(today[0][1]),
                    float(prev[-1][4]),
                    float(today[-1][4]),
                )
            except (IndexError, TypeError, ValueError):
                continue
            if prev_close <= 0:
                continue
            gap = (day_open - prev_close) / prev_close * 100
            if abs(gap) < 3 or len(today) < 6:
                continue
            yield symbol, day, today, day_open, day_close, gap


def build_fade_rows():
    rows = []
    for symbol, day, today, day_open, day_close, gap in iter_gap_days_with_symbol():
        mark30 = float(today[min(1, len(today) - 1)][4])
        first_dir = np.sign(mark30 - day_open)
        if first_dir == 0:
            continue
        fade_ret = (day_close - mark30) / mark30 * 100 * (-first_dir)
        rows.append({"symbol": symbol, "date": day, "gap": gap, "fade_ret": fade_ret})
    return pd.DataFrame(rows)


def load_enrichment():
    sect = pd.read_csv(SECTOR_MAP)[["symbol", "etf"]].rename(columns={"etf": "sector_etf"})
    uni = pd.read_csv(CSV, low_memory=False)
    uni = uni.drop_duplicates(["symbol", "scan_date"], keep="first")
    uni = uni[["symbol", "scan_date", "price", "rvol", "atr_pct_real"]]
    return sect, uni


def day_cluster_stats(sub: pd.DataFrame):
    """Gun-kumeli medyan/ortalama + etkin-N (tekil gun sayisi) + outlier-bagimliligi."""
    n_days = sub["date"].nunique()
    n_months = sub["date"].str.slice(0, 7).nunique()
    if n_days == 0:
        return None
    by_day = sub.groupby("date")["fade_ret"].median()
    day_medians = by_day.values
    m = statistics.mean(day_medians)
    med = statistics.median(day_medians)
    sd = statistics.pstdev(day_medians) if len(day_medians) > 1 else 0.0
    se = sd / math.sqrt(len(day_medians)) if sd else 0.0
    t = m / se if se else float("nan")

    # outlier-bagimliligi: en iyi %5'i (satir bazinda, ham fade_ret) cikar, gun-kumeli medyani yeniden hesapla
    sub_sorted = sub.sort_values("fade_ret", ascending=False)
    cut = max(1, int(len(sub_sorted) * 0.05))
    sub_ex = sub_sorted.iloc[cut:]
    if sub_ex["date"].nunique() >= 3:
        by_day_ex = sub_ex.groupby("date")["fade_ret"].median()
        m_ex = statistics.mean(by_day_ex.values)
    else:
        m_ex = float("nan")

    cost_adj_med = med - COST_PCT
    cost_adj_mean = m - COST_PCT

    return {
        "n_rows": len(sub),
        "n_days": n_days,
        "n_months": n_months,
        "day_mean": round(m, 4),
        "day_median_of_medians": round(med, 4),
        "naive_t": round(t, 3) if t == t else None,
        "mean_after_top5_removed": round(m_ex, 4) if m_ex == m_ex else None,
        "outlier_flip": (m > 0) != (m_ex > 0) if m_ex == m_ex else None,
        "cost_adjusted_median": round(cost_adj_med, 4),
        "cost_adjusted_mean": round(cost_adj_mean, 4),
    }


def apply_filter(stats: dict, mech_reason: str) -> tuple[bool, list[str]]:
    """Bolum 3 -- 5 sartli suzgec."""
    reasons_failed = []
    # 1. mekanistik gerekce -- script seviyesinde her aday icin zaten yazili (SEARCH_BUDGET), gecer sayilir
    # 2. etkin-N >= 20 gun VE >= 3 ay
    if stats["n_days"] < 20 or stats["n_months"] < 3:
        reasons_failed.append(
            f"etkin-N yetersiz (n_gun={stats['n_days']}, n_ay={stats['n_months']}, esik: >=20 gun & >=3 ay)"
        )
    # 3. outlier-bagimliligi: yon degismemeli
    if stats["outlier_flip"] is True:
        reasons_failed.append("top-%5 cikarilinca yon degisiyor (outlier-bagimli)")
    elif stats["outlier_flip"] is None:
        reasons_failed.append("outlier-testi icin yetersiz veri (top-%5 sonrasi <3 gun)")
    # 4. maliyet-sonrasi pozitif
    if stats["cost_adjusted_median"] <= 0:
        reasons_failed.append(f"maliyet-sonrasi medyan <=0 ({stats['cost_adjusted_median']})")
    # 5. duzeltilmis esik
    if stats["naive_t"] is None or abs(stats["naive_t"]) <= T_THRESHOLD:
        reasons_failed.append(
            f"|t|={stats['naive_t']} <= Bonferroni esigi {T_THRESHOLD:.2f} (m_toplam={M_TOTAL})"
        )
    return (len(reasons_failed) == 0), reasons_failed


def main():
    fade = build_fade_rows()
    sect, uni = load_enrichment()
    fade = fade.merge(sect, on="symbol", how="left")
    fade = fade.merge(uni, left_on=["symbol", "date"], right_on=["symbol", "scan_date"], how="left")
    fade["dow"] = pd.to_datetime(fade["date"]).dt.day_name()
    fade["price_tertile"] = pd.qcut(
        fade["price"], 3, labels=["low", "mid", "high"], duplicates="drop"
    )
    fade["gap_size_tertile"] = pd.qcut(
        fade["gap"].abs(), 3, labels=["small", "mid", "large"], duplicates="drop"
    )
    fade["rvol_tertile"] = (
        pd.qcut(fade["rvol"], 3, labels=["low", "mid", "high"], duplicates="drop")
        if fade["rvol"].notna().sum() > 10
        else None
    )

    print(
        f"[VERI] toplam fade gozlemi (sembol-kimlikli, yeniden insa)={len(fade)}  "
        f"tekil-gun={fade['date'].nunique()}  tekil-sembol={fade['symbol'].nunique()}"
    )
    print(
        f"[BUTCE] m_generation={M_GENERATION}  m_eski={M_EXISTING}  m_toplam={M_TOTAL}  "
        f"yeni Bonferroni |t| esigi={T_THRESHOLD:.3f}"
    )
    print(f"[KARANTINA] {DISCOVERY_NOTE}\n")

    search_log = []
    hypothesis_register = []

    def evaluate(var_name, col, group_reason):
        if col not in fade.columns or fade[col].isna().all():
            print(f"  [{var_name}] kolon yok/tumu NaN -- atlandi")
            return
        for val, sub in fade.groupby(col, observed=True):
            if len(sub) < 8:
                continue
            stats = day_cluster_stats(sub)
            if stats is None:
                continue
            passed, fail_reasons = apply_filter(stats, group_reason)
            search_log.append(
                {
                    "degisken": var_name,
                    "kesim": str(val),
                    **stats,
                    "hipoteze_yukseldi_mi": "EVET" if passed else "hayir",
                    "eleme_nedeni": "; ".join(fail_reasons) if fail_reasons else "-",
                }
            )
            if passed:
                hypothesis_register.append(
                    {
                        "degisken": var_name,
                        "kesim": str(val),
                        "stats": stats,
                        "gerekce": group_reason,
                    }
                )

    fade["gap_direction"] = fade["gap"].apply(lambda g: "gap_up" if g > 0 else "gap_down")
    evaluate("gap_direction", "gap_direction", SEARCH_BUDGET[0][2])
    evaluate("price_tertile", "price_tertile", SEARCH_BUDGET[1][2])
    evaluate("gap_size_tertile", "gap_size_tertile", SEARCH_BUDGET[2][2])
    evaluate("rvol_tertile", "rvol_tertile", SEARCH_BUDGET[3][2])
    evaluate("sector_etf", "sector_etf", SEARCH_BUDGET[4][2])
    evaluate("day_of_week", "dow", SEARCH_BUDGET[5][2])

    print("\n" + "=" * 110)
    print("ARAMA GUNLUGU (Bolum 6) -- TUM denenen bolmeler, kazanan/kaybeden ayrimi olmadan")
    print("=" * 110)
    hdr = f"{'degisken':16} {'kesim':10} {'n_satir':>7} {'n_gun':>6} {'n_ay':>5} {'gun-medyan':>11} {'naive-t':>8} {'maliyet-sonrasi-medyan':>22}  hipoteze-yukseldi-mi"
    print(hdr)
    for r in search_log:
        print(
            f"{r['degisken']:16} {r['kesim']:10} {r['n_rows']:>7} {r['n_days']:>6} {r['n_months']:>5} "
            f"{r['day_median_of_medians']:>11} {str(r['naive_t']):>8} {r['cost_adjusted_median']:>22}  "
            f"{r['hipoteze_yukseldi_mi']}  [{r['eleme_nedeni']}]"
        )

    print("\n" + "=" * 110)
    print(f"HIPOTEZ KAYIT DEFTERI (Bolum 7) -- {len(hypothesis_register)} aday 5 sarti gecti")
    print("=" * 110)
    if not hypothesis_register:
        print("HICBIR aday 5 sartin tamamini gecemedi. Bolum 3 disiplinine gore hicbiri HYPOTHESIS")
        print("statusune yukseltilemez -- hepsi SPECULATION seviyesinde kaliyor.")
    else:
        for h in hypothesis_register:
            print(h)

    out = {
        "search_budget_m_generation": M_GENERATION,
        "m_existing": M_EXISTING,
        "m_total": M_TOTAL,
        "bonferroni_t_threshold": round(T_THRESHOLD, 4),
        "discovery_note": DISCOVERY_NOTE,
        "search_log": search_log,
        "hypothesis_register": hypothesis_register,
        "n_total_fade_obs": len(fade),
        "n_total_days": int(fade["date"].nunique()),
    }
    Path("data/backtest_out/hgen_h3_fade_2026-09-03.json").write_text(
        json.dumps(out, indent=2, default=str), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
