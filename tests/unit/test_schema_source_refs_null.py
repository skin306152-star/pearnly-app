# -*- coding: utf-8 -*-
"""守门测试 · ThaiInvoice.source_refs 的 null 容错(2026-05-26 Codex 验收 qa_3 根因)

真实踩坑:Gemini 返回 source_refs = {"vat": null, "total": {...}} 时,
旧 _coerce_source_refs 只防「整个 source_refs=null」,没防「个别字段=null」,
于是 pydantic 报 `source_refs.vat Input should be a valid dictionary` → 整份 PDF 400。

修法:dict 内只保留值为 dict(可构造 FieldRef)的条目,null / 标量 / list 一律丢弃。
"""

import unittest

from services.ocr.schemas import ThaiInvoice
from services.ocr.schemas_layer1 import FieldRef


class FieldRefNullToleranceTests(unittest.TestCase):
    """守门:FieldRef 内层标量字段 = null 须容忍(2026-06-24 真因 · LINE 清晰收据被误判「读不清」)。

    真实事故:Gemini 对无表格列的简单收据返 source_refs.subtotal.source_column=null,
    旧 _coerce_source_refs 只防「source_refs[key] 整个=null」,放行了合法 dict;FieldRef
    构造时 source_column 显式 null 绕过 Field(default='') → ThaiInvoice 校验失败 → 整票回
    ocr_failed「读不清」让重拍。
    """

    def test_inner_scalar_nulls_coerced_to_default(self):
        f = FieldRef(
            value="70.00", source_text=None, source_column=None, source_page=None, confidence=None
        )
        self.assertEqual(f.source_text, "")
        self.assertEqual(f.source_column, "")
        self.assertEqual(f.source_page, 0)
        self.assertEqual(f.confidence, 0.0)

    def test_normal_values_kept(self):
        f = FieldRef(value="70.00", source_column="รวม", confidence=0.9)
        self.assertEqual(f.source_column, "รวม")
        self.assertEqual(f.confidence, 0.9)

    def test_invoice_with_inner_null_source_column_does_not_400(self):
        inv = ThaiInvoice(
            invoice_number="IV1",
            source_refs={
                "subtotal": {"value": "70", "source_text": "70.00", "source_column": None}
            },
        )
        self.assertIn("subtotal", inv.source_refs)
        self.assertEqual(inv.source_refs["subtotal"].source_column, "")


class PaymentMethodNullToleranceTests(unittest.TestCase):
    """守门:LLM 常对没印付款方式的票返 payment_method=null。str 字段须容忍 None→''(否则整页 OCR 挂)。

    真实事故(2026-06-17):新增 payment_method:str 漏进 _coerce_to_str → null 触发
    ThaiInvoice schema 校验失败 → 整张票回「ไม่ครบ」让重拍。
    """

    def test_null_payment_method_coerced_to_empty(self):
        inv = ThaiInvoice(seller_name="x", payment_method=None)
        self.assertEqual(inv.payment_method, "")

    def test_value_kept(self):
        self.assertEqual(ThaiInvoice(seller_name="x", payment_method="qr").payment_method, "qr")


class SourceRefsNullToleranceTests(unittest.TestCase):
    def test_whole_source_refs_null(self):
        """case 1:整个 source_refs = null → 不炸,变 {}。"""
        inv = ThaiInvoice(invoice_number="IV1", source_refs=None)
        self.assertEqual(inv.source_refs, {})

    def test_individual_field_null_does_not_400(self):
        """case 2(qa_3 真因):个别字段 = null → 丢掉该键,其余保留,不抛异常。"""
        inv = ThaiInvoice(
            invoice_number="IV2",
            source_refs={
                "vat": None,
                "total_amount": {"value": "107", "source_text": "107.00"},
            },
        )
        # vat 被丢弃(null 不是合法 FieldRef),total_amount 正常保留并解析为 FieldRef
        self.assertNotIn("vat", inv.source_refs)
        self.assertIn("total_amount", inv.source_refs)
        self.assertEqual(inv.source_refs["total_amount"].value, "107")

    def test_scalar_and_list_values_dropped(self):
        """标量 / list 值也不是合法 FieldRef → 丢弃,不炸。"""
        inv = ThaiInvoice(
            invoice_number="IV3",
            source_refs={"vat": "123", "subtotal": [1, 2], "date": {"source_text": "2026-01-01"}},
        )
        self.assertEqual(set(inv.source_refs.keys()), {"date"})

    def test_empty_dict_fieldref_ok(self):
        """空 dict 是合法 FieldRef(全字段有默认值)→ 保留。"""
        inv = ThaiInvoice(invoice_number="IV4", source_refs={"vat": {}})
        self.assertIn("vat", inv.source_refs)


if __name__ == "__main__":
    unittest.main()
