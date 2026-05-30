#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_ocr_page_to_text.py · REFACTOR-WA-COV5

域:services/ocr/layer2_structure.py::_page_to_text(此前 0 测试 · 最后一个未测 OCR 纯 helper)

为啥(OCR 表格文档安全网 · 0 逻辑改只加测):
  _page_to_text 把一页 Page 序列化成 Layer 2 LLM 的输入文本。表格文档(Excel/CSV/Word/
  table_path)走「管道分隔网格」分支——表头一行 + 每行按【表头顺序】取单元格。若这格式坏了
  (漏表头/单元格错位/丢列),LLM 看到的就是错位表格 → 抽错发票字段。非表格页用 full_text 原样。
  锁:表格分支(表头顺序 / 缺单元格补空 / 非字符串转 str / 多行)· 非表格分支(full_text)·
  table_headers 为 None 即便有 table_rows 也走 full_text(两者都需非 None)。

纯逻辑 · 无 DB / 无网络 · CI 必跑不 skip。依据 2026-05-30 实读 _page_to_text 真实实现。
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.ocr.layer2_structure import _page_to_text  # noqa: E402
from services.ocr.schemas import Page  # noqa: E402


def _page(**kw):
    base = dict(page_number=1, width=0, height=0, full_text="", avg_confidence=1.0, blocks=[])
    base.update(kw)
    return Page(**base)


class PageToTextTest(unittest.TestCase):
    def test_plain_page_uses_full_text(self) -> None:
        p = _page(full_text="hello invoice text")
        self.assertEqual(_page_to_text(p), "hello invoice text")

    def test_table_serializes_pipe_grid(self) -> None:
        p = _page(
            full_text="ignored when table present",
            table_headers=["Date", "Amount"],
            table_rows=[{"Date": "2024-01-02", "Amount": "100"}],
        )
        self.assertEqual(_page_to_text(p), "Date | Amount\n2024-01-02 | 100")

    def test_table_uses_header_order_not_dict_order(self) -> None:
        # 按 table_headers 顺序取格 · 不是 dict 插入顺序
        p = _page(table_headers=["B", "A"], table_rows=[{"A": "1", "B": "2"}])
        self.assertEqual(_page_to_text(p), "B | A\n2 | 1")

    def test_missing_cell_becomes_empty(self) -> None:
        p = _page(table_headers=["A", "B"], table_rows=[{"A": "x"}])
        self.assertEqual(_page_to_text(p), "A | B\nx | ")

    def test_non_string_cells_coerced(self) -> None:
        p = _page(table_headers=["A", "B"], table_rows=[{"A": 123, "B": 4.5}])
        self.assertEqual(_page_to_text(p), "A | B\n123 | 4.5")

    def test_multiple_rows(self) -> None:
        p = _page(
            table_headers=["A", "B"],
            table_rows=[{"A": "1", "B": "2"}, {"A": "3", "B": "4"}],
        )
        self.assertEqual(_page_to_text(p), "A | B\n1 | 2\n3 | 4")

    def test_headers_none_falls_back_to_full_text(self) -> None:
        # 有 table_rows 但 table_headers 为 None → 两者都需非 None · 走 full_text
        p = _page(full_text="fallback", table_rows=[{"A": "1"}], table_headers=None)
        self.assertEqual(_page_to_text(p), "fallback")


if __name__ == "__main__":
    unittest.main(verbosity=2)
