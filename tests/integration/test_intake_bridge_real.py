# -*- coding: utf-8 -*-
"""OCR 确认→正式单据转换桥 · 真库集成测试(照 test_stockcard_report.py 连库范式)。

不走 HTTP:鉴权/RLS 已由别的闸锁住,这里只验 services/intake_bridge 与真 purchase_docs/
sales_documents/purchase_lines/sales_document_lines/workspace_clients 的 SQL 交互 ——
本桥存在的意义是让确认后的票能进商品收发存报表,所以①②③④之外必须验⑤真出数。

种一条销项 history(带 items)+ 一条进项 history,直接调 convert_histories 断言:
  ① sales_documents 落 issued + seller_workspace_client_id + 票面号
  ② purchase_docs 落 posted
  ③ 重复 convert 同一批 history_ids → 全部 skipped=already_converted(幂等)
  ④ 另一张税号/票号/总额全同的进项票撞 dedupe_key → skipped=duplicate(不是 error)
  ⑤ convert 后 services/stockcard/report.summary 里出现该商品且进/销数量对得上
    (这是本桥存在的意义:确认完≠过账完的断层,必须真出数才算补上)

跑法(要真库;CI 不跑 tests/integration):
    set PEARNLY_INTEGRATION_DB=1
    set DATABASE_URL=postgresql://pearnly:pearnly_local_dev@127.0.0.1:5432/pearnly
    set PGSSLMODE=disable
    python -m unittest tests.integration.test_intake_bridge_real -v

账号复用本机开发库现成的 stw_e2e(同 test_stockcard_report.py)。日期不能像 test_stockcard_
report.py 那样选 2031 年:那份是绕过应用层直接 SQL 插入 purchase_docs,本测试走的是真实
build_draft_from_invoice → normalize_ocr_fields 全链路,会撞 ocr_corrections._implausible_
doc_date 的合理窗(2000-01-01 ~ 明年末)把"未来太远"的日期当模型幻觉清空成 ''(doc_date
变 NULL,报表直接看不见这行,曾在此踩过一次坑)。改用窗内但仍是未来、真实业务数据摸不到的
2027 年底 + 高辨识度描述串,双重避免撞到真实数据。
"""

from __future__ import annotations

import os
import unittest
from datetime import date

from tests.integration._helpers import require_db

_USER = os.environ.get("PEARNLY_LOCAL_E2E_USER") or "stw_e2e"

_OWN_TAX = "0105561234563"  # 账套主体自家税号(与 test_stockcard_report.py 里的样例同款式)
_CP_TAX = "0107537000521"  # 对手方税号

_PRODUCT_NAME = "INTAKEBRIDGE_TEST_WIDGET"
_SALE_DOC_NO = "INTAKEBRIDGE-SALE-0001"
_DUP_DOC_NO = "INTAKEBRIDGE-PURCHASE-DUP"


class IntakeBridgeRealTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        require_db()
        from core import db
        from services.intake_bridge import convert as convert_svc
        from services.intake_bridge.schema import ensure_intake_bridge_schema
        from services.stockcard import report as report_svc

        cls.db, cls.convert, cls.report = db, convert_svc, report_svc
        cls._history_ids: list = []
        cls._purchase_doc_ids: list = []
        cls._sales_doc_ids: list = []
        cls._ws_ids: list = []

        # dual-run schema 幂等自愈(本机开发库可能还没跑过 alembic 0098)。
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
                (cls.tenant_id, cls.user_id, "INTAKEBRIDGE_TEST_WS", _OWN_TAX),
            )
            cls.ws_a = int(cur.fetchone()["id"])
            cls._ws_ids.append(cls.ws_a)

        cls.sale_history_id = cls._insert_history(
            fields={
                "document_type": "tax_invoice",
                "invoice_number": _SALE_DOC_NO,
                "date": "2027-12-25",
                "seller_name": "INTAKEBRIDGE_TEST_WS",
                "seller_tax": _OWN_TAX,
                "buyer_name": "Retail Customer Co Ltd",
                "buyer_tax": _CP_TAX,
                "buyer_addr": "99 Test Address Bangkok",
                "subtotal": "60.00",
                "vat": "4.20",
                "total_amount": "64.20",
                "items": [{"name": _PRODUCT_NAME, "qty": "3", "price": "20"}],
            }
        )
        cls.purchase_history_id = cls._insert_history(
            fields={
                "document_type": "tax_invoice",
                "invoice_number": "INTAKEBRIDGE-PURCHASE-0001",
                "date": "2027-12-20",
                "seller_name": "Test Supplier Co Ltd",
                "seller_tax": _CP_TAX,
                "buyer_name": "INTAKEBRIDGE_TEST_WS",
                "buyer_tax": _OWN_TAX,
                "subtotal": "200.00",
                "vat": "14.00",
                "total_amount": "214.00",
                "items": [{"name": _PRODUCT_NAME, "qty": "10", "price": "20"}],
            }
        )
        # ④ dedupe:与另一张(还没转换过的)进项票税号/票号/总额全同,撞 create_doc 的 dedupe_key。
        cls.dup_history_id = cls._insert_history(
            fields={
                "document_type": "tax_invoice",
                "invoice_number": _DUP_DOC_NO,
                "date": "2027-12-21",
                "seller_name": "Test Supplier Co Ltd",
                "seller_tax": _CP_TAX,
                "buyer_name": "INTAKEBRIDGE_TEST_WS",
                "buyer_tax": _OWN_TAX,
                "subtotal": "100.00",
                "vat": "7.00",
                "total_amount": "107.00",
                "items": [{"name": _PRODUCT_NAME, "qty": "5", "price": "20"}],
            }
        )
        cls.dup_history_id_2 = cls._insert_history(
            fields={
                "document_type": "tax_invoice",
                "invoice_number": _DUP_DOC_NO,  # 同票号
                "date": "2027-12-21",
                "seller_name": "Test Supplier Co Ltd",
                "seller_tax": _CP_TAX,  # 同税号
                "buyer_name": "INTAKEBRIDGE_TEST_WS",
                "buyer_tax": _OWN_TAX,
                "subtotal": "100.00",
                "vat": "7.00",
                "total_amount": "107.00",  # 同总额 → dedupe_key 相同
                "items": [{"name": _PRODUCT_NAME, "qty": "5", "price": "20"}],
            }
        )

    @classmethod
    def _insert_history(cls, *, fields: dict) -> str:
        new_id = cls.db.insert_ocr_history(
            user_id=cls.user_id,
            filename="intake-bridge-fixture.pdf",
            page_count=1,
            pages=[{"fields": fields, "is_copy": False, "is_duplicate": False}],
            confidence="high",
            elapsed_ms=0,
            source="manual",
            tenant_id=cls.tenant_id,
            workspace_client_id=cls.ws_a,
        )
        assert new_id, "insert_ocr_history 失败,夹具建不起来"
        cls._history_ids.append(new_id)
        return new_id

    @classmethod
    def tearDownClass(cls):
        if not hasattr(cls, "db"):
            return
        with cls.db.get_cursor(commit=True) as cur:
            cur.execute(
                "DELETE FROM purchase_docs WHERE tenant_id=%s AND ocr_history_id = ANY(%s::uuid[])",
                (cls.tenant_id, cls._history_ids),
            )
            cur.execute(
                "DELETE FROM sales_documents WHERE tenant_id=%s AND ocr_history_id = ANY(%s::uuid[])",
                (cls.tenant_id, cls._history_ids),
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

    def _convert(self, history_ids: list) -> dict:
        with self.db.get_cursor(commit=True) as cur:
            return self.convert.convert_histories(
                cur, tenant_id=self.tenant_id, user_id=self.user_id, history_ids=history_ids
            )

    def test_full_batch_books_sale_and_purchase_then_is_idempotent_and_dedupes(self):
        # ①② 首次转换:销项 issued、进项 posted。
        out = self._convert([self.sale_history_id, self.purchase_history_id])
        self.assertEqual(out["skipped"], [])
        by_type = {c["doc_type"]: c for c in out["converted"]}
        self.assertIn("sales", by_type)
        self.assertIn("purchase", by_type)

        with self.db.get_cursor() as cur:
            cur.execute(
                "SELECT status, seller_workspace_client_id, doc_number FROM sales_documents "
                "WHERE tenant_id=%s AND id=%s",
                (self.tenant_id, by_type["sales"]["doc_id"]),
            )
            sale_row = cur.fetchone()
        self.assertEqual(sale_row["status"], "issued")
        self.assertEqual(sale_row["seller_workspace_client_id"], self.ws_a)
        self.assertEqual(sale_row["doc_number"], _SALE_DOC_NO)

        with self.db.get_cursor() as cur:
            cur.execute(
                "SELECT status FROM purchase_docs WHERE tenant_id=%s AND id=%s",
                (self.tenant_id, by_type["purchase"]["doc_id"]),
            )
            purchase_row = cur.fetchone()
        self.assertEqual(purchase_row["status"], "posted")

        # ③ 幂等:同一批 history_ids 再转一次,全部 already_converted。
        again = self._convert([self.sale_history_id, self.purchase_history_id])
        self.assertEqual(again["converted"], [])
        self.assertEqual(
            {s["reason"] for s in again["skipped"]},
            {"already_converted"},
        )

        # ④ dedupe:先转 dup_history_id(建成),再转 dup_history_id_2(税号/票号/总额全同)→ duplicate。
        first_dup = self._convert([self.dup_history_id])
        self.assertEqual(first_dup["skipped"], [])
        second_dup = self._convert([self.dup_history_id_2])
        self.assertEqual(second_dup["converted"], [])
        self.assertEqual(
            second_dup["skipped"], [{"history_id": self.dup_history_id_2, "reason": "duplicate"}]
        )

        # ⑤ 报表真出数:同一商品,进项 10+5=15、销项 3,数量对得上(本桥存在的意义)。
        with self.db.get_cursor() as cur:
            summary = self.report.summary(
                cur,
                tenant_id=self.tenant_id,
                workspace_client_id=self.ws_a,
                date_from=date(2027, 12, 1),
                date_to=date(2027, 12, 31),
            )
        rows = [p for p in summary["products"] if _PRODUCT_NAME.lower() in p["name"].lower()]
        self.assertEqual(len(rows), 1, f"报表里没找到该商品(或被拆成多组):{summary['products']}")
        row = rows[0]
        self.assertEqual(row["in_qty"], "15.000")
        self.assertEqual(row["out_qty"], "3.000")


if __name__ == "__main__":
    unittest.main()
