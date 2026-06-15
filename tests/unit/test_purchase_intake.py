# -*- coding: utf-8 -*-
"""智能分流纯逻辑单测(P0a 方向判定 + 草稿构建 + 费用归类 · docs/purchasing/02 §0)。

判方向是进项模块灵魂:买方=本主体→进项,卖方=本主体→销项,非发票→inbox。税号比对要扛
空格/连字符差异。草稿从 OCR items 取行、无 items 单行兜底。费用文本取末位金额 + 关键词归类。
"""

import unittest
from decimal import Decimal

from services.purchase import intake as ik

MY = "1234567890123"


class JudgeDirectionTests(unittest.TestCase):
    def test_buyer_is_me_with_vat_to_purchase(self):
        f = {
            "document_type": "tax_invoice",
            "buyer_tax": MY,
            "seller_tax": "9999999999999",
            "vat": "70",
        }
        self.assertEqual(ik.judge_direction(f, my_tax_id=MY), ("purchase_invoice", "purchase"))

    def test_seller_is_me_to_sales(self):
        f = {
            "document_type": "tax_invoice",
            "buyer_tax": "9999999999999",
            "seller_tax": MY,
            "vat": "70",
        }
        self.assertEqual(ik.judge_direction(f, my_tax_id=MY), ("sales", "sales"))

    def test_not_invoice_to_inbox(self):
        f = {"is_not_invoice": True, "document_type": "other"}
        self.assertEqual(ik.judge_direction(f, my_tax_id=MY), ("unknown", "inbox"))

    def test_neither_matches_with_vat_defaults_purchase(self):
        # 商户拍收到的票,双方税号都没对上本主体 → 默认进项。
        f = {
            "document_type": "tax_invoice",
            "buyer_tax": "",
            "seller_tax": "8888888888888",
            "vat": "70",
        }
        self.assertEqual(ik.judge_direction(f, my_tax_id=MY), ("purchase_invoice", "purchase"))

    def test_receipt_no_vat_to_expense(self):
        f = {"document_type": "receipt", "buyer_tax": "", "seller_tax": "", "vat": "0"}
        self.assertEqual(ik.judge_direction(f, my_tax_id=MY), ("expense", "expense"))

    def test_tax_match_ignores_spacing(self):
        f = {
            "document_type": "tax_invoice",
            "buyer_tax": "1-2345 67890123",
            "seller_tax": "x",
            "vat": "7",
        }
        self.assertEqual(ik.judge_direction(f, my_tax_id=MY)[1], "purchase")


class BuildDraftTests(unittest.TestCase):
    def test_items_become_lines(self):
        f = {
            "document_type": "tax_invoice",
            "seller_name": "ACME",
            "seller_tax": MY,
            "vat": "70",
            "invoice_number": "INV-1",
            "items": [{"name": "ของ", "qty": "2", "price": "50"}],
        }
        d = ik.build_draft_from_invoice(f, kind="purchase_invoice")
        self.assertEqual(d["supplier"]["name"], "ACME")
        self.assertEqual(d["doc_no"], "INV-1")
        self.assertEqual(len(d["lines"]), 1)
        self.assertEqual(d["lines"][0]["vat_rate"], 7)

    def test_no_items_fallback_single_line(self):
        f = {
            "document_type": "tax_invoice",
            "seller_name": "X",
            "vat": "7",
            "subtotal": "1000",
            "items": [],
        }
        d = ik.build_draft_from_invoice(f, kind="purchase_invoice")
        self.assertEqual(len(d["lines"]), 1)
        self.assertEqual(d["lines"][0]["unit_price"], "1000")


class ClassifyExpenseTests(unittest.TestCase):
    TREE = [
        {
            "id": "p1",
            "name": "ค่าเดินทางและขนส่ง",
            "children": [{"id": "c1", "name": "ค่าแท็กซี่/แกร็บ"}],
        },
        {"id": "p2", "name": "ค่าเช่า", "children": []},
    ]

    def test_amount_is_last_number(self):
        r = ik.classify_expense_text("แท็กซี่ 50", self.TREE)
        self.assertEqual(r["amount"], Decimal("50"))

    def test_keyword_maps_to_subcategory(self):
        r = ik.classify_expense_text("นั่งแท็กซี่ไปประชุม 120", self.TREE)
        self.assertEqual((r["category_id"], r["subcategory_id"]), ("p1", "c1"))

    def test_parent_name_match(self):
        r = ik.classify_expense_text("ค่าเช่า ออฟฟิศ 8000", self.TREE)
        self.assertEqual((r["category_id"], r["subcategory_id"]), ("p2", None))

    def test_no_match_leaves_blank(self):
        r = ik.classify_expense_text("อะไรก็ไม่รู้ 30", self.TREE)
        self.assertEqual((r["category_id"], r["subcategory_id"]), (None, None))
        self.assertEqual(r["amount"], Decimal("30"))


class _FakeCur:
    def execute(self, *a, **k):
        return None

    def fetchone(self):
        return {"tax_id": "1234567890123"}


class _FakeCM:
    def __enter__(self):
        return _FakeCur()

    def __exit__(self, *a):
        return False


class LineDispatchFirmSafetyTests(unittest.TestCase):
    """LINE 底线(铁律 #26):事务所 firm / 未选业态 → route_line_image 不落库、返回 False。"""

    def _run(self, business_type, expense_on=True):
        from unittest import mock

        from core import db
        from services.modules import store as mstore

        stashed = []
        with (
            mock.patch.object(db, "get_cursor_rls", return_value=_FakeCM()),
            mock.patch.object(mstore, "get_business_type", return_value=business_type),
            mock.patch.object(mstore, "is_enabled", return_value=expense_on),
            mock.patch.object(ik, "_stash_inbox", side_effect=lambda *a, **k: stashed.append(1)),
        ):
            ret = ik.route_line_image(
                tenant_id="t",
                workspace_client_id=1,
                fields={"document_type": "tax_invoice", "vat": "7"},
                confidence="auto",
            )
        return ret, stashed

    # 2026-06-15 Zihao 拍板:统一智能通道·不按业态分。开 expense 即落采购(含 firm/未onboard)。
    def test_firm_routes_when_expense_on(self):
        ret, stashed = self._run("firm")
        self.assertTrue(ret)
        self.assertEqual(stashed, [1])  # 事务所也落采购(统一通道)

    def test_unonboarded_routes_when_expense_on(self):
        ret, stashed = self._run(None)
        self.assertTrue(ret)
        self.assertEqual(stashed, [1])

    def test_expense_off_is_noop(self):
        ret, stashed = self._run("retail", expense_on=False)
        self.assertFalse(ret)
        self.assertEqual(stashed, [])

    def test_merchant_stashes(self):
        ret, stashed = self._run("retail", expense_on=True)
        self.assertTrue(ret)
        self.assertEqual(stashed, [1])  # 商户租户 → 落采购待办


class ResolveImageIntakeTests(unittest.TestCase):
    """F5/F12:糊图(抽取过空 ฿0)/ 低置信 → 落 inbox,绝不返回可保存的 ฿0 草稿。"""

    def _resolve(self, fields, confidence):
        from unittest import mock

        stashed = []
        with mock.patch.object(ik, "_stash_inbox", side_effect=lambda *a, **k: stashed.append(k)):
            data = ik.resolve_image_intake(
                _FakeCur(),
                tenant_id="t",
                workspace_client_id=1,
                fields=fields,
                confidence=confidence,
                settings={},
            )
        return data, stashed

    def test_zero_amount_goes_inbox(self):
        # 买方=我 + 有 VAT 标志 → 方向 purchase,但抽取金额为 0 → 不进表单,落待归类。
        f = {
            "document_type": "tax_invoice",
            "buyer_tax": MY,
            "vat": "7",
            "subtotal": "0",
            "items": [],
        }
        data, stashed = self._resolve(f, "high")
        self.assertEqual(data["route"], "inbox")
        self.assertIsNone(data["draft"])
        self.assertEqual(len(stashed), 1)

    def test_low_confidence_goes_inbox(self):
        f = {
            "document_type": "tax_invoice",
            "buyer_tax": MY,
            "vat": "7",
            "subtotal": "1000",
            "items": [{"name": "x", "qty": "1", "price": "1000"}],
        }
        data, stashed = self._resolve(f, "needs_review")
        self.assertEqual(data["route"], "inbox")
        self.assertIsNone(data["draft"])

    def test_sales_route_no_stash(self):
        f = {"document_type": "tax_invoice", "seller_tax": MY, "buyer_tax": "9", "vat": "7"}
        data, stashed = self._resolve(f, "high")
        self.assertEqual(data["route"], "sales")
        self.assertEqual(stashed, [])


class ResolveInboxTests(unittest.TestCase):
    """待归类一点归类:非法动作拒绝;dismiss/sales 移出收件箱(不建单)。"""

    def test_bad_action_raises(self):
        from core.pos_api import PosError

        with self.assertRaises(PosError):
            ik.resolve_inbox(
                _FakeCur(),
                tenant_id="t",
                workspace_client_id=1,
                item_id="x",
                action="bogus",
                created_by="u",
                settings={},
            )

    def test_dismiss_marks_dismissed(self):
        r = ik.resolve_inbox(
            _FakeCur(),
            tenant_id="t",
            workspace_client_id=1,
            item_id="x",
            action="dismiss",
            created_by="u",
            settings={},
        )
        self.assertEqual(r["status"], "dismissed")

    def test_sales_marks_resolved(self):
        r = ik.resolve_inbox(
            _FakeCur(),
            tenant_id="t",
            workspace_client_id=1,
            item_id="x",
            action="sales",
            created_by="u",
            settings={},
        )
        self.assertEqual(r["status"], "resolved")


# 旧 F10「LINE 文字静默记一笔 posted 费用」已删(违反 doc 10 §5 死穴:绝不静默入账)。
# 文本路改走 services/expense 引擎:解析→草稿→确认卡,覆盖见 test_expense_line_quick_entry.py。


if __name__ == "__main__":
    unittest.main()
