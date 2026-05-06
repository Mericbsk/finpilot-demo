"""
FinPilot — Gerçekçi Slippage Tracker & Kalibrasyon Modülü
==========================================================

Ne yapar:
  1. Her paper/canlı işlemde sinyal fiyatı vs gerçek dolum fiyatını kaydeder
  2. Birikim veriyle gerçek slippage katsayısını hesaplar
  3. Backtest motoruna dinamik slippage modeli sağlar
  4. Haftalık kalibrasyon raporu üretir

Kullanım:
  from core.slippage_tracker import SlippageTracker, RealisticBacktestCosts

  tracker = SlippageTracker()
  tracker.record_fill("AAPL", signal_price=150.0, fill_price=150.35,
                       direction="buy", shares=10, avg_volume=80_000_000)
  costs = RealisticBacktestCosts.from_tracker(tracker)
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

TRACKER_FILE = Path(__file__).parent.parent / "logs" / "slippage_tracker.json"
TRACKER_FILE.parent.mkdir(parents=True, exist_ok=True)


# ── Veri yapıları ──────────────────────────────────────────────────────────


@dataclass
class FillRecord:
    timestamp: str
    symbol: str
    direction: str  # 'buy' veya 'sell'
    signal_price: float  # Scanner'ın gördüğü fiyat
    fill_price: float  # Gerçekte doldurulan fiyat
    shares: int
    avg_volume: float  # Günlük ortalama hacim
    position_usd: float  # İşlem büyüklüğü $
    source: str  # 'paper' | 'live' | 'simulation'

    @property
    def slippage_pct(self) -> float:
        """Slippage yüzdesi — alışta pozitif = kötü, satışta negatif = kötü."""
        if self.signal_price == 0:
            return 0.0
        raw = (self.fill_price - self.signal_price) / self.signal_price
        # Alışta yukarı, satışta aşağı gitmek kötü
        return raw if self.direction == "buy" else -raw

    @property
    def slippage_usd(self) -> float:
        return abs(self.fill_price - self.signal_price) * self.shares

    @property
    def participation_rate(self) -> float:
        """Emrin günlük hacme oranı."""
        if self.avg_volume == 0:
            return 0.0
        return self.position_usd / (self.avg_volume * self.signal_price)


# ══════════════════════════════════════════════════════════════════════════
# SlippageTracker — veri toplama ve kalibrasyon
# ══════════════════════════════════════════════════════════════════════════


class SlippageTracker:
    """
    Paper ve canlı işlemlerden slippage verisi toplar.
    Backtest motorunun doğru katsayıları kullanmasını sağlar.
    """

    def __init__(self, tracker_file: Path = TRACKER_FILE):
        self.file = tracker_file
        self.records: list[FillRecord] = []
        self._load()

    def _load(self):
        if self.file.exists():
            try:
                with open(self.file) as f:
                    data = json.load(f)
                self.records = [FillRecord(**r) for r in data.get("records", [])]
                logger.info(f"SlippageTracker: {len(self.records)} kayıt yüklendi.")
            except Exception as e:
                logger.warning(f"Tracker yüklenemedi: {e}")

    def save(self):
        with open(self.file, "w") as f:
            json.dump(
                {
                    "last_updated": datetime.now().isoformat(),
                    "total_records": len(self.records),
                    "records": [asdict(r) for r in self.records],
                },
                f,
                indent=2,
            )

    # ── Kayıt ─────────────────────────────────────────────────────────────

    def record_fill(
        self,
        symbol: str,
        signal_price: float,
        fill_price: float,
        direction: str,
        shares: int,
        avg_volume: float = 1_000_000,
        source: str = "paper",
    ):
        """
        Her işlem sonrasında çağrılır.
        scanner/signals.py → paper_trading engine içinde kullan.
        """
        rec = FillRecord(
            timestamp=datetime.now().isoformat(),
            symbol=symbol,
            direction=direction,
            signal_price=signal_price,
            fill_price=fill_price,
            shares=shares,
            avg_volume=avg_volume,
            position_usd=signal_price * shares,
            source=source,
        )
        self.records.append(rec)
        self.save()
        logger.debug(
            f"Fill kaydedildi: {symbol} {direction} "
            f"signal={signal_price:.2f} fill={fill_price:.2f} "
            f"slip={rec.slippage_pct*100:.3f}%"
        )
        return rec

    # ── Kalibrasyon ───────────────────────────────────────────────────────

    def calibrate(self, min_records: int = 10) -> dict:
        """
        Biriken veriden gerçek slippage katsayılarını hesaplar.
        Yeterli veri yoksa muhafazakâr varsayılanları döner.
        """
        if len(self.records) < min_records:
            logger.warning(
                f"Kalibrasyon için yetersiz kayıt ({len(self.records)}/{min_records}). "
                "Varsayılan değerler kullanılıyor."
            )
            return self._defaults()

        df = pd.DataFrame([asdict(r) for r in self.records])
        df["slippage_pct"] = [r.slippage_pct for r in self.records]
        df["part_rate"] = [r.participation_rate for r in self.records]

        buys = df[df["direction"] == "buy"]
        sells = df[df["direction"] == "sell"]

        def safe_stats(series):
            if len(series) == 0:
                return {"mean": 0.002, "p75": 0.004, "p95": 0.008}
            return {
                "mean": float(series.mean()),
                "p75": float(series.quantile(0.75)),
                "p95": float(series.quantile(0.95)),
            }

        # Kyle's lambda — piyasa etkisi katsayısı
        if len(df) > 5 and df["part_rate"].std() > 0:
            from numpy.polynomial import polynomial as P

            try:
                coefs = P.polyfit(df["part_rate"], df["slippage_pct"], 1)
                kyle_lambda = float(coefs[1])
            except Exception:
                kyle_lambda = 0.10
        else:
            kyle_lambda = 0.10

        result = {
            "n_records": len(df),
            "buy_slip": safe_stats(buys["slippage_pct"]),
            "sell_slip": safe_stats(sells["slippage_pct"]),
            "kyle_lambda": max(0.0, kyle_lambda),
            "avg_gap_pct": float(df["slippage_pct"].mean()),
            "calibrated": True,
            "as_of": datetime.now().isoformat(),
        }

        logger.info(
            f"Kalibrasyon tamamlandı ({len(df)} kayıt): "
            f"buy_mean={result['buy_slip']['mean']*100:.3f}% "
            f"sell_mean={result['sell_slip']['mean']*100:.3f}%"
        )
        return result

    def _defaults(self) -> dict:
        """Veri yokken muhafazakâr tahminler."""
        return {
            "n_records": 0,
            "buy_slip": {"mean": 0.0020, "p75": 0.0035, "p95": 0.0060},
            "sell_slip": {"mean": 0.0015, "p75": 0.0025, "p95": 0.0045},
            "kyle_lambda": 0.10,
            "avg_gap_pct": 0.0010,
            "calibrated": False,
            "as_of": datetime.now().isoformat(),
        }

    # ── Haftalık rapor ────────────────────────────────────────────────────

    def weekly_report(self) -> str:
        cal = self.calibrate()
        lines = [
            "=" * 55,
            "SLIPPAGE KALİBRASYON RAPORU",
            f"Tarih: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"Toplam kayıt: {cal['n_records']}",
            "=" * 55,
            f"Alış slippage  — ort: {cal['buy_slip']['mean']*100:.3f}%  "
            f"p75: {cal['buy_slip']['p75']*100:.3f}%  "
            f"p95: {cal['buy_slip']['p95']*100:.3f}%",
            f"Satış slippage — ort: {cal['sell_slip']['mean']*100:.3f}%  "
            f"p75: {cal['sell_slip']['p75']*100:.3f}%  "
            f"p95: {cal['sell_slip']['p95']*100:.3f}%",
            f"Kyle λ (piyasa etkisi): {cal['kyle_lambda']:.4f}",
            f"Ortalama gap: {cal['avg_gap_pct']*100:.3f}%",
            "=" * 55,
            "Backtest haircut tahmini (1 işlem başına, $3K pozisyon):",
        ]
        pos = 3000
        slip = (cal["buy_slip"]["mean"] + cal["sell_slip"]["mean"]) * pos
        comm = 3.00  # $1.50 × 2 taraf
        gap = cal["avg_gap_pct"] * pos
        lines += [
            f"  Slippage:   ${slip:.2f}",
            f"  Komisyon:   ${comm:.2f}",
            f"  Gap risk:   ${gap:.2f}",
            f"  Toplam:     ${slip+comm+gap:.2f}  ({(slip+comm+gap)/pos*100:.2f}%)",
        ]
        return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════════════
# RealisticBacktestCosts — backtest motoruna eklenti
# ══════════════════════════════════════════════════════════════════════════


@dataclass
class RealisticBacktestCosts:
    """
    core/backtest.py'deki BacktestConfig.slippage_rate yerine kullanılır.
    Dinamik, veri-odaklı maliyet modeli.
    """

    buy_slippage_pct: float = 0.0020  # %0.20
    sell_slippage_pct: float = 0.0015  # %0.15
    kyle_lambda: float = 0.10  # Piyasa etkisi katsayısı
    commission_per_side: float = 1.50  # $1.50 per taraf (IB Tiered)
    overnight_gap_pct: float = 0.0010  # %0.10 gap riski
    stop_slippage_pct: float = 0.0025  # Stop emirlerinde ek %0.25
    fill_rate: float = 0.92  # Emirlerin %92'si tam dolabiliyor

    @classmethod
    def from_tracker(cls, tracker: SlippageTracker) -> RealisticBacktestCosts:
        """Tracker verisiyle kalibre edilmiş maliyet modeli döner."""
        cal = tracker.calibrate()
        return cls(
            buy_slippage_pct=cal["buy_slip"]["mean"],
            sell_slippage_pct=cal["sell_slip"]["mean"],
            kyle_lambda=cal["kyle_lambda"],
            overnight_gap_pct=cal["avg_gap_pct"],
        )

    @classmethod
    def conservative(cls) -> RealisticBacktestCosts:
        """Veri olmadan muhafazakâr başlangıç değerleri."""
        return cls(
            buy_slippage_pct=0.0030,
            sell_slippage_pct=0.0020,
            overnight_gap_pct=0.0015,
        )

    def entry_cost(self, price: float, shares: int, avg_volume: float = 1_000_000) -> dict:
        """
        Giriş emrinin tam maliyetini hesaplar.
        Backtest engine'inde signal_price → fill_price dönüşümü için kullan.
        """
        position_usd = price * shares
        participation = position_usd / (avg_volume * price + 1e-9)

        # Dinamik slippage: sabit + piyasa etkisi
        dynamic_slip = self.buy_slippage_pct + self.kyle_lambda * participation
        slippage_usd = position_usd * dynamic_slip
        commission_usd = self.commission_per_side
        gap_usd = position_usd * self.overnight_gap_pct

        fill_price = price * (1 + dynamic_slip + self.overnight_gap_pct)
        total_cost = slippage_usd + commission_usd + gap_usd

        return {
            "fill_price": round(fill_price, 4),
            "slippage_usd": round(slippage_usd, 2),
            "commission_usd": round(commission_usd, 2),
            "gap_usd": round(gap_usd, 2),
            "total_cost_usd": round(total_cost, 2),
            "cost_pct": round(total_cost / position_usd * 100, 3),
        }

    def exit_cost(
        self, price: float, shares: int, is_stop_hit: bool = False, avg_volume: float = 1_000_000
    ) -> dict:
        """Çıkış emrinin maliyetini hesaplar."""
        position_usd = price * shares
        participation = position_usd / (avg_volume * price + 1e-9)

        dynamic_slip = self.sell_slippage_pct + self.kyle_lambda * participation
        if is_stop_hit:
            dynamic_slip += self.stop_slippage_pct  # Stop'ta ek kayma

        slippage_usd = position_usd * dynamic_slip
        commission_usd = self.commission_per_side
        fill_price = price * (1 - dynamic_slip)

        return {
            "fill_price": round(fill_price, 4),
            "slippage_usd": round(slippage_usd, 2),
            "commission_usd": round(commission_usd, 2),
            "total_cost_usd": round(slippage_usd + commission_usd, 2),
            "is_stop_hit": is_stop_hit,
        }

    def round_trip_cost_pct(self, position_usd: float = 3000) -> float:
        """Bir işlemin gidiş-dönüş toplam maliyet yüzdesi."""
        entry_slip = self.buy_slippage_pct + self.overnight_gap_pct
        exit_slip = self.sell_slippage_pct
        commissions = (self.commission_per_side * 2) / position_usd
        return (entry_slip + exit_slip + commissions) * 100

    def annual_drag(self, trades_per_year: int, avg_position_usd: float = 3000) -> float:
        """Yıllık maliyet yükünü tahmin eder."""
        cost_per_trade = self.round_trip_cost_pct(avg_position_usd) / 100
        return trades_per_year * cost_per_trade * avg_position_usd


# ══════════════════════════════════════════════════════════════════════════
# Backtest haircut hesaplayıcı — hızlı kullanım
# ══════════════════════════════════════════════════════════════════════════


def apply_realistic_haircut(
    raw_profit: float,
    n_trades: int,
    avg_position_usd: float = 3000,
    costs: RealisticBacktestCosts | None = None,
) -> dict:
    """
    Backtest karına gerçekçilik düzeltmesi uygular.

    Kullanım:
        result = apply_realistic_haircut(raw_profit=9536, n_trades=1791)
        print(result['realistic_profit'])
    """
    if costs is None:
        costs = RealisticBacktestCosts()

    annual_drag = costs.annual_drag(n_trades, avg_position_usd)
    fill_rate_drag = raw_profit * (1 - costs.fill_rate) * 0.25
    total_drag = annual_drag + fill_rate_drag
    realistic_profit = raw_profit - total_drag
    haircut_pct = total_drag / max(abs(raw_profit), 1) * 100

    return {
        "raw_profit": round(raw_profit, 2),
        "slippage_drag": round(annual_drag * 0.55, 2),
        "commission_drag": round(annual_drag * 0.20, 2),
        "gap_drag": round(annual_drag * 0.15, 2),
        "fill_rate_drag": round(fill_rate_drag, 2),
        "other_drag": round(annual_drag * 0.10, 2),
        "total_drag": round(total_drag, 2),
        "realistic_profit": round(realistic_profit, 2),
        "haircut_pct": round(haircut_pct, 1),
        "cost_pct_per_trade": round(costs.round_trip_cost_pct(avg_position_usd), 3),
    }


# ── Hızlı test ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=== Slippage Tracker Test ===\n")

    tracker = SlippageTracker()

    # Simüle fill kayıtları (gerçek paper trading verisi gelene kadar)
    import random

    random.seed(42)
    for _i in range(30):
        sym = random.choice(["AAPL", "MSFT", "NVDA", "TSLA", "AMD"])
        spx = random.uniform(100, 500)
        noise = random.gauss(0.002, 0.001)
        tracker.record_fill(
            symbol=sym,
            signal_price=spx,
            fill_price=spx * (1 + max(noise, 0.0001)),
            direction=random.choice(["buy", "sell"]),
            shares=random.randint(5, 50),
            avg_volume=random.uniform(500_000, 10_000_000),
            source="simulation",
        )

    print(tracker.weekly_report())
    print()

    # Mevcut backtest sonuçlarına haircut uygula
    costs = RealisticBacktestCosts.from_tracker(tracker)
    print("\nGerçekçi maliyet modeli:")
    print(f"  Alış slippage:  {costs.buy_slippage_pct*100:.3f}%")
    print(f"  Satış slippage: {costs.sell_slippage_pct*100:.3f}%")
    print(f"  Gidiş-dönüş maliyet: {costs.round_trip_cost_pct():.3f}%")

    print("\n--- Backtest Haircut (Eski Strateji) ---")
    result_old = apply_realistic_haircut(
        raw_profit=95362,  # %953.62 getiri × $10K
        n_trades=1791,
        avg_position_usd=3000,
        costs=costs,
    )
    for k, v in result_old.items():
        print(f"  {k}: {v}")

    print("\n--- Backtest Haircut (Yeni Strateji) ---")
    result_new = apply_realistic_haircut(
        raw_profit=60229,  # %602.29 getiri × $10K
        n_trades=1626,
        avg_position_usd=3000,
        costs=costs,
    )
    for k, v in result_new.items():
        print(f"  {k}: {v}")

    print(
        f"\nGerçekçi Fark: ${result_new['realistic_profit'] - result_old['realistic_profit']:,.2f}"
    )
