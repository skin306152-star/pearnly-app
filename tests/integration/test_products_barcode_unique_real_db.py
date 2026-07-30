# -*- coding: utf-8 -*-
"""条码唯一索引在真库上真拦得住重复插入(P1-F · 反证前端 UX 拦不算数)。

用真 products / product_units 表 + 生产那份建索引代码(create_barcode_unique_indexes),
不另造桩表 —— 桩表上验出来的唯一性证明不了生产表也有。全程一个事务,末尾 rollback,
索引与测试行都不留在库里。

末尾一组验的是启动期双跑那条路:prod 不跑 alembic,索引全靠 units.ensure_schema() 开机建。
那条路整段包在 try/except 里,不真跑一遍就分不清"建好了"和"失败了但只写了行日志"。

跑法:
    export PEARNLY_INTEGRATION_DB=1
    export DATABASE_URL=postgresql://...
    python -m unittest tests.integration.test_products_barcode_unique_real_db
"""

import os
import unittest
import uuid
from contextlib import contextmanager
from unittest.mock import patch

from tests.integration._helpers import require_db

from services.products import units as units_dal
from services.sales import products as products_dal

_WS = 990001
_BARCODE = "TESTBC-8850001"


class ProductsBarcodeUniqueRealDbTests(unittest.TestCase):
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
        # 体检按 product_active 归组(只看在售商品的单位行 · 0093),列不在直接报 UndefinedColumn。
        products_dal.ensure_unit_visibility_column(cls.cur)
        dirty = {t: g for t, g in products_dal.barcode_conflicts(cls.cur).items() if g}
        if dirty:
            cls.conn.rollback()
            cls.conn.close()
            raise unittest.SkipTest(f"库里已有重复条码,先清理再建唯一索引:{dirty}")
        products_dal.create_barcode_unique_indexes(cls.cur)

    @classmethod
    def tearDownClass(cls):
        if getattr(cls, "conn", None):
            cls.conn.rollback()  # 索引与测试行都不落库
            cls.conn.close()

    def setUp(self):
        self.tenant = str(uuid.uuid4())
        self.cur.execute("SAVEPOINT case_start")

    def tearDown(self):
        self.cur.execute("ROLLBACK TO SAVEPOINT case_start")

    def _insert(self, *, barcode, ws=_WS, active=True, tenant=None):
        self.cur.execute(
            "INSERT INTO products (tenant_id, workspace_client_id, name_th, barcode, is_active) "
            "VALUES (%s, %s, %s, %s, %s) RETURNING id",
            (tenant or self.tenant, ws, "ทดสอบ", barcode, active),
        )
        return self.cur.fetchone()["id"]

    def _insert_unit(self, *, product_id, unit_name, barcode):
        self.cur.execute(
            "INSERT INTO product_units (tenant_id, workspace_client_id, product_id, "
            "unit_name, factor_to_base, barcode) VALUES (%s, %s, %s, %s, %s, %s)",
            (self.tenant, _WS, product_id, unit_name, 12, barcode),
        )

    def test_duplicate_barcode_in_same_workspace_is_rejected(self):
        self._insert(barcode=_BARCODE)
        with self.assertRaises(self.psycopg2.errors.UniqueViolation):
            self._insert(barcode=_BARCODE)

    def test_violation_names_the_barcode_index(self):
        """路由靠 constraint_name 把 409 翻成"条码已存在"而非"编码已存在"。"""
        self._insert(barcode=_BARCODE)
        with self.assertRaises(self.psycopg2.errors.UniqueViolation) as ctx:
            self._insert(barcode=_BARCODE)
        self.assertEqual(ctx.exception.diag.constraint_name, "uq_products_ws_barcode")

    def test_deactivated_product_does_not_hold_the_barcode(self):
        self._insert(barcode=_BARCODE, active=False)
        self._insert(barcode=_BARCODE)  # 停用的老商品不占码

    def test_null_barcode_never_collides(self):
        self._insert(barcode=None)
        self._insert(barcode=None)

    def test_same_barcode_allowed_in_a_different_workspace(self):
        self._insert(barcode=_BARCODE, ws=_WS)
        self._insert(barcode=_BARCODE, ws=_WS + 1)

    def test_same_barcode_allowed_in_a_different_tenant(self):
        self._insert(barcode=_BARCODE)
        self._insert(barcode=_BARCODE, tenant=str(uuid.uuid4()))

    def test_duplicate_unit_barcode_is_rejected(self):
        """POS 扫单位码是 `LIMIT 1` 无 ORDER BY:两条同码单位存在时扫出哪个商品全看运气。"""
        pid = self._insert(barcode=None)
        self._insert_unit(product_id=pid, unit_name="ลัง", barcode=_BARCODE)
        with self.assertRaises(self.psycopg2.errors.UniqueViolation):
            self._insert_unit(product_id=pid, unit_name="แพ็ค", barcode=_BARCODE)

    def test_deactivating_a_product_frees_its_unit_barcodes(self):
        """主码靠 products 索引谓词让位,单位码靠 product_units.product_active 谓词让位
        (0093 起值不再被抹掉 · 见 test_product_price_and_revival_real_db)。不让位就是僵尸码:
        查重说"没人用"(停用商品不算命中),真存撞唯一索引,占码的商品还在列表里看不见。"""
        dead = self._insert(barcode=None)
        self._insert_unit(product_id=dead, unit_name="ลัง", barcode=_BARCODE)
        products_dal.deactivate_product(
            self.cur, tenant_id=self.tenant, workspace_client_id=_WS, product_id=dead
        )
        alive = self._insert(barcode=None)
        self._insert_unit(product_id=alive, unit_name="ลัง", barcode=_BARCODE)

    def test_patching_a_product_inactive_frees_them_too(self):
        """PATCH is_active=false 是第二条软删路径,只堵 DELETE 等于堵了一半。"""
        dead = self._insert(barcode=None)
        self._insert_unit(product_id=dead, unit_name="ลัง", barcode=_BARCODE)
        products_dal.update_product(
            self.cur,
            tenant_id=self.tenant,
            workspace_client_id=_WS,
            product_id=dead,
            fields={"is_active": False},
        )
        alive = self._insert(barcode=None)
        self._insert_unit(product_id=alive, unit_name="ลัง", barcode=_BARCODE)

    def test_conflict_report_catches_dirty_rows_before_the_index(self):
        """建索引前的体检查询本身也得真查得出来,否则迁移到生产才炸。"""
        self.cur.execute("DROP INDEX IF EXISTS uq_products_ws_barcode")
        self._insert(barcode=_BARCODE)
        self._insert(barcode=" " + _BARCODE + " ")  # 归一后才撞上,体检必须按 btrim 归组
        found = products_dal.barcode_conflicts(self.cur)["products"]
        self.assertTrue(
            any(row["barcode"] == _BARCODE and row["n"] == 2 for row in found),
            f"体检没报出重复条码:{found}",
        )


class StartupDualRunRealDbTests(unittest.TestCase):
    """开机双跑真把索引建出来(prod 唯一的生效路径)+ 库脏时宁可不建也不装作建好了。

    只把 db.get_cursor 换成本测试那条事务(否则它自己开连接 commit,索引就留在库里了),
    跑的仍是 units.ensure_schema 的真代码。
    """

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

    @contextmanager
    def _shared_cursor(self, commit=False):
        yield self.cur

    def _run_ensure_schema(self):
        with patch("core.db.get_cursor", self._shared_cursor):
            units_dal.ensure_schema()

    def _index_names(self):
        self.cur.execute(
            "SELECT indexname FROM pg_indexes WHERE indexname IN "
            "('uq_products_ws_barcode', 'uq_product_units_live_barcode')"
        )
        return {r["indexname"] for r in self.cur.fetchall()}

    def test_ensure_schema_creates_the_barcode_indexes(self):
        self._run_ensure_schema()
        self.assertEqual(
            self._index_names(), {"uq_products_ws_barcode", "uq_product_units_live_barcode"}
        )

    def test_ensure_schema_leaves_a_dirty_database_alone(self):
        """有重码时建索引必失败。装作建好了 = 之后每次开机都以为拦住了,实际一直没拦。"""
        for _ in range(2):
            self.cur.execute(
                "INSERT INTO products (tenant_id, workspace_client_id, name_th, barcode) "
                "VALUES (%s, %s, %s, %s)",
                (self.tenant, _WS, "ทดสอบ", _BARCODE),
            )
        self._run_ensure_schema()
        self.assertEqual(self._index_names(), set())


if __name__ == "__main__":
    unittest.main()
