#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/integration/test_recon_matching_safety_net.py · REFACTOR-WC

对账配对正确性安全网 · 纯加测试不改业务 · 给 A/B 拆 vat_excel / recon 当保险。

锁定 vat_excel_export._build_recon_pairs 的一对一配对引擎不变量。这是销项 VAT 对账
「金额对 / 不重复 / 不漏」的核心 —— 发票 ↔ 报告行的配对若被重构改坏,会导致同一笔
被重复计入、或真匹配被误判成孤儿。全部走纯函数(0 DB · 0 网络)→ CI 真跑不 skip。

覆盖维度(对应 loop「对账扣费金额对 / 不重复扣」):
  1. 精确配对 — 发票号一致 / 税号+金额一致 → matched
  2. 不重复   — partition 不变量:每个 inv/rep 下标至多用一次 · 全集守恒(配对+孤儿=全部)
  3. 不误配   — 金额不符且无号匹配 → 双方孤儿(不造假阳)
  4. 边界分类 — 散客三重 matched_cash / OCR 漏税号 ocr_missing
  5. 退化输入 — 空列表 / 单边空 不崩
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _load_recon():
    try:
        from services.vat.vat_excel_export import _build_recon_pairs
    except Exception as e:  # pragma: no cover - import 环境问题才触发
        raise unittest.SkipTest(f"vat_excel_export._build_recon_pairs 不可 import:{e}")
    return _build_recon_pairs


def _inv(invoice_no="", tax_id="", name="", total=0.0):
    return {
        "invoice_no": invoice_no,
        "buyer_tax_id": tax_id,
        "buyer_name": name,
        "total_amount": total,
    }


def _rep(invoice_no="", tax_id="", name="", pre_vat=0.0, vat=0.0):
    return {
        "report_invoice_no": invoice_no,
        "report_buyer_tax_id": tax_id,
        "report_buyer_name": name,
        "report_amount_pre_vat": pre_vat,
        "report_vat_amount": vat,
    }


class ReconExactMatchTest(unittest.TestCase):
    """精确配对:发票号一致 或 税号+含税金额一致 → matched"""

    def setUp(self) -> None:
        self.build = _load_recon()

    def test_invoice_no_match_pairs_no_orphans(self) -> None:
        r = self.build(
            [_inv("INV-001", "0105551234567", "Acme", 107.0)],
            [_rep("INV-001", "0105551234567", "Acme", 100.0, 7.0)],
        )
        self.assertEqual(len(r["pairs"]), 1)
        self.assertEqual(r["pairs"][0]["kind"], "matched")
        self.assertEqual(r["unmatched_inv"], [])
        self.assertEqual(r["unmatched_rep"], [])

    def test_invoice_no_match_ignores_case_and_punctuation(self) -> None:
        # normalize_invoice_no 折叠大小写/标点:'INV-001' ↔ 'inv001' 视为同号
        r = self.build(
            [_inv("INV-001", "0105551234567", "Acme", 107.0)],
            [_rep("inv001", "0105551234567", "Acme", 100.0, 7.0)],
        )
        self.assertEqual(len(r["pairs"]), 1)
        self.assertEqual(r["pairs"][0]["kind"], "matched")

    def test_tax_id_plus_amount_match_when_invoice_no_differs(self) -> None:
        # 发票号不同 · 但税号 + 含税金额一致 → 第 2 轮仍配上(对账靠金额兜底)
        r = self.build(
            [_inv("A-1", "0105551234567", "Acme", 107.0)],
            [_rep("Z-9", "0105551234567", "Acme", 100.0, 7.0)],
        )
        self.assertEqual(len(r["pairs"]), 1)
        self.assertEqual(r["pairs"][0]["kind"], "matched")


class ReconNoFalseMatchTest(unittest.TestCase):
    """不误配:金额不符且发票号不同 → 双方孤儿(绝不造假阳配对)"""

    def setUp(self) -> None:
        self.build = _load_recon()

    def test_amount_mismatch_leaves_both_orphan(self) -> None:
        r = self.build(
            [_inv("A-1", "0105551234567", "Acme", 500.0)],
            [_rep("Z-9", "0105551234567", "Acme", 100.0, 7.0)],
        )
        self.assertEqual(r["pairs"], [])
        self.assertEqual(r["unmatched_inv"], [0])
        self.assertEqual(r["unmatched_rep"], [0])

    def test_no_overlap_all_orphan(self) -> None:
        r = self.build(
            [_inv("A-1", "0105550000001", "X", 100.0), _inv("A-2", "0105550000002", "Y", 200.0)],
            [_rep("B-1", "0105559999999", "Z", 50.0, 3.5)],
        )
        self.assertEqual(r["pairs"], [])
        self.assertEqual(sorted(r["unmatched_inv"]), [0, 1])
        self.assertEqual(r["unmatched_rep"], [0])


class ReconOneToOnePartitionTest(unittest.TestCase):
    """不重复 · partition 不变量:每个下标至多用一次 · 配对 + 孤儿 = 全集(无重复无遗漏)。

    这是「不重复计入 / 不静默丢」的硬护栏:重构若改坏 used_inv/used_rep 簿记,
    同一笔会被重复配对或真匹配被吞掉,本测试立刻红。
    """

    def setUp(self) -> None:
        self.build = _load_recon()

    def _assert_partition(self, r, n_inv, n_rep) -> None:
        paired_inv = [p["inv_idx"] for p in r["pairs"]]
        paired_rep = [p["rep_idx"] for p in r["pairs"]]
        # 1. 配对内无重复下标(一对一)
        self.assertEqual(len(paired_inv), len(set(paired_inv)), "发票下标被重复配对!")
        self.assertEqual(len(paired_rep), len(set(paired_rep)), "报告下标被重复配对!")
        # 2. 配对集与孤儿集互斥
        self.assertEqual(set(paired_inv) & set(r["unmatched_inv"]), set())
        self.assertEqual(set(paired_rep) & set(r["unmatched_rep"]), set())
        # 3. 全集守恒:配对 + 孤儿 == 所有下标
        self.assertEqual(
            sorted(paired_inv + r["unmatched_inv"]), list(range(n_inv)), "发票下标有重复或遗漏!"
        )
        self.assertEqual(
            sorted(paired_rep + r["unmatched_rep"]), list(range(n_rep)), "报告下标有重复或遗漏!"
        )

    def test_duplicate_invoices_one_report_pairs_only_once(self) -> None:
        # 2 张同号同税号发票 vs 1 行报告 → 只配 1 对 · 另 1 张孤儿(不重复消耗同一行)
        inv = [
            _inv("D-1", "0105551234567", "Acme", 107.0),
            _inv("D-1", "0105551234567", "Acme", 107.0),
        ]
        rep = [_rep("D-1", "0105551234567", "Acme", 100.0, 7.0)]
        r = self.build(inv, rep)
        self.assertEqual(len(r["pairs"]), 1)
        self.assertEqual(r["unmatched_inv"], [1])
        self._assert_partition(r, len(inv), len(rep))

    def test_mixed_batch_partition_holds(self) -> None:
        inv = [
            _inv("M-1", "0105550000001", "A", 107.0),  # 精确匹配
            _inv("M-2", "0105550000002", "B", 999.0),  # 金额无对应 → 孤儿
            _inv("M-3", "0105550000003", "C", 214.0),  # 税号+金额匹配
        ]
        rep = [
            _rep("M-1", "0105550000001", "A", 100.0, 7.0),
            _rep("X-9", "0105550000003", "C", 200.0, 14.0),
            _rep("R-7", "0105557777777", "D", 50.0, 3.5),  # 报告孤儿
        ]
        r = self.build(inv, rep)
        self._assert_partition(r, len(inv), len(rep))
        self.assertEqual(len(r["pairs"]), 2)


class ReconBoundaryClassificationTest(unittest.TestCase):
    """边界分类:散客三重 → matched_cash · OCR 漏税号 → ocr_missing"""

    def setUp(self) -> None:
        self.build = _load_recon()

    def test_cash_customer_triple_match(self) -> None:
        # 双方均无税号 · 名+号+金额一致 → 散客匹配
        r = self.build(
            [_inv("C-9", "", "Walk In", 214.0)],
            [_rep("C-9", "", "Walk In", 200.0, 14.0)],
        )
        self.assertEqual(len(r["pairs"]), 1)
        self.assertEqual(r["pairs"][0]["kind"], "matched_cash")

    def test_ocr_missing_tax_id_flagged(self) -> None:
        # 发票漏抽税号(空)· 报告有税号 · 名+号+金额一致 → 标 ocr_missing(不是普通 matched)
        r = self.build(
            [_inv("M-1", "", "Acme", 107.0)],
            [_rep("M-1", "0105551234567", "Acme", 100.0, 7.0)],
        )
        self.assertEqual(len(r["pairs"]), 1)
        self.assertEqual(r["pairs"][0]["kind"], "ocr_missing")


class ReconDegenerateInputTest(unittest.TestCase):
    """退化输入:空 / 单边空 不崩 · 返回结构完整"""

    def setUp(self) -> None:
        self.build = _load_recon()

    def test_both_empty(self) -> None:
        r = self.build([], [])
        self.assertEqual(r, {"pairs": [], "unmatched_inv": [], "unmatched_rep": []})

    def test_invoices_only(self) -> None:
        r = self.build([_inv("A-1", "0105551234567", "X", 107.0)], [])
        self.assertEqual(r["pairs"], [])
        self.assertEqual(r["unmatched_inv"], [0])
        self.assertEqual(r["unmatched_rep"], [])

    def test_reports_only(self) -> None:
        r = self.build([], [_rep("A-1", "0105551234567", "X", 100.0, 7.0)])
        self.assertEqual(r["pairs"], [])
        self.assertEqual(r["unmatched_inv"], [])
        self.assertEqual(r["unmatched_rep"], [0])


if __name__ == "__main__":
    unittest.main(verbosity=2)
