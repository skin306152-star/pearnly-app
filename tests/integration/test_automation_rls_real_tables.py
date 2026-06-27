# -*- coding: utf-8 -*-
"""B8 RLS · 真 automation_rules 表端到端隔离(REFACTOR-B8)。

真 ensure_automation_rls()(enroll apply_tenant_or_user_rls)在真 postgres 上验:automation_rules
是 tenant_or_user(tenant_id 可空 + user_id 兜底),租户 A 的自动化规则租户 B 一概读不到、塞不进
(WITH CHECK);tenant_id IS NULL 的孤立用户行经 user_id 兜底分支隔离。仓库无真 DDL(legacy 孤儿表),
测试自带最小建表(列对齐 prod \\d)。CI 默认 skip,本地跑:

    set PEARNLY_INTEGRATION_DB=1
    set DATABASE_URL=postgresql://pearnly:pearnly_local_dev@localhost:5432/pearnly
    set RLS_ROLE=pearnly_app
    set PGSSLMODE=disable
    python -m unittest tests.integration.test_automation_rls_real_tables -v
"""

import os
import unittest

from tests.integration._helpers import require_db

A = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
B = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
UA = "11111111-1111-1111-1111-111111111111"
UB = "22222222-2222-2222-2222-222222222222"
FAKE = "00000000-0000-0000-0000-0000000000ff"

# 列对齐 prod \d automation_rules:user_id NOT NULL + tenant_id 可空。
_DDL = (
    "id UUID PRIMARY KEY DEFAULT gen_random_uuid(), user_id UUID NOT NULL, "
    "name TEXT NOT NULL, rule_type TEXT NOT NULL, config JSONB NOT NULL DEFAULT '{}'::jsonb, "
    "is_active BOOLEAN DEFAULT true, created_at TIMESTAMPTZ DEFAULT now(), tenant_id UUID"
)


class AutomationRlsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        require_db()
        os.environ.setdefault("PGSSLMODE", "disable")
        os.environ["RLS_ROLE"] = "pearnly_app"

        from core import db, rls
        from services.automation import schema

        cls.db, cls.schema = db, schema
        with db.get_cursor_rls(bypass=True, commit=True) as cur:
            rls.ensure_rls_app_role(cur)
            cur.execute("DROP TABLE IF EXISTS automation_rules CASCADE")
            cur.execute(f"CREATE TABLE automation_rules ({_DDL})")

        schema.ensure_automation_rls()  # enroll apply_tenant_or_user_rls

        with db.get_cursor_rls(bypass=True, commit=True) as cur:
            cur.execute("GRANT SELECT,INSERT,UPDATE,DELETE ON automation_rules TO pearnly_app")
            cur.execute("ALTER TABLE automation_rules FORCE ROW LEVEL SECURITY")

    @classmethod
    def tearDownClass(cls):
        if getattr(cls, "db", None):
            with cls.db.get_cursor_rls(bypass=True, commit=True) as cur:
                cur.execute("DROP TABLE IF EXISTS automation_rules CASCADE")

    def setUp(self):
        with self.db.get_cursor_rls(bypass=True, commit=True) as cur:
            cur.execute("TRUNCATE automation_rules")

    def _seed(self):
        with self.db.get_cursor_rls(bypass=True, commit=True) as cur:
            cur.execute(
                "INSERT INTO automation_rules (user_id, tenant_id, name, rule_type) "
                "VALUES (%s,%s,'A 规则','folder'),(%s,%s,'B 规则','email')",
                (UA, A, UB, B),
            )

    def test_tenant_scoped(self):
        self._seed()
        with self.db.get_cursor_rls(tenant_id=A, user_id=UA) as cur:
            cur.execute("SELECT count(*) n FROM automation_rules")
            self.assertEqual(cur.fetchone()["n"], 1, "A 应只见自己租户 1 行")
        with self.db.get_cursor_rls(tenant_id=FAKE, user_id=FAKE) as cur:
            cur.execute("SELECT count(*) n FROM automation_rules")
            self.assertEqual(cur.fetchone()["n"], 0, "陌生租户应见 0 行")

    def test_user_only_branch(self):
        # tenant_id IS NULL 的孤立用户行走 user_id 兜底分支
        with self.db.get_cursor_rls(bypass=True, commit=True) as cur:
            cur.execute(
                "INSERT INTO automation_rules (user_id, tenant_id, name, rule_type) "
                "VALUES (%s,NULL,'孤立规则','folder')",
                (UA,),
            )
        with self.db.get_cursor_rls(tenant_id=None, user_id=UA) as cur:
            cur.execute("SELECT count(*) n FROM automation_rules")
            self.assertEqual(cur.fetchone()["n"], 1, "孤立用户 A 应见自己 1 行")
        with self.db.get_cursor_rls(tenant_id=None, user_id=UB) as cur:
            cur.execute("SELECT count(*) n FROM automation_rules")
            self.assertEqual(cur.fetchone()["n"], 0, "另一无租户用户应见 0 行")

    def test_with_check_blocks_cross_tenant_insert(self):
        import psycopg2

        with self.db.get_cursor_rls(tenant_id=A, user_id=UA, commit=True) as cur:
            with self.assertRaises(psycopg2.errors.Error):
                cur.execute(
                    "INSERT INTO automation_rules (user_id, tenant_id, name, rule_type) "
                    "VALUES (%s,%s,'x','folder')",
                    (UA, B),
                )

    def test_owner_bypass_sees_all(self):
        self._seed()
        with self.db.get_cursor_rls(bypass=True) as cur:
            cur.execute("SELECT count(*) n FROM automation_rules")
            self.assertEqual(cur.fetchone()["n"], 2)


if __name__ == "__main__":
    unittest.main()
