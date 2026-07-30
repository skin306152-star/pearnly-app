# -*- coding: utf-8 -*-
"""真库验三件事:没设价落 NULL、单位码软删后能复活、PATCH 分得清"没传"和"传了空"。

为什么必须上真库:这三条的病灶全在数据层的默认值和索引谓词上——
  · unit_price 带着 `NOT NULL DEFAULT 0`,应用层传 None 也会被数据库顶成 0,
    桩 cursor 只看得见"没进 INSERT 列",看不见库里最后是 0 还是 NULL;
  · 单位码"让位"是不是真让了,只有唯一索引真拦一次才算数;
  · PATCH 清空是不是真写了 NULL,只有 SELECT 回来才算数。

跑法:
    export PEARNLY_INTEGRATION_DB=1
    export DATABASE_URL=postgresql://...
    python -m unittest tests.integration.test_product_price_and_revival_real_db

全程一个事务,末尾 rollback:schema 改动(DROP NOT NULL / 补列 / 建索引)与测试行都不留在库里。
"""

import os
import unittest
import uuid

from tests.integration._helpers import require_db

from routes import products_routes as routes
from services.pos import catalog as pos_catalog
from services.products import units as units_dal
from services.sales import products as products_dal

_WS = 990101
_BOX = "TESTBC-BOX-8850777"
_BOTTLE = "TESTBC-BTL-8850778"
_PACK = "TESTBC-PCK-8850779"


class _RealDbCase(unittest.TestCase):
    """共用骨架:一条事务 + 每例一个 savepoint + 真 schema(跑生产那份双跑代码)。"""

    @classmethod
    def setUpClass(cls):
        require_db()
        try:
            import psycopg2
            import psycopg2.extras
        except ImportError as exc:
            raise unittest.SkipTest(str(exc)) from exc
        cls.psycopg2 = psycopg2
        cls.conn = psycopg2.connect(os.environ["DATABASE_URL"])
        cls.conn.autocommit = False
        cls.cur = cls.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        products_dal.relax_price_not_null(cls.cur)
        products_dal.ensure_unit_visibility_column(cls.cur)
        dirty = {t: g for t, g in products_dal.barcode_conflicts(cls.cur).items() if g}
        if dirty:
            cls.conn.rollback()
            cls.conn.close()
            raise unittest.SkipTest(f"库里已有重复条码,先清理:{dirty}")
        products_dal.create_barcode_unique_indexes(cls.cur)

    @classmethod
    def tearDownClass(cls):
        if getattr(cls, "conn", None):
            cls.conn.rollback()
            cls.conn.close()

    def setUp(self):
        self.tenant = str(uuid.uuid4())
        self.cur.execute("SAVEPOINT case_start")

    def tearDown(self):
        self.cur.execute("ROLLBACK TO SAVEPOINT case_start")

    def create_via_api_model(self, **payload):
        """走真 pydantic 模型 + 真 DAL:少了模型这一层就验不到"默认值 0"这个病灶。"""
        req = routes.ProductCreate(**payload)
        return products_dal.create_product(
            self.cur,
            tenant_id=self.tenant,
            workspace_client_id=_WS,
            fields=routes._dump(req),
        )

    def patch_via_api_model(self, product_id, body: dict):
        """走真 pydantic 模型 + 路由那段 PATCH 整形:body 就是前端发的 JSON。"""
        req = routes.ProductUpdate(**body)
        fields = routes._patch_fields(req, products_dal.NULLABLE_FIELDS)
        if not fields:
            return None
        return products_dal.update_product(
            self.cur,
            tenant_id=self.tenant,
            workspace_client_id=_WS,
            product_id=product_id,
            fields=fields,
        )

    def column(self, product_id, col):
        self.cur.execute(
            f"SELECT {col} FROM products WHERE tenant_id = %s AND id = %s",
            (self.tenant, product_id),
        )
        return self.cur.fetchone()[col]

    def add_unit(self, product_id, unit_name, barcode, factor=12):
        return units_dal.create_unit(
            self.cur,
            tenant_id=self.tenant,
            workspace_client_id=_WS,
            product_id=str(product_id),
            fields={"unit_name": unit_name, "factor_to_base": factor, "barcode": barcode},
        )

    def unit_barcodes(self, product_id):
        self.cur.execute(
            "SELECT unit_name, barcode, product_active FROM product_units "
            "WHERE tenant_id = %s AND product_id = %s ORDER BY unit_name",
            (self.tenant, str(product_id)),
        )
        return {r["unit_name"]: (r["barcode"], r["product_active"]) for r in self.cur.fetchall()}


class NoPriceIsNullNotZeroTests(_RealDbCase):
    """P0-① · 喂的是扫码就地建品真会发的载荷:只带一个名字,价格那格没人填。

    这条载荷才是会出事的那种——门店扫到没建档的码,当场只输个名字就把货放进目录。
    拿"填了 ฿50"的商品来验永远是绿的:那种输入下 0 和 NULL 的差别根本不出现。
    """

    def test_name_only_product_stores_null_price(self):
        row = self.create_via_api_model(name_th="นมสด 200ml")
        self.assertIsNone(
            self.column(row["id"], "unit_price"),
            "只填名字建出来的商品必须落 NULL —— 落 0 就跟真的 ฿0 赠品在数据层完全一样",
        )

    def test_explicit_zero_still_stores_zero(self):
        """反过来也得成立:฿0 是用户拍板的价(赠品/试用装),不许被当成"没设价"。

        少了这条,把默认值从 0 改成 None 就可能顺手把真的 0 也吞成 NULL,
        病灶从"分不清"换成另一种"分不清"。
        """
        row = self.create_via_api_model(name_th="ของแถม", unit_price=0)
        self.assertEqual(self.column(row["id"], "unit_price"), 0)

    def test_pos_catalog_reports_no_price_as_null(self):
        """收银台的零元闸拦的是 price 为空,拦不住 "0.00" —— 目录必须把这个区别送到前台。"""
        noprice = self.create_via_api_model(name_th="นมสด 200ml", barcode=_BOTTLE)
        free = self.create_via_api_model(name_th="ของแถม", unit_price=0, barcode=_PACK)
        got = {
            item["id"]: item["units"][0]["price"]
            for item in pos_catalog.list_products(
                self.cur, tenant_id=self.tenant, workspace_client_id=_WS
            )["items"]
        }
        self.assertIsNone(got[str(noprice["id"])], "没设价必须回 null,回 0.00 前台就分不出来")
        self.assertEqual(got[str(free["id"])], "0.00")

    def test_scan_lookup_carries_the_null_through(self):
        row = self.create_via_api_model(name_th="นมสด 200ml", barcode=_BOTTLE)
        hit = pos_catalog.product_by_barcode(
            self.cur, tenant_id=self.tenant, workspace_client_id=_WS, code=_BOTTLE
        )
        self.assertEqual(hit["id"], str(row["id"]))
        self.assertIsNone(hit["units"][0]["price"])

    def test_api_envelope_does_not_coerce_null_to_zero(self):
        row = self.create_via_api_model(name_th="นมสด 200ml")
        self.assertIsNone(routes._out(row)["unit_price"])

    def test_excel_import_blank_price_column_lands_null(self):
        """Excel 导入把空单元格整列跳过 —— 那条路上"没填价"进库同样不许变成 0。"""
        row = products_dal.create_product(
            self.cur,
            tenant_id=self.tenant,
            workspace_client_id=_WS,
            fields={"name_th": "นมถั่วเหลือง"},
        )
        self.assertIsNone(self.column(row["id"], "unit_price"))


class UnitBarcodeSurvivesSoftDeleteTests(_RealDbCase):
    """P1-⑥ · 喂的是"下架两个月中间店里没闲着"这种输入。

    会出事的输入有三种,理想输入一种都碰不到:
      · 下架 → 立刻上架(理想):抹值那版也只是"码没了",不会撞任何约束;
      · 下架期间别的商品把箱码用走了(真实):复活必须当面报错,不许静默重码;
      · 停用商品的单位行留着码(本次改法的新风险):扫码 `LIMIT 1` 无 ORDER BY,
        不筛 product_active 就可能挑中死行,把在售商品报成"没这个货"。
    """

    def _milk_with_three_unit_codes(self):
        milk = products_dal.create_product(
            self.cur,
            tenant_id=self.tenant,
            workspace_client_id=_WS,
            fields={"name_th": "นมสด", "code": "MILK-1", "unit_price": 20},
        )
        self.add_unit(milk["id"], "ลัง", _BOX, factor=24)
        self.add_unit(milk["id"], "แพ็ค", _PACK, factor=6)
        self.add_unit(milk["id"], "ขวด", _BOTTLE, factor=1)
        return milk

    def test_soft_delete_keeps_the_values_and_only_hides_them(self):
        milk = self._milk_with_three_unit_codes()
        products_dal.deactivate_product(
            self.cur, tenant_id=self.tenant, workspace_client_id=_WS, product_id=milk["id"]
        )
        after = self.unit_barcodes(milk["id"])
        self.assertEqual(
            {name: bc for name, (bc, _live) in after.items()},
            {"ลัง": _BOX, "แพ็ค": _PACK, "ขวด": _BOTTLE},
            "软删的契约是保留引用可复活;抹成 NULL 之后上架回来单位码全空,只能一条条重录",
        )
        self.assertEqual([live for _bc, live in after.values()], [False, False, False])

    def test_the_codes_are_really_free_while_it_is_down(self):
        """保住值不许以"不让位"为代价:下架期间别的商品必须能用这个箱码。"""
        milk = self._milk_with_three_unit_codes()
        products_dal.deactivate_product(
            self.cur, tenant_id=self.tenant, workspace_client_id=_WS, product_id=milk["id"]
        )
        other = products_dal.create_product(
            self.cur, tenant_id=self.tenant, workspace_client_id=_WS, fields={"name_th": "นมข้น"}
        )
        self.add_unit(other["id"], "ลัง", _BOX)

    def test_reactivating_brings_every_unit_code_back(self):
        milk = self._milk_with_three_unit_codes()
        products_dal.deactivate_product(
            self.cur, tenant_id=self.tenant, workspace_client_id=_WS, product_id=milk["id"]
        )
        products_dal.update_product(
            self.cur,
            tenant_id=self.tenant,
            workspace_client_id=_WS,
            product_id=milk["id"],
            fields={"is_active": True},
        )
        self.assertEqual(
            self.unit_barcodes(milk["id"]),
            {"ลัง": (_BOX, True), "แพ็ค": (_PACK, True), "ขวด": (_BOTTLE, True)},
        )

    def test_scanning_a_box_code_works_again_after_the_round_trip(self):
        """光有值不算数——扫得出来才算复活。"""
        milk = self._milk_with_three_unit_codes()
        products_dal.deactivate_product(
            self.cur, tenant_id=self.tenant, workspace_client_id=_WS, product_id=milk["id"]
        )
        products_dal.update_product(
            self.cur,
            tenant_id=self.tenant,
            workspace_client_id=_WS,
            product_id=milk["id"],
            fields={"is_active": True},
        )
        hit = pos_catalog.product_by_barcode(
            self.cur, tenant_id=self.tenant, workspace_client_id=_WS, code=_BOX
        )
        self.assertEqual(hit["id"], str(milk["id"]))
        self.assertEqual(hit["matched_unit"], "ลัง")

    def test_recreating_by_code_also_brings_the_unit_codes_back(self):
        """第二条复活路径:老板不去"含停用"列表,直接按同一个编码重建一遍。"""
        milk = self._milk_with_three_unit_codes()
        products_dal.deactivate_product(
            self.cur, tenant_id=self.tenant, workspace_client_id=_WS, product_id=milk["id"]
        )
        revived = products_dal.create_product(
            self.cur,
            tenant_id=self.tenant,
            workspace_client_id=_WS,
            fields={"name_th": "นมสด", "code": "MILK-1"},
        )
        self.assertEqual(str(revived["id"]), str(milk["id"]))
        self.assertEqual(
            self.unit_barcodes(milk["id"]),
            {"ลัง": (_BOX, True), "แพ็ค": (_PACK, True), "ขวด": (_BOTTLE, True)},
        )

    def test_revival_onto_a_taken_code_fails_loudly(self):
        """下架期间箱码被别的商品用走了 → 上架必须撞唯一索引报出来。

        静默成功 = 两个在售商品同一个箱码,收银台扫出哪个全看运气;静默抹码 = 又回到
        "商品回来了码没了"。两种静默都不许,只剩"当面说清楚"这一条。
        """
        milk = self._milk_with_three_unit_codes()
        products_dal.deactivate_product(
            self.cur, tenant_id=self.tenant, workspace_client_id=_WS, product_id=milk["id"]
        )
        other = products_dal.create_product(
            self.cur, tenant_id=self.tenant, workspace_client_id=_WS, fields={"name_th": "นมข้น"}
        )
        self.add_unit(other["id"], "ลัง", _BOX)
        with self.assertRaises(self.psycopg2.errors.UniqueViolation) as ctx:
            products_dal.update_product(
                self.cur,
                tenant_id=self.tenant,
                workspace_client_id=_WS,
                product_id=milk["id"],
                fields={"is_active": True},
            )
        self.assertEqual(
            routes._PRODUCT_UNIQUE_CODES.get(ctx.exception.diag.constraint_name),
            "sales.unit_barcode_exists",
            "报「编码已存在」的话用户改多少次编码都过不去,真正要改的是那个箱码",
        )

    def test_a_unit_added_to_a_delisted_product_does_not_hold_the_code(self):
        """给已停用的商品补配箱码(准备下次上架)不许立刻占着码。

        新行的默认值是"在售",而查重那边筛掉了不在售的商品 → 一律回"没人用":绿字放行,
        真存撞唯一索引,占码的商品在列表里看不见。这是软删让位规则上最后一个没堵的口子。
        """
        dead = products_dal.create_product(
            self.cur, tenant_id=self.tenant, workspace_client_id=_WS, fields={"name_th": "เก่า"}
        )
        products_dal.deactivate_product(
            self.cur, tenant_id=self.tenant, workspace_client_id=_WS, product_id=dead["id"]
        )
        self.add_unit(dead["id"], "ลัง", _BOX)
        live = products_dal.create_product(
            self.cur, tenant_id=self.tenant, workspace_client_id=_WS, fields={"name_th": "ใหม่"}
        )
        self.add_unit(live["id"], "ลัง", _BOX)

    def test_a_dead_unit_row_never_shadows_the_live_one(self):
        """停用商品的单位行留着码之后的新风险:同码两行,`LIMIT 1` 无 ORDER BY。

        不筛 product_active 就可能挑中死行 → 商品明明在售却报「商品不存在」。
        """
        milk = self._milk_with_three_unit_codes()
        products_dal.deactivate_product(
            self.cur, tenant_id=self.tenant, workspace_client_id=_WS, product_id=milk["id"]
        )
        other = products_dal.create_product(
            self.cur,
            tenant_id=self.tenant,
            workspace_client_id=_WS,
            fields={"name_th": "นมข้น", "unit_price": 30},
        )
        self.add_unit(other["id"], "ลัง", _BOX)
        for _ in range(5):
            hit = pos_catalog.product_by_barcode(
                self.cur, tenant_id=self.tenant, workspace_client_id=_WS, code=_BOX
            )
            self.assertEqual(hit["id"], str(other["id"]))
        found = products_dal.find_by(
            self.cur, tenant_id=self.tenant, workspace_client_id=_WS, key="barcode", value=_BOX
        )
        self.assertEqual(str(found["id"]), str(other["id"]))

    def test_unit_code_of_a_dead_product_falls_back_to_a_live_main_code(self):
        """P1-⑩:单位码只对得上一条停用商品时,POS 回落主码而不是直接 404。

        老库里(product_active 回填之前建的行)这种残留是常态;不回落就是收银员对着
        列表里明明在的商品看「商品不存在」,台前没处可查。
        """
        dead = products_dal.create_product(
            self.cur, tenant_id=self.tenant, workspace_client_id=_WS, fields={"name_th": "เก่า"}
        )
        self.add_unit(dead["id"], "ลัง", _BOX)
        self.cur.execute(
            "UPDATE products SET is_active = FALSE WHERE tenant_id = %s AND id = %s",
            (self.tenant, dead["id"]),
        )
        live = products_dal.create_product(
            self.cur,
            tenant_id=self.tenant,
            workspace_client_id=_WS,
            fields={"name_th": "ใหม่", "barcode": _BOX, "unit_price": 15},
        )
        hit = pos_catalog.product_by_barcode(
            self.cur, tenant_id=self.tenant, workspace_client_id=_WS, code=_BOX
        )
        self.assertEqual(hit["id"], str(live["id"]))
        self.assertEqual(hit["matched_unit"], live["base_unit"], "回落到主码 = 按基本单位卖")


class PatchTellsUnsetFromClearedTests(_RealDbCase):
    """P1-⑪ · 喂的是前端 readForm() 真会发的两种 body,不是"空白字符串"那种。

    上一版为此写的"留空落 NULL"分支只在收到空白【字符串】时才生效,而前端永远不发空串
    (`val(...) || null`)——用那种理想输入验,分支绿了,产品里那段是死代码。
    """

    def _milk(self):
        return products_dal.create_product(
            self.cur,
            tenant_id=self.tenant,
            workspace_client_id=_WS,
            fields={"name_th": "นมสด", "barcode": _BOTTLE, "unit_price": 20},
        )

    def test_field_not_sent_leaves_the_column_alone(self):
        milk = self._milk()
        self.patch_via_api_model(milk["id"], {"name_th": "นมสดใหม่"})
        self.assertEqual(self.column(milk["id"], "barcode"), _BOTTLE)

    def test_explicit_null_really_clears_the_column(self):
        milk = self._milk()
        out = self.patch_via_api_model(milk["id"], {"name_th": "นมสด", "barcode": None})
        self.assertIsNone(out["barcode"])
        self.assertIsNone(
            self.column(milk["id"], "barcode"),
            "回 ok:true 却没改 = 用户以为删掉了,码还占着别人用不了",
        )

    def test_cleared_code_is_immediately_reusable(self):
        """清空得真让出索引位:清完别的商品马上要能用这个码,否则等于没清。"""
        milk = self._milk()
        self.patch_via_api_model(milk["id"], {"barcode": None})
        products_dal.create_product(
            self.cur,
            tenant_id=self.tenant,
            workspace_client_id=_WS,
            fields={"name_th": "นมข้น", "barcode": _BOTTLE},
        )

    def test_clearing_the_price_is_not_the_same_as_setting_zero(self):
        milk = self._milk()
        self.patch_via_api_model(milk["id"], {"unit_price": 0})
        self.assertEqual(self.column(milk["id"], "unit_price"), 0)
        self.patch_via_api_model(milk["id"], {"unit_price": None})
        self.assertIsNone(self.column(milk["id"], "unit_price"))

    def test_null_on_a_not_null_column_is_treated_as_not_sent(self):
        """NOT NULL 列上的 null 写下去数据库直接报错,拦在整形层比让用户吃 500 说得清。"""
        milk = self._milk()
        self.patch_via_api_model(milk["id"], {"name_th": None, "barcode": None})
        self.assertEqual(self.column(milk["id"], "name_th"), "นมสด")
        self.assertIsNone(self.column(milk["id"], "barcode"))

    def test_clearing_a_unit_barcode_works_the_same_way(self):
        """箱码印错了要能删掉,不能只能改成别的码。"""
        milk = self._milk()
        unit = self.add_unit(milk["id"], "ลัง", _BOX)
        req = routes.UnitUpdate(barcode=None)
        units_dal.update_unit(
            self.cur,
            tenant_id=self.tenant,
            workspace_client_id=_WS,
            product_id=str(milk["id"]),
            unit_id=str(unit["id"]),
            fields=routes._patch_fields(req, units_dal.NULLABLE_UNIT_FIELDS),
        )
        self.assertEqual(self.unit_barcodes(milk["id"]), {"ลัง": (None, True)})


if __name__ == "__main__":
    unittest.main()
