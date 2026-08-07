from research.decision_quality_experiments import model_views, veto_reasons


def test_veto_reasons_are_explicit_and_composable():
    reasons = veto_reasons(
        {
            "entry_ok": False,
            "regime": False,
            "direction": True,
            "atr_pct": 9.0,
            "gap": 6.0,
            "dist52": 0.97,
            "rvol": 0.8,
        },
        {"liquidity_ok": False},
    )

    assert "missing_entry_eligibility" in reasons
    assert "weak_trend" in reasons
    assert "high_volatility" in reasons
    assert "gap_risk" in reasons
    assert "near_52w_high" in reasons
    assert "low_relative_volume" in reasons
    assert "missing_liquidity_eligibility" in reasons


def test_model_views_are_not_a_composite_score():
    views = model_views(
        {
            "regime": True,
            "direction": True,
            "rvol": 2.0,
            "gap": 1.0,
            "atr_pct": 4.0,
            "dist52": 0.8,
        },
        {"liquidity_ok": True},
    )

    assert set(views) == {"trend", "momentum", "risk", "liquidity"}
    assert set(views.values()) == {"support"}
