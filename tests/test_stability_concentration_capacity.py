from research.stability_concentration_capacity import _concentration, _split_dates


def test_temporal_split_is_non_overlapping_and_leaves_locked_metadata():
    dates = [f"2026-01-{day:02d}" for day in range(1, 16)]

    split, groups = _split_dates(dates)

    split.validate()
    assert set(groups["train"]).isdisjoint(groups["validation"])
    assert set(groups["validation"]).isdisjoint(groups["locked_oos"])
    assert split.locked_oos_end == dates[-1]


def test_concentration_reports_hhi_and_top_three_share():
    result = _concentration(
        [{"sector": "Technology"}] * 3
        + [{"sector": "Healthcare"}] * 1
        + [{"sector": "Industrials"}] * 1,
        "sector",
    )

    assert result["status"] == "ok"
    assert result["n"] == 5
    assert result["hhi"] == 0.44
    assert result["top3_share"] == 1.0
