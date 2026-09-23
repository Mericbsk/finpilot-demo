"""Alpaca prefetch: extraction mi, indikatör mü? (2026-09-22)

AMAC: `prefetch.alpaca` suresinin ag-disi kismi (olculmus: 22.9 sn/kosu,
toplamin %64'u) NEREYE gidiyor? Iki aday:
  (a) sembol ayirma dongusu  -> `prefetch.alpaca.extract`
  (b) indikator hesaplama    -> `indicator.compute`

ONCEDEN ILAN EDILEN YORUM (sonuca gore hikaye uydurmamak icin):
  extract >> indicator  -> O(n x bar) teyit; groupby duzeltmesi uygulanir
  extract ~= indicator  -> ikisi de kayda deger; ayri ayri ele alinir
  extract << indicator  -> HIPOTEZ CURUR; dongu sorun degil, asil konu
                           "prefetch sirasinda indikator hesaplamak gerekli mi"

NEDEN AYRI SCRIPT (benchmark degil):
  provider_benchmark.py duvar-saati olcuyor, stage event basmiyor.
  Bu prob yalnizca Alpaca yolunu cagirir ve asama kirilimini dokumektedir.

NEDEN URETIMI ETKILEMEZ:
  - `docker exec` YENI bir surec yaratir: bind mount'tan taze kod, surece ozel env.
  - Calisan uvicorn'a DOKUNULMAZ. Restart/recreate GEREKMEZ.
  - Stage timing yalnizca BU surecte acilir (.env degismez).
  - Salt okuma: hicbir dosya yazilmaz, cache/scheduler/flag degismez.

KULLANIM (konteyner icinde):
    docker exec -w /app finpilot_api python scripts/alpaca_extract_probe.py
    docker exec -w /app finpilot_api python scripts/alpaca_extract_probe.py 40 200 500
"""

from __future__ import annotations

import os
import sys
from collections import defaultdict

# Stage timing'i YALNIZCA bu surec icin ac. performance.enabled() her cagride
# os.getenv okudugu icin import sirasi kritik degil, yine de erken ayarliyoruz.
os.environ["FINPILOT_SCAN_STAGE_TIMING"] = "1"

sys.path.insert(0, "/app" if os.path.isdir("/app") else os.getcwd())

_DEFAULT_SIZES = [40, 200]
_TIMEFRAMES = [("15m", 10), ("1h", 15), ("1d", 300)]


def _aggregate(events: list[dict]) -> dict[str, dict]:
    """stage -> {count, total_s}"""
    agg: dict[str, dict] = defaultdict(lambda: {"count": 0, "total_s": 0.0})
    for ev in events:
        key = ev.get("stage", "?")
        agg[key]["count"] += 1
        agg[key]["total_s"] += float(ev.get("elapsed_s") or 0.0)
    return dict(agg)


def main(argv: list[str]) -> int:
    sizes = [int(a) for a in argv[1:]] or _DEFAULT_SIZES

    from scanner import performance
    from scanner.data_fetcher import _prefetch_alpaca_bulk, alpaca_disabled, load_symbols

    print("=" * 72)
    print("ALPACA PREFETCH PROB — extraction vs indicator")
    print("=" * 72)
    print(f"python          : {sys.executable}")
    print(f"stage timing    : {performance.enabled()}")
    print(f"alpaca_disabled : {alpaca_disabled()}")
    if not performance.enabled():
        print("\nHATA: stage timing acilamadi — olcum yapilamaz.")
        return 2
    if alpaca_disabled():
        print("\nHATA: FINPILOT_DISABLE_ALPACA=1 — Alpaca yolu kapali, olcum anlamsiz.")
        return 2

    rows = []
    for n in sizes:
        symbols = load_symbols(limit=n)
        if len(symbols) != n:
            print(f"\nUYARI: load_symbols(limit={n}) {len(symbols)} sembol dondu — atlaniyor")
            continue

        performance.reset()
        result = _prefetch_alpaca_bulk(symbols, _TIMEFRAMES, with_indicators=True)
        agg = _aggregate(performance.snapshot())

        if result is None:
            print(f"\nN={n}: _prefetch_alpaca_bulk None dondu (Alpaca yolu basarisiz) — atlaniyor")
            continue

        total = agg.get("prefetch.alpaca", {}).get("total_s", 0.0)
        retry = agg.get("retry.attempt", {}).get("total_s", 0.0)
        extract = agg.get("prefetch.alpaca.extract", {}).get("total_s", 0.0)
        indicator = agg.get("indicator.compute", {}).get("total_s", 0.0)
        ind_count = agg.get("indicator.compute", {}).get("count", 0)

        print(f"\n{'-' * 72}\nN = {n}\n{'-' * 72}")
        print(f"  prefetch.alpaca (toplam)   : {total:8.2f} sn")
        print(
            f"    retry.attempt (AG)       : {retry:8.2f} sn  ({100*retry/total if total else 0:5.1f}%)"
        )
        print(
            f"    prefetch.alpaca.extract  : {extract:8.2f} sn  ({100*extract/total if total else 0:5.1f}%)"
        )
        print(
            f"    indicator.compute        : {indicator:8.2f} sn  ({100*indicator/total if total else 0:5.1f}%)  [{ind_count} cagri]"
        )
        accounted = retry + extract
        print(f"    hesaba katilmayan        : {total - accounted:8.2f} sn")
        print("    NOT: indicator.compute extract'in ICINDE olabilir (ic ice timer).")
        print("         Yuzdeler toplami 100'u asabilir — bu beklenen bir durumdur.")

        rows.append((n, total, retry, extract, indicator))

    if len(rows) < 2:
        print("\nOlcekleme karsilastirmasi icin en az iki boyut gerekli.")
        return 0

    print("\n" + "=" * 72)
    print("OLCEKLEME")
    print("=" * 72)
    print(f"{'N':>6} {'toplam':>9} {'ag':>9} {'extract':>9} {'indicator':>10}")
    for n, total, retry, extract, indicator in rows:
        print(f"{n:>6} {total:>9.2f} {retry:>9.2f} {extract:>9.2f} {indicator:>10.2f}")

    (n0, t0, r0, e0, i0), (n1, t1, r1, e1, i1) = rows[0], rows[-1]
    sym_ratio = n1 / n0 if n0 else 0
    print(f"\n  sembol orani        : {sym_ratio:.2f}x")
    for label, a, b in (
        ("toplam", t0, t1),
        ("ag", r0, r1),
        ("extract", e0, e1),
        ("indicator", i0, i1),
    ):
        if a > 0:
            growth = b / a
            shape = (
                "KARESEL?"
                if growth > sym_ratio * 1.5
                else ("dogrusal" if growth > sym_ratio * 0.7 else "alt-dogrusal")
            )
            print(f"  {label:<18}: {growth:5.2f}x  -> {shape}")

    print("\n" + "=" * 72)
    print("ONCEDEN ILAN EDILEN KARAR DALLARI")
    print("=" * 72)
    if not rows:
        return 0
    _, _, _, e_last, i_last = rows[-1]
    if e_last > i_last * 1.5:
        print("  extract >> indicator  -> O(n x bar) TEYIT EDILDI.")
        print("     Sonraki adim: groupby duzeltmesi (Level B), sonra ayni olcum tekrar.")
    elif i_last > e_last * 1.5:
        print("  extract << indicator  -> HIPOTEZ CURUDU.")
        print("     Dongu sorun degil. Asil soru: prefetch sirasinda indikator")
        print("     hesaplamak GEREKLI mi? Ayri tasarim tartismasi.")
    else:
        print("  extract ~= indicator  -> ikisi de kayda deger.")
        print("     Ayri ayri ele alinmali; tek bir duzeltme yetmez.")
    print("\n  Bu dal, olcumden ONCE ilan edildi (script basligi). Sonuca gore")
    print("  yorum degistirilmeyecek.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
