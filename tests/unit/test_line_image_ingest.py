# -*- coding: utf-8 -*-
"""LINE 图片置信驱动入账 ingest_line_image(docs/smart-intake/15 §1)。

锁(待归类已下线·一律建草稿):高置信齐全→建单 + post_doc(已入账);重复→建草稿不过账(dup);
低 band→建草稿请确认(confirm)。create/post 是否被调按档位精确断言。
"""

import unittest
from unittest import mock

from services.purchase import intake as ik
from services.purchase import line_ingest as li


def _draft():
    return {
        "doc_kind": "purchase_invoice",
        "supplier": {"name": "ACME", "tax_id": None},
        "doc_no": "INV-1",
        "lines": [{"description": "x", "unit_price": "100"}],
        "grand_total": "107.00",
    }


def _run(resolve_ret, *, band="high", auto_book=True):
    created = {"doc": {"id": "D1"}}
    with (
        mock.patch.object(ik, "resolve_image_intake", return_value=resolve_ret),
        mock.patch.object(ik, "workspace_name", return_value="WS"),
        mock.patch(
            "services.purchase.settings.get_settings",
            return_value={"auto_stock_in": False, "auto_book": auto_book},
        ),
        mock.patch("services.purchase.categories.get_tree", return_value=[]),
        mock.patch("services.purchase.docs.create_doc", return_value=created) as cdoc,
        mock.patch("services.purchase.posting.post_doc", return_value=created) as pdoc,
        mock.patch("services.line_binding.line_action_nonce.mint", return_value="TOK"),
    ):
        out = li.ingest_line_image(
            object(),
            tenant_id="t",
            workspace_client_id=1,
            fields={"document_type": "", "seller_name": "ACME", "date": "2026-06-14"},
            confidence=band,
            created_by="u",
        )
    return out, cdoc, pdoc


class IngestTests(unittest.TestCase):
    def test_high_complete_posts(self):
        # 自动入账开 + 高置信齐全 → 直接过账(posted)。
        res = {"route": "purchase", "draft": _draft(), "dedupe_hit": False, "field_confidence": {}}
        out, cdoc, pdoc = _run(res, band="high", auto_book=True)
        self.assertEqual(out["state"], "posted")
        self.assertEqual(out["card_fields"]["detail"], "x")  # 逐条明细填进卡
        cdoc.assert_called_once()
        pdoc.assert_called_once()
        self.assertEqual(out["doc_id"], "D1")
        self.assertEqual(out["token"], "TOK")  # PO-12 卡片防重放令牌随结果带出

    def test_autobook_off_confirms_no_post(self):
        # 自动入账关(默认):即便高置信齐全也只建草稿发确认卡,不过账。
        res = {"route": "purchase", "draft": _draft(), "dedupe_hit": False, "field_confidence": {}}
        out, cdoc, pdoc = _run(res, band="high", auto_book=False)
        self.assertEqual(out["state"], "confirm")
        cdoc.assert_called_once()
        pdoc.assert_not_called()

    def test_duplicate_confirms_no_post(self):
        res = {"route": "purchase", "draft": _draft(), "dedupe_hit": True, "field_confidence": {}}
        out, cdoc, pdoc = _run(res, band="high")
        self.assertEqual(out["state"], "dup")
        cdoc.assert_called_once()
        pdoc.assert_not_called()

    def test_low_band_confirms_no_post(self):
        res = {"route": "purchase", "draft": _draft(), "dedupe_hit": False, "field_confidence": {}}
        out, cdoc, pdoc = _run(res, band="needs_review")
        self.assertEqual(out["state"], "confirm")
        cdoc.assert_called_once()
        pdoc.assert_not_called()

    def test_llm_first_category(self):
        # 智能分类:有 key → LLM 优先选(治分类不对/空),填进卡(柴油 → 交通/餐饮)。
        res = {"route": "purchase", "draft": _draft(), "dedupe_hit": False, "field_confidence": {}}
        tree = [{"id": "p1", "name": "餐饮 & 招待", "children": [{"id": "c1", "name": "餐费"}]}]
        created = {"doc": {"id": "D1"}}
        with (
            mock.patch.object(ik, "resolve_image_intake", return_value=res),
            mock.patch.object(ik, "workspace_name", return_value="WS"),
            mock.patch(
                "services.purchase.settings.get_settings",
                return_value={"auto_stock_in": False, "auto_book": False},
            ),
            mock.patch("services.purchase.categories.get_tree", return_value=tree),
            mock.patch.object(ik, "_match_category", return_value=(None, None)),
            mock.patch("services.purchase.docs.create_doc", return_value=created),
            mock.patch("services.line_binding.line_action_nonce.mint", return_value="TOK"),
            mock.patch(
                "services.expense.category_ai.suggest_category", return_value=("p1", "c1")
            ) as suggest,
        ):
            out = li.ingest_line_image(
                object(),
                tenant_id="t",
                workspace_client_id=1,
                fields={"document_type": "", "seller_name": "ACME"},
                confidence="high",
                created_by="u",
                api_key="k",
            )
        suggest.assert_called_once()
        self.assertEqual(out["card_fields"]["category"], "餐饮 & 招待")
        self.assertEqual(out["card_fields"]["subcategory"], "餐费")

    def test_no_api_key_no_llm_call(self):
        # 无 key → 不调 LLM 兜底(省成本),分类留空。
        res = {"route": "purchase", "draft": _draft(), "dedupe_hit": False, "field_confidence": {}}
        tree = [{"id": "p1", "name": "餐饮", "children": [{"id": "c1", "name": "餐费"}]}]
        with (
            mock.patch.object(ik, "resolve_image_intake", return_value=res),
            mock.patch.object(ik, "workspace_name", return_value="WS"),
            mock.patch(
                "services.purchase.settings.get_settings",
                return_value={"auto_stock_in": False, "auto_book": False},
            ),
            mock.patch("services.purchase.categories.get_tree", return_value=tree),
            mock.patch.object(ik, "_match_category", return_value=(None, None)),
            mock.patch("services.purchase.docs.create_doc", return_value={"doc": {"id": "D1"}}),
            mock.patch("services.line_binding.line_action_nonce.mint", return_value="TOK"),
            mock.patch("services.expense.category_ai.suggest_category") as suggest,
        ):
            li.ingest_line_image(
                object(),
                tenant_id="t",
                workspace_client_id=1,
                fields={"document_type": "", "seller_name": "ACME"},
                confidence="high",
                created_by="u",
            )
        suggest.assert_not_called()


class TotalMismatchTests(unittest.TestCase):
    """总额不符提示:明细加总+VAT 与票面总额对不上才提示;对得上/无明细不误报。"""

    def test_reconciles_no_warn(self):
        f = {
            "items": [{"qty": "1", "price": "1000"}],
            "vat": "70",
            "total_amount": "1070",
        }
        self.assertFalse(li._total_mismatch(f))

    def test_mismatch_warns(self):
        # 明细只抽到 1000,但总额 2722(漏行)→ 提示。
        f = {"items": [{"subtotal": "1000"}], "vat": "0", "total_amount": "2722"}
        self.assertTrue(li._total_mismatch(f))

    def test_no_items_no_warn(self):
        self.assertFalse(li._total_mismatch({"total_amount": "500", "items": []}))

    def test_no_total_no_warn(self):
        self.assertFalse(li._total_mismatch({"items": [{"subtotal": "100"}]}))


if __name__ == "__main__":
    unittest.main()
