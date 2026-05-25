# -*- coding: utf-8 -*-
"""P0 漏票 golden regression (Zihao 2026-05-26) · 同页多票不再静默漏识别。

复现背景:图片型 PDF 一页印 2 张发票(SINCERE.pdf 第 1 页 = IV69/00179 +
IV69/00189),旧 pipeline 一页只产 1 张 → 静默漏掉第 2 张。

本测试守 3 个确定性环节(不依赖 Gemini · CI 可跑):
1. ThaiInvoice schema 支持 additional_invoices(一页多票结构)。
2. legacy_adapter 把 additional_invoices 展开成多个 page 条目(主票 + 每张附加票)。
3. invoice_grouper 从展开后的 page 产出 N 张独立发票。
4. pipeline._count_invoice_no_candidates 兜底:页面发票号候选数的计数正确
   (候选 > 实际提取 → 上层标人工核对 · 防静默漏)。
"""

import unittest

from services.ocr.schemas import ThaiInvoice, PipelinePageResult, PipelineResult
from services.ocr.legacy_adapter import pipeline_result_to_legacy_dict
from services.ocr.pipeline import _count_invoice_no_candidates
import invoice_grouper


def _inv(no, total, buyer="", sub="", vat=""):
    return ThaiInvoice(
        invoice_number=no,
        total_amount=total,
        buyer_name=buyer,
        subtotal=sub,
        vat=vat,
    )


class MultiInvoicePerPageTests(unittest.TestCase):
    def test_schema_accepts_additional_invoices(self):
        inv = _inv("IV69/00179", "2889.00")
        inv.additional_invoices = [_inv("IV69/00189", "4001.80")]
        self.assertEqual(len(inv.additional_invoices), 1)
        self.assertEqual(inv.additional_invoices[0].invoice_number, "IV69/00189")
        # 嵌套层默认空 · 不递归
        self.assertEqual(inv.additional_invoices[0].additional_invoices, [])

    def test_legacy_adapter_flattens_additional_into_separate_pages(self):
        primary = _inv("IV69/00179", "2889.00", buyer="A", sub="2700.00", vat="189.00")
        primary.additional_invoices = [
            _inv("IV69/00189", "4001.80", buyer="B", sub="3740.00", vat="261.80")
        ]
        pr = PipelineResult(
            pages=[PipelinePageResult(page_number=1, invoice=primary)],
            page_count=1,
            elapsed_ms=10,
        )
        legacy = pipeline_result_to_legacy_dict(pr)
        # 1 物理页 → 2 个 legacy page 条目
        self.assertEqual(len(legacy["pages"]), 2)
        nums = [(p.get("fields") or {}).get("invoice_number") for p in legacy["pages"]]
        self.assertEqual(nums, ["IV69/00179", "IV69/00189"])
        # 两条都归属物理页 1
        self.assertTrue(all(p.get("page_number") == 1 for p in legacy["pages"]))
        # sibling 标记
        self.assertFalse(legacy["pages"][0]["_multi_invoice_sibling"])
        self.assertTrue(legacy["pages"][1]["_multi_invoice_sibling"])
        # fields 里不再带 additional_invoices(已展开 · 防 history 嵌套)
        self.assertNotIn("additional_invoices", legacy["pages"][0].get("fields") or {})

    def test_grouper_produces_one_invoice_per_flattened_page(self):
        """SINCERE 形态:页1主(179)+页1附(189)+页2(199) → 3 张发票。"""
        p1 = _inv("IV69/00179", "2889.00", buyer="A", sub="2700.00", vat="189.00")
        p1.additional_invoices = [
            _inv("IV69/00189", "4001.80", buyer="B", sub="3740.00", vat="261.80")
        ]
        p2 = _inv("IV69/00199", "706.20", buyer="C", sub="660.00", vat="46.20")
        pr = PipelineResult(
            pages=[
                PipelinePageResult(page_number=1, invoice=p1),
                PipelinePageResult(page_number=2, invoice=p2),
            ],
            page_count=2,
            elapsed_ms=10,
        )
        legacy = pipeline_result_to_legacy_dict(pr)
        groups = invoice_grouper.group_pages_to_invoices(legacy["pages"])
        nums = sorted((g["invoice_fields"].get("invoice_number") or "") for g in groups)
        self.assertEqual(nums, ["IV69/00179", "IV69/00189", "IV69/00199"])
        # 每张金额各自独立(不被合并)
        by_no = {g["invoice_fields"]["invoice_number"]: g["invoice_fields"] for g in groups}
        self.assertEqual(by_no["IV69/00179"]["total_amount"], "2889.00")
        self.assertEqual(by_no["IV69/00189"]["total_amount"], "4001.80")
        self.assertEqual(by_no["IV69/00199"]["total_amount"], "706.20")

    # ── 兜底计数器(防静默漏) ──────────────────────────────
    def test_candidate_count_detects_stacked_invoice(self):
        text = "ใบกำกับภาษี IV69/00179 ... ยอดรวม 2889.00 ใบกำกับภาษี IV69/00189 ยอดรวม 4001.80"
        self.assertEqual(_count_invoice_no_candidates(text, "IV69/00179"), 2)

    def test_candidate_count_single_invoice(self):
        text = "ใบกำกับภาษี IV69/00199 ยอดรวม 706.20"
        self.assertEqual(_count_invoice_no_candidates(text, "IV69/00199"), 1)

    def test_candidate_count_dedupes_repeated_same_number(self):
        # 同一发票号在页眉+页脚各印一次 → 仍算 1 张
        text = "IV69/00179 header ... footer IV69/00179"
        self.assertEqual(_count_invoice_no_candidates(text, "IV69/00179"), 1)

    def test_candidate_count_pure_alpha_no_digit_returns_zero(self):
        # 纯字母发票号 → 不数(正则会过度匹配)
        self.assertEqual(_count_invoice_no_candidates("ABC ABC", "ABC"), 0)

    def test_candidate_count_empty_safe(self):
        self.assertEqual(_count_invoice_no_candidates("", "IV69/00179"), 0)
        self.assertEqual(_count_invoice_no_candidates("text", ""), 0)


if __name__ == "__main__":
    unittest.main()
