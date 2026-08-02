# -*- coding: utf-8 -*-
"""P0-① · "没设价"和"价格是 0"必须在数据层就分得开。

反证的是旧行为:`ProductCreate.unit_price: float = Field(0, ge=0)` 让后端永远收不到"没设价",
再加上列上的 `NOT NULL DEFAULT 0`,空价格进库就是 0。收银台的零元闸只拦得住 price 为空,
拦不住 "0.00" —— 于是扫码就地建品那条路建出来的货全部 ฿0 可售,小票和报表上都看不出异常。

这里喂的一律是会出事的输入:只带名字的建品载荷(门店扫到没建档的码当场只输个名字)、
显式 0(赠品,不许被当成"没设价")、以及价格为 NULL 的菜品被点进餐厅账单。
拿"填了 ฿50"的商品验永远是绿的:那种输入下 0 和 NULL 的差别根本不出现。

"库里真的是 NULL 不是 0"由真库那条兜(桩 cursor 看不见数据库默认值):
tests/integration/test_product_price_and_revival_real_db.NoPriceIsNullNotZeroTests。
"""

import inspect
import unittest
from unittest.mock import patch

from core.pos_api import PosError
from routes import products_routes as routes
from services.pos.restaurant import sessions as rest_sessions
from services.products import units as units_dal
from services.sales import products as products_dal


class _CaptureCursor:
    def __init__(self):
        self.calls = []

    def execute(self, sql, params=None):
        self.calls.append((sql, params))

    def fetchone(self):
        return None


class CreateModelKeepsNoPriceTests(unittest.TestCase):
    def test_name_only_payload_carries_no_price_not_zero(self):
        """扫码就地建品发的就是这个载荷。默认 0 时后端根本收不到"没设价"这个状态。"""
        req = routes.ProductCreate(name_th="นมสด 200ml")
        self.assertIsNone(req.unit_price)

    def test_explicit_zero_survives_as_zero(self):
        """฿0 是用户拍板的价(赠品/试用装):把默认值改成 None 不许顺手把真 0 也吞掉,
        否则病灶只是从一种"分不清"换成另一种。"""
        self.assertEqual(routes.ProductCreate(name_th="ของแถม", unit_price=0).unit_price, 0)

    def test_no_price_never_reaches_the_insert_column_list(self):
        cur = _CaptureCursor()
        products_dal.create_product(
            cur,
            tenant_id="t",
            workspace_client_id=1,
            fields=routes._dump(routes.ProductCreate(name_th="นมสด")),
        )
        sql, params = cur.calls[-1]
        self.assertIn("INSERT INTO products", sql)
        self.assertNotIn("unit_price", sql.split("VALUES")[0])
        self.assertNotIn(0, params)


class ApiEnvelopeIsHonestTests(unittest.TestCase):
    def test_null_price_is_reported_as_null(self):
        """回 0.0 等于替用户拍板"这货免费":前端再也画不出"还没定价",POS 也分不出该拦谁。"""
        self.assertIsNone(routes._out({"id": "p", "unit_price": None})["unit_price"])

    def test_real_zero_is_still_reported_as_zero(self):
        self.assertEqual(routes._out({"id": "p", "unit_price": 0})["unit_price"], 0.0)


class ColumnMustBeNullableTests(unittest.TestCase):
    """应用层传 None 也会被 `NOT NULL DEFAULT 0` 顶成 0 —— 病灶在列定义上,得真去掉。"""

    def test_runtime_ddl_drops_both_the_default_and_the_not_null(self):
        ddl = " ".join(products_dal._PRICE_NULLABLE_DDL)
        self.assertIn("ALTER COLUMN unit_price DROP DEFAULT", ddl)
        self.assertIn("ALTER COLUMN unit_price DROP NOT NULL", ddl)

    def test_startup_path_actually_runs_it(self):
        """prod 不跑 alembic:这段不接在启动期双跑上,迁移写得再对生产也没生效。"""
        src = inspect.getsource(units_dal.ensure_schema)
        self.assertIn("_apply_price_nullability()", src)
        self.assertIn("relax_price_not_null", inspect.getsource(units_dal._apply_price_nullability))


class RestaurantRefusesToServeAnUnpricedDishTests(unittest.TestCase):
    """点单那条路的服务端自己会把 NULL 换成 0 —— 客人点了、厨房做了、结账白送,
    账单上跟真的免费赠品一模一样,月底对不出来。"""

    def _add_line(self, unit_price):
        prod = {
            "id": "p-1",
            "base_unit": "จาน",
            "unit_price": unit_price,
            "vat_applicable": True,
        }
        with (
            patch.object(rest_sessions, "_require_session", return_value={"status": "open"}),
            patch.object(rest_sessions.store, "get_menu_product", return_value=prod),
            patch.object(rest_sessions.order_store, "insert_line") as insert,
            patch.object(rest_sessions, "_draft_view", return_value=[]),
        ):
            rest_sessions.add_lines(
                None,
                tenant_id="t",
                workspace_client_id=1,
                session_id="s",
                lines=[{"product_id": "p-1", "qty": 1}],
            )
        return insert

    def test_null_price_dish_is_refused(self):
        with self.assertRaises(PosError) as ctx:
            self._add_line(None)
        self.assertEqual(ctx.exception.detail, "no_price")

    def test_priced_dish_still_goes_through(self):
        insert = self._add_line(85)
        self.assertEqual(insert.call_args.kwargs["fields"]["unit_price"], 85)

    def test_a_real_zero_priced_dish_is_still_allowed(self):
        """免费赠菜是真业务:拦的是"没定价",不是"定价为 0"。"""
        insert = self._add_line(0)
        self.assertEqual(insert.call_args.kwargs["fields"]["unit_price"], 0)


if __name__ == "__main__":
    unittest.main()
