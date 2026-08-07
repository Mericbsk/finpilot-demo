from research.negative_control import _permuted_signal_returns, _summary


def test_matched_signal_permutation_preserves_daily_signal_count():
    rows = [
        {"scan_date": "2026-01-01"},
        {"scan_date": "2026-01-01"},
        {"scan_date": "2026-01-02"},
        {"scan_date": "2026-01-02"},
    ]
    values = [1.0, 2.0, 10.0, 20.0]
    selected = {0, 2}

    result = _permuted_signal_returns(rows, values, selected, seed=7, mode="signal_permutation")

    assert result in {5.5, 6.0, 10.5, 11.0}


def test_null_summary_reports_candidate_percentile():
    result = _summary([-1.0, 0.0, 1.0], candidate_mean=0.5)

    assert result["status"] == "ok"
    assert result["candidate_percentile"] == 0.666667
