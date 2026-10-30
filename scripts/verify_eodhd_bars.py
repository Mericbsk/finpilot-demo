"""EODHD intraday bar entegrasyonu — yerel doğrulama + hız ölçümü (2026-09-14).

NEDEN: Tarama süresinin ölçülmüş nedeni, Alpaca'nın ücretsiz IEX beslemesinin
15m/1h barlarını vermemesi ve eksiklerin yfinance'ten sembol başına ~2.5 sn'ye
toplanması (kanıt: data/distribution/scan_timing.jsonl). EODHD ücretli
aboneliği bu barları sunuyor. Bu script üç soruyu SIRAYLA cevaplar:

  1) Planımız intraday içeriyor mu?        (1h ve 5m endpoint'i OK mi)
  2) Barlar scanner'ın beklediği şekle uyuyor mu?  (kolon/index/bar sayısı)
  3) yfinance'e göre gerçekten hızlı mı?   (aynı semboller, yan yana ölçüm)

Kullanım:
    python scripts/verify_eodhd_bars.py
    python scripts/verify_eodhd_bars.py AAPL MSFT PLTR SOFI RIOT

API anahtarını asla yazdırmaz. Sadece okuma yapar; hiçbir dosyayı değiştirmez.
Not: intraday çağrıları EODHD kotasından ~5 kredi/çağrı harcar.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

# Varsayılan test seti: 2 mega-cap (IEX'te bar VAR) + 3 küçük/orta
# (IEX'te genelde bar YOK — asıl darboğazı temsil ederler).
_DEFAULT_SYMBOLS = ["AAPL", "MSFT", "PLTR", "SOFI", "RIOT"]


def _load_env() -> None:
    """.env'i içe aktar (python-dotenv yoksa elle oku)."""
    if os.getenv("EODHD_API_KEY"):
        return
    env = _ROOT / ".env"
    if not env.exists():
        return
    for line in env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def step1_plan_check() -> bool:
    """Plan intraday içeriyor mu?"""
    print("\n[1/3] PLAN KONTROLU — EODHD intraday erisimi")
    print("-" * 62)
    from data.eodhd_client import get_client

    client = get_client()
    ok_any = False
    for interval in ("1h", "5m"):
        t0 = time.perf_counter()
        rows = client.intraday("AAPL", interval=interval, days=5)
        dt = time.perf_counter() - t0
        if rows:
            ok_any = True
            print(f"  intraday {interval:3} : OK    ({len(rows)} bar, {dt:.2f} sn)")
        else:
            print(f"  intraday {interval:3} : BOS   ({dt:.2f} sn)")
            print("      -> plan kapsam disi (402/403) VEYA gecici hata olabilir.")
            print("      -> ayrinti icin: python scripts/probe_eodhd.py")
    return ok_any


def step2_shape_check() -> bool:
    """Barlar scanner'in bekledigi sekilde mi?"""
    print("\n[2/3] SEKIL KONTROLU — scanner sozlesmesine uygunluk")
    print("-" * 62)
    from scanner.data_fetcher import MIN_HISTORY_BARS, _eodhd_one

    all_ok = True
    for interval, days in (("1h", 15), ("15m", 10)):
        df = _eodhd_one("AAPL", interval, days, with_indicators=True)
        need = MIN_HISTORY_BARS[interval]
        if df.empty:
            print(f"  {interval:4} : BOS DataFrame — BASARISIZ")
            all_ok = False
            continue
        cols = [c for c in ("Open", "High", "Low", "Close", "Volume") if c in df.columns]
        enough = len(df) >= need
        tz_ok = getattr(df.index, "tz", None) is None
        note = "15m <- 5m'den turetildi" if interval == "15m" else "dogrudan"
        print(
            f"  {interval:4} : {len(df):5} bar (min {need}) | OHLCV {len(cols)}/5 | "
            f"tz-naive {tz_ok} | {note}"
        )
        if not (enough and len(cols) == 5 and tz_ok):
            all_ok = False
            print("      -> UYUMSUZ")
    return all_ok


def step3_speed_test(symbols: list[str]) -> None:
    """EODHD vs yfinance — ayni semboller, yan yana."""
    print("\n[3/3] HIZ KARSILASTIRMASI — EODHD vs yfinance")
    print("-" * 62)
    from scanner.data_fetcher import _bulk_eodhd_intraday, _bulk_yf_download

    interval, days = "1h", 15
    print(f"  {len(symbols)} sembol x {interval} ({days} gun): {', '.join(symbols)}")

    t0 = time.perf_counter()
    eod = _bulk_eodhd_intraday(symbols, interval, days, with_indicators=True)
    t_eod = time.perf_counter() - t0
    n_eod = sum(1 for d in eod.values() if not d.empty)

    t0 = time.perf_counter()
    yfr = _bulk_yf_download(symbols, interval, days, with_indicators=True)
    t_yf = time.perf_counter() - t0
    n_yf = sum(1 for d in yfr.values() if not d.empty)

    print(f"\n  EODHD    : {t_eod:6.2f} sn  ({n_eod}/{len(symbols)} sembol doldu)")
    print(f"  yfinance : {t_yf:6.2f} sn  ({n_yf}/{len(symbols)} sembol doldu)")
    if t_eod > 0 and t_yf > 0:
        if t_eod < t_yf:
            print(f"  -> EODHD {t_yf / t_eod:.1f}x HIZLI")
        else:
            print(f"  -> yfinance {t_eod / t_yf:.1f}x hizli (beklenmedik — nedenini arastir)")
    print("\n  NOT: Bu kucuk bir orneklem. Asil kazanc tam evrende, cunku yfinance")
    print("       maliyeti EKSIK sembol sayisiyla dogrusal buyuyor (~2.5 sn/sembol).")


def main(argv: list[str]) -> int:
    _load_env()
    symbols = [s.upper() for s in argv[1:]] or _DEFAULT_SYMBOLS

    if not os.getenv("EODHD_API_KEY", "").strip():
        print("HATA: EODHD_API_KEY bulunamadi (env veya .env).")
        return 2

    print("=" * 62)
    print("EODHD INTRADAY BAR DOGRULAMA")
    print("=" * 62)

    if not step1_plan_check():
        print("\nSONUC: Plan intraday vermiyor gorunuyor. Entegrasyon kodu hazir ama")
        print("       acilmamali. Once EODHD panelinden plan kapsamini teyit et.")
        return 1

    shape_ok = step2_shape_check()
    step3_speed_test(symbols)

    print("\n" + "=" * 62)
    if shape_ok:
        print("SONUC: Entegrasyon calisiyor. Acmak icin .env'e ekle:")
        print("       FINPILOT_ENABLE_EODHD_BARS=1")
        print("Sonra bir tarama kosup data/distribution/scan_timing.jsonl'de")
        print("yf_fallback sayisinin dustugunu dogrula.")
    else:
        print("SONUC: Erisim VAR ama bar sekli uyumsuz — acmadan once duzeltilmeli.")
    print("=" * 62)
    return 0 if shape_ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
