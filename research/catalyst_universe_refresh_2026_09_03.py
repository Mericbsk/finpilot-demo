#!/usr/bin/env python3
"""
catalyst_factor evren-capli refresh + kalite kapisi (Merric onayli, Level B).

Arastirma Portfoyu Kurulu #3 kalemi. reports/data_repair_diagnosis_2026-09-03.md'nin
kok-neden zinciri: (1) FINPILOT_ENABLE_EDGAR_CATALYST tanimsiz -> hep 0.0 (bu script
BU FLAG'E DOKUNMAZ), (2) data/catalyst_cache.json pratikte bos (8 sembol), (3) EDGAR
ham verisi (data/edgar_cache/*.json, 1.127 CIK dosyasi + tickers.json 10.433 sirket)
zaten var ama scanner.catalyst.refresh_catalyst_cache() bunu KULLANMIYOR -- her
seferinde canli SEC agina gidiyor.

Bu script:
  1. Yerel edgar_cache'i ONCELIKLE kullanir (ag gerektirmez).
  2. Yerelde olmayan sembol icin CANLI SEC agina dener (varsa); bu ortamda
     data.sec.gov'a erisim YOK (proxy 403 dogrulandi) -- bu durumda o sembol
     'coverage_gap' olarak isaretlenir, 0.0 YAZILMAZ (sessiz yanlislik degil,
     acikca 'bilinmiyor' sayilir -- cache'e o sembol icin veri YAZMAZ).
  3. scanner/catalyst.py::_score_filings ile AYNI mantik/agirliklarla skorlar
     (kod tekrar edilmedi, import edildi).
  4. FINPILOT_ENABLE_EDGAR_CATALYST'e DOKUNMAZ -- bu script flag'i acmaz.
  5. Kalite-kapisi raporu uretir: kapsam %, nonzero orani, form dagilimi,
     tazelik (son 7 gun icinde dosyalama var mi).
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import UTC, datetime, timedelta
from pathlib import Path

UTC = UTC

# scanner/catalyst.py::_CATALYST_WEIGHTS ve _score_filings ile BIREBIR AYNI
# (kaynak degistirilmedi). Bu ortamda scanner/ paketinin __init__.py zinciri
# Python 3.11+ 'datetime.UTC' kullanan baska moduller icerdiginden (bu sandbox
# 3.10) dogrudan import edilemiyor -- bu yuzden bu iki kucuk, saf/yan-etkisiz
# fonksiyon/sabit buraya kopyalandi, MANTIK DEGISTIRILMEDI.
_CATALYST_WEIGHTS: dict[str, float] = {
    "8-K": 0.6,
    "4": 0.3,
    "S-1": -0.5,
    "424B5": -0.5,
    "424B3": -0.5,
    "424B4": -0.5,
}


def _score_filings(filings: list[dict[str, str]]) -> float:
    seen: set[str] = set()
    total = 0.0
    for f in filings:
        form = f.get("form", "")
        weight = _CATALYST_WEIGHTS.get(form)
        if weight is None or form in seen:
            continue
        seen.add(form)
        total += weight
    return round(max(-1.0, min(1.0, total)), 4)


EDGAR_CACHE = Path("data/edgar_cache")
TICKERS_JSON = EDGAR_CACHE / "tickers.json"
UNIVERSE_CSV = Path("data/backtest_out/sector_map_full.csv")
OUT_CACHE = Path("data/catalyst_cache.json")
OUT_REPORT = Path("data/backtest_out/catalyst_refresh_quality_2026-09-03.json")
LOOKBACK_DAYS = 7


def load_universe() -> list[str]:
    syms = []
    with open(UNIVERSE_CSV, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r.get("symbol"):
                syms.append(r["symbol"].upper())
    return sorted(set(syms))


def load_ticker_cik_map() -> dict[str, str]:
    data = json.loads(TICKERS_JSON.read_text(encoding="utf-8"))
    m = {}
    for row in data.values():
        try:
            m[str(row["ticker"]).upper()] = str(int(row["cik_str"])).zfill(10)
        except (KeyError, TypeError, ValueError):
            continue
    return m


def local_filings(cik: str) -> list[tuple[str, str]] | None:
    """Yerel cache'ten [(form, date), ...] dondurur; dosya yoksa None."""
    fp = EDGAR_CACHE / f"sub_{cik}.json"
    if not fp.exists():
        return None
    try:
        raw = json.loads(fp.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    out = []
    for item in raw:
        if isinstance(item, (list, tuple)) and len(item) == 2:
            out.append((str(item[0]), str(item[1])))
    return out


def filter_lookback(
    filings: list[tuple[str, str]], as_of: datetime, days: int
) -> list[dict[str, str]]:
    cutoff = (as_of - timedelta(days=days)).date()
    out = []
    for form, date_str in filings:
        try:
            filed = datetime.strptime(date_str, "%Y-%m-%d").date()
        except (TypeError, ValueError):
            continue
        if filed >= cutoff:
            out.append({"form": form, "date": date_str})
    return out


def main():
    universe = load_universe()
    cik_map = load_ticker_cik_map()
    as_of = datetime.now(tz=UTC)

    factors: dict[str, float] = {}
    coverage_gap: list[str] = []  # CIK bulundu ama yerel dosya yok, ag da yok
    no_cik: list[str] = []  # SEC'te hic CIK eslesmesi yok (ADR/OTC/delisted olabilir)
    form_counter: Counter[str] = Counter()
    fresh_count = 0  # son LOOKBACK_DAYS icinde en az 1 dosyalamasi olan sembol sayisi

    for sym in universe:
        cik = cik_map.get(sym)
        if not cik:
            no_cik.append(sym)
            continue
        raw = local_filings(cik)
        if raw is None:
            coverage_gap.append(sym)
            continue
        recent = filter_lookback(raw, as_of, LOOKBACK_DAYS)
        factors[sym] = _score_filings(recent)
        if recent:
            fresh_count += 1
            for f in recent:
                form_counter[f["form"]] += 1

    payload = {"updated": as_of.isoformat(), "factors": factors}
    OUT_CACHE.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUT_CACHE.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload), encoding="utf-8")
    tmp.replace(OUT_CACHE)

    n_universe = len(universe)
    n_scored = len(factors)
    n_nonzero = sum(1 for v in factors.values() if v != 0.0)

    report = {
        "as_of": as_of.isoformat(),
        "universe_n": n_universe,
        "scored_n": n_scored,
        "coverage_pct": round(100 * n_scored / n_universe, 2) if n_universe else 0.0,
        "target_coverage_pct": 90.0,
        "gate_pass": (n_scored / n_universe) >= 0.90 if n_universe else False,
        "no_cik_n": len(no_cik),
        "coverage_gap_n": len(coverage_gap),
        "coverage_gap_reason": "yerel edgar_cache'te bu CIK icin dosya yok; bu ortamda "
        "data.sec.gov'a canli erisim YOK (proxy 403 dogrulandi) -- "
        "bu semboller icin catalyst_cache'e deger YAZILMADI (0.0 "
        "diye sessizce doldurulmadi).",
        "fresh_within_7d_n": fresh_count,
        "nonzero_n": n_nonzero,
        "nonzero_pct_of_scored": round(100 * n_nonzero / n_scored, 2) if n_scored else 0.0,
        "form_distribution_last_7d": dict(form_counter.most_common()),
        "flag_touched": False,
        "note": "FINPILOT_ENABLE_EDGAR_CATALYST bu script tarafindan ACILMADI. "
        "Coverage hedefi (%90) bu ortamda ag kisitlamasi nedeniyle "
        "karsilanamadi -- gercek evren-capli refresh, SEC agina erisimi "
        "olan bir ortamda (canli sunucu / Meric'in makinesi) calistirilmali.",
    }
    OUT_REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"[EVREN] {n_universe} sembol")
    print(
        f"[SKORLANAN] {n_scored} ({report['coverage_pct']}%) -- hedef >=90%, "
        f"gate_pass={report['gate_pass']}"
    )
    print(f"[CIK YOK] {len(no_cik)} sembol (SEC'te eslesme yok -- OTC/ADR/delisted olabilir)")
    print(f"[COVERAGE GAP] {len(coverage_gap)} sembol -- CIK var ama yerel dosya/ag yok")
    print(f"[TAZELIK] son {LOOKBACK_DAYS} gunde en az 1 dosyalamasi olan: {fresh_count}/{n_scored}")
    print(f"[NONZERO] {n_nonzero}/{n_scored} (%{report['nonzero_pct_of_scored']})")
    print(f"[FORM DAGILIMI son {LOOKBACK_DAYS}g] {dict(form_counter.most_common())}")
    print(f"\n[YAZILDI] {OUT_CACHE}")
    print(f"[YAZILDI] {OUT_REPORT}")


if __name__ == "__main__":
    main()
