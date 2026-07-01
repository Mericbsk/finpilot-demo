#!/usr/bin/env python3
"""
INTRADAY STOP TESTI (Alpaca) — MAE + stop/TP grid optimizasyonu
================================================================
enriched_signals_v2.csv'deki sinyaller icin sinyal-sonrasi 5 islem gununun
15-dk barlarini ceker, gercek stop-out'u SIMULE eder ve en iyi ATR stop/TP
carpanlarini bulur. Bu, backtest'te veri olmadigi icin yapamadigimiz STOP
tarafinin gercek testidir.

Yaklasim (her sinyal):
  entry E = CSV entry (yoksa ertesi seans ilk 15dk acilisi)
  ATR($) = atr_pct/100 * E
  Grid: stop_mult x tp_mult -> stop=E-sm*ATR, tp=E+tm*ATR
  Barlar sirayla: once low<=stop mu (kayip -sm), yoksa high>=tp mi (kazanc +tm)?
  (Ayni barda ikisi de olursa MUHAFAZAKAR: stop once vuruldu say.)
  Hicbiri olmazsa: son kapanista cik (R cinsinden).
  Metrik: win%, ort R, beklenti (expectancy R), profit factor.

Not: yuk azaltmak icin varsayilan olarak ALPHA_V2-ilgili alt kume (ATR>=3 veya
gap>=3 veya short>=15) ve --limit uygulanir. --all ile hepsi.

Kullanim:
  pip install requests
  python intraday_stop_test.py            # ilgili alt kume, ilk 800
  python intraday_stop_test.py --limit 0  # sinirsiz (yavas)
"""

import argparse
import csv
import datetime as dt
import json
import os
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
CSVP = os.path.join(ROOT, "data", "backtest_out", "enriched_signals_v2.csv")
CACHE = os.path.join(ROOT, "data", "intraday_cache")
os.makedirs(CACHE, exist_ok=True)
try:
    import requests
except ImportError:
    raise SystemExit("pip install requests")


def env():
    e = {}
    p = os.path.join(ROOT, ".env")
    for line in open(p):
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip()] = v.strip().strip('"').strip("'")
    return e


E = env()
KID = E.get("ALPACA_API_KEY", "")
SEC = E.get("ALPACA_SECRET_KEY", "")
if not (KID and SEC):
    raise SystemExit("ALPACA anahtarlari .env'de yok.")


def ff(x):
    try:
        return float(x)
    except:
        return None


def fetch_intraday(sym, start, end):
    cf = os.path.join(CACHE, f"{sym}_{start}_{end}.json")
    if os.path.exists(cf):
        try:
            return json.load(open(cf))
        except Exception:
            pass
    url = f"https://data.alpaca.markets/v2/stocks/{sym}/bars"
    hdr = {"APCA-API-KEY-ID": KID, "APCA-API-SECRET-KEY": SEC}
    out = []
    page = None
    while True:
        params = {
            "timeframe": "15Min",
            "start": start + "T00:00:00Z",
            "end": end + "T23:59:00Z",
            "limit": 10000,
            "adjustment": "raw",
            "feed": "iex",
        }
        if page:
            params["page_token"] = page
        try:
            r = requests.get(url, headers=hdr, params=params, timeout=30)
        except Exception:
            break
        if r.status_code != 200:
            break
        j = r.json()
        for b in j.get("bars", []) or []:
            out.append((b["t"], b["h"], b["l"], b["c"], b["o"]))
        page = j.get("next_page_token")
        if not page:
            break
    json.dump(out, open(cf, "w"))
    time.sleep(0.1)
    return out


def simulate(entry, atr, bars, sm, tm):
    """R cinsinden sonuc: stop once mu tp once mu?"""
    stop = entry - sm * atr
    tp = entry + tm * atr
    for t, h, l, c, o in bars:
        if l <= stop:  # muhafazakar: stop oncelik
            return -sm
        if h >= tp:
            return +tm
    # cikilamadi -> son kapanista
    if bars:
        last_c = bars[-1][3]
        return (last_c - entry) / atr if atr > 0 else 0.0
    return 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=800)
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args()
    rows = list(csv.DictReader(open(CSVP)))

    # ilgili alt kume
    def relevant(r):
        if args.all:
            return True
        return (
            (ff(r.get("atr_pct")) or 0) >= 3
            or (ff(r.get("gap_pct")) or -9) >= 3
            or (ff(r.get("short_pct")) or -1) >= 15
        )

    sel = [r for r in rows if relevant(r) and ff(r.get("entry")) and ff(r.get("atr_pct"))]
    if args.limit > 0:
        sel = sel[: args.limit]
    print(
        f"Test edilecek sinyal: {len(sel)} (alt kume={'hepsi' if args.all else 'ATR>=3/gap>=3/short>=15'})"
    )

    SM = [1.0, 1.5, 2.0, 2.5, 3.0]
    TM = [2.0, 3.0, 4.0, 5.0]
    agg = {(s, t): [] for s in SM for t in TM}
    mae_list = []
    done = 0
    for r in sel:
        sym = r["symbol"]
        sd = r["signal_date"][:10]
        entry = ff(r["entry"])
        atr = (ff(r["atr_pct"]) / 100.0) * entry
        if atr <= 0:
            continue
        d0 = dt.date.fromisoformat(sd)
        start = (d0 + dt.timedelta(days=1)).isoformat()
        end = (d0 + dt.timedelta(days=8)).isoformat()
        bars = fetch_intraday(sym, start, end)
        if not bars:
            continue
        # MAE (maks aleyhte hareket, R)
        low_min = min(b[2] for b in bars)
        mae_list.append((entry - low_min) / atr)
        for s in SM:
            for t in TM:
                agg[(s, t)].append(simulate(entry, atr, bars, s, t))
        done += 1
        if done % 50 == 0:
            print(f"  {done}/{len(sel)} islendi...")
    if done == 0:
        print("Hic bar cekilemedi (ag/anahtar?).")
        return

    print(f"\nGercekten islenen: {done}")
    if mae_list:
        mae_sorted = sorted(mae_list)
        med = mae_sorted[len(mae_sorted) // 2]
        print(
            f"MAE (R): medyan={med:.2f}  | %75={mae_sorted[int(len(mae_sorted)*0.75)]:.2f}  %90={mae_sorted[int(len(mae_sorted)*0.9)]:.2f}"
        )
        print(f">>> Stop bunu kapsamali: sinyallerin coğu {med:.1f}R'ye kadar geri cekiliyor.")

    print("\n=== STOP x TP GRID (R cinsinden) ===")
    print(f"{'stop':>5}{'tp':>5}{'win%':>7}{'ortR':>7}{'beklenti':>10}{'PF':>7}{'n':>6}")
    best = None
    for s in SM:
        for t in TM:
            rs = agg[(s, t)]
            if len(rs) < 20:
                continue
            wins = [x for x in rs if x > 0]
            losses = [x for x in rs if x < 0]
            win_rate = len(wins) / len(rs)
            exp = sum(rs) / len(rs)
            pf = (sum(wins) / abs(sum(losses))) if losses else float("inf")
            print(
                f"{s:>5.1f}{t:>5.1f}{win_rate*100:>7.1f}{exp:>7.2f}{exp:>10.2f}{pf:>7.2f}{len(rs):>6}"
            )
            if best is None or exp > best[0]:
                best = (exp, s, t, win_rate, pf)
    if best:
        print(
            f"\nEN IYI beklenti: stop={best[1]}xATR tp={best[2]}xATR  -> beklenti {best[0]:.2f}R  win {best[3]*100:.0f}%  PF {best[4]:.2f}"
        )
        print(
            "(Mevcut: Normal stop=2.0x tp2=5.5x; ALPHA_V2 tp=3.0x. Bu tablo gerceklesen en iyiyi gosterir.)"
        )
    print("\nBu ciktinin TAMAMINI Claude'a yapistir.")


if __name__ == "__main__":
    main()
