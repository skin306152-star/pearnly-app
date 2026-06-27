# -*- coding: utf-8 -*-
"""B8 RLS · 真 line_bindings + line_binding_codes 表端到端隔离(REFACTOR-B8)。

真 ensure_line_binding_rls()(enroll apply_user_rls)在真 postgres 上验:两表纯 user 维度
(只有 user_id·无 tenant_id),用户 A 的 LINE 绑定/配对码用户 B 一概读不到、塞不进(WITH CHECK)。
仓库无真 DDL(legacy 孤儿表),测试自带最小建表。CI 默认 skip,本地跑:

    set PEARNLY_INTEGRATION_DB=1
    set DATABASE_URL=postgresql://pearnly:pearnly_local_dev@localhost:5432/pearnly
    set RLS_ROLE=pearnly_app
    set PGSSLMODE=disable
    python -m unittest tests.integration.test_line_binding_rls_real_tables -v
"""

import os
import unittest

from tests.integration._helpers import require_db

UA = "11111111-1111-1111-1111-111111111111"
UB = "22222222-2222-2222-2222-222222222222"
FAKE = "00000000-0000-0000-0000-0000000000ff"

_DDL = {
    "line_bindings": (
        "id BIGSERIAL PRIMARY KEY, user_id UUID NOT NULL UNIQUE, "
        "line_user_id TEXT UNIQUE, line_display_name TEXT, "
        "bound_at TIMESTAMPTZ DEFAULT now()"
    ),
    "line_binding_codes": (
        "id BIGSERIAL PRIMARY KEY, user_id UUID NOT NULL, code TEXT NOT NULL, "
        "expires_at TIMESTAMPTZ, used_at TIMESTAMPTZ"
    ),
}


class LineBindingRlsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        require_db()
        os.environ.setdefault("PGSSLMODE", "disable")
        os.environ["RLS_ROLE"] = "pearnly_app"

        from core import db, rls
        from services.line_binding import store

        cls.db, cls.s = db, store
        with db.get_cursor_rls(bypass=True, commit=True) as cur:
            rls.ensure_rls_app_role(cur)
            for table, cols in _DDL.items():
                cur.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
                cur.execute(f"CREATE TABLE {table} ({cols})")

        store.ensure_line_binding_rls()  # enroll apply_user_rls × 2

        with db.get_cursor_rls(bypass=True, commit=True) as cur:
            for table in _DDL:
                cur.execute(f"GRANT SELECT,INSERT,UPDATE,DELETE ON {table} TO pearnly_app")
                cur.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
            cur.execute("GRANT USAGE,SELECT ON ALL SEQUENCES IN SCHEMA public TO pearnly_app")

    @classmethod
    def tearDownClass(cls):
        if getattr(cls, "db", None):
            with cls.db.get_cursor_rls(bypass=True, commit=True) as cur:
                for table in _DDL:
                    cur.execute(f"DROP TABLE IF EXISTS {table} CASCADE")

    def setUp(self):
        with self.db.get_cursor_rls(bypass=True, commit=True) as cur:
            for table in _DDL:
                cur.execute(f"TRUNCATE {table} RESTART IDENTITY")

    def _seed(self):
        with self.db.get_cursor_rls(bypass=True, commit=True) as cur:
            cur.execute(
                "INSERT INTO line_bindings (user_id, line_user_id) VALUES (%s,'Uaaa'),(%s,'Ubbb')",
                (UA, UB),
            )
            cur.execute(
                "INSERT INTO line_binding_codes (user_id, code) VALUES (%s,'111111'),(%s,'222222')",
                (UA, UB),
            )

    def test_user_sees_only_own(self):
        self._seed()
        for table in _DDL:
            with self.db.get_cursor_rls(user_id=UA) as cur:
                cur.execute(f"SELECT count(*) n FROM {table}")
                self.assertEqual(cur.fetchone()["n"], 1, f"{table}: A 应只见自己 1 行")
            with self.db.get_cursor_rls(user_id=FAKE) as cur:
                cur.execute(f"SELECT count(*) n FROM {table}")
                self.assertEqual(cur.fetchone()["n"], 0, f"{table}: 陌生用户应见 0 行")

    def test_with_check_blocks_other_user_insert(self):
        import psycopg2

        with self.db.get_cursor_rls(user_id=UA, commit=True) as cur:
            with self.assertRaises(psycopg2.errors.Error):
                cur.execute(
                    "INSERT INTO line_binding_codes (user_id, code) VALUES (%s,'999999')",
                    (UB,),
                )

    def test_owner_bypass_sees_all(self):
        self._seed()
        with self.db.get_cursor_rls(bypass=True) as cur:
            cur.execute("SELECT count(*) n FROM line_bindings")
            self.assertEqual(cur.fetchone()["n"], 2)


if __name__ == "__main__":
    unittest.main()
