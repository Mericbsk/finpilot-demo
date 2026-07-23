"""Long-running paper reconciliation worker entrypoint."""

from __future__ import annotations

import logging
import os
import time

from auth.database import get_database

from execution.models import ExecutionMode
from execution.reconciliation import ReconciliationWorker
from execution.repository import ExecutionRepository

logger = logging.getLogger(__name__)


def run_once() -> dict[str, int]:
    mode = ExecutionMode(os.getenv("FINPILOT_EXECUTION_MODE", "dry_run"))
    if mode != ExecutionMode.PAPER_EXECUTION:
        logger.info("Execution worker idle: mode=%s; paper_execution is required", mode.value)
        return {"checked": 0, "updated": 0, "unknown": 0}

    from broker import AlpacaBroker

    broker = AlpacaBroker()
    if not broker.is_available:
        raise RuntimeError("Paper Alpaca credentials are not configured")
    return ReconciliationWorker(ExecutionRepository(get_database()), broker).run_once()


def main() -> None:
    interval = max(5, int(os.getenv("FINPILOT_RECONCILE_INTERVAL_SECONDS", "60")))
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    logger.info("Paper execution reconciliation worker started; interval=%ss", interval)
    while True:
        try:
            logger.info("Reconciliation result: %s", run_once())
        except Exception:
            logger.exception("Reconciliation cycle failed")
        time.sleep(interval)


if __name__ == "__main__":
    main()
