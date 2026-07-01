# -*- coding: utf-8 -*-
"""库存进出(impstktranrec 入库 / impstktraniss 出库)· 生成器 + 校验 纯单测。

真站点已端到端验(2026-07-01 · 建库存商品→入库 IR690701-017699 / 出库 IS690701-784830
落库 · stktranrec/stktraniss UI 截图命中 · 各 250)。库存只做数量(Zihao 定不算成本)。"""

import io
import re
import unittest
import zipfile

from services.erp.mrerp_xlsx_stock import generate_xlsx_stock, validate_stock_history


def _hist():
    return {
        "id": "sd01",
        "client_id": 3,
        "invoice_date": "2026-07-01",
        "items": [{"name": "StockItem", "qty": 10, "unit_price": 25, "amount": 250}],
    }


def _read(xlsx: bytes):
    with zipfile.ZipFile(io.BytesIO(xlsx)) as z:
        sheets = sorted(n for n in z.namelist() if re.match(r"xl/worksheets/sheet\d+\.xml$", n))
        sst = z.read("xl/sharedStrings.xml").decode("utf-8")
        item_xml = z.read(sheets[1]).decode("utf-8")
    return sheets, sst, item_xml


def _item_cols(item_xml: str) -> int:
    # 第 2 行(首条数据)的单元格数
    rows = re.findall(r"<row[^>]*>(.*?)</row>", item_xml, re.DOTALL)
    return len(re.findall(r"<c ", rows[1])) if len(rows) > 1 else 0


class TestStockGenerator(unittest.TestCase):
    def test_receive_two_sheets_items_have_price(self):
        sheets, sst, item_xml = _read(generate_xlsx_stock([_hist()], {"products": []}, "receive"))
        self.assertEqual(len(sheets), 2)
        self.assertEqual(_item_cols(item_xml), 8)  # 入库明细带单价/金额

    def test_issue_items_quantity_only(self):
        sheets, sst, item_xml = _read(generate_xlsx_stock([_hist()], {"products": []}, "issue"))
        self.assertEqual(len(sheets), 2)
        self.assertEqual(_item_cols(item_xml), 6)  # 出库明细仅到数量列

    def test_product_code_resolved_into_sheet(self):
        m = {"products": [{"item_name": "StockItem", "erp_code": "P-ABC"}]}
        _, sst, _ = _read(generate_xlsx_stock([_hist()], m, "receive"))
        self.assertIn("P-ABC", sst)


class TestStockValidate(unittest.TestCase):
    def test_ok(self):
        m = {"products": [{"item_name": "StockItem", "erp_code": "P-ABC"}]}
        ok, err, _ = validate_stock_history(_hist(), m)
        self.assertTrue(ok)
        self.assertIsNone(err)

    def test_missing_date(self):
        h = _hist()
        h["invoice_date"] = ""
        self.assertEqual(validate_stock_history(h, {"products": []})[1], "ERR_NO_INVOICE_DATE")

    def test_no_resolvable_item(self):
        # 商品对不上已有码(未自建)→ code 空 → ERR_NO_STOCK_ITEM
        self.assertEqual(validate_stock_history(_hist(), {"products": []})[1], "ERR_NO_STOCK_ITEM")


if __name__ == "__main__":
    unittest.main()
