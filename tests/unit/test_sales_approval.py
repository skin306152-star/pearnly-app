# -*- coding: utf-8 -*-
"""开具审批工作流守门(状态迁移闸 · 不连库 · docs/16 §F)。"""

import unittest
from datetime import date

from services.sales import approval


class FakeCursor:
    """按配置的 row 应答 SELECT;UPDATE/DELETE 记录但不返回。"""

    def __init__(self, row):
        self._row = row
        self._last = ""
        self.writes = []

    def execute(self, sql, params=None):
        self._last = sql
        if sql.lstrip().startswith(("UPDATE", "DELETE", "INSERT")):
            self.writes.append(sql)

    def fetchone(self):
        return self._row if "SELECT" in self._last else None


class SubmitTests(unittest.TestCase):
    def test_not_found(self):
        self.assertEqual(
            approval.submit_for_approval(FakeCursor(None), tenant_id="t", doc_id="d"), "not_found"
        )

    def test_issued_cannot_submit(self):
        cur = FakeCursor({"status": "issued"})
        self.assertEqual(approval.submit_for_approval(cur, tenant_id="t", doc_id="d"), "not_draft")

    def test_draft_submits(self):
        cur = FakeCursor({"status": "draft"})
        self.assertIsNone(approval.submit_for_approval(cur, tenant_id="t", doc_id="d"))
        self.assertTrue(cur.writes)

    def test_rejected_can_resubmit(self):
        cur = FakeCursor({"status": "rejected"})
        self.assertIsNone(approval.submit_for_approval(cur, tenant_id="t", doc_id="d"))


class ApproveTests(unittest.TestCase):
    def test_not_found(self):
        _, err = approval.approve(
            FakeCursor(None),
            tenant_id="t",
            doc_id="d",
            approver="u",
            prefix="INV",
            reset="yearly",
            on=date(2026, 6, 6),
        )
        self.assertEqual(err, "not_found")

    def test_non_pending_rejected(self):
        cur = FakeCursor({"status": "draft", "doc_type": "tax_invoice"})
        _, err = approval.approve(
            cur,
            tenant_id="t",
            doc_id="d",
            approver="u",
            prefix="INV",
            reset="yearly",
            on=date(2026, 6, 6),
        )
        self.assertEqual(err, "not_pending")


class RejectTests(unittest.TestCase):
    def test_not_found(self):
        self.assertEqual(approval.reject(FakeCursor(None), tenant_id="t", doc_id="d"), "not_found")

    def test_non_pending_rejected(self):
        cur = FakeCursor({"status": "draft"})
        self.assertEqual(approval.reject(cur, tenant_id="t", doc_id="d"), "not_pending")

    def test_pending_rejects_with_reason(self):
        cur = FakeCursor({"status": "pending_approval"})
        self.assertIsNone(approval.reject(cur, tenant_id="t", doc_id="d", reason="bad"))
        self.assertTrue(cur.writes)


if __name__ == "__main__":
    unittest.main()
