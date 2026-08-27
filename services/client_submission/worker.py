"""client_submissions 的短事务投递与重试 tick。"""

from __future__ import annotations

import logging

from core import db
from services.client_submission import delivery, store
from services.client_submission.errors import DELIVERY_FAILED, SubmissionError

logger = logging.getLogger(__name__)

_RETRY_DELAYS = (30, 120, 600, 1800)


def run_tick(limit: int = 20) -> dict:
    with db.get_cursor_rls(bypass=True, commit=True) as cur:
        superseded = store.supersede_ended(cur)
        due_ids = store.list_due_ids(cur, limit=limit)

    delivered = 0
    failed = 0
    for submission_id in due_ids:
        if deliver_one(submission_id):
            delivered += 1
        else:
            failed += 1
    return {"due": len(due_ids), "delivered": delivered, "failed": failed, "superseded": superseded}


def deliver_one(submission_id: str) -> bool:
    try:
        with db.get_cursor_rls(bypass=True, commit=True) as cur:
            submission = store.get_for_delivery(cur, submission_id=submission_id)
            if not submission or submission.get("status") not in {"pending", "failed"}:
                return False
            history_id = delivery.deliver_to_cowork(cur, submission)
            store.mark_delivered(
                cur,
                submission_id=submission_id,
                cowork_history_id=history_id,
            )
        return True
    except SubmissionError as error:
        _record_failure(submission_id, error.code, retry=False)
        return False
    except Exception as error:  # noqa: BLE001 - worker 必须把技术失败留在 outbox，不炸整个 tick
        logger.warning("client submission delivery failed id=%s: %s", submission_id, error)
        _record_failure(submission_id, DELIVERY_FAILED, retry=True)
        return False


def _record_failure(submission_id: str, error: str, *, retry: bool) -> None:
    with db.get_cursor_rls(bypass=True, commit=True) as cur:
        submission = store.get_for_delivery(cur, submission_id=submission_id)
        if not submission or submission.get("status") not in {"pending", "failed"}:
            return
        attempts = int(submission.get("attempts") or 0)
        delay = _RETRY_DELAYS[min(attempts, len(_RETRY_DELAYS) - 1)] if retry else None
        store.mark_failed(
            cur,
            submission_id=submission_id,
            error=error,
            retry_delay_seconds=delay,
        )
