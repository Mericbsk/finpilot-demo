"""Inference memory cache testleri — disk I/O bir kez, sonra memory."""

from __future__ import annotations

import json
from pathlib import Path

import pytest


@pytest.fixture
def tmp_inference(tmp_path, monkeypatch):
    """Geçici inference.json + path patch."""
    from api.routers import inference as inf_mod

    p = tmp_path / "inference.json"
    monkeypatch.setattr(inf_mod, "_INFERENCE_PATH", p)
    # Memory cache'i sıfırla
    monkeypatch.setattr(inf_mod, "_mem_cache", None)
    return p, inf_mod


def test_missing_file_returns_empty(tmp_inference):
    _, inf_mod = tmp_inference
    data, status = inf_mod._load_cached_inference()
    assert data == {}
    assert status["valid"] is False
    assert status["symbol_count"] == 0


def test_first_read_populates_cache(tmp_inference):
    p, inf_mod = tmp_inference
    p.write_text(
        json.dumps({"AAPL": {"timestamp": "2026-05-23T12:00:00+00:00", "confidence": 0.7}})
    )
    data, status = inf_mod._load_cached_inference()
    assert "AAPL" in data
    assert inf_mod._mem_cache is not None


def test_unchanged_mtime_uses_cache(tmp_inference, monkeypatch):
    p, inf_mod = tmp_inference
    p.write_text(
        json.dumps({"AAPL": {"timestamp": "2026-05-23T12:00:00+00:00", "confidence": 0.7}})
    )
    inf_mod._load_cached_inference()

    # read_text çağrılırsa fail et — cache hit beklenir
    original_read = Path.read_text

    call_count = {"n": 0}

    def counting_read(self, *args, **kwargs):
        call_count["n"] += 1
        return original_read(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", counting_read)
    inf_mod._load_cached_inference()
    inf_mod._load_cached_inference()
    assert call_count["n"] == 0, "Cache miss — file was re-read despite same mtime"


def test_mtime_change_invalidates_cache(tmp_inference):
    p, inf_mod = tmp_inference
    p.write_text(
        json.dumps({"AAPL": {"timestamp": "2026-05-23T12:00:00+00:00", "confidence": 0.5}})
    )
    data1, _ = inf_mod._load_cached_inference()
    assert data1["AAPL"]["confidence"] == 0.5

    import os
    import time

    time.sleep(0.01)
    p.write_text(
        json.dumps({"AAPL": {"timestamp": "2026-05-23T13:00:00+00:00", "confidence": 0.9}})
    )
    # mtime'i ileri taşı (Windows precision için)
    future = time.time() + 1
    os.utime(p, (future, future))

    data2, _ = inf_mod._load_cached_inference()
    assert data2["AAPL"]["confidence"] == 0.9


def test_malformed_json_returns_empty(tmp_inference):
    p, inf_mod = tmp_inference
    p.write_text("{not valid json")
    data, status = inf_mod._load_cached_inference()
    assert data == {}
    assert status["valid"] is False
