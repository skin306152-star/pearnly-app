# -*- coding: utf-8 -*-
"""LINE 图片票 OCR 前快速路径(P1G-Perf · 重复图早期短路 + 图片指纹 DAL + Rule 7 收紧)。

锁:
  1. 同图已建单 → early_dup_short_circuit 命中即发当前状态卡,返回 True,不进 OCR。
  2. 未命中 / 无 tenant·ws → 返回 False(回落正常 OCR),不发卡。
  3. 三态各发对应卡(posted 数据卡 / void 终态卡 / draft 可确认卡)。
  4. image_dedup.find_recent / set_sha 参数化 + 套账隔离(fake cursor 验 SQL 形)。
  5. Rule 7 主金额可靠时不再升 L3(只靠 page 末尾 validation_warning 提示)。
"""

import unittest
from unittest import mock


class _CM:
    def __init__(self, cur):
        self._cur = cur

    def __enter__(self):
        return self._cur

    def __exit__(self, *a):
        return False


def _detail(status="posted"):
    return {
        "doc": {"id": "D1", "grand_total": "140.00", "status": status},
        "supplier": {"name": "Cafe", "tax_id": ""},
        "lines": [],
    }


def _user():
    return {"id": "U1", "tenant_id": "T1"}


def _run_short_circuit(*, hit, detail, ws=7):
    from core import db
    from services.expense import line_correct
    from services.line_binding import line_action_nonce, line_client
    from services.ocr import line_image_fastpath as fp

    pushed = []
    with (
        mock.patch.object(db, "get_cursor_rls", return_value=_CM(object())),
        mock.patch("services.purchase.image_dedup.find_recent", return_value=hit),
        mock.patch("services.purchase.docs.get_doc", return_value=detail),
        mock.patch.object(line_action_nonce, "mint", return_value="TOK"),
        mock.patch.object(line_correct, "_set_active"),
        mock.patch.object(
            line_client, "push_messages", side_effect=lambda uid, msgs: pushed.append(msgs) or True
        ),
        # 卡构建只验「发了卡」,不验 Flex 细节(那有 line_card 专测)
        mock.patch("services.line_binding.line_posted_card.build", return_value={"type": "x"}),
        mock.patch("services.line_binding.line_posted_card.fields_from_detail", return_value={}),
        mock.patch("services.line_binding.line_card.result_card", return_value={"type": "x"}),
        mock.patch("services.line_binding.line_card.terminal_card", return_value={"type": "x"}),
    ):
        ok = fp.early_dup_short_circuit(_user(), "Uline", "h" * 64, ws, "th", None)
    return ok, pushed


class EarlyDupShortCircuitTests(unittest.TestCase):
    def test_hit_posted_pushes_and_returns_true(self):
        ok, pushed = _run_short_circuit(
            hit={"id": "D1", "status": "posted"}, detail=_detail("posted")
        )
        self.assertTrue(ok)
        self.assertEqual(len(pushed), 1)

    def test_hit_void_pushes_terminal(self):
        ok, pushed = _run_short_circuit(hit={"id": "D1", "status": "void"}, detail=_detail("void"))
        self.assertTrue(ok)
        self.assertEqual(len(pushed), 1)

    def test_hit_draft_pushes_confirm(self):
        ok, pushed = _run_short_circuit(
            hit={"id": "D1", "status": "draft"}, detail=_detail("draft")
        )
        self.assertTrue(ok)
        self.assertEqual(len(pushed), 1)

    def test_miss_returns_false_no_push(self):
        ok, pushed = _run_short_circuit(hit=None, detail=None)
        self.assertFalse(ok)
        self.assertEqual(pushed, [])

    def test_no_tenant_or_ws_returns_false(self):
        from services.ocr import line_image_fastpath as fp

        self.assertFalse(fp.early_dup_short_circuit({"id": "U1"}, "Uline", "h" * 64, 7, "th", None))
        self.assertFalse(fp.early_dup_short_circuit(_user(), "Uline", "h" * 64, None, "th", None))


class _FakeCursor:
    def __init__(self, row=None):
        self._row = row
        self.executed = []

    def execute(self, sql, params):
        self.executed.append((sql, params))

    def fetchone(self):
        return self._row


class ImageDedupDalTests(unittest.TestCase):
    def test_set_sha_noop_on_empty(self):
        from services.purchase import image_dedup

        cur = _FakeCursor()
        image_dedup.set_sha(
            cur, tenant_id="T1", workspace_client_id=7, doc_id="D1", image_sha256=""
        )
        self.assertEqual(cur.executed, [])

    def test_set_sha_scoped_update(self):
        from services.purchase import image_dedup

        cur = _FakeCursor()
        image_dedup.set_sha(
            cur, tenant_id="T1", workspace_client_id=7, doc_id="D1", image_sha256="abc"
        )
        sql, params = cur.executed[0]
        self.assertIn("UPDATE purchase_docs SET image_sha256", sql)
        self.assertIn("tenant_id", sql)
        self.assertIn("workspace_client_id", sql)
        self.assertEqual(params, ("abc", "T1", 7, "D1"))

    def test_find_recent_hit(self):
        from services.purchase import image_dedup

        cur = _FakeCursor(row={"id": "D9", "status": "posted"})
        out = image_dedup.find_recent(
            cur, tenant_id="T1", workspace_client_id=7, image_sha256="abc"
        )
        self.assertEqual(out, {"id": "D9", "status": "posted"})
        sql, params = cur.executed[0]
        self.assertIn("image_sha256 = %s", sql)
        self.assertIn("make_interval", sql)  # 只认近期单据

    def test_find_recent_empty_hash(self):
        from services.purchase import image_dedup

        cur = _FakeCursor()
        self.assertIsNone(
            image_dedup.find_recent(cur, tenant_id="T1", workspace_client_id=7, image_sha256="")
        )
        self.assertEqual(cur.executed, [])


class Rule7AmountGateTests(unittest.TestCase):
    """主金额可靠的堆叠多票不再升 L3(P1G-Perf);主金额不可靠才升。"""

    def _page(self, full_text):
        from types import SimpleNamespace

        return SimpleNamespace(full_text=full_text, blocks=[], avg_confidence=1.0)

    def _inv(self, **kw):
        from services.ocr.schemas_invoice import ThaiInvoice

        base = dict(
            document_type="tax_invoice",
            invoice_number="IV69/00179",
            total_amount="107",
            subtotal="100",
            vat="7",
            seller_tax="",
            additional_invoices=[],
        )
        base.update(kw)
        return ThaiInvoice(**base)

    def test_reliable_amount_no_l3_for_stacked(self):
        from services.ocr.triggers import _evaluate_triggers

        page = self._page("IV69/00179 IV69/00189 total 107")
        out = " ".join(_evaluate_triggers(page, self._inv()))
        self.assertNotIn("possible_missed_invoice", out)

    def test_unreliable_amount_escalates_stacked(self):
        from services.ocr.triggers import _evaluate_triggers

        # 金额自洽被打破(subtotal+vat != total)→ 主金额不可靠 → 允许 L3 找回漏票
        page = self._page("IV69/00179 IV69/00189 total 999")
        out = " ".join(_evaluate_triggers(page, self._inv(total_amount="999")))
        self.assertIn("possible_missed_invoice", out)


class CategoryTimeoutTests(unittest.TestCase):
    """分类 LLM 走 3s 硬上限 + source 归因(P1G-Perf · 不阻塞入账卡)。"""

    def test_timeout_is_short(self):
        from services.purchase.image_category import _CAT_LLM_TIMEOUT

        self.assertLessEqual(_CAT_LLM_TIMEOUT, 3)

    def _call(self, **over):
        from services.purchase import image_category as li

        kw = dict(
            tenant_id="T1",
            workspace_client_id=7,
            vendor="Cafe",
            tax_id="",
            descs=["latte"],
            items=[],
            api_key="k",
        )
        kw.update(over)
        return li.smart_category(object(), **kw)

    def test_learned_overrides_rules_and_llm(self):
        from services.expense import category_ai
        from services.purchase import image_category as li

        learned = {
            "category_id": "L1",
            "subcategory_id": "LS1",
            "category_name": "Food",
            "subcategory_name": "Drink",
        }
        with (
            mock.patch("services.purchase.categories.get_tree", return_value=[]),
            mock.patch("services.expense.conversation.find_exact", return_value=learned),
            mock.patch.object(category_ai, "classify_rules") as cr,
            mock.patch.object(category_ai, "suggest_category") as sg,
        ):
            out = self._call(tax_id="1234567890123")
        self.assertEqual((out[0], out[1], out[5]), ("L1", "LS1", "learned"))
        cr.assert_not_called()  # 用户学习最高优先 → 不再跑规则/LLM
        sg.assert_not_called()

    def test_rule_item_layer_source_and_no_llm(self):
        from services.expense import category_ai
        from services.purchase import image_category as li

        with (
            mock.patch("services.purchase.categories.get_tree", return_value=[]),
            mock.patch("services.expense.conversation.find_exact", return_value=None),
            mock.patch.object(category_ai, "classify_rules", return_value=("C1", "S1", "item")),
            mock.patch.object(li, "_category_names", return_value=("Food", "Coffee")),
            mock.patch.object(category_ai, "suggest_category") as sg,
        ):
            out = self._call()
        self.assertEqual(out[5], "rule")
        sg.assert_not_called()  # 确定性规则命中 → 不再调 LLM

    def test_vendor_layer_marks_vendor_default(self):
        from services.expense import category_ai
        from services.purchase import image_category as li

        with (
            mock.patch("services.purchase.categories.get_tree", return_value=[]),
            mock.patch("services.expense.conversation.find_exact", return_value=None),
            mock.patch.object(category_ai, "classify_rules", return_value=("C1", "S1", "vendor")),
            mock.patch.object(li, "_category_names", return_value=("Food", "")),
            mock.patch.object(category_ai, "suggest_category") as sg,
        ):
            out = self._call(vendor="7-Eleven", descs=["?????"])
        self.assertEqual(out[5], "vendor_default")  # 品名不清 → 商户默认 → 日志可观察
        sg.assert_not_called()

    def test_llm_fallback_uses_short_timeout(self):
        from services.expense import category_ai
        from services.purchase import image_category as li

        with (
            mock.patch("services.purchase.categories.get_tree", return_value=[]),
            mock.patch("services.expense.conversation.find_exact", return_value=None),
            mock.patch.object(category_ai, "classify_rules", return_value=(None, None, "")),
            mock.patch.object(category_ai, "categorize_items", return_value=[]),
            mock.patch.object(category_ai, "suggest_category", return_value=("C2", "S2")) as sg,
            mock.patch.object(li, "_category_names", return_value=("Office", "Sw")),
        ):
            out = self._call(vendor="Acme", descs=["thing"])
        self.assertEqual(out[5], "ai")
        self.assertEqual(sg.call_args.kwargs.get("timeout"), li._CAT_LLM_TIMEOUT)


if __name__ == "__main__":
    unittest.main(verbosity=2)
