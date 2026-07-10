# -*- coding: utf-8 -*-
"""泰英商号别名方向锚(B2-c · G1R2 毛刺②根治)。

三块:①名集锚 + 匹配模式(exact/substring/legal)+ 税号/名称冲突 → ambiguous;②G1R2 真语料
回放(Ocha「Sister Makeup」跨语种失锚 → 加别名后锚回自家销项);③classify 闸接线(开=名集
路,关=单名现状路)。闸关的逐字节回归由 test_workorder_sort/classify 全量零改动通过背书。
"""

import unittest

from services.workorder.decisions import DIRECTION_AMBIGUOUS, SALES_DIRECTION_UNHANDLED
from services.workorder.engine import StepContext
from services.workorder.steps import classify
from services.workorder.steps import sort as sort_step

OWN_TAX = "0105567178203"
OTHER_TAX = "0735527000289"
# G1R2 真形态:client 94 法定名是泰文,Ocha POS 小票印英文商号,税号被 OCR 读成店头电话。
THAI_LEGAL = "บริษัท ซิสเตอร์ เมคอัพ จำกัด"
ALIAS_EN = "Sister Makeup"
STORE_PHONE = "021234567"  # 9 位电话,clean_tax_id → '' → 税号锚失灵

# Ocha 小票上英文商号的三种真实形态(大小写/法人后缀变体),归一化后都是 "sistermakeup"。
OCHA_SELLER_FORMS = ("Sister Makeup", "SISTER MAKEUP", "Sister Makeup Co., Ltd.")

LEGAL_ENTRY = (THAI_LEGAL, "legal")
ALIAS_ENTRY = (ALIAS_EN, "exact")


def _ocha_receipt(seller_name):
    """Ocha 自家销售小票的 OCR 形态:卖方印英文商号、税号读成电话、零售无买方。"""
    return {
        "document_type": "tax_invoice",
        "vat": "7.00",
        "seller_name": seller_name,
        "seller_tax": STORE_PHONE,
        "buyer_tax": "",
        "buyer_name": "",
    }


class NameSetAnchorTests(unittest.TestCase):
    def test_alias_exact_hit_on_seller_is_sales_direction(self):
        kind, reason = sort_step.bin_ocr_fields(
            _ocha_receipt(ALIAS_EN), own_tax_id=OWN_TAX, own_names=[LEGAL_ENTRY, ALIAS_ENTRY]
        )
        self.assertEqual((kind, reason), ("unknown", SALES_DIRECTION_UNHANDLED))

    def test_alias_exact_does_not_match_superstring(self):
        # exact = 归一等值,不吃子串:别名 "sisterbeauty" 不命中 "sisterbeautysupply"。
        fields = {
            "document_type": "tax_invoice",
            "vat": "5",
            "seller_tax": OTHER_TAX,
            "buyer_tax": "",
            "buyer_name": "Sister Beauty Supply Co., Ltd.",
        }
        kind, reason = sort_step.bin_ocr_fields(
            fields,
            own_tax_id=OWN_TAX,
            own_names=[(THAI_LEGAL, "legal"), ("Sister Beauty", "exact")],
        )
        self.assertEqual((kind, reason), ("unknown", DIRECTION_AMBIGUOUS))

    def test_alias_substring_mode_matches_superstring(self):
        fields = {
            "document_type": "tax_invoice",
            "vat": "5",
            "seller_tax": "",
            "buyer_tax": OTHER_TAX,
            "seller_name": "Sister Beauty Supply Co., Ltd.",
        }
        kind, reason = sort_step.bin_ocr_fields(
            fields,
            own_tax_id=OWN_TAX,
            own_names=[(THAI_LEGAL, "legal"), ("Sister Beauty", "substring")],
        )
        self.assertEqual((kind, reason), ("unknown", SALES_DIRECTION_UNHANDLED))

    def test_legal_name_in_set_keeps_min4_substring(self):
        # 名集路里的法定名仍走 ≥4 子串现状(与闸关单名路同口径)。
        fields = {
            "document_type": "tax_invoice",
            "vat": "9",
            "seller_tax": OTHER_TAX,
            "buyer_tax": "",
            "buyer_name": "ซิสเตอร์ เมคอัพ",  # 缺 บริษัท/จำกัด,归一后是法定字号子串
        }
        kind, reason = sort_step.bin_ocr_fields(fields, own_tax_id=OWN_TAX, own_names=[LEGAL_ENTRY])
        self.assertEqual((kind, reason), ("purchase_invoice", None))

    def test_taxid_first_wins_over_alias(self):
        # 税号第一:买方税号==自家 → 进项,别名无论怎么配都不改结果。
        fields = {
            "document_type": "tax_invoice",
            "vat": "7",
            "seller_tax": OTHER_TAX,
            "buyer_tax": OWN_TAX,
            "seller_name": ALIAS_EN,  # 卖方名撞别名,但税号锚先赢
        }
        kind, reason = sort_step.bin_ocr_fields(
            fields, own_tax_id=OWN_TAX, own_names=[LEGAL_ENTRY, ALIAS_ENTRY]
        )
        self.assertEqual((kind, reason), ("purchase_invoice", None))

    def test_taxid_name_conflict_is_ambiguous_not_guessed(self):
        # 闸4:卖方名命中别名(说自家是卖方),但卖方印着一个 clean 且非自家的税号(说卖方是别家)
        # → 两锚打架,不猜,ambiguous+冲突旗。
        fields = {
            "document_type": "tax_invoice",
            "vat": "7",
            "seller_tax": OTHER_TAX,  # clean 13 位,非自家
            "buyer_tax": "",
            "seller_name": ALIAS_EN,
        }
        kind, reason = sort_step.bin_ocr_fields(
            fields, own_tax_id=OWN_TAX, own_names=[LEGAL_ENTRY, ALIAS_ENTRY]
        )
        self.assertEqual(kind, "unknown")
        self.assertTrue(reason.startswith(DIRECTION_AMBIGUOUS))
        self.assertIn("conflict", reason)


class G1R2ReplayTests(unittest.TestCase):
    """Ocha 真语料回放:≥3 种英文商号形态,无别名=ambiguous,加别名=锚回自家销项。"""

    def test_without_alias_all_forms_stay_ambiguous(self):
        for form in OCHA_SELLER_FORMS:
            kind, reason = sort_step.bin_ocr_fields(
                _ocha_receipt(form), own_tax_id=OWN_TAX, own_names=[LEGAL_ENTRY]
            )
            self.assertEqual((kind, reason), ("unknown", DIRECTION_AMBIGUOUS), msg=f"form={form!r}")

    def test_with_alias_all_forms_anchor_back_to_sales(self):
        for form in OCHA_SELLER_FORMS:
            kind, reason = sort_step.bin_ocr_fields(
                _ocha_receipt(form), own_tax_id=OWN_TAX, own_names=[LEGAL_ENTRY, ALIAS_ENTRY]
            )
            self.assertEqual(
                (kind, reason),
                ("unknown", SALES_DIRECTION_UNHANDLED),
                msg=f"form={form!r}",
            )


class _FakeItemStore:
    def __init__(self, items):
        self.items = items
        self.events = []

    def list_items(self, cur, *, tenant_id, work_order_id, status=None):
        return [dict(it) for it in self.items if status is None or it["status"] == status]

    def update_item(self, cur, *, tenant_id, item_id, status=None, kind=None, flag_reason=None):
        it = next(i for i in self.items if i["id"] == item_id)
        it["status"] = status
        it["kind"] = kind if kind is not None else it["kind"]
        it["flag_reason"] = flag_reason

    def append_event(
        self,
        cur,
        *,
        tenant_id,
        work_order_id,
        step,
        event_type,
        payload=None,
        actor="system",
        dedupe_key=None,
    ):
        self.events.append({"event_type": event_type, "payload": payload or {}})

    def by_id(self, item_id):
        return next(i for i in self.items if i["id"] == item_id)


def _item(item_id, file_ref):
    return {
        "id": item_id,
        "file_ref": file_ref,
        "kind": "unknown",
        "status": "pending",
        "flag_reason": None,
    }


def _ctx(store):
    return StepContext(cur=None, tenant_id="t-1", work_order_id="wo-1", store=store, data={})


class ClassifyFlagWiringTests(unittest.TestCase):
    """classify 接线:闸开走名集锚(别名生效),闸关走单名现状路(别名不参与)。"""

    def setUp(self):
        classify._resolve_own_tax_id = lambda ctx: OWN_TAX
        self.addCleanup(
            setattr, classify, "_resolve_own_tax_id", classify._default_resolve_own_tax_id
        )
        self.addCleanup(setattr, classify, "_resolve_own_name", classify._default_resolve_own_name)
        self.addCleanup(
            setattr, classify, "_resolve_own_names", classify._default_resolve_own_names
        )
        self.addCleanup(setattr, classify, "_m1_enabled", classify._default_m1_enabled)
        self.addCleanup(setattr, classify, "_ocr_image", classify._default_ocr_image)

    def test_flag_on_uses_alias_set_and_anchors_ocha_to_sales(self):
        classify._m1_enabled = lambda ctx: True
        classify._resolve_own_names = lambda ctx: [LEGAL_ENTRY, ALIAS_ENTRY]
        # 单名路若被误用会抛,坐实闸开只走名集路。
        classify._resolve_own_name = lambda ctx: (_ for _ in ()).throw(
            AssertionError("单名路不该被调")
        )
        classify._ocr_image = lambda path: _ocha_receipt(ALIAS_EN)

        store = _FakeItemStore([_item("i1", "/in/IMG_ocha.jpg")])
        classify.run(_ctx(store))

        row = store.by_id("i1")
        self.assertEqual(row["kind"], "unknown")
        self.assertEqual(row["flag_reason"], SALES_DIRECTION_UNHANDLED)

    def test_flag_off_uses_single_legal_name_and_stays_ambiguous(self):
        classify._m1_enabled = lambda ctx: False
        classify._resolve_own_name = lambda ctx: THAI_LEGAL
        # 名集路若被误用会抛,坐实闸关只走单名现状路(别名不参与)。
        classify._resolve_own_names = lambda ctx: (_ for _ in ()).throw(
            AssertionError("名集路不该被调")
        )
        classify._ocr_image = lambda path: _ocha_receipt(ALIAS_EN)

        store = _FakeItemStore([_item("i1", "/in/IMG_ocha.jpg")])
        classify.run(_ctx(store))

        row = store.by_id("i1")
        self.assertEqual(row["kind"], "unknown")
        self.assertEqual(row["flag_reason"], DIRECTION_AMBIGUOUS)


if __name__ == "__main__":
    unittest.main(verbosity=2)
