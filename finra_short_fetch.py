#!/usr/bin/env python3
"""
FINRA TARIHSEL SHORT + NOKTA-ZAMANLI SQUEEZE DOGRULAMASI
========================================================
Simdiye kadar squeeze'i GUNCEL short ile olctuk (look-ahead riski). Bu script
FINRA'nin bi-weekly (settlement tarihli) tarihsel short-interest verisini ceker,
her sinyale O TARIHTEKI gercek short'u esler ve squeeze edge'ini (short>=20 +
ATR>=4) NOKTA-ZAMANLI olarak yeniden test eder.

Kaynak: FINRA Query API (bedava, anahtarsiz)
  https://api.finra.org/data/group/otcMarket/name/consolidatedShortInterest
  short% = currentShortPositionQuantity / floatShares   (float enriched CSV'den)

Kullanim:
  pip install requests
  python finra_short_fetch.py
Ciktinin TAMAMINI Claude'a yapistir.
"""

import csv
import json
import os
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
CSVP = os.path.join(ROOT, "data", "backtest_out", "enriched_signals_v2.csv")
CACHE = os.path.join(ROOT, "data", "finra_cache")
os.makedirs(CACHE, exist_ok=True)
try:
    import requests
except ImportError:
    raise SystemExit("pip install requests")

URL = "https://api.finra.org/data/group/otcMarket/name/consolidatedShortInterest"


def ff(x):
    try:
        return float(x)
    except:
        return None


_printed_keys = [False]


def fetch_finra(sym):
    cf = os.path.join(CACHE, f"{sym}.json")
    if os.path.exists(cf):
        try:
            return json.load(open(cf))
        except Exception:
            pass
    recs = []
    # 1) POST JSON (modern FINRA Query API) — symbol filtresiyle
    try:
        payload = {
            "limit": 5000,
            "offset": 0,
            "compareFilters": [
                {"compareType": "EQUAL", "fieldName": "symbolCode", "fieldValue": sym}
            ],
        }
        r = requests.post(
            URL,
            json=payload,
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            timeout=30,
        )
        if r.status_code == 200:
            data = r.json()
            rows = data if isinstance(data, list) else data.get("data", data.get("results", []))
            if rows and not _printed_keys[0]:
                print("  [FINRA alan adlari]:", list(rows[0].keys()))
                _printed_keys[0] = True
            for x in rows:
                d = (
                    x.get("settlementDate")
                    or x.get("SettlementDate")
                    or x.get("accountingYearMonthNumber")
                )
                q = x.get("currentShortPositionQuantity") or x.get("CurrentShortPositionQuantity")
                if d and q is not None:
                    d = str(d)
                    if len(d) == 6 and d.isdigit():
                        d = f"{d[:4]}-{d[4:]}-15"  # YYYYMM -> ortalama
                    recs.append((d[:10], ff(q)))
    except Exception as ex:
        if not _printed_keys[0]:
            print("  [FINRA POST hata]", repr(ex)[:80])
    recs = sorted(set(recs))
    json.dump(recs, open(cf, "w"))
    time.sleep(0.15)
    return recs


def pit_short(hist, sig_date, float_shares):
    """sinyal tarihinden ONCEKI en yakin settlement short'u -> short%."""
    if not hist or not float_shares or float_shares <= 0:
        return None
    prior = [q for d, q in hist if d <= sig_date and q is not None]
    if not prior:
        return None
    short_shares = prior[-1]
    return short_shares / float_shares * 100.0


def main():
    rows = [r for r in csv.DictReader(open(CSVP)) if ff(r.get("resolved_pct_t5")) is not None]
    syms = sorted({r["symbol"] for r in rows})
    print(f"Sinyal: {len(rows)}  sembol: {len(syms)}  (FINRA bi-weekly cekiliyor...)")
    hist = {}
    empty = 0
    for i, s in enumerate(syms, 1):
        hist[s] = fetch_finra(s)
        if not hist[s]:
            empty += 1
        if i % 50 == 0:
            print(f"  {i}/{len(syms)}...")
    print(f"FINRA verisi bos donen sembol: {empty}/{len(syms)}")
    if empty == len(syms):
        print(
            "!! Hicbir sembolde FINRA verisi yok — istek formati/erisim sorunu. Yukaridaki alan/hata satirina bak."
        )
        return

    # PIT short ekle
    cov = 0
    for r in rows:
        ps = pit_short(hist.get(r["symbol"], []), r["signal_date"][:10], ff(r.get("float_shares")))
        r["short_pit"] = ps
        if ps is not None:
            cov += 1
    print(f"Nokta-zamanli short kapsami: {cov}/{len(rows)}")

    def rate(sub, thr):
        return sum(1 for r in sub if ff(r["resolved_pct_t5"]) >= thr) / len(sub) if sub else 0

    base5 = rate(rows, 5)
    base10 = rate(rows, 10)
    print(f"\nBaz oran: >=5% {base5*100:.1f}%  >=10% {base10*100:.1f}%")

    def seg(name, cond):
        sub = [r for r in rows if cond(r)]
        if len(sub) < 30:
            print(f"  {name}: n={len(sub)} (yetersiz)")
            return
        h5 = rate(sub, 5)
        h10 = rate(sub, 10)
        print(
            f"  {name:32s} n={len(sub):>4} >=5%:{h5*100:5.1f}%(lift {h5/base5 if base5 else 0:.2f})  >=10%:{h10*100:5.1f}%(lift {h10/base10 if base10 else 0:.2f})"
        )

    at = lambda r: (ff(r.get("atr_pct")) or 0)
    sp = lambda r: (r.get("short_pit") if r.get("short_pit") is not None else -1)
    print(
        "\n=== NOKTA-ZAMANLI SHORT ile SQUEEZE (karsilastir: guncel short short>=20 lift 2.57 idi) ==="
    )
    seg("short_pit>=15%", lambda r: sp(r) >= 15)
    seg("short_pit>=20%", lambda r: sp(r) >= 20)
    seg("short_pit>=20% + ATR>=4", lambda r: sp(r) >= 20 and at(r) >= 4)
    seg("short_pit>=30%", lambda r: sp(r) >= 30)

    # walk-forward
    IS = [r for r in rows if r["signal_date"][:10] < "2026-01-01"]
    OOS = [r for r in rows if r["signal_date"][:10] >= "2026-01-01"]

    def wf(sub, cond, tag):
        s = [r for r in sub if cond(r)]
        if len(s) < 30:
            print(f"    {tag}: n={len(s)} yetersiz")
            return
        b = rate(sub, 10)
        h = rate(s, 10)
        print(
            f"    {tag}: n={len(s)} >=10% hit {h*100:.1f}% baz {b*100:.1f}% lift {h/b if b else 0:.2f}"
        )

    print("\n  --- walk-forward (short_pit>=20 + ATR>=4, >=10%) ---")
    wf(IS, lambda r: sp(r) >= 20 and at(r) >= 4, "IS 2025")
    wf(OOS, lambda r: sp(r) >= 20 and at(r) >= 4, "OOS 2026")
    print("\n>>> Nokta-zamanli lift, guncel-short lift'e YAKINSA edge gercek (look-ahead degil).")
    print(">>> Belirgin DUSUKSE, guncel short kismen look-ahead tasiyordu demektir.")
    # v3 yaz
    keys = list(rows[0].keys())
    with open(
        os.path.join(ROOT, "data", "backtest_out", "enriched_signals_v3.csv"), "w", newline=""
    ) as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print("\nYazildi: data/backtest_out/enriched_signals_v3.csv (short_pit eklendi)")
    print("Bu ciktinin TAMAMINI Claude'a yapistir.")


if __name__ == "__main__":
    main()
