#!/usr/bin/env python3
"""
shadow_scorecard.py — Gölge defterine (data/shadow/scan_shadow.jsonl) otomatik
sonuç-skorlama ekler ve 3 modeli (legacy_quality / v2 / both) karşılaştırır.

Ne yapar:
  1) scan_shadow.jsonl'daki uygun (selection_eligible/entry_ok) sinyalleri okur.
  2) Her sinyali (symbol, gün) data/price_cache/<SYMBOL>.json günlük barlarıyla eşler.
  3) Giriş = sinyal gününden SONRAKİ ilk barın açılışı. ATR% barlardan hesaplanır.
  4) Her modelin KENDİ exit profilini (tp_atr, sl_atr, horizon) üçlü-bariyerle uygular
     (bar içinde önce STOP — muhafazakâr). Ayrıca model-bağımsız MFE/isabet(%≥5,%≥10).
  5) Olgunlaşmamış (yeterli ileri bar yok) sinyaller "pending" olarak atlanır.
  6) Çıktı: data/shadow/shadow_scored.csv (satır bazında) + shadow_scorecard.md (özet).

Kullanım (repo kökünden, price_cache GÜNCEL olmalı):
    python shadow_scorecard.py
    python shadow_scorecard.py --horizon 5 --dedup

Not: price_cache bayatsa çoğu sinyal "pending" kalır — önce cache'i (EODHD) güncelle.
"""

from __future__ import annotations

import argparse
import collections
import csv
import json
import os
import statistics
from datetime import datetime

LEDGER = "data/shadow/scan_shadow.jsonl"
PRICE_DIR = "data/price_cache"
OUT_CSV = "data/shadow/shadow_scored.csv"
OUT_MD = "data/shadow/shadow_scorecard.md"

MODELS = ("legacy_quality", "v2", "both")
SELECT_FLAG = {
    "legacy_quality": "selected_by_legacy_quality",
    "v2": "selected_by_v2",
    "both": "selected_by_both",
}
DEFAULT_EXIT = {  # exit_profiles satırda yoksa
    "legacy_quality": {"tp_atr": 2.0, "sl_atr": 1.0, "horizon": 5},
    "v2": {"tp_atr": 5.0, "sl_atr": 1.0, "horizon": 5},
    "both": {"tp_atr": 5.0, "sl_atr": 1.0, "horizon": 5},
}


# ---------------------------------------------------------------- veri okuma
def load_ledger(path: str) -> list[dict]:
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if r.get("selection_eligible") or r.get("entry_ok"):
                rows.append(r)
    return rows


_price_cache: dict[str, list | None] = {}


def load_bars(sym: str) -> list | None:
    if sym in _price_cache:
        return _price_cache[sym]
    p = os.path.join(PRICE_DIR, f"{sym}.json")
    bars = None
    if os.path.exists(p):
        try:
            data = json.load(open(p, encoding="utf-8"))
            if isinstance(data, list) and data and "date" in data[0]:
                bars = sorted(data, key=lambda b: b["date"])
        except (json.JSONDecodeError, OSError, KeyError):
            bars = None
    _price_cache[sym] = bars
    return bars


# ---------------------------------------------------------------- hesaplama
def atr_pct(bars: list, entry_idx: int, period: int = 14) -> float | None:
    """entry_idx barından ÖNCEKİ `period` barla ATR% (giriş kapanışına oranla)."""
    if entry_idx < 1:
        return None
    trs = []
    for i in range(max(1, entry_idx - period), entry_idx):
        h, low, pc = bars[i]["high"], bars[i]["low"], bars[i - 1]["close"]
        trs.append(max(h - low, abs(h - pc), abs(low - pc)))
    if not trs:
        return None
    atr = sum(trs) / len(trs)
    ref = bars[entry_idx]["open"] or bars[entry_idx - 1]["close"]
    return atr / ref if ref else None


def barrier_exit(bars, entry_idx, entry, atrp, tp_atr, sl_atr, horizon):
    """Üçlü bariyer; bar içinde önce STOP. Getiri % döndürür (+MFE, sonuç etiketi)."""
    tp = entry * (1 + tp_atr * atrp)
    sl = entry * (1 - sl_atr * atrp)
    mfe = 0.0
    for j in range(entry_idx, min(entry_idx + horizon, len(bars))):
        b = bars[j]
        mfe = max(mfe, (b["high"] / entry - 1))
        if b["low"] <= sl:
            return (sl / entry - 1) * 100, mfe * 100, "SL"
        if b["high"] >= tp:
            return (tp / entry - 1) * 100, mfe * 100, "TP"
    last = bars[min(entry_idx + horizon - 1, len(bars) - 1)]["close"]
    return (last / entry - 1) * 100, mfe * 100, "TIME"


def score_signal(row, horizon_override=None):
    """Bir sinyali skorla. Olgun değilse None. Model bazlı sonuç dict'i döndürür."""
    sym = row["symbol"]
    d = (row.get("timestamp") or "")[:10]
    if not d:
        return None
    bars = load_bars(sym)
    if not bars:
        return {"_status": "no_cache", "symbol": sym, "date": d}
    # giriş barı = sinyal gününden sonraki ilk bar
    entry_idx = next((i for i, b in enumerate(bars) if b["date"] > d), None)
    if entry_idx is None:
        return {"_status": "pending", "symbol": sym, "date": d}
    atrp = atr_pct(bars, entry_idx)
    if not atrp:
        return {"_status": "no_atr", "symbol": sym, "date": d}
    entry = bars[entry_idx]["open"] or bars[entry_idx]["close"]

    out = {"symbol": sym, "date": d, "entry": round(entry, 4), "atr_pct": round(atrp, 4)}
    max_h = max(DEFAULT_EXIT[m]["horizon"] for m in MODELS)
    if horizon_override:
        max_h = horizon_override
    if len(bars) - entry_idx < max_h:
        return {"_status": "pending", "symbol": sym, "date": d}

    ep_row = row.get("exit_profiles") or {}
    scored_any = False
    for m in MODELS:
        if not row.get(SELECT_FLAG[m]):
            continue
        ep = ep_row.get(m) or DEFAULT_EXIT[m]
        tp_atr = float(ep.get("tp_atr", DEFAULT_EXIT[m]["tp_atr"]))
        sl_atr = float(ep.get("sl_atr", DEFAULT_EXIT[m]["sl_atr"]))
        hor = int(horizon_override or ep.get("horizon", DEFAULT_EXIT[m]["horizon"]))
        ret, mfe, label = barrier_exit(bars, entry_idx, entry, atrp, tp_atr, sl_atr, hor)
        out[f"{m}_ret"] = round(ret, 3)
        out[f"{m}_mfe"] = round(mfe, 3)
        out[f"{m}_exit"] = label
        scored_any = True
    if not scored_any:
        return {"_status": "not_selected", "symbol": sym, "date": d}
    out["_status"] = "scored"
    return out


# ---------------------------------------------------------------- toplama
def summarize(scored: list[dict]) -> dict:
    agg = {}
    for m in MODELS:
        rets = [s[f"{m}_ret"] for s in scored if f"{m}_ret" in s]
        mfes = [s[f"{m}_mfe"] for s in scored if f"{m}_mfe" in s]
        exits = [s[f"{m}_exit"] for s in scored if f"{m}_exit" in s]
        if not rets:
            agg[m] = None
            continue
        wins = [r for r in rets if r > 0]
        losses = [r for r in rets if r <= 0]
        gross_win = sum(wins)
        gross_loss = abs(sum(losses))
        agg[m] = {
            "n": len(rets),
            "avg_ret": round(statistics.mean(rets), 2),
            "median_ret": round(statistics.median(rets), 2),
            "win_rate": round(100 * len(wins) / len(rets), 1),
            "tp_rate": round(100 * exits.count("TP") / len(exits), 1),
            "sl_rate": round(100 * exits.count("SL") / len(exits), 1),
            "profit_factor": round(gross_win / gross_loss, 2) if gross_loss else float("inf"),
            "mfe_ge5": round(100 * sum(1 for x in mfes if x >= 5) / len(mfes), 1),
            "mfe_ge10": round(100 * sum(1 for x in mfes if x >= 10) / len(mfes), 1),
            "avg_mfe": round(statistics.mean(mfes), 2),
        }
    return agg


def write_md(agg, meta):
    lines = [
        "# Gölge Skor Kartı — 3 Model Karşılaştırması",
        "",
        f"Üretim: {datetime.now().strftime('%Y-%m-%d %H:%M')}  ·  "
        f"Skorlanan sinyal: {meta['scored']}  ·  Beklemede (olgunlaşmamış): {meta['pending']}  ·  "
        f"Cache yok/eksik: {meta['no_cache'] + meta['no_atr']}",
        "",
        "Not: giriş = sinyal ertesi bar açılışı; her model KENDİ exit profilini kullanır "
        "(üçlü bariyer, bar içinde önce stop). MFE = model-bağımsız en yüksek lehte hareket.",
        "",
        "| Model | n | Ort.% | Medyan% | Kazanç% | TP% | SL% | ProfitF | MFE≥5% | MFE≥10% | Ort.MFE |",
        "|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|",
    ]
    for m in MODELS:
        a = agg[m]
        if not a:
            lines.append(f"| {m} | 0 | — | — | — | — | — | — | — | — | — |")
            continue
        lines.append(
            f"| {m} | {a['n']} | {a['avg_ret']} | {a['median_ret']} | {a['win_rate']} | "
            f"{a['tp_rate']} | {a['sl_rate']} | {a['profit_factor']} | {a['mfe_ge5']} | "
            f"{a['mfe_ge10']} | {a['avg_mfe']} |"
        )
    lines += [
        "",
        "Yorum ipuçları: v2 legacy'nin alt kümesiyse (v2_only=0), asıl soru v2'nin "
        "daha AZ ama daha KALİTELİ mi (yüksek TP%/ProfitF, düşük n) olduğudur. "
        "Örneklem küçükken (n<30) farklar gürültü olabilir — güven aralığı için daha çok gün biriktir.",
    ]
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def write_csv(scored):
    if not scored:
        return
    cols = ["symbol", "date", "entry", "atr_pct"]
    for m in MODELS:
        cols += [f"{m}_ret", f"{m}_mfe", f"{m}_exit"]
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for s in scored:
            w.writerow(s)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--horizon", type=int, default=None, help="Tüm modeller için ortak horizon override"
    )
    ap.add_argument("--dedup", action="store_true", help="Aynı (symbol,gün) ilk kez alınsın")
    args = ap.parse_args()

    if not os.path.exists(LEDGER):
        print(f"HATA: {LEDGER} yok.")
        return
    rows = load_ledger(LEDGER)
    print(f"Uygun sinyal (ham): {len(rows)}")

    if args.dedup:
        seen = set()
        dd = []
        for r in rows:
            key = (r["symbol"], (r.get("timestamp") or "")[:10])
            if key in seen:
                continue
            seen.add(key)
            dd.append(r)
        rows = dd
        print(f"Dedup sonrası: {len(rows)}")

    scored, status = [], collections.Counter()
    for r in rows:
        res = score_signal(r, args.horizon)
        if res is None:
            status["skip"] += 1
            continue
        status[res["_status"]] += 1
        if res["_status"] == "scored":
            scored.append(res)

    meta = {
        "scored": status["scored"],
        "pending": status["pending"],
        "no_cache": status["no_cache"],
        "no_atr": status["no_atr"],
    }
    print(
        f"Skorlandı: {meta['scored']} | Beklemede: {meta['pending']} | "
        f"Cache yok: {meta['no_cache']} | ATR yok: {meta['no_atr']} | "
        f"Seçilmemiş: {status['not_selected']}"
    )

    if not scored:
        print(
            "\nHenüz skorlanabilir sinyal yok. price_cache güncel mi? "
            "(sinyal günü + horizon kadar ileri bar gerekiyor.)"
        )
        return

    agg = summarize(scored)
    write_csv(scored)
    write_md(agg, meta)

    print(
        f"\n{'Model':16} {'n':>4} {'Ort%':>7} {'Kaz%':>6} {'TP%':>6} {'SL%':>6} {'PF':>6} {'MFE≥5%':>7} {'MFE≥10%':>8}"
    )
    for m in MODELS:
        a = agg[m]
        if not a:
            print(f"{m:16} {'0':>4}   (seçim yok)")
            continue
        print(
            f"{m:16} {a['n']:>4} {a['avg_ret']:>7} {a['win_rate']:>6} {a['tp_rate']:>6} "
            f"{a['sl_rate']:>6} {a['profit_factor']:>6} {a['mfe_ge5']:>7} {a['mfe_ge10']:>8}"
        )
    print(f"\nYazıldı: {OUT_CSV}  ·  {OUT_MD}")


if __name__ == "__main__":
    main()
