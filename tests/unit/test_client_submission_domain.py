"""确认快照入队、精确投递与失败状态契约。"""

from __future__ import annotations

import contextlib
import unittest
from unittest import mock

from services.accounting_engagement.errors import WORKSPACE_MISMATCH, EngagementError
from services.client_submission import delivery, enqueue, worker
from services.client_submission.errors import (
    REVISION_CONFLICT,
    TARGET_MISMATCH,
    SubmissionError,
)


def engagement(status="active"):
    return {
        "id": "eng-1",
        "firm_tenant_id": "firm-1",
        "firm_workspace_client_id": 8,
        "merchant_tenant_id": "merchant-1",
        "merchant_workspace_client_id": 7,
        "status": status,
    }


def submission(**overrides):
    data = {
        "id": "sub-1",
        "engagement_id": "eng-1",
        "source_tenant_id": "merchant-1",
        "source_workspace_client_id": 7,
        "source_document_type": "purchase",
        "source_document_id": "doc-1",
        "source_revision": 1,
        "source_hash": "hash-1",
        "target_tenant_id": "firm-1",
        "target_workspace_client_id": 8,
        "snapshot_json": {
            "filename": "invoice.pdf",
            "fields": {
                "invoice_number": "INV-1",
                "date": "2026-08-27",
                "seller_name": "Vendor",
                "total_amount": "125.50",
                "items": [{"name": "Paper", "quantity": 1}],
            },
        },
        "status": "pending",
        "attempts": 0,
        "engagement_status": "active",
        "engagement_firm_tenant_id": "firm-1",
        "engagement_firm_workspace_client_id": 8,
        "engagement_merchant_tenant_id": "merchant-1",
        "engagement_merchant_workspace_client_id": 7,
    }
    data.update(overrides)
    return data


class EnqueueTests(unittest.TestCase):
    def test_no_active_or_suspended_relationship_is_zero_side_effect(self):
        with (
            mock.patch.object(enqueue.engagement_store, "get_open_for_merchant", return_value=None),
            mock.patch.object(enqueue.store, "create_pending") as create,
        ):
            result = enqueue.enqueue_confirmed_document(
                mock.Mock(),
                merchant_tenant_id="merchant-1",
                merchant_workspace_client_id=7,
                source_document_type="purchase",
                source_document_id="doc-1",
                source_revision=1,
                snapshot={"fields": {}},
            )
        self.assertIsNone(result)
        create.assert_not_called()

    def test_active_and_suspended_relationships_create_pending(self):
        for status in ("active", "suspended"):
            created = {"id": "sub-1", "source_hash": ""}

            def create_pending(*_args, **kwargs):
                created["source_hash"] = kwargs["source_hash"]
                return dict(created)

            with (
                self.subTest(status=status),
                mock.patch.object(
                    enqueue.engagement_store,
                    "get_open_for_merchant",
                    return_value=engagement(status),
                ),
                mock.patch.object(enqueue.store, "create_pending", side_effect=create_pending),
            ):
                result = enqueue.enqueue_confirmed_document(
                    mock.Mock(),
                    merchant_tenant_id="merchant-1",
                    merchant_workspace_client_id=7,
                    source_document_type="sales",
                    source_document_id="doc-1",
                    source_revision=1,
                    snapshot={"fields": {"total_amount": "10.00"}},
                )
            self.assertEqual(result["id"], "sub-1")

    def test_workspace_mismatch_is_rejected(self):
        with mock.patch.object(
            enqueue.engagement_store,
            "get_open_for_merchant",
            return_value=engagement(),
        ):
            with self.assertRaises(EngagementError) as error:
                enqueue.enqueue_confirmed_document(
                    mock.Mock(),
                    merchant_tenant_id="merchant-1",
                    merchant_workspace_client_id=99,
                    source_document_type="purchase",
                    source_document_id="doc-1",
                    source_revision=1,
                    snapshot={"fields": {}},
                )
        self.assertEqual(error.exception.code, WORKSPACE_MISMATCH)

    def test_same_revision_with_different_snapshot_is_explicit_conflict(self):
        with (
            mock.patch.object(
                enqueue.engagement_store,
                "get_open_for_merchant",
                return_value=engagement(),
            ),
            mock.patch.object(
                enqueue.store,
                "create_pending",
                return_value={"id": "sub-1", "source_hash": "different"},
            ),
        ):
            with self.assertRaises(SubmissionError) as error:
                enqueue.enqueue_confirmed_document(
                    mock.Mock(),
                    merchant_tenant_id="merchant-1",
                    merchant_workspace_client_id=7,
                    source_document_type="purchase",
                    source_document_id="doc-1",
                    source_revision=1,
                    snapshot={"fields": {"total_amount": 10}},
                )
        self.assertEqual(error.exception.code, REVISION_CONFLICT)


class Cursor:
    def __init__(self, rows):
        self.rows = list(rows)
        self.calls = []

    def execute(self, sql, params=None):
        self.calls.append((sql, params))

    def fetchone(self):
        return self.rows.pop(0) if self.rows else None


class DeliveryTests(unittest.TestCase):
    def test_delivery_writes_confirmed_snapshot_to_exact_cowork_workspace(self):
        cur = Cursor([{"user_id": "owner-1"}, {"id": "history-1"}])
        history_id = delivery.deliver_to_cowork(cur, submission())
        self.assertEqual(history_id, "history-1")
        target_sql, target_params = cur.calls[0]
        self.assertIn("accounting_firm_profiles", target_sql)
        self.assertEqual(target_params, ("firm-1", 8))
        insert_sql, insert_params = cur.calls[1]
        self.assertIn("INSERT INTO ocr_history", insert_sql)
        self.assertEqual(insert_params[1], "firm-1")
        self.assertEqual(insert_params[10], delivery.SOURCE)
        self.assertEqual(insert_params[11], "sub-1")
        self.assertEqual(insert_params[12], 8)

    def test_delivery_normalizes_thai_buddhist_invoice_date(self):
        row = submission()
        row["snapshot_json"]["fields"].update({"date_raw": "27/08/2569", "date": "2569-08-27"})
        cur = Cursor([{"user_id": "owner-1"}, {"id": "history-1"}])

        delivery.deliver_to_cowork(cur, row)

        _insert_sql, insert_params = cur.calls[1]
        self.assertEqual(insert_params[7], "2026-08-27")

    def test_changed_relationship_target_is_non_retryable_mismatch(self):
        with self.assertRaises(SubmissionError) as error:
            delivery.deliver_to_cowork(
                Cursor([]), submission(engagement_firm_workspace_client_id=9)
            )
        self.assertEqual(error.exception.code, TARGET_MISMATCH)


@contextlib.contextmanager
def cursor_cm(cur):
    yield cur


class WorkerTests(unittest.TestCase):
    def test_technical_failure_schedules_retry_and_mismatch_does_not(self):
        for raised, expected_retry in (
            (RuntimeError("network"), True),
            (SubmissionError(TARGET_MISMATCH), False),
        ):
            cur = object()
            with (
                self.subTest(error=type(raised).__name__),
                mock.patch.object(
                    worker.db,
                    "get_cursor_rls",
                    side_effect=[cursor_cm(cur), cursor_cm(cur)],
                ),
                mock.patch.object(worker.store, "get_for_delivery", return_value=submission()),
                mock.patch.object(worker.delivery, "deliver_to_cowork", side_effect=raised),
                mock.patch.object(worker.store, "mark_failed") as mark_failed,
            ):
                self.assertFalse(worker.deliver_one("sub-1"))
            delay = mark_failed.call_args.kwargs["retry_delay_seconds"]
            self.assertEqual(delay is not None, expected_retry)
            expected_error = TARGET_MISMATCH if not expected_retry else "ERR_SUBMISSION_DELIVERY"
            self.assertEqual(mark_failed.call_args.kwargs["error"], expected_error)


if __name__ == "__main__":
    unittest.main()
