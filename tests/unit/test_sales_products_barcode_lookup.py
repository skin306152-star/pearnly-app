# -*- coding: utf-8 -*-
"""条码 lookup 与 POS 同口径的守门(P1-J)+ 空白条码归一(P1-F 前置)。

反证的是旧行为:services/sales/products.find_by 只查 products.barcode,于是 POS 认得的
箱码/瓶码在入库扫码与建品查重这边一律未命中 —— 查重绿字说"没人用这个码",用户照建,
重码要到收银台扫出错商品才暴露。这里逐条锁住:单位码先配、命中回单位名、主码回落、
停用商品不占码、每条语句都带租户+套账。
"""

import unittest

from services.sales import products as dal

_PRODUCT = {
    "id": "aaaaaaaa-0000-0000-0000-000000000001",
    "tenant_id": "t-1",
    "code": "P01",
    "barcode": "8850001",
    "name_th": "น้ำ",
    "base_unit": "ขวด",
    "is_active": True,
}


class _RoutingCursor:
    """按语句形态分发假数据:product_units 查一套、products 查一套(FakeCursor 只能按
    调用次序给死答案,分不出"单位码没配上但主码配上了"这种分支)。"""

    def __init__(self, *, unit_row=None, product_by_id=None, product_by_barcode=None):
        self.calls = []
        self._unit_row = unit_row
        self._by_id = product_by_id
        self._by_barcode = product_by_barcode
        self._last = None

    def execute(self, sql, params=None):
        self.calls.append((sql, params))
        if "FROM product_units" in sql:
            self._last = self._unit_row
        elif "AND id = %s" in sql:
            self._last = self._by_id
        else:
            self._last = self._by_barcode

    def fetchone(self):
        return self._last

    def fetchall(self):
        return []

    @property
    def sqls(self):
        return [c[0] for c in self.calls]


class BarcodeLookupMatchesPosRuleTests(unittest.TestCase):
    def test_unit_barcode_hits_the_owning_product(self):
        """箱码只存在于 product_units:旧实现只查 products.barcode → 返 None(假"没人用")。"""
        cur = _RoutingCursor(
            unit_row={"product_id": _PRODUCT["id"], "unit_name": "ลัง"},
            product_by_id=_PRODUCT,
        )
        out = dal.find_by(cur, tenant_id="t-1", workspace_client_id=1, key="barcode", value="BOX9")
        self.assertIsNotNone(out, "单位码必须能查到所属商品(与 POS product_by_barcode 同口径)")
        self.assertEqual(out["id"], _PRODUCT["id"])

    def test_unit_hit_reports_which_unit(self):
        cur = _RoutingCursor(
            unit_row={"product_id": _PRODUCT["id"], "unit_name": "ลัง"},
            product_by_id=_PRODUCT,
        )
        out = dal.find_by(cur, tenant_id="t-1", workspace_client_id=1, key="barcode", value="BOX9")
        self.assertEqual(out["matched_by"], "unit")
        self.assertEqual(out["matched_unit"], "ลัง")

    def test_unit_table_is_queried_before_products(self):
        """先单位后主码的次序本身是口径的一部分:箱码与另一商品主码同值时,POS 取箱码那个。"""
        cur = _RoutingCursor(
            unit_row={"product_id": _PRODUCT["id"], "unit_name": "ลัง"},
            product_by_id=_PRODUCT,
            product_by_barcode={**_PRODUCT, "id": "other"},
        )
        out = dal.find_by(cur, tenant_id="t-1", workspace_client_id=1, key="barcode", value="BOX9")
        self.assertIn("FROM product_units", cur.sqls[0])
        self.assertEqual(out["id"], _PRODUCT["id"])

    def test_main_barcode_hit_reports_product(self):
        cur = _RoutingCursor(unit_row=None, product_by_barcode=_PRODUCT)
        out = dal.find_by(
            cur, tenant_id="t-1", workspace_client_id=1, key="barcode", value="8850001"
        )
        self.assertEqual(out["id"], _PRODUCT["id"])
        self.assertEqual(out["matched_by"], "product")
        self.assertIsNone(out["matched_unit"])

    def test_unit_on_deactivated_product_falls_back_to_active_main(self):
        """停用商品不占码(唯一索引谓词同为 is_active=TRUE)· 别把"码被占了"报成"空的"。"""
        cur = _RoutingCursor(
            unit_row={"product_id": "dead", "unit_name": "ลัง"},
            product_by_id=None,
            product_by_barcode=_PRODUCT,
        )
        out = dal.find_by(cur, tenant_id="t-1", workspace_client_id=1, key="barcode", value="BOX9")
        self.assertEqual(out["id"], _PRODUCT["id"])
        self.assertEqual(out["matched_by"], "product")

    def test_no_match_anywhere_returns_none(self):
        cur = _RoutingCursor()
        self.assertIsNone(
            dal.find_by(cur, tenant_id="t-1", workspace_client_id=1, key="barcode", value="NOPE")
        )

    def test_code_and_qr_keys_report_product_match(self):
        for key, value in (("code", "P01"), ("qr", "Q1")):
            cur = _RoutingCursor(product_by_barcode=_PRODUCT)
            out = dal.find_by(cur, tenant_id="t-1", workspace_client_id=1, key=key, value=value)
            self.assertEqual(out["matched_by"], "product")
            self.assertNotIn("FROM product_units", " ".join(cur.sqls))

    def test_every_barcode_statement_is_tenant_and_workspace_scoped(self):
        cur = _RoutingCursor(
            unit_row={"product_id": _PRODUCT["id"], "unit_name": "ลัง"},
            product_by_id=_PRODUCT,
        )
        dal.find_by(cur, tenant_id="t-1", workspace_client_id=7, key="barcode", value="BOX9")
        self.assertTrue(cur.calls)
        for sql, params in cur.calls:
            self.assertIn("tenant_id = %s", sql)
            self.assertIn("workspace_client_id = %s", sql)
            self.assertIn("t-1", params)
            self.assertIn(7, params)
            self.assertNotIn("BOX9", sql, "条码值必须走占位符")


class BlankBarcodeNormalizationTests(unittest.TestCase):
    """空串条码照样进 `WHERE barcode IS NOT NULL` 的部分唯一索引 → 几个"没填条码"的
    商品互撞。归一必须发生在写入前,否则 0092 一上线建品就 409。"""

    class _Cursor:
        def __init__(self):
            self.calls = []

        def execute(self, sql, params=None):
            self.calls.append((sql, params))

        def fetchone(self):
            return None

    def _insert(self, fields):
        cur = self._Cursor()
        dal.create_product(cur, tenant_id="t", workspace_client_id=1, fields=fields)
        return next(c for c in cur.calls if "INSERT" in c[0])

    def test_blank_barcode_omitted_from_insert(self):
        sql, params = self._insert({"name_th": "A", "barcode": "   "})
        self.assertNotIn("barcode", sql.split("VALUES")[0])
        self.assertNotIn("   ", params)

    def test_barcode_stripped_before_insert(self):
        _sql, params = self._insert({"name_th": "A", "barcode": " 8850001 "})
        self.assertIn("8850001", params)
        self.assertNotIn(" 8850001 ", params)

    def test_update_clears_barcode_to_null_not_empty_string(self):
        """清空条码要真写 NULL:写空串等于占着索引位,几个"没填"的商品互撞 409。"""
        cur = self._Cursor()
        dal.update_product(
            cur, tenant_id="t", workspace_client_id=1, product_id="p", fields={"barcode": "  "}
        )
        sql, params = cur.calls[-1]
        self.assertIn("barcode = %s", sql)
        self.assertIn(None, params)
        self.assertNotIn("  ", params)


if __name__ == "__main__":
    unittest.main()
