# -*- coding: utf-8 -*-
"""B8 RLS · settings 杂项域真表端到端隔离(REFACTOR-B8)。

覆盖 6 张表 3 种模板,在真 postgres 上验隔离:
- tenant_or_user:user_settings / api_keys(user_id NOT NULL + tenant_id 可空·含 user-only 兜底分支)
- tenant:invitations / ownership_transfers(tenant_id NOT NULL·无 user_id)
- user:payment_pending / client_assignments(user_id NOT NULL·无 tenant_id)

仓库无真 DDL(legacy 孤儿表)或建表散在多个 ensure,测试自带最小建表(列对齐 prod \\d)并直接调
各自的 enroll 入口(ensure_settings_misc_rls / 内联进 ensure_authz/membership 的 apply_*)。CI 默认
skip,本地跑:

    set PEARNLY_INTEGRATION_DB=1
    set DATABASE_URL=postgresql://pearnly:pearnly_local_dev@localhost:5432/pearnly
    set RLS_ROLE=pearnly_app
    set PGSSLMODE=disable
    python -m unittest tests.integration.test_settings_misc_rls_real_tables -v
"""

import os
import unittest

from tests.integration._helpers import require_db

A = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
B = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
UA = "11111111-1111-1111-1111-111111111111"
UB = "22222222-2222-2222-2222-222222222222"
FAKE = "00000000-0000-0000-0000-0000000000ff"

# 列对齐 prod \d(只保留隔离/约束相关列)。
_DDL = {
    "user_settings": "user_id UUID NOT NULL, settings_json JSONB, tenant_id UUID",
    "api_keys": (
        "id UUID PRIMARY KEY DEFAULT gen_random_uuid(), user_id UUID NOT NULL, "
        "key_prefix TEXT NOT NULL, key_hash TEXT NOT NULL, name TEXT NOT NULL, tenant_id UUID"
    ),
    "invitations": (
        "id UUID PRIMARY KEY DEFAULT gen_random_uuid(), tenant_id UUID NOT NULL, "
        "role_key TEXT NOT NULL, scope_mode TEXT NOT NULL DEFAULT 'all', "
        "workspace_ids JSONB NOT NULL DEFAULT '[]'::jsonb, token_hash TEXT NOT NULL, "
        "invited_by UUID NOT NULL, expires_at TIMESTAMPTZ NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT now()"
    ),
    "ownership_transfers": (
        "id UUID PRIMARY KEY DEFAULT gen_random_uuid(), tenant_id UUID NOT NULL, "
        "from_user_id UUID NOT NULL, to_user_id UUID NOT NULL, token_hash TEXT NOT NULL, "
        "expires_at TIMESTAMPTZ NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT now()"
    ),
    "payment_pending": (
        "id BIGSERIAL PRIMARY KEY, user_id UUID NOT NULL, target_plan TEXT NOT NULL, "
        "amount_thb NUMERIC NOT NULL, status TEXT NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT now()"
    ),
    "client_assignments": (
        "id UUID PRIMARY KEY DEFAULT gen_random_uuid(), user_id UUID NOT NULL, "
        "client_id BIGINT NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT now(), UNIQUE(user_id, client_id)"
    ),
}

_TENANT_TABLES = ("invitations", "ownership_transfers")
_USER_TABLES = ("payment_pending", "client_assignments")
_TOU_TABLES = ("user_settings", "api_keys")


class SettingsMiscRlsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        require_db()
        os.environ.setdefault("PGSSLMODE", "disable")
        os.environ["RLS_ROLE"] = "pearnly_app"

        from core import db, rls

        cls.db = db
        with db.get_cursor_rls(bypass=True, commit=True) as cur:
            rls.ensure_rls_app_role(cur)
            for table, cols in _DDL.items():
                cur.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
                cur.execute(f"CREATE TABLE {table} ({cols})")
            # 直接 enroll(对齐各域真实落点的模板,不依赖外部表 FK)。
            rls.apply_tenant_or_user_rls(cur, *_TOU_TABLES)
            rls.apply_tenant_rls(cur, *_TENANT_TABLES)
            rls.apply_user_rls(cur, *_USER_TABLES)
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
                cur.execute(f"TRUNCATE {table} RESTART IDENTITY CASCADE")

    def test_tenant_tables_scoped(self):
        with self.db.get_cursor_rls(bypass=True, commit=True) as cur:
            cur.execute(
                "INSERT INTO invitations (tenant_id, role_key, token_hash, invited_by, expires_at) "
                "VALUES (%s,'staff','h1',%s,now()),(%s,'staff','h2',%s,now())",
                (A, UA, B, UB),
            )
            cur.execute(
                "INSERT INTO ownership_transfers (tenant_id, from_user_id, to_user_id, token_hash, expires_at) "
                "VALUES (%s,%s,%s,'t1',now()),(%s,%s,%s,'t2',now())",
                (A, UA, UB, B, UB, UA),
            )
        for table in _TENANT_TABLES:
            with self.db.get_cursor_rls(tenant_id=A) as cur:
                cur.execute(f"SELECT count(*) n FROM {table}")
                self.assertEqual(cur.fetchone()["n"], 1, f"{table}: A 应只见 1 行")
            with self.db.get_cursor_rls(tenant_id=FAKE) as cur:
                cur.execute(f"SELECT count(*) n FROM {table}")
                self.assertEqual(cur.fetchone()["n"], 0, f"{table}: 陌生租户应见 0 行")

    def test_user_tables_scoped(self):
        with self.db.get_cursor_rls(bypass=True, commit=True) as cur:
            cur.execute(
                "INSERT INTO payment_pending (user_id, target_plan, amount_thb, status) "
                "VALUES (%s,'pro',299,'pending'),(%s,'pro',299,'pending')",
                (UA, UB),
            )
            cur.execute(
                "INSERT INTO client_assignments (user_id, client_id) VALUES (%s,1),(%s,2)",
                (UA, UB),
            )
        for table in _USER_TABLES:
            with self.db.get_cursor_rls(user_id=UA) as cur:
                cur.execute(f"SELECT count(*) n FROM {table}")
                self.assertEqual(cur.fetchone()["n"], 1, f"{table}: UA 应只见 1 行")
            with self.db.get_cursor_rls(user_id=FAKE) as cur:
                cur.execute(f"SELECT count(*) n FROM {table}")
                self.assertEqual(cur.fetchone()["n"], 0, f"{table}: 陌生用户应见 0 行")

    def test_tenant_or_user_both_branches(self):
        with self.db.get_cursor_rls(bypass=True, commit=True) as cur:
            # 有租户行 + 孤立用户行(tenant_id NULL 走 user 兜底)
            cur.execute(
                "INSERT INTO user_settings (user_id, tenant_id) VALUES (%s,%s),(%s,NULL)",
                (UA, A, UB),
            )
        with self.db.get_cursor_rls(tenant_id=A, user_id=UA) as cur:
            cur.execute("SELECT count(*) n FROM user_settings")
            self.assertEqual(cur.fetchone()["n"], 1, "租户分支:A/UA 见自己 1 行")
        with self.db.get_cursor_rls(tenant_id=None, user_id=UB) as cur:
            cur.execute("SELECT count(*) n FROM user_settings")
            self.assertEqual(cur.fetchone()["n"], 1, "user 兜底分支:孤立 UB 见自己 1 行")
        with self.db.get_cursor_rls(tenant_id=None, user_id=FAKE) as cur:
            cur.execute("SELECT count(*) n FROM user_settings")
            self.assertEqual(cur.fetchone()["n"], 0, "陌生无租户用户见 0 行")

    def test_with_check_blocks_cross_tenant(self):
        import psycopg2

        with self.db.get_cursor_rls(tenant_id=A, commit=True) as cur:
            with self.assertRaises(psycopg2.errors.Error):
                cur.execute(
                    "INSERT INTO invitations (tenant_id, role_key, token_hash, invited_by, expires_at) "
                    "VALUES (%s,'staff','x',%s,now())",
                    (B, UA),
                )

    def test_owner_bypass_sees_all(self):
        with self.db.get_cursor_rls(bypass=True, commit=True) as cur:
            cur.execute(
                "INSERT INTO payment_pending (user_id, target_plan, amount_thb, status) "
                "VALUES (%s,'pro',299,'pending'),(%s,'pro',299,'pending')",
                (UA, UB),
            )
        with self.db.get_cursor_rls(bypass=True) as cur:
            cur.execute("SELECT count(*) n FROM payment_pending")
            self.assertEqual(cur.fetchone()["n"], 2)


if __name__ == "__main__":
    unittest.main()
