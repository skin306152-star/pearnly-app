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

    def test_payment_evidence_to_inbox_never_posts(self):
        # PO-10:银行转账截图判付款证据 → 待归类,即便带金额/VAT 也不冒充税票、不建费用单。
        f = {"document_type": "payment_evidence", "seller_tax": "", "vat": "70"}
        self.assertEqual(ik.judge_direction(f, my_tax_id=MY), ("unknown", "inbox"))

    def test_order_evidence_to_inbox(self):
        f = {"document_type": "order_evidence", "seller_tax": "", "vat": "0"}
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

    def test_subtotal_trusted_when_qty_price_conflict(self):
        # 加油票:qty=22(积分)× price=39.85 = 876.70 ≠ subtotal 1780 → 信 subtotal,行额=1780。
        f = {"items": [{"name": "ไฮดีเซล", "qty": "22", "price": "39.85", "subtotal": "1780"}]}
        ln = ik.build_draft_from_invoice(f, kind="expense")["lines"][0]
        self.assertEqual(ln["qty"], "1")
        self.assertEqual(ln["unit_price"], "1780")

    def test_qty_price_kept_when_consistent(self):
        # qty×price 与 subtotal 一致 → 保留明细(不动)。
        f = {"items": [{"name": "x", "qty": "2", "price": "50", "subtotal": "100"}]}
        ln = ik.build_draft_from_invoice(f, kind="expense")["lines"][0]
        self.assertEqual(ln["qty"], "2")
        self.assertEqual(ln["unit_price"], "50")


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


class LineGateTests(unittest.TestCase):
    """LINE 入账门控(统一智能通道 · 2026-06-15):开 expense 即放行(不按业态分)。

    置信驱动入账见 test_line_image_ingest.py(图)/ test_expense_confidence.py(判级)。
    """

    def _gate(self, expense_on):
        from unittest import mock

        from services.modules import store as mstore

        with mock.patch.object(mstore, "is_enabled", return_value=expense_on):
            return ik.line_expense_gate_open(_FakeCur(), tenant_id="t")

    def test_open_when_expense_on(self):
        self.assertTrue(self._gate(True))

    def test_closed_when_expense_off(self):
        self.assertFalse(self._gate(False))


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

    def test_source_propagates_to_draft(self):
        # 来源(line/photo)必须落到草稿,否则 create_doc 默认 manual → 列表显「手录」(PO-6)。
        f = {
            "document_type": "tax_invoice",
            "buyer_tax": MY,
            "vat": "7",
            "subtotal": "1000",
            "items": [{"name": "x", "qty": "1", "price": "1000"}],
        }
        data = ik.resolve_image_intake(
            _FakeCur(),
            tenant_id="t",
            workspace_client_id=1,
            fields=f,
            confidence="high",
            settings={},
            source="line",
        )
        self.assertIsNotNone(data["draft"])
        self.assertEqual(data["draft"]["source"], "line")


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

    def test_resolve_preserves_source(self):
        # 归类建单时保留待归类项的原始来源(line/photo),不退回「手录」(PO-6)。
        from unittest import mock

        from services.purchase import docs as docs_svc

        captured = {}

        class Cur:
            def execute(self, *a, **k):
                return None

            def fetchone(self):
                return {
                    "source": "line",
                    "raw": {"items": [{"name": "x", "qty": "1", "price": "100"}]},
                    "image_url": "",
                }

        def fake_create(cur, **k):
            captured.update(k.get("data") or {})
            return {"doc": {"id": "d1"}}

        with mock.patch.object(docs_svc, "create_doc", side_effect=fake_create):
            ik.resolve_inbox(
                Cur(),
                tenant_id="t",
                workspace_client_id=1,
                item_id="x",
                action="expense",
                created_by="u",
                settings={},
            )
        self.assertEqual(captured.get("source"), "line")


# 旧 F10「LINE 文字静默记一笔 posted 费用」已删(违反 doc 10 §5 死穴:绝不静默入账)。
# 文本路改走 services/expense 引擎:解析→直接落采购草稿单(草稿态待复核,非 posted),
# 覆盖见 test_expense_line_quick_entry.py + test_line_expense_to_purchase.py。


class PaymentDefaultTests(unittest.TestCase):
    """PO-5 智能默认付款态:现金收据 → 已付;税务发票/赊账 → 未付。"""

    def test_receipt_defaults_paid(self):
        self.assertEqual(ik.default_payment_status("receipt", "expense"), "paid")

    def test_tax_invoice_defaults_unpaid(self):
        self.assertEqual(ik.default_payment_status("tax_invoice", "purchase_invoice"), "unpaid")
        self.assertEqual(ik.default_payment_status("simplified_tax_invoice", "expense"), "unpaid")

    def test_expense_no_type_defaults_paid(self):
        self.assertEqual(ik.default_payment_status("", "expense"), "paid")

    def test_purchase_no_type_defaults_unpaid(self):
        self.assertEqual(ik.default_payment_status("", "purchase_invoice"), "unpaid")

    def test_build_draft_carries_payment_status(self):
        f = {
            "document_type": "receipt",
            "vat": "0",
            "items": [{"name": "x", "qty": "1", "price": "50"}],
        }
        d = ik.build_draft_from_invoice(f, kind="expense")
        self.assertEqual(d["payment_status"], "paid")


if __name__ == "__main__":
    unittest.main()
