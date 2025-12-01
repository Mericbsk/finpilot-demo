"""Async adapter for Glassnode-like on-chain analytics providers."""
from __future__ import annotations

from typing import Any, Mapping, Optional, Sequence

import pandas as pd

from ..async_base import (
    AsyncHTTPAdapter,
    AsyncHTTPClient,
    CircuitBreakerConfig,
    RateLimitConfig,
    RetryConfig,
)
from ..exceptions import AdapterResponseError
from ..onchain import normalize_onchain_rows
from ..base import DataSlice


def _to_unix(ts: Optional[pd.Timestamp | str | int | float]) -> Optional[int]:
    if ts is None:
        return None
    stamp = pd.Timestamp(ts)
    if stamp.tzinfo is None:
        stamp = stamp.tz_localize("UTC")
    else:
        stamp = stamp.tz_convert("UTC")
    return int(stamp.timestamp())


class GlassnodeAdapter(AsyncHTTPAdapter):
    """Adapter for Glassnode REST API returning on-chain metrics."""

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        endpoint: str = "/v2/metrics/custom",
        frequency: str = "1d",
        extra_filters: Optional[Mapping[str, Any]] = None,
        provider: str = "glassnode",
        rate_limit: Optional[RateLimitConfig] = None,
        retry: Optional[RetryConfig] = None,
        circuit_breaker: Optional[CircuitBreakerConfig] = None,
        timeout: Optional[float] = 10.0,
    ) -> None:
        params = dict(extra_filters or {})
        self._endpoint = endpoint
        self._frequency = frequency
        self._extra_filters = params
        headers = {"X-Api-Key": api_key}
        client = AsyncHTTPClient(
            base_url=base_url,
            provider=provider,
            timeout=timeout,
            default_headers=headers,
            rate_limit=rate_limit,
            retry=retry,
            circuit_breaker=circuit_breaker,
        )
        super().__init__(client=client, provider=provider)

    async def fetch_async(
        self,
        symbol: str,
        *,
        start: Optional[pd.Timestamp] = None,
        end: Optional[pd.Timestamp] = None,
    ) -> DataSlice:
        params: dict[str, Any] = {"symbol": symbol, "interval": self._frequency}
        params.update(self._extra_filters)
        start_unix = _to_unix(start)
        end_unix = _to_unix(end)
        if start_unix is not None:
            params["start"] = start_unix
        if end_unix is not None:
            params["end"] = end_unix

        payload = await self.client.get_json(self._endpoint, params=params)
        data: Optional[Sequence[Mapping[str, Any]]]
        if isinstance(payload, Mapping):
            data = payload.get("data")  # new API schema
        else:
            data = payload  # fallback for legacy API returning list

        if not isinstance(data, Sequence):
            raise AdapterResponseError("Provider response missing 'data' array", provider=self.provider)

        rows = []
        for entry in data:
            if not isinstance(entry, Mapping):
                continue
            rows.append(
                {
                    "timestamp": entry.get("t") or entry.get("timestamp"),
                    "onchain_active_addresses": entry.get("activeAddresses")
                    or entry.get("onchain_active_addresses"),
                    "onchain_tx_volume": entry.get("transactionValue")
                    or entry.get("onchain_tx_volume"),
                    "stablecoin_ratio": entry.get("stablecoinRatio") or entry.get("stablecoin_ratio"),
                }
            )

        frame = normalize_onchain_rows(rows)
        metadata = self._build_metadata(symbol, rows=len(frame))
        return DataSlice(frame=frame, metadata=metadata)


__all__ = ["GlassnodeAdapter"]
