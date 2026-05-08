"""Tests for Sprint 2-A/B new endpoints: SSE price stream + LLM explain."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def api_client():
    from api.main import app
    from fastapi.testclient import TestClient

    return TestClient(app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# Unit tests: prices._fetch_price_sync helper
# ---------------------------------------------------------------------------


class TestFetchPriceSync:
    def test_returns_expected_keys(self):
        from api.routers.prices import _fetch_price_sync

        mock_info = MagicMock()
        mock_info.last_price = 150.0
        mock_info.previous_close = 148.0

        mock_ticker = MagicMock()
        mock_ticker.fast_info = mock_info

        with patch("yfinance.Ticker", return_value=mock_ticker):
            result = _fetch_price_sync("MSFT")

        assert result["symbol"] == "MSFT"
        assert result["price"] == 150.0
        assert abs(result["change_pct"] - 1.35) < 0.1
        assert "ts" in result

    def test_zero_prev_close_does_not_divide_by_zero(self):
        from api.routers.prices import _fetch_price_sync

        mock_info = MagicMock()
        mock_info.last_price = 50.0
        mock_info.previous_close = 0.0

        mock_ticker = MagicMock()
        mock_ticker.fast_info = mock_info

        with patch("yfinance.Ticker", return_value=mock_ticker):
            result = _fetch_price_sync("XYZ")

        assert result["change_pct"] == 0.0

    def test_rounds_price_to_four_decimals(self):
        from api.routers.prices import _fetch_price_sync

        mock_info = MagicMock()
        mock_info.last_price = 123.456789
        mock_info.previous_close = 123.0

        mock_ticker = MagicMock()
        mock_ticker.fast_info = mock_info

        with patch("yfinance.Ticker", return_value=mock_ticker):
            result = _fetch_price_sync("AAPL")

        assert result["price"] == 123.4568


# ---------------------------------------------------------------------------
# Unit tests: symbol validation regex
# ---------------------------------------------------------------------------


class TestSymbolValidation:
    def test_valid_symbols_pass(self):
        from api.routers.prices import _SYMBOL_RE

        valid = ["AAPL", "TSLA", "BRK.B", "MSFT", "A", "ABCDE12345"]  # pragma: allowlist secret
        for sym in valid:
            assert _SYMBOL_RE.match(sym), f"{sym!r} should match"

    def test_invalid_symbols_fail(self):
        from api.routers.prices import _SYMBOL_RE

        invalid = ["", "TOO_LONG_SYM!", "aapl", "AAPL MSFT", "A" * 11]
        for sym in invalid:
            assert not _SYMBOL_RE.match(sym), f"{sym!r} should not match"


# ---------------------------------------------------------------------------
# Route registration sanity checks (no streaming)
# ---------------------------------------------------------------------------


class TestRouteRegistration:
    def test_prices_stream_route_exists(self, api_client):
        """GET /prices/stream/{symbol} must be registered (not 404)."""
        mock_data = {"symbol": "AAPL", "price": 1.0, "change_pct": 0.0, "ts": "now"}
        # Patch sleep to immediately raise StopAsyncIteration so the loop exits
        with patch("api.routers.prices._fetch_price_sync", return_value=mock_data):
            with patch("asyncio.sleep", side_effect=StopAsyncIteration):
                resp = api_client.get(
                    "/api/v1/prices/stream/AAPL",
                    headers={"Accept": "text/event-stream"},
                    timeout=3,
                )
        assert resp.status_code != 404

    def test_llm_explain_route_exists(self, api_client):
        """GET /llm/explain/{symbol} must be registered (not 404)."""
        mock_router = MagicMock()
        mock_router.available_providers = []
        with patch("llm.get_router", return_value=mock_router):
            resp = api_client.get(
                "/api/v1/llm/explain/AAPL",
                headers={"Accept": "text/event-stream"},
                timeout=3,
            )
        assert resp.status_code != 404

    def test_llm_explain_no_providers_returns_error_body(self):
        """With no providers, the generator should yield an error SSE event."""
        import asyncio

        from api.routers.llm import explain_symbol_stream

        mock_router = MagicMock()
        mock_router.available_providers = []

        with patch("llm.get_router", return_value=mock_router):

            async def run():
                resp = await explain_symbol_stream("AAPL", language="en")
                parts = []
                async for chunk in resp.body_iterator:
                    parts.append(chunk.decode() if isinstance(chunk, bytes) else chunk)
                return "".join(parts)

            body = asyncio.run(run())

        assert "error" in body
        assert "No LLM" in body or "unavailable" in body.lower()

    def test_llm_explain_invalid_symbol_returns_error(self):
        """Invalid symbol char → immediate error SSE event."""
        import asyncio

        from api.routers.llm import explain_symbol_stream

        async def run():
            resp = await explain_symbol_stream("bad!sym", language="en")
            parts = []
            async for chunk in resp.body_iterator:
                parts.append(chunk.decode() if isinstance(chunk, bytes) else chunk)
            return "".join(parts)

        body = asyncio.run(run())
        assert "error" in body
        assert "invalid symbol" in body


# ---------------------------------------------------------------------------
# LLM explain stream: unit test the generator (bypasses HTTP)
# ---------------------------------------------------------------------------


class TestLLMExplainGenerator:
    def test_generator_emits_chunks_then_done(self):
        """Test the async generator logic directly without HTTP overhead."""
        import asyncio

        tokens = ["Hello", " world", "!"]

        async def run():
            from api.routers.llm import explain_symbol_stream

            mock_router = MagicMock()
            mock_router.available_providers = ["groq"]
            mock_router.stream.return_value = iter(tokens)

            chunks = []
            done_seen = False

            with patch("llm.get_router", return_value=mock_router):
                response = await explain_symbol_stream("TEST", language="en")
                async for chunk in response.body_iterator:
                    line = chunk.decode() if isinstance(chunk, bytes) else chunk
                    if not line.startswith("data: "):
                        continue
                    payload = json.loads(line[6:])
                    if payload.get("done"):
                        done_seen = True
                        break
                    if "chunk" in payload:
                        chunks.append(payload["chunk"])

            return chunks, done_seen

        chunks, done_seen = asyncio.run(run())
        assert "".join(chunks) == "Hello world!"
        assert done_seen
