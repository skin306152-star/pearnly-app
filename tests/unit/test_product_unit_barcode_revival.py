# -*- coding: utf-8 -*-
"""P1-⑥/P1-⑩ · 单位码靠索引谓词让位,不靠抹值;POS 扫码不许挑中死行也不许不回落。

反证的是旧行为:停用商品时 `UPDATE product_units SET barcode = NULL`。软删的契约是
"保留引用、可复活",抹值破的正是这条 —— 季节性下架的牛奶两个月后上架,商品和主码都回来了,
三条单位码全空,扫箱码 404「商品不存在」而商品就在列表里,无提示无审计,只能一条条重录。

改成保留值之后冒出的新风险也一起钉住:同一个码可能同时存在于"死商品的单位行"和"在售商品"
上,而扫码那两条查询都是 `LIMIT 1` 无 ORDER BY —— 不筛 product_active 就是抛硬币。

真库那条验的是"索引真拦得住 / 复活真扫得出来":
tests/integration/test_product_price_and_revival_real_db.UnitBarcodeSurvivesSoftDeleteTests。
"""

import unittest

from services.pos import catalog as pos_catalog
from services.sales import products as products_dal

_PRODUCT = {
    "id": "aaaaaaaa-0000-0000-0000-000000000001",
    "name_th": "นมสด",
    "name_en": None,
    "name_zh": None,
    "category_id": None,
    "image_url": None,
    "base_unit": "ขวด",
    "barcode": "8850001",
    "vat_applicable": True,
    "track_batch": False,
    "is_weighed": False,
    "is_active": True,
    "unit_price": 20,
}


class _Cursor:
    def __init__(self, row=None):
        self.calls = []
        self._row = row if row is not None else _PRODUCT

    def execute(self, sql, params=None):
        self.calls.append((sql, params))

    def fetchone(self):
        return self._row

    def fetchall(self):
        return []

    @property
    def sqls(self):
        return [c[0] for c in self.calls]


class _ScanCursor:
    """按语句形态分发:单位码查一套、按 id 查商品一套、按主码查商品一套。

    真实里三条查询的结果互相独立(单位行在但商品停用、主码却挂在另一个在售商品上),
    按调用次序给死答案的桩分不出这些分支,验不到回落。
    """

    def __init__(self, *, unit_row=None, product_by_id=None, product_by_barcode=None):
        self.calls = []
        self._unit = unit_row
        self._by_id = product_by_id
        self._by_barcode = product_by_barcode
        self._last = None

    def execute(self, sql, params=None):
        self.calls.append((sql, params))
        if "FROM product_units" in sql and "barcode = %s" in sql:
            self._last = self._unit
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


def _unit_writes(cur):
    return [(sql, params) for sql, params in cur.calls if "UPDATE product_units" in sql]


class SoftDeleteHidesTheCodeInsteadOfErasingItTests(unittest.TestCase):
    def test_deactivate_never_nulls_a_barcode(self):
        cur = _Cursor()
        cur.rowcount = 1
        products_dal.deactivate_product(cur, tenant_id="t", workspace_client_id=1, product_id="p")
        writes = _unit_writes(cur)
        self.assertTrue(writes, "停用必须同步单位行的让位标记")
        sql, params = writes[0]
        self.assertIn("product_active = %s", sql)
        self.assertIn(False, params)
        self.assertNotIn("barcode", sql, "抹值 = 复活不回来,契约破在这里")

    def test_patch_inactive_hides_them_too(self):
        cur = _Cursor()
        products_dal.update_product(
            cur, tenant_id="t", workspace_client_id=1, product_id="p", fields={"is_active": False}
        )
        sql, params = _unit_writes(cur)[0]
        self.assertIn("product_active = %s", sql)
        self.assertIn(False, params)

    def test_patch_active_brings_them_back(self):
        """只跟 false 就成了"下架让码、上架不收回" —— 商品回来了,箱码还是扫不出。"""
        cur = _Cursor()
        products_dal.update_product(
            cur, tenant_id="t", workspace_client_id=1, product_id="p", fields={"is_active": True}
        )
        sql, params = _unit_writes(cur)[0]
        self.assertIn("product_active = %s", sql)
        self.assertIn(True, params)

    def test_an_ordinary_patch_does_not_touch_the_units(self):
        cur = _Cursor()
        products_dal.update_product(
            cur, tenant_id="t", workspace_client_id=1, product_id="p", fields={"unit": "ea"}
        )
        self.assertEqual(_unit_writes(cur), [])

    def test_reviving_by_code_restores_and_moves_the_unit_rows(self):
        """第二条复活路径:按同一个编码重建。单位行不跟着挪套账就成孤儿,界面上看不见、码还占着。"""
        cur = _Cursor(row={"id": "dead1"})
        products_dal.create_product(
            cur, tenant_id="t", workspace_client_id=7, fields={"name_th": "นมสด", "code": "MILK-1"}
        )
        sql, params = _unit_writes(cur)[0]
        self.assertIn("product_active = TRUE", sql)
        self.assertIn("workspace_client_id = %s", sql)
        self.assertEqual(params[0], 7)
        self.assertIn("dead1", params)

    def test_unit_writes_stay_inside_the_tenant(self):
        for fields in ({"is_active": False}, {"is_active": True}):
            cur = _Cursor()
            products_dal.update_product(
                cur, tenant_id="t-1", workspace_client_id=9, product_id="p", fields=fields
            )
            sql, params = _unit_writes(cur)[0]
            self.assertIn("tenant_id = %s", sql)
            self.assertIn("workspace_client_id = %s", sql)
            self.assertIn("t-1", params)
            self.assertIn(9, params)


class NewUnitRowInheritsTheProductStateTests(unittest.TestCase):
    """给已停用的商品补配箱码(准备下次上架)时,新行不许自带"在售"标记。

    默认值 TRUE 只对在售商品才对:挂在停用商品上就立刻占着码,而查重那边筛掉了不在售的
    商品、一律回"没人用" —— 绿字放行,真存撞唯一索引,占码的在列表里看不见。
    """

    def test_create_unit_syncs_the_flag_from_the_owning_product(self):
        from services.products import units as units_dal

        cur = _Cursor(row={"id": "u1"})
        units_dal.create_unit(
            cur,
            tenant_id="t",
            workspace_client_id=1,
            product_id="p",
            fields={"unit_name": "ลัง", "factor_to_base": 24, "barcode": "BOX9"},
        )
        sql, params = cur.calls[-1]
        self.assertIn("SET product_active = p.is_active", sql)
        self.assertIn("u1", params)


class ScanNeverPicksADeadUnitRowTests(unittest.TestCase):
    """保留值之后同码可能有多行,`LIMIT 1` 无 ORDER BY 就是抛硬币 —— 那是钱路径。"""

    def test_sales_lookup_filters_on_product_active(self):
        cur = _ScanCursor(product_by_barcode=_PRODUCT)
        products_dal.find_by(cur, tenant_id="t", workspace_client_id=1, key="barcode", value="BOX9")
        unit_sql = next(s for s in cur.sqls if "FROM product_units" in s)
        self.assertIn("product_active", unit_sql)

    def test_pos_lookup_filters_on_product_active(self):
        cur = _ScanCursor(product_by_barcode=_PRODUCT)
        pos_catalog.product_by_barcode(cur, tenant_id="t", workspace_client_id=1, code="BOX9")
        unit_sql = next(s for s in cur.sqls if "FROM product_units" in s)
        self.assertIn("product_active", unit_sql)


class PosFallsBackToTheMainCodeTests(unittest.TestCase):
    """P1-⑩:单位行对得上但那个商品已停用时,POS 曾经直接 404,不像主 SPA 那样回落主码。

    收银员看到的是「商品不存在」,而商品就在网格里 —— 台前没处可查。两边口径分叉过一次,
    结果是 POS 认得的箱码在建品查重那边显示"没人用",绿字骗人还放行重码。
    """

    def test_dead_unit_row_falls_back_to_the_live_main_barcode(self):
        cur = _ScanCursor(
            unit_row={"product_id": "dead", "unit_name": "ลัง"},
            product_by_id=None,
            product_by_barcode=_PRODUCT,
        )
        hit = pos_catalog.product_by_barcode(cur, tenant_id="t", workspace_client_id=1, code="BOX9")
        self.assertEqual(hit["id"], _PRODUCT["id"])
        self.assertEqual(hit["matched_unit"], _PRODUCT["base_unit"])

    def test_a_live_unit_hit_still_wins_over_the_main_code(self):
        """回落不许变成"总是按主码":扫箱码就得按箱卖,否则扫一箱收一瓶的钱。"""
        cur = _ScanCursor(
            unit_row={"product_id": _PRODUCT["id"], "unit_name": "ลัง"},
            product_by_id=_PRODUCT,
            product_by_barcode={**_PRODUCT, "id": "other"},
        )
        hit = pos_catalog.product_by_barcode(cur, tenant_id="t", workspace_client_id=1, code="BOX9")
        self.assertEqual(hit["id"], _PRODUCT["id"])
        self.assertEqual(hit["matched_unit"], "ลัง")

    def test_nothing_anywhere_is_still_a_404(self):
        from core.pos_api import PosError

        cur = _ScanCursor()
        with self.assertRaises(PosError) as ctx:
            pos_catalog.product_by_barcode(cur, tenant_id="t", workspace_client_id=1, code="NOPE")
        self.assertEqual(ctx.exception.code, "pos.product_not_found")


if __name__ == "__main__":
    unittest.main()
