from __future__ import annotations

from tests.scanner_rollout.historical_compare import compare_shortlist_history


def test_historical_comparison_has_meaningful_coverage():
    result = compare_shortlist_history(window_days=365)

    assert result.summary["files_used"] > 0
    assert result.summary["rows_evaluated"] > 0
    assert result.summary["coverage_start"] < result.summary["coverage_end"]


def test_historical_comparison_detects_old_vs_new_differences():
    result = compare_shortlist_history(window_days=365)

    assert result.summary["added_by_candidate"] > 0
    assert result.summary["removed_by_candidate"] > 0
    assert not result.changes.empty
    assert set(result.changes["change_type"].unique()) <= {
        "added_by_candidate",
        "removed_by_candidate",
    }
