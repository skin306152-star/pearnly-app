# -*- coding: utf-8 -*-
"""B8 RLS · 真 etax_submissions / etax_channel_settings / invoice_risk_checks 端到端隔离(REFACTOR-B8)。

三表都 tenant_id NOT NULL、无 user_id、workspace_client_id 可空 → 纯 tenant 模板。在真 postgres 上验:
租户 A 的 e-Tax 提交/通道配置/风险检查租户 B 一概读不到、塞不进(WITH CHECK);workspace_client_id
IS NULL 的 firm-wide 行在 tenant 上下文下仍可见(纯 tenant 不隐藏 NULL·回归守门)。仓库无真 DDL
(legacy 孤儿表),测试自带最小建表(列对齐 prod \\d)。CI 默认 skip,本地跑:

    set PEARNLY_INTEGRATION_DB=1
    set DATABASE_URL=postgresql://pearnly:pearnly_local_dev@localhost:5432/pearnly
    set RLS_ROLE=pearnly_app
    set PGSSLMODE=disable
    python -m unittest tests.integration.test_etax_rls_real_tables -v
"""

import os
import unittest

from tests.integration._helpers import require_db

A = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
B = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
FAKE = "00000000-0000-0000-0000-0000000000ff"
DOC = "dddddddd-dddd-dddd-dddd-dddddddddddd"
HIST = "11111111-2222-3333-4444-555555555555"

# 列对齐 prod \d(只保留隔离/约束相关列)。
_DDL = {
    "etax_channel_settings": (
        "tenant_id UUID NOT NULL, client_id BIGINT, channel TEXT NOT NULL, "
        "workspace_client_id BIGINT, created_at TIMESTAMPTZ NOT NULL DEFAULT now(), "
        "updated_at TIMESTAMPTZ NOT NULL DEFAULT now()"
    ),
    "etax_submissions": (
        "id UUID PRIMARY KEY DEFAULT gen_random_uuid(), tenant_id UUID NOT NULL, "
        "document_id UUID NOT NULL, channel TEXT NOT NULL, status TEXT NOT NULL, "
        "workspace_client_id BIGINT, created_at TIMESTAMPTZ NOT NULL DEFAULT now()"
    ),
    "invoice_risk_checks": (
        "id BIGSERIAL PRIMARY KEY, tenant_id UUID NOT NULL, workspace_client_id BIGINT, "
        "history_id UUID NOT NULL, risk_level TEXT NOT NULL, needs_human_review BOOLEAN NOT NULL, "
        "findings JSONB NOT NULL, status TEXT NOT NULL, human_status TEXT NOT NULL DEFAULT 'none', "
        "checked_at TIMESTAMPTZ NOT NULL DEFAULT now(), created_at TIMESTAMPTZ NOT NULL DEFAULT now()"
    ),
}


class EtaxRlsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        require_db()
        os.environ.setdefault("PGSSLMODE", "disable")
        os.environ["RLS_ROLE"] = "pearnly_app"

        from core import db, rls
        from services.etax import schema as etax_schema
        from services.knowledge import risk_check

        cls.db = db
        with db.get_cursor_rls(bypass=True, commit=True) as cur:
            rls.ensure_rls_app_role(cur)
            for table, cols in _DDL.items():
                cur.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
                cur.execute(f"CREATE TABLE {table} ({cols})")

        etax_schema.ensure_etax_rls()  # etax 两表 apply_tenant_rls
        risk_check.ensure_risk_check_rls()  # invoice_risk_checks apply_tenant_rls

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
            cur.execute(
                "INSERT INTO etax_channel_settings (tenant_id, channel) VALUES (%s,'rd'),(%s,'rd')",
                (A, B),
            )
            cur.execute(
                "INSERT INTO etax_submissions (tenant_id, document_id, channel, status) "
                "VALUES (%s,%s,'rd','sent'),(%s,%s,'rd','sent')",
                (A, DOC, B, DOC),
            )
            cur.execute(
                "INSERT INTO invoice_risk_checks "
                "(tenant_id, history_id, risk_level, needs_human_review, findings, status) "
                "VALUES (%s,%s,'low',false,'[]'::jsonb,'success'),"
                "(%s,%s,'low',false,'[]'::jsonb,'success')",
                (A, HIST, B, HIST),
            )

    def test_tenant_scoped(self):
        self._seed()
        for table in _DDL:
            with self.db.get_cursor_rls(tenant_id=A) as cur:
                cur.execute(f"SELECT count(*) n FROM {table}")
                self.assertEqual(cur.fetchone()["n"], 1, f"{table}: A 应只见自己租户 1 行")
            with self.db.get_cursor_rls(tenant_id=FAKE) as cur:
                cur.execute(f"SELECT count(*) n FROM {table}")
                self.assertEqual(cur.fetchone()["n"], 0, f"{table}: 陌生租户应见 0 行")

    def test_firm_wide_null_workspace_visible(self):
        # 纯 tenant 模板:workspace_client_id IS NULL 的 firm-wide 行在 tenant 上下文下仍可见
        with self.db.get_cursor_rls(bypass=True, commit=True) as cur:
            cur.execute(
                "INSERT INTO invoice_risk_checks "
                "(tenant_id, workspace_client_id, history_id, risk_level, needs_human_review, "
                " findings, status) VALUES (%s,NULL,%s,'low',false,'[]'::jsonb,'success')",
                (A, HIST),
            )
        with self.db.get_cursor_rls(tenant_id=A) as cur:
            cur.execute("SELECT count(*) n FROM invoice_risk_checks")
            self.assertEqual(
                cur.fetchone()["n"], 1, "firm-wide NULL 账套行应可见(纯 tenant 不隐藏)"
            )

    def test_with_check_blocks_cross_tenant_insert(self):
        import psycopg2

        with self.db.get_cursor_rls(tenant_id=A, commit=True) as cur:
            with self.assertRaises(psycopg2.errors.Error):
                cur.execute(
                    "INSERT INTO etax_submissions (tenant_id, document_id, channel, status) "
                    "VALUES (%s,%s,'rd','sent')",
                    (B, DOC),
                )

    def test_owner_bypass_sees_all(self):
        self._seed()
        with self.db.get_cursor_rls(bypass=True) as cur:
            cur.execute("SELECT count(*) n FROM etax_submissions")
            self.assertEqual(cur.fetchone()["n"], 2)


if __name__ == "__main__":
    unittest.main()
