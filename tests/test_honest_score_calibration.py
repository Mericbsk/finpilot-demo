from research.honest_score_calibration import _band, _evaluate


def test_score_bands_are_explicit_and_bounded():
    assert _band(0) == "0-20"
    assert _band(79.9) == "65-80"
    assert _band(100) == "80-100"
    assert _band(None) is None


def test_evaluate_returns_insufficient_data_without_predictions():
    assert _evaluate([{"band": "0-20", "target": 1.0}], {})["status"] == "insufficient_data"


def test_evaluate_marks_thin_bands_insufficient():
    result = _evaluate([{"band": "0-20", "target": 1.0}], {"0-20": 1.0}, minimum_band_n=2)

    assert result["bands"]["0-20"]["status"] == "insufficient_data"
