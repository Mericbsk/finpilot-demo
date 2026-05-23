"""Tests for core.analytics — event counter module."""

from __future__ import annotations

import importlib

import pytest


@pytest.fixture(autouse=True)
def _reset_analytics():
    """Reset analytics module state before each test."""
    import core.analytics as m

    m._redis_unavailable = True
    m._redis_client = None
    m._mem_counters.clear()
    importlib.reload(m)
    # Force in-memory mode after reload
    m._redis_unavailable = True
    m._redis_client = None
    m._mem_counters.clear()
    yield


def test_increment_page_view_creates_counter():
    from core.analytics import _mem_counters, increment_page_view

    increment_page_view("/dashboard")
    assert _mem_counters["page_view:/dashboard"] == 1


def test_increment_page_view_accumulates():
    from core.analytics import _mem_counters, increment_page_view

    increment_page_view("/agent")
    increment_page_view("/agent")
    increment_page_view("/agent")
    assert _mem_counters["page_view:/agent"] == 3


def test_increment_event_creates_counter():
    from core.analytics import _mem_counters, increment_event

    increment_event("champion_edge_query")
    assert _mem_counters["event:champion_edge_query"] == 1


def test_increment_event_accumulates():
    from core.analytics import _mem_counters, increment_event

    increment_event("scan_run")
    increment_event("scan_run")
    assert _mem_counters["event:scan_run"] == 2


def test_get_summary_empty():
    from core.analytics import get_summary

    s = get_summary()
    assert s["page_views"] == {}
    assert s["events"] == {}


def test_get_summary_populated():
    from core.analytics import get_summary, increment_event, increment_page_view

    increment_page_view("/dashboard")
    increment_page_view("/dashboard")
    increment_event("scan_run")
    increment_event("champion_edge_query")

    s = get_summary()
    assert s["page_views"]["/dashboard"] == 2
    assert s["events"]["scan_run"] == 1
    assert s["events"]["champion_edge_query"] == 1


def test_get_summary_separates_page_views_and_events():
    from core.analytics import get_summary, increment_event, increment_page_view

    increment_page_view("/agent")
    increment_event("agent_event")

    s = get_summary()
    assert "/agent" in s["page_views"]
    assert "agent_event" in s["events"]
    # page view not in events and vice-versa
    assert "/agent" not in s["events"]
    assert "agent_event" not in s["page_views"]


def test_multiple_page_paths_tracked_independently():
    from core.analytics import get_summary, increment_page_view

    increment_page_view("/dashboard")
    increment_page_view("/agent")
    increment_page_view("/scanner")

    s = get_summary()
    assert s["page_views"]["/dashboard"] == 1
    assert s["page_views"]["/agent"] == 1
    assert s["page_views"]["/scanner"] == 1
