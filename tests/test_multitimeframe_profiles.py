from __future__ import annotations

from research.multitimeframe_profiles import classify_multitimeframe_profile


def test_full_alignment_and_momentum_is_confirmatory():
    assert (
        classify_multitimeframe_profile(
            alignment_ratio=1.0, momentum_ratio=0.67, momentum_confluence=True
        )
        == "confirmatory"
    )


def test_partial_alignment_with_momentum_is_early():
    assert (
        classify_multitimeframe_profile(
            alignment_ratio=0.67, momentum_ratio=0.67, momentum_confluence=True
        )
        == "early"
    )


def test_missing_momentum_confluence_is_not_early():
    assert (
        classify_multitimeframe_profile(
            alignment_ratio=0.67, momentum_ratio=0.67, momentum_confluence=False
        )
        == "insufficient_data"
    )


def test_weak_momentum_is_not_early():
    assert (
        classify_multitimeframe_profile(
            alignment_ratio=0.67, momentum_ratio=0.49, momentum_confluence=True
        )
        == "insufficient_data"
    )


def test_ratio_values_are_clamped_before_classification():
    assert (
        classify_multitimeframe_profile(
            alignment_ratio=1.4, momentum_ratio=1.4, momentum_confluence=True
        )
        == "confirmatory"
    )
