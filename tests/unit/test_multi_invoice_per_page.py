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
from services.ocr import invoice_grouper


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


def _page(idx, num, total="", sub="", vat="", **extra):
    """1 页原始 dict(legacy_adapter 落库形态)· 只填 grouper 关心的字段。"""
    fields = {"invoice_number": num, "total_amount": total, "subtotal": sub, "vat": vat}
    fields.update(extra)
    return {"page_index": idx, "page_number": idx, "fields": fields}


class PackedMultiInvoiceBoundaryTests(unittest.TestCase):
    """打包多票 PDF 不再塌成 1 张(grouper 边界分组回归)。

    根因:旧策略1 把所有「没读出发票号」的页无条件并入第一组 → 另一张打包票的号一旦
    没读到,整张票被静默吞进第一张、金额一并蒸发(N 张 → 1 张)。修复:自带完整钱块
    (总额+税基/税额)的无号页判为独立发票,续页(仅带结尾总额)仍并入当前票。
    """

    def test_packed_multi_invoice_missing_number_still_splits(self):
        # (b) 打包多票:第 2 张的号没读到,但它自带 subtotal/vat/total → 必须仍是 2 张,
        # 且被吞过的那张金额(4001.80)不能丢。这是「塌成 1 张」的直接回归锚。
        pages = [
            _page(1, "IV69100179", total="2889.00", sub="2700.00", vat="189.00", buyer_name="A"),
            _page(2, None, total="4001.80", sub="3740.00", vat="261.80", buyer_name="B"),
        ]
        groups = invoice_grouper.group_pages_to_invoices(pages)
        self.assertEqual(len(groups), 2)
        totals = sorted((g["invoice_fields"].get("total_amount") or "") for g in groups)
        self.assertEqual(totals, ["2889.00", "4001.80"])

    def test_packed_three_invoices_all_numbered_split_to_three(self):
        # (b) 全部读到号的正常打包三票 → 3 张(happy path 保持)
        pages = [
            _page(1, "IV69100179", total="2889.00", sub="2700.00", vat="189.00"),
            _page(2, "IV69100189", total="4001.80", sub="3740.00", vat="261.80"),
            _page(3, "IV69/00199", total="706.20", sub="660.00", vat="46.20"),
        ]
        groups = invoice_grouper.group_pages_to_invoices(pages)
        self.assertEqual(len(groups), 3)

    def test_single_invoice_one_page_stays_one(self):
        # (a) 单票单页 → 1 张
        groups = invoice_grouper.group_pages_to_invoices(
            [_page(1, "IV69100179", total="2889.00", sub="2700.00", vat="189.00")]
        )
        self.assertEqual(len(groups), 1)

    def test_single_invoice_spanning_two_pages_stays_one(self):
        # (a) 单票跨两页:结尾总额印在末页(续页只有 total、没有自己的 subtotal/vat)
        # → 续页并入,仍是 1 张(不能被误拆)。
        pages = [
            _page(1, "IV69100179", total="", sub="2700.00", vat="189.00", buyer_name="A"),
            _page(2, None, total="2889.00"),  # 续页:仅结尾总额
        ]
        groups = invoice_grouper.group_pages_to_invoices(pages)
        self.assertEqual(len(groups), 1)
        self.assertEqual(sorted(groups[0]["page_indices"]), [1, 2])

    def test_continuation_repeating_summary_block_stays_one(self):
        # (a) 续页把汇总块(总额+税基+税额)整段重复打印、但没重复号 → 总额与首页相同,
        # 重复汇总护栏认出这是同一张票,不误拆成 2 张。
        pages = [
            _page(1, "IV69100179", total="2889.00", sub="2700.00", vat="189.00"),
            _page(2, None, total="2889.00", sub="2700.00", vat="189.00"),
        ]
        groups = invoice_grouper.group_pages_to_invoices(pages)
        self.assertEqual(len(groups), 1)


if __name__ == "__main__":
    unittest.main()
