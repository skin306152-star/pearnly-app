# -*- coding: utf-8 -*-
"""CLI 端到端(合成 xlsx · 上传→猜列→校验→三产出)。金标真链本地跑,见汇报。"""

import tempfile
import unittest
from pathlib import Path

from openpyxl import Workbook

from services.payroll import cli


def _valid_id(prefix12: str) -> str:
    total = sum(int(prefix12[i]) * (13 - i) for i in range(12))
    return prefix12 + str((11 - total % 11) % 10)


_PAYER = _valid_id("010554808241")
_EMP = [_valid_id(p) for p in ("365010069742", "110420000252")]


def _write_xlsx(path: Path) -> None:
    wb = Workbook()
    ws = wb.active
    ws.append(
        [
            "รหัสเงินได้",
            "ลำดับ",
            "ผู้หัก",
            "เลข 13 หลัก",
            "คำนำหน้า",
            "ชื่อ",
            "นามสกุล",
            "วันที่จ่าย",
            "จำนวนเงิน",
            "ภาษีหัก",
            "เงื่อนไข",
        ]
    )
    ws.append(["40(1)", 1, _PAYER, _EMP[0], "นางสาว", "สมหญิง", "ใจดี", 31052569, 13000, 0, 1])
    ws.append(["40(1)", 2, _PAYER, _EMP[1], "นาย", "สมชาย", "รักงาน", 31052569, 12040, 0, 1])
    ws.append([None, None, None, None, None, None, None, None, 25040, None, None])  # 合计行
    wb.save(path)


class CliEndToEndTests(unittest.TestCase):
    def test_full_run_writes_three_outputs(self):
        with tempfile.TemporaryDirectory() as d:
            in_path = Path(d) / "payroll.xlsx"
            out_dir = Path(d) / "out"
            _write_xlsx(in_path)

            code = cli.main([str(in_path), str(out_dir)])
            self.assertEqual(code, 0)  # 合成数据全过

            # 读字节:read_text 会做通用换行翻译("\r\n"→"\n"),掩盖上传件的精确 CR/LF。
            attach = (out_dir / "pnd1_attach.txt").read_bytes().decode("utf-8")
            self.assertTrue((out_dir / "pnd1_keying.xlsx").is_file())
            self.assertTrue((out_dir / "pnd1_central.txt").is_file())

            lines = attach.split("\r\n")
            self.assertEqual(lines[0], f"40(1)|1|{_EMP[0]}|นางสาว|สมหญิง|ใจดี|31052569|13000|0|1")
            self.assertEqual(len(lines), 2)  # 合计行不进产出

    def test_usage_error_returns_1(self):
        self.assertEqual(cli.main(["only-one-arg"]), 1)


if __name__ == "__main__":
    unittest.main()
