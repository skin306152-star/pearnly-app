# -*- coding: utf-8 -*-
"""sales_cash 生成器 + 收款科目解析 + 模块表 · 纯单测(无网络)。

真站点端到端已在 2026-07-01 验过(见 mrerp_http/modules.py sales_cash 注释);此处守列结构/
收款槽契约与科目回退,防回归。"""

import io
import re
import unittest
import zipfile

from services.erp import mrerp_xlsx_generator as gen
from services.erp.mrerp_http.modules import get_module
from services.erp.mrerp_xlsx_sales_cash import (
    _DEFAULT_RECEIPT_ACCOUNT_BANK,
    _DEFAULT_RECEIPT_ACCOUNT_CASH,
    _receipt_account,
)

_HISTORY = {
    "id": "t1",
    "client_id": 99,
    "invoice_number": "PT-1",
    "invoice_date": "2026-07-01",
    "subtotal": "100.00",
    "vat": "7.00",
    "total_amount": "107.00",
    "items": [{"name": "ITEM A", "qty": 1, "unit_price": 60, "amount": 60}],
}
_MAPPINGS = {"clients": [{"erp_type": "mrerp", "client_id": 99, "erp_code": "0006"}]}


def _sheet1_datarow_cells(xlsx: bytes):
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


class TestSalesCashGenerator(unittest.TestCase):
    def test_produces_four_sheet_zip(self):
        xlsx = gen.generate_xlsx([_HISTORY], _MAPPINGS, sheet_kind="sales_cash")
        with zipfile.ZipFile(io.BytesIO(xlsx)) as z:
            names = z.namelist()
        for i in (1, 2, 3, 4):
            self.assertIn(f"xl/worksheets/sheet{i}.xml", names)

    def test_receipt_slots_carry_account_and_total(self):
        xlsx = gen.generate_xlsx([_HISTORY], _MAPPINGS, sheet_kind="sales_cash")
        cells = _sheet1_datarow_cells(xlsx)
        # 现金收讫(P/16)=0 · 全额走收款槽1(R/18)
        self.assertEqual(cells.get("P"), "0")
        self.assertEqual(cells.get("R"), "107")
        # 3 个收款科目槽(Q/S/U)全填有效科目码(默认转账→银行)· 满足 MR.ERP 非空校验
        for col in ("Q", "S", "U"):
            self.assertEqual(cells.get(col), _DEFAULT_RECEIPT_ACCOUNT_BANK)
        # 槽2/3 金额(T/V)=0
        self.assertEqual(cells.get("T"), "0")
        self.assertEqual(cells.get("V"), "0")


class TestReceiptAccount(unittest.TestCase):
    def test_transfer_defaults_to_bank(self):
        self.assertEqual(_receipt_account(_HISTORY, {}), _DEFAULT_RECEIPT_ACCOUNT_BANK)

    def test_cash_payment_uses_cash_account(self):
        h = {**_HISTORY, "payment_status": "paid", "payment_method": "cash"}
        self.assertEqual(_receipt_account(h, {}), _DEFAULT_RECEIPT_ACCOUNT_CASH)

    def test_mappings_override(self):
        self.assertEqual(
            _receipt_account(_HISTORY, {"_mrerp_receipt_account_bank": "1113-01"}), "1113-01"
        )


class TestModule(unittest.TestCase):
    def test_sales_cash_verified_and_listing(self):
        m = get_module("sales_cash")
        self.assertTrue(m.verified)
        self.assertEqual(m.listing_module, "arse")
        self.assertEqual(m.listing_idmenu, 125)


if __name__ == "__main__":
    unittest.main()
