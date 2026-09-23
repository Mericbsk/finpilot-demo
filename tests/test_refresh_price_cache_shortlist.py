"""Unit tests for the --shortlist scope-widening helpers in refresh_price_cache.py.

Pure file I/O logic — no network, no EODHD key required.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_SPEC = importlib.util.spec_from_file_location(
    "refresh_price_cache", Path(__file__).resolve().parents[1] / "refresh_price_cache.py"
)
refresh_price_cache = importlib.util.module_from_spec(_SPEC)
sys.modules["refresh_price_cache"] = refresh_price_cache
_SPEC.loader.exec_module(refresh_price_cache)


@pytest.fixture
def shortlist_dir(tmp_path: Path) -> Path:
    d = tmp_path / "shortlists"
    d.mkdir()
    return d


def _write_csv(path: Path, symbols: list[str]) -> None:
    lines = ["symbol,price,score"]
    lines += [f"{s},1.0,10" for s in symbols]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_shortlist_symbols_reads_unique_nonempty_symbols(tmp_path: Path):
    path = tmp_path / "shortlist_a.csv"
    _write_csv(path, ["AAPL", "MSFT", "AAPL", ""])
    result = refresh_price_cache.shortlist_symbols(str(path))
    assert result == {"AAPL", "MSFT"}


def test_latest_shortlist_path_picks_most_recently_modified(shortlist_dir: Path):
    older = shortlist_dir / "shortlist_20260101_0900.csv"
    newer = shortlist_dir / "shortlist_20260814_1157.csv"
    _write_csv(older, ["AAPL"])
    _write_csv(newer, ["LX"])
    # force distinct, ordered mtimes regardless of filesystem timestamp resolution
    import os
    import time

    os.utime(older, (time.time() - 100, time.time() - 100))
    os.utime(newer, (time.time(), time.time()))

    result = refresh_price_cache.latest_shortlist_path(str(shortlist_dir))
    assert result == str(newer)


def test_latest_shortlist_path_returns_none_when_no_csv(shortlist_dir: Path):
    assert refresh_price_cache.latest_shortlist_path(str(shortlist_dir)) is None


def test_latest_shortlist_path_returns_none_when_dir_missing(tmp_path: Path):
    missing = tmp_path / "does-not-exist"
    assert refresh_price_cache.latest_shortlist_path(str(missing)) is None


def test_shortlist_symbols_ignores_missing_symbol_column(tmp_path: Path):
    path = tmp_path / "no_symbol_col.csv"
    path.write_text("price,score\n1.0,10\n", encoding="utf-8")
    assert refresh_price_cache.shortlist_symbols(str(path)) == set()
