# -*- coding: utf-8 -*-
"""P1-⑥ 复活来回 · 对抗素材(真库)。

上一轮那批喂的都是「一个套账里的一件货,下架再上架」。这一份专挑那批没走到的形状:

  1. 两条【都已停用】的记录同时握着同一个箱码(A 下架留码 → B 用走 → B 也下架留码)。
     复活其中一条之后再复活另一条 —— 唯一索引这时才第一次被真正逼到墙角。
  2. 复活时【换了套账】:products 的 code 唯一约束是租户级(不带 workspace),所以
     「在套账 A 删掉、后来在套账 B 按同一编码重建」是产品里走得通的一条路。商品行会被
     搬到 B,单位行不跟着搬就成孤儿 —— 码还占着、界面上没了、扫箱码在 B 里 404。
     判据落在「在 B 里扫得出来 / 在 A 里扫不出来」,不落在某一列的值上。
  3. 复活之后再下架一次:第二轮的让位必须仍然生效(_set_unit_visibility 按 ws 定位,
     而商品刚被搬过 ws)。

跑法:
    export PEARNLY_INTEGRATION_DB=1
    export DATABASE_URL=postgresql://...
    python -m unittest tests.integration.test_hostile_revival_real_db
"""

import os
import unittest
import uuid

from tests.integration._helpers import require_db

from routes import products_routes as routes
from services.pos import catalog as pos_catalog
from services.products import units as units_dal
from services.sales import products as products_dal

_WS_A = 990201
_WS_B = 990202
_BOX = "HOSTILE-BOX-77001"


class _RealDbCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        require_db()
        try:
            import psycopg2
            import psycopg2.extras
        except ImportError as exc:
            raise unittest.SkipTest(str(exc)) from exc
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

    def create(self, ws=_WS_A, **payload):
        req = routes.ProductCreate(**payload)
        return products_dal.create_product(
            self.cur, tenant_id=self.tenant, workspace_client_id=ws, fields=routes._dump(req)
        )

    def add_unit(self, product_id, unit_name, barcode, ws=_WS_A):
        return units_dal.create_unit(
            self.cur,
            tenant_id=self.tenant,
            workspace_client_id=ws,
            product_id=str(product_id),
            fields={"unit_name": unit_name, "factor_to_base": 24, "barcode": barcode},
        )

    def delist(self, product_id, ws=_WS_A):
        return products_dal.deactivate_product(
            self.cur, tenant_id=self.tenant, workspace_client_id=ws, product_id=str(product_id)
        )

    def scan(self, code, ws=_WS_A):
        """走 POS 真取件口:光有值不算复活,扫得出来才算。"""
        try:
            return pos_catalog.product_by_barcode(
                self.cur, tenant_id=self.tenant, workspace_client_id=ws, code=code
            )
        except Exception as exc:  # PosError 404 也在内
            return {"error": getattr(exc, "code", type(exc).__name__)}


class TwoDeadRowsHoldingTheSameCodeTests(_RealDbCase):
    """喂的是「同一个箱码上压着两条死行」:A 下架留码 → B 用走 → B 也下架留码。

    上一轮验的是「下架期间被【在售】商品用走 → 复活撞索引报错」,那条路上活行只有一条,
    唯一索引一直只装着一条记录。两条死行并存时索引里【一条都没有】,两次复活都以为自己
    是唯一的那个 —— 谁先复活谁拿码,后一个必须当面失败,不许静默成功(两个在售商品同码,
    收银台扫出哪个全看运气),也不许静默抹码(那就退回「商品回来了码没了」)。
    """

    def _two_dead_rows(self):
        a = self.create(code="HOSTILE-A", name_th="สินค้า A")
        self.add_unit(a["id"], "ลัง", _BOX)
        self.assertTrue(self.delist(a["id"]))
        b = self.create(code="HOSTILE-B", name_th="สินค้า B")
        self.add_unit(b["id"], "ลัง", _BOX)  # 停用期间码是自由的
        self.assertTrue(self.delist(b["id"]))
        return a, b

    def test_first_revival_takes_the_code_and_scans(self):
        a, _b = self._two_dead_rows()
        products_dal.update_product(
            self.cur,
            tenant_id=self.tenant,
            workspace_client_id=_WS_A,
            product_id=str(a["id"]),
            fields={"is_active": True},
        )
        hit = self.scan(_BOX)
        self.assertEqual(str(hit.get("id")), str(a["id"]), "先复活的那个必须扫得出来")
        self.assertEqual(hit.get("matched_unit"), "ลัง")

    def test_second_revival_fails_loudly_with_a_message_the_owner_can_act_on(self):
        """第二条复活必须当面失败,且失败得说人话。

        静默成功 = 两个在售商品同一个箱码,收银台扫出哪个全看运气;静默抹码 = 又回到
        「商品回来了码没了」。第三种同样不行:裸 500。所以断到路由那层翻出来的码上,
        并当场核对这个码在四语字典里都有文案(店主看到的是那句话,不是 detail 本身)。
        """
        import json
        import re
        from pathlib import Path

        import psycopg2
        from fastapi import HTTPException

        from core.route_helpers import translate_unique_violation

        a, b = self._two_dead_rows()
        products_dal.update_product(
            self.cur,
            tenant_id=self.tenant,
            workspace_client_id=_WS_A,
            product_id=str(a["id"]),
            fields={"is_active": True},
        )
        self.cur.execute("SAVEPOINT before_second")
        detail = None
        try:
            with translate_unique_violation(
                "sales.product_code_exists", routes._PRODUCT_UNIQUE_CODES
            ):
                products_dal.update_product(
                    self.cur,
                    tenant_id=self.tenant,
                    workspace_client_id=_WS_A,
                    product_id=str(b["id"]),
                    fields={"is_active": True},
                )
        except HTTPException as exc:
            detail = exc.detail
            self.assertEqual(exc.status_code, 409)
        except psycopg2.errors.UniqueViolation:
            self.fail("撞索引没被翻成 409,店主拿到的是裸 500")
        self.cur.execute("ROLLBACK TO SAVEPOINT before_second")
        self.assertEqual(
            detail,
            "sales.unit_barcode_exists",
            "报「编码已存在」就是撒谎:撞的是箱码,改编码永远改不好",
        )
        src = Path("static/i18n-data.js").read_text(encoding="utf-8")
        langs = re.findall(r"'sales\.unit_barcode_exists':\s*'", src)
        self.assertGreaterEqual(len(langs), 4, "这句话得四语齐全,店主看的是它不是 detail")


class RevivalIntoAnotherWorkspaceTests(_RealDbCase):
    """喂的是「在套账 A 删掉、后来在套账 B 按同一编码重建」。

    products 的 code 唯一约束是租户级(_revive_soft_deleted 的注释自己写着「死记录全租户
    至多 1 条」),所以这条路在产品里走得通,而它是唯一会让商品行换套账的路。判据落在
    「换过去之后扫得出来吗」——只断某一列的值会漏掉「行搬了、码没搬」这种半截搬家。
    """

    def test_box_code_scans_in_the_workspace_it_moved_to(self):
        a = self.create(ws=_WS_A, code="HOSTILE-MOVE", name_th="สินค้า ย้าย")
        self.add_unit(a["id"], "ลัง", _BOX, ws=_WS_A)
        self.assertTrue(self.delist(a["id"], ws=_WS_A))
        revived = self.create(ws=_WS_B, code="HOSTILE-MOVE", name_th="สินค้า ย้าย")
        self.assertEqual(str(revived["id"]), str(a["id"]), "同编码重建走的必须是复活那条路")
        hit = self.scan(_BOX, ws=_WS_B)
        self.assertEqual(
            str(hit.get("id")),
            str(a["id"]),
            f"商品搬到新套账之后箱码必须跟着能扫(现在是 {hit})",
        )

    def test_the_old_workspace_no_longer_answers_that_code(self):
        a = self.create(ws=_WS_A, code="HOSTILE-MOVE", name_th="สินค้า ย้าย")
        self.add_unit(a["id"], "ลัง", _BOX, ws=_WS_A)
        self.delist(a["id"], ws=_WS_A)
        self.create(ws=_WS_B, code="HOSTILE-MOVE", name_th="สินค้า ย้าย")
        self.assertEqual(
            self.scan(_BOX, ws=_WS_A).get("error"),
            "pos.product_not_found",
            "货已经不在这个套账里了,原套账不许还扫得出来",
        )

    def test_delisting_again_after_the_move_still_frees_the_code(self):
        """复活搬过套账之后再下架一次:让位必须仍然生效。

        _set_unit_visibility 按 (tenant, ws, product_id) 定位,而这件货刚被搬过 ws ——
        少走一步单位行就留在「在售」里占着码,而商品已经下架,谁也拿不回这个码。
        """
        a = self.create(ws=_WS_A, code="HOSTILE-MOVE", name_th="สินค้า ย้าย")
        self.add_unit(a["id"], "ลัง", _BOX, ws=_WS_A)
        self.delist(a["id"], ws=_WS_A)
        self.create(ws=_WS_B, code="HOSTILE-MOVE", name_th="สินค้า ย้าย")
        self.assertTrue(self.delist(a["id"], ws=_WS_B))
        other = self.create(ws=_WS_B, code="HOSTILE-OTHER", name_th="สินค้าอื่น")
        self.add_unit(other["id"], "ลัง", _BOX, ws=_WS_B)  # 撞索引就会当场炸
        hit = self.scan(_BOX, ws=_WS_B)
        self.assertEqual(str(hit.get("id")), str(other["id"]))


if __name__ == "__main__":
    unittest.main()
