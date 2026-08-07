from research.score_bridge import build_score_bridge


def test_bridge_reconciles_live_score_and_exposes_filter_overlap():
    row = {
        "regime": True,
        "direction": True,
        "score": 3,
        "filter_score": 3,
        "alignment_ratio": 1.0,
        "momentum_ratio": 1.0,
        "vol_regime": 0,
        "volume_spike": True,
        "price_momentum": True,
        "trend_strength": True,
    }

    bridge = build_score_bridge(row, research_score=8.0)

    assert bridge["live_score"] == 16.0
    assert bridge["score_delta"] == 8.0
    assert bridge["filter_flag_count"] == 3
    assert bridge["filter_accounting_delta"] == 0.0
    assert bridge["live_components"]["total"] == bridge["live_score"]


def test_bridge_marks_missing_research_score_instead_of_inventing_one():
    bridge = build_score_bridge({"score": 1})

    assert bridge["research_score"] is None
    assert bridge["score_delta"] is None
    assert bridge["research_score_status"] == "missing"
