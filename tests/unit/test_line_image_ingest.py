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


def _run(resolve_ret, *, band="high", auto_book=True, fields=None, tree=None):
    created = {"doc": {"id": "D1"}}
    with (
        mock.patch.object(ik, "resolve_image_intake", return_value=resolve_ret),
        mock.patch.object(ik, "workspace_name", return_value="WS"),
        mock.patch(
            "services.purchase.settings.get_settings",
            return_value={"auto_stock_in": False, "auto_book": auto_book},
        ),
        mock.patch("services.purchase.categories.get_tree", return_value=tree or []),
        mock.patch("services.purchase.docs.create_doc", return_value=created) as cdoc,
        mock.patch("services.purchase.posting.post_doc", return_value=created) as pdoc,
        mock.patch("services.line_binding.line_action_nonce.mint", return_value="TOK"),
    ):
        out = li.ingest_line_image(
            object(),
            tenant_id="t",
            workspace_client_id=1,
            fields=fields or {"document_type": "", "seller_name": "ACME", "date": "2026-06-14"},
            confidence=band,
            created_by="u",
        )
    return out, cdoc, pdoc


class IngestTests(unittest.TestCase):
    def test_high_complete_posts(self):
        # 自动入账开 + 高置信齐全 → 直接过账(posted)。卡片明细取自 OCR items(加总≤总额)。
        res = {"route": "purchase", "draft": _draft(), "dedupe_hit": False, "field_confidence": {}}
        fields = {
            "document_type": "",
            "seller_name": "ACME",
            "date": "2026-06-14",
            "total_amount": "100",
            "items": [{"name": "x", "subtotal": "100"}],
        }
        out, cdoc, pdoc = _run(res, band="high", auto_book=True, fields=fields)
        self.assertEqual(out["state"], "posted")
        self.assertEqual(out["card_fields"]["detail"], "x")  # 逐条明细填进卡
        self.assertEqual(out["card_fields"]["items"], [{"name": "x", "amount": "100.00"}])
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
                "services.expense.category_ai.categorize_items",
                return_value=[(None, None)],
            ),
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

    def test_food_item_overrides_fuel_vendor_category(self):
        # PTT 体系小票如果买的是咖啡,按明细归餐饮,不能被卖家名带到燃油。
        draft = {
            "doc_kind": "expense",
            "supplier": {"name": "บมจ. ปตท. น้ำมันและการค้าปลีก", "tax_id": None},
            "doc_no": "R#1",
            "lines": [
                {"description": "บมจ. ปตท. น้ำมันและการค้าปลีก", "qty": "1", "unit_price": "70"}
            ],
            "grand_total": "70.00",
        }
        res = {"route": "expense", "draft": draft, "dedupe_hit": False, "field_confidence": {}}
        tree = [
            {
                "id": "p_fuel",
                "name": "ค่าเดินทางและขนส่ง",
                "children": [{"id": "c_fuel", "name": "ค่าน้ำมันเชื้อเพลิง"}],
            },
            {
                "id": "p_food",
                "name": "ค่าอาหารและรับรอง",
                "children": [{"id": "c_food", "name": "ค่าอาหาร/เครื่องดื่ม"}],
            },
        ]
        fields = {
            "document_type": "receipt",
            "seller_name": "บมจ. ปตท. น้ำมันและการค้าปลีก",
            "total_amount": "70",
            "vat": "4.58",
            "items": [
                {"name": "TW แบล็คคอฟฟี่ เย็น", "subtotal": "60"},
                {"name": "TW เพิ่มช็อตกาแฟ", "subtotal": "10"},
            ],
        }
        out, _cdoc, _pdoc = _run(res, band="high", auto_book=False, fields=fields, tree=tree)
        self.assertEqual(out["card_fields"]["category"], "ค่าอาหารและรับรอง")
        self.assertEqual(out["card_fields"]["subcategory"], "ค่าอาหาร/เครื่องดื่ม")
        self.assertNotIn("category", out["field_confidence"])

    def test_mixed_receipt_dominant_category_marks_close_split_for_review(self):
        # 混合小票按金额最大的类别显示;接近五五开时分类字段打低置信,卡片会提示核对。
        draft = {
            "doc_kind": "expense",
            "supplier": {"name": "PTT", "tax_id": None},
            "doc_no": "R#1",
            "lines": [{"description": "PTT", "qty": "1", "unit_price": "110"}],
            "grand_total": "110.00",
        }
        res = {"route": "expense", "draft": draft, "dedupe_hit": False, "field_confidence": {}}
        tree = [
            {
                "id": "p_fuel",
                "name": "ค่าเดินทางและขนส่ง",
                "children": [{"id": "c_fuel", "name": "ค่าน้ำมันเชื้อเพลิง"}],
            },
            {
                "id": "p_food",
                "name": "ค่าอาหารและรับรอง",
                "children": [{"id": "c_food", "name": "ค่าอาหาร/เครื่องดื่ม"}],
            },
        ]
        fields = {
            "document_type": "receipt",
            "seller_name": "PTT",
            "total_amount": "110",
            "items": [
                {"name": "ดีเซล", "subtotal": "60"},
                {"name": "กาแฟ", "subtotal": "50"},
            ],
        }
        out, _cdoc, _pdoc = _run(res, band="high", auto_book=False, fields=fields, tree=tree)
        self.assertEqual(out["card_fields"]["category"], "ค่าเดินทางและขนส่ง")
        self.assertEqual(out["field_confidence"]["category"], 0.82)

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

    def test_garbage_ocr_collapses_to_no_items_not_fake_vendor_line(self):
        # OCR 原始 items 荒腔走板(7-11 单行 845 ≫ 票面 110)→ 草稿收敛成卖家兜底单行;卡片不显
        # 「1. 卖家名 ฿110」假行(那看着像 1 个叫店名的商品·误导)→ 明细留空,去详情页看。
        draft = {
            "doc_kind": "expense",
            "supplier": {"name": "7-Eleven", "tax_id": None},
            "doc_no": "R#1",
            "lines": [{"description": "7-Eleven", "qty": "1", "unit_price": "110"}],
            "grand_total": "110.00",
        }
        res = {"route": "expense", "draft": draft, "dedupe_hit": False, "field_confidence": {}}
        fields = {
            "document_type": "simplified_tax_invoice",
            "seller_name": "7-Eleven",
            "total_amount": "110",
            "vat": "0",
            "items": [{"name": "bad OCR item", "subtotal": "845"}],
        }
        out, _cdoc, _pdoc = _run(res, band="high", auto_book=False, fields=fields)
        self.assertEqual(out["card_fields"]["items"], [])
        self.assertEqual(out["card_fields"]["detail"], "")
        # 不显明细时不再报「明细可能不全」(矛盾)→ 改出 items_unread 提示,warn 关。
        self.assertFalse(out["warn_total"])
        self.assertTrue(out["card_fields"].get("items_unread"))

    def test_no_ocr_items_shows_no_fake_line(self):
        # OCR 一条明细都没抽出(旋转热敏票)→ 草稿卖家兜底单行 → 卡片明细留空,不显假的卖家名单行。
        draft = {
            "doc_kind": "expense",
            "supplier": {"name": "Little Betong", "tax_id": None},
            "doc_no": None,
            "lines": [{"description": "Little Betong", "qty": "1", "unit_price": "431"}],
            "grand_total": "431.00",
        }
        res = {"route": "expense", "draft": draft, "dedupe_hit": False, "field_confidence": {}}
        fields = {
            "document_type": "receipt",
            "seller_name": "Little Betong",
            "total_amount": "431",
            "vat": "0",
            "items": [],
        }
        out, _cdoc, _pdoc = _run(res, band="needs_review", auto_book=False, fields=fields)
        self.assertEqual(out["card_fields"]["items"], [])
        self.assertEqual(out["card_fields"]["detail"], "")
        self.assertTrue(out["card_fields"].get("items_unread"))

    def test_pos_receipt_card_keeps_raw_items_when_they_match_total(self):
        # POS 小票价格通常已含 VAT:商品行 60+10=总额 70,不要因为 VAT 表存在而压成供应商一行。
        draft = {
            "doc_kind": "expense",
            "supplier": {"name": "Cafe Amazon", "tax_id": None},
            "doc_no": "R#1",
            "lines": [{"description": "Cafe Amazon", "qty": "1", "unit_price": "70"}],
            "grand_total": "70.00",
        }
        res = {"route": "expense", "draft": draft, "dedupe_hit": False, "field_confidence": {}}
        fields = {
            "document_type": "receipt",
            "seller_name": "Cafe Amazon",
            "total_amount": "70",
            "vat": "4.58",
            "items": [
                {"name": "TW แบล็คคอฟฟี่ เย็น", "subtotal": "60"},
                {"name": "TW เพิ่มช็อตกาแฟ", "subtotal": "10"},
            ],
        }
        out, _cdoc, _pdoc = _run(res, band="high", auto_book=False, fields=fields)
        self.assertEqual(
            out["card_fields"]["items"],
            [
                {"name": "TW แบล็คคอฟฟี่ เย็น", "amount": "60.00"},
                {"name": "TW เพิ่มช็อตกาแฟ", "amount": "10.00"},
            ],
        )
        self.assertFalse(out["warn_total"])

    def test_zero_modifier_items_dropped_from_main_detail(self):
        # 0 元 modifier(ไม่หวาน 0%/แถมฟรี)不进主明细 · 只留有金额的主项。
        f = {
            "items": [
                {"name": "TW กาแฟ", "subtotal": "120"},
                {"name": "TW ไม่หวาน 0%", "subtotal": "0"},
                {"name": "TW เพิ่มช็อต", "subtotal": "10"},
                {"name": "แก้ว Mickey (แถมฟรี)", "subtotal": "0"},
            ],
            "total_amount": "130",
        }
        self.assertEqual(
            li._card_items(f),
            [{"name": "TW กาแฟ", "amount": "120.00"}, {"name": "TW เพิ่มช็อต", "amount": "10.00"}],
        )

    def test_summary_items_are_filtered_from_card(self):
        f = {
            "items": [
                {"name": "ไก่ทอดเบตง", "subtotal": "165"},
                {"name": "จำนวน 8", "subtotal": "131"},
            ],
            "total_amount": "165",
        }
        self.assertEqual(li._card_items(f), [{"name": "ไก่ทอดเบตง", "amount": "165.00"}])


class TotalMismatchTests(unittest.TestCase):
    """总额不符提示:明细加总+VAT 与票面总额对不上才提示;对得上/无明细不误报。"""

    def test_reconciles_no_warn(self):
        f = {
            "items": [{"qty": "1", "price": "1000"}],
            "vat": "70",
            "total_amount": "1070",
        }
        self.assertFalse(li._total_mismatch(f))

    def test_pos_inclusive_vat_no_warn(self):
        f = {
            "items": [{"subtotal": "60"}, {"subtotal": "10"}],
            "vat": "4.58",
            "total_amount": "70",
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


class VatBreakdownTests(unittest.TestCase):
    """税额拆解确定性算(7% · 不信 OCR 误读位数):税前 = total−VAT,VAT 按 7% 含税重算。"""

    def test_inclusive_70(self):
        # 70 含税:VAT 4.58、税前 65.42。
        self.assertEqual(
            li._vat_breakdown({"subtotal": "70.00", "vat": "4.58", "total_amount": "70.00"}),
            ("65.42", "4.58"),
        )

    def test_vat_misread_recomputed_to_7pct(self):
        # OCR 把 140 的 VAT 读成 10(应 9.16)→ 按 7% 确定性重算 → 130.84 / 9.16。
        self.assertEqual(
            li._vat_breakdown({"subtotal": "130", "vat": "10", "total_amount": "140"}),
            ("130.84", "9.16"),
        )

    def test_no_vat_keeps_subtotal(self):
        self.assertEqual(
            li._vat_breakdown({"subtotal": "431.00", "vat": "0.00", "total_amount": "431.00"}),
            ("431.00", "0.00"),
        )


class IncompleteItemsCardTests(unittest.TestCase):
    def test_collapsed_draft_still_shows_real_ocr_lines(self):
        # 草稿因不对账塌成「卖家名单行」,但 OCR 原行像真(漏行非乱读)→ 卡片照显原多行 + 不全提示。
        draft = {
            "doc_kind": "expense",
            "supplier": {"name": "Little Betong", "tax_id": None},
            "doc_no": None,
            "lines": [{"description": "Little Betong", "qty": "1", "unit_price": "431"}],
            "grand_total": "431.00",
        }
        res = {"route": "expense", "draft": draft, "dedupe_hit": False, "field_confidence": {}}
        fields = {
            "document_type": "receipt",
            "seller_name": "Little Betong",
            "total_amount": "431",
            "vat": "0",
            "items": [
                {"name": "ข้าวเนื้อ", "subtotal": "95"},
                {"name": "ไก่ทอดเบตง", "subtotal": "125"},
                {"name": "ข้าวเปล่า", "subtotal": "165"},
                {"name": "น้ำแข็ง", "subtotal": "6"},
            ],
        }
        out, _c, _p = _run(res, band="needs_review", auto_book=False, fields=fields)
        names = [i["name"] for i in out["card_fields"]["items"]]
        self.assertEqual(names, ["ข้าวเนื้อ", "ไก่ทอดเบตง", "ข้าวเปล่า", "น้ำแข็ง"])
        self.assertTrue(out["warn_total"])

    def test_payment_method_from_ocr_into_card(self):
        # 票面 QRPayment → 归一 promptpay 进卡片付款方式。
        res = {"route": "purchase", "draft": _draft(), "dedupe_hit": False, "field_confidence": {}}
        fields = {
            "document_type": "",
            "seller_name": "ACME",
            "payment_method": "QRPayment(API)",
        }
        out, _c, _p = _run(res, band="needs_review", auto_book=False, fields=fields)
        self.assertEqual(out["card_fields"]["payment_method"], "promptpay")


if __name__ == "__main__":
    unittest.main()
