"""Score sözleşme testleri — 3 skor ölçeğinin (score 0-3, composite_score 0-100,
finpilot_score 0-100) davranışını kilitle.

Bu testler regresyon yakalamak için yazıldı; Faz 1 stabilizasyon kapsamında.
Davranış değiştirilmek istenirse önce buradaki test güncellenmeli.
"""

from __future__ import annotations

import pytest
from scanner.finpilot_score import compute_finpilot_score


class TestFinPilotScoreDRLBypass:
    """DRL mevcut değilken composite_score pass-through olmalı."""

    def test_drl_signal_none_returns_composite(self):
        assert compute_finpilot_score(75, "BUY", None, 0.8) == 75

    def test_drl_confidence_none_returns_composite(self):
        assert compute_finpilot_score(75, "BUY", "BUY", None) == 75

    def test_both_none_returns_composite(self):
        assert compute_finpilot_score(60, "SELL", None, None) == 60

    def test_zero_composite_returns_zero(self):
        assert compute_finpilot_score(0, "BUY", None, None) == 0

    def test_hundred_composite_returns_hundred(self):
        assert compute_finpilot_score(100, "BUY", None, None) == 100

    def test_composite_clamped_to_100(self):
        assert compute_finpilot_score(150, "BUY", None, None) == 100

    def test_composite_clamped_to_0(self):
        assert compute_finpilot_score(-10, "BUY", None, None) == 0


class TestFinPilotScoreWithDRL:
    """DRL aktifken ağırlıklı hesaplama (şu an _W_DRL=0.0, yani pratikte
    composite'e yakın ama agreement multiplier hesaba katılmıyor).
    """

    def test_drl_active_returns_int(self):
        result = compute_finpilot_score(75, "BUY", "BUY", 0.8)
        assert isinstance(result, int)
        assert 0 <= result <= 100

    def test_drl_clamped_to_100(self):
        # Yüksek composite + yüksek DRL confidence + agreement → 100'ü geçemez
        assert compute_finpilot_score(95, "BUY", "BUY", 0.95) <= 100

    def test_drl_clamped_to_0(self):
        # Düşük composite + düşük DRL confidence + çelişki → 0'ın altına inemez
        assert compute_finpilot_score(5, "BUY", "SELL", 0.1) >= 0

    def test_drl_hold_no_agreement_penalty(self):
        # DRL HOLD ise agreement=0, base ile aynı olmalı
        with_hold = compute_finpilot_score(70, "BUY", "HOLD", 0.5)
        with_none = compute_finpilot_score(70, "BUY", None, None)
        # _W_DRL=0 olduğu sürece ikisi de composite'e eşit olmalı
        assert with_hold == with_none == 70


class TestFinPilotScoreInputTypes:
    """Tip toleransı: int veya float composite kabul edilmeli."""

    def test_float_composite(self):
        assert compute_finpilot_score(75.7, "BUY", None, None) == 76

    def test_int_composite(self):
        assert compute_finpilot_score(75, "BUY", None, None) == 75

    def test_result_always_int(self):
        assert isinstance(compute_finpilot_score(50.5, "BUY", None, None), int)


@pytest.mark.parametrize("composite", [0, 25, 50, 75, 100])
def test_pass_through_when_drl_unavailable(composite):
    """Parametrik: her composite değeri DRL yokken aynısı dönmeli."""
    assert compute_finpilot_score(composite, "BUY", None, None) == composite
