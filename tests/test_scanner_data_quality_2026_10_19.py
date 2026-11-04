"""Regression tests for the 2026-10-19 scanner data-quality fix (decision-log).

1. Daily Alpaca bars use the consolidated SIP feed (IEX carries ~2-4% of US
   volume), adjusted for corporate actions, with the request end at least
   15 minutes old (data-plan limit). Intraday bars stay on IEX.
2. The earnings blackout window covers the 5-trading-day holding period.

All tests are synthetic: no network, no credentials.
"""

from __future__ import annotations

import time
from datetime import UTC, datetime, timedelta

import pytest

import scanner.data_fetcher as data_fetcher
import scanner.earnings_blackout as earnings_blackout
from scanner.evaluate import evaluate_symbol
from tests.test_evaluate import TestEvaluateSymbol as _EvalFixtures


def _value(field):
    return getattr(field, "value", field)


def _utc(dt):
    """alpaca-py stores request datetimes as naive UTC."""
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


@pytest.fixture
def captured_requests(monkeypatch):
    """Capture StockBarsRequest objects without any network call."""
    captured = []

    def _fake_retry(client, req, interval, days):
        captured.append(req)
        return None  # forces the caller's documented fallback path

    monkeypatch.setattr(data_fetcher, "_alpaca_available", lambda: True)
    monkeypatch.setattr(data_fetcher, "_get_alpaca_client", lambda: object())
    monkeypatch.setattr(data_fetcher, "_get_stock_bars_with_retry", _fake_retry)
    return captured


def test_daily_bars_use_sip_adjusted_and_delayed(captured_requests):
    before = datetime.now(UTC)
    data_fetcher._prefetch_alpaca_bulk(["AAA"], [("1d", 300)], with_indicators=False)

    assert len(captured_requests) == 1
    req = captured_requests[0]
    assert _value(req.feed) == "sip"
    assert _value(req.adjustment) == "all"
    min_delay = timedelta(minutes=data_fetcher._SIP_MIN_DELAY_MINUTES)
    assert _utc(req.end) <= before - min_delay + timedelta(seconds=5)
    assert data_fetcher._SIP_MIN_DELAY_MINUTES > 15


def test_intraday_bars_stay_on_iex_without_delay(captured_requests):
    before = datetime.now(UTC)
    data_fetcher._prefetch_alpaca_bulk(["AAA"], [("15m", 5)], with_indicators=False)

    assert len(captured_requests) == 1
    req = captured_requests[0]
    assert _value(req.feed) == "iex"
    assert _value(req.adjustment) == "all"
    assert _utc(req.end) >= before - timedelta(seconds=5)


def test_evaluate_uses_holding_period_earnings_window(monkeypatch):
    calls = []

    def _fake_blackout(symbol, days_before=2, days_after=1):
        calls.append((days_before, days_after))
        return False

    monkeypatch.setattr(earnings_blackout, "is_earnings_blackout", _fake_blackout)
    monkeypatch.setattr(earnings_blackout, "earnings_proximity", lambda symbol: 0.0)

    evaluate_symbol("TEST", prefetched_data=_EvalFixtures._make_mock_data())

    assert calls == [(7, 1)]


def test_earnings_five_days_out_is_blacked_out_with_new_window(monkeypatch):
    in_five_days = time.time() + 5 * 86400
    monkeypatch.setattr(earnings_blackout, "_get_next_earnings_cached", lambda s: in_five_days)

    assert earnings_blackout.is_earnings_blackout("X", days_before=7, days_after=1)
    # The previous 2-day window let this position open into the print.
    assert not earnings_blackout.is_earnings_blackout("X", days_before=2, days_after=1)
