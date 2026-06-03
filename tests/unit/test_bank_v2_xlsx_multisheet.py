# -*- coding: utf-8 -*-
"""
v118.35.0.55 · 守门测试 · 银行流水 Excel 多 sheet + 旧.xls + 单一带符号金额列

真实案例(skin 实测 KTB 8258&8606):
- 一个文件 2 个 sheet = 2 个账户(用户可能塞 10 个)→ 需遍历所有 sheet
- 表头在第 11 行(超出旧的前 10 行扫描窗口)
- 单一带符号 Amount 列(正=存 负=取)· 非独立存/取列
- 关键 bug:"in" 子串命中 "Init Br." 分行号列 → 当成存款列 → 金额全错

锁定契约:
  1. _hit 短词整词匹配:"in" 不命中 "Init Br." · 但命中独立 "IN"
  2. KTB 表头映射出 amount 列(不是把 "Init Br." 当 deposit)
  3. 多 sheet 工作簿 → 所有 sheet 的行都被解析合并
  4. 带符号金额 → 正存负取
"""

import io
import unittest

import openpyxl

from services.recon.bank_recon_v2 import _hit, _map_bank_stmt_cols, parse_bank_stmt_xlsx_direct
from services.recon.bank_recon_v2 import _STMT_DEPOSIT_H


class HitWholeWordTests(unittest.TestCase):

    def test_in_not_match_init(self):
        self.assertFalse(_hit("Init Br.", _STMT_DEPOSIT_H), "'in' 不应子串命中 'Init Br.'")

    def test_in_matches_standalone(self):
        self.assertTrue(_hit("IN", _STMT_DEPOSIT_H), "独立 'IN' 应命中存款")

    def test_long_keyword_substring_ok(self):
        self.assertTrue(_hit("Total Deposit", _STMT_DEPOSIT_H), "长词 deposit 子串仍命中")


class KtbHeaderMapTests(unittest.TestCase):

    def test_ktb_header_maps_amount_not_initbr(self):
        header = [
            "Date",
            "Teller Id",
            "Transaction Code",
            "Description",
            "Cheque No.",
            "Amount",
            "Tax",
            "Balance",
            "Init Br.",
        ]
        cm = _map_bank_stmt_cols(header)
        self.assertEqual(cm.get("amount"), 5)
        self.assertEqual(cm.get("balance"), 7)
        self.assertNotIn("deposit", cm, "'Init Br.' 不应被当成存款列")


class MultiSheetXlsxTests(unittest.TestCase):

    def _build(self):
        wb = openpyxl.Workbook()
        for si, (acct, txns) in enumerate(
            [
                (
                    "ACC-1",
                    [
                        ("01/01/2026", "dep1", 1000.0, 11000.0),
                        ("02/01/2026", "wd1", -500.0, 10500.0),
                    ],
                ),
                (
                    "ACC-2",
                    [
                        ("01/01/2026", "dep2", 2000.0, 22000.0),
                        ("02/01/2026", "wd2", -700.0, 21300.0),
                    ],
                ),
            ]
        ):
            ws = wb.create_sheet(acct) if si else wb.active
            if si == 0:
                ws.title = acct
            ws.append(["Account No.", acct])
            ws.append([])
            ws.append([])
            ws.append(["Date", "Description", "Amount", "Balance"])  # 单一带符号金额列
            for d, desc, amt, bal in txns:
                ws.append([d, desc, amt, bal])
        bio = io.BytesIO()
        wb.save(bio)
        return bio.getvalue()

    def test_all_sheets_parsed_signed_amount(self):
        res = parse_bank_stmt_xlsx_direct(self._build(), "multi.xlsx")
        self.assertTrue(res["ok"])
        self.assertEqual(res.get("sheets_parsed"), 2, "两个 sheet 都应被解析")
        self.assertEqual(res["row_count"], 4, "两 sheet 共 4 行")
        rows = res["rows"]
        # 带符号金额:正→存 负→取
        deps = [r for r in rows if r.deposit > 0]
        wds = [r for r in rows if r.withdrawal > 0]
        self.assertEqual(len(deps), 2)
        self.assertEqual(len(wds), 2)
        self.assertEqual(wds[0].withdrawal, 500.0)  # -500 → 取款 500
        # v118.35.0.59 · Excel 路径也要跑余额校验(不再全 None/"—")
        self.assertTrue(
            any(r.balance_ok is not None for r in rows),
            "Excel 路径应做余额校验 · 不应所有行都未校验",
        )


if __name__ == "__main__":
    unittest.main()
