# -*- coding: utf-8 -*-
"""销项 PO-5 · 红冲/补开守门测试(引用原单 + 自身连号 + 状态校验 · 不连库)。"""

import unittest
from datetime import date
from decimal import Decimal

from services.sales import credit_note


class NoteCursor:
    """模拟原单状态查询 + 取号 + 插入,记录关键调用。"""

    def __init__(self, original_status, seller_ws=None):
        self.original_status = original_status
        self.seller_ws = seller_ws
        self.seq = {}
        self._last = None
        self.inserted_select_from_original = False
        self.note_doc_type = None
        self.inserted_seller_ws = None  # PO-7b:红冲单是否继承原单卖方主体

    def execute(self, sql, params=None):
        if sql.startswith("SELECT status, price_includes_vat") and "sales_documents" in sql:
            self._last = (
                None
                if self.original_status is None
                else {
                    "status": self.original_status,
                    "price_includes_vat": False,
                    "seller_workspace_client_id": self.seller_ws,
                }
            )
        elif sql.startswith("INSERT INTO document_number_sequences"):
            # 键 = 除末位 next_number 外的列(4 列旧键 / 5 列含主体键都适配)
            self.seq.setdefault(tuple(params[:-1]), params[-1])
            self.note_doc_type = "credit_note" if "credit_note" in params else params[1]
            self._last = None
        elif sql.startswith("SELECT next_number"):
            self._last = {"next_number": self.seq.get(tuple(params), 1)}
        elif sql.startswith("UPDATE document_number_sequences"):
            k = tuple(params)
            self.seq[k] = self.seq.get(k, 1) + 1
            self._last = None
        elif sql.startswith("INSERT INTO sales_documents"):
            # 红冲单从原单 SELECT 派生(继承 client/currency + 引用原单 id)
            self.inserted_select_from_original = "FROM sales_documents" in sql
            if "seller_workspace_client_id" in sql:
                self.inserted_seller_ws = self.seller_ws
            self._last = {"id": "note-1"}
        elif sql.startswith("SELECT") and "FROM sales_documents WHERE tenant_id" in sql:
            self._last = {
                "id": "note-1",
                "doc_type": self.note_doc_type,
                "doc_number": "CN2026-00001",
            }
        else:
            self._last = None

    def fetchone(self):
        return self._last

    def fetchall(self):
        return []


_LINES = [{"description": "退货", "qty": 1, "unit_price": "50"}]


class CreateNoteTests(unittest.TestCase):
    def test_bad_note_type(self):
        note, err = credit_note.create_note(
            NoteCursor("issued"),
            tenant_id="t",
            created_by=None,
            original_id="o",
            note_type="refund",
            reason=None,
            lines=_LINES,
            vat_rate=7,
            wht_rate=0,
            prefix=None,
            reset="yearly",
            on=date(2026, 6, 6),
        )
        self.assertEqual(err, "bad_note_type")

    def test_original_must_exist(self):
        _, err = credit_note.create_note(
            NoteCursor(None),
            tenant_id="t",
            created_by=None,
            original_id="o",
            note_type="credit_note",
            reason=None,
            lines=_LINES,
            vat_rate=7,
            wht_rate=0,
            prefix=None,
            reset="yearly",
            on=date(2026, 6, 6),
        )
        self.assertEqual(err, "original_not_found")

    def test_original_must_be_issued(self):
        for bad in ("draft", "void"):
            _, err = credit_note.create_note(
                NoteCursor(bad),
                tenant_id="t",
                created_by=None,
                original_id="o",
                note_type="credit_note",
                reason="x",
                lines=_LINES,
                vat_rate=7,
                wht_rate=0,
                prefix=None,
                reset="yearly",
                on=date(2026, 6, 6),
            )
            self.assertEqual(err, "original_not_issued")

    def test_credit_note_references_original_and_numbers_itself(self):
        cur = NoteCursor("issued")
        note, err = credit_note.create_note(
            cur,
            tenant_id="t",
            created_by="u",
            original_id="o",
            note_type="credit_note",
            reason="退货",
            lines=_LINES,
            vat_rate=7,
            wht_rate=0,
            prefix=None,
            reset="yearly",
            on=date(2026, 6, 6),
        )
        self.assertIsNone(err)
        self.assertTrue(cur.inserted_select_from_original, "红冲单应从原单派生并引用其 id")
        self.assertEqual(cur.note_doc_type, "credit_note", "取号序列按 note 类型独立")
        self.assertEqual(note["doc_number"], "CN2026-00001")

    def test_note_inherits_seller_workspace(self):
        # PO-7b:红冲/补开继承原单卖方主体 → 同主体号段 + 不留 NULL 跨套账泄漏。
        cur = NoteCursor("issued", seller_ws=77)
        _, err = credit_note.create_note(
            cur,
            tenant_id="t",
            created_by="u",
            original_id="o",
            note_type="credit_note",
            reason="退货",
            lines=_LINES,
            vat_rate=7,
            wht_rate=0,
            prefix=None,
            reset="yearly",
            on=date(2026, 6, 6),
        )
        self.assertIsNone(err)
        self.assertEqual(cur.inserted_seller_ws, 77)

    def test_note_prefix_defaults_by_type(self):
        self.assertEqual(credit_note._NOTE_PREFIX["credit_note"], "CN")
        self.assertEqual(credit_note._NOTE_PREFIX["debit_note"], "DN")


if __name__ == "__main__":
    unittest.main()
