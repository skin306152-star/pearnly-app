# -*- coding: utf-8 -*-
"""汇总表导入 → intake_bridge 当场转正式单据 · 真库集成测试(追加任务 G 的验收点)。

commit_rows 现在不只是写 ocr_history:整批写完后当场调 services.intake_bridge.convert
(见 services/summary_import/commit.py 顶部 2026-08-07 拍板改向说明)。这里验证的正是那条
新接线,方向判定/幂等/防重等 intake_bridge 自身口径已由 test_intake_bridge_real.py 覆盖,
不重复断。

断言:
  ① commit 一批(含一条销项行)→ sales_documents 落 issued
  ② convert 后 services/stockcard/report.summary 出数
  ③ 二次 commit 同一批(内容相同的行,各自新建 ocr_history)→ 不重复建单
    (第二条 ocr_history 转换时撞 doc_number 唯一索引 → skipped=duplicate,sales_documents
    仍只有一行,不是"发现同批就不建"——ocr_history 层没有查重,查重发生在正式单据层)

跑法(要真库;CI 不跑 tests/integration):
    set PEARNLY_INTEGRATION_DB=1
    set DATABASE_URL=postgresql://pearnly:pearnly_local_dev@127.0.0.1:5432/pearnly
    set PGSSLMODE=disable
    python -m unittest tests.integration.test_summary_import_bridge_real -v

日期用 2027 年底(理由同 test_intake_bridge_real.py:normalize_ocr_fields 的未来日期合理窗
挡不住太远的年份,2031 会被当模型幻觉清空)。
"""

from __future__ import annotations

import os
import unittest
from datetime import date

from tests.integration._helpers import require_db

_USER = os.environ.get("PEARNLY_LOCAL_E2E_USER") or "stw_e2e"

_OWN_TAX = "0105561234563"
_CP_TAX = "0107537000521"
_PRODUCT_NAME = "SUMMARYBRIDGE_TEST_WIDGET"
_DOC_NO = "SUMMARYBRIDGE-SALE-0001"


def _row(index: int) -> dict:
    return {
        "row_index": index,
        "fields": {
            "document_type": "tax_invoice",
            "invoice_number": _DOC_NO,
            "date": "2027-12-15",
            "seller_name": "SUMMARYBRIDGE_TEST_WS",
            "seller_tax": _OWN_TAX,
            "buyer_name": "Summary Batch Customer Co",
            "buyer_tax": _CP_TAX,
            "buyer_addr": "1 Summary Import Road",
            "subtotal": "80.00",
            "vat": "5.60",
            "total_amount": "85.60",
            "items": [{"name": _PRODUCT_NAME, "qty": "4", "price": "20"}],
        },
    }


class SummaryImportBridgeRealTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        require_db()
        from core import db
        from services.intake_bridge.schema import ensure_intake_bridge_schema
        from services.stockcard import report as report_svc
        from services.summary_import import commit as commit_svc

        cls.db, cls.commit_svc, cls.report = db, commit_svc, report_svc
        cls._history_ids: list = []
        cls._ws_ids: list = []
        ensure_intake_bridge_schema()

        with db.get_cursor(commit=True) as cur:
            cur.execute("SELECT id, tenant_id FROM users WHERE username = %s", (_USER,))
            row = cur.fetchone()
            if not row:
                raise unittest.SkipTest(f"本机开发库没有测试号 {_USER},建不了套账夹具")
            cls.tenant_id = str(row["tenant_id"])
            cls.user_id = str(row["id"])
            cur.execute(
                "INSERT INTO workspace_clients (tenant_id, user_id, name, tax_id) "
                "VALUES (%s,%s,%s,%s) RETURNING id",
                (cls.tenant_id, cls.user_id, "SUMMARYBRIDGE_TEST_WS", _OWN_TAX),
            )
            cls.ws_a = int(cur.fetchone()["id"])
            cls._ws_ids.append(cls.ws_a)

    @classmethod
    def tearDownClass(cls):
        if not hasattr(cls, "db"):
            return
        with cls.db.get_cursor(commit=True) as cur:
            cur.execute(
                "DELETE FROM sales_documents WHERE tenant_id=%s AND doc_number=%s",
                (cls.tenant_id, _DOC_NO),
            )
            cur.execute(
                "DELETE FROM ocr_history WHERE tenant_id=%s AND id = ANY(%s::uuid[])",
                (cls.tenant_id, cls._history_ids),
            )
            for ws_id in cls._ws_ids:
                cur.execute(
                    "DELETE FROM workspace_clients WHERE tenant_id=%s AND id=%s",
                    (cls.tenant_id, ws_id),
                )

    def _commit_one_row(self) -> dict:
        out = self.commit_svc.commit_rows(
            tenant_id=self.tenant_id,
            workspace_client_id=self.ws_a,
            created_by=self.user_id,
            rows=[_row(0)],
            batch_ref="intakebridge-summary-test",
        )
        for r in out["rows"]:
            if r.get("ocr_history_id"):
                self._history_ids.append(r["ocr_history_id"])
        return out

    def test_commit_books_sales_document_and_reports_then_second_commit_does_not_duplicate(self):
        first = self._commit_one_row()
        self.assertEqual(first["rows"][0]["status"], "created")
        self.assertEqual(len(first["converted"]), 1)
        self.assertEqual(first["converted"][0]["doc_type"], "sales")
        self.assertEqual(first["skipped"], [])

        with self.db.get_cursor() as cur:
            cur.execute(
                "SELECT status FROM sales_documents WHERE tenant_id=%s AND doc_number=%s",
                (self.tenant_id, _DOC_NO),
            )
            rows = cur.fetchall()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["status"], "issued")

        with self.db.get_cursor() as cur:
            summary = self.report.summary(
                cur,
                tenant_id=self.tenant_id,
                workspace_client_id=self.ws_a,
                date_from=date(2027, 12, 1),
                date_to=date(2027, 12, 31),
            )
        matches = [p for p in summary["products"] if _PRODUCT_NAME.lower() in p["name"].lower()]
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["out_qty"], "4.000")

        # ③ 二次 commit 同一批内容:新写一条 ocr_history(commit 层没有查重),但撞
        # sales_documents 的票号唯一索引 → 正式单据不重复建。
        second = self._commit_one_row()
        self.assertEqual(second["rows"][0]["status"], "created")  # ocr_history 照常写成
        self.assertEqual(second["converted"], [])
        self.assertEqual(len(second["skipped"]), 1)
        self.assertEqual(second["skipped"][0]["reason"], "duplicate")

        with self.db.get_cursor() as cur:
            cur.execute(
                "SELECT count(*) AS n FROM sales_documents WHERE tenant_id=%s AND doc_number=%s",
                (self.tenant_id, _DOC_NO),
            )
            self.assertEqual(cur.fetchone()["n"], 1)


if __name__ == "__main__":
    unittest.main()
