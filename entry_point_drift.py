#!/usr/bin/env python3
"""
entry_point_drift.py — Big Bet #1b: 3-giriş-noktası ayrıştırması + bariyersiz drift eğrisi.

Üç giriş noktası:
  A) signal-close : entry = scan_date barının kendi kapanışı
  B) next-open     : entry = ertesi bar açılışı (mevcut edge_recheck varsayılanı)
  C) next-close    : entry = ertesi bar kapanışı (gecikmeli giriş)

Her biri için t+1..t+10 KÜMÜLATİF getiri (bariyersiz — TP/SL yok):
  ham, SPY-excess, sektör-excess (sector_map_full.csv korelasyon-proxy).

Amaç: drift var mı, hangi giriş-noktasında yaşıyor, half-life nerede.
Resumable değil (tek koşuda tüm evren) — timeout olursa sembol-limit ile parçalanır.
"""

from __future__ import annotations

import bisect
import csv
import json
import os
import statistics
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PD = "data/price_cache"
H = 10  # t+1..t+10


def load_series(sym):
    p = f"{PD}/{sym}.json"
    if not os.path.exists(p):
        return None
    try:
        b = sorted(json.load(open(p)), key=lambda x: x["date"])
        return b if b else None
    except Exception:
        return None


class Bench:
    """Basit benchmark serisi: tarih->close, asof-erişim."""

    def __init__(self, sym):
        b = load_series(sym)
        self.dates = [x["date"] for x in b] if b else []
        self.close = [x["close"] for x in b] if b else []

    def idx_asof(self, d):
        i = bisect.bisect_right(self.dates, d) - 1
        return i if i >= 0 else None

    def cumret(self, i0, k):
        """i0 barının kapanışından k gün sonrasının kapanışına kümülatif getiri (%)."""
        if i0 is None or i0 + k >= len(self.close) or i0 < 0:
            return None
        return (self.close[i0 + k] / self.close[i0] - 1) * 100


def main(limit_syms=None):
    spy = Bench("SPY")
    sec_map = {
        r["symbol"]: r["etf"]
        for r in csv.DictReader(open("data/backtest_out/sector_map_full.csv"))
        if r["etf"]
    }
    etf_cache = {}

    def get_etf(e):
        if e not in etf_cache:
            etf_cache[e] = Bench(e)
        return etf_cache[e]

    sig_rows = list(csv.DictReader(open("data/backtest_out/edge_recheck.csv")))
    syms = sorted({r["symbol"] for r in sig_rows})
    if limit_syms:
        syms = syms[:limit_syms]
    sym_set = set(syms)

    bars_cache = {}

    def get_bars(s):
        if s not in bars_cache:
            bars_cache[s] = load_series(s)
        return bars_cache[s]

    # Sonuç biriktiriciler: variant -> t -> list of (raw, spy_excess, sector_excess)
    variants = ["signal_close", "next_open", "next_close"]
    acc = {
        v: {t: {"raw": [], "spy_ex": [], "sec_ex": []} for t in range(1, H + 1)} for v in variants
    }
    n_signals = 0

    for r in sig_rows:
        s = r["symbol"]
        if s not in sym_set:
            continue
        d = str(r["scan_date"])
        b = get_bars(s)
        if not b:
            continue
        dates = [x["date"] for x in b]
        # ei0: scan_date barının kendisi (<=d, son bar)
        ei0 = bisect.bisect_right(dates, d) - 1
        if ei0 < 0 or ei0 + 1 >= len(b):
            continue
        ei1 = ei0 + 1  # ertesi bar
        if ei1 + H >= len(b):
            continue

        close0 = b[ei0]["close"]
        open1 = b[ei1]["open"] or b[ei1]["close"]
        close1 = b[ei1]["close"]
        if not close0 or not open1 or not close1:
            continue

        etf = get_etf(sec_map.get(s)) if sec_map.get(s) else None
        spy_i_signal = spy.idx_asof(d)
        spy_i_next = (
            spy_i_signal + 1
            if spy_i_signal is not None and spy_i_signal + 1 < len(spy.close)
            else None
        )
        etf_i_signal = etf.idx_asof(d) if etf else None
        etf_i_next = (
            etf_i_signal + 1
            if (etf and etf_i_signal is not None and etf_i_signal + 1 < len(etf.close))
            else None
        )

        n_signals += 1
        for t in range(1, H + 1):
            if ei0 + t < len(b):
                raw_a = (b[ei0 + t]["close"] / close0 - 1) * 100  # A) signal-close
            else:
                raw_a = None
            if ei1 + t - 1 < len(b):
                raw_b = (
                    b[ei1 + t - 1]["close"] / open1 - 1
                ) * 100  # B) next-open (t=1 -> same day close)
            else:
                raw_b = None
            if ei1 + t < len(b):
                raw_c = (b[ei1 + t]["close"] / close1 - 1) * 100  # C) next-close
            else:
                raw_c = None

            spy_a = spy.cumret(spy_i_signal, t) if spy_i_signal is not None else None
            spy_b = spy.cumret(spy_i_next, t - 1) if spy_i_next is not None and t >= 1 else None
            spy_c = spy.cumret(spy_i_next, t) if spy_i_next is not None else None

            sec_a = etf.cumret(etf_i_signal, t) if (etf and etf_i_signal is not None) else None
            sec_b = (
                etf.cumret(etf_i_next, t - 1)
                if (etf and etf_i_next is not None and t >= 1)
                else None
            )
            sec_c = etf.cumret(etf_i_next, t) if (etf and etf_i_next is not None) else None

            for val, spy_v, sec_v, variant in [
                (raw_a, spy_a, sec_a, "signal_close"),
                (raw_b, spy_b, sec_b, "next_open"),
                (raw_c, spy_c, sec_c, "next_close"),
            ]:
                if val is None:
                    continue
                acc[variant][t]["raw"].append(val)
                if spy_v is not None:
                    acc[variant][t]["spy_ex"].append(val - spy_v)
                if sec_v is not None:
                    acc[variant][t]["sec_ex"].append(val - sec_v)

    print(f"n_signals işlendi = {n_signals}")
    for v in variants:
        print(f"\n=== GİRİŞ NOKTASI: {v} ===")
        print(
            f"{'t':>3} {'n':>7} {'ham-medyan':>11} {'SPY-excess-med':>15} {'sektör-excess-med':>18}"
        )
        for t in range(1, H + 1):
            raw = acc[v][t]["raw"]
            spy_ex = acc[v][t]["spy_ex"]
            sec_ex = acc[v][t]["sec_ex"]
            rm = statistics.median(raw) if raw else float("nan")
            sm = statistics.median(spy_ex) if spy_ex else float("nan")
            secm = statistics.median(sec_ex) if sec_ex else float("nan")
            print(f"{t:>3} {len(raw):>7} {rm:>11.3f} {sm:>15.3f} {secm:>18.3f}")

    # Half-life proxy: hangi t'de SPY-excess-medyan tepe yapıyor (next_open için)
    v = "next_open"
    peak_t, peak_val = None, -1e9
    for t in range(1, H + 1):
        vals = acc[v][t]["spy_ex"]
        if vals:
            m = statistics.median(vals)
            if m > peak_val:
                peak_val, peak_t = m, t
    print(f"\nnext_open SPY-excess tepe noktası: t={peak_t} (medyan={peak_val:.3f})")


if __name__ == "__main__":
    lim = int(sys.argv[1]) if len(sys.argv) > 1 else None
    main(lim)
