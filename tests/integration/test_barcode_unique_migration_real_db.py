# -*- coding: utf-8 -*-
"""迁移 0092 在真库上真跑得动(P1-F)· 含脏数据时前置校验必须先拦。

只验"文件里有 CREATE UNIQUE INDEX"是假绿:SQL 语法错、DO 块引号错、脏数据下半截死在生产库,
这些静态断言一个都看不见。这里把 0092 的 upgrade()/downgrade() 真喂给 Postgres 跑,
op.execute 换成本连接的游标(迁移里全是裸 SQL 字符串,不碰 alembic 上下文)。

全程一个事务,末尾 rollback —— 索引和测试行都不落库。

跑法:
    export PEARNLY_INTEGRATION_DB=1
    export DATABASE_URL=postgresql://...
    python -m unittest tests.integration.test_barcode_unique_migration_real_db
"""

import importlib.util
import os
import unittest
import uuid
from pathlib import Path

from tests.integration._helpers import require_db

_MIGRATION = (
    Path(__file__).resolve().parents[2] / "alembic" / "versions" / "0092_products_barcode_unique.py"
)
_WS = 990002
_BARCODE = "TESTMIG-8850002"


class _OpShim:
    """迁移里的 op.execute → 本测试连接的游标(alembic 只当 SQL 的搬运工用)。"""

    def __init__(self, cur):
        self._cur = cur

    def execute(self, sql):
        self._cur.execute(sql)


def _load_migration():
    spec = importlib.util.spec_from_file_location("_mig_0092", _MIGRATION)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BarcodeUniqueMigrationRealDbTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        require_db()
        try:
            import psycopg2
            import psycopg2.extras
        except ImportError as exc:
            raise unittest.SkipTest(str(exc)) from exc
        cls.psycopg2 = psycopg2
        cls.mig = _load_migration()
        cls.conn = psycopg2.connect(os.environ["DATABASE_URL"])
        cls.conn.autocommit = False
        cls.cur = cls.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cls.mig.op = _OpShim(cls.cur)

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

    def _insert(self, *, barcode, active=True):
        self.cur.execute(
            "INSERT INTO products (tenant_id, workspace_client_id, name_th, barcode, is_active) "
            "VALUES (%s, %s, %s, %s, %s) RETURNING id",
            (self.tenant, _WS, "ทดสอบ", barcode, active),
        )
        return self.cur.fetchone()["id"]

    def _index_names(self):
        self.cur.execute(
            "SELECT indexname FROM pg_indexes WHERE indexname IN "
            "('uq_products_ws_barcode', 'uq_product_units_ws_barcode')"
        )
        return {r["indexname"] for r in self.cur.fetchall()}

    def _barcode_of(self, pid):
        self.cur.execute("SELECT barcode FROM products WHERE id = %s", (pid,))
        return self.cur.fetchone()["barcode"]

    def test_upgrade_creates_both_unique_indexes(self):
        self.mig.upgrade()
        self.assertEqual(
            self._index_names(), {"uq_products_ws_barcode", "uq_product_units_ws_barcode"}
        )

    def test_upgrade_indexes_really_reject_duplicates(self):
        """索引建出来了 ≠ 拦得住(谓词写错就成了摆设)。"""
        self.mig.upgrade()
        self._insert(barcode=_BARCODE)
        with self.assertRaises(self.psycopg2.errors.UniqueViolation):
            self._insert(barcode=_BARCODE)

    def test_upgrade_normalizes_blank_and_padded_barcodes(self):
        """空串照样进 `WHERE barcode IS NOT NULL` 的索引 → 归一必须发生在建索引之前。"""
        blank = self._insert(barcode="")
        padded = self._insert(barcode=" " + _BARCODE + " ")
        self.mig.upgrade()
        self.assertIsNone(self._barcode_of(blank))
        self.assertEqual(self._barcode_of(padded), _BARCODE)

    def test_upgrade_aborts_before_touching_anything_when_duplicates_exist(self):
        """脏库上必须整条中止:半截迁移(归一了却没建索引)比不迁移更难查。"""
        self._insert(barcode=_BARCODE)
        self._insert(barcode=_BARCODE)
        with self.assertRaises(self.psycopg2.errors.RaiseException) as ctx:
            self.mig.upgrade()
        self.assertIn("products", str(ctx.exception))
        self.assertIn(_BARCODE, str(ctx.exception))
        self.cur.execute("ROLLBACK TO SAVEPOINT case_start")
        self.assertEqual(self._index_names(), set())

    def test_precheck_catches_duplicates_that_only_collide_after_normalizing(self):
        """` 8850` 与 `8850` 归一后才撞上 —— 校验不按 btrim 归组就会放行,再炸在 CREATE 上。"""
        self._insert(barcode=_BARCODE)
        self._insert(barcode=" " + _BARCODE)
        with self.assertRaises(self.psycopg2.errors.RaiseException):
            self.mig.upgrade()

    def test_deactivated_rows_do_not_block_the_migration(self):
        self._insert(barcode=_BARCODE, active=False)
        self._insert(barcode=_BARCODE, active=False)
        self._insert(barcode=_BARCODE)
        self.mig.upgrade()
        self.assertIn("uq_products_ws_barcode", self._index_names())

    def test_downgrade_drops_both_indexes(self):
        self.mig.upgrade()
        self.mig.downgrade()
        self.assertEqual(self._index_names(), set())


if __name__ == "__main__":
    unittest.main()
