# -*- coding: utf-8 -*-
"""CSV 公式注入中和:危险前缀补单引号,纯数字与普通文本放行,伪装负数不放行。

安全评估 2026-07-07 · 见 services/export/csv_safe.py。
"""

from __future__ import annotations

import unittest

from services.export.csv_safe import safe_row


class CsvSafeTest(unittest.TestCase):
    def test_neutralizes_formula_prefixes(self) -> None:
        row = safe_row(["=1+1", "+1+2", "@SUM(A1)", "\tx", "\rx", "-1+9*cmd"])
        self.assertTrue(all(isinstance(c, str) and c.startswith("'") for c in row))

    def test_hyperlink_payload_neutralized(self) -> None:
        payload = '=HYPERLINK("http://evil","click")'
        self.assertEqual(safe_row([payload]), ["'" + payload])

    def test_preserves_plain_text_and_numbers(self) -> None:
        # 普通文本 / 纯数字(含负金额)/ 非字符串 一律原样
        row = ["Acme Co", "-100.50", "+42", "1,250.00", 5, None, "user@x.com"]
        self.assertEqual(safe_row(row), row)


if __name__ == "__main__":
    unittest.main()
