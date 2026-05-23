# -*- coding: utf-8 -*-
"""
v118.35.0.54 · 守门测试 · 银行对账输入不匹配警告(_detect_recon_mismatch)

真实案例(skin 实测):上传 KBank 1月对账单(277行)+ 12月挂账科目 GL(1行)·
系统闷头算出 -455,613 差额让用户看不懂。应主动警告"期间/规模不匹配"。

锁定契约:
  1. GL 与对账单期间不重叠 → period_mismatch 警告
  2. GL 行数极少 vs 对账单很多 → gl_too_few 警告
  3. 同期间、有匹配 → 无警告
"""

import unittest
from datetime import date

from bank_recon_v2 import StatementRow, GlRow
from recon_routes import _detect_recon_mismatch


def _s(d):
    return StatementRow(date=d, description="x", withdrawal=100.0, deposit=0, balance=0.0)


def _g(d):
    return GlRow(date=d, doc_no="J", account_code="1112", description="x", debit=100.0, credit=0)


class MismatchWarnTests(unittest.TestCase):

    def test_period_mismatch_warns(self):
        stmt = [_s(date(2026, 1, i + 1)) for i in range(25)]
        gl = [_g(date(2025, 12, 31)), _g(date(2025, 12, 30))]
        w = _detect_recon_mismatch(stmt, gl, matched_count=0, lang="zh")
        self.assertTrue(any("期间" in x for x in w), "应警告期间不重叠")

    def test_gl_too_few_warns(self):
        stmt = [_s(date(2026, 1, i + 1)) for i in range(30)]
        gl = [_g(date(2026, 1, 15))]
        w = _detect_recon_mismatch(stmt, gl, matched_count=0, lang="zh")
        self.assertTrue(any("GL" in x for x in w), "GL 行数过少应警告")

    def test_aligned_no_warn(self):
        stmt = [_s(date(2026, 1, i + 1)) for i in range(10)]
        gl = [_g(date(2026, 1, i + 1)) for i in range(10)]
        w = _detect_recon_mismatch(stmt, gl, matched_count=8, lang="zh")
        self.assertEqual(w, [], "同期间且有匹配不应警告")

    def test_lang_follows(self):
        stmt = [_s(date(2026, 1, i + 1)) for i in range(25)]
        gl = [_g(date(2025, 12, 31)), _g(date(2025, 12, 30))]
        w_en = _detect_recon_mismatch(stmt, gl, matched_count=0, lang="en")
        self.assertTrue(any("period" in x.lower() for x in w_en), "英文界面应出英文警告")


if __name__ == "__main__":
    unittest.main()
