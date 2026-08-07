from research.evidence_ledger import EvidenceError, EvidenceEvent


def make_event(**overrides) -> EvidenceEvent:
    values = {
        "symbol": "aapl",
        "scan_date": "2026-08-01",
        "snapshot_id": "snapshot-001",
        "feature_as_of": "2026-08-01T13:30:00+00:00",
        "label_version": "tb-v1",
        "cost_model_version": "cost-v1",
    }
    values.update(overrides)
    return EvidenceEvent(**values)


def test_event_id_is_stable_and_normalizes_symbol():
    first = make_event()
    second = make_event(symbol=" AAPL ")

    assert first.event_id == second.event_id
    assert first.as_dict()["event_id"] == first.event_id


def test_feature_timestamp_cannot_leak_after_scan_date():
    event = make_event(feature_as_of="2026-08-02T00:00:00+00:00")

    try:
        event.validate()
    except EvidenceError as error:
        assert "after scan_date" in str(error)
    else:
        raise AssertionError("future feature timestamp was accepted")


def test_resolved_event_requires_outcome_timestamp():
    event = make_event(outcome_status="resolved")

    try:
        event.validate()
    except EvidenceError as error:
        assert "outcome_as_of" in str(error)
    else:
        raise AssertionError("resolved event without maturity timestamp was accepted")


def test_naive_feature_timestamp_is_rejected():
    event = make_event(feature_as_of="2026-08-01T13:30:00")

    try:
        event.validate()
    except EvidenceError as error:
        assert "timezone" in str(error)
    else:
        raise AssertionError("naive timestamp was accepted")
