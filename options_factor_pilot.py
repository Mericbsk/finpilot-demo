#!/usr/bin/env python3
"""
options_factor_pilot.py — YENİ-BİLGİ pilotu: EODHD opsiyon verisinden faktör türet,
edge_recheck dürüst-metriğiyle IS/OOS test et. (Roadmap v2, P1 yeni-veri.)

Hipotez: teknik faktörler tükendi (IC~0). Opsiyon verisi (positioning/IV/put-call)
fiyat-hacimden türetilemeyen YENİ bilgi taşır → gerçek edge potansiyeli.

Türetilen faktörler (as-of scan_date, underlying başına):
  put_call_oi   : Σput OI / Σcall OI        (crowd positioning)
  put_call_vol  : Σput hacim / Σcall hacim
  atm_iv        : ATM implied vol (spot'a en yakın kontratlar medyanı)
  iv_skew       : ATM put IV − ATM call IV   (korku/talep asimetrisi)
  total_oi/vol  : toplam açık pozisyon / hacim (ilgi)

AKIŞ (local; ağ + EODHD UnicornBay opsiyon eklentisi gerekir):
  1) python options_factor_pilot.py --probe AAPL     # canlı şemayı gör, FIELD_MAP'i teyit et
  2) python options_factor_pilot.py --build --limit 300   # resumable fetch→faktör
  3) python options_factor_pilot.py --analyze        # IS/OOS rank-IC (edge_recheck ile)

Sandbox'ta ağ yok → build burada çalışmaz; --analyze sentetik/hazır CSV ile test edilebilir.
NOT: alan adları ilk --probe çıktısıyla DOĞRULANMALI (aşağıdaki FIELD_MAP'i güncelle).
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import statistics
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

EDGE = "data/backtest_out/edge_recheck.csv"  # honest c2c5_net kaynağı (symbol, scan_date)
PRICE_DIR = "data/price_cache"
OUT = "data/backtest_out/options_factors.csv"

# ── Alan adı eşlemesi — İLK --probe SONRASI TEYİT ET/GÜNCELLE ────────────────
FIELD_MAP = {
    "type": ["type", "option_type", "cp_flag", "side"],  # 'call'/'put'
    "strike": ["strike", "strike_price"],
    "oi": ["open_interest", "openinterest", "oi"],
    "volume": ["volume", "vol"],
    "iv": ["implied_volatility", "iv", "impliedvolatility"],
    "exp": ["exp_date", "expiration", "expiration_date", "expdate"],
}


def _pick(d: dict, keys: list[str]):
    for k in keys:
        if k in d and d[k] not in (None, ""):
            return d[k]
    return None


def _is_put(v) -> bool | None:
    s = str(v).lower()
    if s.startswith("p"):
        return True
    if s.startswith("c"):
        return False
    return None


def spot_on(sym: str, d: str):
    p = f"{PRICE_DIR}/{sym}.json"
    if not os.path.exists(p):
        return None
    try:
        b = sorted(json.load(open(p)), key=lambda x: x["date"])
    except Exception:
        return None
    prior = [x for x in b if x["date"] <= d]
    return prior[-1]["close"] if prior else None


def derive_factors(contracts: list[dict], spot: float | None) -> dict | None:
    """Kontrat listesinden (bir underlying, bir gün) faktör satırı türet."""
    puts_oi = calls_oi = puts_vol = calls_vol = 0.0
    ivs_atm_put: list[float] = []
    ivs_atm_call: list[float] = []
    ivs_atm: list[float] = []
    tot_oi = tot_vol = 0.0
    for c in contracts:
        put = _is_put(_pick(c, FIELD_MAP["type"]))
        if put is None:
            continue
        oi = float(_pick(c, FIELD_MAP["oi"]) or 0)
        vol = float(_pick(c, FIELD_MAP["volume"]) or 0)
        iv = _pick(c, FIELD_MAP["iv"])
        strike = _pick(c, FIELD_MAP["strike"])
        tot_oi += oi
        tot_vol += vol
        if put:
            puts_oi += oi
            puts_vol += vol
        else:
            calls_oi += oi
            calls_vol += vol
        # ATM bandı: spot'a %5 yakın strike
        if iv is not None and strike is not None and spot:
            try:
                if abs(float(strike) - spot) / spot <= 0.05:
                    ivs_atm.append(float(iv))
                    (ivs_atm_put if put else ivs_atm_call).append(float(iv))
            except (TypeError, ValueError):
                pass
    if tot_oi == 0 and tot_vol == 0:
        return None
    return {
        "put_call_oi": round(puts_oi / calls_oi, 4) if calls_oi else None,
        "put_call_vol": round(puts_vol / calls_vol, 4) if calls_vol else None,
        "atm_iv": round(statistics.median(ivs_atm), 4) if ivs_atm else None,
        "iv_skew": round(statistics.median(ivs_atm_put) - statistics.median(ivs_atm_call), 4)
        if ivs_atm_put and ivs_atm_call
        else None,
        "total_oi": int(tot_oi),
        "total_vol": int(tot_vol),
    }


def probe(symbol: str):
    from data.eodhd_client import options_eod

    rows = options_eod(symbol, limit=20)
    print(f"probe {symbol}: {len(rows)} kontrat döndü")
    if not rows:
        print("BOŞ → plan opsiyon eklentisini kapsamıyor olabilir ya da endpoint/param farklı.")
        return
    print("ilk kontrat anahtarları:", sorted(rows[0].keys()))
    print("örnek:", json.dumps(rows[0], ensure_ascii=False)[:600])
    print("\n→ Yukarıdaki anahtarlara göre FIELD_MAP'i güncelle, sonra --build.")


def build(limit: int):
    import pandas as pd
    from data.eodhd_client import options_eod

    sig = pd.read_csv(EDGE)[["symbol", "scan_date"]].drop_duplicates()
    done = set()
    exists = os.path.exists(OUT)
    if exists:
        for r in csv.DictReader(open(OUT)):
            done.add((r["symbol"], r["scan_date"]))
    todo = [(s, d) for s, d in sig.itertuples(index=False) if (s, str(d)) not in done]
    print(f"toplam sinyal {len(sig)} | bitmiş {len(done)} | kalan {len(todo)}")
    batch = todo[:limit]
    cols = [
        "symbol",
        "scan_date",
        "put_call_oi",
        "put_call_vol",
        "atm_iv",
        "iv_skew",
        "total_oi",
        "total_vol",
    ]
    fh = open(OUT, "a", newline="", encoding="utf-8")
    w = csv.DictWriter(fh, fieldnames=cols)
    if not exists:
        w.writeheader()
    n = 0
    for sym, d in batch:
        d = str(d)
        contracts = options_eod(sym, date_from=d, date_to=d)
        if not contracts:
            continue
        f = derive_factors(contracts, spot_on(sym, d))
        if not f:
            continue
        w.writerow({"symbol": sym, "scan_date": d, **f})
        n += 1
    fh.close()
    print(f"bu koşuda {len(batch)} sinyal denendi, {n} faktör satırı eklendi → {OUT}")
    print("kalan:", len(todo) - len(batch), "(0 ise --analyze)")


def analyze():
    import pandas as pd

    o = pd.read_csv(OUT)
    e = pd.read_csv(EDGE)[["symbol", "scan_date", "c2c5_net"]]
    m = o.merge(e, on=["symbol", "scan_date"], how="inner").dropna(subset=["c2c5_net"])
    print(f"eşleşen n={len(m)} (opsiyon faktörü + honest getiri)")
    facs = ["put_call_oi", "put_call_vol", "atm_iv", "iv_skew", "total_oi", "total_vol"]
    dates = sorted(m.scan_date.unique())
    cut = dates[len(dates) // 2] if dates else None
    IS, OOS = m[m.scan_date < cut], m[m.scan_date >= cut]

    def ic(sub, f):
        k = sub[f].notna() & sub.c2c5_net.notna()
        return (
            round(sub.loc[k, f].rank().corr(sub.loc[k, "c2c5_net"].rank()), 3)
            if k.sum() >= 30
            else None
        )

    print(f"\n=== OPSİYON FAKTÖRÜ → honest c2c5_net rank-IC (IS<{cut}) ===")
    print(f"{'faktör':14}{'tüm-IC':>9}{'IS-IC':>8}{'OOS-IC':>8}  verdikt")
    for f in facs:
        allic, isic, ooic = ic(m, f), ic(IS, f), ic(OOS, f)
        stable = (
            isic is not None
            and ooic is not None
            and abs(isic) > 0.03
            and (isic > 0) == (ooic > 0)
            and abs(ooic) > 0.02
        )
        print(
            f"{f:14}{str(allic):>9}{str(isic):>8}{str(ooic):>8}  {'✅ stabil-aday' if stable else 'zayıf/tutarsız'}"
        )
    print(
        "\nKural: IS ve OOS aynı işaret + |IC|>~0.03 → gerçek-aday. Değilse elenir (roadmap ilkesi)."
    )


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--probe", metavar="SYMBOL")
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--analyze", action="store_true")
    ap.add_argument("--limit", type=int, default=300)
    a = ap.parse_args()
    if a.probe:
        probe(a.probe)
    elif a.build:
        build(a.limit)
    elif a.analyze:
        analyze()
    else:
        ap.print_help()
