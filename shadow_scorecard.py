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
import random
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
def load_ledger(
    path: str, include_control: bool = False, control_limit: int | None = None
) -> list[dict]:
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
            if include_control or r.get("selection_eligible") or r.get("entry_ok"):
                rows.append(r)
                if control_limit and len(rows) >= control_limit:
                    break
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


def forward_return(bars: list, entry_idx: int, horizon: int) -> float | None:
    """Return close-to-close forward return in percent for any row."""
    end = entry_idx + horizon - 1
    if entry_idx < 0 or end >= len(bars):
        return None
    entry = bars[entry_idx].get("open") or bars[entry_idx].get("close")
    close = bars[end].get("close")
    if not entry or close is None:
        return None
    return (float(close) / float(entry) - 1.0) * 100.0


def percentile_summary(values: list[float]) -> dict[str, float | None]:
    """Return robust p10/median/p90 values without inventing empty data."""
    if not values:
        return {"p10": None, "median": None, "p90": None}
    ordered = sorted(values)

    def at(q: float) -> float:
        position = (len(ordered) - 1) * q
        lower = int(position)
        upper = min(lower + 1, len(ordered) - 1)
        return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)

    return {
        "p10": round(at(0.10), 2),
        "median": round(statistics.median(ordered), 2),
        "p90": round(at(0.90), 2),
    }


def sharpe_like(values: list[float]) -> float | None:
    """Annualized mean/std proxy; returns None when variance is not estimable."""
    if len(values) < 2:
        return None
    deviation = statistics.stdev(values)
    return round(statistics.mean(values) / deviation * (252**0.5), 3) if deviation else None


def bootstrap_mean_ci(
    values: list[float], iterations: int = 1000, seed: int = 42
) -> dict[str, float | None]:
    """Deterministic percentile CI for the mean; empty/singleton data stays explicit."""
    if len(values) < 2:
        return {"low": None, "high": None}
    rng = random.Random(seed)
    means = [statistics.mean(rng.choices(values, k=len(values))) for _ in range(iterations)]
    bounds = percentile_summary(means)
    return {"low": bounds["p10"], "high": bounds["p90"]}


def benchmark_return(bars: list | None, signal_date: str, horizon: int) -> float | None:
    """Return the benchmark's same-window close-to-close return."""
    if not bars:
        return None
    entry_idx = next((i for i, bar in enumerate(bars) if bar["date"] > signal_date), None)
    if entry_idx is None:
        return None
    return forward_return(bars, entry_idx, horizon)


def _adv_bucket(value: object) -> str:
    try:
        adv = float(value)
    except (TypeError, ValueError):
        return "unknown"
    if adv < 1_000_000:
        return "<1m"
    if adv < 10_000_000:
        return "1m-10m"
    if adv < 100_000_000:
        return "10m-100m"
    return ">=100m"


def _reason_key(row: dict) -> str:
    reasons = row.get("reject_reason") or ["selected"]
    if isinstance(reasons, str):
        reasons = [reasons]
    return ",".join(sorted(str(reason) for reason in reasons)) or "unknown"


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


def score_signal(
    row,
    horizon_override=None,
    horizons=None,
    benchmark_symbol="SPY",
    benchmark_symbols=None,
    include_benchmark=True,
):
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
    horizons = sorted(set(horizons or [horizon_override or 5]))
    # Olgunluk = bariyer çıkışının (model horizon'u) gerektirdiği bar sayısı.
    # Sweep'teki daha uzun horizon'lar (10/20) henüz mevcut değilse sinyali
    # PENDING yapma; yalnız o horizon'un alanlarını boş bırak (summarize
    # per-horizon eksikliği tolere eder). Böylece varsayılan sweep ile de
    # olgun sinyaller skorlanır — 20 bar beklemek gerekmez.
    base_h = max(DEFAULT_EXIT[m]["horizon"] for m in MODELS)
    if horizon_override:
        base_h = max(base_h, horizon_override)
    available = len(bars) - entry_idx
    if available < base_h:
        return {"_status": "pending", "symbol": sym, "date": d}

    ep_row = row.get("exit_profiles") or {}
    # Çoklu benchmark: SPY tek başına yanlış kıyas (büyük-cap); küçük/orta-cap
    # sinyalleri için IWM (küçük-cap) ve QQQ (tekno) de excess olarak hesaplanır.
    bench_syms = benchmark_symbols if benchmark_symbols else [benchmark_symbol]
    bench_bars = {b: load_bars(b) for b in bench_syms} if include_benchmark else {}
    for horizon in horizons:
        if available < horizon:
            continue  # bu horizon henüz olgun değil — atla, pending yapma
        ret = forward_return(bars, entry_idx, horizon)
        if ret is None:
            continue
        out[f"forward_ret_{horizon}"] = round(ret, 3)
        out[f"forward_mfe_{horizon}"] = round(
            max((bars[j]["high"] / entry - 1) * 100 for j in range(entry_idx, entry_idx + horizon)),
            3,
        )
        out[f"forward_ret_atr_{horizon}"] = round(ret / (atrp * 100), 3) if atrp else None
        for bsym, bbars in bench_bars.items():
            if not bbars:
                continue
            bench = benchmark_return(bbars, d, horizon)
            if bench is not None:
                out[f"{bsym.lower()}_excess_{horizon}"] = round(ret - bench, 3)
    out["segment_adv"] = _adv_bucket(row.get("dollar_adv"))
    out["segment_quality"] = str(row.get("data_quality_tier") or "unknown")
    out["reject_reason"] = _reason_key(row)
    out["is_control"] = not bool(row.get("selection_eligible") or row.get("entry_ok"))
    scored_any = False
    for m in MODELS:
        if not row.get(SELECT_FLAG[m]):
            continue
        ep = ep_row.get(m) or DEFAULT_EXIT[m]
        tp_atr = float(ep.get("tp_atr", DEFAULT_EXIT[m]["tp_atr"]))
        sl_atr = float(ep.get("sl_atr", DEFAULT_EXIT[m]["sl_atr"]))
        hor = int(
            horizon_override
            or ep.get("horizon_bars", ep.get("horizon", DEFAULT_EXIT[m]["horizon"]))
        )
        ret, mfe, label = barrier_exit(bars, entry_idx, entry, atrp, tp_atr, sl_atr, hor)
        out[f"{m}_ret"] = round(ret, 3)
        out[f"{m}_mfe"] = round(mfe, 3)
        out[f"{m}_exit"] = label
        scored_any = True
    if not scored_any and not out["is_control"]:
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
            "distribution": percentile_summary(rets),
            "avg_ret_atr": round(
                statistics.mean(
                    s["forward_ret_atr_5"]
                    for s in scored
                    if f"{m}_ret" in s and "forward_ret_atr_5" in s
                ),
                3,
            )
            if any(f"{m}_ret" in s and "forward_ret_atr_5" in s for s in scored)
            else None,
        }
    for group_name, group_rows in (
        ("selected", [s for s in scored if not s.get("is_control")]),
        ("control", [s for s in scored if s.get("is_control")]),
    ):
        values = [s["forward_ret_5"] for s in group_rows if "forward_ret_5" in s]
        excess = [s["spy_excess_5"] for s in group_rows if "spy_excess_5" in s]
        agg[group_name] = {
            "n": len(values),
            "return": percentile_summary(values),
            "avg_ret": round(statistics.mean(values), 2) if values else None,
            "win_rate": round(100 * sum(v > 0 for v in values) / len(values), 1)
            if values
            else None,
            "avg_ret_atr": round(
                statistics.mean(
                    s["forward_ret_atr_5"] for s in group_rows if "forward_ret_atr_5" in s
                ),
                3,
            )
            if any("forward_ret_atr_5" in s for s in group_rows)
            else None,
            "excess": percentile_summary(excess),
            "excess_win_rate": round(100 * sum(v > 0 for v in excess) / len(excess), 1)
            if excess
            else None,
            "sharpe_like": sharpe_like(values),
            "bootstrap_mean_ci": bootstrap_mean_ci(values),
        }
    agg["control_by_reason"] = {}
    for row in (s for s in scored if s.get("is_control")):
        key = row.get("reject_reason", "unknown")
        agg["control_by_reason"].setdefault(key, []).append(row)
    for key, rows in list(agg["control_by_reason"].items()):
        values = [r["forward_ret_5"] for r in rows if "forward_ret_5" in r]
        agg["control_by_reason"][key] = {"n": len(values), "return": percentile_summary(values)}
    return agg


def summarize_horizons(scored: list[dict], horizons: list[int]) -> dict[int, dict]:
    result = {}
    for horizon in horizons:
        result[horizon] = {}
        for group, rows in (
            ("selected", [s for s in scored if not s.get("is_control")]),
            ("control", [s for s in scored if s.get("is_control")]),
        ):
            values = [s[f"forward_ret_{horizon}"] for s in rows if f"forward_ret_{horizon}" in s]
            excess = [s[f"spy_excess_{horizon}"] for s in rows if f"spy_excess_{horizon}" in s]
            result[horizon][group] = {
                "n": len(values),
                "return": percentile_summary(values),
                "avg_ret_atr": round(
                    statistics.mean(
                        s[f"forward_ret_atr_{horizon}"]
                        for s in rows
                        if f"forward_ret_atr_{horizon}" in s
                    ),
                    3,
                )
                if any(f"forward_ret_atr_{horizon}" in s for s in rows)
                else None,
                "excess": percentile_summary(excess),
                "sharpe_like": sharpe_like(values),
            }
    return result


def summarize_benchmarks(scored: list[dict], benchmarks: list[str], horizon: int = 5) -> dict:
    """Seçilen vs kontrol için her benchmark'a göre excess medyanı + pozitif oranı."""
    out: dict = {}
    for group, rows in (
        ("selected", [s for s in scored if not s.get("is_control")]),
        ("control", [s for s in scored if s.get("is_control")]),
    ):
        raw = [s[f"forward_ret_{horizon}"] for s in rows if f"forward_ret_{horizon}" in s]
        out[group] = {
            "raw_median": round(statistics.median(raw), 2) if raw else None,
            "n": len(raw),
        }
        for b in benchmarks:
            ex = [
                s[f"{b.lower()}_excess_{horizon}"]
                for s in rows
                if f"{b.lower()}_excess_{horizon}" in s
            ]
            out[group][b] = {
                "median": round(statistics.median(ex), 2) if ex else None,
                "win": round(100 * sum(v > 0 for v in ex) / len(ex), 1) if ex else None,
            }
    return out


def write_md(agg, meta, horizons=None):
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
        "",
        "## Seçilen vs Kontrol — Dağılım ve Excess",
        "",
        "| Grup | n | Getiri p10 / medyan / p90 | Kazanç% | Getiri/ATR | Excess p10 / medyan / p90 |",
        "|---|---:|---|---:|---:|---|",
    ]
    for group in ("selected", "control"):
        a = agg.get(group, {})
        dist = a.get("return", {})
        excess = a.get("excess", {})
        lines.append(
            f"| {group} | {a.get('n', 0)} | {dist.get('p10', '—')} / {dist.get('median', '—')} / {dist.get('p90', '—')} | "
            f"{a.get('win_rate', '—')} | {a.get('avg_ret_atr', '—')} | "
            f"{excess.get('p10', '—')} / {excess.get('median', '—')} / {excess.get('p90', '—')} |"
        )
    lines += [
        "",
        "Risk notu: Sharpe-benzeri değer ve bootstrap ortalama aralığı yalnız n≥2 ise hesaplanır; bu rapor istatistiksel kanıt veya canlı kural değişikliği değildir.",
    ]
    if agg.get("benchmarks"):
        bmarks = meta.get("benchmarks", [])
        h = meta.get("benchmark_horizon", 5)
        lines += [
            "",
            f"## Çoklu Benchmark Excess ({h}g) — medyan (poz%)",
            "",
            "Not: SPY tek başına büyük-cap; IWM küçük-cap, QQQ tekno. Sinyaller küçük/orta-cap olduğu için IWM en doğru stil eşi.",
            "",
            "| Grup | n | Ham medyan | " + " | ".join(f"{b} excess" for b in bmarks) + " |",
            "|---|---:|---:|" + "---:|" * len(bmarks),
        ]
        for group in ("selected", "control"):
            g = agg["benchmarks"].get(group, {})
            cells = []
            for b in bmarks:
                bb = g.get(b, {})
                cells.append(f"{bb.get('median', '—')} ({bb.get('win', '—')})")
            lines.append(
                f"| {group} | {g.get('n', 0)} | {g.get('raw_median', '—')} | "
                + " | ".join(cells)
                + " |"
            )
    if horizons:
        lines += [
            "",
            "## Horizon × Metrik",
            "",
            "| Gün | Grup | n | Getiri p10 / medyan / p90 | Getiri/ATR | Excess p10 / medyan / p90 |",
            "|---:|---|---:|---|---:|---|",
        ]
        for horizon in horizons:
            for group in ("selected", "control"):
                a = agg.get("horizons", {}).get(horizon, {}).get(group, {})
                ret = a.get("return", {})
                excess = a.get("excess", {})
                lines.append(
                    f"| {horizon} | {group} | {a.get('n', 0)} | {ret.get('p10', '—')} / {ret.get('median', '—')} / {ret.get('p90', '—')} | "
                    f"{a.get('avg_ret_atr', '—')} | {excess.get('p10', '—')} / {excess.get('median', '—')} / {excess.get('p90', '—')} |"
                )
    if agg.get("control_by_reason"):
        lines += [
            "",
            "## Kontrol Grubu — Red Nedeni",
            "",
            "| Red nedeni | n | Getiri p10 / medyan / p90 |",
            "|---|---:|---|",
        ]
        for reason, a in sorted(agg["control_by_reason"].items()):
            dist = a["return"]
            lines.append(
                f"| {reason} | {a['n']} | {dist['p10']} / {dist['median']} / {dist['p90']} |"
            )
    if agg.get("segments"):
        lines += ["", "## Segment Sayıları", "", "| Segment | Skorlanan satır |", "|---|---:|"]
        lines.extend(f"| {key} | {count} |" for key, count in sorted(agg["segments"].items()))
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def write_csv(scored):
    if not scored:
        return
    cols = sorted({key for row in scored for key in row if not key.startswith("_")})
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
    ap.add_argument(
        "--control", action="store_true", help="Seçilmeyen satırları kontrol grubu olarak dahil et"
    )
    ap.add_argument(
        "--control-limit", type=int, default=None, help="Kontrol grubu için performans sınırı"
    )
    ap.add_argument("--horizon-sweep", default="1,3,5,10,20", help="İleri günleri virgülle belirt")
    ap.add_argument(
        "--benchmark",
        default="SPY,IWM,QQQ",
        help="Excess benchmark(lar), virgülle. İlk sembol birincil (SPY).",
    )
    ap.add_argument("--by-segment", action="store_true", help="Segment alanlarını çıktıya ekle")
    args = ap.parse_args()

    if not os.path.exists(LEDGER):
        print(f"HATA: {LEDGER} yok.")
        return
    horizons = sorted({int(x) for x in args.horizon_sweep.split(",") if int(x) > 0})
    rows = load_ledger(LEDGER, include_control=args.control, control_limit=args.control_limit)
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

    benchmarks = [b.strip().upper() for b in args.benchmark.split(",") if b.strip()]
    scored, status = [], collections.Counter()
    for r in rows:
        res = score_signal(r, args.horizon, horizons=horizons, benchmark_symbols=benchmarks)
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
        "control": args.control,
        "benchmarks": benchmarks,
        "benchmark_horizon": 5,
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
    agg["horizons"] = summarize_horizons(scored, horizons)
    agg["benchmarks"] = summarize_benchmarks(scored, benchmarks)
    if args.by_segment:
        agg["segments"] = {}
        for row in scored:
            key = f"{row.get('segment_adv')} / {row.get('segment_quality')}"
            agg["segments"].setdefault(key, 0)
            agg["segments"][key] += 1
    write_csv(scored)
    write_md(agg, meta, horizons=horizons)

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
