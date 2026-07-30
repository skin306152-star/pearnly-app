# -*- coding: utf-8 -*-
"""P1-⑪ · PATCH 得分得清"这次没传这个字段"和"传了空 = 清空"。

反证的是旧行为:路由用 `{k: v for k, v in _dump(req).items() if v is not None}` 把两者揉成同
一件事,于是 UPDATE 根本不碰 barcode 列,接口却回 ok:true —— 用户以为条码删掉了,码还占着,
别的商品用不了,而占码的这个在列表里看着是空的。

上一版为此在 DAL 里写过"唯一键留空落 NULL"的分支,但它只在收到空白【字符串】时才生效,
而前端 readForm() 是 `val(...) || null`,永远不发空串 —— 那段修复对产品是死代码。
所以这里喂的是前端真会发的 body(显式 null / 整个键不出现),不是空白字符串那种理想输入:
用 `{"barcode": "  "}` 验,旧代码也绿,证明不了任何事。
"""

import unittest

from routes import products_routes as routes
from services.products import units as units_dal
from services.sales import products as products_dal


class _CaptureCursor:
    def __init__(self, row=None):
        self.calls = []
        self._row = row or {"id": "p", "barcode": None}

    def execute(self, sql, params=None):
        self.calls.append((sql, params))

    def fetchone(self):
        return self._row


def _fields(body: dict) -> dict:
    return routes._patch_fields(routes.ProductUpdate(**body), products_dal.NULLABLE_FIELDS)


class PatchShapingTellsUnsetFromClearedTests(unittest.TestCase):
    def test_a_field_the_client_never_sent_is_absent(self):
        self.assertNotIn("barcode", _fields({"name_th": "นมสดใหม่"}))

    def test_an_explicit_null_survives_as_a_clear_instruction(self):
        shaped = _fields({"name_th": "นมสด", "barcode": None})
        self.assertIn("barcode", shaped)
        self.assertIsNone(shaped["barcode"])

    def test_the_whole_form_body_clears_only_what_the_user_emptied(self):
        """前端提交的是整张表单:清掉的格发 null,填着的格发值。两种得在同一个 body 里分开。"""
        shaped = _fields({"name_th": "นมสด", "code": "MILK-1", "barcode": None, "name_en": None})
        self.assertEqual(shaped["code"], "MILK-1")
        self.assertIsNone(shaped["barcode"])
        self.assertIsNone(shaped["name_en"])

    def test_null_on_a_not_null_column_is_dropped(self):
        """name_th 是 NOT NULL 列:写下去数据库直接报错,拦在整形层比让用户吃 500 说得清。"""
        self.assertNotIn("name_th", _fields({"name_th": None, "barcode": None}))

    def test_empty_body_is_still_no_changes(self):
        self.assertEqual(_fields({}), {})

    def test_price_zero_and_price_cleared_are_different_instructions(self):
        self.assertEqual(_fields({"unit_price": 0})["unit_price"], 0)
        self.assertIsNone(_fields({"unit_price": None})["unit_price"])


class ClearReachesTheUpdateStatementTests(unittest.TestCase):
    """整形对了还得真写进 SET —— DAL 那层也曾把 None 一起滤掉。"""

    def test_clearing_the_barcode_writes_null(self):
        cur = _CaptureCursor()
        products_dal.update_product(
            cur,
            tenant_id="t",
            workspace_client_id=1,
            product_id="p",
            fields=_fields({"barcode": None}),
        )
        sql, params = cur.calls[-1]
        self.assertIn("barcode = %s", sql)
        self.assertIn(None, params)

    def test_not_sending_the_barcode_leaves_the_column_out_of_the_statement(self):
        cur = _CaptureCursor()
        products_dal.update_product(
            cur,
            tenant_id="t",
            workspace_client_id=1,
            product_id="p",
            fields=_fields({"name_th": "นมสดใหม่"}),
        )
        sql, _params = cur.calls[-1]
        self.assertIn("name_th = %s", sql)
        self.assertNotIn("barcode", sql.split("WHERE")[0])

    def test_clearing_the_price_writes_null_not_zero(self):
        cur = _CaptureCursor()
        products_dal.update_product(
            cur,
            tenant_id="t",
            workspace_client_id=1,
            product_id="p",
            fields=_fields({"unit_price": None}),
        )
        sql, params = cur.calls[-1]
        self.assertIn("unit_price = %s", sql)
        self.assertIn(None, params)
        self.assertNotIn(0, params)


class UnitPatchFollowsTheSameContractTests(unittest.TestCase):
    """箱码印错了要能删掉,不能只能改成别的码 —— 单位那条 PATCH 是同一个坑。"""

    def _unit_fields(self, body: dict) -> dict:
        return routes._patch_fields(routes.UnitUpdate(**body), units_dal.NULLABLE_UNIT_FIELDS)

    def test_explicit_null_clears_the_unit_barcode(self):
        cur = _CaptureCursor(row={"id": "u"})
        units_dal.update_unit(
            cur,
            tenant_id="t",
            workspace_client_id=1,
            product_id="p",
            unit_id="u",
            fields=self._unit_fields({"barcode": None}),
        )
        sql, params = cur.calls[-1]
        self.assertIn("barcode = %s", sql)
        self.assertIn(None, params)

    def test_untouched_unit_barcode_stays_out_of_the_statement(self):
        cur = _CaptureCursor(row={"id": "u"})
        units_dal.update_unit(
            cur,
            tenant_id="t",
            workspace_client_id=1,
            product_id="p",
            unit_id="u",
            fields=self._unit_fields({"unit_name": "ลัง"}),
        )
        sql, _params = cur.calls[-1]
        self.assertNotIn("barcode", sql.split("WHERE")[0])


if __name__ == "__main__":
    unittest.main()
