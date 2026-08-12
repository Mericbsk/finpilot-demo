"""FinSense reasoning layer — /api/v1/finsense/* — VS-01 Phase 3.

Case -> Prediction -> Outcome -> Evaluation, per
docs/strategy/FinSense_Vertical_Slice_Specification_v1_2026-08-11.md.

Design rules this router enforces (Contract LOCK-02/03/04/05/06):
  - The client never supplies `committed_at` or any outcome field — both are
    always server- or FinPilot-derived.
  - A prediction is immutable once committed: there is no PATCH/PUT endpoint,
    and a second POST for the same (anonymous_user_id, case_id) is rejected
    with 409 (backed by the DB's own UNIQUE constraint, not just app logic).
  - `actual_direction`/`actual_return_pct` are read from `fs_outcomes`, which
    is only ever populated by importing FinPilot's own resolver output
    (scripts/export_resolved_cases.py) — this router never computes them.
  - No calibration/Brier/bucket output here (LOCK-05) — evaluation is the raw,
    single-prediction comparison only.
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import UTC, datetime
from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Response, status
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/finsense", tags=["finsense"])

Direction = Literal["UP", "DOWN", "FLAT"]


def _get_db():
    from auth.database import Database

    db = Database()
    db.initialize()
    return db


# ─────────────────────────────────────────────────────────────────────────────
# Schemas
# ─────────────────────────────────────────────────────────────────────────────
class PredictRequest(BaseModel):
    anonymous_user_id: str = Field(..., min_length=8, max_length=128)
    direction: Direction
    probability: float = Field(..., ge=0.0, le=1.0)
    reason: str = Field(..., min_length=20, max_length=500)


class PredictionOut(BaseModel):
    id: str
    case_id: str
    direction: Direction
    probability: float
    reason: str
    committed_at: str


class CaseOut(BaseModel):
    id: str
    asset: str
    event_timestamp: str
    snapshot: dict[str, Any]
    context: str
    horizon_days: int
    # Deliberately NO outcome/grade field — see LOCK-03/Contract §17.
    my_prediction: PredictionOut | None = None
    # ^ Phase 5 addition (refresh problem): lets the client discover, on load,
    # that IT already predicted on this case — so a refresh after commit lands
    # on the locked screen instead of re-showing the prediction form. Only
    # ever the caller's OWN prediction (direction/probability/reason/
    # committed_at) — never actual_direction/actual_return_pct/resolved_at/
    # evaluation, which stay behind GET /case/{id}/outcome (LOCK-03 still
    # holds: this is not an outcome leak, just "did *I* already commit").


class EvaluationOut(BaseModel):
    direction_correct: bool
    binary_outcome: int
    probability_error: float


class OutcomeOut(BaseModel):
    case_id: str
    actual_direction: Direction
    actual_return_pct: float | None
    resolved_at: str
    your_prediction: PredictionOut | None = None
    evaluation: EvaluationOut | None = None


# ─────────────────────────────────────────────────────────────────────────────
# GET /finsense/case/today
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/case/today", response_model=CaseOut | None)
def get_case_today(response: Response, anonymous_user_id: str | None = None) -> CaseOut | None:
    """Returns the open case, if any. No outcome/grade field is ever included
    here — outcome only exists behind GET /case/{id}/outcome, after resolution.

    `anonymous_user_id` is optional and purely additive: when supplied, the
    response also carries `my_prediction` (this caller's own prediction on
    this case, if one already exists) so the client can render the locked
    state immediately after a refresh instead of re-showing the form and
    then hitting 409 on submit."""
    db = _get_db()
    try:
        with db.connection() as conn:
            row = conn.execute(
                "SELECT id, asset, event_timestamp, snapshot, context, horizon_days "
                "FROM fs_cases WHERE status = 'open' ORDER BY created_at DESC LIMIT 1"
            ).fetchone()
    except Exception as exc:  # noqa: BLE001
        logger.warning("[finsense] case/today failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"case lookup error: {exc}") from exc

    if row is None:
        response.status_code = status.HTTP_204_NO_CONTENT
        return None

    my_prediction: PredictionOut | None = None
    if anonymous_user_id:
        with db.connection() as conn:
            pred_row = conn.execute(
                "SELECT id, direction, probability, reason, committed_at FROM fs_predictions "
                "WHERE case_id = ? AND anonymous_user_id = ?",
                (row["id"], anonymous_user_id),
            ).fetchone()
        if pred_row is not None:
            my_prediction = PredictionOut(
                id=pred_row["id"],
                case_id=row["id"],
                direction=pred_row["direction"],
                probability=pred_row["probability"],
                reason=pred_row["reason"],
                committed_at=pred_row["committed_at"],
            )

    return CaseOut(
        id=row["id"],
        asset=row["asset"],
        event_timestamp=row["event_timestamp"],
        snapshot=json.loads(row["snapshot"]),
        context=row["context"],
        horizon_days=row["horizon_days"],
        my_prediction=my_prediction,
    )


# ─────────────────────────────────────────────────────────────────────────────
# POST /finsense/case/{case_id}/predict
# ─────────────────────────────────────────────────────────────────────────────
@router.post("/case/{case_id}/predict", response_model=PredictionOut, status_code=201)
def predict(case_id: str, req: PredictRequest) -> PredictionOut:
    db = _get_db()

    with db.connection() as conn:
        case_row = conn.execute(
            "SELECT id, status FROM fs_cases WHERE id = ?", (case_id,)
        ).fetchone()
    if case_row is None:
        raise HTTPException(status_code=404, detail="case not found")
    if case_row["status"] != "open":
        raise HTTPException(status_code=400, detail="case is not open for predictions")

    prediction_id = f"pred_{uuid.uuid4().hex[:12]}"
    now = datetime.now(UTC).isoformat()  # server-generated — client cannot override

    try:
        with db.connection() as conn:
            conn.execute(
                "INSERT INTO fs_predictions (id, case_id, anonymous_user_id, direction, "
                "probability, reason, status, committed_at, created_at) "
                "VALUES (?,?,?,?,?,?,?,?,?)",
                (
                    prediction_id,
                    case_id,
                    req.anonymous_user_id,
                    req.direction,
                    req.probability,
                    req.reason,
                    "committed",
                    now,
                    now,
                ),
            )
    except Exception as exc:  # noqa: BLE001
        # UNIQUE(anonymous_user_id, case_id) violation -> this user already
        # predicted on this case. Immutability (LOCK-04): no edit path, just 409.
        if "UNIQUE" in str(exc):
            raise HTTPException(
                status_code=409,
                detail="a prediction for this user and case already exists and cannot be changed",
            ) from exc
        logger.warning("[finsense] predict failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"predict error: {exc}") from exc

    return PredictionOut(
        id=prediction_id,
        case_id=case_id,
        direction=req.direction,
        probability=req.probability,
        reason=req.reason,
        committed_at=now,
    )


# ─────────────────────────────────────────────────────────────────────────────
# GET /finsense/case/{case_id}/outcome
# ─────────────────────────────────────────────────────────────────────────────
def _binary_outcome(predicted_direction: str, actual_direction: str) -> int:
    """1 if the actual direction matches what the user predicted, else 0 —
    symmetric for UP/DOWN/FLAT (see VS spec §3.1: probability is always
    'probability of MY chosen direction', not always 'probability of UP')."""
    return 1 if predicted_direction == actual_direction else 0


@router.get("/case/{case_id}/outcome", response_model=OutcomeOut)
def get_outcome(case_id: str, anonymous_user_id: str | None = None) -> OutcomeOut:
    db = _get_db()

    with db.connection() as conn:
        outcome_row = conn.execute(
            "SELECT case_id, actual_direction, actual_return_pct, resolved_at "
            "FROM fs_outcomes WHERE case_id = ?",
            (case_id,),
        ).fetchone()

    if outcome_row is None:
        raise HTTPException(status_code=404, detail="outcome pending — case not yet resolved")

    result = OutcomeOut(
        case_id=outcome_row["case_id"],
        actual_direction=outcome_row["actual_direction"],
        actual_return_pct=outcome_row["actual_return_pct"],
        resolved_at=outcome_row["resolved_at"],
    )

    if not anonymous_user_id:
        return result

    with db.connection() as conn:
        pred_row = conn.execute(
            "SELECT id, direction, probability, reason, committed_at FROM fs_predictions "
            "WHERE case_id = ? AND anonymous_user_id = ?",
            (case_id, anonymous_user_id),
        ).fetchone()
    if pred_row is None:
        return result  # user never predicted on this case — outcome still shown, no evaluation

    result.your_prediction = PredictionOut(
        id=pred_row["id"],
        case_id=case_id,
        direction=pred_row["direction"],
        probability=pred_row["probability"],
        reason=pred_row["reason"],
        committed_at=pred_row["committed_at"],
    )

    binary_outcome = _binary_outcome(pred_row["direction"], outcome_row["actual_direction"])
    probability_error = (
        pred_row["probability"] - binary_outcome
    )  # SIGNED — raw data, no interpretation (Calibration Spec v1 §4)

    with db.connection() as conn:
        existing_eval = conn.execute(
            "SELECT direction_correct, binary_outcome, probability_error FROM fs_evaluations "
            "WHERE prediction_id = ?",
            (pred_row["id"],),
        ).fetchone()
        if existing_eval is None:
            now = datetime.now(UTC).isoformat()
            conn.execute(
                "INSERT INTO fs_evaluations (prediction_id, direction_correct, binary_outcome, "
                "probability_error, created_at) VALUES (?,?,?,?,?)",
                (pred_row["id"], binary_outcome, binary_outcome, probability_error, now),
            )
            direction_correct = bool(binary_outcome)
        else:
            direction_correct = bool(existing_eval["direction_correct"])
            binary_outcome = existing_eval["binary_outcome"]
            probability_error = existing_eval["probability_error"]

    result.evaluation = EvaluationOut(
        direction_correct=direction_correct,
        binary_outcome=binary_outcome,
        probability_error=probability_error,
    )
    return result
