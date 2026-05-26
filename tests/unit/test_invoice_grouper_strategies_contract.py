# -*- coding: utf-8 -*-
"""REFACTOR-D2 守门 · 多发票分页归组 invoice_grouper.py 策略契约

group_pages_to_invoices 此前仅 test_multi_invoice_per_page 覆盖「拆页 happy path」。
本测试补 3 个分组策略的边界(核心 OCR 功能 · 纯函数 · 零冲突):
  策略1 按 invoice_number 分组(同号多页合并 · 无号页归第一组)
  策略2 无发票号 → 按 total_amount 作发票结束页分界
  策略3 都没有 → 全部作一张(fallback)
"""

import unittest

import invoice_grouper as ig


def _p(idx=None, **fields):
    d = {"fields": fields}
    if idx is not None:
        d["page_index"] = idx
    return d


class EmptyTests(unittest.TestCase):
    def test_empty_returns_empty(self):
        self.assertEqual(ig.group_pages_to_invoices([]), [])


class Strategy1ByInvoiceNoTests(unittest.TestCase):
    def test_same_invoice_number_merges_pages(self):
        pages = [_p(invoice_number="A", total_amount="100"), _p(invoice_number="A")]
        groups = ig.group_pages_to_invoices(pages)
        self.assertEqual(len(groups), 1)
        self.assertEqual(sorted(groups[0]["page_indices"]), [1, 2])
        self.assertEqual(groups[0]["invoice_fields"].get("invoice_number"), "A")

    def test_different_numbers_split_in_first_seen_order(self):
        pages = [_p(invoice_number="B", total_amount="1"), _p(invoice_number="A", total_amount="2")]
        groups = ig.group_pages_to_invoices(pages)
        nums = [g["invoice_fields"].get("invoice_number") for g in groups]
        self.assertEqual(nums, ["B", "A"])  # 按首次出现顺序 · 非字母序

    def test_page_without_number_attaches_to_first_group(self):
        # 1 页有号 + 1 页无号(无号 ≤ 半数)→ 策略1 · 无号页并入第一组
        pages = [_p(invoice_number="A", total_amount="100"), _p()]
        groups = ig.group_pages_to_invoices(pages)
        self.assertEqual(len(groups), 1)
        self.assertEqual(sorted(groups[0]["page_indices"]), [1, 2])


class Strategy2ByTotalTests(unittest.TestCase):
    def test_total_amount_marks_invoice_boundary(self):
        # 无任何发票号 → 按 total 分界:有 total 的页是一张发票结束
        pages = [_p(), _p(total_amount="100"), _p(total_amount="200")]
        groups = ig.group_pages_to_invoices(pages)
        self.assertEqual(len(groups), 2)
        self.assertEqual(sorted(groups[0]["page_indices"]), [1, 2])  # 无 total 页并入下个 total 页
        self.assertEqual(sorted(groups[1]["page_indices"]), [3])

    def test_trailing_no_total_attaches_to_last(self):
        pages = [_p(total_amount="100"), _p()]  # 结尾无 total 页
        groups = ig.group_pages_to_invoices(pages)
        self.assertEqual(len(groups), 1)
        self.assertEqual(sorted(groups[0]["page_indices"]), [1, 2])


class Strategy3FallbackTests(unittest.TestCase):
    def test_no_number_no_total_all_one_invoice(self):
        pages = [_p(), _p()]
        groups = ig.group_pages_to_invoices(pages)
        self.assertEqual(len(groups), 1)
        self.assertEqual(sorted(groups[0]["page_indices"]), [1, 2])


if __name__ == "__main__":
    unittest.main()
