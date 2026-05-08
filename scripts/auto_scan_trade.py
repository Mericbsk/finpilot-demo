#!/usr/bin/env python3
"""
Automated Scanner & Trader — Sprint 22 (Strateji B + Gap Filtresi + Risk Limiti).

Pipeline:
  16:15 ET  → Borsa kapanışından 15 dk sonra tarama (tüm preset'ler)
              Günlük barlar ve indikatörler (RSI/MACD/EMA) kapanış fiyatıyla kesinleşmiş
              Strateji B post-filtresi uygulanır
              Sinyaller DB'ye kaydedilir
              Cuma kapanışı → Pazartesi sabahı işlem (hafta sonu gap koruması)
  09:35 ET  → Sabah gap kontrolü (sinyal fiyatı vs açılış fiyatı)
              Günlük risk limitleri kontrol edilir
              Geçen sinyaller Alpaca'ya bracket order olarak girilir

Çalıştırma:
  python scripts/auto_scan_trade.py --once          # tek seferlik (şimdi)
  python scripts/auto_scan_trade.py --scan-only     # sadece tarama, emir yok
  python scripts/auto_scan_trade.py --dry-run       # her şeyi simüle et, gerçek emir yok
  python scripts/auto_scan_trade.py --schedule-scan 16:15 --schedule-trade 09:35

Environment değişkenleri:
    ALPACA_API_KEY       — Alpaca paper trading API anahtarı
    ALPACA_SECRET_KEY    — Alpaca paper trading gizli anahtarı
    ALPACA_PAPER=true    — Paper trading modu (varsayılan: true)
"""

from __future__ import annotations

import argparse
import io
import json
import logging
import os
import sys
import time
from datetime import date, datetime
from pathlib import Path

# Windows terminal: force UTF-8 so emoji/Turkish chars don't crash
if sys.platform == "win32":
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "buffer"):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Ensure project root on path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

Path("logs").mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/auto_scan_trade.log", mode="a"),
    ],
)
logger = logging.getLogger("auto_scan_trade")


# ===========================================================================
# ── BLOK 1: Strateji B Parametreleri & Post-Filtre ─────────────────────────
# ===========================================================================

STRATEGY_B = {
    "min_alignment_ratio": 0.67,  # eski: 0.75
    "min_momentum_ratio": 0.40,  # eski: 0.60
    "min_filter_score": 1,  # eski: 2
    "min_signal_score": 2,  # eski: 3
    "min_zscore": 0.0,  # eski: 1.5
    "min_price_filter": 2.0,  # değişmedi
    "min_risk_reward": 2.0,  # değişmedi
}


def apply_strategy_b(signals: list[dict]) -> list[dict]:
    """
    Scanner çıktısını Strateji B eşikleriyle filtrele.
    entry_ok=True olan sinyaller buraya gelir, burada ek kalite filtresi uygulanır.
    """
    p = STRATEGY_B
    filtered = []
    skipped = 0

    for s in signals:
        checks = [
            float(s.get("alignment_ratio", 1.0)) >= p["min_alignment_ratio"],
            float(s.get("momentum_ratio", 1.0)) >= p["min_momentum_ratio"],
            float(s.get("filter_score", 99)) >= p["min_filter_score"],
            float(s.get("signal_score", 99)) >= p["min_signal_score"],
            float(s.get("zscore", 99)) >= p["min_zscore"],
            float(s.get("price_filter", 99)) >= p["min_price_filter"],
            float(s.get("risk_reward", 0)) >= p["min_risk_reward"],
        ]
        if all(checks):
            filtered.append(s)
        else:
            skipped += 1
            logger.debug(
                f"  ⛔ {s.get('symbol','?')} Strateji B filtreden geçemedi — "
                f"align={s.get('alignment_ratio','?'):.2f} "
                f"mom={s.get('momentum_ratio','?'):.2f} "
                f"filter={s.get('filter_score','?')} "
                f"signal={s.get('signal_score','?')}"
            )

    logger.info(
        f"Strateji B filtresi: {len(signals)} sinyal → {len(filtered)} geçti " f"({skipped} elendi)"
    )
    return filtered


# ===========================================================================
# ── BLOK 2: Sabah Gap Filtresi ──────────────────────────────────────────────
# ===========================================================================

MAX_GAP_PCT = 0.005  # %0.5 — sinyal fiyatından bu kadar uzaklaşırsa geç


def fetch_current_price(symbol: str) -> float | None:
    """Alpaca veya yfinance'tan anlık/açılış fiyatını çek."""
    # Önce yfinance dene (yüklü olma ihtimali yüksek)
    try:
        import yfinance as yf

        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="1d", interval="1m")
        if not hist.empty:
            return float(hist["Close"].iloc[-1])
    except Exception:
        pass

    # yfinance yoksa Alpaca market data API dene
    try:
        from alpaca.data.historical import StockHistoricalDataClient
        from alpaca.data.requests import StockLatestTradeRequest

        client = StockHistoricalDataClient(
            os.environ.get("ALPACA_API_KEY", ""),
            os.environ.get("ALPACA_SECRET_KEY", ""),
        )
        req = StockLatestTradeRequest(symbol_or_symbols=symbol)
        trades = client.get_stock_latest_trade(req)
        return float(trades[symbol].price)
    except Exception:
        pass

    return None


def check_gap(signal: dict) -> tuple[bool, str]:
    """
    Sinyal fiyatı ile güncel fiyat arasındaki gap'i kontrol et.
    Returns: (geçti_mi, açıklama)
    """
    symbol = signal.get("symbol", "?")
    signal_price = float(signal.get("entry_price") or signal.get("price", 0))

    if signal_price <= 0:
        return True, "Fiyat bilgisi yok — geç"

    current = fetch_current_price(symbol)
    if current is None:
        logger.warning(f"  ⚠️  {symbol}: anlık fiyat alınamadı, gap kontrolü atlandı")
        return True, "Fiyat alınamadı — geçildi (dikkat)"

    gap_pct = abs(current - signal_price) / signal_price
    direction = "yukarı" if current > signal_price else "aşağı"

    if gap_pct > MAX_GAP_PCT:
        reason = (
            f"GAP REDDEDİLDİ: {symbol} sinyal=${signal_price:.2f} "
            f"güncel=${current:.2f} ({direction} %{gap_pct*100:.2f} > %{MAX_GAP_PCT*100:.1f})"
        )
        logger.warning(f"  🚫 {reason}")
        return False, reason

    logger.info(
        f"  ✅ Gap OK: {symbol} sinyal=${signal_price:.2f} "
        f"güncel=${current:.2f} ({direction} %{gap_pct*100:.2f})"
    )
    return True, f"Gap {gap_pct*100:.2f}% — OK"


# ===========================================================================
# ── BLOK 3: Günlük Risk Limiti ──────────────────────────────────────────────
# ===========================================================================


class DailyRiskGuard:
    """
    Her gün sıfırlanan risk limitleri:
      - MAX_OPEN_POSITIONS  : aynı anda açık maksimum pozisyon sayısı
      - MAX_DAILY_LOSS_PCT  : portföyün %X'ini tek günde kaybedince dur
      - MAX_SECTOR_POSITIONS: tek sektörde maksimum pozisyon sayısı
    """

    MAX_OPEN_POSITIONS = 5
    MAX_DAILY_LOSS_PCT = 0.05  # %5
    MAX_SECTOR_POSITIONS = 3

    # Sektör eşleşme tablosu (genişletilebilir)
    SECTOR_MAP: dict[str, str] = {
        "AAPL": "Tech",
        "MSFT": "Tech",
        "GOOGL": "Tech",
        "META": "Tech",
        "NVDA": "Semicon",
        "AMD": "Semicon",
        "INTC": "Semicon",
        "QCOM": "Semicon",
        "AMZN": "Consumer",
        "TSLA": "Auto",
        "F": "Auto",
        "GM": "Auto",
        "JPM": "Finance",
        "GS": "Finance",
        "BAC": "Finance",
        "WFC": "Finance",
        "JNJ": "Health",
        "PFE": "Health",
        "MRNA": "Health",
        "ABBV": "Health",
    }

    def __init__(self, broker=None, dry_run: bool = False):
        self.broker = broker
        self.dry_run = dry_run
        self._log_file = Path("logs/auto_trade") / f"risk_{date.today()}.json"
        self._log_file.parent.mkdir(parents=True, exist_ok=True)
        self._state = self._load_state()

    def _load_state(self) -> dict:
        if self._log_file.exists():
            try:
                return json.loads(self._log_file.read_text())
            except Exception:
                pass
        return {"orders_placed": [], "sectors": {}, "start_portfolio": None}

    def _save_state(self):
        self._log_file.write_text(json.dumps(self._state, indent=2, default=str))

    def _get_open_count(self) -> int:
        """Alpaca'daki açık pozisyon sayısı."""
        if self.dry_run or self.broker is None:
            return len(self._state.get("orders_placed", []))
        try:
            return len(self.broker.get_positions())
        except Exception:
            return len(self._state.get("orders_placed", []))

    def _get_portfolio_value(self) -> float:
        if self.dry_run or self.broker is None:
            return 100_000.0
        try:
            return float(self.broker.get_account()["portfolio_value"])
        except Exception:
            return 100_000.0

    def _get_daily_pnl_pct(self) -> float:
        """Günlük portföy değişimi (%)."""
        current = self._get_portfolio_value()
        start = self._state.get("start_portfolio")
        if start is None:
            self._state["start_portfolio"] = current
            self._save_state()
            return 0.0
        return (current - start) / start

    def _sector_count(self, symbol: str) -> int:
        sector = self.SECTOR_MAP.get(symbol, "Other")
        sectors = self._state.get("sectors", {})
        return sectors.get(sector, 0)

    def can_trade(self, symbol: str) -> tuple[bool, str]:
        """
        Bu sembol için işlem yapılabilir mi?
        Returns: (evet_mi, red_sebebi_veya_ok)
        """
        # 1. Açık pozisyon limiti
        open_count = self._get_open_count()
        if open_count >= self.MAX_OPEN_POSITIONS:
            return (
                False,
                f"Max pozisyon limiti ({self.MAX_OPEN_POSITIONS}) doldu — açık: {open_count}",
            )

        # 2. Günlük kayıp limiti
        pnl = self._get_daily_pnl_pct()
        if pnl <= -self.MAX_DAILY_LOSS_PCT:
            return False, (
                f"Günlük kayıp limiti aşıldı: "
                f"%{pnl*100:.2f} ≤ -%{self.MAX_DAILY_LOSS_PCT*100:.0f}"
            )

        # 3. Sektör konsantrasyonu
        sector = self.SECTOR_MAP.get(symbol, "Other")
        sector_count = self._sector_count(symbol)
        if sector_count >= self.MAX_SECTOR_POSITIONS:
            return False, (
                f"Sektör limiti ({sector}) doldu: " f"{sector_count}/{self.MAX_SECTOR_POSITIONS}"
            )

        return True, (
            f"✅ Risk OK: {open_count}/{self.MAX_OPEN_POSITIONS} pozisyon, "
            f"günlük P&L %{pnl*100:.2f}, sektör {sector} {sector_count}/{self.MAX_SECTOR_POSITIONS}"
        )

    def register_order(self, symbol: str):
        """Yerleştirilen emri kaydet (state güncelle)."""
        orders = self._state.setdefault("orders_placed", [])
        orders.append({"symbol": symbol, "time": datetime.now().isoformat()})

        sector = self.SECTOR_MAP.get(symbol, "Other")
        sectors = self._state.setdefault("sectors", {})
        sectors[sector] = sectors.get(sector, 0) + 1

        self._save_state()

    def summary(self) -> str:
        open_count = self._get_open_count()
        pnl = self._get_daily_pnl_pct()
        orders = len(self._state.get("orders_placed", []))
        return (
            f"Risk Guard özet: {open_count}/{self.MAX_OPEN_POSITIONS} açık pozisyon | "
            f"Günlük P&L: %{pnl*100:.2f} | "
            f"Bugün yerleştirilen emir: {orders}"
        )


# ===========================================================================
# Scan Engine
# ===========================================================================


def run_scan(preset_name: str = "tech_giants") -> list[dict]:
    """
    Run the FinPilot scanner on a preset and return BUY signals.

    Returns list of dicts with: symbol, price, stop_loss, take_profit,
    score, strength, regime, entry_ok, risk_reward, position_size, etc.
    """
    from scanner.evaluate import evaluate_symbols_parallel
    from views.components.stock_presets import STOCK_PRESETS

    # Load symbols
    if preset_name in STOCK_PRESETS:
        symbols = STOCK_PRESETS[preset_name].symbols
        logger.info(f"Scanning preset '{preset_name}': {len(symbols)} symbols")
    else:
        # Default fallback
        symbols = ["AAPL", "MSFT", "GOOGL", "NVDA", "TSLA", "META", "AMD", "AMZN"]
        logger.info(f"Scanning default symbols: {len(symbols)}")

    results = evaluate_symbols_parallel(symbols, kelly_fraction=0.5)
    logger.info(f"Scan complete: {len(results)} results")

    # Filter to BUY signals only (entry_ok=True)
    buy_signals = [r for r in results if r.get("entry_ok")]
    logger.info(f"BUY signals: {len(buy_signals)}")

    return buy_signals


def get_all_unique_symbols() -> list[str]:
    """Collect all unique symbols from every preset."""
    from views.components.stock_presets import STOCK_PRESETS

    seen = set()
    symbols = []
    for preset in STOCK_PRESETS.values():
        for s in preset.symbols:
            if s not in seen:
                seen.add(s)
                symbols.append(s)
    return symbols


def run_multi_preset_scan(presets: list[str] | None = None) -> list[dict]:
    """Run scan across multiple presets and deduplicate."""
    if presets is None:
        presets = ["tech_giants", "semiconductors", "cloud_saas"]

    all_signals = {}
    for preset in presets:
        try:
            signals = run_scan(preset)
            for s in signals:
                sym = s["symbol"]
                # Keep the highest-scoring signal per symbol
                if sym not in all_signals or s.get("score", 0) > all_signals[sym].get("score", 0):
                    s["scan_source"] = preset
                    all_signals[sym] = s
        except Exception as e:
            logger.error(f"Scan failed for preset '{preset}': {e}")

    return list(all_signals.values())


def run_full_scan(chunk_size: int = 100) -> list[dict]:
    """
    Scan ALL symbols from every preset in one go.

    Splits into chunks to avoid yfinance rate limits and memory issues.
    Deduplicates by symbol — keeps the highest-scoring signal.

    Args:
        chunk_size: Number of symbols per batch (default 100).

    Returns:
        List of BUY signal dicts, deduplicated by symbol.
    """
    from scanner.evaluate import evaluate_symbols_parallel

    all_symbols = get_all_unique_symbols()
    total = len(all_symbols)
    logger.info(f"🔍 FULL SCAN: {total} unique symbols across all presets")

    # Split into chunks
    chunks = [all_symbols[i : i + chunk_size] for i in range(0, total, chunk_size)]
    logger.info(f"   Split into {len(chunks)} chunks of ~{chunk_size}")

    all_signals: dict[str, dict] = {}
    scanned = 0

    for idx, chunk in enumerate(chunks, 1):
        t0 = time.time()
        logger.info(f"\n   ▶ Chunk {idx}/{len(chunks)}: {len(chunk)} symbols ...")

        try:
            results = evaluate_symbols_parallel(chunk, kelly_fraction=0.5)
            buy_signals = [r for r in results if r.get("entry_ok")]

            for s in buy_signals:
                sym = s["symbol"]
                if sym not in all_signals or s.get("score", 0) > all_signals[sym].get("score", 0):
                    s["scan_source"] = "full_scan"
                    all_signals[sym] = s

            scanned += len(chunk)
            elapsed = round(time.time() - t0, 1)
            logger.info(
                f"     ✓ {len(buy_signals)} BUY / {len(results)} total "
                f"({elapsed}s) — running total: {len(all_signals)} BUY, "
                f"{scanned}/{total} scanned"
            )
        except Exception as e:
            logger.error(f"     ✗ Chunk {idx} failed: {e}")
            scanned += len(chunk)

        # Brief pause between chunks to be kind to yfinance
        if idx < len(chunks):
            time.sleep(2)

    logger.info(f"\n🏁 FULL SCAN DONE: {len(all_signals)} BUY signals from {scanned} symbols")
    return list(all_signals.values())


# ===========================================================================
# Save to DB
# ===========================================================================


def record_buy_signals(signals: list[dict]) -> list[dict]:
    """
    Record BUY signals to the buy_signals table.

    Returns list of saved signals with their DB IDs.
    """
    from auth.database import BuySignalRepository, get_database

    db = get_database()
    repo = BuySignalRepository(db)
    today = date.today().isoformat()
    saved = []

    for s in signals:
        record = {
            "date": today,
            "symbol": s["symbol"],
            "entry_price": s["price"],
            "stop_loss": s.get("stop_loss"),
            "take_profit": s.get("take_profit"),
            "risk_reward": s.get("risk_reward"),
            "score": s.get("score"),
            "strength": s.get("filter_score", s.get("strength")),
            "regime": str(s.get("regime", "")),
            "sentiment": s.get("sentiment"),
            "position_size": s.get("position_size"),
            "kelly_fraction": s.get("kelly_fraction"),
            "reason": _build_reason(s),
            "scan_source": s.get("scan_source", ""),
        }
        row_id = repo.save(record)
        if row_id:
            record["id"] = row_id
            saved.append(record)
            logger.info(
                f"  📝 {s['symbol']}: ${s['price']:.2f} "
                f"SL=${s.get('stop_loss', 0):.2f} "
                f"TP=${s.get('take_profit', 0):.2f} "
                f"Score={s.get('score')}"
            )

    logger.info(f"Recorded {len(saved)} buy signals for {today}")
    return saved


def _build_reason(signal: dict) -> str:
    """Build a human-readable reason string."""
    parts = []
    if signal.get("direction"):
        parts.append("Trend UP")
    if signal.get("volume_spike"):
        parts.append("Volume Spike")
    if signal.get("momentum_confluence"):
        parts.append("Momentum Confluence")
    if signal.get("timeframe_aligned"):
        parts.append(f"MTF Aligned ({signal.get('alignment_ratio', 0):.0%})")
    rr = signal.get("risk_reward")
    if rr:
        parts.append(f"R/R {rr:.1f}")
    return " | ".join(parts) if parts else "Signal conditions met"


# ===========================================================================
# Place Orders on Alpaca
# ===========================================================================


def place_alpaca_orders(
    signals: list[dict],
    dry_run: bool = False,
    skip_gap_check: bool = False,
) -> list[dict]:
    """
    Place BUY orders on Alpaca paper trading for each signal.

    Yeni:  gap filtresi + günlük risk limiti kontrolü.
    dry_run=True → hiçbir gerçek emir gönderilmez, simülasyon loglanır.
    """
    from broker import AlpacaBroker

    broker = AlpacaBroker()
    if not dry_run and not broker.is_available:
        logger.warning("❌ Alpaca yapılandırılmamış — emir atlanıyor")
        logger.warning("   ALPACA_API_KEY ve ALPACA_SECRET_KEY env değişkenlerini ayarlayın")
        return []

    # Hesap bilgisi
    if not dry_run:
        try:
            acct = broker.get_account()
            logger.info(
                f"💰 Alpaca Hesabı: ${acct['portfolio_value']:,.2f} "
                f"(Nakit: ${acct['cash']:,.2f})"
            )
        except Exception as e:
            logger.error(f"Alpaca bağlantısı kurulamadı: {e}")
            return []

    # Risk guard başlat
    guard = DailyRiskGuard(
        broker=broker if not dry_run else None,
        dry_run=dry_run,
    )
    logger.info(guard.summary())

    orders = []
    gap_rejected = 0
    risk_blocked = 0

    for s in signals:
        symbol = s["symbol"]
        entry_price = float(s.get("entry_price") or s.get("price", 0))
        stop_loss = s.get("stop_loss")
        take_profit = s.get("take_profit")
        signal_id = s.get("id")

        # ── 1. Günlük risk kontrolü ──────────────────────────────────────
        ok, reason = guard.can_trade(symbol)
        if not ok:
            logger.warning(f"  🛑 {symbol}: Risk limit → {reason}")
            risk_blocked += 1
            continue
        logger.info(f"  {reason}")

        # ── 2. Gap filtresi ──────────────────────────────────────────────
        if not skip_gap_check:
            gap_ok, gap_msg = check_gap(s)
            if not gap_ok:
                gap_rejected += 1
                continue

        # ── 3. Pozisyon büyüklüğü ────────────────────────────────────────
        if stop_loss and not dry_run:
            qty = broker.calculate_position_size(entry_price, stop_loss)
        else:
            qty = max(1, int(500 / max(entry_price, 1)))

        # ── 4. Emri gönder ───────────────────────────────────────────────
        if dry_run:
            fake_order = {
                "order_id": f"DRY-{symbol}-{datetime.now().strftime('%H%M%S')}",
                "symbol": symbol,
                "qty": qty,
                "limit_price": round(entry_price * 1.005, 2),
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "status": "dry_run",
            }
            orders.append(fake_order)
            logger.info(
                f"  🧪 DRY-RUN {symbol}: BUY {qty} hisse @ ${entry_price:.2f} "
                f"SL=${stop_loss:.2f if stop_loss else 0:.2f} "
                f"TP=${take_profit:.2f if take_profit else 0:.2f}"
            )
            guard.register_order(symbol)
        else:
            try:
                order = broker.place_buy_order(
                    symbol=symbol,
                    qty=qty,
                    limit_price=round(entry_price * 1.005, 2),
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    buy_signal_id=signal_id,
                    time_in_force="day",
                )
                orders.append(order)
                guard.register_order(symbol)
                logger.info(
                    f"  ✅ {symbol}: BUY {qty} hisse @ ${entry_price:.2f} "
                    f"(emir: {order['order_id'][:8]}...)"
                )
            except Exception as e:
                logger.error(f"  ❌ {symbol}: Emir başarısız — {e}")

    logger.info(
        f"Alpaca emir özeti: {len(orders)} emir | "
        f"{gap_rejected} gap reddedildi | {risk_blocked} risk limiti"
    )
    return orders


# ===========================================================================
# Also log to CSV + DB signals table for backward compat
# ===========================================================================


def log_to_legacy_systems(signals: list[dict]) -> None:
    """Also save to the Sprint 20 signals table and CSV for compat."""
    try:
        from auth.database import SignalRepository, get_database

        db = get_database()
        repo = SignalRepository(db)
        now = datetime.now().strftime("%Y-%m-%d %H:%M")

        batch = []
        for s in signals:
            batch.append(
                {
                    "timestamp": now,
                    "symbol": s["symbol"],
                    "price": s.get("entry_price", s.get("price")),
                    "stop_loss": s.get("stop_loss"),
                    "take_profit": s.get("take_profit"),
                    "score": s.get("score"),
                    "strength": s.get("strength"),
                    "regime": s.get("regime"),
                    "sentiment": s.get("sentiment"),
                    "entry_ok": True,
                    "summary": s.get("reason", ""),
                    "reason": s.get("scan_source", ""),
                }
            )

        if batch:
            repo.save_batch(batch)
            logger.info(f"Also logged {len(batch)} to signals table")
    except Exception as e:
        logger.warning(f"Legacy logging failed: {e}")


# ===========================================================================
# Full Pipeline
# ===========================================================================


def run_full_pipeline(
    presets: list[str] | None = None,
    place_orders: bool = True,
    dry_run: bool = False,
    skip_gap_check: bool = False,
) -> dict:
    """
    Tam pipeline: tarama → Strateji B filtresi → DB kayıt → Alpaca emir.

    dry_run=True  → gerçek emir gönderilmez, her şey loglanır
    skip_gap_check → sabah gap filtresi atlanır (test için)
    """
    start = time.time()
    today = date.today().isoformat()

    logger.info("=" * 60)
    logger.info(f"🚀 AUTO SCAN & TRADE — {today}" + (" [DRY RUN]" if dry_run else ""))
    logger.info("=" * 60)

    # ── Adım 1: Tarama ──────────────────────────────────────────────────
    logger.info("\n📊 Adım 1: Tarama başlıyor...")
    raw_signals = run_full_scan() if presets == ["__ALL__"] else run_multi_preset_scan(presets)

    if not raw_signals:
        logger.info("Bugün BUY sinyali bulunamadı.")
        return {"date": today, "raw_signals": 0, "filtered_signals": 0, "orders": 0, "elapsed": 0}

    logger.info(f"  Ham sinyal sayısı: {len(raw_signals)}")

    # ── Adım 2: Strateji B Post-Filtresi ────────────────────────────────
    logger.info("\n🎯 Adım 2: Strateji B filtresi uygulanıyor...")
    buy_signals = apply_strategy_b(raw_signals)

    if not buy_signals:
        logger.info("Strateji B filtresi sonrası sinyal kalmadı.")
        _save_summary(
            {
                "date": today,
                "raw_signals": len(raw_signals),
                "filtered_signals": 0,
                "orders": 0,
                "elapsed": 0,
            }
        )
        return {"date": today, "raw_signals": len(raw_signals), "filtered_signals": 0, "orders": 0}

    # ── Adım 3: DB Kaydı ────────────────────────────────────────────────
    logger.info(f"\n📝 Adım 3: {len(buy_signals)} sinyal DB'ye kaydediliyor...")
    saved_signals = record_buy_signals(buy_signals)
    log_to_legacy_systems(buy_signals)

    # ── Adım 4: Alpaca Emirleri ──────────────────────────────────────────
    orders = []
    if place_orders and saved_signals:
        logger.info(f"\n📈 Adım 4: {len(saved_signals)} sinyal için Alpaca emri...")
        orders = place_alpaca_orders(
            saved_signals,
            dry_run=dry_run,
            skip_gap_check=skip_gap_check,
        )

    elapsed = round(time.time() - start, 1)

    summary = {
        "date": today,
        "raw_signals": len(raw_signals),
        "filtered_signals": len(saved_signals),
        "orders": len(orders),
        "elapsed": elapsed,
        "dry_run": dry_run,
        "symbols": [s["symbol"] for s in saved_signals],
        "strategy_params": STRATEGY_B,
    }

    logger.info("\n" + "=" * 60)
    logger.info(
        f"✅ TAMAMLANDI — {len(raw_signals)} ham → {len(saved_signals)} filtreli → "
        f"{len(orders)} emir | {elapsed}s"
    )
    logger.info("=" * 60)

    _save_summary(summary)
    return summary


def _save_summary(summary: dict) -> None:
    """Save daily summary to logs."""
    log_dir = Path("logs/auto_trade")
    log_dir.mkdir(parents=True, exist_ok=True)
    fpath = log_dir / f"summary_{summary['date']}.json"
    with open(fpath, "w") as f:
        json.dump(summary, f, indent=2, default=str)


# ===========================================================================
# Scheduler
# ===========================================================================


def start_scheduler(scan_time: str = "14:00", presets: list[str] | None = None) -> None:
    """
    Start APScheduler to run the pipeline at a specific time daily.

    Args:
        scan_time: HH:MM format (24h), e.g. "14:00"
        presets: Stock preset names to scan
    """
    from apscheduler.schedulers.blocking import BlockingScheduler
    from apscheduler.triggers.cron import CronTrigger

    hour, minute = map(int, scan_time.split(":"))

    scheduler = BlockingScheduler()
    scheduler.add_job(
        run_full_pipeline,
        CronTrigger(
            day_of_week="mon-fri",
            hour=hour,
            minute=minute,
            timezone="America/New_York",
        ),
        kwargs={"presets": presets, "place_orders": True},
        id="daily_scan_trade",
        name=f"Daily Scan & Trade @ {scan_time} ET",
        misfire_grace_time=3600,
    )

    logger.info(f"⏰ Scheduler started — scanning at {scan_time} ET (Mon-Fri)")
    logger.info("   Press Ctrl+C to stop")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped.")
        scheduler.shutdown()


# ===========================================================================
# CLI
# ===========================================================================


def start_dual_scheduler(
    scan_time: str = "16:15",
    trade_time: str = "09:35",
    presets: list[str] | None = None,
    dry_run: bool = False,
) -> None:
    """
    İki ayrı job çalıştır:
      1. scan_time  → tam tarama + Strateji B filtresi + DB kaydı (emir YOK)
      2. trade_time → gap filtresi + risk limiti + Alpaca emirleri
    """
    from apscheduler.schedulers.blocking import BlockingScheduler
    from apscheduler.triggers.cron import CronTrigger

    scan_h, scan_m = map(int, scan_time.split(":"))
    trade_h, trade_m = map(int, trade_time.split(":"))

    scheduler = BlockingScheduler()

    # Job 1: Tarama — borsa kapanışından sonra (16:15 ET varsayılan)
    # Kapanış fiyatlarıyla indikatörler (RSI/MACD/EMA) kesinleşmiş olur
    scheduler.add_job(
        run_full_pipeline,
        CronTrigger(day_of_week="mon-fri", hour=scan_h, minute=scan_m, timezone="America/New_York"),
        kwargs={"presets": presets, "place_orders": False, "dry_run": dry_run},
        id="daily_scan",
        name=f"Kapanış Taraması @ {scan_time} ET",
        misfire_grace_time=3600,
    )

    # Job 2: Emir girme (sabah)
    scheduler.add_job(
        run_full_pipeline,
        CronTrigger(
            day_of_week="mon-fri", hour=trade_h, minute=trade_m, timezone="America/New_York"
        ),
        kwargs={"presets": presets, "place_orders": True, "dry_run": dry_run},
        id="daily_trade",
        name=f"Sabah Emirleri @ {trade_time} ET",
        misfire_grace_time=1800,
    )

    mode = "DRY-RUN" if dry_run else "CANLI (PAPER)"
    logger.info(f"⏰ Çift zamanlı scheduler başlatıldı [{mode}]")
    logger.info(f"   📊 Tarama  : her hafta içi {scan_time} ET (borsa kapanışı sonrası)")
    logger.info(f"   📈 Emirler : her hafta içi {trade_time} ET (açılış + 5 dk)")
    logger.info("   📅 Cuma sinyalleri Pazartesi sabahı işlem görür")
    logger.info("   Durdurmak için Ctrl+C basın")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler durduruldu.")
        scheduler.shutdown()


def main():
    os.makedirs("logs", exist_ok=True)

    parser = argparse.ArgumentParser(
        description="FinPilot Auto Scanner & Trader (Strateji B)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Örnekler:
  python scripts/auto_scan_trade.py --dry-run          # Simüle et, emir gönderme
  python scripts/auto_scan_trade.py --once             # Hemen çalıştır (gerçek emir)
  python scripts/auto_scan_trade.py --scan-only        # Sadece tara, emir yok
  python scripts/auto_scan_trade.py \\
      --schedule-scan 16:15 --schedule-trade 09:35     # Tam otomasyon (kapanış saati)
        """,
    )
    parser.add_argument("--once", action="store_true", help="Hemen bir kere çalıştır")
    parser.add_argument("--scan-only", action="store_true", help="Sadece tara, emir girme")
    parser.add_argument("--no-trade", action="store_true", help="--scan-only ile aynı")
    parser.add_argument("--dry-run", action="store_true", help="Simülasyon — gerçek emir YOK")
    parser.add_argument("--skip-gap", action="store_true", help="Gap filtresini atla (test için)")
    parser.add_argument(
        "--presets",
        nargs="+",
        default=["tech_giants", "semiconductors", "cloud_saas"],
        help="Taranacak preset'ler",
    )
    parser.add_argument("--all", action="store_true", help="Tüm preset'lerdeki sembolleri tara")

    # Çift zamanlı scheduler
    parser.add_argument(
        "--schedule-scan",
        type=str,
        default=None,
        help="Tarama saati HH:MM ET (varsayılan: 16:15 — borsa kapanışı sonrası)",
    )
    parser.add_argument(
        "--schedule-trade",
        type=str,
        default="09:35",
        help="Emir girme saati HH:MM ET (varsayılan: 09:35 — açılış + 5 dk)",
    )

    # Eski tek-zamanlı (geriye uyumluluk)
    parser.add_argument(
        "--schedule", type=str, default=None, help="(Eski) Tek seferlik zamanlama HH:MM"
    )

    args = parser.parse_args()

    if getattr(args, "all", False):
        args.presets = ["__ALL__"]

    place_orders = not (args.scan_only or args.no_trade)

    if args.schedule_scan:
        # Yeni çift zamanlı mod
        start_dual_scheduler(
            scan_time=args.schedule_scan,
            trade_time=args.schedule_trade,
            presets=args.presets,
            dry_run=args.dry_run,
        )
    elif args.schedule:
        # Eski tek zamanlı mod (geriye uyumluluk)
        start_scheduler(args.schedule, args.presets)
    else:
        # Tek seferlik çalıştırma
        run_full_pipeline(
            presets=args.presets,
            place_orders=place_orders,
            dry_run=args.dry_run,
            skip_gap_check=args.skip_gap,
        )


if __name__ == "__main__":
    main()
