# -*- coding: utf-8 -*-
"""
v118.35.0.66 · 守门测试 · 坐标感知内嵌文本对账单解析(_parse_stmt_text_coords)

真实案例(skin BAY 9789 · 24 页文本 PDF):get_text() 线性化丢列位置 → 314 笔存款
被全判成取款 → 余额链坏 → 触发 Gemini · 再被 Gemini 漏读 30-40%。坐标解析按表头列
x 归位 · 跨全部页 · 免费 100% 召回(BAY 实测 314/31)。

锁定契约:
  1. 表头『取/存/余额』分立三列 → 金额按 x 归到正确列
  2. 期初由首笔『余额 − 净额』数学反推
  3. 末额 = 末行余额
  4. 存取合并列(如 KBank『ถอนเงิน / ฝากเงิน』· x 间距<20)→ 返回空 · 交回上层(不硬解 · 防错列)
"""

import io
import unittest

import fitz  # PyMuPDF

from services.recon.bank_recon_v2 import _parse_stmt_text_coords


def _make_pdf(header, rows, width=400):
    """合成一页对账单 PDF · header=[(x,text)] · rows=[(date, wd|None, dep|None, bal)] 按列 x 落字。"""
    doc = fitz.open()
    pg = doc.new_page(width=width, height=320)
    for x, t in header:
        pg.insert_text((x, 50), t, fontsize=9)
    y = 80
    cols_x = {"date": 25, "wd": 135, "dep": 215, "bal": 290}
    for d, wd, dep, bal in rows:
        pg.insert_text((cols_x["date"], y), d, fontsize=9)
        if wd:
            pg.insert_text((cols_x["wd"], y), wd, fontsize=9)
        if dep:
            pg.insert_text((cols_x["dep"], y), dep, fontsize=9)
        pg.insert_text((cols_x["bal"], y), bal, fontsize=9)
        y += 25
    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()


_HDR_SEP = [(25, "Date"), (135, "Withdrawal"), (215, "Deposit"), (290, "Balance")]
_HDR_MERGED = [(25, "Date"), (175, "ถอนเงิน / ฝากเงิน"), (290, "Balance")]


class CoordParserTests(unittest.TestCase):

    def test_separate_columns_split_correctly(self):
        pdf = _make_pdf(
            _HDR_SEP,
            [
                ("01/01/2026", None, "100.00", "1,100.00"),  # 存 100(期初 1000)
                ("02/01/2026", None, "50.00", "1,150.00"),  # 存 50
                ("03/01/2026", "200.00", None, "950.00"),  # 取 200
            ],
        )
        rows, opening, closing = _parse_stmt_text_coords(pdf)
        self.assertEqual(len(rows), 3)
        self.assertEqual(sum(1 for r in rows if r.deposit > 0), 2)
        self.assertEqual(sum(1 for r in rows if r.withdrawal > 0), 1)
        self.assertAlmostEqual(opening, 1000.0, places=2)  # 数学反推期初
        self.assertAlmostEqual(closing, 950.0, places=2)

    def test_merged_column_falls_back_to_xcluster_direction_by_delta(self):
        """KBank 那种『存取合并列 + 表头列代表不了数据列』· 表头法失效 → 数据驱动 x 聚类
        兜底:金额列 + 余额列两簇,方向由余额涨跌定。锁定 266/33 这类能被正确切分。"""
        # 单一金额列(x~150)+ 余额列(x~250)· 首行 B/F 无金额 · 其余按余额涨跌定方向
        doc = fitz.open()
        pg = doc.new_page(width=360, height=400)
        pg.insert_text((25, 50), "Date", fontsize=9)
        pg.insert_text((140, 50), "Amount", fontsize=9)  # 不是 取/存 关键词
        pg.insert_text((240, 50), "Balance", fontsize=9)
        # (date, amount, balance) · None amount = B/F 期初行
        data = [
            ("01/01/2026", None, "1,000.00"),  # B/F → 期初 1000
            ("02/01/2026", "100.00", "1,100.00"),  # +100 存
            ("03/01/2026", "200.00", "1,300.00"),  # +200 存
            ("04/01/2026", "50.00", "1,250.00"),  # -50  取
            ("05/01/2026", "300.00", "1,550.00"),  # +300 存
            ("06/01/2026", "400.00", "1,150.00"),  # -400 取
            ("07/01/2026", "100.00", "1,250.00"),  # +100 存
            ("08/01/2026", "500.00", "1,750.00"),  # +500 存
            ("09/01/2026", "250.00", "1,500.00"),  # -250 取
        ]
        y = 80
        for d, amt, bal in data:
            pg.insert_text((25, y), d, fontsize=9)
            if amt:
                pg.insert_text((140, y), amt, fontsize=9)
            pg.insert_text((240, y), bal, fontsize=9)
            y += 25
        bio = io.BytesIO()
        doc.save(bio)
        rows, opening, closing = _parse_stmt_text_coords(bio.getvalue())
        self.assertEqual(len(rows), 8)  # 8 笔交易(B/F 不算)
        self.assertEqual(sum(1 for r in rows if r.deposit > 0), 5)
        self.assertEqual(sum(1 for r in rows if r.withdrawal > 0), 3)
        self.assertAlmostEqual(opening, 1000.0, places=2)
        self.assertAlmostEqual(closing, 1500.0, places=2)


if __name__ == "__main__":
    unittest.main()
