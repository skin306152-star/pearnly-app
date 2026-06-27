# -*- coding: utf-8 -*-
"""B8 RLS · ERP 凭据零暴露孤儿端到端隔离(REFACTOR-B8)。

erp_oauth_states / erp_oauth_tokens / mrerp_credentials 均 tenant_id NOT NULL → 纯 tenant 模板。
真 postgres 验:租户 A 的 OAuth state/token/MR.ERP 凭据租户 B 读不到、塞不进(WITH CHECK)。这些是
零代码访问点的纯 prod 孤儿(已删 Xero 残留 + MR.ERP 凭据),enroll 为防御纵深。仓库无真 DDL,测试自带
最小建表(列对齐 prod \\d)。CI 默认 skip,本地跑:

    set PEARNLY_INTEGRATION_DB=1
    set DATABASE_URL=postgresql://pearnly:pearnly_local_dev@localhost:5432/pearnly
    set RLS_ROLE=pearnly_app
    set PGSSLMODE=disable
    python -m unittest tests.integration.test_erp_credentials_rls_real_tables -v
"""

import os
import unittest

from tests.integration._helpers import require_db

A = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
B = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
UA = "11111111-1111-1111-1111-111111111111"
FAKE = "00000000-0000-0000-0000-0000000000ff"

_DDL = {
    "erp_oauth_states": (
        "state TEXT NOT NULL, tenant_id UUID NOT NULL, user_id UUID NOT NULL, "
        "erp_type TEXT NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT now()"
    ),
    "erp_oauth_tokens": (
        "id UUID PRIMARY KEY DEFAULT gen_random_uuid(), tenant_id UUID NOT NULL, "
        "erp_type TEXT NOT NULL, organisation_id TEXT NOT NULL, access_token TEXT NOT NULL, "
        "refresh_token TEXT NOT NULL, expires_at TIMESTAMPTZ NOT NULL, is_default BOOLEAN NOT NULL DEFAULT false, "
        "token_version INTEGER NOT NULL DEFAULT 1, auto_push BOOLEAN NOT NULL DEFAULT false, "
        "created_at TIMESTAMPTZ NOT NULL DEFAULT now(), updated_at TIMESTAMPTZ NOT NULL DEFAULT now()"
    ),
    "mrerp_credentials": (
        "id UUID PRIMARY KEY DEFAULT gen_random_uuid(), tenant_id UUID NOT NULL, "
        "encrypted_username TEXT NOT NULL, encrypted_password TEXT NOT NULL, comidyear INTEGER NOT NULL, "
        "seldb INTEGER NOT NULL, auto_push BOOLEAN NOT NULL DEFAULT false, "
        "created_at TIMESTAMPTZ NOT NULL DEFAULT now(), updated_at TIMESTAMPTZ NOT NULL DEFAULT now()"
    ),
}

_SEED = {
    "erp_oauth_states": ("state, user_id, erp_type", f"'st','{UA}','xero'"),
    "erp_oauth_tokens": (
        "erp_type, organisation_id, access_token, refresh_token, expires_at",
        "'xero','org','at','rt',now()",
    ),
    "mrerp_credentials": (
        "encrypted_username, encrypted_password, comidyear, seldb",
        "'u','p',2024,1",
    ),
}


class ErpCredentialsRlsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        require_db()
        os.environ.setdefault("PGSSLMODE", "disable")
        os.environ["RLS_ROLE"] = "pearnly_app"

        from core import db, rls
        from services.erp import credentials_rls

        cls.db = db
        with db.get_cursor_rls(bypass=True, commit=True) as cur:
            rls.ensure_rls_app_role(cur)
            for table, cols in _DDL.items():
                cur.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
                cur.execute(f"CREATE TABLE {table} ({cols})")

        credentials_rls.ensure_erp_credentials_rls()  # 3 表 apply_tenant_rls(erp_connectors 不存在跳过)

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
                cur.execute(f"TRUNCATE {table} RESTART IDENTITY CASCADE")

    def _seed(self):
        with self.db.get_cursor_rls(bypass=True, commit=True) as cur:
            for table, (cols, vals) in _SEED.items():
                for tid in (A, B):
                    cur.execute(f"INSERT INTO {table} (tenant_id, {cols}) VALUES ('{tid}', {vals})")

    def test_tenant_scoped(self):
        self._seed()
        for table in _DDL:
            with self.db.get_cursor_rls(tenant_id=A) as cur:
                cur.execute(f"SELECT count(*) n FROM {table}")
                self.assertEqual(cur.fetchone()["n"], 1, f"{table}: A 应只见 1 行")
            with self.db.get_cursor_rls(tenant_id=FAKE) as cur:
                cur.execute(f"SELECT count(*) n FROM {table}")
                self.assertEqual(cur.fetchone()["n"], 0, f"{table}: 陌生租户应见 0 行")

    def test_with_check_blocks_cross_tenant_insert(self):
        import psycopg2

        with self.db.get_cursor_rls(tenant_id=A, commit=True) as cur:
            with self.assertRaises(psycopg2.errors.Error):
                cur.execute(
                    "INSERT INTO mrerp_credentials "
                    "(tenant_id, encrypted_username, encrypted_password, comidyear, seldb) "
                    "VALUES (%s,'u','p',2024,1)",
                    (B,),
                )

    def test_owner_bypass_sees_all(self):
        self._seed()
        with self.db.get_cursor_rls(bypass=True) as cur:
            cur.execute("SELECT count(*) n FROM erp_oauth_states")
            self.assertEqual(cur.fetchone()["n"], 2)


if __name__ == "__main__":
    unittest.main()
