#!/usr/bin/env python3
"""
FinPilot — Walk-Forward Validation + Monte Carlo Simülasyonu
=============================================================

Amaç:
  Backtest sonuçlarını veri snooping'e karşı sertleştirmek.
  "Backtest ile gerçek arasındaki fark" analizinin 3. katmanı.

İki ana modül:
  1. WalkForwardValidator  — rolling train/test penceresiyle out-of-sample doğrulama
  2. MonteCarloSimulator   — trade sırası karıştırarak şans payını ölç

Kullanım (CLI):
  python scripts/walkforward_montecarlo.py \\
      --csv data/shortlist_20260419.csv \\
      --out data/wf_mc_report_$(date +%Y%m%d).json

Kullanım (import):
  from scripts.walkforward_montecarlo import WalkForwardValidator, MonteCarloSimulator

  wf  = WalkForwardValidator(df, train_days=90, test_days=30)
  res = wf.run()

  mc  = MonteCarloSimulator(trades_pnl=[...])
  mc_res = mc.run(n_simulations=1000)

Bağımlılıklar: numpy, pandas (scipy yok — proxy engelini aşmak için)
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

# ── Proje kök dizini ───────────────────────────────────────────────────────
_ROOT = Path(__file__).parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

try:
    from core.slippage_tracker import RealisticBacktestCosts as _RBC  # noqa: F401
    from core.slippage_tracker import SlippageTracker as _ST  # noqa: F401

    _TRACKER_OK = True
except ImportError:
    _TRACKER_OK = False


# ══════════════════════════════════════════════════════════════════════════
# Yardımcı istatistik fonksiyonları (scipy bağımlılığı yok)
# ══════════════════════════════════════════════════════════════════════════


def _sharpe(returns: np.ndarray, ann: int = 252) -> float:
    """Yıllıklaştırılmış Sharpe oranı."""
    if len(returns) < 2 or returns.std() < 1e-9:
        return 0.0
    return float(np.sqrt(ann) * returns.mean() / returns.std())


def _max_drawdown(cum_returns: np.ndarray) -> float:
    """Peak-to-trough maksimum drawdown (%)."""
    peak = np.maximum.accumulate(cum_returns)
    dd = (cum_returns - peak) / (np.abs(peak) + 1e-9)
    return float(dd.min() * 100)


def _profit_factor(pnls: np.ndarray) -> float:
    wins = pnls[pnls > 0].sum()
    losses = np.abs(pnls[pnls < 0].sum())
    return float(wins / losses) if losses > 0 else float("inf")


def _deflated_sharpe(raw_sharpe: float, n_trials: int, n_obs: int) -> float:
    """
    Bailey & de Prado (2014) Deflated Sharpe Ratio.
    n_trials: test edilen parametre kombinasyonu sayısı
    n_obs:    gözlem sayısı (gün)
    """
    import math

    if n_trials <= 1 or n_obs <= 1:
        return raw_sharpe
    # Expected max Sharpe under H0 (normal approx)
    gamma_euler = 0.5772156649
    _ = (1 - gamma_euler) * math.erfc(math.sqrt(math.log(n_trials) / 2)) + gamma_euler * math.erfc(
        math.sqrt(math.log(n_trials / 2) / 2)
    )
    # Simplified: expected max ≈ sqrt(2 * log(n_trials))
    # (Bailey approximation)
    e_max_approx = math.sqrt(2.0 * math.log(n_trials))
    # Deflation factor
    deflation = 1.0 - e_max_approx / math.sqrt(n_obs)
    return float(raw_sharpe * max(0.0, deflation))


# ══════════════════════════════════════════════════════════════════════════
# Strateji parametreleri — shortlist CSV formatına uyarlanmış
# ══════════════════════════════════════════════════════════════════════════

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

# Profit formülü (ab_backtest.py ile aynı)
TP_UNIT = 1000 * (0.52 * 0.067 - 0.48 * 0.020)  # ≈ $24.52
FP_COST = 15.00
FN_COST = 5.00


def _apply_strategy(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    """Filtre eşiklerini uygula ve predicted=True olanları işaretle."""
    mask = (
        (df.get("alignment_ratio", pd.Series(1.0, index=df.index)) >= params["min_alignment_ratio"])
        & (df.get("momentum_ratio", pd.Series(1.0, index=df.index)) >= params["min_momentum_ratio"])
        & (df.get("filter_score", pd.Series(99, index=df.index)) >= params["min_filter_score"])
        & (df.get("signal_score", pd.Series(99, index=df.index)) >= params["min_signal_score"])
        & (df.get("zscore", pd.Series(99, index=df.index)) >= params["min_zscore"])
        & (df.get("price_filter", pd.Series(99, index=df.index)) >= params["min_price_filter"])
    )
    out = df.copy()
    out["predicted"] = mask
    return out


def _compute_period_profit(sub: pd.DataFrame, params: dict) -> float:
    """Bir penceredeki profit'i hesapla."""
    pred = _apply_strategy(sub, params)
    gt = sub.get("ground_truth", pd.Series(False, index=sub.index))
    tp = int((pred["predicted"] & gt).sum())
    fp = int((pred["predicted"] & ~gt).sum())
    fn = int((~pred["predicted"] & gt).sum())
    return tp * TP_UNIT - fp * FP_COST - fn * FN_COST


# ══════════════════════════════════════════════════════════════════════════
# WalkForwardValidator
# ══════════════════════════════════════════════════════════════════════════


class WalkForwardValidator:
    """
    Rolling train/test penceresiyle out-of-sample doğrulama.

    Parametreler:
        df         : shortlist DataFrame (date sütunu veya DatetimeIndex)
        train_days : eğitim penceresi (gün)
        test_days  : test penceresi (gün)
        strategies : {"A": params_dict, "B": params_dict, ...}
        n_trials   : Deflated Sharpe için kombinsyon sayısı
    """

    def __init__(
        self,
        df: pd.DataFrame,
        train_days: int = 90,
        test_days: int = 30,
        strategies: dict | None = None,
        n_trials: int = 3456,
    ):
        self.df = self._prepare(df)
        self.train_days = train_days
        self.test_days = test_days
        self.strategies = strategies or {"A": STRATEGY_A, "B": STRATEGY_B}
        self.n_trials = n_trials

    def _prepare(self, df: pd.DataFrame) -> pd.DataFrame:
        """DatetimeIndex'e çevir, sırala."""
        out = df.copy()
        if "date" in out.columns:
            out["date"] = pd.to_datetime(out["date"])
            out = out.set_index("date")
        elif not isinstance(out.index, pd.DatetimeIndex):
            out.index = pd.to_datetime(out.index)
        return out.sort_index()

    def run(self) -> dict:
        """Walk-forward testi çalıştır."""
        dates = self.df.index
        min_date = dates.min()
        max_date = dates.max()
        total_days = (max_date - min_date).days

        if total_days < self.train_days + self.test_days:
            return {"error": f"Yetersiz veri: {total_days} gün < {self.train_days+self.test_days}"}

        windows = []
        oos_profits = {k: [] for k in self.strategies}
        is_profits = {k: [] for k in self.strategies}

        # Rolling windows
        cursor = min_date
        while True:
            train_end = cursor + pd.Timedelta(days=self.train_days)
            test_end = train_end + pd.Timedelta(days=self.test_days)
            if test_end > max_date:
                break

            train_df = self.df[(self.df.index >= cursor) & (self.df.index < train_end)]
            test_df = self.df[(self.df.index >= train_end) & (self.df.index < test_end)]

            if len(train_df) < 10 or len(test_df) < 5:
                cursor += pd.Timedelta(days=self.test_days)
                continue

            win = {
                "train_start": cursor.isoformat(),
                "train_end": train_end.isoformat(),
                "test_start": train_end.isoformat(),
                "test_end": test_end.isoformat(),
                "train_n": len(train_df),
                "test_n": len(test_df),
                "strategies": {},
            }

            for name, params in self.strategies.items():
                is_p = _compute_period_profit(train_df, params)
                oos_p = _compute_period_profit(test_df, params)
                win["strategies"][name] = {
                    "in_sample_profit": round(is_p, 2),
                    "out_of_sample_profit": round(oos_p, 2),
                    "oos_is_ratio": round(oos_p / max(abs(is_p), 1e-9), 4),
                }
                is_profits[name].append(is_p)
                oos_profits[name].append(oos_p)

            windows.append(win)
            cursor += pd.Timedelta(days=self.test_days)

        if not windows:
            return {"error": "Geçerli pencere bulunamadı."}

        # Özet istatistikler
        summary = {}
        for name in self.strategies:
            oos = np.array(oos_profits[name])
            is_ = np.array(is_profits[name])

            if len(oos) == 0:
                continue

            # Sharpe (window bazında günlük profit)
            oos_sharpe = _sharpe(oos / max(self.test_days, 1))
            dsr = _deflated_sharpe(oos_sharpe, self.n_trials, len(oos) * self.test_days)

            summary[name] = {
                "n_windows": len(oos),
                "oos_total_profit": round(float(oos.sum()), 2),
                "oos_mean_profit": round(float(oos.mean()), 2),
                "oos_std_profit": round(float(oos.std()), 2),
                "oos_win_rate": round(float((oos > 0).mean() * 100), 1),
                "oos_sharpe": round(oos_sharpe, 3),
                "deflated_sharpe": round(dsr, 3),
                "is_total_profit": round(float(is_.sum()), 2),
                "oos_is_consistency": round(float(np.corrcoef(is_, oos)[0, 1]), 3)
                if len(is_) > 2
                else None,
                "best_window_profit": round(float(oos.max()), 2),
                "worst_window_profit": round(float(oos.min()), 2),
                "pct_windows_profitable": round(float((oos > 0).mean() * 100), 1),
            }

        return {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "train_days": self.train_days,
                "test_days": self.test_days,
                "n_windows": len(windows),
                "data_range": f"{min_date.date()} → {max_date.date()}",
                "n_trials_dsr": self.n_trials,
            },
            "summary": summary,
            "windows": windows,
        }


# ══════════════════════════════════════════════════════════════════════════
# MonteCarloSimulator
# ══════════════════════════════════════════════════════════════════════════


class MonteCarloSimulator:
    """
    Trade sırası karıştırarak şans payını ölçer.

    Bir backtest sonucunun ne kadarı gerçek edge'den,
    ne kadarı trade sırasının şansından geliyor?

    Parametreler:
        trades_pnl    : Her trade'in P&L listesi [$]
        initial_cap   : Başlangıç sermayesi (equity curve için)
        n_simulations : Kaç farklı sıralama dene
    """

    def __init__(
        self,
        trades_pnl: list[float],
        initial_cap: float = 10_000.0,
        n_simulations: int = 1000,
    ):
        self.pnl = np.array(trades_pnl, dtype=float)
        self.cap = initial_cap
        self.n_sims = n_simulations

    def run(self) -> dict:
        """Monte Carlo simülasyonunu çalıştır."""
        if len(self.pnl) == 0:
            return {"error": "Boş trade listesi"}

        rng = np.random.default_rng(seed=42)
        total_returns = []
        sharpes = []
        max_dds = []
        profit_factors = []

        for _ in range(self.n_sims):
            shuffled = rng.permutation(self.pnl)
            cum = self.cap + np.cumsum(shuffled)
            daily_ret = np.diff(cum) / (cum[:-1] + 1e-9)

            total_returns.append(float((cum[-1] - self.cap) / self.cap * 100))
            sharpes.append(_sharpe(daily_ret))
            max_dds.append(_max_drawdown(cum))
            profit_factors.append(_profit_factor(shuffled))

        total_returns = np.array(total_returns)
        sharpes = np.array(sharpes)
        max_dds = np.array(max_dds)
        profit_factors = np.array(profit_factors)

        # Gerçek (orijinal sıra) metrikler
        real_cum = self.cap + np.cumsum(self.pnl)
        real_ret = np.diff(real_cum) / (real_cum[:-1] + 1e-9)
        real_total = float((real_cum[-1] - self.cap) / self.cap * 100)
        real_sharpe = _sharpe(real_ret)
        real_dd = _max_drawdown(real_cum)
        real_pf = _profit_factor(self.pnl)

        # P-value: gerçek sonuç, rastgele dağılımda nerede?
        p_return = float((total_returns >= real_total).mean())
        p_sharpe = float((sharpes >= real_sharpe).mean())

        def _pct(arr, q):
            return round(float(np.percentile(arr, q)), 3)

        return {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "n_trades": len(self.pnl),
                "n_simulations": self.n_sims,
                "initial_cap": self.cap,
            },
            "real_metrics": {
                "total_return_pct": round(real_total, 2),
                "sharpe": round(real_sharpe, 3),
                "max_drawdown_pct": round(real_dd, 2),
                "profit_factor": round(real_pf, 3),
                "total_pnl": round(float(self.pnl.sum()), 2),
            },
            "mc_distribution": {
                "return_p5": _pct(total_returns, 5),
                "return_p25": _pct(total_returns, 25),
                "return_p50": _pct(total_returns, 50),
                "return_p75": _pct(total_returns, 75),
                "return_p95": _pct(total_returns, 95),
                "sharpe_p5": _pct(sharpes, 5),
                "sharpe_p50": _pct(sharpes, 50),
                "sharpe_p95": _pct(sharpes, 95),
                "dd_worst": _pct(max_dds, 5),
                "dd_median": _pct(max_dds, 50),
                "pf_p25": _pct(profit_factors, 25),
                "pf_p75": _pct(profit_factors, 75),
            },
            "significance": {
                "p_value_return": round(p_return, 4),
                "p_value_sharpe": round(p_sharpe, 4),
                "return_significant_5pct": p_return < 0.05,
                "sharpe_significant_5pct": p_sharpe < 0.05,
                "pct_sims_above_real_return": round(p_return * 100, 1),
                "interpretation": (
                    "✅ Güçlü edge: sonuç şans eseri değil"
                    if p_sharpe < 0.05
                    else "⚠️  Zayıf edge: şans payı yüksek"
                    if p_sharpe < 0.20
                    else "❌ Şansa dayalı: sonuç rastgele dağılımdan ayırt edilemiyor"
                ),
            },
        }


# ══════════════════════════════════════════════════════════════════════════
# Markdown rapor üretici
# ══════════════════════════════════════════════════════════════════════════


def generate_report(wf_result: dict, mc_results: dict, out_path: Path) -> str:
    """Walk-Forward + Monte Carlo bulgularını Markdown'a yaz."""

    lines = [
        "# FinPilot — Walk-Forward & Monte Carlo Raporu",
        f"**Üretim tarihi:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "---",
        "",
        "## 1. Walk-Forward Doğrulama",
        "",
    ]

    meta = wf_result.get("metadata", {})
    lines += [
        f"- Veri aralığı: `{meta.get('data_range', 'N/A')}`",
        f"- Eğitim penceresi: **{meta.get('train_days', '?')} gün**",
        f"- Test penceresi: **{meta.get('test_days', '?')} gün**",
        f"- Toplam pencere sayısı: **{meta.get('n_windows', '?')}**",
        f"- DSR düzeltmesi için kombinsyon: **{meta.get('n_trials_dsr', '?')}**",
        "",
        "### Strateji Karşılaştırması (Out-of-Sample)",
        "",
        "| Metrik | Strateji A | Strateji B |",
        "|--------|-----------|-----------|",
    ]

    summ = wf_result.get("summary", {})
    metrics = [
        ("OOS Toplam Kâr ($)", "oos_total_profit"),
        ("OOS Ortalama Kâr/Pencere ($)", "oos_mean_profit"),
        ("OOS Kazançlı Pencere (%)", "pct_windows_profitable"),
        ("OOS Sharpe", "oos_sharpe"),
        ("Deflated Sharpe", "deflated_sharpe"),
        ("IS/OOS Korelasyon", "oos_is_consistency"),
        ("En İyi Pencere ($)", "best_window_profit"),
        ("En Kötü Pencere ($)", "worst_window_profit"),
    ]

    a = summ.get("A", {})
    b = summ.get("B", {})
    for label, key in metrics:
        av = a.get(key, "—")
        bv = b.get(key, "—")
        lines.append(f"| {label} | {av} | {bv} |")

    lines += [
        "",
        "> **Deflated Sharpe Nedir?**  ",
        "> Bailey & de Prado (2014) metoduyla; test edilen kombinasyon sayısına göre  ",
        "> Sharpe oranını aşağı düzelterek veri snooping etkisini giderir.  ",
        "> DSR > 0.5 → güvenilir; DSR < 0 → muhtemelen overfit.",
        "",
        "---",
        "",
        "## 2. Monte Carlo Simülasyonu",
        "",
    ]

    for strat, mc in mc_results.items():
        if "error" in mc:
            lines += [f"### Strateji {strat}", f"> {mc['error']}", ""]
            continue

        real = mc.get("real_metrics", {})
        dist = mc.get("mc_distribution", {})
        sig = mc.get("significance", {})
        meta2 = mc.get("metadata", {})

        lines += [
            f"### Strateji {strat} ({meta2.get('n_simulations', '?')} simülasyon, {meta2.get('n_trades', '?')} trade)",
            "",
            "**Gerçek Backtest Metrikleri:**",
            "",
            "| Metrik | Gerçek | MC p50 | MC p5 | MC p95 |",
            "|--------|--------|--------|-------|--------|",
            f"| Toplam Getiri (%) | {real.get('total_return_pct', '—')} | {dist.get('return_p50', '—')} | {dist.get('return_p5', '—')} | {dist.get('return_p95', '—')} |",
            f"| Sharpe Oranı | {real.get('sharpe', '—')} | {dist.get('sharpe_p50', '—')} | {dist.get('sharpe_p5', '—')} | {dist.get('sharpe_p95', '—')} |",
            f"| Max Drawdown (%) | {real.get('max_drawdown_pct', '—')} | {dist.get('dd_median', '—')} | — | {dist.get('dd_worst', '—')} |",
            f"| Profit Factor | {real.get('profit_factor', '—')} | — | {dist.get('pf_p25', '—')} | {dist.get('pf_p75', '—')} |",
            "",
            "**İstatistiksel Anlamlılık:**",
            "",
            f"- Getiri p-değeri: **{sig.get('p_value_return', '—')}** (simülasyonların `{sig.get('pct_sims_above_real_return', '—')}%`'i gerçek sonucu geçti)",
            f"- Sharpe p-değeri: **{sig.get('p_value_sharpe', '—')}**",
            f"- Değerlendirme: {sig.get('interpretation', '—')}",
            "",
        ]

    lines += [
        "---",
        "",
        "## 3. Yorumlar ve Öneriler",
        "",
        "### Walk-Forward Bulguları",
        "",
        "Eğer Strateji B'nin **Deflated Sharpe > 0.5** ve **IS/OOS korelasyonu > 0.3** ise:",
        "- Parametreler gerçek bir edge'i yakalıyor, overfit değil.",
        "- Canlı trading'e geçiş için yeşil ışık.",
        "",
        "Eğer DSR < 0 veya korelasyon negatifse:",
        "- Parametreler geçmiş veriye overfit olmuş.",
        "- Daha az parametre veya daha geniş aralık dene.",
        "",
        "### Monte Carlo Bulguları",
        "",
        "- **p < 0.05**: Strateji istatistiksel olarak anlamlı — şans payı düşük.",
        "- **p > 0.20**: Sonuçlar büyük ölçüde şansa bağlı — stratejiyi yeniden değerlendir.",
        "- MC p5 getiri negatifse → kötü şans senaryosunda zarar riski var.",
        "",
        "### Otomasyona Alma",
        "",
        "Bu scripti haftalık çalıştırmak için cron veya APScheduler:",
        "",
        "```bash",
        "# Her Pazartesi 07:00'de çalıştır",
        "0 7 * * 1 cd /path/to/Borsa && python scripts/walkforward_montecarlo.py \\",
        "    --csv data/shortlist_latest.csv \\",
        "    --out data/wf_mc_$(date +%Y%m%d).json",
        "```",
        "",
        "---",
        f"*FinPilot Walk-Forward + Monte Carlo Engine v1.0 — {datetime.now().strftime('%Y-%m-%d')}*",
    ]

    report = "\n".join(lines)
    out_path.write_text(report, encoding="utf-8")
    return report


# ══════════════════════════════════════════════════════════════════════════
# CLI entry point
# ══════════════════════════════════════════════════════════════════════════


def main():
    parser = argparse.ArgumentParser(description="FinPilot Walk-Forward + Monte Carlo Analizi")
    parser.add_argument("--csv", default=None, help="Shortlist CSV dosyası (date sütunlu)")
    parser.add_argument("--out", default=None, help="Çıktı JSON dosyası")
    parser.add_argument("--train-days", type=int, default=90)
    parser.add_argument("--test-days", type=int, default=30)
    parser.add_argument("--n-sims", type=int, default=1000)
    parser.add_argument(
        "--n-trials", type=int, default=3456, help="Deflated Sharpe için kombinsyon sayısı"
    )
    parser.add_argument("--demo", action="store_true", help="CSV yoksa demo verisiyle çalıştır")
    args = parser.parse_args()

    # ── Veri yükle ────────────────────────────────────────────────────────
    if args.csv and Path(args.csv).exists():
        df = pd.read_csv(args.csv, parse_dates=["date"])
        print(f"📂 Veri yüklendi: {args.csv} ({len(df)} satır)")
    elif args.demo or not args.csv:
        print("ℹ️  Demo modu — sentetik veri üretiliyor...")
        np.random.seed(42)
        n = 500
        dates = pd.date_range("2025-09-01", periods=n, freq="B")
        df = pd.DataFrame(
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
    else:
        print(f"❌ CSV bulunamadı: {args.csv}")
        sys.exit(1)

    # ── Walk-Forward ──────────────────────────────────────────────────────
    print(f"\n🔄 Walk-Forward ({args.train_days}g eğitim / {args.test_days}g test)...")
    wf = WalkForwardValidator(df, args.train_days, args.test_days, n_trials=args.n_trials)
    wf_res = wf.run()

    if "error" in wf_res:
        print(f"❌ Walk-Forward hatası: {wf_res['error']}")
        sys.exit(1)

    n_win = wf_res["metadata"]["n_windows"]
    print(f"   ✅ {n_win} pencere tamamlandı")

    for strat, s in wf_res["summary"].items():
        print(f"\n   Strateji {strat}:")
        print(f"     OOS Toplam Kâr:     ${s['oos_total_profit']:,.2f}")
        print(f"     Deflated Sharpe:     {s['deflated_sharpe']:.3f}")
        print(f"     Kazançlı Pencere:    {s['pct_windows_profitable']:.1f}%")
        print(f"     IS/OOS Korelasyon:   {s.get('oos_is_consistency', 'N/A')}")

    # ── Monte Carlo ───────────────────────────────────────────────────────
    print(f"\n🎲 Monte Carlo ({args.n_sims} simülasyon)...")
    mc_results = {}
    for strat, params in {"A": STRATEGY_A, "B": STRATEGY_B}.items():
        pred_df = _apply_strategy(df, params)
        gt = df.get("ground_truth", pd.Series(False, index=df.index))

        # Her trade'in P&L'i: TP → +TP_UNIT, FP → -FP_COST
        pnls = []
        for _, row in pred_df.iterrows():
            p = row.get("predicted", False)
            g = bool(gt.loc[row.name]) if row.name in gt.index else False
            if p and g:
                pnls.append(TP_UNIT)
            elif p and not g:
                pnls.append(-FP_COST)
            elif not p and g:
                pnls.append(-FN_COST)

        mc = MonteCarloSimulator(pnls, initial_cap=10_000.0, n_simulations=args.n_sims)
        mc_results[strat] = mc.run()
        sig = mc_results[strat].get("significance", {})
        print(f"\n   Strateji {strat}:")
        print(f"     Gerçek Getiri:  {mc_results[strat]['real_metrics']['total_return_pct']:.2f}%")
        print(f"     Sharpe p-val:   {sig.get('p_value_sharpe', 'N/A')}")
        print(f"     {sig.get('interpretation', '')}")

    # ── Çıktı kaydet ──────────────────────────────────────────────────────
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    json_path = Path(args.out) if args.out else data_dir / f"wf_mc_{ts}.json"
    md_path = json_path.with_suffix(".md")

    combined = {
        "walk_forward": wf_res,
        "monte_carlo": mc_results,
    }
    json_path.write_text(json.dumps(combined, indent=2, default=str), encoding="utf-8")
    print(f"\n💾 JSON:     {json_path}")

    generate_report(wf_res, mc_results, md_path)
    print(f"💾 Rapor:    {md_path}")

    # Borsa/data'ya da kaydet (eğer farklı bir konumsa)
    borsa_data = Path(__file__).parent.parent / "data"
    borsa_data.mkdir(parents=True, exist_ok=True)
    if json_path.parent.resolve() != borsa_data.resolve():
        import shutil

        shutil.copy2(json_path, borsa_data / json_path.name)
        shutil.copy2(md_path, borsa_data / md_path.name)
        print(f"💾 Borsa/data: {md_path.name}")

    print("\n✅ Walk-Forward + Monte Carlo tamamlandı.")
    return combined


if __name__ == "__main__":
    main()
