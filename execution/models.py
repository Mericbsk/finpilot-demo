"""Typed values used by the paper execution gateway."""

from __future__ import annotations

from enum import StrEnum


class ExecutionMode(StrEnum):
    DRY_RUN = "dry_run"
    PAPER_SHADOW = "paper_shadow"
    PAPER_EXECUTION = "paper_execution"


class IntentStatus(StrEnum):
    CREATED = "created"
    RISK_REJECTED = "risk_rejected"
    RISK_APPROVED = "risk_approved"
    SUBMITTED = "submitted"
    ACCEPTED = "accepted"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    REJECTED = "rejected"
    CANCELED = "canceled"
    EXPIRED = "expired"
    UNKNOWN = "unknown"
    RECONCILED = "reconciled"
