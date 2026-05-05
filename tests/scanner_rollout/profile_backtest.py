from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import pandas as pd
import yfinance as yf

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scanner.indicators import add_indicators

EXPECTED_DIR = Path(__file__).resolve().parent / "expected"
DEFAULT_TICKERS_FILE = ROOT / "data" / "tickers" / "tickers.txt"
DEFAULT_START = "2024-04-19"
DEFAULT_END = "2026-04-18"
DEFAULT_INDEX = "^IXIC"


@dataclass(frozen=True)
class StrategyProfile:
    name: str
    description: str
    min_signal_score: int
    min_alignment_ratio: float
    min_momentum_ratio: float
    min_filter_score: int
    min_price: float
    min_avg_volume: float
    require_liquidity: bool


BASELINE_PROFILE = StrategyProfile(
    name="baseline_current_proxy",
    description="Current sade backtest mantigi: regime + direction + score >= 2",
    min_signal_score=2,
    min_alignment_ratio=0.0,
    min_momentum_ratio=0.0,
    min_filter_score=0,
    min_price=0.0,
    min_avg_volume=0.0,
    require_liquidity=False,
)


OPTIMIZED_CANDIDATE_PROFILE = StrategyProfile(
    name="optimized_candidate_proxy",
    description=(
        "Published optimized candidate thresholds applied to the same daily proxy features"
    ),
    min_signal_score=2,
    min_alignment_ratio=0.60,
    min_momentum_ratio=0.40,
    min_filter_score=1,
    min_price=2.0,
    min_avg_volume=300_000.0,
    require_liquidity=True,
)


@dataclass(frozen=True)
class BacktestOutputs:
    summary: dict[str, Any]
    per_strategy: pd.DataFrame
    entry_diff: pd.DataFrame
    baseline_trades: pd.DataFrame
    candidate_trades: pd.DataFrame
    baseline_entries: pd.DataFrame
    candidate_entries: pd.DataFrame


ENTRY_COLUMNS = [
    "profile",
    "symbol",
    "entry_date",
    "price",
    "score",
    "filter_score",
    "alignment_ratio",
    "momentum_ratio",
    "liquidity_ok",
]


TRADE_COLUMNS = [
    "profile",
    "symbol",
    "entry_date",
    "entry_price",
    "exit_date",
    "exit_price",
    "shares",
    "stop_loss",
    "take_profit",
    "pnl",
    "pnl_pct",
    "commission",
    "r_multiple",
    "reason",
    "kelly",
    "kelly_position",
    "score",
    "filter_score",
    "alignment_ratio",
    "momentum_ratio",
]


class ProfileBacktestEngine:
    def __init__(
        self,
        profile: StrategyProfile,
        initial_capital: float,
        risk_percent: float,
        kelly_fraction: float,
    ):
        self.profile = profile
        self.initial_capital = float(initial_capital)
        self.current_portfolio = float(initial_capital)
        self.risk_percent = float(risk_percent)
        self.kelly_fraction = float(kelly_fraction)
        self.commission_bps = 5.0
        self.slippage_bps = 10.0
        self.cooldown_days = 3
        self.max_allocation_pct = 0.10
        self.trades: list[dict[str, Any]] = []
        self.entries: list[dict[str, Any]] = []
        self.daily_portfolio: list[dict[str, Any]] = []
        self.signals_found = 0

    def run(
        self,
        symbol_frames: dict[str, pd.DataFrame],
        trading_dates: list[pd.Timestamp],
        index_frame: pd.DataFrame,
        entry_column: str,
    ) -> None:
        for current_date in trading_dates:
            if not market_regime_ok(index_frame, current_date):
                self.daily_portfolio.append(
                    {
                        "date": current_date,
                        "portfolio_value": self.current_portfolio,
                    }
                )
                continue

            for symbol, frame in symbol_frames.items():
                if current_date not in frame.index:
                    continue
                row = frame.loc[current_date]
                if bool(row.get(entry_column, False)):
                    self.signals_found += 1
                    self.execute_trade(symbol, row, frame, current_date)

            self.daily_portfolio.append(
                {
                    "date": current_date,
                    "portfolio_value": self.current_portfolio,
                }
            )

    def execute_trade(
        self, symbol: str, row: pd.Series, frame: pd.DataFrame, entry_date: pd.Timestamp
    ) -> None:
        for trade in self.trades:
            if trade["symbol"] != symbol:
                continue
            exit_date = pd.Timestamp(trade["exit_date"])
            if entry_date <= exit_date:
                return
            if entry_date <= exit_date + pd.Timedelta(days=self.cooldown_days):
                return

        entry_price = float(row["Close"])
        atr = float(row.get("atr", 0.01) or 0.01)
        stop_loss = entry_price - (atr * 2.0)
        tp1 = entry_price + (atr * 4.0)
        tp2 = entry_price + (atr * 6.0)
        tp3 = entry_price + (atr * 9.0)

        price_risk = entry_price - stop_loss
        if price_risk <= 0:
            return

        win_rate = 0.5
        avg_win = 2.0
        avg_loss = 1.0
        if len(self.trades) > 10:
            wins = [t["pnl"] for t in self.trades if t["pnl"] > 0]
            losses = [t["pnl"] for t in self.trades if t["pnl"] < 0]
            win_rate = len(wins) / len(self.trades) if self.trades else 0.5
            avg_win = sum(wins) / len(wins) if wins else 2.0
            avg_loss = abs(sum(losses) / len(losses)) if losses else 1.0

        kelly = (win_rate - (1 - win_rate) / (avg_win / avg_loss)) if avg_loss > 0 else 0.1
        kelly = max(0.01, min(kelly, 1.0))
        kelly_position = self.current_portfolio * self.kelly_fraction * kelly
        risk_amount = self.current_portfolio * self.risk_percent / 100.0
        risk_based_shares = min(kelly_position, risk_amount) / price_risk
        max_position_value = self.current_portfolio * self.max_allocation_pct
        max_shares_by_value = max_position_value / entry_price
        position_size = min(risk_based_shares, max_shares_by_value)
        if position_size <= 0:
            return

        exits = simulate_exit(frame, entry_date, stop_loss, tp1, tp2, tp3)
        if not exits:
            return

        total_pnl_net = 0.0
        total_commission = 0.0
        weighted_exit_price = 0.0
        total_fraction = 0.0
        exit_reasons: list[str] = []
        last_exit_date = entry_date

        for exit_trade in exits:
            fraction = float(exit_trade["fraction"])
            exit_price = float(exit_trade["price"])
            exit_date = pd.Timestamp(exit_trade["date"])
            reason = str(exit_trade["reason"])

            part_size = position_size * fraction
            slip = self.slippage_bps / 10000.0
            entry_exec = entry_price * (1 + slip)
            exit_exec = exit_price * (1 - slip)
            commission_rate = self.commission_bps / 10000.0
            commission = commission_rate * (entry_exec * part_size + exit_exec * part_size)
            pnl_gross = (exit_exec - entry_exec) * part_size
            pnl_net = pnl_gross - commission

            total_pnl_net += pnl_net
            total_commission += commission
            weighted_exit_price += exit_price * fraction
            total_fraction += fraction
            exit_reasons.append(f"{reason}({int(fraction * 100)}%)")
            last_exit_date = exit_date

        avg_exit_price = weighted_exit_price / total_fraction if total_fraction > 0 else 0.0
        initial_risk_dollar = price_risk * position_size
        r_multiple = total_pnl_net / initial_risk_dollar if initial_risk_dollar > 0 else 0.0
        pnl_pct = (total_pnl_net / (entry_price * position_size)) * 100 if entry_price > 0 else 0.0

        trade = {
            "profile": self.profile.name,
            "symbol": symbol,
            "entry_date": entry_date.strftime("%Y-%m-%d"),
            "entry_price": entry_price,
            "exit_date": last_exit_date.strftime("%Y-%m-%d"),
            "exit_price": avg_exit_price,
            "shares": position_size,
            "stop_loss": stop_loss,
            "take_profit": tp2,
            "pnl": total_pnl_net,
            "pnl_pct": pnl_pct,
            "commission": total_commission,
            "r_multiple": r_multiple,
            "reason": ", ".join(exit_reasons),
            "kelly": kelly,
            "kelly_position": kelly_position,
            "score": int(row["score"]),
            "filter_score": int(row["filter_score"]),
            "alignment_ratio": float(row["alignment_ratio"]),
            "momentum_ratio": float(row["momentum_ratio"]),
        }
        self.trades.append(trade)
        self.entries.append(
            {
                "profile": self.profile.name,
                "symbol": symbol,
                "entry_date": entry_date.strftime("%Y-%m-%d"),
                "price": entry_price,
                "score": int(row["score"]),
                "filter_score": int(row["filter_score"]),
                "alignment_ratio": round(float(row["alignment_ratio"]), 4),
                "momentum_ratio": round(float(row["momentum_ratio"]), 4),
                "liquidity_ok": bool(row["liquidity_ok"]),
            }
        )
        self.current_portfolio += total_pnl_net

    def build_metrics(self) -> dict[str, Any]:
        trades = pd.DataFrame(self.trades)
        total_return_pct = (
            (self.current_portfolio - self.initial_capital) / self.initial_capital
        ) * 100.0

        metrics: dict[str, Any] = {
            "profile": self.profile.name,
            "description": self.profile.description,
            "initial_capital": round(self.initial_capital, 2),
            "final_capital": round(self.current_portfolio, 2),
            "total_return_pct": round(total_return_pct, 2),
            "signals_found": int(self.signals_found),
            "executed_trades": int(len(self.trades)),
        }

        if trades.empty:
            metrics.update(
                {
                    "win_rate_pct": 0.0,
                    "avg_trade_pnl": 0.0,
                    "avg_win": 0.0,
                    "avg_loss": 0.0,
                    "profit_factor": 0.0,
                    "avg_hold_days": 0.0,
                    "cagr_pct": 0.0,
                    "sharpe": 0.0,
                    "max_drawdown_pct": 0.0,
                }
            )
            return metrics

        wins = trades.loc[trades["pnl"] > 0, "pnl"]
        losses = trades.loc[trades["pnl"] < 0, "pnl"]
        win_rate_pct = (len(wins) / len(trades)) * 100.0
        gross_profit = float(wins.sum()) if not wins.empty else 0.0
        gross_loss = abs(float(losses.sum())) if not losses.empty else 0.0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0.0
        holding_days = (
            pd.to_datetime(trades["exit_date"]) - pd.to_datetime(trades["entry_date"])
        ).dt.days

        equity = pd.DataFrame(self.daily_portfolio)
        equity["date"] = pd.to_datetime(equity["date"])
        equity = equity.sort_values("date")
        cagr_pct = 0.0
        sharpe = 0.0
        max_drawdown_pct = 0.0
        if len(equity) >= 2:
            days = max(int((equity["date"].iloc[-1] - equity["date"].iloc[0]).days), 1)
            start_val = float(equity["portfolio_value"].iloc[0])
            end_val = float(equity["portfolio_value"].iloc[-1])
            if start_val > 0:
                cagr_pct = (((end_val / start_val) ** (365.0 / days)) - 1.0) * 100.0
            returns = equity["portfolio_value"].pct_change().fillna(0.0)
            std = float(returns.std(ddof=0))
            if std > 0:
                sharpe = float((returns.mean() / std) * (252**0.5))
            running_max = equity["portfolio_value"].cummax()
            drawdown = (equity["portfolio_value"] / running_max) - 1.0
            max_drawdown_pct = abs(float(drawdown.min() * 100.0))

        metrics.update(
            {
                "win_rate_pct": round(win_rate_pct, 2),
                "avg_trade_pnl": round(float(trades["pnl"].mean()), 2),
                "avg_win": round(float(wins.mean()) if not wins.empty else 0.0, 2),
                "avg_loss": round(float(losses.mean()) if not losses.empty else 0.0, 2),
                "profit_factor": round(profit_factor, 2),
                "avg_hold_days": round(
                    float(holding_days.mean()) if not holding_days.empty else 0.0, 2
                ),
                "cagr_pct": round(cagr_pct, 2),
                "sharpe": round(sharpe, 2),
                "max_drawdown_pct": round(max_drawdown_pct, 2),
            }
        )
        return metrics


def load_symbol_universe(tickers_file: Path, max_symbols: int | None = None) -> list[str]:
    symbols: list[str] = []
    for raw_line in tickers_file.read_text().splitlines():
        line = raw_line.strip().upper()
        if not line or line.startswith("#"):
            continue
        symbols.append(line)
    if max_symbols is not None:
        return symbols[:max_symbols]
    return symbols


def normalize_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    if isinstance(df.columns, pd.MultiIndex):
        try:
            df.columns = df.columns.droplevel(1)
        except Exception:
            df = df.loc[:, [c for c in df.columns if c is not None]]
    if "Close" not in df.columns and "Adj Close" in df.columns:
        df = df.rename(columns={"Adj Close": "Close"})
    required = {"Open", "High", "Low", "Close", "Volume"}
    if not required.issubset(df.columns):
        return pd.DataFrame()
    if isinstance(df.index, pd.DatetimeIndex) and getattr(df.index, "tz", None) is not None:
        df.index = df.index.tz_convert(None)
    if isinstance(df.index, pd.DatetimeIndex):
        df.index = df.index.normalize()
    return df.dropna().copy()


def download_symbol_history(
    symbol: str, start: pd.Timestamp, end: pd.Timestamp
) -> tuple[str, pd.DataFrame | None, str | None]:
    fetch_start = (start - pd.Timedelta(days=450)).strftime("%Y-%m-%d")
    today = pd.Timestamp.now().normalize()
    fetch_end = (min(end + pd.Timedelta(days=91), today) + pd.Timedelta(days=1)).strftime(
        "%Y-%m-%d"
    )
    try:
        df = yf.Ticker(symbol).history(
            start=fetch_start,
            end=fetch_end,
            interval="1d",
            auto_adjust=True,
            actions=False,
            back_adjust=False,
        )
    except Exception as exc:
        return symbol, None, type(exc).__name__

    df = normalize_ohlcv(df)
    if df.empty:
        return symbol, None, "empty"

    df = add_indicators(df)
    if df.empty:
        return symbol, None, "indicator_failed"

    df["ema20"] = df["Close"].ewm(span=20, adjust=False).mean()
    visible = df.loc[(df.index >= start) & (df.index <= end)]
    if visible.empty:
        return symbol, None, "no_window_data"

    prepared = build_feature_frame(df)
    if prepared.empty:
        return symbol, None, "feature_failed"
    return symbol, prepared, None


def build_feature_frame(df: pd.DataFrame) -> pd.DataFrame:
    frame = df.copy()
    frame = frame.sort_index()
    vol_roll10 = frame["Volume"].rolling(10).mean()
    price_change_3d = frame["Close"].pct_change(3)
    price_change_5d = frame["Close"].pct_change(5)
    gap_pct = ((frame["ema50"] - frame["ema200"]) / frame["ema200"]).replace(
        [pd.NA, pd.NaT], 0.0
    ) * 100.0

    frame["regime"] = frame["Close"] > frame["ema200"]
    frame["direction"] = frame["Close"] > frame["ema50"]
    frame["score"] = (
        frame["rsi"].between(30, 70).astype(int)
        + (frame["Volume"] > frame["vol_med20"] * 1.2).astype(int)
        + ((frame["macd_hist"] > 0) & (frame["macd_hist"] > frame["macd_hist"].shift(1))).astype(
            int
        )
    )
    frame["volume_spike"] = (frame["Volume"] > vol_roll10 * 1.2).fillna(False)
    frame["price_momentum"] = (price_change_3d >= 0.015).fillna(False)
    frame["trend_strength"] = (gap_pct >= 3.0).fillna(False)
    frame["filter_score"] = (
        frame["volume_spike"].astype(int)
        + frame["price_momentum"].astype(int)
        + frame["trend_strength"].astype(int)
    )
    frame["alignment_ratio"] = (
        (frame["Close"] > frame["ema20"]).astype(int)
        + frame["direction"].astype(int)
        + frame["regime"].astype(int)
    ) / 3.0
    frame["momentum_ratio"] = (
        frame["rsi"].between(45, 65).astype(int)
        + (frame["macd_hist"] > 0.01).astype(int)
        + (frame["rsi"] > frame["rsi"].shift(1)).astype(int)
        + (frame["macd_hist"] > frame["macd_hist"].shift(1)).astype(int)
        + (frame["Close"] > frame["ema20"]).astype(int)
        + (price_change_5d > 0).astype(int)
    ) / 6.0
    frame["liquidity_ok"] = ((frame["Close"] >= 2.0) & (frame["vol_avg10"] >= 300_000)).fillna(
        False
    )
    frame["baseline_entry_ok"] = (
        frame["regime"] & frame["direction"] & (frame["score"] >= BASELINE_PROFILE.min_signal_score)
    )
    frame["candidate_entry_ok"] = (
        frame["regime"]
        & frame["direction"]
        & (frame["score"] >= OPTIMIZED_CANDIDATE_PROFILE.min_signal_score)
        & (frame["alignment_ratio"] >= OPTIMIZED_CANDIDATE_PROFILE.min_alignment_ratio)
        & (frame["momentum_ratio"] >= OPTIMIZED_CANDIDATE_PROFILE.min_momentum_ratio)
        & (frame["filter_score"] >= OPTIMIZED_CANDIDATE_PROFILE.min_filter_score)
        & (frame["Close"] >= OPTIMIZED_CANDIDATE_PROFILE.min_price)
        & frame["liquidity_ok"]
    )
    return frame.dropna(subset=["Close", "ema20", "ema50", "ema200", "rsi", "macd_hist", "atr"])


def load_index_frame(
    start: pd.Timestamp, end: pd.Timestamp, index_symbol: str = DEFAULT_INDEX
) -> pd.DataFrame:
    fetch_start = (start - pd.Timedelta(days=365)).strftime("%Y-%m-%d")
    fetch_end = (end + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    frame = yf.download(
        index_symbol, start=fetch_start, end=fetch_end, interval="1d", progress=False
    )
    frame = normalize_ohlcv(frame)
    if frame.empty:
        return pd.DataFrame()
    frame["ema50"] = frame["Close"].ewm(span=50, adjust=False).mean()
    return frame


def market_regime_ok(index_frame: pd.DataFrame, current_date: pd.Timestamp) -> bool:
    if index_frame.empty or current_date not in index_frame.index:
        return True
    row = index_frame.loc[current_date]
    close = float(row["Close"])
    open_price = float(row["Open"])
    ema50 = float(row["ema50"])
    return bool(close >= ema50 and close >= open_price)


def simulate_exit(
    frame: pd.DataFrame,
    entry_date: pd.Timestamp,
    stop_loss: float,
    tp1: float,
    tp2: float,
    tp3: float,
) -> list[dict[str, Any]] | None:
    df = frame.loc[
        (frame.index >= entry_date) & (frame.index <= entry_date + pd.Timedelta(days=90))
    ]
    if df.empty:
        return None

    exits: list[dict[str, Any]] = []
    remaining_fraction = 1.0
    entry_price = float(df.iloc[0]["Close"])
    highest_price = entry_price
    estimated_atr = (entry_price - stop_loss) / 2.0
    trailing_dist = estimated_atr * 2.5
    current_stop = stop_loss
    last_date = entry_date
    last_close = entry_price

    for idx, row in df.iloc[1:].iterrows():
        high = float(row["High"])
        low = float(row["Low"])
        close = float(row["Close"])
        last_date = pd.Timestamp(idx)
        last_close = close

        if high > highest_price:
            highest_price = high

        if low <= current_stop:
            exits.append(
                {
                    "date": last_date,
                    "price": current_stop,
                    "fraction": remaining_fraction,
                    "reason": "trailing_stop" if current_stop > stop_loss else "stop_loss",
                }
            )
            return exits

        if remaining_fraction >= 1.0 and high >= tp1:
            exits.append({"date": last_date, "price": tp1, "fraction": 0.5, "reason": "tp1"})
            remaining_fraction -= 0.5
            current_stop = max(current_stop, entry_price)

        if remaining_fraction >= 0.5 and high >= tp2:
            exits.append({"date": last_date, "price": tp2, "fraction": 0.3, "reason": "tp2"})
            remaining_fraction -= 0.3
            current_stop = max(current_stop, highest_price - trailing_dist)

        if remaining_fraction <= 0.25:
            current_stop = max(current_stop, highest_price - trailing_dist)

    if remaining_fraction > 0:
        exits.append(
            {
                "date": last_date,
                "price": last_close,
                "fraction": remaining_fraction,
                "reason": "timeout",
            }
        )
    return exits


def collect_entry_diff(
    baseline_entries: pd.DataFrame, candidate_entries: pd.DataFrame
) -> pd.DataFrame:
    if baseline_entries.empty:
        baseline_entries = pd.DataFrame(columns=ENTRY_COLUMNS)
    if candidate_entries.empty:
        candidate_entries = pd.DataFrame(columns=ENTRY_COLUMNS)

    baseline_keys = set(
        zip(baseline_entries["entry_date"], baseline_entries["symbol"], strict=False)
    )
    candidate_keys = set(
        zip(candidate_entries["entry_date"], candidate_entries["symbol"], strict=False)
    )
    baseline_lookup = baseline_entries.set_index(["entry_date", "symbol"]).to_dict("index")
    candidate_lookup = candidate_entries.set_index(["entry_date", "symbol"]).to_dict("index")

    rows: list[dict[str, Any]] = []

    for key in sorted(candidate_keys - baseline_keys):
        record = candidate_lookup[key]
        rows.append(
            {
                "change_type": "added_by_candidate",
                "entry_date": key[0],
                "symbol": key[1],
                **record,
            }
        )

    for key in sorted(baseline_keys - candidate_keys):
        record = baseline_lookup[key]
        rows.append(
            {
                "change_type": "removed_by_candidate",
                "entry_date": key[0],
                "symbol": key[1],
                **record,
            }
        )

    if not rows:
        return pd.DataFrame(columns=["change_type", *ENTRY_COLUMNS])
    return pd.DataFrame(rows)


def build_summary(
    *,
    start: pd.Timestamp,
    end: pd.Timestamp,
    symbols_requested: int,
    symbols_used: int,
    skipped_symbols: dict[str, str],
    baseline_metrics: dict[str, Any],
    candidate_metrics: dict[str, Any],
    entry_diff: pd.DataFrame,
) -> dict[str, Any]:
    top_added = {}
    top_removed = {}
    overlap_pct = 100.0

    if not entry_diff.empty:
        top_added = (
            entry_diff.loc[entry_diff["change_type"] == "added_by_candidate", "symbol"]
            .value_counts()
            .head(15)
            .to_dict()
        )
        top_removed = (
            entry_diff.loc[entry_diff["change_type"] == "removed_by_candidate", "symbol"]
            .value_counts()
            .head(15)
            .to_dict()
        )

    baseline_trades = int(baseline_metrics["executed_trades"])
    candidate_trades = int(candidate_metrics["executed_trades"])
    changed = len(entry_diff)
    overlap = max(baseline_trades + candidate_trades - changed, 0)
    union = len(entry_diff) + overlap
    if union > 0:
        overlap_pct = round((overlap / union) * 100.0, 2)

    return {
        "backtest_type": "daily_proxy_profile_comparison",
        "window_start": start.strftime("%Y-%m-%d"),
        "window_end": end.strftime("%Y-%m-%d"),
        "window_days": int((end - start).days) + 1,
        "symbols_requested": symbols_requested,
        "symbols_used": symbols_used,
        "symbols_skipped": len(skipped_symbols),
        "skipped_examples": dict(list(skipped_symbols.items())[:15]),
        "baseline_profile": asdict(BASELINE_PROFILE),
        "candidate_profile": asdict(OPTIMIZED_CANDIDATE_PROFILE),
        "baseline_metrics": baseline_metrics,
        "candidate_metrics": candidate_metrics,
        "added_entries_by_candidate": int((entry_diff["change_type"] == "added_by_candidate").sum())
        if not entry_diff.empty
        else 0,
        "removed_entries_by_candidate": int(
            (entry_diff["change_type"] == "removed_by_candidate").sum()
        )
        if not entry_diff.empty
        else 0,
        "entry_overlap_pct": overlap_pct,
        "top_added_symbols": top_added,
        "top_removed_symbols": top_removed,
    }


def render_report(summary: dict[str, Any]) -> str:
    baseline = summary["baseline_metrics"]
    candidate = summary["candidate_metrics"]

    def diff_line(key: str, label: str, suffix: str = "") -> str:
        base_val = baseline[key]
        cand_val = candidate[key]
        if isinstance(base_val, (int, float)) and isinstance(cand_val, (int, float)):
            delta = cand_val - base_val
            sign = "+" if delta >= 0 else ""
            return f"- {label}: {base_val}{suffix} -> {cand_val}{suffix} ({sign}{round(delta, 2)}{suffix})"
        return f"- {label}: {base_val} -> {cand_val}"

    verdict_lines = []
    if candidate["total_return_pct"] > baseline["total_return_pct"]:
        verdict_lines.append("- Yeni aday strateji, toplam getiride eski stratejiyi geciyor.")
    else:
        verdict_lines.append("- Eski strateji, toplam getiride yeni adaydan daha iyi gorunuyor.")

    if candidate["max_drawdown_pct"] < baseline["max_drawdown_pct"]:
        verdict_lines.append("- Yeni aday daha az geri cekilme yasiyor; risk daha kontrollu.")
    else:
        verdict_lines.append("- Yeni aday daha derin geri cekilme yasiyor; risk tarafi daha sert.")

    if candidate["executed_trades"] < baseline["executed_trades"]:
        verdict_lines.append("- Yeni aday daha secici; daha az islem aciyor.")
    elif candidate["executed_trades"] > baseline["executed_trades"]:
        verdict_lines.append("- Yeni aday daha fazla islem aciyor; secicilik dusuyor.")
    else:
        verdict_lines.append("- Iki strateji neredeyse ayni islem sayisina sahip.")

    top_added = json.dumps(summary["top_added_symbols"], ensure_ascii=True, indent=2)
    top_removed = json.dumps(summary["top_removed_symbols"], ensure_ascii=True, indent=2)

    return "\n".join(
        [
            "# 2Y Profile Backtest Report",
            "",
            "Bu rapor, iki stratejiyi ayni gunluk proxy backtest mantigiyla karsilastirir.",
            "Canli MTF runtime birebir replay edilmedi; bunun yerine mevcut sade backtest mantigi uzerine iki profil uygulandi.",
            "",
            "## Kapsam",
            f"- Donem: {summary['window_start']} -> {summary['window_end']}",
            f"- Gun sayisi: {summary['window_days']}",
            f"- Istenen sembol: {summary['symbols_requested']}",
            f"- Kullanilan sembol: {summary['symbols_used']}",
            f"- Atlanan sembol: {summary['symbols_skipped']}",
            "",
            "## Kisa Yorum",
            *verdict_lines,
            "",
            "## Metrik Farki",
            diff_line("total_return_pct", "Toplam getiri", "%"),
            diff_line("final_capital", "Final sermaye", ""),
            diff_line("executed_trades", "Gerceklesen islem", ""),
            diff_line("signals_found", "Bulunan sinyal", ""),
            diff_line("win_rate_pct", "Kazanma orani", "%"),
            diff_line("profit_factor", "Profit factor", ""),
            diff_line("avg_trade_pnl", "Islem basi ortalama PnL", ""),
            diff_line("avg_hold_days", "Ortalama bekleme suresi", " gun"),
            diff_line("cagr_pct", "Yilliklandirilmis getiri", "%"),
            diff_line("sharpe", "Sharpe", ""),
            diff_line("max_drawdown_pct", "Max drawdown", "%"),
            "",
            "## Giris Farki",
            f"- Candidate tarafindan eklenen giris: {summary['added_entries_by_candidate']}",
            f"- Candidate tarafindan cikartilan giris: {summary['removed_entries_by_candidate']}",
            f"- Ortak giris orani: {summary['entry_overlap_pct']}%",
            "",
            "## En Cok Eklenen Semboller",
            "```json",
            top_added,
            "```",
            "",
            "## En Cok Cikarilan Semboller",
            "```json",
            top_removed,
            "```",
            "",
            "## Not",
            "- Bu calisma, mevcut rollout incelemesiyle tutarlilik icin gunluk proxy kullaniyor.",
            "- Yani sonuc, canlidaki tum intraday detaylari degil; ayni veri tabani uzerindeki iki profil farkini gosteriyor.",
            "- Gercek canli esdegerlik icin bir sonraki adim runtime threshold refactor ve shadow replay olmali.",
        ]
    )


def export_outputs(outputs: BacktestOutputs, prefix: str) -> dict[str, Path]:
    EXPECTED_DIR.mkdir(parents=True, exist_ok=True)
    paths = {
        "summary": EXPECTED_DIR / f"{prefix}_summary.json",
        "per_strategy": EXPECTED_DIR / f"{prefix}_per_strategy.csv",
        "entry_diff": EXPECTED_DIR / f"{prefix}_entry_diff.csv",
        "baseline_trades": EXPECTED_DIR / f"{prefix}_baseline_trades.csv",
        "candidate_trades": EXPECTED_DIR / f"{prefix}_candidate_trades.csv",
        "baseline_entries": EXPECTED_DIR / f"{prefix}_baseline_entries.csv",
        "candidate_entries": EXPECTED_DIR / f"{prefix}_candidate_entries.csv",
        "report": EXPECTED_DIR / f"{prefix}_report.md",
    }

    paths["summary"].write_text(json.dumps(outputs.summary, indent=2, ensure_ascii=True))
    outputs.per_strategy.to_csv(paths["per_strategy"], index=False)
    outputs.entry_diff.to_csv(paths["entry_diff"], index=False)
    outputs.baseline_trades.to_csv(paths["baseline_trades"], index=False)
    outputs.candidate_trades.to_csv(paths["candidate_trades"], index=False)
    outputs.baseline_entries.to_csv(paths["baseline_entries"], index=False)
    outputs.candidate_entries.to_csv(paths["candidate_entries"], index=False)
    paths["report"].write_text(render_report(outputs.summary))
    return paths


def run_profile_backtest(
    *,
    start: str,
    end: str,
    tickers_file: Path,
    capital: float,
    risk: float,
    kelly: float,
    max_symbols: int | None,
) -> BacktestOutputs:
    start_ts = pd.Timestamp(start)
    end_ts = pd.Timestamp(end)
    symbols = load_symbol_universe(tickers_file, max_symbols=max_symbols)

    index_frame = load_index_frame(start_ts, end_ts)
    if index_frame.empty:
        raise RuntimeError("Market index data could not be loaded for backtest window")

    symbol_frames: dict[str, pd.DataFrame] = {}
    skipped_symbols: dict[str, str] = {}
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {
            executor.submit(download_symbol_history, symbol, start_ts, end_ts): symbol
            for symbol in symbols
        }
        for future in as_completed(futures):
            symbol = futures[future]
            loaded_symbol, frame, reason = future.result()
            if frame is None:
                skipped_symbols[loaded_symbol] = reason or "unknown"
                continue
            symbol_frames[symbol] = frame

    if not symbol_frames:
        raise RuntimeError("No symbol data available for profile backtest")

    trading_dates = [ts for ts in index_frame.index if start_ts <= ts <= end_ts]

    baseline_engine = ProfileBacktestEngine(BASELINE_PROFILE, capital, risk, kelly)
    candidate_engine = ProfileBacktestEngine(OPTIMIZED_CANDIDATE_PROFILE, capital, risk, kelly)
    baseline_engine.run(symbol_frames, trading_dates, index_frame, "baseline_entry_ok")
    candidate_engine.run(symbol_frames, trading_dates, index_frame, "candidate_entry_ok")

    baseline_metrics = baseline_engine.build_metrics()
    candidate_metrics = candidate_engine.build_metrics()
    baseline_trades = pd.DataFrame(baseline_engine.trades, columns=TRADE_COLUMNS)
    candidate_trades = pd.DataFrame(candidate_engine.trades, columns=TRADE_COLUMNS)
    baseline_entries = pd.DataFrame(baseline_engine.entries, columns=ENTRY_COLUMNS)
    candidate_entries = pd.DataFrame(candidate_engine.entries, columns=ENTRY_COLUMNS)
    entry_diff = collect_entry_diff(baseline_entries, candidate_entries)

    summary = build_summary(
        start=start_ts,
        end=end_ts,
        symbols_requested=len(symbols),
        symbols_used=len(symbol_frames),
        skipped_symbols=skipped_symbols,
        baseline_metrics=baseline_metrics,
        candidate_metrics=candidate_metrics,
        entry_diff=entry_diff,
    )
    per_strategy = pd.DataFrame([baseline_metrics, candidate_metrics])
    return BacktestOutputs(
        summary=summary,
        per_strategy=per_strategy,
        entry_diff=entry_diff,
        baseline_trades=baseline_trades,
        candidate_trades=candidate_trades,
        baseline_entries=baseline_entries,
        candidate_entries=candidate_entries,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run 2Y old-vs-new profile backtest")
    parser.add_argument("--start", default=DEFAULT_START, help="Backtest start date (YYYY-MM-DD)")
    parser.add_argument("--end", default=DEFAULT_END, help="Backtest end date (YYYY-MM-DD)")
    parser.add_argument(
        "--tickers-file",
        default=str(DEFAULT_TICKERS_FILE),
        help="Ticker universe file",
    )
    parser.add_argument("--capital", type=float, default=10000.0, help="Initial capital")
    parser.add_argument("--risk", type=float, default=2.0, help="Risk per trade percent")
    parser.add_argument("--kelly", type=float, default=0.5, help="Kelly fraction")
    parser.add_argument(
        "--max-symbols", type=int, default=None, help="Optional symbol limit for smoke runs"
    )
    parser.add_argument(
        "--export-prefix",
        default="historical_profile_backtest_2y",
        help="Prefix for output files under tests/scanner_rollout/expected",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    outputs = run_profile_backtest(
        start=args.start,
        end=args.end,
        tickers_file=Path(args.tickers_file),
        capital=args.capital,
        risk=args.risk,
        kelly=args.kelly,
        max_symbols=args.max_symbols,
    )
    paths = export_outputs(outputs, args.export_prefix)
    print(json.dumps(outputs.summary, indent=2, ensure_ascii=True))
    print("\nGenerated files:")
    for path in paths.values():
        print(path)


if __name__ == "__main__":
    main()
