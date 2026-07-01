# -*- coding: utf-8 -*-
"""master_customer(自建客户)生成器 · 纯单测(无网络)。

真站点端到端已在 2026-07-01 验过(imparse 导入 raw=1 → armas 列表命中 → 删);此处守
25 列结构 / 必填字段兜底 / 邮箱合法化 / 结构码可覆盖,防回归。"""

import io
import re
import unittest
import zipfile

from services.erp import mrerp_xlsx_generator as gen
from services.erp.mrerp_xlsx_customer import _DEFAULTS, _email, build_customer_row

_CUST = {
    "code": "PT0001",
    "name": "Acme Co Ltd",
    "tax_id": "0105561000000",
    "address": "1 Road",
    "postcode": "10110",
}


def _row2_cells(xlsx: bytes):
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


class TestCustomerGenerator(unittest.TestCase):
    def test_single_sheet_25col_header(self):
        xlsx = gen.generate_xlsx([_CUST], {}, sheet_kind="customer_master")
        cells = _row2_cells(xlsx)
        self.assertEqual(cells.get("A"), "PT0001")  # 客户码
        self.assertEqual(cells.get("B"), _DEFAULTS["type"])  # 类型 1-11
        self.assertEqual(cells.get("D"), "Acme Co Ltd")  # 名称
        self.assertEqual(cells.get("M"), _DEFAULTS["account"])  # 应收科目
        self.assertEqual(cells.get("Q"), _DEFAULTS["area"])  # 销售区(6 字符)
        self.assertEqual(cells.get("X"), "0105561000000")  # 税号
        self.assertEqual(cells.get("Y"), _DEFAULTS["branch"])  # 分支

    def test_required_text_fields_get_placeholder(self):
        # 地址 2-4(F/G/H)无数据 → 占位 "-"(空会被 MR.ERP 判 เป็นค่าว่าง)
        cells = _row2_cells(gen.generate_xlsx([_CUST], {}, sheet_kind="customer_master"))
        for col in ("G", "H"):
            self.assertEqual(cells.get(col), "-")

    def test_structural_codes_overridable(self):
        m = {"_mrerp_customer_area": "ABCDEF", "_mrerp_customer_account": "1130-99"}
        cells = _row2_cells(gen.generate_xlsx([_CUST], m, sheet_kind="customer_master"))
        self.assertEqual(cells.get("Q"), "ABCDEF")
        self.assertEqual(cells.get("M"), "1130-99")


class TestEmail(unittest.TestCase):
    def test_valid_email_kept(self):
        self.assertEqual(_email("a@b.com"), "a@b.com")

    def test_empty_or_invalid_falls_to_default(self):
        # MR.ERP 邮箱必填且须合法 · 空/'-' 都用合法占位默认
        self.assertEqual(_email(""), _DEFAULTS["email"])
        self.assertEqual(_email("-"), _DEFAULTS["email"])
        self.assertTrue(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", _email("")))

    def test_row_uses_email_default_when_missing(self):
        self.assertEqual(build_customer_row(_CUST, {})[11], _DEFAULTS["email"])


if __name__ == "__main__":
    unittest.main()
