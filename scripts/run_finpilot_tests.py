#!/usr/bin/env python3
"""
FinPilot — Master Test Koşucu
==============================

Tüm analiz & doğrulama adımlarını sırayla çalıştırır:
  1. Shortlist CSV'lerini birleştir (data/shortlists/*.csv)
  2. A/B Backtest karşılaştırması
  3. Walk-Forward doğrulama
  4. Monte Carlo simülasyonu
  5. Slippage kalibrasyon raporu
  6. Özet rapor üret → data/finpilot_weekly_report_YYYYMMDD.md

Kullanım:
  python scripts/run_finpilot_tests.py               # tam çalıştır
  python scripts/run_finpilot_tests.py --quick       # sadece A/B + Slippage (hızlı)
  python scripts/run_finpilot_tests.py --wf-only     # sadece walk-forward
"""

from __future__ import annotations

import argparse
import json
import sys
import traceback
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

# ── Proje kökü ─────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# ── Sabitler ───────────────────────────────────────────────────────────────
DATA_DIR = ROOT / "data"
SHORTLIST_DIR = DATA_DIR / "shortlists"
LOG_DIR = ROOT / "logs"
TS = datetime.now().strftime("%Y%m%d_%H%M")

TP_UNIT = 1000 * (0.52 * 0.067 - 0.48 * 0.020)  # ≈ $24.52
FP_COST = 15.00
FN_COST = 5.00

STRATEGY_A = {
    "min_alignment_ratio": 0.75,
    "min_momentum_ratio": 0.60,
    "min_filter_score": 2,
    "min_signal_score": 3,
    "min_zscore": 1.5,
    "min_price_filter": 2.0,
}
STRATEGY_B = {
    "min_alignment_ratio": 0.67,
    "min_momentum_ratio": 0.40,
    "min_filter_score": 1,
    "min_signal_score": 2,
    "min_zscore": 0.0,
    "min_price_filter": 2.0,
}

# ══════════════════════════════════════════════════════════════════════════
# Adım 0 — Shortlist CSV'lerini birleştir
# ══════════════════════════════════════════════════════════════════════════


def load_shortlists(days_back: int = 365) -> pd.DataFrame:
    """Son N güne ait tüm shortlist CSV'lerini tek DataFrame'e birleştir."""
    files = sorted(SHORTLIST_DIR.glob("shortlist_*.csv"))
    if not files:
        print("  ⚠️  Shortlist CSV bulunamadı — demo verisi kullanılıyor")
        return _demo_df()

    cutoff = pd.Timestamp.now() - pd.Timedelta(days=days_back)
    frames = []
    for f in files:
        try:
            df = pd.read_csv(f)
            # date sütununu bul
            for col in ("date", "scan_date", "Date", "timestamp"):
                if col in df.columns:
                    df["date"] = pd.to_datetime(df[col], errors="coerce")
                    break
            else:
                # dosya adından tarihi çek: shortlist_YYYYMMDD_HHMM.csv
                try:
                    stem = f.stem  # "shortlist_20250912_1222"
                    parts = stem.split("_")
                    date_str = parts[1] + parts[2]  # "202509121222"
                    df["date"] = pd.to_datetime(date_str, format="%Y%m%d%H%M")
                except Exception:
                    df["date"] = pd.Timestamp.now()

            df = df[df["date"] >= cutoff]
            if not df.empty:
                frames.append(df)
        except Exception as e:
            print(f"  ⚠️  {f.name} atlandı: {e}")

    if not frames:
        print("  ⚠️  Hiç uygun kayıt yok — demo verisi kullanılıyor")
        return _demo_df()

    combined = pd.concat(frames, ignore_index=True)
    combined = combined.sort_values("date").reset_index(drop=True)
    print(f"  ✅ {len(combined)} satır, {len(frames)} CSV dosyası birleştirildi")

    # ground_truth sütunu oluştur (eksikse tahmini yöntemle)
    if "ground_truth" not in combined.columns:
        combined["ground_truth"] = _estimate_ground_truth(combined)

    return combined


def _estimate_ground_truth(df: pd.DataFrame) -> pd.Series:
    """
    Gerçek etiket yoksa A/B backtest tanımını kullan:
    regime=True AND direction=True AND score≥2 AND alignment≥0.67
    AND filter_score≥1 AND risk_reward≥2.0
    """
    conds = pd.Series(True, index=df.index)
    for col, thresh in [
        ("regime", True),
        ("alignment_ratio", 0.67),
        ("signal_score", 2),
        ("filter_score", 1),
        ("risk_reward", 2.0),
    ]:
        if col in df.columns:
            if thresh is True:
                conds &= df[col].astype(bool)
            else:
                conds &= pd.to_numeric(df[col], errors="coerce").fillna(0) >= thresh
    return conds


def _demo_df() -> pd.DataFrame:
    np.random.seed(42)
    n = 600
    dates = pd.date_range("2025-09-01", periods=n, freq="B")
    return pd.DataFrame(
        {
            "date": dates,
            "ground_truth": np.random.choice([True, False], n, p=[0.45, 0.55]),
            "alignment_ratio": np.random.beta(5, 3, n),
            "momentum_ratio": np.random.beta(4, 3, n),
            "filter_score": np.random.randint(0, 5, n),
            "signal_score": np.random.randint(0, 6, n),
            "zscore": np.random.randn(n),
            "price_filter": np.random.uniform(0, 5, n),
        }
    )


# ══════════════════════════════════════════════════════════════════════════
# Adım 1 — A/B Backtest
# ══════════════════════════════════════════════════════════════════════════


def run_ab_backtest(df: pd.DataFrame) -> dict:
    """Strateji A ve B'yi karşılaştır, temel metrikleri döndür."""
    print("\n📊 A/B Backtest...")

    results = {}
    for name, params in {"A": STRATEGY_A, "B": STRATEGY_B}.items():
        pred_mask = pd.Series(True, index=df.index)
        for col, val in [
            ("alignment_ratio", params["min_alignment_ratio"]),
            ("momentum_ratio", params["min_momentum_ratio"]),
            ("filter_score", params["min_filter_score"]),
            ("signal_score", params["min_signal_score"]),
            ("zscore", params["min_zscore"]),
            ("price_filter", params["min_price_filter"]),
        ]:
            if col in df.columns:
                pred_mask &= pd.to_numeric(df[col], errors="coerce").fillna(-999) >= val

        gt = df["ground_truth"].astype(bool)
        pred = pred_mask

        tp = int((pred & gt).sum())
        fp = int((pred & ~gt).sum())
        fn = int((~pred & gt).sum())
        tn = int((~pred & ~gt).sum())

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        profit = tp * TP_UNIT - fp * FP_COST - fn * FN_COST

        results[name] = {
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "tn": tn,
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "profit": round(profit, 2),
            "signals": tp + fp,
        }
        winner = "✅" if name == "B" and profit > results.get("A", {}).get("profit", -1e9) else ""
        print(
            f"  Strateji {name}: TP={tp} FP={fp} FN={fn} | "
            f"F1={f1:.3f} | Kâr=${profit:,.2f} {winner}"
        )

    return results


# ══════════════════════════════════════════════════════════════════════════
# Adım 2 — Walk-Forward + Monte Carlo
# ══════════════════════════════════════════════════════════════════════════


def run_wf_mc(df: pd.DataFrame, n_sims: int = 1000) -> dict:
    """Walk-forward + Monte Carlo modülünü çalıştır."""
    print("\n🔄 Walk-Forward + Monte Carlo...")
    try:
        from scripts.walkforward_montecarlo import (
            MonteCarloSimulator,
            WalkForwardValidator,
            _apply_strategy,
        )
    except ImportError:
        # Doğrudan import dene
        wfmc_path = ROOT / "scripts" / "walkforward_montecarlo.py"
        import importlib.util

        spec = importlib.util.spec_from_file_location("wfmc", wfmc_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        WalkForwardValidator = mod.WalkForwardValidator
        MonteCarloSimulator = mod.MonteCarloSimulator
        _apply_strategy = mod._apply_strategy

    # Walk-forward
    wf = WalkForwardValidator(df, train_days=90, test_days=30, n_trials=3456)
    wf_res = wf.run()
    n_win = wf_res.get("metadata", {}).get("n_windows", 0)
    print(f"  ✅ Walk-Forward: {n_win} pencere")

    for strat, s in wf_res.get("summary", {}).items():
        print(
            f"     Strateji {strat}: OOS kâr=${s['oos_total_profit']:,.2f}  "
            f"DSR={s['deflated_sharpe']:.3f}  "
            f"Kazançlı={s['pct_windows_profitable']:.0f}%"
        )

    # Monte Carlo
    mc_results = {}
    for strat, params in {"A": STRATEGY_A, "B": STRATEGY_B}.items():
        pred_df = _apply_strategy(df.copy(), params)
        gt = df["ground_truth"].astype(bool)
        pnls = []
        for idx in pred_df.index:
            p = bool(pred_df.loc[idx, "predicted"])
            g = bool(gt.loc[idx])
            if p and g:
                pnls.append(TP_UNIT)
            elif p:
                pnls.append(-FP_COST)
            elif g:
                pnls.append(-FN_COST)

        mc = MonteCarloSimulator(pnls, initial_cap=10_000.0, n_simulations=n_sims)
        mc_results[strat] = mc.run()
        sig = mc_results[strat].get("significance", {})
        print(
            f"  Monte Carlo {strat}: p={sig.get('p_value_sharpe','?')} — "
            f"{sig.get('interpretation','')}"
        )

    return {"walk_forward": wf_res, "monte_carlo": mc_results}


# ══════════════════════════════════════════════════════════════════════════
# Adım 3 — Slippage Kalibrasyon Raporu
# ══════════════════════════════════════════════════════════════════════════


def _import_slippage_tracker():
    """
    slippage_tracker'ı core/__init__.py (pydantic) çalıştırmadan import et.
    Modülü sys.modules'e kayıt ederek @dataclass'ın kendi modülünü bulmasını sağla.
    """
    import importlib.util

    mod_name = "core.slippage_tracker"
    if mod_name in sys.modules:
        return sys.modules[mod_name]

    # Önce core paketini sys.modules'e sahte olarak ekle (gerçek __init__ olmadan)
    import types

    if "core" not in sys.modules:
        fake_core = types.ModuleType("core")
        fake_core.__path__ = [str(ROOT / "core")]
        fake_core.__package__ = "core"
        sys.modules["core"] = fake_core

    path = ROOT / "core" / "slippage_tracker.py"
    spec = importlib.util.spec_from_file_location(mod_name, path)
    mod = importlib.util.module_from_spec(spec)
    mod.__package__ = "core"
    sys.modules[mod_name] = mod  # önce kaydet, sonra çalıştır
    spec.loader.exec_module(mod)
    return mod


def run_slippage_report() -> dict:
    """SlippageTracker'dan mevcut kalibrasyon raporunu üret."""
    print("\n📏 Slippage Kalibrasyon...")
    try:
        mod = _import_slippage_tracker()
        tracker = mod.SlippageTracker()
        cal = tracker.calibrate(min_records=5)
        print(tracker.weekly_report())
        return cal
    except Exception as e:
        print(f"  ⚠️  Slippage tracker: {e}")
        return {"error": str(e)}


# ══════════════════════════════════════════════════════════════════════════
# Adım 4 — Markdown özet raporu
# ══════════════════════════════════════════════════════════════════════════


def write_summary_report(
    ab: dict,
    wf_mc: dict,
    slippage: dict,
    out_path: Path,
) -> None:
    """Tüm bulguları tek Markdown'a yaz."""

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        f"# FinPilot Haftalık Test Raporu — {now}",
        "",
        "---",
        "",
        "## 1. A/B Backtest Özeti",
        "",
        "| Metrik | Strateji A | Strateji B | Fark |",
        "|--------|-----------|-----------|------|",
    ]

    a = ab.get("A", {})
    b = ab.get("B", {})
    for label, key in [
        ("TP (Doğru Pozitif)", "tp"),
        ("FP (Yanlış Pozitif)", "fp"),
        ("FN (Kaçırılan)", "fn"),
        ("Precision", "precision"),
        ("Recall", "recall"),
        ("F1 Skoru", "f1"),
        ("Kâr ($)", "profit"),
        ("Toplam Sinyal", "signals"),
    ]:
        av = a.get(key, "—")
        bv = b.get(key, "—")
        try:
            diff = round(float(bv) - float(av), 2)
            diff_str = f"+{diff}" if diff >= 0 else str(diff)
        except Exception:
            diff_str = "—"
        lines.append(f"| {label} | {av} | {bv} | {diff_str} |")

    winner = "B" if b.get("profit", 0) > a.get("profit", 0) else "A"
    lines += [
        "",
        f"> **Kazanan:** Strateji **{winner}** — "
        f"Kâr farkı ${abs(b.get('profit',0) - a.get('profit',0)):,.2f}",
        "",
        "---",
        "",
        "## 2. Walk-Forward Doğrulama",
        "",
    ]

    wf_sum = wf_mc.get("walk_forward", {}).get("summary", {})
    wf_meta = wf_mc.get("walk_forward", {}).get("metadata", {})
    lines += [
        f"- Veri aralığı: `{wf_meta.get('data_range','N/A')}`",
        f"- Pencere sayısı: **{wf_meta.get('n_windows','?')}** "
        f"({wf_meta.get('train_days','?')}g eğitim / {wf_meta.get('test_days','?')}g test)",
        "",
        "| Metrik | A | B |",
        "|--------|---|---|",
    ]
    for label, key in [
        ("OOS Toplam Kâr ($)", "oos_total_profit"),
        ("Deflated Sharpe", "deflated_sharpe"),
        ("Kazançlı Pencere %", "pct_windows_profitable"),
        ("IS/OOS Korelasyon", "oos_is_consistency"),
    ]:
        av = wf_sum.get("A", {}).get(key, "—")
        bv = wf_sum.get("B", {}).get(key, "—")
        lines.append(f"| {label} | {av} | {bv} |")

    lines += ["", "---", "", "## 3. Monte Carlo Anlamlılık", ""]
    for strat in ["A", "B"]:
        mc = wf_mc.get("monte_carlo", {}).get(strat, {})
        sig = mc.get("significance", {})
        real = mc.get("real_metrics", {})
        dist = mc.get("mc_distribution", {})
        lines += [
            f"**Strateji {strat}:**",
            f"- Gerçek getiri: **{real.get('total_return_pct','—')}%**  "
            f"(MC ortanca: {dist.get('return_p50','—')}%)",
            f"- Sharpe p-değeri: **{sig.get('p_value_sharpe','—')}**",
            f"- {sig.get('interpretation','—')}",
            "",
        ]

    lines += ["---", "", "## 4. Slippage Kalibrasyon", ""]
    if "error" in slippage:
        lines.append(f"> ⚠️ {slippage['error']}")
    else:
        n = slippage.get("n_records", 0)
        b_mean = slippage.get("buy_slip", {}).get("mean", 0.002) * 100
        s_mean = slippage.get("sell_slip", {}).get("mean", 0.0015) * 100
        kl = slippage.get("kyle_lambda", 0.10)
        lines += [
            f"- Kayıt sayısı: **{n}** "
            f"({'kalibrasyon aktif' if slippage.get('calibrated') else 'varsayılan değerler'})",
            f"- Alış slippage: **{b_mean:.3f}%**",
            f"- Satış slippage: **{s_mean:.3f}%**",
            f"- Kyle λ: **{kl:.4f}** (piyasa etkisi katsayısı)",
            f"- Gidiş-dönüş maliyet ≈ **{(b_mean + s_mean + 0.10):.3f}%** ($3K pozisyon)",
        ]

    lines += [
        "",
        "---",
        "",
        "## 5. Öneri Özeti",
        "",
        "| Kriter | Durum |",
        "|--------|-------|",
    ]

    dsr_b = wf_sum.get("B", {}).get("deflated_sharpe", -999)
    p_b = wf_mc.get("monte_carlo", {}).get("B", {}).get("significance", {}).get("p_value_sharpe", 1)
    win_b = wf_sum.get("B", {}).get("pct_windows_profitable", 0)
    profit_b = b.get("profit", 0)

    checks = [
        ("Strateji B kârlı mı?", "✅" if profit_b > 0 else "❌", f"${profit_b:,.2f}"),
        ("Walk-Forward DSR > 0.5?", "✅" if dsr_b > 0.5 else "❌", f"{dsr_b:.3f}"),
        ("Monte Carlo p < 0.05?", "✅" if p_b < 0.05 else "⚠️", f"{p_b:.4f}"),
        ("Kazançlı pencere > 50%?", "✅" if win_b > 50 else "⚠️", f"{win_b:.0f}%"),
        ("Slippage kalibre mi?", "✅" if slippage.get("calibrated") else "⚠️ Veri biriksin", ""),
    ]
    for label, status, val in checks:
        lines.append(f"| {label} | {status} {val} |")

    all_green = profit_b > 0 and dsr_b > 0.5 and p_b < 0.05 and win_b > 50
    rec = (
        "🟢 **Strateji B canlıya hazır.** Tüm filtreler geçildi."
        if all_green
        else "🟡 **Strateji B ek doğrulama gerektiriyor.** Zayıf kriterler var."
        if profit_b > 0
        else "🔴 **Strateji B henüz canlıya alınmamalı.** Daha fazla veri birikmeli."
    )
    lines += ["", f"> {rec}", "", "---", f"*FinPilot otomatik rapor — {now}*"]

    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n💾 Özet rapor: {out_path}")


# ══════════════════════════════════════════════════════════════════════════
# Ana çalıştırıcı
# ══════════════════════════════════════════════════════════════════════════


def main():
    parser = argparse.ArgumentParser(description="FinPilot Master Test Koşucu")
    parser.add_argument("--quick", action="store_true", help="Sadece A/B + Slippage")
    parser.add_argument("--wf-only", action="store_true", help="Sadece Walk-Forward")
    parser.add_argument(
        "--days", type=int, default=365, help="Kaç günlük shortlist (varsayılan 365)"
    )
    parser.add_argument("--n-sims", type=int, default=1000)
    parser.add_argument("--demo", action="store_true", help="Gerçek CSV yerine demo veri")
    args = parser.parse_args()

    print("=" * 70)
    print("🚀 FinPilot Master Test Koşucu")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 70)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    results = {"timestamp": datetime.now().isoformat(), "steps": {}}
    errors = []

    # ── Veri yükle ─────────────────────────────────────────────────────────
    print("\n📂 Shortlist verileri yükleniyor...")
    if args.demo:
        df = _demo_df()
        print("  ℹ️  Demo modu aktif")
    else:
        df = load_shortlists(days_back=args.days)

    if df.empty:
        print("❌ Veri yüklenemedi. Çıkılıyor.")
        sys.exit(1)

    results["data_info"] = {
        "rows": len(df),
        "date_range": f"{df['date'].min().date()} → {df['date'].max().date()}"
        if "date" in df.columns
        else "N/A",
    }

    # ── A/B Backtest ───────────────────────────────────────────────────────
    if not args.wf_only:
        try:
            ab = run_ab_backtest(df)
            results["steps"]["ab_backtest"] = ab
        except Exception as e:
            print(f"  ❌ A/B Backtest hatası: {e}")
            errors.append(f"ab_backtest: {e}")
            ab = {}
    else:
        ab = {}

    # ── Walk-Forward + Monte Carlo ─────────────────────────────────────────
    wf_mc = {}
    if not args.quick:
        try:
            wf_mc = run_wf_mc(df, n_sims=args.n_sims)
            results["steps"]["wf_mc"] = {
                "wf_summary": wf_mc["walk_forward"].get("summary", {}),
                "mc_significance": {
                    k: v.get("significance", {}) for k, v in wf_mc.get("monte_carlo", {}).items()
                },
            }
        except Exception as e:
            print(f"  ❌ Walk-Forward/MC hatası: {e}")
            traceback.print_exc()
            errors.append(f"wf_mc: {e}")

    # ── Slippage ───────────────────────────────────────────────────────────
    try:
        slippage = run_slippage_report()
        results["steps"]["slippage"] = slippage
    except Exception as e:
        print(f"  ❌ Slippage hatası: {e}")
        errors.append(f"slippage: {e}")
        slippage = {}

    # ── Özet rapor ─────────────────────────────────────────────────────────
    out_md = DATA_DIR / f"finpilot_weekly_report_{TS}.md"
    out_json = DATA_DIR / f"finpilot_weekly_report_{TS}.json"

    try:
        write_summary_report(ab, wf_mc, slippage, out_md)
    except Exception as e:
        print(f"  ❌ Rapor hatası: {e}")
        errors.append(f"report: {e}")

    results["errors"] = errors
    out_json.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    print(f"💾 JSON sonuç:  {out_json}")

    # ── Final özet ─────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    if errors:
        print(f"⚠️  {len(errors)} adımda hata oluştu: {', '.join(errors)}")
    else:
        print("✅ Tüm adımlar başarıyla tamamlandı.")
    print("=" * 70)

    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
