"""Storage helpers for alternative data ETL outputs."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Optional

import pandas as pd


@dataclass(frozen=True)
class StorageResult:
    rows_written: int
    partitions: int
    base_path: Path


def build_partition_path(base_path: Path, source: str, symbol: str, timestamp: pd.Timestamp) -> Path:
    ts = pd.Timestamp(timestamp).tz_convert("UTC") if pd.Timestamp(timestamp).tzinfo else pd.Timestamp(timestamp).tz_localize("UTC")
    return base_path / source.lower() / symbol.upper() / f"{ts.year:04d}" / f"{ts.month:02d}" / f"{ts.day:02d}"


def ensure_timestamp_column(frame: pd.DataFrame, column_name: str = "timestamp") -> pd.DataFrame:
    if column_name in frame.columns:
        return frame
    if frame.index.name == column_name:
        return frame.reset_index()
    if column_name not in frame.index.names:
        raise KeyError(f"DataFrame does not expose a '{column_name}' column or index")
    return frame.reset_index()


Compression = Literal["snappy", "gzip", "brotli", "lz4", "zstd"]


def write_partitioned_parquet(
    frame: pd.DataFrame,
    *,
    base_path: Path,
    source: str,
    symbol: str,
    timestamp_column: str = "timestamp",
    compression: Compression = "snappy",
) -> StorageResult:
    if frame.empty:
        return StorageResult(rows_written=0, partitions=0, base_path=base_path)

    frame = ensure_timestamp_column(frame, timestamp_column)
    frame[timestamp_column] = pd.to_datetime(frame[timestamp_column], utc=True)

    rows_written = 0
    partitions = 0
    for partition_ts, partition_df in frame.groupby(frame[timestamp_column].dt.normalize()):
        partition_path = build_partition_path(base_path, source, symbol, partition_ts)
        partition_path.mkdir(parents=True, exist_ok=True)
        file_path = partition_path / f"data.parquet"
        partition_df.to_parquet(file_path, index=False, compression=compression)
        rows_written += len(partition_df)
        partitions += 1

    return StorageResult(rows_written=rows_written, partitions=partitions, base_path=base_path)


__all__ = ["StorageResult", "write_partitioned_parquet", "build_partition_path", "ensure_timestamp_column"]
