from __future__ import annotations

import contextlib
import unittest
from unittest import mock

from services.erp import line_push_notification as notification


class _Cursor:
    def __init__(self, rows):
        self.rows = list(rows)
        self.calls = []

    def execute(self, sql, params=None):
        self.calls.append((sql, params))

    def fetchone(self):
        return self.rows.pop(0) if self.rows else None


def _cursor(rows):
    @contextlib.contextmanager
    def context():
        yield _Cursor(rows)

    return context


class ErpLinePushNotificationTests(unittest.TestCase):
    def test_cowork_success_includes_external_number_account_and_total(self):
        log = {
            "user_id": "user-1",
            "tenant_id": "tenant-1",
            "invoice_no": "HS6901-101",
            "total_amount": "6687.50",
            "request_body": {
                "source": "cowork_line",
                "payload": {"account_dir": r"\\Accserver\d$\ACCOUNT\70EXP\TEST"},
            },
            "response_body": '{"express_docnum":"HS681224-001"}',
            "endpoint_name": "Express",
            "adapter": "express",
            "endpoint_config": {},
            "bound_account_set": None,
        }
        with (
            mock.patch.object(
                notification.db, "get_cursor", _cursor([log, {"line_user_id": "U1"}])
            ),
            mock.patch.object(notification.line_client, "push_text", return_value=True) as push,
        ):
            sent = notification.notify_success("log-1")

        self.assertTrue(sent)
        line_user_id, message = push.call_args.args
        self.assertEqual(line_user_id, "U1")
        self.assertEqual(push.call_args.kwargs["channel"], "cowork")
        self.assertIn("HS6901-101", message)
        self.assertIn("HS681224-001", message)
        self.assertIn(r"\\Accserver\d$\ACCOUNT\70EXP\TEST", message)
        self.assertIn("฿6,687.50", message)

    def test_non_line_push_stays_silent(self):
        log = {
            "user_id": "user-1",
            "tenant_id": "tenant-1",
            "invoice_no": "INV-1",
            "total_amount": "1",
            "request_body": {"source": "main"},
            "response_body": "{}",
            "endpoint_name": "MR.ERP",
            "adapter": "mrerp",
            "endpoint_config": {},
            "bound_account_set": None,
        }
        with (
            mock.patch.object(notification.db, "get_cursor", _cursor([log])),
            mock.patch.object(notification.line_client, "push_text") as push,
        ):
            sent = notification.notify_success("log-2")

        self.assertFalse(sent)
        push.assert_not_called()


if __name__ == "__main__":
    unittest.main()
