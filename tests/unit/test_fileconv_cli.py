# -*- coding: utf-8 -*-
"""fileconv CLI 控制台编码回归 · K1a-R1。

现场:泰文 Windows 控制台(stdout=cp874)跑成功路径,摘要里的 U+2192 等字符
UnicodeEncodeError,成功转换却退出 1。契约:任意控制台编码下打印永不崩溃,
退出码语义不变(0 守恒全过 / 2 有 issue / 3 no_text_layer / 1 用法错)。
"""

import io
import sys
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from services.fileconv import cli
from services.fileconv.model import ConvertResult, Issue, STATUS_OK, GL_LEDGER


def _ascii_strict_stdout() -> io.TextIOWrapper:
    """模拟编不了非 ASCII 的控制台(比 cp874 更严,盖住所有单字节编码)。"""
    return io.TextIOWrapper(io.BytesIO(), encoding="ascii", errors="strict", write_through=True)


def _result_with_thai_issue() -> ConvertResult:
    return ConvertResult(
        doc_type=GL_LEDGER,
        status=STATUS_OK,
        source_name="สมุดแยกประเภท.pdf",
        issues=[
            Issue(
                kind="gl_balance_chain",
                line_no=7,
                account="1113-01",
                message="ยอดคงเหลือ ไม่ตรง",
                expected="100.00",
                actual="99.00",
            )
        ],
        stats={"row_count": 1, "accounts": ["1113-01"], "closing_balance": "99.00"},
    )


class CliConsoleEncodingTests(unittest.TestCase):
    def _run_main(self, result: ConvertResult) -> int:
        with tempfile.TemporaryDirectory() as td:
            in_pdf = Path(td) / "in.pdf"
            in_pdf.write_bytes(b"%PDF-placeholder")
            out_xlsx = Path(td) / "out.xlsx"
            with (
                patch.object(cli, "convert_pdf", return_value=result),
                patch.object(cli, "build_xlsx", return_value=b"xlsx"),
                patch.object(sys, "stdout", _ascii_strict_stdout()),
            ):
                return cli.main([str(in_pdf), str(out_xlsx)])

    def test_success_path_survives_ascii_only_console(self):
        """摘要打印(含泰文 issue 点名)在纯 ASCII 控制台不崩,退出码仍按契约 = 2。"""
        rc = self._run_main(_result_with_thai_issue())
        self.assertEqual(rc, 2)

    def test_conserved_path_exits_zero_on_ascii_only_console(self):
        result = _result_with_thai_issue()
        result.issues = []
        rc = self._run_main(result)
        self.assertEqual(rc, 0)

    def test_decimal_stats_print_survives(self):
        result = _result_with_thai_issue()
        result.stats["sum_debit"] = f"{Decimal('920125.84')}"
        rc = self._run_main(result)
        self.assertEqual(rc, 2)


if __name__ == "__main__":
    unittest.main()
