"""Saglayici kiyaslamasi: Alpaca vs EODHD vs yfinance (2026-09-21).

AYNI sembol listesi, AYNI zaman dilimleri, UC saglayici, yan yana olculur.

KRITIK TASARIM NOTU — HIZ TEK BASINA ANLAMSIZDIR:
  Bos donen bir saglayici "2 saniyede bitti" diye kazanmis gorunur. Bu yuzden
  her olcumde SURE ve KAPSAM birlikte raporlanir. Alpaca'nin bilinen sorunu tam
  da budur: 1d'de kusursuz, 15m/1h'te kucuk/orta likiditede bos donuyor
  (kanit: 321 tarama kaydinda alpaca_miss deseni).
  Karar verirken bakilacak sutun "sure" degil, "yeterli-bar orani".

NE YAPMAZ:
  - Uretim davranisini DEGISTIRMEZ. Hicbir dosya yazmaz (rapor disinda).
  - Bayrak/.env/cache/scheduler'a dokunmaz.
  - Uretimin kullandigi GERCEK kod yollarini cagirir (yeniden yazmaz) —
    olculen sey uretimin gercekte yaptigi istir.

NEREDE KOSULMALI:
  finpilot_api konteynerinin ICINDE. Kimlik bilgileri ve paketler orada.
    docker exec -it finpilot_api python scripts/provider_benchmark.py

KULLANIM:
    python scripts/provider_benchmark.py                  # varsayilan 40 sembol
    python scripts/provider_benchmark.py AAPL MSFT PLTR   # belirli semboller
    python scripts/provider_benchmark.py --rounds 3       # tur sayisi (varsayilan 3)
    python scripts/provider_benchmark.py --rounds 1 --skip-yfinance  # yalnizca Alpaca/EODHD

API anahtari asla yazdirilmaz.
"""

from __future__ import annotations

import statistics
import sys
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

# Mega-cap + orta + kucuk karisimi. Asil ayrim kucuklerde ortaya cikar:
# Alpaca'nin IEX beslemesi orada gun ici bar tasimiyor.
_DEFAULT_SYMBOLS = [
    "AAPL",
    "MSFT",
    "NVDA",
    "GOOGL",
    "META",
    "AMZN",
    "TSLA",
    "AMD",
    "JPM",
    "XOM",
    "JNJ",
    "PG",
    "KO",
    "DIS",
    "BA",
    "CAT",
    "PLTR",
    "SOFI",
    "RIOT",
    "MARA",
    "LCID",
    "CHPT",
    "OPEN",
    "AFRM",
    "BBAI",
    "IONQ",
    "RKLB",
    "ASTS",
    "SOUN",
    "GME",
    "AMC",
    "CLOV",
    "WULF",
    "CIFR",
    "HIVE",
    "BTBT",
    "GEVO",
    "FCEL",
    "PLUG",
    "NKLA",
]

# (interval, days) — uretimin DEFAULT_TIMEFRAMES'i ile ayni mantik
_TIMEFRAMES = [("15m", 10), ("1h", 15), ("1d", 300)]


def _fmt(v: float) -> str:
    return f"{v:7.2f}"


def _covered_set(frames: dict, interval: str, min_bars: dict) -> set:
    """Yeterli bar getiren SEMBOLLERIN kumesi (sayisi degil, kimligi).

    Kesisim/birlesim hesabi icin kimlik sart: iki saglayici AYNI sembolleri mi
    kaciriyor, yoksa birbirini tamamliyor mu? Faz 5R'nin gercek getirisi buna
    bagli — yalnizca sayilara bakmak bu soruyu cevaplayamaz.
    """
    need = min_bars.get(interval, 1)
    out = set()
    for sym, df in frames.items():
        try:
            if df is not None and len(df) >= need:
                out.add(sym)
        except Exception:  # noqa: BLE001
            pass
    return out


def _coverage(frames: dict, interval: str, min_bars: dict) -> tuple[int, int]:
    """(yeterli_bar_sayisi, toplam) — 'yeterli' uretimdeki esikle ayni."""
    return len(_covered_set(frames, interval, min_bars)), len(frames)


def main(argv: list[str]) -> int:
    rounds = 3
    args = list(argv[1:])
    skip_yfinance = "--skip-yfinance" in args
    if skip_yfinance:
        args.remove("--skip-yfinance")
    if "--rounds" in args:
        i = args.index("--rounds")
        try:
            rounds = int(args[i + 1])
            del args[i : i + 2]
        except Exception:  # noqa: BLE001
            print("HATA: --rounds sayisal olmali")
            return 2
    symbols = [s.upper() for s in args] or _DEFAULT_SYMBOLS

    from scanner.data_fetcher import (
        MIN_HISTORY_BARS,
        _bulk_eodhd_intraday,
        _bulk_yf_download,
        _prefetch_alpaca_bulk,
        alpaca_disabled,
        eodhd_bars_enabled,
    )

    print("=" * 74)
    print("SAGLAYICI KIYASLAMASI — Alpaca / EODHD / yfinance")
    print("=" * 74)
    print(
        f"Sembol: {len(symbols)}  Tur: {rounds}  Zaman dilimleri: "
        f"{', '.join(iv for iv, _ in _TIMEFRAMES)}"
    )
    print(f"Python: {sys.executable}")

    # Ortam durumu — deger degil, VARLIK bilgisi
    import os

    print("\n[ORTAM]")
    print(f"  ALPACA_API_KEY       : {'var' if os.environ.get('ALPACA_API_KEY') else 'YOK'}")
    print(f"  EODHD_API_KEY        : {'var' if os.environ.get('EODHD_API_KEY') else 'YOK'}")
    print(f"  FINPILOT_DISABLE_ALPACA : {os.environ.get('FINPILOT_DISABLE_ALPACA', '0')}")
    print(f"  FINPILOT_ENABLE_EODHD_BARS: {os.environ.get('FINPILOT_ENABLE_EODHD_BARS', '0')}")
    try:
        import alpaca

        print(f"  alpaca paketi        : {getattr(alpaca, '__version__', 'bilinmiyor')}")
    except Exception:  # noqa: BLE001
        print("  alpaca paketi        : YOK")

    if alpaca_disabled():
        print("\n  UYARI: FINPILOT_DISABLE_ALPACA=1 — Alpaca olcumu ANLAMSIZ olur.")
        print("         Adil kiyas icin bayraksiz kos.")
    if not eodhd_bars_enabled():
        print("\n  NOT: FINPILOT_ENABLE_EODHD_BARS kapali. Bu script EODHD'yi")
        print("       DOGRUDAN cagirir, yani bayraktan bagimsiz olcum yapar.")
        print("       (Bayrak yalnizca uretim zincirini etkiler.)")

    results: dict[str, dict[str, list]] = {}
    # saglayici -> interval -> kapsanan sembol KUMESI (son turdan)
    covered: dict[str, dict[str, set]] = {"alpaca": {}, "eodhd": {}, "yfinance": {}}

    # ── Alpaca (tek cagri ile TUM zaman dilimleri) ────────────────────────
    print("\n[ALPACA] uretimdeki _prefetch_alpaca_bulk() cagriliyor...")
    alp_times: list[float] = []
    alp_cov: dict[str, tuple[int, int]] = {}
    for r in range(rounds):
        t0 = time.perf_counter()
        res = _prefetch_alpaca_bulk(symbols, _TIMEFRAMES, with_indicators=False)
        dt = time.perf_counter() - t0
        alp_times.append(dt)
        if res is None:
            print(f"  tur {r+1}: {_fmt(dt)} sn — None dondu (Alpaca yolu devre disi/basarisiz)")
        else:
            for interval, _ in _TIMEFRAMES:
                frames = {s: res.get(s, {}).get(interval) for s in symbols}
                alp_cov[interval] = _coverage(frames, interval, MIN_HISTORY_BARS)
                covered["alpaca"][interval] = _covered_set(frames, interval, MIN_HISTORY_BARS)
            cov_txt = "  ".join(
                f"{iv}:{alp_cov.get(iv, (0,0))[0]}/{len(symbols)}" for iv, _ in _TIMEFRAMES
            )
            print(f"  tur {r+1}: {_fmt(dt)} sn — kapsam {cov_txt}")
    results["alpaca"] = {"times": alp_times, "cov": alp_cov}

    # ── EODHD (yalnizca gun ici; 1d icin zincir baglanmamis — K8) ─────────
    print("\n[EODHD] _bulk_eodhd_intraday() cagriliyor (15m 5m'den turetilir)...")
    eod_times: list[float] = []
    eod_cov: dict[str, tuple[int, int]] = {}
    for r in range(rounds):
        t0 = time.perf_counter()
        per_tf = {}
        for interval, days in _TIMEFRAMES:
            if interval == "1d":
                continue  # EODHD 1d yolu uretim zincirine BAGLI DEGIL (bulk_eod kullanilmiyor)
            per_tf[interval] = _bulk_eodhd_intraday(symbols, interval, days, with_indicators=False)
        dt = time.perf_counter() - t0
        eod_times.append(dt)
        for interval, frames in per_tf.items():
            eod_cov[interval] = _coverage(frames, interval, MIN_HISTORY_BARS)
            covered["eodhd"][interval] = _covered_set(frames, interval, MIN_HISTORY_BARS)
        cov_txt = "  ".join(f"{iv}:{eod_cov.get(iv, (0,0))[0]}/{len(symbols)}" for iv in per_tf)
        print(f"  tur {r+1}: {_fmt(dt)} sn — kapsam {cov_txt}   (1d: zincire bagli degil)")
    results["eodhd"] = {"times": eod_times, "cov": eod_cov}

    # ── yfinance (toplu) ──────────────────────────────────────────────────
    yf_times: list[float] = []
    yf_cov: dict[str, tuple[int, int]] = {}
    if skip_yfinance:
        print("\n[YFINANCE] atlandi (--skip-yfinance)")
    else:
        print("\n[YFINANCE] _bulk_yf_download() cagriliyor...")
        for r in range(rounds):
            t0 = time.perf_counter()
            per_tf = {}
            for interval, days in _TIMEFRAMES:
                per_tf[interval] = _bulk_yf_download(symbols, interval, days, with_indicators=False)
            dt = time.perf_counter() - t0
            yf_times.append(dt)
            for interval, frames in per_tf.items():
                yf_cov[interval] = _coverage(frames, interval, MIN_HISTORY_BARS)
            cov_txt = "  ".join(
                f"{iv}:{yf_cov.get(iv, (0,0))[0]}/{len(symbols)}" for iv, _ in _TIMEFRAMES
            )
            print(f"  tur {r+1}: {_fmt(dt)} sn — kapsam {cov_txt}")
    results["yfinance"] = {"times": yf_times, "cov": yf_cov}

    # ── Ozet ──────────────────────────────────────────────────────────────
    print("\n" + "=" * 74)
    print("OZET — medyan sure ve YETERLI-BAR kapsami")
    print("=" * 74)
    print(f"{'Saglayici':<12} {'medyan sn':>10} {'min':>8} {'max':>8}   kapsam (yeterli/toplam)")
    for name in ("alpaca", "eodhd", "yfinance"):
        t = results[name]["times"]
        cov = results[name]["cov"]
        if not t:
            continue
        cov_txt = "  ".join(
            f"{iv}:{cov.get(iv, (0, 0))[0]}/{len(symbols)}"
            for iv in ("15m", "1h", "1d")
            if iv in cov
        )
        print(
            f"{name:<12} {statistics.median(t):>10.2f} {min(t):>8.2f} {max(t):>8.2f}   {cov_txt or '-'}"
        )

    # ── KESISIM / BIRLESIM — FAZ 5R'nin gercek getirisini belirleyen sayi ──
    print("\n" + "=" * 74)
    print("ALPACA + EODHD BIRLESIMI (zincirin gercek kapsami)")
    print("=" * 74)
    print("Soru: iki saglayici AYNI sembolleri mi kaciriyor, yoksa tamamliyor mu?")
    print("Zincir Alpaca -> EODHD kuruldugunda yfinance'e DUSECEK sembol sayisi budur.\n")
    n = len(symbols)
    all_syms = set(symbols)
    for interval in ("15m", "1h"):
        a = covered["alpaca"].get(interval)
        e = covered["eodhd"].get(interval)
        if a is None or e is None:
            print(f"  {interval:4} : olculemedi (bir saglayici tamamlanmadi)")
            continue
        union = a | e
        inter = a & e
        only_e = e - a  # EODHD'nin Alpaca bosluguna KATTIGI
        neither = all_syms - union  # zincir sonrasi HALA yfinance'e dusecekler
        print(f"  {interval}:")
        print(f"    Alpaca                   : {len(a):3}/{n}")
        print(f"    EODHD                    : {len(e):3}/{n}")
        print(f"    ikisi de (kesisim)       : {len(inter):3}")
        print(f"    EODHD'nin EKLEDIGI       : {len(only_e):3}  <- zincirin net kazanci")
        print(f"    BIRLESIM                 : {len(union):3}/{n}  ({100*len(union)/n:.1f}%)")
        print(f"    HICBIRI -> yfinance      : {len(neither):3}  <- kalan repair yuku")
    print("\n  YORUM: 'HICBIRI' satiri kucukse zincir yfinance'i pratikte devre disi")
    print("  birakir ve FAZ 5R tam kazanc verir. Buyukse repair maliyeti SURER ve")
    print("  beklenen iyilesme orantili olarak azalir.")

    print("\nYORUM KURALI:")
    print("  Once KAPSAM sutununa bak. Dusuk kapsamli bir saglayicinin dusuk suresi")
    print("  bir kazanim degil, isin yapilmamis olmasidir. Yalnizca kapsami denk olan")
    print("  saglayicilar sure uzerinden kiyaslanabilir.")
    print("\nNOT: Bu olcum tek seferliktir ve ag kosullarina duyarlidir.")
    print("     Karar icin tek basina yeterli degildir; FAZ 3R'nin serpistirilmis")
    print("     tasarimi ile birlikte degerlendirilmelidir.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
