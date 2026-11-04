from types import SimpleNamespace

import pytest
from scripts.b2_n_diagnostic import diagnose_rows, validate_receipt


def test_diagnostic_dispatch_preserves_population_and_skips_unknown_inputs():
    calls = []
    model = SimpleNamespace(squeeze_interval=lambda value: calls.append(value) or {"decision": "UNRESOLVED"})
    rows = [{"symbol": "FAKE", "entry_ok": True, "squeeze_factor": 0.5},
            {"symbol": "FAKE", "entry_ok": False}, {"symbol": "OTHER"},
            {"entry_ok": "false"}, {"entry_ok": True},
            {"entry_ok": True, "squeeze_factor": True},
            {"entry_ok": True, "squeeze_factor": 0.5, "score_input": {"squeeze_factor": 0.6}}]
    result = diagnose_rows(rows, model)
    assert calls == [0.5]
    assert [row["row_index"] for row in result] == list(range(7))
    assert [row["entry_ok_state"] for row in result] == ["TRUE", "FALSE", "MISSING", "MALFORMED", "TRUE", "TRUE", "TRUE"]
    assert result[0]["squeeze"]["status"] == "CONDITIONAL_MODEL_ONLY"
    assert all(row["historical_recovery_claim"] == "NOT_ESTABLISHED" and row["atr"]["status"] == "NOT_EVALUATED" for row in result)
    assert result[-1]["squeeze"]["reason"] == "NESTED_ENCODING_DISAGREEMENT"
    assert "score_input" in rows[-1]


def test_diagnostic_dispatch_rejects_nonobject_population():
    with pytest.raises(ValueError, match="original rows"):
        diagnose_rows([None], SimpleNamespace())


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -0.1, 1.1, "0.5", False])
def test_invalid_factor_never_reaches_model(value):
    result = diagnose_rows([{"entry_ok": True, "squeeze_factor": value}], SimpleNamespace())
    assert result[0]["squeeze"] == {"status": "NOT_EVALUATED", "reason": "INVALID_TOP_LEVEL_SQUEEZE"}


def test_exact_diagnostic_authorization_not_inherited_from_another_study():
    receipt = {"study": "B2-N", "approved_by": "Meric", "execution_authorized": True, "manifest_sha256": "frozen"}
    validate_receipt(receipt, "frozen")
    for change in ({"study": "B2-T"}, {"study": "B2-1"}, {"execution_authorized": False}, {"manifest_sha256": "other"}, {"approved_by": None}):
        with pytest.raises(ValueError, match="exact B2-N"):
            validate_receipt(receipt | change, "frozen")
