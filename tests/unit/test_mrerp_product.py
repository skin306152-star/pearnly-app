# -*- coding: utf-8 -*-
"""master_product(自建商品)生成器 · 纯单测(无网络)。

真站点端到端已验(impstkmas 导入 raw=1 → stkmas 列表命中 → 删 · 2026-07-01);此处守
29 列结构 / 类型与成本法标签 / 8 科目可覆盖,防回归。"""

import io
import re
import unittest
import zipfile

from services.erp import mrerp_xlsx_generator as gen
from services.erp.mrerp_xlsx_product import _DEFAULTS

_PROD = {"code": "PP0001", "name": "Lipstick", "price": 25}


def _row2(xlsx: bytes):
    with zipfile.ZipFile(io.BytesIO(xlsx)) as z:
        s1 = z.read("xl/worksheets/sheet1.xml").decode("utf-8")
        sst = z.read("xl/sharedStrings.xml").decode("utf-8")
    strings = [re.sub(r"<[^>]+>", "", x) for x in re.findall(r"<si>.*?</si>", sst, re.S)]
    row = re.search(r'<row r="2"[^>]*>(.*?)</row>', s1, re.S).group(1)
    out = {}
    for c in re.finditer(r'<c r="([A-Z]+)2"([^>]*)>(?:<v>(.*?)</v>)?</c>', row):
        col, attrs, v = c.group(1), c.group(2), c.group(3)
        out[col] = strings[int(v)] if (v and 't="s"' in attrs) else v
    return out


class TestProductGenerator(unittest.TestCase):
    def test_29col_stock_item(self):
        cells = _row2(gen.generate_xlsx([_PROD], {}, sheet_kind="product_master"))
        self.assertEqual(cells.get("A"), _DEFAULTS["type"])  # 类型标签 จัดทำสต๊อค(非 select 值 1)
        self.assertEqual(cells.get("C"), "PP0001")  # 商品码
        self.assertEqual(cells.get("D"), "Lipstick")  # 名
        self.assertEqual(cells.get("I"), "25")  # 售价
        self.assertEqual(cells.get("J"), _DEFAULTS["cost_method"])  # 成本法 Average
        self.assertEqual(cells.get("AA"), _DEFAULTS["acc_inv"])  # 存货科目
        self.assertEqual(cells.get("AB"), _DEFAULTS["acc_cost"])  # 销货成本
        self.assertEqual(cells.get("AC"), _DEFAULTS["supplier"])  # 供应商占位

    def test_type_is_short_label_not_select_value(self):
        # 实测:import 认 "จัดทำสต๊อค",带 "สินค้า : " 前缀或 "1" 都被拒
        self.assertEqual(_DEFAULTS["type"], "จัดทำสต๊อค")

    def test_accounts_overridable(self):
        m = {"_mrerp_product_acc_inv": "1155-99", "_mrerp_product_category": "ZZ"}
        cells = _row2(gen.generate_xlsx([_PROD], m, sheet_kind="product_master"))
        self.assertEqual(cells.get("AA"), "1155-99")
        self.assertEqual(cells.get("B"), "ZZ")


if __name__ == "__main__":
    unittest.main()
