#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/integration/test_excel_charge_units_safety_net.py · REFACTOR-WC

Excel/CSV 扣费字符数安全网 · 纯加测试不改业务 · 给 A 拆高敏 billing 当保险。

锁定 services/billing/charge._excel_char_count_estimate —— Excel/CSV/Word 上传的
「扣费 units」由它算出,再喂给 estimate_excel_cost_thb 换算 THB。这是 Excel 计费链的
输入端:文件 bytes → 字符数 → satang → THB。若重构把「数字符」写成「数字节」,
泰文/中文客户会被多收 3 倍(1 字 = 3 字节)。本测试锁住字符口径 + 端到端金额。

覆盖维度(对应 loop「OCR 扣费 · 金额对」· units 层):
  1. 文本类(csv/tsv/txt)= 解码后字符数(非字节数)· 多字节按「字」计
  2. 退化输入 = 0(空 bytes / 未知扩展名 / 无文件名)· 不乱收
  3. 端到端 = 文件 → 字符 → estimate_excel_cost_thb 的金额闭合
  4. xlsx(env-gated · openpyxl 在才跑)= 各单元格 str 长度求和
"""

from __future__ import annotations

import io
import sys
import unittest
from decimal import Decimal
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _load():
    try:
        from services.billing.charge import _excel_char_count_estimate
        from services.billing.pricing import estimate_excel_cost_thb
    except Exception as e:  # pragma: no cover - import 环境问题才触发
        raise unittest.SkipTest(f"services.billing 不可 import:{e}")
    return _excel_char_count_estimate, estimate_excel_cost_thb


class TextFileCharCountTest(unittest.TestCase):
    """文本类(csv/tsv/txt)· 字符数 = utf-8 解码后长度"""

    def setUp(self) -> None:
        self.est, _ = _load()

    def test_csv_ascii_char_count(self) -> None:
        self.assertEqual(self.est(b"hello,world", "data.csv"), 11)

    def test_txt_char_count(self) -> None:
        self.assertEqual(self.est(b"abc", "note.txt"), 3)

    def test_tsv_char_count(self) -> None:
        self.assertEqual(self.est(b"a\tb\tc", "x.tsv"), 5)

    def test_multibyte_counts_characters_not_bytes(self) -> None:
        # 泰文 3 字 = 9 字节(utf-8)· 必须按「3 字」计费 · 不能按 9 字节(否则多收 3 倍)
        thai = "กขค"
        self.assertEqual(len(thai.encode("utf-8")), 9)  # 前提:确实 3 字节/字
        self.assertEqual(self.est(thai.encode("utf-8"), "th.csv"), 3)

    def test_chinese_multibyte_char_count(self) -> None:
        zh = "中文发票"  # 4 字
        self.assertEqual(self.est(zh.encode("utf-8"), "inv.csv"), 4)


class DegenerateInputCharCountTest(unittest.TestCase):
    """退化输入 → 0 · 绝不在无法识别时乱收费"""

    def setUp(self) -> None:
        self.est, _ = _load()

    def test_empty_bytes_zero(self) -> None:
        self.assertEqual(self.est(b"", "x.csv"), 0)

    def test_unknown_extension_zero(self) -> None:
        # 未知扩展名 · 不在文本/xlsx/docx 分支 → 0(不瞎估)
        self.assertEqual(self.est(b"whatever", "file.bin"), 0)

    def test_none_filename_zero(self) -> None:
        self.assertEqual(self.est(b"abc", None), 0)

    def test_empty_filename_zero(self) -> None:
        self.assertEqual(self.est(b"abc", ""), 0)


class EndToEndUnitsToCostTest(unittest.TestCase):
    """端到端:文件 bytes → 字符数 → estimate_excel_cost_thb 金额闭合"""

    def setUp(self) -> None:
        self.est, self.cost = _load()

    def test_100_char_csv_costs_2_satang(self) -> None:
        # 100 字符 → ceil(100/50)=2 satang = 0.02 THB
        chars = self.est(b"x" * 100, "big.csv")
        self.assertEqual(chars, 100)
        self.assertEqual(self.cost(chars), Decimal("0.02"))

    def test_exactly_50_char_csv_costs_1_satang(self) -> None:
        chars = self.est(b"y" * 50, "half.csv")
        self.assertEqual(chars, 50)
        self.assertEqual(self.cost(chars), Decimal("0.01"))

    def test_empty_file_costs_zero(self) -> None:
        chars = self.est(b"", "empty.csv")
        self.assertEqual(self.cost(chars), Decimal("0.00"))


class XlsxCharCountTest(unittest.TestCase):
    """xlsx 路径 · 各非空单元格 str 长度求和(env-gated · openpyxl 在才跑)"""

    def setUp(self) -> None:
        self.est, _ = _load()
        try:
            import openpyxl  # noqa: F401
        except Exception as e:
            raise unittest.SkipTest(f"openpyxl 不可用 · xlsx 路径跳过:{e}")

    def _make_xlsx(self, cells) -> bytes:
        import openpyxl

        wb = openpyxl.Workbook()
        ws = wb.active
        for coord, value in cells.items():
            ws[coord] = value
        buf = io.BytesIO()
        wb.save(buf)
        return buf.getvalue()

    def test_text_and_number_cells_summed(self) -> None:
        # 'hello'(5) + 12345(str 后 5)= 10
        data = self._make_xlsx({"A1": "hello", "B1": 12345})
        self.assertEqual(self.est(data, "book.xlsx"), 10)

    def test_empty_cells_ignored(self) -> None:
        # 只 1 个非空单元格 'abc' = 3 · 空单元格不计
        data = self._make_xlsx({"A1": "abc"})
        self.assertEqual(self.est(data, "sparse.xlsx"), 3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
