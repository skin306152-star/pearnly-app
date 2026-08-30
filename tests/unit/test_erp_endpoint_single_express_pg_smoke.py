# -*- coding: utf-8 -*-
"""真 PostgreSQL 冒烟：legacy Express 去重与缺失部分唯一索引自愈。"""

from __future__ import annotations

import unittest
from unittest import mock

from services.erp import push_schema
from tests.unit._pg_smoke import connect_or_skip


class _CursorContext:
    def __init__(self, cursor):
        self.cursor = cursor

    def __enter__(self):
        return self.cursor

    def __exit__(self, *args):
        return False


class SingleExpressPgSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.conn = connect_or_skip()
        from psycopg2.extras import RealDictCursor

        cls.cur = cls.conn.cursor(cursor_factory=RealDictCursor)
        cls.cur.execute("SET search_path TO pg_temp, public")
        cls.cur.execute(
            "CREATE TEMP TABLE erp_endpoints ("
            "id UUID PRIMARY KEY, user_id UUID NOT NULL, name TEXT NOT NULL, "
            "adapter TEXT NOT NULL, binding_generation BIGINT NOT NULL DEFAULT 0, "
            "last_used_at TIMESTAMPTZ, created_at TIMESTAMPTZ NOT NULL DEFAULT now())"
        )
        cls.cur.execute("CREATE TEMP TABLE erp_push_logs (endpoint_id UUID NOT NULL)")
        cls.conn.commit()

    @classmethod
    def tearDownClass(cls):
        cls.conn.rollback()
        cls.cur.close()
        cls.conn.close()

    def test_missing_index_dedups_only_legacy_and_is_idempotent(self):
        user_id = "22222222-2222-2222-2222-222222222222"
        self.cur.execute(
            "INSERT INTO erp_endpoints (id,user_id,name,adapter,binding_generation) "
            "VALUES ('eeeeeeee-eeee-eeee-eeee-eeeeeeee0001',%s,'legacy-1','express',0),"
            "('eeeeeeee-eeee-eeee-eeee-eeeeeeee0002',%s,'legacy-2','express',0),"
            "('eeeeeeee-eeee-eeee-eeee-eeeeeeee0003',%s,'managed','express',1)",
            (user_id, user_id, user_id),
        )
        self.conn.commit()

        with mock.patch.object(push_schema.db, "get_cursor", return_value=_CursorContext(self.cur)):
            push_schema.ensure_single_express_endpoint()
        self.conn.commit()

        self.cur.execute(
            "SELECT binding_generation, count(*) AS n FROM erp_endpoints "
            "GROUP BY binding_generation ORDER BY binding_generation"
        )
        self.assertEqual(
            [(row["binding_generation"], row["n"]) for row in self.cur.fetchall()], [(0, 1), (1, 1)]
        )
        self.cur.execute(
            "SELECT pg_get_expr(index_meta.indpred, index_meta.indrelid) AS predicate "
            "FROM pg_index index_meta WHERE index_meta.indexrelid = "
            "to_regclass('uq_erp_endpoints_user_express')"
        )
        self.assertIn("binding_generation = 0", self.cur.fetchone()["predicate"])

        with mock.patch.object(push_schema.db, "get_cursor", return_value=_CursorContext(self.cur)):
            push_schema.ensure_single_express_endpoint()
        self.conn.commit()
        self.cur.execute(
            "SELECT count(*) AS n FROM pg_class "
            "WHERE oid = to_regclass('uq_erp_endpoints_user_express')"
        )
        self.assertEqual(self.cur.fetchone()["n"], 1)
        self.conn.rollback()


if __name__ == "__main__":
    unittest.main()
